"""Portfolio-level metric calculations.

Computes total revenue, ROI per book, revenue trends, platform breakdowns,
and other aggregate portfolio metrics.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.advertising.models import Campaign, CampaignPerformance
from app.modules.analytics.models import (
    RoyaltyRecord,
)
from app.modules.analytics.schemas import (
    AggregationPeriod,
    KPICard,
    PortfolioMetrics,
    TrendData,
    TrendDataPoint,
)

CHANGE_THRESHOLD = float(os.environ.get("ANALYTICS_CHANGE_THRESHOLD", "0.5"))


def _quantize(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to the given number of decimal places."""
    fmt = Decimal(10) ** -places
    return value.quantize(fmt, rounding=ROUND_HALF_UP)


def _percent_change(current: Decimal, previous: Decimal) -> float | None:
    """Calculate the percentage change between two values."""
    if previous == 0:
        return None
    return float(((current - previous) / previous) * 100)


def _change_direction(change: float | None) -> str:
    """Return 'up', 'down', or 'flat' based on percentage change."""
    if change is None:
        return "flat"
    if change > CHANGE_THRESHOLD:
        return "up"
    if change < -CHANGE_THRESHOLD:
        return "down"
    return "flat"


async def _compute_total_expenses(
    db: AsyncSession,
    org_id: UUID,
) -> Decimal:
    """Sum all tracked expenses for an organization.

    Currently aggregates:
    - Advertising spend from ``CampaignPerformance`` records (joined
      through ``Campaign`` for org-level filtering).

    The query joins ``CampaignPerformance`` to ``Campaign`` so we can
    filter by ``Campaign.org_id`` (``CampaignPerformance`` itself is
    a non-tenant ``BaseModel`` without ``org_id``).
    """
    ad_spend_query = (
        select(
            func.coalesce(func.sum(CampaignPerformance.spend), 0).label("total_ad_spend"),
        )
        .join(Campaign, CampaignPerformance.campaign_id == Campaign.id)
        .where(
            and_(
                Campaign.org_id == org_id,
                Campaign.deleted_at.is_(None),
                CampaignPerformance.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(ad_spend_query)
    row = result.one()
    return Decimal(str(row.total_ad_spend))


async def compute_portfolio_metrics(
    db: AsyncSession,
    org_id: UUID,
    as_of: datetime | None = None,
) -> PortfolioMetrics:
    """Compute portfolio-level metrics from royalty records."""
    if as_of is None:
        as_of = datetime.now(UTC)

    # Total revenue & units
    totals_query = select(
        func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("total_revenue"),
        func.coalesce(func.sum(RoyaltyRecord.gross_revenue), 0).label("gross_revenue"),
        func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("total_units"),
        func.count(func.distinct(RoyaltyRecord.title)).label("total_books"),
    ).where(
        and_(
            RoyaltyRecord.org_id == org_id,
            RoyaltyRecord.deleted_at.is_(None),
        )
    )
    result = await db.execute(totals_query)
    row = result.one()

    total_revenue = Decimal(str(row.total_revenue))
    total_units = int(row.total_units)
    total_books = int(row.total_books)

    # Total expenses (advertising spend + other tracked costs)
    total_expenses = await _compute_total_expenses(db, org_id)

    # Net profit = revenue minus expenses
    net_profit = total_revenue - total_expenses

    # Average ROI: (revenue - expenses) / expenses when expenses > 0
    avg_roi = (total_revenue - total_expenses) / total_expenses if total_expenses > 0 else Decimal("0.00")

    # Platform breakdown
    platform_query = (
        select(
            RoyaltyRecord.platform,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.platform)
    )
    platform_result = await db.execute(platform_query)
    platform_breakdown = {row.platform: Decimal(str(row.revenue)) for row in platform_result.all()}

    # Format breakdown
    format_query = (
        select(
            RoyaltyRecord.format_type,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.format_type)
    )
    format_result = await db.execute(format_query)
    format_breakdown = {
        row.format_type: {"revenue": Decimal(str(row.revenue)), "units": int(row.units)} for row in format_result.all()
    }

    # Top books by revenue
    top_books_query = (
        select(
            RoyaltyRecord.title,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.title)
        .order_by(func.sum(RoyaltyRecord.net_revenue).desc())
        .limit(10)
    )
    top_books_result = await db.execute(top_books_query)
    top_books = [
        {
            "title": row.title,
            "revenue": Decimal(str(row.revenue)),
            "units": int(row.units),
        }
        for row in top_books_result.all()
    ]

    return PortfolioMetrics(
        total_books=total_books,
        total_revenue=_quantize(total_revenue),
        total_units_sold=total_units,
        total_expenses=_quantize(total_expenses),
        net_profit=_quantize(net_profit),
        avg_roi=_quantize(avg_roi, places=4),
        platform_breakdown=platform_breakdown,
        format_breakdown=format_breakdown,
        top_books=top_books,
        snapshot_date=as_of,
    )


async def compute_kpis(
    db: AsyncSession,
    org_id: UUID,
    period_start: datetime,
    period_end: datetime,
) -> list[KPICard]:
    """Compute key performance indicator cards for the dashboard."""
    period_length = period_end - period_start
    prev_start = period_start - period_length
    prev_end = period_start

    async def _period_totals(start: datetime, end: datetime):
        query = select(
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
            func.count(RoyaltyRecord.id).label("records"),
        ).where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= start,
                RoyaltyRecord.period_end <= end,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        return result.one()

    current = await _period_totals(period_start, period_end)
    previous = await _period_totals(prev_start, prev_end)

    curr_revenue = Decimal(str(current.revenue))
    prev_revenue = Decimal(str(previous.revenue))
    revenue_change = _percent_change(curr_revenue, prev_revenue)

    curr_units = int(current.units)
    prev_units = int(previous.units)
    units_change = _percent_change(Decimal(str(curr_units)), Decimal(str(prev_units)))

    return [
        KPICard(
            label="Total Revenue",
            value=f"${_quantize(curr_revenue):,}",
            change_percent=round(revenue_change, 1) if revenue_change is not None else None,
            change_direction=_change_direction(revenue_change),
        ),
        KPICard(
            label="Units Sold",
            value=f"{curr_units:,}",
            change_percent=round(units_change, 1) if units_change is not None else None,
            change_direction=_change_direction(units_change),
        ),
        KPICard(
            label="Avg Revenue/Unit",
            value=f"${_quantize(curr_revenue / Decimal(max(curr_units, 1))):,}",
            change_percent=None,
            change_direction="flat",
        ),
        KPICard(
            label="Royalty Records",
            value=f"{current.records:,}",
            change_percent=None,
            change_direction="flat",
        ),
    ]


async def compute_revenue_trend(
    db: AsyncSession,
    org_id: UUID,
    period_start: datetime,
    period_end: datetime,
    aggregation: AggregationPeriod = AggregationPeriod.MONTHLY,
) -> TrendData:
    """Compute revenue trend data over a time range."""
    trunc_fn = _get_date_trunc(aggregation)

    query = (
        select(
            func.date_trunc(trunc_fn, RoyaltyRecord.period_start).label("period"),
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
        .group_by(text("1"))
        .order_by(text("1"))
    )

    result = await db.execute(query)
    rows = result.all()

    data_points = []
    total = Decimal("0.00")
    for row in rows:
        value = Decimal(str(row.revenue))
        total += value
        data_points.append(
            TrendDataPoint(
                period=row.period.isoformat() if row.period else "",
                value=_quantize(value),
                label=None,
            )
        )

    avg = _quantize(total / Decimal(max(len(data_points), 1)))

    # Compute change between first and last data points
    change = None
    if len(data_points) >= 2:
        first_val = data_points[0].value
        last_val = data_points[-1].value
        change = _percent_change(last_val, first_val)

    return TrendData(
        metric="revenue",
        data_points=data_points,
        aggregation=aggregation,
        period_start=period_start,
        period_end=period_end,
        total=_quantize(total),
        average=avg,
        change_percent=round(change, 1) if change is not None else None,
    )


def _get_date_trunc(aggregation: AggregationPeriod) -> str:
    """Map aggregation period to PostgreSQL date_trunc interval."""
    mapping = {
        AggregationPeriod.DAILY: "day",
        AggregationPeriod.WEEKLY: "week",
        AggregationPeriod.MONTHLY: "month",
        AggregationPeriod.QUARTERLY: "quarter",
        AggregationPeriod.YEARLY: "year",
    }
    return mapping.get(aggregation, "month")
