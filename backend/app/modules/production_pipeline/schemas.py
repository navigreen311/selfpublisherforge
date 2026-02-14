"""Pydantic schemas for the Production Pipeline module."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.production_pipeline.models import (
    PipelineStatus,
    TaskStatus,
    TaskType,
)

# ── Task Schemas ──────────────────────────────────────────────────────────


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    type: TaskType = TaskType.WRITING
    assignee_id: uuid.UUID | None = None
    due_date: datetime | None = None
    depends_on: list[str] | None = Field(default_factory=list)
    position: int = 0
    stage_id: uuid.UUID | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    checklist: list[dict] | None = Field(default_factory=list)
    links: list[dict] | None = Field(default_factory=list)
    blocked_by: list[uuid.UUID] | None = Field(default_factory=list)
    metadata_json: dict | None = Field(default_factory=dict)
    order_index: int = 0


class CreateTask(TaskBase):
    """Schema for adding a task to a pipeline. Inherits all fields from TaskBase."""


class UpdateTask(BaseModel):
    """Schema for updating a task (partial)."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    type: TaskType | None = None
    status: TaskStatus | None = None
    assignee_id: uuid.UUID | None = None
    due_date: datetime | None = None
    depends_on: list[str] | None = None
    position: int | None = None
    stage_id: uuid.UUID | None = None
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    checklist: list[dict] | None = None
    links: list[dict] | None = None
    blocked_by: list[uuid.UUID] | None = None
    metadata_json: dict | None = None
    order_index: int | None = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    org_id: uuid.UUID
    status: TaskStatus
    completed_at: datetime | None = None
    stage_id: uuid.UUID | None = None
    priority: str | None = "medium"
    checklist: list[dict] | None = []
    links: list[dict] | None = []
    blocked_by: list[uuid.UUID] | None = []
    metadata_json: dict | None = {}
    order_index: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pipeline Schemas ──────────────────────────────────────────────────────


class PipelineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    book_id: uuid.UUID
    deadline: datetime | None = None
    settings: dict | None = Field(default_factory=dict)
    template: str | None = Field(None, max_length=100)
    target_launch_date: date | None = None


class CreatePipeline(PipelineBase):
    """Schema for creating a new pipeline."""

    template_id: uuid.UUID | None = None


class UpdatePipeline(BaseModel):
    """Schema for updating pipeline settings (partial)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: PipelineStatus | None = None
    deadline: datetime | None = None
    settings: dict | None = None
    template: str | None = Field(None, max_length=100)
    target_launch_date: date | None = None


class PipelineResponse(PipelineBase):
    id: uuid.UUID
    org_id: uuid.UUID
    status: PipelineStatus
    progress_pct: int = 0
    tasks: list[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineSummaryResponse(BaseModel):
    """Lightweight pipeline listing (without full task details)."""

    id: uuid.UUID
    org_id: uuid.UUID
    book_id: uuid.UUID
    name: str
    status: PipelineStatus
    deadline: datetime | None = None
    task_count: int = 0
    completed_task_count: int = 0
    overdue_task_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Timeline Schemas ──────────────────────────────────────────────────────


class TimelineTask(BaseModel):
    """A task represented as a Gantt bar."""

    id: uuid.UUID
    title: str
    type: TaskType
    status: TaskStatus
    assignee_id: uuid.UUID | None = None
    start_date: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    depends_on: list[str] = []
    progress: float = 0.0  # 0.0 – 1.0


class TimelineView(BaseModel):
    """Gantt-style timeline for a pipeline."""

    pipeline_id: uuid.UUID
    pipeline_name: str
    deadline: datetime | None = None
    tasks: list[TimelineTask] = []
    critical_path: list[str] = []  # ordered task IDs on the critical path


# ── Template Schemas ──────────────────────────────────────────────────────


class TaskDefinition(BaseModel):
    """A task blueprint within a template."""

    title: str
    type: TaskType = TaskType.WRITING
    description: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    estimated_days: int = 1
    position: int = 0


class CreateTemplate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    task_definitions: list[TaskDefinition] = Field(default_factory=list)
    settings: dict | None = Field(default_factory=dict)
    is_public: bool = False


class TemplateResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None = None
    task_definitions: list[dict] = []
    settings: dict | None = None
    is_public: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination ────────────────────────────────────────────────────────────


class PaginatedPipelines(BaseModel):
    items: list[PipelineSummaryResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ── Stage Schemas ────────────────────────────────────────────────────────


class StageCreate(BaseModel):
    """Schema for creating a pipeline stage."""

    name: str = Field(..., min_length=1, max_length=255)
    order_index: int = 0
    color: str | None = Field(None, max_length=20)
    start_date: date | None = None
    end_date: date | None = None


class StageUpdate(BaseModel):
    """Schema for updating a stage (partial)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    order_index: int | None = None
    color: str | None = Field(None, max_length=20)
    start_date: date | None = None
    end_date: date | None = None


class StageResponse(BaseModel):
    """Response schema for a pipeline stage."""

    id: uuid.UUID
    org_id: uuid.UUID
    pipeline_id: uuid.UUID
    name: str
    order_index: int
    color: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    tasks: list[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StageReorderRequest(BaseModel):
    """Request body for reordering stages."""

    stage_ids: list[uuid.UUID] = Field(
        ..., description="Ordered list of stage IDs in their new order"
    )


# ── Checklist Schemas ────────────────────────────────────────────────────


class ChecklistItemCreate(BaseModel):
    """Schema for creating a checklist item within a task."""

    label: str = Field(..., min_length=1, max_length=500)
    done: bool = False


class ChecklistItem(BaseModel):
    """A single checklist item."""

    id: str | None = None
    label: str
    done: bool = False


# ── Activity Schemas ─────────────────────────────────────────────────────


class ActivityResponse(BaseModel):
    """Response schema for a pipeline activity entry."""

    id: uuid.UUID
    pipeline_id: uuid.UUID
    task_id: uuid.UUID | None = None
    action: str
    details: dict | None = None
    user_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Automation Schemas ───────────────────────────────────────────────────


class AutomationCreate(BaseModel):
    """Schema for creating a pipeline automation."""

    trigger_type: str = Field(..., max_length=50)
    trigger_config: dict
    action_type: str = Field(..., max_length=50)
    action_config: dict
    enabled: bool = True


class AutomationUpdate(BaseModel):
    """Schema for updating an automation (partial)."""

    trigger_type: str | None = Field(None, max_length=50)
    trigger_config: dict | None = None
    action_type: str | None = Field(None, max_length=50)
    action_config: dict | None = None
    enabled: bool | None = None


class AutomationResponse(BaseModel):
    """Response schema for a pipeline automation."""

    id: uuid.UUID
    pipeline_id: uuid.UUID
    trigger_type: str
    trigger_config: dict
    action_type: str
    action_config: dict
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Pipeline Detail Schema ───────────────────────────────────────────────


class PipelineDetail(BaseModel):
    """Full pipeline detail including stages, tasks, and progress."""

    id: uuid.UUID
    org_id: uuid.UUID
    book_id: uuid.UUID
    name: str
    description: str | None = None
    status: PipelineStatus
    template: str | None = None
    target_launch_date: date | None = None
    progress_pct: int = 0
    deadline: datetime | None = None
    settings: dict | None = None
    stages: list[StageResponse] = []
    tasks: list[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
