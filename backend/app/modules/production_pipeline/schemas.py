"""Pydantic schemas for the Production Pipeline module."""

from __future__ import annotations

import uuid
from datetime import datetime

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


class TaskResponse(TaskBase):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    org_id: uuid.UUID
    status: TaskStatus
    completed_at: datetime | None = None
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


class PipelineResponse(PipelineBase):
    id: uuid.UUID
    org_id: uuid.UUID
    status: PipelineStatus
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
