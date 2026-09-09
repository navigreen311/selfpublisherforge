"""Unit tests for the Agent Governance layer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.governance import (
    BudgetExceeded,
    PermissionDenied,
    QualityBelowSLA,
    check_budget,
    check_permission,
    emergency_stop,
    record_usage,
    requires_approval,
    validate_quality,
)
from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentWorkflow,
    AuditTrail,
    PermissionLevel,
    TaskStatus,
    WorkflowStatus,
)

# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------

class TestCheckPermission:
    def test_disabled_agent_raises(self, sample_agent: Agent):
        """Disabled agents should raise PermissionDenied."""
        sample_agent.is_enabled = False
        with pytest.raises(PermissionDenied, match="disabled"):
            check_permission(sample_agent, "execute_auto")

    def test_draft_only_cannot_auto_execute(self, sample_agent: Agent):
        """Draft-only agents cannot auto-execute."""
        sample_agent.permission_level = PermissionLevel.DRAFT_ONLY
        with pytest.raises(PermissionDenied, match="does not allow"):
            check_permission(sample_agent, "execute_auto")

    def test_suggest_cannot_auto_execute(self, sample_agent: Agent):
        """Suggest-level agents cannot auto-execute."""
        sample_agent.permission_level = PermissionLevel.SUGGEST
        with pytest.raises(PermissionDenied, match="does not allow"):
            check_permission(sample_agent, "execute_auto")

    def test_auto_execute_low_allowed(self, sample_agent: Agent):
        """Auto-execute low should be allowed."""
        sample_agent.permission_level = PermissionLevel.AUTO_EXECUTE_LOW
        assert check_permission(sample_agent, "execute_auto") is True

    def test_auto_execute_high_requires_admin(self, sample_agent: Agent):
        """Auto-execute high requires admin role."""
        sample_agent.permission_level = PermissionLevel.AUTO_EXECUTE_HIGH
        with pytest.raises(PermissionDenied, match="admin or owner"):
            check_permission(sample_agent, "execute_auto", user_role="editor")

    def test_auto_execute_high_allowed_for_admin(self, sample_agent: Agent):
        """Auto-execute high should work for admin."""
        sample_agent.permission_level = PermissionLevel.AUTO_EXECUTE_HIGH
        assert check_permission(sample_agent, "execute_auto", user_role="admin") is True

    def test_full_autonomous_requires_admin(self, sample_agent: Agent):
        """Full autonomous requires admin role."""
        sample_agent.permission_level = PermissionLevel.FULL_AUTONOMOUS
        with pytest.raises(PermissionDenied, match="admin or owner"):
            check_permission(sample_agent, "execute_auto", user_role="writer")

    def test_full_autonomous_allowed_for_owner(self, sample_agent: Agent):
        """Full autonomous should work for owner."""
        sample_agent.permission_level = PermissionLevel.FULL_AUTONOMOUS
        assert check_permission(sample_agent, "execute_auto", user_role="owner") is True

    def test_approve_action_allowed(self, sample_agent: Agent):
        """Approve action should always be allowed for enabled agents."""
        sample_agent.permission_level = PermissionLevel.DRAFT_ONLY
        assert check_permission(sample_agent, "approve") is True


class TestRequiresApproval:
    def test_draft_only_requires_approval(self, sample_agent: Agent):
        sample_agent.permission_level = PermissionLevel.DRAFT_ONLY
        assert requires_approval(sample_agent) is True

    def test_suggest_requires_approval(self, sample_agent: Agent):
        sample_agent.permission_level = PermissionLevel.SUGGEST
        assert requires_approval(sample_agent) is True

    def test_auto_execute_low_no_approval(self, sample_agent: Agent):
        sample_agent.permission_level = PermissionLevel.AUTO_EXECUTE_LOW
        assert requires_approval(sample_agent) is False

    def test_full_autonomous_no_approval(self, sample_agent: Agent):
        sample_agent.permission_level = PermissionLevel.FULL_AUTONOMOUS
        assert requires_approval(sample_agent) is False


# ---------------------------------------------------------------------------
# Budget checks
# ---------------------------------------------------------------------------

class TestCheckBudget:
    @pytest.mark.asyncio
    async def test_creates_default_budget_if_missing(
        self,
        db: AsyncSession,
        sample_agent: Agent,
    ):
        """Should create a budget if none exists."""
        budget = await check_budget(db, sample_agent, estimated_tokens=100, estimated_cost=0.01)
        assert budget is not None
        assert budget.agent_id == sample_agent.id

    @pytest.mark.asyncio
    async def test_daily_token_limit_exceeded(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_budget: AgentBudget,
    ):
        """Should raise BudgetExceeded when daily tokens would be exceeded."""
        sample_budget.tokens_used_today = 99000
        sample_budget.daily_token_limit = 100000
        await db.flush()

        with pytest.raises(BudgetExceeded, match="Daily token limit"):
            await check_budget(db, sample_agent, estimated_tokens=2000)

    @pytest.mark.asyncio
    async def test_daily_usd_limit_exceeded(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_budget: AgentBudget,
    ):
        """Should raise BudgetExceeded when daily USD would be exceeded."""
        sample_budget.usd_used_today = 9.5
        sample_budget.daily_usd_limit = 10.0
        await db.flush()

        with pytest.raises(BudgetExceeded, match="Daily USD limit"):
            await check_budget(db, sample_agent, estimated_cost=1.0)

    @pytest.mark.asyncio
    async def test_monthly_usd_limit_exceeded(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_budget: AgentBudget,
    ):
        """Should raise BudgetExceeded when monthly USD would be exceeded."""
        sample_budget.usd_used_this_month = 199.0
        sample_budget.monthly_usd_limit = 200.0
        await db.flush()

        with pytest.raises(BudgetExceeded, match="Monthly USD limit"):
            await check_budget(db, sample_agent, estimated_cost=2.0)

    @pytest.mark.asyncio
    async def test_within_budget_passes(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_budget: AgentBudget,
    ):
        """Should pass when within all limits."""
        budget = await check_budget(
            db, sample_agent, estimated_tokens=100, estimated_cost=0.01
        )
        assert budget is not None

    @pytest.mark.asyncio
    async def test_daily_reset(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_budget: AgentBudget,
    ):
        """Daily counters should reset when last_reset_daily is > 1 day ago."""
        sample_budget.last_reset_daily = datetime.now(UTC) - timedelta(days=2)
        sample_budget.tokens_used_today = 50000
        sample_budget.usd_used_today = 5.0
        await db.flush()

        budget = await check_budget(db, sample_agent, estimated_tokens=100)
        assert budget.tokens_used_today == 0
        assert budget.usd_used_today == 0.0


class TestRecordUsage:
    @pytest.mark.asyncio
    async def test_increments_counters(
        self,
        db: AsyncSession,
        sample_agent: Agent,
        sample_budget: AgentBudget,
    ):
        """Should increment all usage counters."""
        initial_tokens = sample_budget.tokens_used_today
        initial_usd = sample_budget.usd_used_today

        budget = await record_usage(
            db,
            agent_id=sample_agent.id,
            tokens_used=1000,
            cost_usd=0.003,
        )
        assert budget.tokens_used_today == initial_tokens + 1000
        assert budget.usd_used_today == pytest.approx(initial_usd + 0.003)
        assert budget.total_tokens_used == 1000
        assert budget.total_usd_used == pytest.approx(0.003)


# ---------------------------------------------------------------------------
# Quality SLA validation
# ---------------------------------------------------------------------------

class TestValidateQuality:
    def test_above_threshold_passes(self):
        assert validate_quality(0.9, threshold=0.7) is True

    def test_at_threshold_passes(self):
        assert validate_quality(0.7, threshold=0.7) is True

    def test_below_threshold_raises(self):
        with pytest.raises(QualityBelowSLA, match="below threshold"):
            validate_quality(0.5, threshold=0.7)

    def test_custom_threshold(self):
        with pytest.raises(QualityBelowSLA):
            validate_quality(0.8, threshold=0.9)


# ---------------------------------------------------------------------------
# Emergency stop
# ---------------------------------------------------------------------------

class TestEmergencyStop:
    @pytest.mark.asyncio
    async def test_cancels_running_tasks(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        sample_agent: Agent,
    ):
        """Emergency stop should cancel all running/pending tasks."""
        # Create some tasks in different states
        for task_status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED]:
            task = AgentTask(
                org_id=org_id,
                agent_id=sample_agent.id,
                title=f"Task {task_status.value}",
                status=task_status,
                created_by=user_id,
            )
            db.add(task)
        await db.flush()

        tasks_cancelled, wf_cancelled = await emergency_stop(
            db, org_id, actor_id=user_id
        )

        # PENDING and RUNNING should be cancelled; COMPLETED should not
        assert tasks_cancelled == 2
        assert wf_cancelled == 0

    @pytest.mark.asyncio
    async def test_cancels_running_workflows(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """Emergency stop should cancel running/paused workflows."""
        for wf_status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED, WorkflowStatus.COMPLETED]:
            wf = AgentWorkflow(
                org_id=org_id,
                name=f"WF {wf_status.value}",
                steps=[],
                status=wf_status,
                created_by=user_id,
            )
            db.add(wf)
        await db.flush()

        tasks_cancelled, wf_cancelled = await emergency_stop(
            db, org_id, actor_id=user_id
        )

        assert wf_cancelled == 2  # RUNNING and PAUSED

    @pytest.mark.asyncio
    async def test_creates_audit_entry(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """Emergency stop should create an audit trail entry."""
        from sqlalchemy import select

        await emergency_stop(db, org_id, actor_id=user_id)

        result = await db.execute(
            select(AuditTrail).where(
                AuditTrail.org_id == org_id,
                AuditTrail.action == "emergency_stop",
            )
        )
        entry = result.scalar_one_or_none()
        assert entry is not None
        assert entry.actor_id == user_id
