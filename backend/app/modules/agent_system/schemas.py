"""Pydantic v2 schemas for the AI Agent System."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.agent_system.models import (
    AgentType,
    AuditAction,
    PermissionLevel,
    TaskPriority,
    TaskStatus,
    WorkflowStatus,
    WorkflowStepStatus,
)


# ---------------------------------------------------------------------------
# Agent schemas
# ---------------------------------------------------------------------------

class AgentBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., min_length=1, max_length=255)
    agent_type: AgentType
    description: str | None = None
    is_enabled: bool = True
    permission_level: PermissionLevel = PermissionLevel.DRAFT_ONLY
    model_id: str = "claude-sonnet-4-5-20250929"
    system_prompt: str | None = None
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    config: dict[str, Any] | None = None


class AgentCreate(AgentBase):
    """Request body for creating a new AI agent. Inherits all fields from AgentBase."""


class AgentConfigUpdate(BaseModel):
    """Partial update for agent configuration."""
    model_config = ConfigDict(protected_namespaces=())

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None
    permission_level: PermissionLevel | None = None
    model_id: str | None = None
    system_prompt: str | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=200000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    config: dict[str, Any] | None = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total_count: int


# ---------------------------------------------------------------------------
# Task schemas
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    agent_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    input_data: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    agent_id: UUID
    workflow_id: UUID | None = None
    workflow_step_index: int | None = None
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    quality_score: float | None = None
    created_by: UUID
    approved_by: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None


class TaskApproveRequest(BaseModel):
    feedback: str | None = None


class TaskRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)
    regenerate: bool = False


class TaskCancelRequest(BaseModel):
    reason: str | None = None


class TaskListParams(BaseModel):
    status: TaskStatus | None = None
    agent_id: UUID | None = None
    priority: TaskPriority | None = None
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Workflow schemas
# ---------------------------------------------------------------------------

class WorkflowStepDefinition(BaseModel):
    agent_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    input_data: dict[str, Any] | None = None
    condition: str | None = None  # Optional condition expression for branching
    on_failure: str = "stop"  # "stop" | "skip" | "retry"
    max_retries: int = Field(default=0, ge=0, le=5)


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    steps: list[WorkflowStepDefinition] = Field(..., min_length=1)


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    description: str | None = None
    status: WorkflowStatus
    steps: list[dict[str, Any]]
    current_step_index: int = 0
    context: dict[str, Any] | None = None
    error_message: str | None = None
    created_by: UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowListResponse(BaseModel):
    items: list[WorkflowResponse]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None


# ---------------------------------------------------------------------------
# Budget schemas
# ---------------------------------------------------------------------------

class BudgetUpdate(BaseModel):
    daily_token_limit: int | None = Field(default=None, ge=0)
    daily_usd_limit: float | None = Field(default=None, ge=0.0)
    monthly_usd_limit: float | None = Field(default=None, ge=0.0)


class BudgetStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    agent_id: UUID
    daily_token_limit: int
    daily_usd_limit: float
    monthly_usd_limit: float
    tokens_used_today: int
    usd_used_today: float
    usd_used_this_month: float
    total_tokens_used: int
    total_usd_used: float
    last_reset_daily: datetime | None = None
    last_reset_monthly: datetime | None = None
    daily_token_pct: float = 0.0
    daily_usd_pct: float = 0.0
    monthly_usd_pct: float = 0.0


class BudgetListResponse(BaseModel):
    items: list[BudgetStatus]


# ---------------------------------------------------------------------------
# Audit schemas
# ---------------------------------------------------------------------------

class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    action: AuditAction
    actor_id: UUID
    actor_type: str
    resource_type: str
    resource_id: UUID
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEntry]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None


class AuditListParams(BaseModel):
    action: AuditAction | None = None
    actor_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Emergency stop
# ---------------------------------------------------------------------------

class EmergencyStopResponse(BaseModel):
    tasks_cancelled: int
    workflows_cancelled: int
    message: str


# ---------------------------------------------------------------------------
# Generic message
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str
