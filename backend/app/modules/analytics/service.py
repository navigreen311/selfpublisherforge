"""Analytics service layer.

Orchestrates dashboard aggregation, revenue calculations, and report generation.
Serves as the main entry point for the analytics router.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from kombu.exceptions import OperationalError as BrokerOperationalError
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse
from app.modules.analytics.aggregator import (
    aggregate_revenue,
    aggregate_revenue_by_book,
    aggregate_revenue_by_platform,
)
from app.modules.analytics.metrics import (
    compute_kpis,
    compute_portfolio_metrics,
    compute_revenue_trend,
)
from app.modules.analytics.models import (
    AnalyticsEvent,
    Report,
    RoyaltyRecord,
)
from app.modules.analytics.report_builder import generate_report
from app.modules.analytics.royalty_importer import import_royalties
from app.modules.analytics.schemas import (
    AggregationPeriod,
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    DashboardData,
    PortfolioMetrics,
    ReportRequest,
    ReportResponse,
    ReportStatus,
    RevenueQueryParams,
    RevenueResponse,
    RoyaltyImportRequest,
    RoyaltyImportResponse,
    RoyaltyRecordResponse,
    TrendData,
)
from app.tasks.analytics import scheduled_report_generation

logger = logging.getLogger(__name__)


# ---------- Dashboard ----------

async def get_dashboard(
    db: AsyncSession,
    org_id: uuid.UUID,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> DashboardData:
    """Build the main analytics dashboard payload."""
    now = datetime.now(UTC)
    if period_end is None:
        period_end = now
    if period_start is None:
        period_start = now - timedelta(days=30)

    # Parallel data gathering
    kpis = await compute_kpis(db, org_id, period_start, period_end)
    revenue_chart = await aggregate_revenue(
        db, org_id, period_start, period_end, AggregationPeriod.DAILY
    )
    top_books = await aggregate_revenue_by_book(db, org_id, period_start, period_end, limit=5)
    platform_breakdown = await aggregate_revenue_by_platform(db, org_id, period_start, period_end)

    # Recent royalties
    royalties_query = (
        select(RoyaltyRecord)
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .order_by(desc(RoyaltyRecord.created_at))
        .limit(5)
    )
    royalties_result = await db.execute(royalties_query)
    recent_royalties = [
        RoyaltyRecordResponse.model_validate(r)
        for r in royalties_result.scalars().all()
    ]

    return DashboardData(
        kpis=kpis,
        revenue_chart=revenue_chart,
        top_books=top_books,
        platform_breakdown=platform_breakdown,
        recent_royalties=recent_royalties,
        period_start=period_start,
        period_end=period_end,
    )


# ---------- Revenue ----------

async def get_revenue(
    db: AsyncSession,
    org_id: uuid.UUID,
    params: RevenueQueryParams,
) -> RevenueResponse:
    """Get revenue data with optional filters."""
    now = datetime.now(UTC)
    start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=UTC) if params.start_date else now - timedelta(days=365)
    end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=UTC) if params.end_date else now

    platform_str = params.platform.value if params.platform else None

    data_points = await aggregate_revenue(
        db, org_id, start, end, params.aggregation, platform=platform_str, book_id=params.book_id
    )

    total_revenue = sum((dp.revenue for dp in data_points), Decimal("0.00"))
    total_units = sum(dp.units for dp in data_points)

    by_platform = await aggregate_revenue_by_platform(db, org_id, start, end)
    by_book = await aggregate_revenue_by_book(db, org_id, start, end, limit=10)

    return RevenueResponse(
        total_revenue=total_revenue,
        total_units=total_units,
        data_points=data_points,
        period_start=start,
        period_end=end,
        aggregation=params.aggregation,
        by_platform=by_platform,
        by_book=by_book,
    )


# ---------- Royalties ----------

async def get_royalties(
    db: AsyncSession,
    org_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
    platform: str | None = None,
) -> PaginatedResponse[RoyaltyRecordResponse]:
    """List royalty records with cursor-based pagination."""
    conditions = [
        RoyaltyRecord.org_id == org_id,
        RoyaltyRecord.deleted_at.is_(None),
    ]
    if platform:
        conditions.append(RoyaltyRecord.platform == platform)
    if cursor:
        try:
            conditions.append(RoyaltyRecord.id < uuid.UUID(cursor))
        except ValueError:
            logger.warning("Failed to parse timezone value, using default UTC")

    count_query = (
        select(func.count(RoyaltyRecord.id))
        .where(and_(*[c for c in conditions if "id <" not in str(c)]))
    )
    count_result = await db.execute(
        select(func.count(RoyaltyRecord.id)).where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
                *([RoyaltyRecord.platform == platform] if platform else []),
            )
        )
    )
    total = count_result.scalar() or 0

    query = (
        select(RoyaltyRecord)
        .where(and_(*conditions))
        .order_by(desc(RoyaltyRecord.created_at))
        .limit(limit + 1)
    )
    result = await db.execute(query)
    records = result.scalars().all()

    has_more = len(records) > limit
    if has_more:
        records = records[:limit]

    items = [RoyaltyRecordResponse.model_validate(r) for r in records]
    next_cursor = str(items[-1].id) if has_more and items else None

    return PaginatedResponse[RoyaltyRecordResponse](
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total,
    )


async def import_royalty_data(
    db: AsyncSession,
    org_id: uuid.UUID,
    request: RoyaltyImportRequest,
) -> RoyaltyImportResponse:
    """Import royalty data from a CSV file."""
    if not request.file_content:
        return RoyaltyImportResponse(
            import_batch_id=uuid.uuid4(),
            records_imported=0,
            records_skipped=0,
            errors=["No file content provided"],
            platform=request.platform.value,
        )

    return await import_royalties(
        db, org_id, request.platform, request.file_content
    )


# ---------- Portfolio ----------

async def get_portfolio_metrics(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> PortfolioMetrics:
    """Get current portfolio-level metrics."""
    return await compute_portfolio_metrics(db, org_id)


# ---------- Reports ----------

async def create_report(
    db: AsyncSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    request: ReportRequest,
) -> ReportResponse:
    """Create and generate a report."""
    report = Report(
        org_id=org_id,
        title=request.title,
        report_type=request.report_type.value,
        output_format=request.output_format.value,
        parameters=request.parameters,
        status=ReportStatus.PENDING.value,
        generated_by=user_id,
    )
    db.add(report)
    await db.flush()
    await db.commit()

    try:
        task_result = scheduled_report_generation.delay(str(report.id))
        logger.info(
            "Dispatched report generation task for report_id=%s, celery_task_id=%s",
            report.id,
            task_result.id,
        )
    except (ConnectionError, OSError, BrokerOperationalError):
        logger.exception(
            "Failed to dispatch Celery task for report_id=%s; "
            "falling back to synchronous generation.",
            report.id,
        )
        async with db.begin():
            report = await generate_report(db, report)

    return ReportResponse.model_validate(report)


async def list_reports(
    db: AsyncSession,
    org_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
) -> PaginatedResponse[ReportResponse]:
    """List generated reports with cursor-based pagination."""
    conditions = [
        Report.org_id == org_id,
        Report.deleted_at.is_(None),
    ]
    if cursor:
        try:
            conditions.append(Report.id < uuid.UUID(cursor))
        except ValueError:
            logger.warning("Failed to parse timezone value, using default UTC")

    total_result = await db.execute(
        select(func.count(Report.id)).where(
            and_(
                Report.org_id == org_id,
                Report.deleted_at.is_(None),
            )
        )
    )
    total = total_result.scalar() or 0

    query = (
        select(Report)
        .where(and_(*conditions))
        .order_by(desc(Report.created_at))
        .limit(limit + 1)
    )
    result = await db.execute(query)
    records = result.scalars().all()

    has_more = len(records) > limit
    if has_more:
        records = records[:limit]

    items = [ReportResponse.model_validate(r) for r in records]
    next_cursor = str(items[-1].id) if has_more and items else None

    return PaginatedResponse[ReportResponse](
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total,
    )


async def get_report_by_id(
    db: AsyncSession,
    org_id: uuid.UUID,
    report_id: uuid.UUID,
) -> Report | None:
    """Fetch a single report by ID, scoped to the org."""
    query = (
        select(Report)
        .where(
            and_(
                Report.id == report_id,
                Report.org_id == org_id,
                Report.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ---------- Events ----------

async def record_event(
    db: AsyncSession,
    org_id: uuid.UUID,
    event: AnalyticsEventCreate,
) -> AnalyticsEventResponse:
    """Record an analytics event."""
    analytics_event = AnalyticsEvent(
        org_id=org_id,
        event_type=event.event_type,
        event_source=event.event_source,
        actor_id=event.actor_id,
        actor_type=event.actor_type,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        data=event.data,
        occurred_at=event.occurred_at or datetime.now(UTC),
    )
    db.add(analytics_event)
    await db.flush()
    return AnalyticsEventResponse.model_validate(analytics_event)


# ---------- Trends ----------

async def get_trends(
    db: AsyncSession,
    org_id: uuid.UUID,
    metric: str = "revenue",
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    aggregation: AggregationPeriod = AggregationPeriod.MONTHLY,
) -> TrendData:
    """Get trend data for a specified metric."""
    now = datetime.now(UTC)
    if period_end is None:
        period_end = now
    if period_start is None:
        period_start = now - timedelta(days=365)

    return await compute_revenue_trend(
        db, org_id, period_start, period_end, aggregation
    )
