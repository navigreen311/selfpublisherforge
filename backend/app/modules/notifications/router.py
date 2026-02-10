"""FastAPI router for notification endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.notifications import service
from app.modules.notifications.schemas import (
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    UnreadCountOut,
)
from app.schemas.common import MessageResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Notification list & read operations
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedResponse[NotificationOut],
    summary="List notifications",
    description="List the authenticated user's notifications, paginated and newest first.",
)
async def list_notifications(
    cursor: str | None = Query(None, description="Pagination cursor (ISO datetime)"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the authenticated user's notifications (paginated, newest first)."""
    items, next_cursor, has_more = await service.list_notifications(
        db, current_user["user_id"], cursor=cursor, limit=limit
    )
    return PaginatedResponse[NotificationOut](
        items=[NotificationOut.model_validate(n) for n in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationOut,
    summary="Mark notification read",
    description="Mark a single notification as read.",
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    notification = await service.mark_as_read(db, notification_id, current_user["user_id"])
    return NotificationOut.model_validate(notification)


@router.post(
    "/read-all",
    response_model=MessageResponse,
    summary="Mark all notifications read",
    description="Mark all of the authenticated user's notifications as read.",
)
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all of the authenticated user's notifications as read."""
    count = await service.mark_all_as_read(db, current_user["user_id"])
    return MessageResponse(message=f"Marked {count} notifications as read")


# ---------------------------------------------------------------------------
# Unread count
# ---------------------------------------------------------------------------


@router.get(
    "/unread-count",
    response_model=UnreadCountOut,
    summary="Get unread count",
    description="Get the number of unread notifications for the authenticated user.",
)
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the number of unread notifications for the authenticated user."""
    count = await service.get_unread_count(db, current_user["user_id"])
    return UnreadCountOut(unread_count=count)


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


@router.get(
    "/preferences",
    response_model=list[NotificationPreferenceOut],
    summary="Get notification preferences",
    description="Get all notification preferences for the authenticated user.",
)
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all notification preferences for the authenticated user."""
    prefs = await service.get_preferences(db, current_user["user_id"])
    return [NotificationPreferenceOut.model_validate(p) for p in prefs]


@router.patch(
    "/preferences",
    response_model=list[NotificationPreferenceOut],
    summary="Update notification preferences",
    description="Create or update notification preferences for the authenticated user.",
)
async def update_preferences(
    body: NotificationPreferenceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update notification preferences for the authenticated user."""
    prefs = await service.upsert_preferences(
        db, current_user["user_id"], body.preferences
    )
    return [NotificationPreferenceOut.model_validate(p) for p in prefs]
