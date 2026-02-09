"""Agent, AgentTask, AgentWorkflow, AgentBudget, and AuditTrail models."""
import enum
import uuid
from datetime import datetime

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
    Enum as SAEnum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class AgentType(str, enum.Enum):
    RESEARCH = "research"
    WRITING = "writing"
    EDITING = "editing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PUBLISHING = "publishing"


class PermissionLevel(str, enum.Enum):
    READ_ONLY = "read_only"
    SUGGEST = "suggest"
    EXECUTE = "execute"
    AUTONOMOUS = "autonomous"


class AgentTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class BudgetType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    PER_TASK = "per_task"


class ActorType(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Agent(TenantModel):
    __tablename__ = "agents"

    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType, name="agent_type", create_constraint=True),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    permission_level: Mapped[PermissionLevel] = mapped_column(
        SAEnum(PermissionLevel, name="permission_level", create_constraint=True),
        default=PermissionLevel.SUGGEST,
        server_default="suggest",
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    organization = relationship(
        "Organization", back_populates="agents",
        primaryjoin="Agent.org_id == Organization.id",
        foreign_keys="[Agent.org_id]",
    )
    tasks = relationship("AgentTask", back_populates="agent", lazy="selectin")

    __table_args__ = (
        Index("ix_agents_agent_type", "agent_type"),
        Index("ix_agents_permission_level", "permission_level"),
        Index("ix_agents_active", "active"),
        Index("ix_agents_configuration_gin", "configuration", postgresql_using="gin"),
        Index("ix_agents_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_agents_org_id_created_at", "org_id", "created_at"),
    )


class AgentTask(BaseModel):
    __tablename__ = "agent_tasks"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input: Mapped[dict | None] = mapped_column("input", JSONB, nullable=True, default=None)
    output: Mapped[dict | None] = mapped_column("output", JSONB, nullable=True, default=None)
    status: Mapped[AgentTaskStatus] = mapped_column(
        SAEnum(AgentTaskStatus, name="agent_task_status", create_constraint=True),
        default=AgentTaskStatus.PENDING,
        server_default="pending",
    )
    cost_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True, default=None)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # Relationships
    agent = relationship("Agent", back_populates="tasks")

    __table_args__ = (
        Index("ix_agent_tasks_task_type", "task_type"),
        Index("ix_agent_tasks_status", "status"),
        Index("ix_agent_tasks_input_gin", "input", postgresql_using="gin"),
        Index("ix_agent_tasks_output_gin", "output", postgresql_using="gin"),
        Index("ix_agent_tasks_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class AgentWorkflow(TenantModel):
    __tablename__ = "agent_workflows"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    steps: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    trigger_conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    organization = relationship(
        "Organization", back_populates="agent_workflows",
        primaryjoin="AgentWorkflow.org_id == Organization.id",
        foreign_keys="[AgentWorkflow.org_id]",
    )

    __table_args__ = (
        Index("ix_agent_workflows_active", "active"),
        Index("ix_agent_workflows_steps_gin", "steps", postgresql_using="gin"),
        Index("ix_agent_workflows_trigger_conditions_gin", "trigger_conditions", postgresql_using="gin"),
        Index("ix_agent_workflows_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_agent_workflows_org_id_created_at", "org_id", "created_at"),
    )


class AgentBudget(TenantModel):
    __tablename__ = "agent_budgets"

    budget_type: Mapped[BudgetType] = mapped_column(
        SAEnum(BudgetType, name="budget_type", create_constraint=True),
        nullable=False,
    )
    limit_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    spent_value: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, server_default="0"
    )
    period: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    alerts_sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    organization = relationship(
        "Organization", back_populates="agent_budgets",
        primaryjoin="AgentBudget.org_id == Organization.id",
        foreign_keys="[AgentBudget.org_id]",
    )

    __table_args__ = (
        Index("ix_agent_budgets_budget_type", "budget_type"),
        Index("ix_agent_budgets_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_agent_budgets_org_id_created_at", "org_id", "created_at"),
    )


class AuditTrail(BaseModel):
    __tablename__ = "audit_trail"

    org_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    actor_type: Mapped[ActorType] = mapped_column(
        SAEnum(ActorType, name="actor_type", create_constraint=True),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization = relationship(
        "Organization", back_populates="audit_trails",
        primaryjoin="AuditTrail.org_id == Organization.id",
        foreign_keys="[AuditTrail.org_id]",
    )

    __table_args__ = (
        Index("ix_audit_trail_actor_type", "actor_type"),
        Index("ix_audit_trail_action", "action"),
        Index("ix_audit_trail_resource_type", "resource_type"),
        Index("ix_audit_trail_resource_id", "resource_id"),
        Index("ix_audit_trail_details_gin", "details", postgresql_using="gin"),
        Index("ix_audit_trail_timestamp_brin", "timestamp", postgresql_using="brin"),
        Index("ix_audit_trail_org_id_created_at", "org_id", "created_at"),
    )
