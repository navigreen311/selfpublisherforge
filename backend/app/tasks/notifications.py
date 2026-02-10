"""Celery tasks for asynchronous notification delivery."""

from __future__ import annotations

import logging
from typing import Any

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="notifications.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_email_task(
    self,
    to_email: str,
    template_name: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a transactional email asynchronously via Celery.

    Retries up to 3 times with a 60-second delay between attempts.
    """
    from app.modules.notifications.email import send_transactional_email

    try:
        success = send_transactional_email(to_email, template_name, context)
        if not success:
            raise RuntimeError(f"SendGrid rejected email to {to_email}")
        logger.info("Email task completed: to=%s template=%s", to_email, template_name)
        return {"status": "sent", "to": to_email, "template": template_name}
    except Exception as exc:
        logger.warning(
            "Email task failed (attempt %s/%s): to=%s template=%s error=%s",
            self.request.retries + 1,
            self.max_retries + 1,
            to_email,
            template_name,
            str(exc),
        )
        raise self.retry(exc=exc)


@celery_app.task(
    name="notifications.create_in_app",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def create_in_app_notification_task(
    self,
    user_id: str,
    org_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an in-app notification record asynchronously.

    This is useful when a background job (e.g. AI processing) completes and
    needs to notify the user without blocking.
    """
    import asyncio
    from uuid import UUID

    from app.database import async_session
    from app.modules.notifications.schemas import CreateNotification
    from app.modules.notifications.service import create_notification

    payload = CreateNotification(
        user_id=UUID(user_id),
        org_id=UUID(org_id),
        type=notification_type,
        title=title,
        message=message,
        data=data,
    )

    async def _create() -> str:
        async with async_session() as session:
            notification = await create_notification(session, payload)
            await session.commit()
            return str(notification.id)

    loop = asyncio.new_event_loop()
    try:
        notification_id = loop.run_until_complete(_create())
        logger.info(
            "In-app notification created: id=%s user=%s type=%s",
            notification_id,
            user_id,
            notification_type,
        )
        return {"status": "created", "notification_id": notification_id}
    except Exception as exc:
        logger.warning(
            "In-app notification task failed (attempt %s/%s): user=%s error=%s",
            self.request.retries + 1,
            self.max_retries + 1,
            user_id,
            str(exc),
        )
        raise self.retry(exc=exc)
    finally:
        loop.close()


@celery_app.task(
    name="notifications.batch_deliver",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def batch_notification_delivery_task(
    self,
    notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deliver a batch of notifications (in-app + email).

    Each entry in *notifications* should have:
        - user_id (str)
        - org_id (str)
        - type (str)          — notification type enum value
        - title (str)
        - message (str)
        - data (dict | None)
        - email (str | None)  — if provided, also send an email
        - email_template (str | None)
        - email_context (dict | None)
    """
    succeeded = 0
    failed = 0

    for entry in notifications:
        try:
            # Fan-out: queue individual tasks
            create_in_app_notification_task.delay(
                user_id=entry["user_id"],
                org_id=entry["org_id"],
                notification_type=entry.get("type", "info"),
                title=entry["title"],
                message=entry["message"],
                data=entry.get("data"),
            )

            email = entry.get("email")
            template = entry.get("email_template")
            if email and template:
                send_email_task.delay(
                    to_email=email,
                    template_name=template,
                    context=entry.get("email_context"),
                )

            succeeded += 1
        except Exception:
            logger.exception("Failed to queue notification for user %s", entry.get("user_id"))
            failed += 1

    logger.info("Batch delivery: queued=%d failed=%d", succeeded, failed)
    return {"queued": succeeded, "failed": failed}
