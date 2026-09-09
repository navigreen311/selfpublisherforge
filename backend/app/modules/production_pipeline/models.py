"""SQLAlchemy models for the Production Pipeline module."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class PipelineStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    WRITING = "writing"
    EDITING = "editing"
    PROOFREADING = "proofreading"
    FORMATTING = "formatting"
    REVIEW = "review"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Pipeline(TenantModel):
    """A production pipeline for a book."""

    __tablename__ = "pipelines"

    book_id: Mapped[uuid.UUID] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus, name="pipeline_status"),
        default=PipelineStatus.DRAFT,
        server_default="draft",
    )
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    template: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_pct: Mapped[int | None] = mapped_column(Integer, server_default="0", default=0)

    # Relationships
    tasks: Mapped[list[PipelineTask]] = relationship(
        "PipelineTask",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PipelineTask.created_at",
    )
    stages: Mapped[list[PipelineStage]] = relationship(
        "PipelineStage",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PipelineStage.order_index",
    )

    __table_args__ = (
        Index("ix_pipelines_org_book", "org_id", "book_id"),
        Index("ix_pipelines_status", "status"),
    )


class PipelineTask(TenantModel):
    """A task within a production pipeline."""

    __tablename__ = "pipeline_tasks"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type"),
        default=TaskType.WRITING,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        default=TaskStatus.PENDING,
        server_default="pending",
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    depends_on: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(default=0)
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="SET NULL"), nullable=True
    )
    priority: Mapped[str | None] = mapped_column(String(20), server_default="medium", default="medium")
    checklist: Mapped[list | None] = mapped_column(JSONB, server_default="[]", nullable=True)
    links: Mapped[list | None] = mapped_column(JSONB, server_default="[]", nullable=True)
    blocked_by: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)), server_default="{}", nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, server_default="{}", nullable=True)
    order_index: Mapped[int | None] = mapped_column(Integer, server_default="0", default=0)

    # Relationships
    pipeline: Mapped[Pipeline] = relationship("Pipeline", back_populates="tasks")
    stage: Mapped[PipelineStage | None] = relationship("PipelineStage", back_populates="tasks")

    __table_args__ = (
        Index("ix_pipeline_tasks_pipeline_status", "pipeline_id", "status"),
        Index("ix_pipeline_tasks_assignee", "assignee_id"),
        Index("ix_pipeline_tasks_due_date", "due_date"),
    )


class PipelineTemplate(TenantModel):
    """Reusable pipeline template."""

    __tablename__ = "pipeline_templates"

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_definitions: Mapped[dict] = mapped_column(JSON, default=list)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    is_public: Mapped[bool] = mapped_column(default=False, server_default="false")

    __table_args__ = (Index("ix_pipeline_templates_org", "org_id"),)


class PipelineStage(TenantModel):
    """A stage (phase) within a production pipeline."""

    __tablename__ = "pipeline_stages"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    pipeline: Mapped[Pipeline] = relationship("Pipeline", back_populates="stages")
    tasks: Mapped[list[PipelineTask]] = relationship(
        "PipelineTask",
        back_populates="stage",
        lazy="selectin",
        order_by="PipelineTask.order_index",
    )

    __table_args__ = (Index("idx_pipeline_stages_pipeline", "pipeline_id"),)


class PipelineActivity(BaseModel):
    """Activity log entry for a pipeline or task event."""

    __tablename__ = "pipeline_activity"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pipeline_tasks.id", ondelete="CASCADE"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    __table_args__ = (Index("idx_pipeline_activity_pipeline", "pipeline_id"),)


class PipelineAutomation(BaseModel):
    """An automation rule attached to a pipeline."""

    __tablename__ = "pipeline_automations"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), index=True)
    trigger_type: Mapped[str] = mapped_column(String(50))
    trigger_config: Mapped[dict] = mapped_column(JSONB)
    action_type: Mapped[str] = mapped_column(String(50))
    action_config: Mapped[dict] = mapped_column(JSONB)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default="true", default=True)
