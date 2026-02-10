"""SQLAlchemy models for the AI Agent System."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

import enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentType(str, enum.Enum):
    RESEARCH = "research"
    WRITING_ASSISTANT = "writing_assistant"
    EDITOR = "editor"
    MARKETING_COPY = "marketing_copy"


class PermissionLevel(str, enum.Enum):
    DRAFT_ONLY = "draft_only"
    SUGGEST = "suggest"
    AUTO_EXECUTE_LOW = "auto_execute_low"
    AUTO_EXECUTE_HIGH = "auto_execute_high"
    FULL_AUTONOMOUS = "full_autonomous"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AuditAction(str, enum.Enum):
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_APPROVED = "task_approved"
    TASK_REJECTED = "task_rejected"
    TASK_CANCELLED = "task_cancelled"
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    CONFIG_UPDATED = "config_updated"
    BUDGET_UPDATED = "budget_updated"
    BUDGET_ALERT = "budget_alert"
    EMERGENCY_STOP = "emergency_stop"
    PERMISSION_CHANGED = "permission_changed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Agent(Base):
    """Agent type definition and configuration for an organization."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType, name="agent_type_enum", create_constraint=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    permission_level: Mapped[PermissionLevel] = mapped_column(
        SAEnum(PermissionLevel, name="permission_level_enum", create_constraint=False),
        default=PermissionLevel.DRAFT_ONLY,
        nullable=False,
    )
    model_id: Mapped[str] = mapped_column(String(255), default="claude-sonnet-4-5-20250929", nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    tasks: Mapped[list["AgentTask"]] = relationship(back_populates="agent", lazy="selectin")
    budget: Mapped[Optional["AgentBudget"]] = relationship(back_populates="agent", uselist=False, lazy="selectin")


class AgentTask(Base):
    """An individual task assigned to an agent."""

    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), index=True, nullable=False
    )
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_workflows.id"), nullable=True, index=True
    )
    workflow_step_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status_enum", create_constraint=False),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, name="task_priority_enum", create_constraint=False),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="tasks", lazy="selectin")
    workflow: Mapped[Optional["AgentWorkflow"]] = relationship(back_populates="tasks", lazy="selectin")


class AgentWorkflow(Base):
    """Multi-step workflow that orchestrates multiple agent tasks."""

    __tablename__ = "agent_workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        SAEnum(WorkflowStatus, name="workflow_status_enum", create_constraint=False),
        default=WorkflowStatus.DRAFT,
        nullable=False,
        index=True,
    )
    steps: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    tasks: Mapped[list["AgentTask"]] = relationship(back_populates="workflow", lazy="selectin")


class AgentBudget(Base):
    """Budget tracking and limits for an agent within an organization."""

    __tablename__ = "agent_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), unique=True, nullable=False
    )

    daily_token_limit: Mapped[int] = mapped_column(Integer, default=100000, nullable=False)
    daily_usd_limit: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    monthly_usd_limit: Mapped[float] = mapped_column(Float, default=200.0, nullable=False)

    tokens_used_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usd_used_today: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    usd_used_this_month: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_usd_used: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    last_reset_daily: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_reset_monthly: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="budget", lazy="selectin")


class AuditTrail(Base):
    """Immutable audit log for every agent action."""

    __tablename__ = "audit_trail"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action_enum", create_constraint=False),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
