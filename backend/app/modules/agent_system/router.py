"""FastAPI router for the AI Agent System.

All endpoints under /api/v1/agents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.agent_system import service
from app.modules.agent_system.audit import list_audit_entries, record_audit
from app.modules.agent_system.governance import (
    emergency_stop as gov_emergency_stop,
)
from app.modules.agent_system.models import (
    AuditAction,
    TaskPriority,
    TaskStatus,
)
from app.modules.agent_system.schemas import (
    AgentConfigUpdate,
    AgentConfigureRequest,
    AgentListResponse,
    AgentResponse,
    AgentUsageResponse,
    AuditEntry,
    AuditListResponse,
    BudgetListResponse,
    BudgetStatus,
    BudgetUpdate,
    CustomAgentCreateRequest,
    EmergencyStopResponse,
    TaskApproveRequest,
    TaskCancelRequest,
    TaskCreate,
    TaskCreateRequest,
    TaskExecutionResponse,
    TaskListResponse,
    TaskRateRequest,
    TaskRejectRequest,
    TaskResponse,
    WorkflowCreate,
    WorkflowListResponse,
    WorkflowResponse,
)

router = APIRouter()


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from the request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _compute_budget_pcts(budget) -> dict:
    """Compute percentage fields for a budget."""
    daily_token_pct = (
        (budget.tokens_used_today / budget.daily_token_limit * 100) if budget.daily_token_limit > 0 else 0.0
    )
    daily_usd_pct = (budget.usd_used_today / budget.daily_usd_limit * 100) if budget.daily_usd_limit > 0 else 0.0
    monthly_usd_pct = (
        (budget.usd_used_this_month / budget.monthly_usd_limit * 100) if budget.monthly_usd_limit > 0 else 0.0
    )
    return {
        "daily_token_pct": round(daily_token_pct, 2),
        "daily_usd_pct": round(daily_usd_pct, 2),
        "monthly_usd_pct": round(monthly_usd_pct, 2),
    }


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List agents",
    description="List available AI agent types for the organization.",
)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List available agent types for the organization."""
    agents = await service.list_agents(db, current_user["org_id"])
    return AgentListResponse(
        items=[AgentResponse.model_validate(a) for a in agents],
        total_count=len(agents),
    )


@router.get(
    "/{agent_id}/config",
    response_model=AgentResponse,
    summary="Get agent config",
    description="Get configuration details for a specific agent.",
)
async def get_agent_config(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get agent configuration."""
    agent = await service.get_agent(db, agent_id, current_user["org_id"])
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.patch(
    "/{agent_id}/config",
    response_model=AgentResponse,
    summary="Update agent config",
    description="Update agent configuration including permissions, model, and budget. Requires admin or owner role.",
)
async def update_agent_config(
    agent_id: UUID,
    payload: AgentConfigUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "owner")),
):
    """Update agent configuration (permissions, model, budget)."""
    agent = await service.update_agent_config(
        db,
        agent_id,
        current_user["org_id"],
        payload,
        actor_id=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return AgentResponse.model_validate(agent)


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent task",
    description="Create a new task for an AI agent to execute.",
)
async def create_task(
    payload: TaskCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new agent task."""
    # Verify agent exists
    agent = await service.get_agent(db, payload.agent_id, current_user["org_id"])
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    task = await service.create_task(
        db,
        current_user["org_id"],
        payload,
        created_by=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )
    return TaskResponse.model_validate(task)


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="List agent tasks",
    description="List tasks with optional filters by status, agent, and priority.",
)
async def list_tasks(
    status_filter: TaskStatus | None = Query(None, alias="status"),
    agent_id: UUID | None = Query(None),
    priority: TaskPriority | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List tasks with optional filters."""
    tasks, next_cursor, has_more, total = await service.list_tasks(
        db,
        current_user["org_id"],
        status=status_filter,
        agent_id=agent_id,
        priority=priority,
        cursor=cursor,
        limit=limit,
    )
    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task detail",
    description="Get task detail including input, output, and execution metadata.",
)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get task detail with input/output."""
    task = await service.get_task(db, task_id, current_user["org_id"])
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post(
    "/tasks/{task_id}/approve",
    response_model=TaskResponse,
    summary="Approve task output",
    description="Approve an agent task's output for use.",
)
async def approve_task(
    task_id: UUID,
    payload: TaskApproveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve task output."""
    try:
        task = await service.approve_task(
            db,
            task_id,
            current_user["org_id"],
            approved_by=current_user["user_id"],
            payload=payload,
            ip_address=_get_client_ip(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post(
    "/tasks/{task_id}/reject",
    response_model=TaskResponse,
    summary="Reject task output",
    description="Reject a task's output and optionally request regeneration.",
)
async def reject_task(
    task_id: UUID,
    payload: TaskRejectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reject and optionally regenerate."""
    try:
        task = await service.reject_task(
            db,
            task_id,
            current_user["org_id"],
            rejected_by=current_user["user_id"],
            payload=payload,
            ip_address=_get_client_ip(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskResponse,
    summary="Cancel task",
    description="Cancel a running or pending agent task.",
)
async def cancel_task(
    task_id: UUID,
    payload: TaskCancelRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cancel running task."""
    try:
        task = await service.cancel_task(
            db,
            task_id,
            current_user["org_id"],
            cancelled_by=current_user["user_id"],
            reason=payload.reason,
            ip_address=_get_client_ip(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
    description="Create a multi-step agent workflow with dependent tasks.",
)
async def create_workflow(
    payload: WorkflowCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a multi-step workflow."""
    workflow = await service.create_workflow(
        db,
        current_user["org_id"],
        payload,
        created_by=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )
    return WorkflowResponse.model_validate(workflow)


@router.get(
    "/workflows",
    response_model=WorkflowListResponse,
    summary="List workflows",
    description="List agent workflows with pagination.",
)
async def list_workflows(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List workflows."""
    workflows, next_cursor, has_more, total = await service.list_workflows(
        db,
        current_user["org_id"],
        cursor=cursor,
        limit=limit,
    )
    return WorkflowListResponse(
        items=[WorkflowResponse.model_validate(w) for w in workflows],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total,
    )


# ---------------------------------------------------------------------------
# Budget endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/budgets",
    response_model=BudgetListResponse,
    summary="Get agent budgets",
    description="Get budget status (token/USD limits and usage) for all agents.",
)
async def get_budgets(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get budget status (token/USD/daily) for all agents."""
    budgets = await service.get_budgets(db, current_user["org_id"])
    items = []
    for b in budgets:
        pcts = _compute_budget_pcts(b)
        item = BudgetStatus.model_validate(b)
        item.daily_token_pct = pcts["daily_token_pct"]
        item.daily_usd_pct = pcts["daily_usd_pct"]
        item.monthly_usd_pct = pcts["monthly_usd_pct"]
        items.append(item)
    return BudgetListResponse(items=items)


@router.patch(
    "/budgets",
    response_model=BudgetStatus,
    summary="Update agent budget",
    description="Update budget limits for a specific agent. Requires admin or owner role.",
)
async def update_budgets(
    agent_id: UUID = Query(...),
    payload: BudgetUpdate = ...,
    request: Request = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "owner")),
):
    """Update budget limits for a specific agent."""
    budget = await service.update_budget(
        db,
        current_user["org_id"],
        agent_id,
        payload,
        actor_id=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    result = BudgetStatus.model_validate(budget)
    pcts = _compute_budget_pcts(budget)
    result.daily_token_pct = pcts["daily_token_pct"]
    result.daily_usd_pct = pcts["daily_usd_pct"]
    result.monthly_usd_pct = pcts["monthly_usd_pct"]
    return result


# ---------------------------------------------------------------------------
# Emergency stop
# ---------------------------------------------------------------------------


@router.post(
    "/emergency-stop",
    response_model=EmergencyStopResponse,
    summary="Emergency stop all agents",
    description="Immediately cancel all running tasks and workflows. Requires admin or owner role.",
)
async def emergency_stop(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "owner")),
):
    """Emergency stop all running tasks and workflows."""
    tasks_cancelled, workflows_cancelled = await gov_emergency_stop(
        db,
        current_user["org_id"],
        actor_id=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )
    return EmergencyStopResponse(
        tasks_cancelled=tasks_cancelled,
        workflows_cancelled=workflows_cancelled,
        message=f"Emergency stop complete. {tasks_cancelled} tasks and {workflows_cancelled} workflows cancelled.",
    )


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


@router.get(
    "/audit",
    response_model=AuditListResponse,
    summary="Get audit trail",
    description="Get paginated audit trail of agent actions with optional filters.",
)
async def get_audit_trail(
    action: AuditAction | None = Query(None),
    actor_id: UUID | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get paginated audit trail."""
    entries, next_cursor, has_more, total = await list_audit_entries(
        db,
        org_id=current_user["org_id"],
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        cursor=cursor,
        limit=limit,
    )
    return AuditListResponse(
        items=[AuditEntry.model_validate(e) for e in entries],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total,
    )


# ---------------------------------------------------------------------------
# Extended task execution endpoints (Worker 02)
# ---------------------------------------------------------------------------


@router.post(
    "/agents/{agent_id}/tasks",
    response_model=TaskExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and run a task",
    description="Create a new task for a specific agent and begin execution.",
)
async def create_agent_task(
    agent_id: UUID,
    payload: TaskCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Create and execute a task for a specific agent."""
    from app.modules.agent_system.task_runner import execute_task

    # Verify agent exists
    agent = await service.get_agent(db, agent_id, current_user["org_id"])
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Create the task
    task_create = TaskCreate(
        agent_id=agent_id,
        title=payload.task_type,
        description=payload.instructions,
        priority=TaskPriority.MEDIUM if payload.priority == "normal" else TaskPriority.HIGH,
        input_data={
            "task_type": payload.task_type,
            "book_id": str(payload.book_id) if payload.book_id else None,
            "instructions": payload.instructions,
            "execution_mode": payload.execution_mode,
            "max_tokens": payload.max_tokens,
        },
    )

    task = await service.create_task(
        db,
        current_user["org_id"],
        task_create,
        created_by=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )

    # Execute the task
    result = await execute_task(db, task, agent)

    return TaskExecutionResponse(
        task_id=result["task_id"],
        status=result["status"],
        progress=result["progress"],
        steps=result["steps"],
        output=result.get("output"),
        tokens_used=result["tokens_used"],
        cost=result["cost"],
        execution_time_seconds=result.get("execution_time_seconds"),
    )


@router.post(
    "/agents/tasks/{task_id}/regenerate",
    response_model=TaskExecutionResponse,
    summary="Regenerate task output",
    description="Re-run a task to generate new output.",
)
async def regenerate_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Regenerate task output."""
    from app.modules.agent_system.task_runner import execute_task

    task = await service.get_task(db, task_id, current_user["org_id"])
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    agent = await service.get_agent(db, task.agent_id, current_user["org_id"])
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Reset task status and re-execute
    task.status = TaskStatus.PENDING
    task.output_data = None
    await db.commit()

    result = await execute_task(db, task, agent)

    return TaskExecutionResponse(
        task_id=result["task_id"],
        status=result["status"],
        progress=result["progress"],
        steps=result["steps"],
        output=result.get("output"),
        tokens_used=result["tokens_used"],
        cost=result["cost"],
        execution_time_seconds=result.get("execution_time_seconds"),
    )


@router.post(
    "/agents/tasks/{task_id}/rate",
    response_model=TaskResponse,
    summary="Rate task output",
    description="Rate the quality of a task's output (1-5 stars).",
)
async def rate_task(
    task_id: UUID,
    payload: TaskRateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Rate task output quality."""
    task = await service.get_task(db, task_id, current_user["org_id"])
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.quality_score = float(payload.rating)
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.post(
    "/agents/tasks/{task_id}/stop",
    response_model=TaskResponse,
    summary="Stop running task",
    description="Stop a currently running task.",
)
async def stop_running_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Stop a running task."""
    from app.modules.agent_system.task_runner import stop_task

    task = await stop_task(db, task_id, current_user["org_id"])
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return TaskResponse.model_validate(task)


@router.get(
    "/agents/tasks/{task_id}/stream",
    summary="Stream task execution",
    description="Server-Sent Events stream of task execution progress.",
)
async def stream_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Stream task execution progress via SSE."""
    from app.modules.agent_system.task_runner import stream_task_execution

    # Verify task exists
    task = await service.get_task(db, task_id, current_user["org_id"])
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return StreamingResponse(
        stream_task_execution(db, task_id),
        media_type="text/event-stream",
    )


@router.get(
    "/agents/usage",
    response_model=AgentUsageResponse,
    summary="Get usage statistics",
    description="Get agent usage stats including tasks, tokens, and costs.",
)
async def get_agent_usage(
    period: str = Query("30d", description="Time period (e.g., 7d, 30d, 90d)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Get usage statistics for agents."""
    from sqlalchemy import func, select

    from app.modules.agent_system.models import Agent, AgentTask

    # Parse period to days
    days = 30
    if period.endswith("d"):
        days = int(period[:-1])

    # Calculate date threshold
    from datetime import timedelta

    threshold = datetime.now(UTC) - timedelta(days=days)

    # Total tasks
    total_result = await db.execute(
        select(func.count(AgentTask.id)).where(
            AgentTask.org_id == current_user["org_id"],
            AgentTask.created_at >= threshold,
        )
    )
    total_tasks = total_result.scalar_one()

    # Running tasks
    running_result = await db.execute(
        select(func.count(AgentTask.id)).where(
            AgentTask.org_id == current_user["org_id"],
            AgentTask.status == TaskStatus.RUNNING,
        )
    )
    running_tasks = running_result.scalar_one()

    # Total tokens and cost
    usage_result = await db.execute(
        select(
            func.sum(AgentTask.tokens_used),
            func.sum(AgentTask.cost_usd),
        ).where(
            AgentTask.org_id == current_user["org_id"],
            AgentTask.created_at >= threshold,
        )
    )
    total_tokens, total_cost = usage_result.one()
    total_tokens = total_tokens or 0
    total_cost = total_cost or 0.0

    # By agent
    by_agent_result = await db.execute(
        select(
            Agent.name,
            Agent.id,
            func.count(AgentTask.id).label("task_count"),
            func.sum(AgentTask.tokens_used).label("tokens"),
            func.sum(AgentTask.cost_usd).label("cost"),
        )
        .join(AgentTask, Agent.id == AgentTask.agent_id)
        .where(
            AgentTask.org_id == current_user["org_id"],
            AgentTask.created_at >= threshold,
        )
        .group_by(Agent.id, Agent.name)
    )

    by_agent = [
        {
            "agent_name": row.name,
            "agent_id": str(row.id),
            "tasks": row.task_count,
            "tokens": row.tokens or 0,
            "cost": row.cost or 0.0,
        }
        for row in by_agent_result
    ]

    return AgentUsageResponse(
        total_tasks=total_tasks,
        running_tasks=running_tasks,
        total_tokens=total_tokens,
        total_cost=total_cost,
        by_agent=by_agent,
    )


@router.patch(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Configure agent",
    description="Update agent configuration and settings.",
)
async def configure_agent(
    agent_id: UUID,
    payload: AgentConfigureRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Configure agent settings."""
    # Map AgentConfigureRequest to AgentConfigUpdate
    config_update = AgentConfigUpdate(
        name=payload.name,
        description=payload.description,
        system_prompt=payload.system_prompt,
        model_id=payload.model,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
        config={
            "default_execution_mode": payload.default_execution_mode,
            "task_types": payload.task_types,
            "context_sources": payload.context_sources,
            "budget_per_task": payload.budget_per_task,
            "monthly_budget": payload.monthly_budget,
        }
        if any(
            [
                payload.default_execution_mode,
                payload.task_types,
                payload.context_sources,
                payload.budget_per_task,
                payload.monthly_budget,
            ]
        )
        else None,
    )

    agent = await service.update_agent_config(
        db,
        agent_id,
        current_user["org_id"],
        config_update,
        actor_id=current_user["user_id"],
        ip_address=_get_client_ip(request),
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    return AgentResponse.model_validate(agent)


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom agent",
    description="Create a new custom agent with specific capabilities.",
)
async def create_custom_agent(
    payload: CustomAgentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Create a custom agent."""
    from app.modules.agent_system.models import Agent, AgentType

    # Create agent
    agent = Agent(
        org_id=current_user["org_id"],
        agent_type=AgentType.RESEARCH,  # Default to research type for custom agents
        name=payload.name,
        description=payload.description,
        system_prompt=payload.system_prompt,
        model_id=payload.model,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
        config={
            "category": payload.category,
            "icon": payload.icon,
            "task_types": payload.task_types,
            "default_execution_mode": payload.default_execution_mode,
            "is_custom": True,
        },
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # Record audit
    await record_audit(
        db,
        org_id=current_user["org_id"],
        action=AuditAction.CONFIG_UPDATED,
        actor_id=current_user["user_id"],
        actor_type="user",
        resource_type="agent",
        resource_id=agent.id,
        details={"action": "created_custom_agent", "name": payload.name},
        ip_address=_get_client_ip(request),
    )

    return AgentResponse.model_validate(agent)


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete custom agent",
    description="Delete a custom agent (soft delete).",
)
async def delete_custom_agent(
    agent_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("member")),
):
    """Delete a custom agent."""
    agent = await service.get_agent(db, agent_id, current_user["org_id"])
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Only allow deletion of custom agents
    if not agent.config or not agent.config.get("is_custom"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default agents",
        )

    # Soft delete
    agent.deleted_at = datetime.now(UTC)
    await db.commit()

    # Record audit
    await record_audit(
        db,
        org_id=current_user["org_id"],
        action=AuditAction.CONFIG_UPDATED,
        actor_id=current_user["user_id"],
        actor_type="user",
        resource_type="agent",
        resource_id=agent.id,
        details={"action": "deleted_custom_agent", "name": agent.name},
        ip_address=_get_client_ip(request),
    )
