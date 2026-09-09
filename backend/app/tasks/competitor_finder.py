"""Celery tasks for the Competitor Weakness Finder module.

Tasks:
  - process_single_analysis: Analyze a single competitor book asynchronously.
  - process_batch_analysis: Analyze multiple competitor books.
  - check_competitor_alerts: Periodic task to check for competitor changes.

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
from uuid import UUID

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="competitor_finder.process_single_analysis",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=300,
    time_limit=600,
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

    from sqlalchemy import select

    from app.database import async_session
    from app.modules.competitor_finder.models import CompetitorAnalysis
    from app.modules.competitor_finder.schemas import (
        AnalysisStatus,
        CompetitorAnalyzeRequest,
    )
    from app.modules.competitor_finder.service import CompetitorFinderService

    logger.info(
        "Starting single analysis task: analysis_id=%s, org_id=%s",
        analysis_id,
        org_id,
    )

    async def _run():
        async with async_session() as db:
            try:
                # Fetch the analysis record
                stmt = select(CompetitorAnalysis).where(CompetitorAnalysis.id == UUID(analysis_id))
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
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error("Database error in analysis task: %s", e, exc_info=True)
                raise
            except (ValueError, KeyError) as e:
                await db.rollback()
                logger.error("Validation error in analysis task: %s", e, exc_info=True)
                raise

    try:
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(_run())
            return result
        finally:
            loop.close()
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("Task failed, retrying: %s", exc, exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="competitor_finder.process_batch_analysis",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
    soft_time_limit=60,
    time_limit=120,
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
        except (ConnectionError, OSError) as e:
            logger.error("Broker connection error enqueueing analysis %s: %s", aid, e, exc_info=True)
            results["errors"] += 1
        except Exception as e:
            logger.error("Failed to enqueue analysis %s: %s", aid, e, exc_info=True)
            results["errors"] += 1

    logger.info("Batch enqueue complete: %s", results)
    return results


@celery_app.task(
    name="competitor_finder.check_competitor_alerts",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    acks_late=True,
    soft_time_limit=300,
    time_limit=600,
)
def check_competitor_alerts(self, org_id: str | None = None) -> dict:
    """Periodic task to check for competitor changes and generate alerts.

    Compares each tracked competitor book's current data against its most
    recent historical snapshot and fires alerts when thresholds are exceeded.

    Alert conditions:
    - Price change > 20%: price_change alert (critical if > 50%)
    - BSR improvement > 50 positions: bsr_shift alert
    - New reviews (review count increase): review_spike alert
    - Rating drop > 0.3 stars: rating_drop alert (critical if > 1.0)

    Returns a dict with books_checked, alerts_created, and alert_summary.
    """
    import asyncio

    from sqlalchemy import select

    from app.database import async_session
    from app.modules.competitor_finder.models import CompetitorAlert, CompetitorBook
    from app.modules.competitor_finder.schemas import AlertSeverity, AlertType

    logger.info("Running competitor alert check, org_id=%s", org_id)

    # Alert thresholds
    PRICE_CHANGE_THRESHOLD = 0.20  # 20% price change
    BSR_IMPROVEMENT_THRESHOLD = 50  # 50 positions improvement
    RATING_DROP_THRESHOLD = 0.3  # 0.3 star drop

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
                alert_summary: list[str] = []

                for book in books:
                    # Extract the most recent historical snapshot from bsr_history.
                    # bsr_history is a list of dicts: [{"date": ..., "bsr": ..., "price": ...}, ...]
                    history = book.bsr_history or []
                    if not history:
                        continue

                    # The last entry in bsr_history is the most recent snapshot
                    latest_snapshot = history[-1] if isinstance(history, list) else None
                    if not latest_snapshot or not isinstance(latest_snapshot, dict):
                        continue

                    snapshot_price = latest_snapshot.get("price")
                    snapshot_bsr = latest_snapshot.get("bsr")

                    # Also pull previous review count and rating from metadata_json
                    # if available, since bsr_history only tracks bsr and price.
                    meta = book.metadata_json or {}
                    snapshot_reviews_count = meta.get("last_reviews_count")
                    snapshot_rating = meta.get("last_rating")

                    # --- Price change detection (>20% change) ---
                    if book.price is not None and snapshot_price is not None and float(snapshot_price) > 0:
                        current_price = float(book.price)
                        previous_price = float(snapshot_price)
                        price_pct_change = abs(current_price - previous_price) / previous_price

                        if price_pct_change > PRICE_CHANGE_THRESHOLD:
                            direction = "increased" if current_price > previous_price else "decreased"
                            severity = AlertSeverity.CRITICAL if price_pct_change > 0.50 else AlertSeverity.WARNING
                            alert = CompetitorAlert(
                                org_id=book.org_id,
                                book_id=book.id,
                                alert_type=AlertType.PRICE_CHANGE.value,
                                severity=severity.value,
                                title=f"Price {direction} {price_pct_change:.0%} for '{book.title}'",
                                description=(
                                    f"Price {direction} from ${previous_price:.2f} to "
                                    f"${current_price:.2f} ({price_pct_change:.0%} change)."
                                ),
                                data={
                                    "previous_price": previous_price,
                                    "current_price": current_price,
                                    "change_pct": round(price_pct_change, 4),
                                    "direction": direction,
                                    "asin": book.asin,
                                },
                            )
                            db.add(alert)
                            alerts_created += 1
                            msg = f"Price {direction} {price_pct_change:.0%} for " f"'{book.title}' (ASIN: {book.asin})"
                            alert_summary.append(msg)
                            logger.info("Alert generated: %s", msg)

                    # --- BSR improvement detection (>50 positions) ---
                    if book.bsr_current is not None and snapshot_bsr is not None:
                        current_bsr = int(book.bsr_current)
                        previous_bsr = int(snapshot_bsr)
                        bsr_improvement = previous_bsr - current_bsr

                        if bsr_improvement > BSR_IMPROVEMENT_THRESHOLD:
                            severity = (
                                AlertSeverity.CRITICAL
                                if bsr_improvement > 500
                                else AlertSeverity.WARNING
                                if bsr_improvement > 100
                                else AlertSeverity.INFO
                            )
                            alert = CompetitorAlert(
                                org_id=book.org_id,
                                book_id=book.id,
                                alert_type=AlertType.BSR_SHIFT.value,
                                severity=severity.value,
                                title=f"BSR improved by {bsr_improvement} positions for '{book.title}'",
                                description=(
                                    f"BSR improved from #{previous_bsr:,} to #{current_bsr:,} "
                                    f"({bsr_improvement:,} positions). This competitor is gaining traction."
                                ),
                                data={
                                    "previous_bsr": previous_bsr,
                                    "current_bsr": current_bsr,
                                    "improvement": bsr_improvement,
                                    "asin": book.asin,
                                },
                            )
                            db.add(alert)
                            alerts_created += 1
                            msg = (
                                f"BSR improved by {bsr_improvement:,} positions for "
                                f"'{book.title}' (ASIN: {book.asin})"
                            )
                            alert_summary.append(msg)
                            logger.info("Alert generated: %s", msg)

                    # --- New reviews detection (review count increase) ---
                    if snapshot_reviews_count is not None and book.reviews_count > int(snapshot_reviews_count):
                        new_review_count = book.reviews_count - int(snapshot_reviews_count)
                        severity = AlertSeverity.WARNING if new_review_count >= 10 else AlertSeverity.INFO
                        alert = CompetitorAlert(
                            org_id=book.org_id,
                            book_id=book.id,
                            alert_type=AlertType.REVIEW_SPIKE.value,
                            severity=severity.value,
                            title=f"{new_review_count} new review(s) for '{book.title}'",
                            description=(
                                f"Review count went from {int(snapshot_reviews_count):,} to "
                                f"{book.reviews_count:,} ({new_review_count:,} new)."
                            ),
                            data={
                                "previous_reviews": int(snapshot_reviews_count),
                                "current_reviews": book.reviews_count,
                                "new_reviews": new_review_count,
                                "asin": book.asin,
                            },
                        )
                        db.add(alert)
                        alerts_created += 1
                        msg = f"{new_review_count} new review(s) for " f"'{book.title}' (ASIN: {book.asin})"
                        alert_summary.append(msg)
                        logger.info("Alert generated: %s", msg)

                    # --- Rating drop detection (>0.3 stars) ---
                    if book.rating is not None and snapshot_rating is not None:
                        current_rating = float(book.rating)
                        previous_rating = float(snapshot_rating)
                        rating_drop = previous_rating - current_rating

                        if rating_drop > RATING_DROP_THRESHOLD:
                            severity = AlertSeverity.CRITICAL if rating_drop > 1.0 else AlertSeverity.WARNING
                            alert = CompetitorAlert(
                                org_id=book.org_id,
                                book_id=book.id,
                                alert_type="rating_drop",
                                severity=severity.value,
                                title=f"Rating dropped by {rating_drop:.1f} stars for '{book.title}'",
                                description=(
                                    f"Rating fell from {previous_rating:.1f} to "
                                    f"{current_rating:.1f} ({rating_drop:.1f} star drop)."
                                ),
                                data={
                                    "previous_rating": previous_rating,
                                    "current_rating": current_rating,
                                    "drop": round(rating_drop, 2),
                                    "asin": book.asin,
                                },
                            )
                            db.add(alert)
                            alerts_created += 1
                            msg = (
                                f"Rating dropped by {rating_drop:.1f} stars for " f"'{book.title}' (ASIN: {book.asin})"
                            )
                            alert_summary.append(msg)
                            logger.info("Alert generated: %s", msg)

                    # Update metadata_json with current values as the new baseline
                    # for next alert check cycle (reviews_count and rating).
                    updated_meta = dict(meta)
                    updated_meta["last_reviews_count"] = book.reviews_count
                    if book.rating is not None:
                        updated_meta["last_rating"] = float(book.rating)
                    book.metadata_json = updated_meta

                await db.commit()

                logger.info(
                    "Competitor alert check complete: %d books checked, %d alerts created",
                    len(books),
                    alerts_created,
                )

                return {
                    "status": "completed",
                    "books_checked": len(books),
                    "alerts_created": alerts_created,
                    "alert_summary": alert_summary,
                }
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error("Database error in alert check: %s", e, exc_info=True)
                raise
            except (ValueError, TypeError) as e:
                await db.rollback()
                logger.error("Data conversion error in alert check: %s", e, exc_info=True)
                raise

    try:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("Alert check task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc) from exc


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
