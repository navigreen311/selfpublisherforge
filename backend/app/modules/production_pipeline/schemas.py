"""Pydantic schemas for the Production Pipeline module."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.production_pipeline.models import (
    PipelineStatus,
    TaskStatus,
    TaskType,
)


# ── Task Schemas ──────────────────────────────────────────────────────────


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: TaskType = TaskType.WRITING
    assignee_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    depends_on: Optional[list[str]] = Field(default_factory=list)
    position: int = 0


class CreateTask(TaskBase):
    """Schema for adding a task to a pipeline."""

    pass


class UpdateTask(BaseModel):
    """Schema for updating a task (partial)."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    depends_on: Optional[list[str]] = None
    position: Optional[int] = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    org_id: uuid.UUID
    status: TaskStatus
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pipeline Schemas ──────────────────────────────────────────────────────


class PipelineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    book_id: uuid.UUID
    deadline: Optional[datetime] = None
    settings: Optional[dict] = Field(default_factory=dict)


class CreatePipeline(PipelineBase):
    """Schema for creating a new pipeline."""

    template_id: Optional[uuid.UUID] = None


class UpdatePipeline(BaseModel):
    """Schema for updating pipeline settings (partial)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[PipelineStatus] = None
    deadline: Optional[datetime] = None
    settings: Optional[dict] = None


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
    deadline: Optional[datetime] = None
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
    assignee_id: Optional[uuid.UUID] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    depends_on: list[str] = []
    progress: float = 0.0  # 0.0 – 1.0


class TimelineView(BaseModel):
    """Gantt-style timeline for a pipeline."""

    pipeline_id: uuid.UUID
    pipeline_name: str
    deadline: Optional[datetime] = None
    tasks: list[TimelineTask] = []
    critical_path: list[str] = []  # ordered task IDs on the critical path


# ── Template Schemas ──────────────────────────────────────────────────────


class TaskDefinition(BaseModel):
    """A task blueprint within a template."""

    title: str
    type: TaskType = TaskType.WRITING
    description: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    estimated_days: int = 1
    position: int = 0


class CreateTemplate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_definitions: list[TaskDefinition] = Field(default_factory=list)
    settings: Optional[dict] = Field(default_factory=dict)
    is_public: bool = False


class TemplateResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: Optional[str] = None
    task_definitions: list[dict] = []
    settings: Optional[dict] = None
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
