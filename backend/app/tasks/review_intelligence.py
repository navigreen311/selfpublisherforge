"""Celery tasks for Review Intelligence: periodic review fetch,
sentiment analysis batch, alert checking.

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

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="review_intelligence.analyze_pending_reviews",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1800,
    time_limit=3600,
)
def analyze_pending_reviews(self, org_id: str, book_id: str | None = None):
    """Analyze reviews that have not yet been sentiment-analyzed.

    Picks up reviews where sentiment is NULL and runs them through
    the sentiment analysis pipeline.
    """
    logger.info(f"Starting pending review analysis for org {org_id}")

    async def _analyze():
        from sqlalchemy import and_, select

        from app.database import async_session
        from app.modules.review_intelligence.models import BookReview
        from app.modules.review_intelligence.sentiment import analyze_sentiment_llm

        async with async_session() as db:
            try:
                stmt = select(BookReview).where(
                    and_(
                        BookReview.org_id == UUID(org_id),
                        BookReview.sentiment.is_(None),
                        BookReview.body.isnot(None),
                        BookReview.deleted_at.is_(None),
                    )
                )
                if book_id:
                    stmt = stmt.where(BookReview.book_id == UUID(book_id))

                stmt = stmt.limit(100)

                result = await db.execute(stmt)
                reviews = list(result.scalars().all())

                logger.info(f"Found {len(reviews)} reviews to analyze")
                analyzed = 0

                for review in reviews:
                    try:
                        analysis = await analyze_sentiment_llm(
                            review.body, review.star_rating
                        )
                        review.sentiment = analysis.sentiment.value
                        review.sentiment_score = analysis.score
                        review.themes = {
                            "themes": analysis.themes,
                            "key_phrases": analysis.key_phrases,
                            "complaints": analysis.complaints,
                            "praise": analysis.praise,
                        }
                        review.analyzed_at = datetime.now(UTC)
                        db.add(review)
                        analyzed += 1
                    except (ValueError, KeyError, TypeError) as e:
                        logger.error(
                            f"Failed to parse sentiment result for review {review.id}: {e}",
                            exc_info=True,
                        )
                        # Graceful degradation: mark as unknown so it's not retried endlessly
                        review.sentiment = "unknown"
                        review.sentiment_score = 0.0
                        review.analyzed_at = datetime.now(UTC)
                        db.add(review)
                    except (ConnectionError, TimeoutError, OSError) as e:
                        logger.error(
                            f"AI service unavailable for review {review.id}: {e}",
                            exc_info=True,
                        )
                        # Graceful degradation: mark as unknown for now, can re-analyze later
                        review.sentiment = "unknown"
                        review.sentiment_score = 0.0
                        review.analyzed_at = datetime.now(UTC)
                        db.add(review)

                await db.commit()
                logger.info(
                    f"Successfully analyzed {analyzed}/{len(reviews)} reviews"
                )
                return {"analyzed": analyzed, "total": len(reviews)}
            except SQLAlchemyError as e:
                logger.error(
                    f"Database error during review analysis for org {org_id}: {e}",
                    exc_info=True,
                )
                await db.rollback()
                raise

    try:
        return _run_async(_analyze())
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as e:
        logger.error(f"Task analyze_pending_reviews failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    name="review_intelligence.check_alerts",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=600,
)
def check_alerts(self, org_id: str, book_id: str):
    """Run all alert checks for a specific book.

    Checks for:
    - Negative review spike
    - Review velocity drop
    - Star rating decline
    - Competitor review surge
    """
    logger.info(f"Running alert checks for org {org_id}, book {book_id}")

    async def _check():
        from app.database import async_session
        from app.modules.review_intelligence.alerts import run_all_checks

        async with async_session() as db:
            try:
                alerts = await run_all_checks(db, UUID(org_id), UUID(book_id))
                await db.commit()

                alert_count = len(alerts)
                logger.info(f"Created {alert_count} alerts for book {book_id}")
                return {
                    "alerts_created": alert_count,
                    "alert_types": [a.alert_type for a in alerts],
                }
            except SQLAlchemyError as e:
                logger.error(
                    f"Database error during alert checks for book {book_id}: {e}",
                    exc_info=True,
                )
                await db.rollback()
                raise

    try:
        return _run_async(_check())
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as e:
        logger.error(f"Alert check task failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    name="review_intelligence.compute_velocity_snapshots",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    soft_time_limit=300,
    time_limit=600,
)
def compute_velocity_snapshots(self, org_id: str, book_id: str, period: str = "weekly"):
    """Compute and store velocity snapshots for a book.

    Calculates review counts and stats for the most recent period
    and stores them in the review_velocity_snapshots table.
    """
    logger.info(
        f"Computing velocity snapshot for org {org_id}, book {book_id}, period {period}"
    )

    async def _compute():
        from sqlalchemy import and_, func, select

        from app.database import async_session
        from app.modules.review_intelligence.models import BookReview
        from app.modules.review_intelligence.schemas import VelocityPeriod
        from app.modules.review_intelligence.velocity import save_velocity_snapshot

        async with async_session() as db:
            try:
                vel_period = VelocityPeriod(period)

                now = datetime.now(UTC)
                if vel_period == VelocityPeriod.DAILY:
                    period_start = now.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ) - timedelta(days=1)
                    period_end = period_start + timedelta(days=1)
                elif vel_period == VelocityPeriod.WEEKLY:
                    # Start from last Monday
                    days_since_monday = now.weekday()
                    period_end = now.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ) - timedelta(days=days_since_monday)
                    period_start = period_end - timedelta(weeks=1)
                else:  # monthly
                    period_end = now.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0
                    )
                    period_start = (period_end - timedelta(days=1)).replace(day=1)

                # Aggregate reviews for the period
                stmt = select(
                    func.count(BookReview.id).label("count"),
                    func.avg(BookReview.star_rating).label("avg_rating"),
                    func.count(
                        func.nullif(BookReview.sentiment == "positive", False)
                    ).label("positive"),
                    func.count(
                        func.nullif(BookReview.sentiment == "neutral", False)
                    ).label("neutral"),
                    func.count(
                        func.nullif(BookReview.sentiment == "negative", False)
                    ).label("negative"),
                ).where(
                    and_(
                        BookReview.org_id == UUID(org_id),
                        BookReview.book_id == UUID(book_id),
                        BookReview.review_date >= period_start,
                        BookReview.review_date < period_end,
                        BookReview.deleted_at.is_(None),
                    )
                )

                result = await db.execute(stmt)
                row = result.one()

                snapshot = await save_velocity_snapshot(
                    db=db,
                    org_id=UUID(org_id),
                    book_id=UUID(book_id),
                    period=vel_period,
                    period_start=period_start,
                    period_end=period_end,
                    review_count=row.count or 0,
                    avg_rating=(
                        round(float(row.avg_rating), 2) if row.avg_rating else None
                    ),
                    positive_count=row.positive or 0,
                    neutral_count=row.neutral or 0,
                    negative_count=row.negative or 0,
                )

                await db.commit()
                logger.info(
                    f"Saved velocity snapshot: {row.count} reviews for "
                    f"{period_start.isoformat()} to {period_end.isoformat()}"
                )
                return {
                    "snapshot_id": str(snapshot.id),
                    "review_count": row.count or 0,
                    "period": period,
                }
            except SQLAlchemyError as e:
                logger.error(
                    f"Database error during velocity snapshot for book {book_id}: {e}",
                    exc_info=True,
                )
                await db.rollback()
                raise

    try:
        return _run_async(_compute())
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as e:
        logger.error(f"Velocity snapshot task failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(name="review_intelligence.compute_reputation", soft_time_limit=300, time_limit=600)
def compute_reputation(org_id: str, book_id: str):
    """Recompute reputation score for a book."""
    logger.info(f"Computing reputation for org {org_id}, book {book_id}")

    async def _compute():
        from app.database import async_session
        from app.modules.review_intelligence.service import compute_reputation_score

        async with async_session() as db:
            try:
                metrics = await compute_reputation_score(
                    db, UUID(org_id), UUID(book_id)
                )
                await db.commit()
                logger.info(
                    f"Reputation computed: score={metrics.overall_score}, "
                    f"grade={metrics.health_grade}"
                )
                return {
                    "overall_score": metrics.overall_score,
                    "health_grade": metrics.health_grade,
                    "total_reviews": metrics.total_reviews,
                }
            except SQLAlchemyError as e:
                logger.error(
                    f"Database error during reputation computation for book {book_id}: {e}",
                    exc_info=True,
                )
                await db.rollback()
                raise

    return _run_async(_compute())


# --- Periodic task schedule (to be included in celery beat config) ---

REVIEW_INTELLIGENCE_BEAT_SCHEDULE = {
    "analyze-pending-reviews-hourly": {
        "task": "review_intelligence.analyze_pending_reviews",
        "schedule": 3600.0,  # Every hour
        "kwargs": {"org_id": "all"},
    },
    "compute-velocity-snapshots-daily": {
        "task": "review_intelligence.compute_velocity_snapshots",
        "schedule": 86400.0,  # Every 24 hours
        "kwargs": {"org_id": "all", "book_id": "all", "period": "daily"},
    },
}
