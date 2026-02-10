"""Time-series aggregation for analytics events.

Provides daily, weekly, and monthly rollups of analytics_events
for efficient querying and charting.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsEvent, PortfolioMetricSnapshot, RoyaltyRecord
from app.modules.analytics.schemas import AggregationPeriod, RevenueDataPoint


async def aggregate_events_by_type(
    db: AsyncSession,
    org_id: UUID,
    period_start: datetime,
    period_end: datetime,
    aggregation: AggregationPeriod = AggregationPeriod.DAILY,
) -> list[dict[str, Any]]:
    """Aggregate analytics events by type over a time range.

    Returns a list of {period, event_type, count} dictionaries.
    """
    trunc_interval = _agg_to_trunc(aggregation)

    query = (
        select(
            func.date_trunc(trunc_interval, AnalyticsEvent.occurred_at).label("period"),
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count"),
        )
        .where(
            and_(
                AnalyticsEvent.org_id == org_id,
                AnalyticsEvent.occurred_at >= period_start,
                AnalyticsEvent.occurred_at <= period_end,
                AnalyticsEvent.deleted_at.is_(None),
            )
        )
        .group_by(text("1"), AnalyticsEvent.event_type)
        .order_by(text("1"))
    )

    result = await db.execute(query)
    return [
        {
            "period": row.period.isoformat() if row.period else "",
            "event_type": row.event_type,
            "count": row.count,
        }
        for row in result.all()
    ]


async def aggregate_revenue(
    db: AsyncSession,
    org_id: UUID,
    period_start: datetime,
    period_end: datetime,
    aggregation: AggregationPeriod = AggregationPeriod.MONTHLY,
    platform: str | None = None,
    book_id: UUID | None = None,
) -> list[RevenueDataPoint]:
    """Aggregate revenue data from royalty records over a time range.

    Returns a list of RevenueDataPoint objects grouped by period.
    """
    trunc_interval = _agg_to_trunc(aggregation)

    conditions = [
        RoyaltyRecord.org_id == org_id,
        RoyaltyRecord.period_start >= period_start,
        RoyaltyRecord.period_end <= period_end,
        RoyaltyRecord.deleted_at.is_(None),
    ]
    if platform:
        conditions.append(RoyaltyRecord.platform == platform)
    if book_id:
        conditions.append(RoyaltyRecord.book_id == book_id)

    query = (
        select(
            func.date_trunc(trunc_interval, RoyaltyRecord.period_start).label("period"),
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
        )
        .where(and_(*conditions))
        .group_by(text("1"))
        .order_by(text("1"))
    )

    result = await db.execute(query)
    return [
        RevenueDataPoint(
            period=row.period.isoformat() if row.period else "",
            revenue=Decimal(str(row.revenue)),
            units=int(row.units),
        )
        for row in result.all()
    ]


async def aggregate_revenue_by_platform(
    db: AsyncSession,
    org_id: UUID,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Decimal]:
    """Aggregate total revenue by platform over a time range."""
    query = (
        select(
            RoyaltyRecord.platform,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= period_start,
                RoyaltyRecord.period_end <= period_end,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.platform)
    )

    result = await db.execute(query)
    return {row.platform: Decimal(str(row.revenue)) for row in result.all()}


async def aggregate_revenue_by_book(
    db: AsyncSession,
    org_id: UUID,
    period_start: datetime,
    period_end: datetime,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Aggregate revenue by book title over a time range, returning top N."""
    query = (
        select(
            RoyaltyRecord.title,
            RoyaltyRecord.book_id,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= period_start,
                RoyaltyRecord.period_end <= period_end,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.title, RoyaltyRecord.book_id)
        .order_by(func.sum(RoyaltyRecord.net_revenue).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        {
            "title": row.title,
            "book_id": str(row.book_id) if row.book_id else None,
            "revenue": Decimal(str(row.revenue)),
            "units": int(row.units),
        }
        for row in result.all()
    ]


async def save_portfolio_snapshot(
    db: AsyncSession,
    org_id: UUID,
    snapshot_date: datetime,
    metrics_data: dict[str, Any],
) -> PortfolioMetricSnapshot:
    """Save a point-in-time portfolio metric snapshot."""
    snapshot = PortfolioMetricSnapshot(
        org_id=org_id,
        snapshot_date=snapshot_date,
        total_books=metrics_data.get("total_books", 0),
        total_revenue=Decimal(str(metrics_data.get("total_revenue", "0.00"))),
        total_units_sold=metrics_data.get("total_units_sold", 0),
        total_expenses=Decimal(str(metrics_data.get("total_expenses", "0.00"))),
        net_profit=Decimal(str(metrics_data.get("net_profit", "0.00"))),
        avg_roi=Decimal(str(metrics_data.get("avg_roi", "0.00"))),
        platform_breakdown=metrics_data.get("platform_breakdown", {}),
        format_breakdown=metrics_data.get("format_breakdown", {}),
        top_books=metrics_data.get("top_books", []),
        metrics_data=metrics_data,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


def _agg_to_trunc(aggregation: AggregationPeriod) -> str:
    """Map AggregationPeriod enum to PostgreSQL date_trunc interval."""
    return {
        AggregationPeriod.DAILY: "day",
        AggregationPeriod.WEEKLY: "week",
        AggregationPeriod.MONTHLY: "month",
        AggregationPeriod.QUARTERLY: "quarter",
        AggregationPeriod.YEARLY: "year",
    }.get(aggregation, "month")
