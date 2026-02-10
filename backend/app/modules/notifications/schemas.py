"""Pydantic schemas for the notification service."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.notifications.models import NotificationChannel, NotificationType


# ---------------------------------------------------------------------------
# Notification schemas
# ---------------------------------------------------------------------------


class CreateNotification(BaseModel):
    """Payload for creating a new notification."""

    user_id: UUID
    org_id: UUID
    type: NotificationType = NotificationType.INFO
    title: str = Field(..., max_length=255)
    message: str
    data: dict | None = None


class NotificationOut(BaseModel):
    """Response schema for a single notification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    message: str
    data: dict | None = None
    read_at: datetime | None = None
    created_at: datetime


class UnreadCountOut(BaseModel):
    """Response with the count of unread notifications."""

    unread_count: int


# ---------------------------------------------------------------------------
# Notification-preference schemas
# ---------------------------------------------------------------------------


class NotificationPreferenceOut(BaseModel):
    """Response schema for a single notification preference row."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    channel: NotificationChannel
    category: str
    enabled: bool


class NotificationPreferenceUpdate(BaseModel):
    """Payload for updating one or more notification preferences."""

    preferences: list["PreferenceItem"]


class PreferenceItem(BaseModel):
    """A single preference toggle."""

    channel: NotificationChannel
    category: str
    enabled: bool
