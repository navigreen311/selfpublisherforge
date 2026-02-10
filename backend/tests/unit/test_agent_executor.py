"""Unit tests for the Agent Task Executor."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

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
# Helpers – fake LLM responses used by multiple test classes
# ---------------------------------------------------------------------------

def _make_fake_llm_response(*, content: str = "Generated text.", total_tokens: int = 42, model_id: str = "test-model"):
    """Return a mock object that behaves like an ``LLMResponse``."""
    resp = MagicMock()
    resp.succeeded = True
    resp.content = content
    resp.total_tokens = total_tokens
    resp.model_id = model_id
    resp.finish_reason = "end_turn"
    resp.metadata = {}
    return resp


def _make_fake_call_llm_result(*, text: str = "Generated text.", tokens_used: int = 42, cost_usd: float = 0.000126, model: str = "test-model"):
    """Return a dict matching the shape produced by ``_call_llm``."""
    return {
        "text": text,
        "tokens_used": tokens_used,
        "cost_usd": cost_usd,
        "model": model,
    }


# ---------------------------------------------------------------------------
# LLM stub tests
# ---------------------------------------------------------------------------

class TestCallLLM:
    @pytest.mark.asyncio
    @patch("app.modules.agent_system.executor.AnthropicProvider")
    async def test_returns_expected_keys(self, mock_provider_cls):
        """_call_llm should return the expected dict keys when the provider succeeds."""
        mock_provider = mock_provider_cls.return_value
        mock_provider.generate = AsyncMock(
            return_value=_make_fake_llm_response(model_id="test-model", total_tokens=50),
        )

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
    @patch("app.modules.agent_system.executor.AnthropicProvider")
    async def test_tokens_used_bounded_by_max(self, mock_provider_cls):
        """tokens_used returned by the provider must not exceed max_tokens."""
        mock_provider = mock_provider_cls.return_value
        mock_provider.generate = AsyncMock(
            return_value=_make_fake_llm_response(total_tokens=8),
        )

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
        # The new heuristic-based scoring considers length adequacy,
        # sentence structure, vocabulary richness, formatting, and keyword
        # relevance.  A short single sentence scores well below 0.7 because
        # it is far shorter than the default expected_min_words=50.
        # Use a sufficiently long, well-structured paragraph instead.
        text = (
            "The self-publishing industry has experienced remarkable growth over the "
            "past decade, driven by accessible digital platforms and a thriving "
            "community of independent authors. Writers now have unprecedented control "
            "over pricing, distribution, and creative direction. Marketing strategies "
            "have evolved to include social media outreach, email newsletters, and "
            "targeted advertising campaigns. Reader engagement remains a critical "
            "metric for long-term success in this competitive landscape."
        )
        score = await _compute_quality_score(text)
        assert score >= 0.7


# ---------------------------------------------------------------------------
# TaskExecutor tests
# ---------------------------------------------------------------------------

# All TaskExecutor tests that would trigger an LLM call mock ``_call_llm``
# at the module level so no real API requests are made.

_CALL_LLM_PATCH = "app.modules.agent_system.executor._call_llm"


class TestTaskExecutor:
    """Test the TaskExecutor with in-memory database."""

    @pytest.mark.asyncio
    @patch(_CALL_LLM_PATCH, new_callable=AsyncMock, return_value=_make_fake_call_llm_result())
    async def test_execute_draft_only_goes_to_awaiting_approval(
        self,
        mock_call_llm,
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
    @patch("app.modules.agent_system.executor._compute_quality_score", new_callable=AsyncMock, return_value=0.9)
    @patch(_CALL_LLM_PATCH, new_callable=AsyncMock, return_value=_make_fake_call_llm_result())
    async def test_execute_auto_agent_completes(
        self,
        mock_call_llm,
        mock_quality_score,
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
    @patch(_CALL_LLM_PATCH, new_callable=AsyncMock, return_value=_make_fake_call_llm_result())
    async def test_execute_records_tokens_and_cost(
        self,
        mock_call_llm,
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
    @patch(_CALL_LLM_PATCH, new_callable=AsyncMock, return_value=_make_fake_call_llm_result())
    async def test_task_marked_running_during_execution(
        self,
        mock_call_llm,
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
