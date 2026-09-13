"""SQLAlchemy models for the AI Agent System."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

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
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType, name="agent_type_enum", create_constraint=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    permission_level: Mapped[PermissionLevel] = mapped_column(
        SAEnum(PermissionLevel, name="permission_level_enum", create_constraint=False),
        default=PermissionLevel.DRAFT_ONLY,
        nullable=False,
    )
    model_id: Mapped[str] = mapped_column(String(255), default="claude-sonnet-4-5-20250929", nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False, server_default=text("0.7"))
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    tasks: Mapped[list[AgentTask]] = relationship(back_populates="agent", lazy="selectin")
    budget: Mapped[AgentBudget | None] = relationship(back_populates="agent", uselist=False, lazy="selectin")
    organization = relationship(
        "Organization",
        back_populates="agents",
        primaryjoin="Agent.org_id == Organization.id",
        foreign_keys="[Agent.org_id]",
    )
    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    configuration: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    icon: Mapped[str | None] = mapped_column(String(10), nullable=True, default=None)
    default_execution_mode: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    task_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    context_sources: Mapped[list | None] = mapped_column(ARRAY(Text()), nullable=True, default=None)
    budget_per_task: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, default=None)
    monthly_budget: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, default=None)
    is_system: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)

    __table_args__ = (
        Index("ix_agents_active", "active"),
        Index("ix_agents_agent_type", "agent_type"),
        Index("ix_agents_configuration_gin", "configuration", postgresql_using="gin"),
        Index("ix_agents_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_agents_org_id_created_at", "org_id", "created_at"),
        Index("ix_agents_permission_level", "permission_level"),
    )


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
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), index=True, nullable=False)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_workflows.id"), nullable=True, index=True
    )
    workflow_step_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default=text("0"))
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    agent: Mapped[Agent] = relationship(back_populates="tasks", lazy="selectin")
    workflow: Mapped[AgentWorkflow | None] = relationship(back_populates="tasks", lazy="selectin")
    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    # NOT NULL in the database with no default, and nothing writes it — so
    # every insert into this table against the migrated schema failed. It
    # is superseded by `type`; relaxed rather than dropped.
    task_type: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    input: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    cost_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("books.id", ondelete="SET NULL"), nullable=True, default=None
    )
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    execution_mode: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    output_format: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    steps: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True, default=None)
    execution_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    applied_to: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)

    __table_args__ = (
        Index("idx_agent_tasks_agent", "agent_id", "status"),
        Index("ix_agent_tasks_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_agent_tasks_input_gin", "input", postgresql_using="gin"),
        Index("ix_agent_tasks_output_gin", "output", postgresql_using="gin"),
        Index("ix_agent_tasks_task_type", "task_type"),
    )


class AgentWorkflow(Base):
    """Multi-step workflow that orchestrates multiple agent tasks."""

    __tablename__ = "agent_workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        SAEnum(WorkflowStatus, name="workflow_status_enum", create_constraint=False),
        default=WorkflowStatus.DRAFT,
        nullable=False,
        index=True,
    )
    steps: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    tasks: Mapped[list[AgentTask]] = relationship(back_populates="workflow", lazy="selectin")
    organization = relationship(
        "Organization",
        back_populates="agent_workflows",
        primaryjoin="AgentWorkflow.org_id == Organization.id",
        foreign_keys="[AgentWorkflow.org_id]",
    )
    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    trigger_conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        Index("ix_agent_workflows_active", "active"),
        Index("ix_agent_workflows_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_agent_workflows_org_id_created_at", "org_id", "created_at"),
        Index("ix_agent_workflows_steps_gin", "steps", postgresql_using="gin"),
        Index("ix_agent_workflows_trigger_conditions_gin", "trigger_conditions", postgresql_using="gin"),
    )


class AgentBudget(Base):
    """Budget tracking and limits for an agent within an organization."""

    __tablename__ = "agent_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
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

    last_reset_daily: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reset_monthly: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    agent: Mapped[Agent] = relationship(back_populates="budget", lazy="selectin")
    organization = relationship(
        "Organization",
        back_populates="agent_budgets",
        primaryjoin="AgentBudget.org_id == Organization.id",
        foreign_keys="[AgentBudget.org_id]",
    )
    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    # NOT NULL in the database with no default, and nothing writes it — so
    # every insert into this table against the migrated schema failed. It
    # is superseded by `period` + `limit_tokens`/`limit_usd`; relaxed rather than dropped.
    budget_type: Mapped[str | None] = mapped_column(
        ENUM(name="budget_type", create_type=False), nullable=True, default=None
    )
    limit_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, default=None)
    spent_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    period: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    alerts_sent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    __table_args__ = (
        Index("ix_agent_budgets_budget_type", "budget_type"),
        Index("ix_agent_budgets_deleted_at_partial", "id", postgresql_where=text("(deleted_at IS NULL)")),
        Index("ix_agent_budgets_org_id_created_at", "org_id", "created_at"),
    )


class AuditTrail(Base):
    """Immutable audit log for every agent action."""

    __tablename__ = "audit_trail"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action_enum", create_constraint=False),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="audit_trails",
        primaryjoin="AuditTrail.org_id == Organization.id",
        foreign_keys="[AuditTrail.org_id]",
    )
    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    __table_args__ = (
        Index("ix_audit_trail_actor_id", "actor_id"),
        Index("ix_audit_trail_actor_type", "actor_type"),
        Index("ix_audit_trail_details_gin", "details", postgresql_using="gin"),
        Index("ix_audit_trail_org_id_action", "org_id", "action"),
        Index("ix_audit_trail_org_id_created_at", "org_id", "created_at"),
        Index("ix_audit_trail_resource_id", "resource_id"),
        Index("ix_audit_trail_resource_type", "resource_type"),
        Index("ix_audit_trail_timestamp_brin", "timestamp", postgresql_using="brin"),
    )
