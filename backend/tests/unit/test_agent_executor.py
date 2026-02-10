"""Unit tests for the Agent Task Executor."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.executor import (
    TaskExecutor,
    _call_llm,
    _compute_quality_score,
)
from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    AuditAction,
    PermissionLevel,
    TaskPriority,
    TaskStatus,
)
from app.modules.agent_system.governance import (
    BudgetExceeded,
    PermissionDenied,
)


# ---------------------------------------------------------------------------
# LLM stub tests
# ---------------------------------------------------------------------------

class TestCallLLM:
    @pytest.mark.asyncio
    async def test_returns_expected_keys(self):
        result = await _call_llm(
            model_id="test-model",
            system_prompt="You are a test.",
            user_prompt="Hello world",
            max_tokens=100,
            temperature=0.5,
        )
        assert "text" in result
        assert "tokens_used" in result
        assert "cost_usd" in result
        assert "model" in result
        assert result["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_tokens_used_bounded_by_max(self):
        result = await _call_llm(
            model_id="test",
            system_prompt=None,
            user_prompt="short",
            max_tokens=10,
            temperature=0.7,
        )
        assert result["tokens_used"] <= 10


class TestComputeQualityScore:
    @pytest.mark.asyncio
    async def test_short_text_low_score(self):
        score = await _compute_quality_score("")
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_normal_text_reasonable_score(self):
        score = await _compute_quality_score("This is a well-formed paragraph of text.")
        assert score >= 0.7


# ---------------------------------------------------------------------------
# TaskExecutor tests
# ---------------------------------------------------------------------------

class TestTaskExecutor:
    """Test the TaskExecutor with in-memory database."""

    @pytest.mark.asyncio
    async def test_execute_draft_only_goes_to_awaiting_approval(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_task: AgentTask,
        sample_budget: AgentBudget,
    ):
        """Draft-only agent tasks should end up awaiting approval."""
        assert sample_agent.permission_level == PermissionLevel.DRAFT_ONLY

        executor = TaskExecutor(db)
        result = await executor.execute(sample_task, user_role="editor")

        assert result.status == TaskStatus.AWAITING_APPROVAL
        assert result.output_data is not None
        assert result.tokens_used > 0
        assert result.quality_score is not None

    @pytest.mark.asyncio
    async def test_execute_auto_agent_completes(
        self,
        db: AsyncSession,
        auto_agent: Agent,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """Auto-execute agent tasks should complete directly."""
        # Create budget for auto_agent
        budget = AgentBudget(
            org_id=org_id,
            agent_id=auto_agent.id,
            daily_token_limit=100000,
            daily_usd_limit=10.0,
            monthly_usd_limit=200.0,
            last_reset_daily=datetime.now(timezone.utc),
            last_reset_monthly=datetime.now(timezone.utc),
        )
        db.add(budget)
        await db.flush()

        task = AgentTask(
            org_id=org_id,
            agent_id=auto_agent.id,
            title="Auto Task",
            input_data={"context": "test"},
            created_by=user_id,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        executor = TaskExecutor(db)
        result = await executor.execute(task, user_role="editor")

        assert result.status == TaskStatus.COMPLETED
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_disabled_agent_fails(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_task: AgentTask,
        sample_budget: AgentBudget,
    ):
        """Disabled agent should cause task failure."""
        sample_agent.is_enabled = False
        await db.flush()

        executor = TaskExecutor(db)
        result = await executor.execute(sample_task, user_role="editor")

        assert result.status == TaskStatus.FAILED
        assert "disabled" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_budget_exceeded_fails(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_task: AgentTask,
        sample_budget: AgentBudget,
    ):
        """Task should fail when budget is exceeded."""
        # Set budget to nearly exhausted
        sample_budget.tokens_used_today = 99999
        sample_budget.daily_token_limit = 100000
        await db.flush()

        # The agent max_tokens is 4096, which would exceed remaining 1 token
        executor = TaskExecutor(db)
        result = await executor.execute(sample_task, user_role="editor")

        assert result.status == TaskStatus.FAILED
        assert "budget" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_records_tokens_and_cost(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_task: AgentTask,
        sample_budget: AgentBudget,
    ):
        """Execution should record token usage and cost."""
        executor = TaskExecutor(db)
        result = await executor.execute(sample_task, user_role="editor")

        assert result.tokens_used > 0
        assert result.cost_usd > 0.0

    @pytest.mark.asyncio
    async def test_build_prompt_includes_all_parts(
        self,
        db: AsyncSession,
    ):
        """_build_prompt should combine title, description, and input_data."""
        executor = TaskExecutor(db)
        task = AgentTask(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            title="My Title",
            description="My Description",
            input_data={"context": "some context", "instructions": "do this"},
            created_by=uuid.uuid4(),
        )
        prompt = executor._build_prompt(task)
        assert "My Title" in prompt
        assert "My Description" in prompt
        assert "some context" in prompt
        assert "do this" in prompt

    @pytest.mark.asyncio
    async def test_build_prompt_handles_no_input(
        self,
        db: AsyncSession,
    ):
        """_build_prompt should work without input_data."""
        executor = TaskExecutor(db)
        task = AgentTask(
            org_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            title="Simple Title",
            description=None,
            input_data=None,
            created_by=uuid.uuid4(),
        )
        prompt = executor._build_prompt(task)
        assert "Simple Title" in prompt

    @pytest.mark.asyncio
    async def test_task_marked_running_during_execution(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_task: AgentTask,
        sample_budget: AgentBudget,
    ):
        """Task should be marked as RUNNING before LLM call."""
        # We verify the started_at is set after execution
        assert sample_task.started_at is None

        executor = TaskExecutor(db)
        result = await executor.execute(sample_task, user_role="editor")

        assert result.started_at is not None
