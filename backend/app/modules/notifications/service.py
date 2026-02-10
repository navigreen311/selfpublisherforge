"""Core business logic for the notification service.

Handles in-app notification CRUD, user preference management, and
dispatches email notifications via the SMTP channel for relevant
notification types.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.notifications.email_channel import send_template_email
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
# Mapping: notification type -> email template name
# ---------------------------------------------------------------------------
# Only notification types listed here trigger an email dispatch.  Types that
# are purely informational (INFO, SUCCESS, WARNING, ERROR) are in-app only by
# default.
_TYPE_TO_EMAIL_TEMPLATE: dict[NotificationType, str] = {
    NotificationType.TEAM_INVITE: "invitation",
    NotificationType.AI_COMPLETE: "report_ready",
    NotificationType.PUBLISH_STATUS: "report_ready",
}


# ---------------------------------------------------------------------------
# Notification CRUD
# ---------------------------------------------------------------------------


async def create_notification(
    db: AsyncSession,
    payload: CreateNotification,
    *,
    recipient_email: str | None = None,
    email_context: dict[str, Any] | None = None,
) -> Notification:
    """Persist a new in-app notification and optionally dispatch an email.

    When the notification type is mapped to an email template **and** the
    user has not opted-out of the ``email`` channel for the corresponding
    category, an email is sent asynchronously via the SMTP channel.

    Args:
        db: Active database session.
        payload: Notification data.
        recipient_email: If provided (and email dispatch is appropriate),
            an email will be sent to this address.
        email_context: Extra template context values for the email.  The
            notification ``title`` and ``message`` are included
            automatically.

    Returns:
        The created ``Notification`` instance (already flushed so that
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

    # --- Email dispatch (best-effort, never blocks the caller) -----------
    await _maybe_send_email(
        db=db,
        notification=notification,
        recipient_email=recipient_email,
        extra_context=email_context,
    )

    return notification


async def _maybe_send_email(
    db: AsyncSession,
    notification: Notification,
    recipient_email: str | None,
    extra_context: dict[str, Any] | None,
) -> None:
    """Conditionally dispatch an email for a notification.

    The email is sent only when:
    1. ``recipient_email`` is provided.
    2. The notification type is mapped to an email template.
    3. The user has not opted-out of the ``email`` channel for the
       notification's type category.

    Failures are logged but never propagated -- email is a best-effort
    side-channel.
    """
    if not recipient_email:
        return

    template_name = _TYPE_TO_EMAIL_TEMPLATE.get(notification.type)
    if template_name is None:
        return

    # Respect user preferences (opt-out model: default is enabled)
    category = notification.type.value
    email_enabled = await is_preference_enabled(
        db, notification.user_id, NotificationChannel.EMAIL, category
    )
    if not email_enabled:
        logger.info(
            "Email channel disabled by user %s for category %s; skipping.",
            notification.user_id,
            category,
        )
        return

    context: dict[str, Any] = {
        "title": notification.title,
        "message": notification.message,
        **(notification.data or {}),
        **(extra_context or {}),
    }

    try:
        sent = await send_template_email(
            to=recipient_email,
            template_name=template_name,
            context=context,
        )
        if sent:
            logger.info(
                "Email dispatched for notification %s (template=%s, to=%s)",
                notification.id,
                template_name,
                recipient_email,
            )
        else:
            logger.warning(
                "Email not sent for notification %s (template=%s, to=%s). "
                "SMTP may not be configured.",
                notification.id,
                template_name,
                recipient_email,
            )
    except Exception:
        logger.exception(
            "Unexpected error sending email for notification %s",
            notification.id,
        )


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


# ---------------------------------------------------------------------------
# Direct email dispatch helpers
# ---------------------------------------------------------------------------
# These are convenience wrappers for emails that are triggered outside of the
# normal notification-creation flow (e.g., auth events).


async def send_welcome_email(
    to: str,
    *,
    name: str = "there",
    dashboard_url: str = "#",
) -> bool:
    """Send the welcome email to a newly registered user."""
    return await send_template_email(
        to=to,
        template_name="welcome",
        context={"name": name, "dashboard_url": dashboard_url},
    )


async def send_password_reset_email(
    to: str,
    *,
    name: str = "there",
    reset_url: str,
    expiry_hours: int | str = 24,
) -> bool:
    """Send a password-reset email."""
    return await send_template_email(
        to=to,
        template_name="password_reset",
        context={
            "name": name,
            "reset_url": reset_url,
            "expiry_hours": str(expiry_hours),
        },
    )


async def send_invitation_email(
    to: str,
    *,
    name: str = "there",
    org_name: str,
    role: str = "member",
    invite_url: str,
    expiry_days: int | str = 7,
) -> bool:
    """Send an organization invitation email."""
    return await send_template_email(
        to=to,
        template_name="invitation",
        context={
            "name": name,
            "org_name": org_name,
            "role": role,
            "invite_url": invite_url,
            "expiry_days": str(expiry_days),
        },
    )


async def send_report_ready_email(
    to: str,
    *,
    name: str = "there",
    report_name: str,
    download_url: str,
    expiry_days: int | str = 7,
) -> bool:
    """Send a report-ready-for-download email."""
    return await send_template_email(
        to=to,
        template_name="report_ready",
        context={
            "name": name,
            "report_name": report_name,
            "download_url": download_url,
            "expiry_days": str(expiry_days),
        },
    )
