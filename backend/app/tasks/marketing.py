"""Celery tasks for the Marketing & Launch Command module.

Handles:
- Scheduled email sends
- Social post reminders
- ARC follow-up emails
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="marketing.send_scheduled_emails",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_scheduled_emails(self, sequence_id: str, org_id: str) -> dict:
    """Send scheduled emails for an active email sequence.

    Checks all email templates in the sequence and sends any that are due
    based on their delay_days / delay_hours configuration.
    """
    import asyncio
    from app.database import async_session
    from app.modules.marketing.service import MarketingService
    from app.models.marketing import EmailSendStatus

    async def _process():
        async with async_session() as db:
            service = MarketingService(db)
            sequence = await service.get_email_sequence(
                UUID(sequence_id), UUID(org_id)
            )
            if not sequence:
                logger.warning(f"Sequence {sequence_id} not found")
                return {"status": "not_found"}

            sent_count = 0
            for template in sequence.emails:
                if template.send_status != EmailSendStatus.SCHEDULED:
                    continue

                if template.scheduled_at and template.scheduled_at <= datetime.utcnow():
                    # In production, this would call SendGrid/SES
                    template.send_status = EmailSendStatus.SENT
                    template.sent_at = datetime.utcnow()
                    sent_count += 1
                    logger.info(
                        f"Sent email '{template.subject}' for sequence {sequence_id}"
                    )

            sequence.sent_count += sent_count
            await db.commit()

            return {"status": "ok", "sent_count": sent_count}

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_process())
        return result
    except Exception as exc:
        logger.error(f"Failed to send scheduled emails: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        loop.close()


@celery_app.task(
    name="marketing.send_social_post_reminders",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_social_post_reminders(self, org_id: str) -> dict:
    """Send reminders for social posts that are scheduled within the next 24 hours.

    This task is meant to be run periodically (e.g., every 6 hours) by a
    Celery Beat schedule.
    """
    import asyncio
    from app.database import async_session
    from app.models.marketing import SocialPost, SocialPostStatus
    from sqlalchemy import select, and_

    async def _process():
        async with async_session() as db:
            now = datetime.utcnow()
            tomorrow = now + timedelta(hours=24)

            stmt = select(SocialPost).where(
                and_(
                    SocialPost.org_id == UUID(org_id),
                    SocialPost.status == SocialPostStatus.SCHEDULED,
                    SocialPost.scheduled_at >= now,
                    SocialPost.scheduled_at <= tomorrow,
                    SocialPost.deleted_at.is_(None),
                )
            )
            result = await db.execute(stmt)
            posts = list(result.scalars().all())

            reminders_sent = 0
            for post in posts:
                # In production, send notification (push, email, in-app)
                logger.info(
                    f"Reminder: Social post for {post.platform.value} "
                    f"scheduled at {post.scheduled_at}"
                )
                reminders_sent += 1

            return {"status": "ok", "reminders_sent": reminders_sent}

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_process())
        return result
    except Exception as exc:
        logger.error(f"Failed to send social post reminders: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        loop.close()


@celery_app.task(
    name="marketing.send_arc_follow_ups",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def send_arc_follow_ups(self, org_id: str, days_since_send: int = 7) -> dict:
    """Send follow-up emails to ARC recipients who have not submitted reviews.

    Targets recipients whose copies were sent more than `days_since_send`
    days ago and who have not yet submitted a review.
    """
    import asyncio
    from app.database import async_session
    from app.modules.marketing.arc_manager import ARCManager

    async def _process():
        async with async_session() as db:
            manager = ARCManager(db)
            pending = await manager.get_pending_follow_ups(
                org_id=UUID(org_id),
                days_since_send=days_since_send,
            )

            follow_ups_sent = 0
            for recipient_info in pending:
                # In production, this would send an actual email via SendGrid/SES
                logger.info(
                    f"ARC follow-up: Sending to {recipient_info['email']} "
                    f"({recipient_info['days_since_send']} days since send)"
                )
                follow_ups_sent += 1

            return {"status": "ok", "follow_ups_sent": follow_ups_sent}

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_process())
        return result
    except Exception as exc:
        logger.error(f"Failed to send ARC follow-ups: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        loop.close()


@celery_app.task(name="marketing.generate_launch_plan_async")
def generate_launch_plan_async(
    org_id: str,
    user_id: str,
    request_data: dict,
) -> dict:
    """Asynchronously generate a launch plan using AI.

    Used for LLM-based generation which may take longer.
    The result is saved to the database and a notification is sent.
    """
    import asyncio
    from app.database import async_session
    from app.modules.marketing.launch_planner import LaunchPlanner
    from app.modules.marketing.service import MarketingService
    from app.modules.marketing.schemas import GenerateLaunchPlanRequest

    async def _process():
        request = GenerateLaunchPlanRequest(**request_data)
        planner = LaunchPlanner()
        plan_data = await planner.generate_plan_with_ai(request)

        async with async_session() as db:
            service = MarketingService(db)
            plan = await service.save_generated_plan(
                org_id=UUID(org_id),
                user_id=UUID(user_id),
                plan_data=plan_data,
                ai_metadata={
                    "generator": "ai",
                    "request": request_data,
                },
            )
            await db.commit()
            return {"status": "ok", "plan_id": str(plan.id)}

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_process())
        return result
    except Exception as exc:
        logger.error(f"Failed to generate launch plan: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}
    finally:
        loop.close()
