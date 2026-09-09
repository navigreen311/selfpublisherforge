"""Governance layer for the Agent System.

Handles permission enforcement, budget checking, quality SLA validation,
and emergency stop.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.audit import record_audit
from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentWorkflow,
    AuditAction,
    PermissionLevel,
    TaskStatus,
    WorkflowStatus,
)

# ---------------------------------------------------------------------------
# Permission enforcement
# ---------------------------------------------------------------------------


class PermissionDenied(Exception):
    """Raised when an action is not permitted by the governance layer."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BudgetExceeded(Exception):
    """Raised when a budget limit would be exceeded."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class QualityBelowSLA(Exception):
    """Raised when output quality does not meet the SLA threshold."""

    def __init__(self, message: str, score: float, threshold: float):
        self.message = message
        self.score = score
        self.threshold = threshold
        super().__init__(message)


def check_permission(
    agent: Agent,
    action: str,
    *,
    user_role: str = "viewer",
) -> bool:
    """Check whether the agent's permission level allows the given action.

    Returns True if permitted, raises PermissionDenied otherwise.
    """
    try:
        level = agent.permission_level

        if not agent.is_enabled:
            raise PermissionDenied(f"Agent '{agent.name}' is currently disabled.")

        if action == "execute_auto":
            if level in (PermissionLevel.DRAFT_ONLY, PermissionLevel.SUGGEST):
                raise PermissionDenied(
                    f"Agent '{agent.name}' has permission level '{level.value}' "
                    "which does not allow autonomous execution."
                )
            if level == PermissionLevel.AUTO_EXECUTE_HIGH and user_role not in ("admin", "owner"):
                raise PermissionDenied("Auto-execute (high risk) requires admin or owner role.")
            if level == PermissionLevel.FULL_AUTONOMOUS and user_role not in ("admin", "owner"):
                raise PermissionDenied("Full autonomous requires admin or owner role.")

        if action == "approve":
            # Draft-only and suggest both require human approval
            if level in (
                PermissionLevel.AUTO_EXECUTE_LOW,
                PermissionLevel.AUTO_EXECUTE_HIGH,
                PermissionLevel.FULL_AUTONOMOUS,
            ):
                # Auto-approve is valid
                pass

        return True
    except PermissionDenied:
        raise
    except (AttributeError, TypeError):
        logger.exception(
            "Permission check failed for agent '%s' action '%s' (role=%s) — denying by default",
            agent.name,
            action,
            user_role,
        )
        return False  # Fail closed: deny permission on error


def requires_approval(agent: Agent) -> bool:
    """Check whether tasks from this agent need explicit human approval."""
    return agent.permission_level in (
        PermissionLevel.DRAFT_ONLY,
        PermissionLevel.SUGGEST,
    )


# ---------------------------------------------------------------------------
# Budget checking
# ---------------------------------------------------------------------------


async def check_budget(
    db: AsyncSession,
    agent: Agent,
    estimated_tokens: int = 0,
    estimated_cost: float = 0.0,
) -> AgentBudget:
    """Check if the agent's budget allows the estimated usage.

    Returns the budget record, raises BudgetExceeded if over limit.
    Also handles daily/monthly reset logic.
    """
    result = await db.execute(select(AgentBudget).where(AgentBudget.agent_id == agent.id))
    budget = result.scalar_one_or_none()

    if budget is None:
        # Create a default budget
        budget = AgentBudget(
            org_id=agent.org_id,
            agent_id=agent.id,
        )
        db.add(budget)
        await db.flush()
        await db.refresh(budget)

    now = datetime.now(UTC)

    # Helper: ensure datetime is timezone-aware (SQLite strips tzinfo)
    def _aware(dt: datetime | None) -> datetime | None:
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    # Daily reset
    last_daily = _aware(budget.last_reset_daily)
    if last_daily is None or (now - last_daily) > timedelta(days=1):
        budget.tokens_used_today = 0
        budget.usd_used_today = 0.0
        budget.last_reset_daily = now

    # Monthly reset
    last_monthly = _aware(budget.last_reset_monthly)
    if last_monthly is None or (now - last_monthly) > timedelta(days=30):
        budget.usd_used_this_month = 0.0
        budget.last_reset_monthly = now

    # Check daily token limit
    if budget.daily_token_limit > 0:
        if budget.tokens_used_today + estimated_tokens > budget.daily_token_limit:
            raise BudgetExceeded(
                f"Daily token limit exceeded. Used: {budget.tokens_used_today}, "
                f"Limit: {budget.daily_token_limit}, Estimated: {estimated_tokens}"
            )

    # Check daily USD limit
    if budget.daily_usd_limit > 0:
        if budget.usd_used_today + estimated_cost > budget.daily_usd_limit:
            raise BudgetExceeded(
                f"Daily USD limit exceeded. Used: ${budget.usd_used_today:.4f}, "
                f"Limit: ${budget.daily_usd_limit:.2f}, Estimated: ${estimated_cost:.4f}"
            )

    # Check monthly USD limit
    if budget.monthly_usd_limit > 0:
        if budget.usd_used_this_month + estimated_cost > budget.monthly_usd_limit:
            raise BudgetExceeded(
                f"Monthly USD limit exceeded. Used: ${budget.usd_used_this_month:.4f}, "
                f"Limit: ${budget.monthly_usd_limit:.2f}, Estimated: ${estimated_cost:.4f}"
            )

    await db.flush()
    return budget


async def record_usage(
    db: AsyncSession,
    agent_id: uuid.UUID,
    tokens_used: int,
    cost_usd: float,
) -> AgentBudget:
    """Record token/cost usage against the agent's budget."""
    result = await db.execute(select(AgentBudget).where(AgentBudget.agent_id == agent_id))
    budget = result.scalar_one_or_none()

    if budget is None:
        return budget  # type: ignore[return-value]

    budget.tokens_used_today += tokens_used
    budget.usd_used_today += cost_usd
    budget.usd_used_this_month += cost_usd
    budget.total_tokens_used += tokens_used
    budget.total_usd_used += cost_usd

    await db.flush()
    return budget


# ---------------------------------------------------------------------------
# Quality SLA validation
# ---------------------------------------------------------------------------

DEFAULT_QUALITY_THRESHOLD = 0.7


def validate_quality(
    quality_score: float,
    threshold: float = DEFAULT_QUALITY_THRESHOLD,
) -> bool:
    """Validate that output quality meets the SLA threshold.

    Returns True if quality is acceptable, raises QualityBelowSLA otherwise.
    """
    if quality_score < threshold:
        raise QualityBelowSLA(
            f"Quality score {quality_score:.2f} is below threshold {threshold:.2f}",
            score=quality_score,
            threshold=threshold,
        )
    return True


# ---------------------------------------------------------------------------
# Emergency stop
# ---------------------------------------------------------------------------


async def emergency_stop(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    ip_address: str | None = None,
) -> tuple[int, int]:
    """Cancel all running tasks and workflows for an organization.

    Returns (tasks_cancelled, workflows_cancelled).
    """
    # Cancel running tasks
    task_result = await db.execute(
        update(AgentTask)
        .where(
            AgentTask.org_id == org_id,
            AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.AWAITING_APPROVAL]),
        )
        .values(
            status=TaskStatus.CANCELLED,
            error_message="Emergency stop activated",
            completed_at=datetime.now(UTC),
        )
        .returning(AgentTask.id)
    )
    cancelled_tasks = len(task_result.all())

    # Cancel running workflows
    wf_result = await db.execute(
        update(AgentWorkflow)
        .where(
            AgentWorkflow.org_id == org_id,
            AgentWorkflow.status.in_([WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]),
        )
        .values(
            status=WorkflowStatus.CANCELLED,
            error_message="Emergency stop activated",
            completed_at=datetime.now(UTC),
        )
        .returning(AgentWorkflow.id)
    )
    cancelled_workflows = len(wf_result.all())

    # Audit the emergency stop
    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.EMERGENCY_STOP,
        actor_id=actor_id,
        actor_type="user",
        resource_type="organization",
        resource_id=org_id,
        details={
            "tasks_cancelled": cancelled_tasks,
            "workflows_cancelled": cancelled_workflows,
        },
        ip_address=ip_address,
    )

    await db.flush()
    return cancelled_tasks, cancelled_workflows
