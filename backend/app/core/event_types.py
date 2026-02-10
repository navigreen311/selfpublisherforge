"""Event types for inter-module communication via Redis Streams / SNS.

Local copy of shared/types/events.py so the backend can run without the
root-level ``shared`` package on sys.path.
"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum


class EventType(str, Enum):
    # Auth events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    BOOK_CREATED = "book.created"
    BOOK_STATUS_CHANGED = "book.status_changed"

    # AI events
    AI_GENERATION_STARTED = "ai.generation.started"
    AI_GENERATION_COMPLETED = "ai.generation.completed"
    AI_GENERATION_FAILED = "ai.generation.failed"

    # Publishing events
    BOOK_VALIDATED = "publishing.validated"
    BOOK_UPLOADED = "publishing.uploaded"
    LISTING_SYNCED = "publishing.listing_synced"

    # Marketing events
    CAMPAIGN_CREATED = "marketing.campaign.created"
    CAMPAIGN_UPDATED = "marketing.campaign.updated"

    # Agent events
    AGENT_TASK_STARTED = "agent.task.started"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    AGENT_TASK_FAILED = "agent.task.failed"
    AGENT_BUDGET_ALERT = "agent.budget.alert"

    # Analytics events
    METRIC_RECORDED = "analytics.metric"
    REPORT_GENERATED = "analytics.report.generated"


class BaseEvent(BaseModel):
    event_type: EventType
    org_id: UUID
    actor_id: UUID
    actor_type: str = "user"  # user | agent | system
    timestamp: datetime
    data: dict = {}


class EventPublisher:
    """Interface for publishing events. Implemented by infrastructure layer."""

    async def publish(self, event: BaseEvent) -> None:
        raise NotImplementedError
