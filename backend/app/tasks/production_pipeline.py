"""Celery tasks for the Production Pipeline module.

Handles deadline reminder notifications and overdue alerts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="production_pipeline.check_deadlines",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def check_deadlines(self) -> dict:
    """Periodic task: scan active pipelines for upcoming and overdue deadlines.

    This task is meant to be scheduled via Celery Beat (e.g., every hour).
    It queries all active pipelines, identifies overdue and upcoming tasks,
    and dispatches notification events.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_check_deadlines_async())
        return result
    except Exception as exc:
        logger.exception("check_deadlines failed")
        raise self.retry(exc=exc)
    finally:
        loop.close()


async def _check_deadlines_async() -> dict:
    """Async inner implementation for deadline checking."""
    from sqlalchemy import select

    from app.database import async_session
    from app.modules.production_pipeline.models import (
        Pipeline,
        PipelineStatus,
    )
    from app.modules.production_pipeline.workflow import (
        get_overdue_tasks,
        get_upcoming_deadlines,
    )

    now = datetime.now(timezone.utc)
    overdue_count = 0
    reminder_count = 0

    async with async_session() as db:
        stmt = select(Pipeline).where(
            Pipeline.status == PipelineStatus.ACTIVE,
            Pipeline.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        pipelines = list(result.scalars().all())

        for pipeline in pipelines:
            tasks = pipeline.tasks or []

            # Overdue tasks
            overdue = get_overdue_tasks(tasks, now)
            for task in overdue:
                _send_overdue_alert(pipeline, task)
                overdue_count += 1

            # Tasks due within 48 hours
            upcoming = get_upcoming_deadlines(tasks, within_hours=48, now=now)
            for task in upcoming:
                _send_deadline_reminder(pipeline, task)
                reminder_count += 1

            # Pipeline-level deadline
            if (
                pipeline.deadline
                and pipeline.deadline < now
                and pipeline.status == PipelineStatus.ACTIVE
            ):
                _send_pipeline_overdue_alert(pipeline)

    logger.info(
        "Deadline check completed: %d overdue alerts, %d reminders sent",
        overdue_count,
        reminder_count,
    )
    return {
        "overdue_alerts": overdue_count,
        "reminders_sent": reminder_count,
        "pipelines_scanned": len(pipelines),
        "checked_at": now.isoformat(),
    }


@celery_app.task(
    name="production_pipeline.send_overdue_alert",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_overdue_alert(self, pipeline_id: str, task_id: str) -> dict:
    """Send an overdue notification for a specific task."""
    logger.info(
        "Sending overdue alert for pipeline=%s task=%s",
        pipeline_id,
        task_id,
    )
    # In production, this would dispatch an email/push/in-app notification
    # via the notifications module.
    return {
        "pipeline_id": pipeline_id,
        "task_id": task_id,
        "alert_type": "overdue",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(
    name="production_pipeline.send_deadline_reminder",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_deadline_reminder(self, pipeline_id: str, task_id: str) -> dict:
    """Send a deadline reminder for a task approaching its due date."""
    logger.info(
        "Sending deadline reminder for pipeline=%s task=%s",
        pipeline_id,
        task_id,
    )
    return {
        "pipeline_id": pipeline_id,
        "task_id": task_id,
        "alert_type": "deadline_reminder",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Internal helpers ──────────────────────────────────────────────────────


def _send_overdue_alert(pipeline, task) -> None:
    """Dispatch an async overdue alert notification."""
    send_overdue_alert.delay(str(pipeline.id), str(task.id))


def _send_deadline_reminder(pipeline, task) -> None:
    """Dispatch an async deadline reminder notification."""
    send_deadline_reminder.delay(str(pipeline.id), str(task.id))


def _send_pipeline_overdue_alert(pipeline) -> None:
    """Log a pipeline-level overdue alert."""
    logger.warning(
        "Pipeline '%s' (id=%s) is past its deadline of %s",
        pipeline.name,
        pipeline.id,
        pipeline.deadline,
    )
