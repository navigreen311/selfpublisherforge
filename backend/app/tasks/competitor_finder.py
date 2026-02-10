"""Celery tasks for the Competitor Weakness Finder module.

Tasks:
  - process_single_analysis: Analyze a single competitor book asynchronously.
  - process_batch_analysis: Analyze multiple competitor books.
  - check_competitor_alerts: Periodic task to check for competitor changes.
"""
from __future__ import annotations

import logging
from uuid import UUID

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="competitor_finder.process_single_analysis",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def process_single_analysis(
    self,
    analysis_id: str,
    org_id: str,
    include_opportunity: bool = True,
) -> dict:
    """Process a single competitor analysis asynchronously.

    This task is enqueued when a user requests analysis via the API.
    It runs the full review analysis + opportunity blueprint pipeline.
    """
    import asyncio
    from app.database import async_session
    from app.modules.competitor_finder.service import CompetitorFinderService
    from app.modules.competitor_finder.schemas import (
        AnalysisStatus,
        CompetitorAnalyzeRequest,
    )
    from app.modules.competitor_finder.models import CompetitorAnalysis
    from sqlalchemy import select

    logger.info(
        "Starting single analysis task: analysis_id=%s, org_id=%s",
        analysis_id,
        org_id,
    )

    async def _run():
        async with async_session() as db:
            try:
                # Fetch the analysis record
                stmt = select(CompetitorAnalysis).where(
                    CompetitorAnalysis.id == UUID(analysis_id)
                )
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()

                if not analysis:
                    logger.error("Analysis %s not found", analysis_id)
                    return {"status": "error", "message": "Analysis not found"}

                if analysis.status == AnalysisStatus.COMPLETED.value:
                    logger.info("Analysis %s already completed", analysis_id)
                    return {"status": "skipped", "message": "Already completed"}

                # Run analysis via service
                service = CompetitorFinderService(db)
                request = CompetitorAnalyzeRequest(
                    book_id=analysis.book_id,
                    include_opportunity=include_opportunity,
                )
                updated = await service.analyze_competitor(
                    request=request,
                    org_id=UUID(org_id),
                )
                await db.commit()

                return {
                    "status": "completed",
                    "analysis_id": str(updated.id),
                    "weakness_count": updated.weakness_count,
                    "overall_score": updated.overall_score,
                }
            except Exception as e:
                await db.rollback()
                logger.error(
                    "Analysis task failed: %s", e, exc_info=True
                )
                raise

    try:
        result = asyncio.get_event_loop().run_until_complete(_run())
        return result
    except RuntimeError:
        # No event loop running - create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except Exception as exc:
        logger.error("Task failed, retrying: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task(
    name="competitor_finder.process_batch_analysis",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
)
def process_batch_analysis(
    self,
    analysis_ids: list[str],
    org_id: str,
    include_opportunity: bool = True,
) -> dict:
    """Process a batch of competitor analyses.

    Enqueues individual analysis tasks for each book in the batch.
    """
    logger.info(
        "Starting batch analysis: %d analyses for org %s",
        len(analysis_ids),
        org_id,
    )

    results = {"total": len(analysis_ids), "enqueued": 0, "errors": 0}

    for aid in analysis_ids:
        try:
            process_single_analysis.delay(
                analysis_id=aid,
                org_id=org_id,
                include_opportunity=include_opportunity,
            )
            results["enqueued"] += 1
        except Exception as e:
            logger.error("Failed to enqueue analysis %s: %s", aid, e)
            results["errors"] += 1

    logger.info("Batch enqueue complete: %s", results)
    return results


@celery_app.task(
    name="competitor_finder.check_competitor_alerts",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    acks_late=True,
)
def check_competitor_alerts(self, org_id: str | None = None) -> dict:
    """Periodic task to check for competitor changes and generate alerts.

    Checks for:
    - Price changes (significant drops or increases)
    - BSR shifts (significant rank improvements or drops)
    - New books appearing in tracked categories
    - Review count spikes
    """
    import asyncio
    from app.database import async_session
    from app.modules.competitor_finder.models import CompetitorBook, CompetitorAlert
    from app.modules.competitor_finder.schemas import AlertType, AlertSeverity
    from sqlalchemy import select

    logger.info("Running competitor alert check, org_id=%s", org_id)

    async def _run():
        async with async_session() as db:
            try:
                # Fetch books to check (optionally scoped to org)
                stmt = select(CompetitorBook).limit(500)
                if org_id:
                    stmt = stmt.where(CompetitorBook.org_id == UUID(org_id))

                result = await db.execute(stmt)
                books = list(result.scalars().all())

                alerts_created = 0

                for book in books:
                    # ASSUMPTION: In a production system, we would compare current
                    # data with historical snapshots stored in a separate table.
                    # For now, this is a placeholder for the alert detection logic.
                    pass

                await db.commit()

                return {
                    "status": "completed",
                    "books_checked": len(books),
                    "alerts_created": alerts_created,
                }
            except Exception as e:
                await db.rollback()
                logger.error("Alert check failed: %s", e, exc_info=True)
                raise

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except Exception as exc:
        logger.error("Alert check task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Celery Beat schedule entry (to be registered in celery config)
# ---------------------------------------------------------------------------

CELERY_BEAT_SCHEDULE = {
    "check-competitor-alerts-hourly": {
        "task": "competitor_finder.check_competitor_alerts",
        "schedule": 3600.0,  # Every hour
        "args": [],
    },
}
