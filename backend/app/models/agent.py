"""Agent, AgentTask, AgentWorkflow, AgentBudget, and AuditTrail models.

The canonical model definitions live in ``app.modules.agent_system.models``.
This file re-exports them so that legacy imports
(``from app.models.agent import Agent``) continue to work without
registering duplicate classes in SQLAlchemy's declarative base.
"""
import enum

# ── Re-exports from the canonical module ──────────────────────────────
from app.modules.agent_system.models import (  # noqa: F401
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    AgentWorkflow,
    AuditTrail,
    PermissionLevel,
    TaskStatus,
    WorkflowStatus,
)

# ── Enums unique to the central models layer ──────────────────────────
# These are NOT defined in the module file but are referenced by existing
# code / tests that import from ``app.models.agent``.


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
