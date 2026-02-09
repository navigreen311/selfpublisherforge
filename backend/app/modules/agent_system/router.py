"""FastAPI router for the AI Agent System.

All endpoints under /api/v1/agents.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user, require_role

from app.modules.agent_system import service
from app.modules.agent_system.governance import (
    BudgetExceeded,
    PermissionDenied,
    emergency_stop as gov_emergency_stop,
)
from app.modules.agent_system.audit import list_audit_entries
from app.modules.agent_system.models import (
    AuditAction,
    TaskPriority,
    TaskStatus,
)
from app.modules.agent_system.schemas import (
    AgentConfigUpdate,
    AgentListResponse,
    AgentResponse,
    AuditEntry,
    AuditListResponse,
    BudgetListResponse,
    BudgetStatus,
    BudgetUpdate,
    EmergencyStopResponse,
    MessageResponse,
    TaskApproveRequest,
    TaskCancelRequest,
    TaskCreate,
    TaskListResponse,
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
        (budget.tokens_used_today / budget.daily_token_limit * 100)
        if budget.daily_token_limit > 0
        else 0.0
    )
    daily_usd_pct = (
        (budget.usd_used_today / budget.daily_usd_limit * 100)
        if budget.daily_usd_limit > 0
        else 0.0
    )
    monthly_usd_pct = (
        (budget.usd_used_this_month / budget.monthly_usd_limit * 100)
        if budget.monthly_usd_limit > 0
        else 0.0
    )
    return {
        "daily_token_pct": round(daily_token_pct, 2),
        "daily_usd_pct": round(daily_usd_pct, 2),
        "monthly_usd_pct": round(monthly_usd_pct, 2),
    }


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=AgentListResponse)
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


@router.get("/{agent_id}/config", response_model=AgentResponse)
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


@router.patch("/{agent_id}/config", response_model=AgentResponse)
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


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/tasks", response_model=TaskListResponse)
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


@router.get("/tasks/{task_id}", response_model=TaskResponse)
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


@router.post("/tasks/{task_id}/approve", response_model=TaskResponse)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/reject", response_model=TaskResponse)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/workflows", response_model=WorkflowListResponse)
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


@router.get("/budgets", response_model=BudgetListResponse)
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


@router.patch("/budgets", response_model=BudgetStatus)
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


@router.post("/emergency-stop", response_model=EmergencyStopResponse)
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


@router.get("/audit", response_model=AuditListResponse)
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
