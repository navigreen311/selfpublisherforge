"""Service layer for the AI Agent System.

Agent CRUD, task execution orchestration, workflow management, and budget
operations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.agent_system.audit import record_audit
from app.modules.agent_system.executor import TaskExecutor
from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    AgentWorkflow,
    AuditAction,
    PermissionLevel,
    TaskPriority,
    TaskStatus,
    WorkflowStatus,
)
from app.modules.agent_system.schemas import (
    AgentConfigUpdate,
    BudgetUpdate,
    TaskApproveRequest,
    TaskCreate,
    TaskRejectRequest,
    WorkflowCreate,
)
from app.modules.agent_system.workflow_engine import WorkflowEngine

# ---------------------------------------------------------------------------
# Default agent definitions (seeded per-org on first access)
# ---------------------------------------------------------------------------

DEFAULT_AGENTS: list[dict[str, Any]] = [
    {
        "agent_type": AgentType.RESEARCH,
        "name": "Research Agent",
        "description": "Market research, competitor analysis, keyword discovery",
        "permission_level": PermissionLevel.DRAFT_ONLY,
        "system_prompt": (
            "You are a research agent for self-publishers. Provide thorough, "
            "data-driven analysis on market trends, competitor strategies, and "
            "keyword opportunities."
        ),
    },
    {
        "agent_type": AgentType.WRITING_ASSISTANT,
        "name": "Writing Assistant Agent",
        "description": "Drafting, continuation, editing suggestions",
        "permission_level": PermissionLevel.SUGGEST,
        "system_prompt": (
            "You are a writing assistant for self-publishers. Help with "
            "drafting chapters, continuing narratives, and suggesting edits."
        ),
    },
    {
        "agent_type": AgentType.EDITOR,
        "name": "Editor Agent",
        "description": "Grammar, style, consistency checking",
        "permission_level": PermissionLevel.SUGGEST,
        "system_prompt": (
            "You are a professional editor. Check for grammar, style, "
            "consistency, and readability issues. Provide detailed suggestions."
        ),
    },
    {
        "agent_type": AgentType.MARKETING_COPY,
        "name": "Marketing Copy Agent",
        "description": "Blurbs, ad copy, email sequences, social posts",
        "permission_level": PermissionLevel.DRAFT_ONLY,
        "system_prompt": (
            "You are a marketing copywriter for self-publishers. Create "
            "compelling blurbs, ad copy, email sequences, and social media posts."
        ),
    },
]


# ---------------------------------------------------------------------------
# Agent CRUD
# ---------------------------------------------------------------------------


async def ensure_default_agents(db: AsyncSession, org_id: uuid.UUID) -> list[Agent]:
    """Ensure default agents exist for the org. Seed if needed."""
    result = await db.execute(select(Agent).where(Agent.org_id == org_id, Agent.deleted_at.is_(None)))
    agents = list(result.scalars().all())

    if agents:
        return agents

    # Seed defaults
    new_agents: list[Agent] = []
    for defn in DEFAULT_AGENTS:
        agent = Agent(org_id=org_id, **defn)
        db.add(agent)
        new_agents.append(agent)

    await db.flush()
    for a in new_agents:
        await db.refresh(a)
    return new_agents


async def list_agents(db: AsyncSession, org_id: uuid.UUID) -> list[Agent]:
    """List all non-deleted agents for the org, seeding defaults if needed."""
    return await ensure_default_agents(db, org_id)


async def get_agent(db: AsyncSession, agent_id: uuid.UUID, org_id: uuid.UUID) -> Agent:
    """Get a single agent by ID."""
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.org_id == org_id,
            Agent.deleted_at.is_(None),
        )
    )
    agent = result.scalar_one_or_none()
    if agent is None:
        raise AppException(
            status_code=404,
            code="AGENT_NOT_FOUND",
            message=f"Agent {agent_id} not found",
        )
    return agent


async def update_agent_config(
    db: AsyncSession,
    agent_id: uuid.UUID,
    org_id: uuid.UUID,
    updates: AgentConfigUpdate,
    actor_id: uuid.UUID,
    ip_address: str | None = None,
) -> Agent:
    """Update agent configuration."""
    agent = await get_agent(db, agent_id, org_id)

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.flush()
    await db.refresh(agent)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.CONFIG_UPDATED,
        actor_id=actor_id,
        resource_type="agent",
        resource_id=agent_id,
        details={"updates": update_data},
        ip_address=ip_address,
    )

    return agent


# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------


async def create_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    payload: TaskCreate,
    created_by: uuid.UUID,
    ip_address: str | None = None,
) -> AgentTask:
    """Create a new agent task."""
    task = AgentTask(
        org_id=org_id,
        agent_id=payload.agent_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        input_data=payload.input_data,
        created_by=created_by,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.TASK_CREATED,
        actor_id=created_by,
        resource_type="agent_task",
        resource_id=task.id,
        details={"agent_id": str(payload.agent_id), "title": payload.title},
        ip_address=ip_address,
    )

    return task


async def list_tasks(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    status: TaskStatus | None = None,
    agent_id: uuid.UUID | None = None,
    priority: TaskPriority | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[AgentTask], str | None, bool, int]:
    """List tasks with optional filters. Returns (items, next_cursor, has_more, total)."""
    # Count
    count_q = (
        select(func.count()).select_from(AgentTask).where(AgentTask.org_id == org_id, AgentTask.deleted_at.is_(None))
    )
    if status:
        count_q = count_q.where(AgentTask.status == status)
    if agent_id:
        count_q = count_q.where(AgentTask.agent_id == agent_id)
    if priority:
        count_q = count_q.where(AgentTask.priority == priority)

    total_result = await db.execute(count_q)
    total_count = total_result.scalar() or 0

    # Data
    query = (
        select(AgentTask)
        .where(AgentTask.org_id == org_id, AgentTask.deleted_at.is_(None))
        .order_by(desc(AgentTask.created_at))
    )
    if status:
        query = query.where(AgentTask.status == status)
    if agent_id:
        query = query.where(AgentTask.agent_id == agent_id)
    if priority:
        query = query.where(AgentTask.priority == priority)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(AgentTask.created_at < cursor_dt)
        except ValueError:
            logger.warning("Invalid status value encountered: %s", cursor)

    query = query.limit(limit + 1)
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    has_more = len(tasks) > limit
    if has_more:
        tasks = tasks[:limit]

    next_cursor = None
    if has_more and tasks:
        next_cursor = tasks[-1].created_at.isoformat()

    return tasks, next_cursor, has_more, total_count


async def get_task(db: AsyncSession, task_id: uuid.UUID, org_id: uuid.UUID) -> AgentTask:
    """Get a single task by ID."""
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.id == task_id,
            AgentTask.org_id == org_id,
            AgentTask.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise AppException(
            status_code=404,
            code="TASK_NOT_FOUND",
            message=f"Task {task_id} not found",
        )
    return task


async def approve_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
    approved_by: uuid.UUID,
    payload: TaskApproveRequest,
    ip_address: str | None = None,
) -> AgentTask:
    """Approve a task that is awaiting approval."""
    task = await get_task(db, task_id, org_id)

    if task.status != TaskStatus.AWAITING_APPROVAL:
        raise ValueError(f"Task is not awaiting approval (status: {task.status.value})")

    task.status = TaskStatus.APPROVED
    task.approved_by = approved_by
    task.completed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(task)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.TASK_APPROVED,
        actor_id=approved_by,
        resource_type="agent_task",
        resource_id=task_id,
        details={"feedback": payload.feedback},
        ip_address=ip_address,
    )

    return task


async def reject_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
    rejected_by: uuid.UUID,
    payload: TaskRejectRequest,
    ip_address: str | None = None,
) -> AgentTask:
    """Reject a task, optionally requesting regeneration."""
    task = await get_task(db, task_id, org_id)

    if task.status != TaskStatus.AWAITING_APPROVAL:
        raise ValueError(f"Task is not awaiting approval (status: {task.status.value})")

    task.status = TaskStatus.REJECTED
    task.completed_at = datetime.now(UTC)
    task.error_message = f"Rejected: {payload.reason}"
    await db.flush()
    await db.refresh(task)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.TASK_REJECTED,
        actor_id=rejected_by,
        resource_type="agent_task",
        resource_id=task_id,
        details={"reason": payload.reason, "regenerate": payload.regenerate},
        ip_address=ip_address,
    )

    # If regenerate requested, create a new task
    if payload.regenerate:
        new_task = AgentTask(
            org_id=task.org_id,
            agent_id=task.agent_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            input_data=task.input_data,
            created_by=rejected_by,
        )
        db.add(new_task)
        await db.flush()
        await db.refresh(new_task)
        return new_task

    return task


async def cancel_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
    cancelled_by: uuid.UUID,
    reason: str | None = None,
    ip_address: str | None = None,
) -> AgentTask:
    """Cancel a running or pending task."""
    task = await get_task(db, task_id, org_id)

    if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.AWAITING_APPROVAL):
        raise ValueError(f"Cannot cancel task in status '{task.status.value}'")

    task.status = TaskStatus.CANCELLED
    task.error_message = f"Cancelled: {reason}" if reason else "Cancelled by user"
    task.completed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(task)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.TASK_CANCELLED,
        actor_id=cancelled_by,
        resource_type="agent_task",
        resource_id=task_id,
        details={"reason": reason},
        ip_address=ip_address,
    )

    return task


# ---------------------------------------------------------------------------
# Workflow management
# ---------------------------------------------------------------------------


async def create_workflow(
    db: AsyncSession,
    org_id: uuid.UUID,
    payload: WorkflowCreate,
    created_by: uuid.UUID,
    ip_address: str | None = None,
) -> AgentWorkflow:
    """Create a new multi-step workflow."""
    steps_data = []
    for step in payload.steps:
        step_dict = step.model_dump()
        step_dict["agent_id"] = str(step.agent_id)
        step_dict["status"] = "pending"
        steps_data.append(step_dict)

    workflow = AgentWorkflow(
        org_id=org_id,
        name=payload.name,
        description=payload.description,
        steps=steps_data,
        created_by=created_by,
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.WORKFLOW_CREATED,
        actor_id=created_by,
        resource_type="agent_workflow",
        resource_id=workflow.id,
        details={"name": payload.name, "step_count": len(payload.steps)},
        ip_address=ip_address,
    )

    return workflow


async def list_workflows(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[AgentWorkflow], str | None, bool, int]:
    """List workflows for the org."""
    count_q = (
        select(func.count())
        .select_from(AgentWorkflow)
        .where(AgentWorkflow.org_id == org_id, AgentWorkflow.deleted_at.is_(None))
    )
    total_result = await db.execute(count_q)
    total_count = total_result.scalar() or 0

    query = (
        select(AgentWorkflow)
        .where(AgentWorkflow.org_id == org_id, AgentWorkflow.deleted_at.is_(None))
        .order_by(desc(AgentWorkflow.created_at))
    )
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(AgentWorkflow.created_at < cursor_dt)
        except ValueError:
            logger.warning("Invalid status value encountered: %s", cursor)

    query = query.limit(limit + 1)
    result = await db.execute(query)
    workflows = list(result.scalars().all())

    has_more = len(workflows) > limit
    if has_more:
        workflows = workflows[:limit]

    next_cursor = None
    if has_more and workflows:
        next_cursor = workflows[-1].created_at.isoformat()

    return workflows, next_cursor, has_more, total_count


async def get_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    org_id: uuid.UUID,
) -> AgentWorkflow:
    """Get a single workflow by ID."""
    result = await db.execute(
        select(AgentWorkflow).where(
            AgentWorkflow.id == workflow_id,
            AgentWorkflow.org_id == org_id,
            AgentWorkflow.deleted_at.is_(None),
        )
    )
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise AppException(
            status_code=404,
            code="WORKFLOW_NOT_FOUND",
            message=f"Workflow {workflow_id} not found",
        )
    return workflow


# ---------------------------------------------------------------------------
# Budget management
# ---------------------------------------------------------------------------


async def get_budgets(db: AsyncSession, org_id: uuid.UUID) -> list[AgentBudget]:
    """Get all budget records for the org."""
    result = await db.execute(select(AgentBudget).where(AgentBudget.org_id == org_id))
    return list(result.scalars().all())


async def update_budget(
    db: AsyncSession,
    org_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: BudgetUpdate,
    actor_id: uuid.UUID,
    ip_address: str | None = None,
) -> AgentBudget:
    """Update budget limits for a specific agent."""
    result = await db.execute(
        select(AgentBudget).where(
            AgentBudget.agent_id == agent_id,
            AgentBudget.org_id == org_id,
        )
    )
    budget = result.scalar_one_or_none()

    if budget is None:
        # Create a new budget with the provided limits
        budget = AgentBudget(
            org_id=org_id,
            agent_id=agent_id,
        )
        db.add(budget)
        await db.flush()

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    await db.flush()
    await db.refresh(budget)

    await record_audit(
        db,
        org_id=org_id,
        action=AuditAction.BUDGET_UPDATED,
        actor_id=actor_id,
        resource_type="agent_budget",
        resource_id=budget.id,
        details={"agent_id": str(agent_id), "updates": update_data},
        ip_address=ip_address,
    )

    return budget


# ---------------------------------------------------------------------------
# Execute task (sync entry point)
# ---------------------------------------------------------------------------


async def execute_task(
    db: AsyncSession,
    task: AgentTask,
    *,
    user_role: str = "viewer",
    ip_address: str | None = None,
) -> AgentTask:
    """Execute a task via the TaskExecutor."""
    executor = TaskExecutor(db)
    return await executor.execute(task, user_role=user_role, ip_address=ip_address)


async def execute_workflow(
    db: AsyncSession,
    workflow: AgentWorkflow,
    *,
    user_role: str = "viewer",
    ip_address: str | None = None,
) -> AgentWorkflow:
    """Start or resume a workflow via the WorkflowEngine."""
    engine = WorkflowEngine(db)
    if workflow.status == WorkflowStatus.DRAFT:
        return await engine.start_workflow(workflow, user_role=user_role, ip_address=ip_address)
    return await engine.resume_workflow(workflow, user_role=user_role, ip_address=ip_address)
