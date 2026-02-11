"""WebSocket message types and typed event schemas for each channel."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Channel enum
# ---------------------------------------------------------------------------

class WSChannel(str, Enum):
    WRITING = "writing"
    AGENTS = "agents"
    ANALYTICS = "analytics"
    PUBLISHING = "publishing"


# ---------------------------------------------------------------------------
# Base message envelope
# ---------------------------------------------------------------------------

class WSMessage(BaseModel):
    """Canonical envelope for every WebSocket message."""
    type: str
    channel: WSChannel
    room_id: str
    data: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Writing channel events
# ---------------------------------------------------------------------------

class CursorMoveData(BaseModel):
    user_id: str
    position: int
    selection_start: int | None = None
    selection_end: int | None = None


class TextChangeData(BaseModel):
    user_id: str
    offset: int
    length: int
    text: str
    revision: int


class AISuggestionData(BaseModel):
    suggestion_id: str
    text: str
    position: int
    confidence: float


class SaveAckData(BaseModel):
    revision: int
    saved_at: datetime


# ---------------------------------------------------------------------------
# Agent channel events
# ---------------------------------------------------------------------------

class TaskStartedData(BaseModel):
    task_id: str
    task_type: str
    agent_name: str


class TaskProgressData(BaseModel):
    task_id: str
    progress: float = Field(ge=0, le=100)
    message: str = ""


class TaskCompletedData(BaseModel):
    task_id: str
    result_summary: str = ""


class TaskFailedData(BaseModel):
    task_id: str
    error: str


class BudgetAlertData(BaseModel):
    current_spend: float
    budget_limit: float
    alert_type: str = "warning"


# ---------------------------------------------------------------------------
# Analytics channel events
# ---------------------------------------------------------------------------

class MetricUpdateData(BaseModel):
    metric_name: str
    value: float
    dimensions: dict[str, str] = {}


class AlertTriggeredData(BaseModel):
    alert_id: str
    severity: str
    message: str


class ReportReadyData(BaseModel):
    report_id: str
    report_type: str
    download_url: str | None = None


# ---------------------------------------------------------------------------
# Publishing channel events
# ---------------------------------------------------------------------------

class ValidationProgressData(BaseModel):
    step: str
    total_steps: int
    current_step: int
    passed: bool | None = None
    message: str = ""


class UploadProgressData(BaseModel):
    platform: str
    progress: float = Field(ge=0, le=100)
    file_name: str = ""


class ListingSyncedData(BaseModel):
    platform: str
    listing_url: str | None = None
    status: str


# ---------------------------------------------------------------------------
# Mapping of event type strings to their data schemas
# ---------------------------------------------------------------------------

WRITING_EVENT_TYPES = {
    "cursor_move": CursorMoveData,
    "text_change": TextChangeData,
    "ai_suggestion": AISuggestionData,
    "save_ack": SaveAckData,
}

AGENT_EVENT_TYPES = {
    "task_started": TaskStartedData,
    "task_progress": TaskProgressData,
    "task_completed": TaskCompletedData,
    "task_failed": TaskFailedData,
    "budget_alert": BudgetAlertData,
}

ANALYTICS_EVENT_TYPES = {
    "metric_update": MetricUpdateData,
    "alert_triggered": AlertTriggeredData,
    "report_ready": ReportReadyData,
}

PUBLISHING_EVENT_TYPES = {
    "validation_progress": ValidationProgressData,
    "upload_progress": UploadProgressData,
    "listing_synced": ListingSyncedData,
}

CHANNEL_EVENT_TYPES = {
    WSChannel.WRITING: WRITING_EVENT_TYPES,
    WSChannel.AGENTS: AGENT_EVENT_TYPES,
    WSChannel.ANALYTICS: ANALYTICS_EVENT_TYPES,
    WSChannel.PUBLISHING: PUBLISHING_EVENT_TYPES,
}
