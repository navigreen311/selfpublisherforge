"""SQLAlchemy models for the Production Pipeline module."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus, name="pipeline_status"),
        default=PipelineStatus.DRAFT,
        server_default="draft",
    )
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    tasks: Mapped[list["PipelineTask"]] = relationship(
        "PipelineTask",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PipelineTask.created_at",
    )

    __table_args__ = (
        Index("ix_pipelines_org_book", "org_id", "book_id"),
        Index("ix_pipelines_status", "status"),
    )


class PipelineTask(TenantModel):
    """A task within a production pipeline."""

    __tablename__ = "pipeline_tasks"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipelines.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type"),
        default=TaskType.WRITING,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        default=TaskStatus.PENDING,
        server_default="pending",
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    depends_on: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True, default=list
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    position: Mapped[int] = mapped_column(default=0)

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship(
        "Pipeline", back_populates="tasks"
    )

    __table_args__ = (
        Index("ix_pipeline_tasks_pipeline_status", "pipeline_id", "status"),
        Index("ix_pipeline_tasks_assignee", "assignee_id"),
        Index("ix_pipeline_tasks_due_date", "due_date"),
    )


class PipelineTemplate(TenantModel):
    """Reusable pipeline template."""

    __tablename__ = "pipeline_templates"

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_definitions: Mapped[dict] = mapped_column(JSON, default=list)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    is_public: Mapped[bool] = mapped_column(default=False, server_default="false")

    __table_args__ = (
        Index("ix_pipeline_templates_org", "org_id"),
    )
