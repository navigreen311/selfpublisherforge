"""Celery tasks for analytics background processing.

Tasks:
  - daily_metric_aggregation: Computes and stores daily portfolio metric snapshots
  - scheduled_report_generation: Generates scheduled/queued reports
  - royalty_sync: Placeholder for periodic royalty data sync from platforms
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.tasks import celery_app
from app.database import async_session

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="analytics.daily_metric_aggregation",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def daily_metric_aggregation(self, org_id: str | None = None) -> dict[str, Any]:
    """Compute and store daily portfolio metric snapshots.

    If org_id is provided, only aggregates for that org.
    Otherwise, aggregates for all active organizations.
    """
    logger.info("Starting daily metric aggregation (org_id=%s)", org_id)

    async def _aggregate():
        from app.modules.analytics.metrics import compute_portfolio_metrics
        from app.modules.analytics.aggregator import save_portfolio_snapshot
        from app.modules.analytics.models import RoyaltyRecord
        from sqlalchemy import select, func, and_

        async with async_session() as db:
            try:
                if org_id:
                    org_ids = [UUID(org_id)]
                else:
                    # Get all distinct org_ids from royalty records
                    query = select(func.distinct(RoyaltyRecord.org_id)).where(
                        RoyaltyRecord.deleted_at.is_(None)
                    )
                    result = await db.execute(query)
                    org_ids = [row[0] for row in result.all()]

                now = datetime.now(timezone.utc)
                snapshots_created = 0

                for oid in org_ids:
                    try:
                        metrics = await compute_portfolio_metrics(db, oid, as_of=now)
                        await save_portfolio_snapshot(
                            db,
                            oid,
                            snapshot_date=now,
                            metrics_data={
                                "total_books": metrics.total_books,
                                "total_revenue": str(metrics.total_revenue),
                                "total_units_sold": metrics.total_units_sold,
                                "total_expenses": str(metrics.total_expenses),
                                "net_profit": str(metrics.net_profit),
                                "avg_roi": str(metrics.avg_roi),
                                "platform_breakdown": {
                                    k: str(v) for k, v in metrics.platform_breakdown.items()
                                },
                                "format_breakdown": metrics.format_breakdown,
                                "top_books": metrics.top_books,
                            },
                        )
                        snapshots_created += 1
                    except Exception as exc:
                        logger.error("Failed to aggregate metrics for org %s: %s", oid, exc)

                await db.commit()
                return {"snapshots_created": snapshots_created, "org_count": len(org_ids)}

            except Exception:
                await db.rollback()
                raise

    try:
        result = _run_async(_aggregate())
        logger.info("Daily metric aggregation complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Daily metric aggregation failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="analytics.scheduled_report_generation",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scheduled_report_generation(self, report_id: str) -> dict[str, Any]:
    """Generate a queued report by its ID.

    Used for async report generation dispatched from the API.
    """
    logger.info("Starting report generation for report_id=%s", report_id)

    async def _generate():
        from app.modules.analytics.models import Report
        from app.modules.analytics.report_builder import generate_report
        from sqlalchemy import select, and_

        async with async_session() as db:
            try:
                query = select(Report).where(
                    and_(
                        Report.id == UUID(report_id),
                        Report.deleted_at.is_(None),
                    )
                )
                result = await db.execute(query)
                report = result.scalar_one_or_none()

                if not report:
                    return {"error": f"Report {report_id} not found"}

                report = await generate_report(db, report)
                await db.commit()

                return {
                    "report_id": str(report.id),
                    "status": report.status,
                    "file_path": report.file_path,
                    "file_size": report.file_size,
                }

            except Exception:
                await db.rollback()
                raise

    try:
        result = _run_async(_generate())
        logger.info("Report generation complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Report generation failed for %s: %s", report_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="analytics.royalty_sync",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
)
def royalty_sync(self, org_id: str, platform: str) -> dict[str, Any]:
    """Sync royalty data from a publishing platform API.

    This is a placeholder for future API-based royalty import.
    In production, this would authenticate with KDP/IngramSpark/D2D APIs
    and pull latest royalty reports.
    """
    logger.info("Starting royalty sync for org_id=%s, platform=%s", org_id, platform)

    # Placeholder: API integration would go here
    return {
        "org_id": org_id,
        "platform": platform,
        "status": "not_implemented",
        "message": "API-based royalty sync is not yet implemented. Use CSV import.",
    }


# ---------- Celery Beat Schedule (for periodic tasks) ----------
# Merge analytics tasks into the existing beat schedule rather than overwriting it.

_existing_schedule = getattr(celery_app.conf, "beat_schedule", None) or {}
_existing_schedule["daily-metric-aggregation"] = {
    "task": "analytics.daily_metric_aggregation",
    "schedule": 86400.0,  # Every 24 hours
    "args": (None,),  # All orgs
}
celery_app.conf.beat_schedule = _existing_schedule
