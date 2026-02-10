"""Core business logic for the notification service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationType,
)
from app.modules.notifications.schemas import (
    CreateNotification,
    PreferenceItem,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Notification CRUD
# ---------------------------------------------------------------------------


async def create_notification(
    db: AsyncSession,
    payload: CreateNotification,
) -> Notification:
    """Persist a new in-app notification.

    Returns the created ``Notification`` instance (already flushed so that
    ``id`` and ``created_at`` are populated).
    """
    notification = Notification(
        user_id=payload.user_id,
        org_id=payload.org_id,
        type=payload.type,
        title=payload.title,
        message=payload.message,
        data=payload.data,
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    *,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Notification], str | None, bool]:
    """Return a paginated list of notifications for the user.

    Uses cursor-based pagination keyed on ``created_at``.

    Returns:
        Tuple of (items, next_cursor, has_more).
    """
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )

    if cursor:
        cursor_dt = datetime.fromisoformat(cursor)
        query = query.where(Notification.created_at < cursor_dt)

    # Fetch one extra to determine has_more
    query = query.limit(limit + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor: str | None = None
    if has_more and items:
        next_cursor = items[-1].created_at.isoformat()

    return items, next_cursor, has_more


async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
    """Return the number of unread notifications for a user."""
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
    )
    return result.scalar_one()


async def mark_as_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> Notification:
    """Mark a single notification as read.

    Raises ``AppException`` (404) if the notification does not belong to the user.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise AppException(
            status_code=404,
            code="NOTIFICATION_NOT_FOUND",
            message="Notification not found",
        )
    notification.read_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(notification)
    return notification


async def mark_all_as_read(db: AsyncSession, user_id: UUID) -> int:
    """Mark every unread notification for the user as read.

    Returns the number of notifications that were updated.
    """
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    return result.rowcount  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Preference management
# ---------------------------------------------------------------------------


async def get_preferences(
    db: AsyncSession,
    user_id: UUID,
) -> list[NotificationPreference]:
    """Return all notification preferences for a user."""
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    )
    return list(result.scalars().all())


async def upsert_preferences(
    db: AsyncSession,
    user_id: UUID,
    items: list[PreferenceItem],
) -> list[NotificationPreference]:
    """Create or update notification preferences for a user.

    For each item in ``items`` the method will either create a new row or
    update the existing one (matched on the unique constraint
    ``(user_id, channel, category)``).

    Returns the full list of preferences after the upsert.
    """
    for item in items:
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == item.channel,
                NotificationPreference.category == item.category,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.enabled = item.enabled
        else:
            pref = NotificationPreference(
                user_id=user_id,
                channel=item.channel,
                category=item.category,
                enabled=item.enabled,
            )
            db.add(pref)

    await db.flush()
    return await get_preferences(db, user_id)


async def is_preference_enabled(
    db: AsyncSession,
    user_id: UUID,
    channel: NotificationChannel,
    category: str,
) -> bool:
    """Check whether a specific notification preference is enabled.

    Defaults to ``True`` when no explicit preference row exists (opt-out model).
    """
    result = await db.execute(
        select(NotificationPreference.enabled).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.channel == channel,
            NotificationPreference.category == category,
        )
    )
    row = result.scalar_one_or_none()
    return row if row is not None else True
