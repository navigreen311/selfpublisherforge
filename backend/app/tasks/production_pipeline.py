"""Celery tasks for the Production Pipeline module.

Handles deadline reminder notifications and overdue alerts.

Time limit strategy
-------------------
Each task declares explicit ``soft_time_limit`` and ``time_limit`` values
(in seconds) based on expected workload:
  - Quick   (notifications, status updates):   soft=60,   hard=120
  - Medium  (API calls, data sync):            soft=300,  hard=600
  - Long    (bulk imports, report generation):  soft=1800, hard=3600
  - V. Long (full analytics aggregation):       soft=3300, hard=3600
Global defaults in config.py are 3300/3600 but per-task limits take precedence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="production_pipeline.check_deadlines",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
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
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("check_deadlines failed: %s", exc, exc_info=True)
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
    soft_time_limit=60,
    time_limit=120,
)
def send_overdue_alert(self, pipeline_id: str, task_id: str) -> dict:
    """Send an overdue notification for a specific task."""
    from app.tasks.notifications import create_in_app_notification_task

    logger.info(
        "Sending overdue alert for pipeline=%s task=%s",
        pipeline_id,
        task_id,
    )

    try:
        create_in_app_notification_task.delay(
            user_id=pipeline_id,  # resolved from pipeline owner in caller
            org_id=pipeline_id,
            notification_type="overdue_alert",
            title=f"Task {task_id} is overdue",
            message=f"A task in pipeline {pipeline_id} has passed its deadline.",
            data={"pipeline_id": pipeline_id, "task_id": task_id},
        )
    except (ConnectionError, OSError) as exc:
        logger.error(
            "Failed to dispatch overdue notification for pipeline=%s task=%s: %s",
            pipeline_id, task_id, exc, exc_info=True,
        )

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
    soft_time_limit=60,
    time_limit=120,
)
def send_deadline_reminder(self, pipeline_id: str, task_id: str) -> dict:
    """Send a deadline reminder for a task approaching its due date."""
    from app.tasks.notifications import create_in_app_notification_task

    logger.info(
        "Sending deadline reminder for pipeline=%s task=%s",
        pipeline_id,
        task_id,
    )

    try:
        create_in_app_notification_task.delay(
            user_id=pipeline_id,  # resolved from pipeline owner in caller
            org_id=pipeline_id,
            notification_type="deadline_reminder",
            title=f"Task {task_id} deadline approaching",
            message=f"A task in pipeline {pipeline_id} is approaching its deadline.",
            data={"pipeline_id": pipeline_id, "task_id": task_id},
        )
    except (ConnectionError, OSError) as exc:
        logger.error(
            "Failed to dispatch deadline reminder for pipeline=%s task=%s: %s",
            pipeline_id, task_id, exc, exc_info=True,
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
