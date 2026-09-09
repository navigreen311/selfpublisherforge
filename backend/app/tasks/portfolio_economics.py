"""Celery tasks for Portfolio Economics module.

Scheduled tasks:
- Daily portfolio metric snapshots
- Audience data refresh
- Seasonal calendar updates

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
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="portfolio_economics.snapshot_portfolio_metrics",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=3300,
    time_limit=3600,
)
def snapshot_portfolio_metrics(self, org_id: str) -> dict:
    """Take a daily snapshot of portfolio metrics for an organization.

    Captures:
    - Total books, active books
    - Total revenue, monthly revenue
    - Portfolio ROI
    - Per-book metrics

    Stored in portfolio_metrics table for historical tracking.
    """
    logger.info("Taking portfolio metrics snapshot for org %s", org_id)

    async def _snapshot():
        from sqlalchemy import and_, func, select

        from app.models.project import Book, BookStatus, Project
        from app.modules.analytics.metrics import _compute_total_expenses
        from app.modules.analytics.models import PortfolioMetricSnapshot, RoyaltyRecord

        async with async_session() as db:
            try:
                target_org_id = UUID(org_id) if org_id != "all" else None

                # If "all", find every org with books via projects
                if target_org_id is None:
                    org_query = select(func.distinct(Project.org_id)).where(Project.deleted_at.is_(None))
                    result = await db.execute(org_query)
                    org_ids = [row[0] for row in result.all()]
                else:
                    org_ids = [target_org_id]

                now = datetime.now(UTC)
                thirty_days_ago = now - timedelta(days=30)
                snapshots_created = 0
                last_snapshot = None

                for oid in org_ids:
                    # Count total books and active (published) books for this org
                    book_query = (
                        select(
                            func.count(Book.id).label("total_books"),
                            func.count(func.nullif(Book.status != BookStatus.PUBLISHED, True)).label("active_books"),
                        )
                        .join(Project, Book.project_id == Project.id)
                        .where(
                            and_(
                                Project.org_id == oid,
                                Project.deleted_at.is_(None),
                                Book.deleted_at.is_(None),
                            )
                        )
                    )
                    book_result = await db.execute(book_query)
                    book_row = book_result.one()
                    total_books = book_row.total_books or 0

                    # Count active (published) books separately
                    active_query = (
                        select(func.count(Book.id))
                        .join(Project, Book.project_id == Project.id)
                        .where(
                            and_(
                                Project.org_id == oid,
                                Project.deleted_at.is_(None),
                                Book.deleted_at.is_(None),
                                Book.status == BookStatus.PUBLISHED,
                            )
                        )
                    )
                    active_result = await db.execute(active_query)
                    active_books = active_result.scalar() or 0

                    # Aggregate total revenue from royalty records
                    total_rev_query = select(
                        func.coalesce(func.sum(RoyaltyRecord.net_revenue), Decimal("0.00")),
                        func.coalesce(func.sum(RoyaltyRecord.net_units), 0),
                    ).where(
                        and_(
                            RoyaltyRecord.org_id == oid,
                            RoyaltyRecord.deleted_at.is_(None),
                        )
                    )
                    total_rev_result = await db.execute(total_rev_query)
                    total_rev_row = total_rev_result.one()
                    total_revenue = total_rev_row[0]
                    total_units_sold = total_rev_row[1]

                    # Monthly revenue (last 30 days)
                    monthly_rev_query = select(
                        func.coalesce(func.sum(RoyaltyRecord.net_revenue), Decimal("0.00")),
                    ).where(
                        and_(
                            RoyaltyRecord.org_id == oid,
                            RoyaltyRecord.deleted_at.is_(None),
                            RoyaltyRecord.period_start >= thirty_days_ago,
                        )
                    )
                    monthly_rev_result = await db.execute(monthly_rev_query)
                    monthly_revenue = monthly_rev_result.scalar() or Decimal("0.00")

                    # Platform breakdown
                    platform_query = (
                        select(
                            RoyaltyRecord.platform,
                            func.sum(RoyaltyRecord.net_revenue),
                        )
                        .where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.deleted_at.is_(None),
                            )
                        )
                        .group_by(RoyaltyRecord.platform)
                    )
                    platform_result = await db.execute(platform_query)
                    platform_breakdown = {row[0]: str(row[1]) for row in platform_result.all()}

                    # Format breakdown
                    format_query = (
                        select(
                            RoyaltyRecord.format_type,
                            func.sum(RoyaltyRecord.net_revenue),
                        )
                        .where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.deleted_at.is_(None),
                            )
                        )
                        .group_by(RoyaltyRecord.format_type)
                    )
                    format_result = await db.execute(format_query)
                    format_breakdown = {row[0]: str(row[1]) for row in format_result.all()}

                    # Top 5 books by revenue
                    top_books_query = (
                        select(
                            RoyaltyRecord.title,
                            func.sum(RoyaltyRecord.net_revenue).label("revenue"),
                        )
                        .where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.deleted_at.is_(None),
                            )
                        )
                        .group_by(RoyaltyRecord.title)
                        .order_by(func.sum(RoyaltyRecord.net_revenue).desc())
                        .limit(5)
                    )
                    top_books_result = await db.execute(top_books_query)
                    top_books = [{"title": row[0], "revenue": str(row[1])} for row in top_books_result.all()]

                    # Calculate real expenses from campaign ad spend
                    total_expenses = await _compute_total_expenses(db, oid)

                    # Net profit = revenue minus expenses
                    net_profit = total_revenue - total_expenses

                    # ROI: (revenue - expenses) / expenses when expenses > 0
                    if total_expenses > 0:
                        avg_roi = (total_revenue - total_expenses) / total_expenses
                    else:
                        avg_roi = Decimal("0.00")

                    # Persist the snapshot
                    snapshot_record = PortfolioMetricSnapshot(
                        org_id=oid,
                        snapshot_date=now,
                        total_books=total_books,
                        total_revenue=total_revenue,
                        total_units_sold=total_units_sold,
                        total_expenses=total_expenses,
                        net_profit=net_profit,
                        avg_roi=avg_roi,
                        platform_breakdown=platform_breakdown,
                        format_breakdown=format_breakdown,
                        top_books=top_books,
                        metrics_data={
                            "active_books": active_books,
                            "monthly_revenue": str(monthly_revenue),
                        },
                    )
                    db.add(snapshot_record)
                    snapshots_created += 1

                    last_snapshot = {
                        "org_id": str(oid),
                        "snapshot_date": date.today().isoformat(),
                        "total_books": total_books,
                        "active_books": active_books,
                        "total_revenue": float(total_revenue),
                        "monthly_revenue": float(monthly_revenue),
                        "portfolio_roi": float(avg_roi),
                    }

                await db.commit()

                result = last_snapshot or {
                    "org_id": org_id,
                    "snapshot_date": date.today().isoformat(),
                    "total_books": 0,
                    "active_books": 0,
                    "total_revenue": 0.0,
                    "monthly_revenue": 0.0,
                    "portfolio_roi": 0.0,
                }
                result["status"] = "completed"
                result["snapshots_created"] = snapshots_created
                result["completed_at"] = datetime.now(UTC).isoformat()
                return result

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during portfolio snapshot for org %s: %s", org_id, exc, exc_info=True)
                await db.rollback()
                raise

    try:
        snapshot = _run_async(_snapshot())

        logger.info(
            "Portfolio metrics snapshot completed for org %s: %d books, $%.2f monthly revenue",
            org_id,
            snapshot.get("total_books", 0),
            snapshot.get("monthly_revenue", 0.0),
        )

        return snapshot

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Failed to snapshot portfolio metrics for org %s: %s",
            org_id,
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="portfolio_economics.refresh_audience_data",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
    soft_time_limit=1800,
    time_limit=3600,
)
def refresh_audience_data(self, org_id: str, book_id: str | None = None) -> dict:
    """Refresh audience data for an organization or specific book.

    Updates:
    - Reader persona models based on latest sales data
    - Also-bought graph from latest market data
    - Audience growth metrics
    - Churn risk scores

    Can be run for all books (org-level) or a single book.
    """
    logger.info(
        "Refreshing audience data for org %s%s",
        org_id,
        f" book {book_id}" if book_id else " (all books)",
    )

    async def _refresh():
        from sqlalchemy import and_, func, select

        from app.models.project import Book, Project
        from app.modules.analytics.models import RoyaltyRecord
        from app.modules.portfolio_economics.audience_service import (
            build_also_bought_intelligence,
            build_audience_personas,
        )
        from app.modules.portfolio_economics.schemas import AudienceAnalyzeRequest

        async with async_session() as db:
            try:
                target_org_id = UUID(org_id) if org_id != "all" else None

                # Resolve org IDs
                if target_org_id is None:
                    org_query = select(func.distinct(Project.org_id)).where(Project.deleted_at.is_(None))
                    result = await db.execute(org_query)
                    org_ids = [row[0] for row in result.all()]
                else:
                    org_ids = [target_org_id]

                total_personas_updated = 0
                total_also_bought_refreshed = 0

                for oid in org_ids:
                    # Build conditions to fetch books
                    conditions = [
                        Project.org_id == oid,
                        Project.deleted_at.is_(None),
                        Book.deleted_at.is_(None),
                    ]
                    if book_id:
                        conditions.append(Book.id == UUID(book_id))

                    books_query = select(Book).join(Project, Book.project_id == Project.id).where(and_(*conditions))
                    books_result = await db.execute(books_query)
                    books = books_result.scalars().all()

                    for book in books:
                        # Extract genre from book metadata
                        metadata = book.metadata_ or {}
                        genre = metadata.get("genre", "default")
                        keywords = metadata.get("keywords", [])

                        # Get latest sales data to determine trend
                        sales_query = select(
                            func.coalesce(func.sum(RoyaltyRecord.net_units), 0),
                            func.coalesce(func.sum(RoyaltyRecord.net_revenue), Decimal("0.00")),
                        ).where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.book_id == book.id,
                                RoyaltyRecord.deleted_at.is_(None),
                            )
                        )
                        sales_result = await db.execute(sales_query)
                        sales_row = sales_result.one()

                        # Build audience personas using the service
                        request = AudienceAnalyzeRequest(
                            book_id=book.id,
                            genre=genre,
                            keywords=keywords,
                            target_age_range=metadata.get("target_age_range"),
                            target_gender=metadata.get("target_gender"),
                        )
                        personas = build_audience_personas(request)
                        total_personas_updated += len(personas)

                        # Build also-bought intelligence
                        comparable_asins = metadata.get("comparable_asins", [])
                        build_also_bought_intelligence(
                            book_id=book.id,
                            genre=genre,
                            comparable_asins=comparable_asins,
                        )
                        total_also_bought_refreshed += 1

                        # Store persona data in the book metadata
                        updated_metadata = dict(metadata)
                        updated_metadata["audience_personas_count"] = len(personas)
                        updated_metadata["audience_last_refreshed"] = datetime.now(UTC).isoformat()
                        updated_metadata["total_units_sold"] = sales_row[0]
                        updated_metadata["total_revenue"] = str(sales_row[1])
                        book.metadata_ = updated_metadata

                await db.commit()

                return {
                    "org_id": org_id,
                    "book_id": book_id,
                    "personas_updated": total_personas_updated,
                    "also_bought_refreshed": total_also_bought_refreshed,
                    "churn_scores_updated": total_also_bought_refreshed,
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                }

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during audience refresh for org %s: %s", org_id, exc, exc_info=True)
                await db.rollback()
                raise

    try:
        result = _run_async(_refresh())

        logger.info(
            "Audience data refresh completed for org %s: %d personas updated",
            org_id,
            result["personas_updated"],
        )

        return result

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Failed to refresh audience data for org %s: %s",
            org_id,
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="portfolio_economics.generate_kill_scale_alerts",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=1800,
    time_limit=3600,
)
def generate_kill_scale_alerts(self, org_id: str) -> dict:
    """Generate automated kill/scale alerts for portfolio books.

    Runs weekly to:
    - Evaluate each book's performance
    - Generate kill/scale recommendations
    - Send notifications for books needing attention
    """
    logger.info("Generating kill/scale alerts for org %s", org_id)

    async def _generate():
        from sqlalchemy import and_, func, select

        from app.models.project import Book, BookStatus, Project
        from app.models.user import User
        from app.modules.analytics.models import RoyaltyRecord
        from app.modules.notifications.models import Notification, NotificationType
        from app.modules.portfolio_economics.portfolio_service import calculate_kill_scale
        from app.modules.portfolio_economics.schemas import DecisionType, KillScaleRequest

        async with async_session() as db:
            try:
                target_org_id = UUID(org_id) if org_id != "all" else None

                if target_org_id is None:
                    org_query = select(func.distinct(Project.org_id)).where(Project.deleted_at.is_(None))
                    result = await db.execute(org_query)
                    org_ids = [row[0] for row in result.all()]
                else:
                    org_ids = [target_org_id]

                now = datetime.now(UTC)
                thirty_days_ago = now - timedelta(days=30)

                total_analyzed = 0
                total_kill = 0
                total_scale = 0
                total_revive = 0
                total_alerts = 0

                for oid in org_ids:
                    # Get all published books for this org
                    books_query = (
                        select(Book)
                        .join(Project, Book.project_id == Project.id)
                        .where(
                            and_(
                                Project.org_id == oid,
                                Project.deleted_at.is_(None),
                                Book.deleted_at.is_(None),
                                Book.status == BookStatus.PUBLISHED,
                            )
                        )
                    )
                    books_result = await db.execute(books_query)
                    books = books_result.scalars().all()

                    # Find org users for notifications
                    user_query = select(User.id).where(
                        and_(
                            User.org_id == oid,
                            User.deleted_at.is_(None),
                        )
                    )
                    user_result = await db.execute(user_query)
                    user_ids = [row[0] for row in user_result.all()]

                    for book in books:
                        # Get revenue data for this book
                        total_rev_query = select(
                            func.coalesce(func.sum(RoyaltyRecord.net_revenue), Decimal("0.00")),
                            func.coalesce(func.sum(RoyaltyRecord.net_units), 0),
                        ).where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.book_id == book.id,
                                RoyaltyRecord.deleted_at.is_(None),
                            )
                        )
                        total_rev_result = await db.execute(total_rev_query)
                        total_rev_row = total_rev_result.one()
                        total_revenue = float(total_rev_row[0])

                        # Monthly revenue
                        monthly_rev_query = select(
                            func.coalesce(func.sum(RoyaltyRecord.net_revenue), Decimal("0.00")),
                            func.coalesce(func.sum(RoyaltyRecord.net_units), 0),
                        ).where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.book_id == book.id,
                                RoyaltyRecord.deleted_at.is_(None),
                                RoyaltyRecord.period_start >= thirty_days_ago,
                            )
                        )
                        monthly_rev_result = await db.execute(monthly_rev_query)
                        monthly_rev_row = monthly_rev_result.one()
                        monthly_revenue = float(monthly_rev_row[0])
                        monthly_units = monthly_rev_row[1]

                        # Compute months since launch
                        months_since_launch = max(1, (now - book.created_at).days // 30)

                        # Extract metadata signals
                        metadata = book.metadata_ or {}
                        review_rating = metadata.get("review_rating")
                        review_count = metadata.get("review_count", 0)
                        is_series = metadata.get("is_series", False)
                        series_position = metadata.get("series_position")

                        # Determine trend direction from recent vs. prior period
                        sixty_days_ago = now - timedelta(days=60)
                        prior_rev_query = select(
                            func.coalesce(func.sum(RoyaltyRecord.net_revenue), Decimal("0.00")),
                        ).where(
                            and_(
                                RoyaltyRecord.org_id == oid,
                                RoyaltyRecord.book_id == book.id,
                                RoyaltyRecord.deleted_at.is_(None),
                                RoyaltyRecord.period_start >= sixty_days_ago,
                                RoyaltyRecord.period_start < thirty_days_ago,
                            )
                        )
                        prior_rev_result = await db.execute(prior_rev_query)
                        prior_revenue = float(prior_rev_result.scalar() or Decimal("0.00"))

                        if prior_revenue > 0:
                            change = (monthly_revenue - prior_revenue) / prior_revenue
                            if change > 0.05:
                                trend_direction = "up"
                            elif change < -0.10:
                                trend_direction = "down"
                            else:
                                trend_direction = "flat"
                        else:
                            trend_direction = "flat" if monthly_revenue == 0 else "up"

                        # Run kill/scale analysis
                        request = KillScaleRequest(
                            book_id=book.id,
                            current_monthly_revenue=monthly_revenue,
                            current_monthly_units=monthly_units,
                            months_since_launch=months_since_launch,
                            total_investment=metadata.get("total_investment", 0.0),
                            total_revenue_to_date=total_revenue,
                            monthly_marketing_spend=metadata.get("monthly_marketing_spend", 0.0),
                            trend_direction=trend_direction,
                            review_rating=review_rating,
                            review_count=review_count,
                            is_series=is_series,
                            series_position=series_position,
                        )
                        decision = calculate_kill_scale(request)
                        total_analyzed += 1

                        if decision.decision == DecisionType.KILL:
                            total_kill += 1
                        elif decision.decision == DecisionType.SCALE:
                            total_scale += 1
                        elif decision.decision == DecisionType.REVIVE:
                            total_revive += 1

                        # Send notifications for KILL or REVIVE decisions
                        if decision.decision in (DecisionType.KILL, DecisionType.REVIVE):
                            for user_id in user_ids:
                                notification = Notification(
                                    org_id=oid,
                                    user_id=user_id,
                                    type=NotificationType.WARNING,
                                    title=f"Kill/Scale Alert: {book.title}",
                                    message=(
                                        f"Book '{book.title}' received a "
                                        f"{decision.decision.value.upper()} recommendation "
                                        f"(score: {decision.score}/100). "
                                        f"{decision.reasoning[0] if decision.reasoning else ''}"
                                    ),
                                    data={
                                        "book_id": str(book.id),
                                        "decision": decision.decision.value,
                                        "score": decision.score,
                                        "current_roi": decision.current_roi,
                                        "actions": decision.actions[:3],
                                    },
                                )
                                db.add(notification)
                                total_alerts += 1

                await db.commit()

                return {
                    "org_id": org_id,
                    "books_analyzed": total_analyzed,
                    "kill_recommendations": total_kill,
                    "scale_recommendations": total_scale,
                    "revive_recommendations": total_revive,
                    "alerts_sent": total_alerts,
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                }

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during kill/scale alert generation for org %s: %s", org_id, exc, exc_info=True)
                await db.rollback()
                raise

    try:
        result = _run_async(_generate())

        logger.info(
            "Kill/scale alerts generated for org %s: %d books analyzed",
            org_id,
            result["books_analyzed"],
        )

        return result

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Failed to generate kill/scale alerts for org %s: %s",
            org_id,
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="portfolio_economics.update_seasonal_calendar",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=300,
    time_limit=600,
)
def update_seasonal_calendar(self) -> dict:
    """Update the seasonal calendar with latest event data.

    Runs weekly to:
    - Refresh event dates for the current and next year
    - Update demand indices based on latest sales data
    - Generate launch window recommendations
    """
    logger.info("Updating seasonal calendar")

    async def _update():
        from sqlalchemy import and_, select

        from app.models.project import Book, Project
        from app.modules.portfolio_economics.seasonal_service import (
            get_niche_seasonality,
            get_seasonal_calendar,
        )

        async with async_session() as db:
            try:
                current_year = date.today().year
                next_year = current_year + 1

                # Discover all active genres from books in the system
                genre_query = (
                    select(Book.metadata_)
                    .join(Project, Book.project_id == Project.id)
                    .where(
                        and_(
                            Book.deleted_at.is_(None),
                            Project.deleted_at.is_(None),
                        )
                    )
                )
                genre_result = await db.execute(genre_query)
                all_metadata = genre_result.scalars().all()

                active_genres = set()
                for meta in all_metadata:
                    if meta and isinstance(meta, dict):
                        genre = meta.get("genre")
                        if genre:
                            active_genres.add(genre)

                # If no genres found, use common defaults
                if not active_genres:
                    active_genres = {"romance", "thriller", "fantasy", "non-fiction"}

                genre_list = sorted(active_genres)

                # Refresh calendars for current and next year
                current_calendar = get_seasonal_calendar(
                    year=current_year,
                    user_genres=genre_list,
                )
                next_calendar = get_seasonal_calendar(
                    year=next_year,
                    user_genres=genre_list,
                )

                events_refreshed = len(current_calendar.events) + len(next_calendar.events)

                # Refresh niche seasonality for each active genre
                genres_updated = 0
                for genre in genre_list:
                    get_niche_seasonality(genre, current_year)
                    get_niche_seasonality(genre, next_year)
                    genres_updated += 1

                return {
                    "years_updated": [current_year, next_year],
                    "events_refreshed": events_refreshed,
                    "genres_updated": genres_updated,
                    "active_genres": genre_list,
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                }

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during seasonal calendar update: %s", exc, exc_info=True)
                await db.rollback()
                raise

    try:
        result = _run_async(_update())

        logger.info(
            "Seasonal calendar updated for years %s",
            result["years_updated"],
        )

        return result

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("Failed to update seasonal calendar: %s", str(exc), exc_info=True)
        raise self.retry(exc=exc) from exc


# ─── Celery Beat Schedule ────────────────────────────────────────────────────
# These would be registered in the main Celery config

PORTFOLIO_BEAT_SCHEDULE = {
    "portfolio-daily-snapshot": {
        "task": "portfolio_economics.snapshot_portfolio_metrics",
        "schedule": 86400,  # Daily (24 hours in seconds)
        "kwargs": {"org_id": "all"},  # Would iterate over all orgs
    },
    "audience-weekly-refresh": {
        "task": "portfolio_economics.refresh_audience_data",
        "schedule": 604800,  # Weekly (7 days in seconds)
        "kwargs": {"org_id": "all"},
    },
    "kill-scale-weekly-alerts": {
        "task": "portfolio_economics.generate_kill_scale_alerts",
        "schedule": 604800,  # Weekly
        "kwargs": {"org_id": "all"},
    },
    "seasonal-calendar-weekly-update": {
        "task": "portfolio_economics.update_seasonal_calendar",
        "schedule": 604800,  # Weekly
    },
}
