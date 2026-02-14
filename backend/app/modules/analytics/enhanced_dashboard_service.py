"""Enhanced dashboard service for Analytics module.

Provides a richer dashboard with KPI comparisons, trend data,
revenue breakdowns, and AI-generated insights.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import SalesData, RoyaltyRecord

logger = logging.getLogger(__name__)


async def get_enhanced_dashboard(
    db: AsyncSession,
    org_id: UUID,
    period: str = "30d",
    compare: str = "previous",
) -> dict:
    """Build an enhanced analytics dashboard payload.

    Returns stats (KPI cards with change percentages), daily trend data,
    revenue breakdowns by book and format, and AI-generated insights.
    The *compare* parameter controls the comparison period: ``"previous"``
    compares against the immediately preceding period of the same length.
    """
    days = int(period.replace("d", "")) if period.endswith("d") else 30
    now = datetime.utcnow()
    current_start = now - timedelta(days=days)
    prev_start = current_start - timedelta(days=days)
    prev_end = current_start

    # --- Current period totals ---
    current_totals = await _period_totals(db, org_id, current_start, now)
    prev_totals = await _period_totals(db, org_id, prev_start, prev_end)

    # --- KPI stat cards ---
    stats = _build_stat_cards(current_totals, prev_totals)

    # --- Daily trend data ---
    trend_data = await _daily_trend(db, org_id, current_start, now)

    # --- Revenue by book ---
    revenue_by_book = await _revenue_by_book(db, org_id, current_start, now)

    # --- Revenue by format ---
    revenue_by_format = await _revenue_by_format(db, org_id, current_start, now)

    # --- AI insights ---
    insights = _generate_insights(current_totals, prev_totals, revenue_by_book, revenue_by_format)

    compare_label = f"previous {days}d" if compare == "previous" else None

    return {
        "stats": stats,
        "trend_data": trend_data,
        "revenue_by_book": revenue_by_book,
        "revenue_by_format": revenue_by_format,
        "insights": insights,
        "period": f"{days}d",
        "compare_period": compare_label,
    }


# ---------- Internal helpers ----------


async def _period_totals(
    db: AsyncSession,
    org_id: UUID,
    start: datetime,
    end: datetime,
) -> dict:
    """Aggregate totals from sales_data for a date range, falling back to royalty_records."""
    try:
        stmt = (
            select(
                func.coalesce(func.sum(SalesData.revenue), 0).label("revenue"),
                func.coalesce(func.sum(SalesData.units), 0).label("units"),
                func.coalesce(func.sum(SalesData.royalties), 0).label("royalties"),
                func.coalesce(func.sum(SalesData.kenp_read), 0).label("kenp"),
            )
            .where(
                and_(
                    SalesData.org_id == org_id,
                    SalesData.date >= start,
                    SalesData.date <= end,
                )
            )
        )
        result = await db.execute(stmt)
        row = result.one()
        revenue = float(row.revenue)
        units = int(row.units)
        royalties = float(row.royalties)
        kenp = int(row.kenp)
    except Exception:
        logger.debug("sales_data query failed, trying royalty_records", exc_info=True)
        revenue, units, royalties, kenp = 0.0, 0, 0.0, 0

    # Fallback: try royalty_records if sales_data was empty
    if revenue == 0 and units == 0:
        try:
            stmt2 = (
                select(
                    func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
                    func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
                )
                .where(
                    and_(
                        RoyaltyRecord.org_id == org_id,
                        RoyaltyRecord.period_start >= start,
                        RoyaltyRecord.period_end <= end,
                        RoyaltyRecord.deleted_at.is_(None),
                    )
                )
            )
            result2 = await db.execute(stmt2)
            row2 = result2.one()
            revenue = float(row2.revenue)
            units = int(row2.units)
            royalties = revenue  # approximate
        except Exception:
            logger.debug("royalty_records fallback also failed", exc_info=True)

    return {
        "revenue": revenue,
        "units": units,
        "royalties": royalties,
        "kenp": kenp,
    }


async def _daily_trend(
    db: AsyncSession,
    org_id: UUID,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Return daily aggregated revenue and units for charting."""
    try:
        stmt = (
            select(
                func.date_trunc("day", SalesData.date).label("day"),
                func.coalesce(func.sum(SalesData.revenue), 0).label("revenue"),
                func.coalesce(func.sum(SalesData.units), 0).label("units"),
            )
            .where(
                and_(
                    SalesData.org_id == org_id,
                    SalesData.date >= start,
                    SalesData.date <= end,
                )
            )
            .group_by(func.date_trunc("day", SalesData.date))
            .order_by(func.date_trunc("day", SalesData.date))
        )
        result = await db.execute(stmt)
        return [
            {
                "date": row.day.strftime("%Y-%m-%d") if row.day else "",
                "revenue": float(row.revenue),
                "units": int(row.units),
            }
            for row in result.all()
        ]
    except Exception:
        logger.debug("daily_trend query failed", exc_info=True)
        return []


async def _revenue_by_book(
    db: AsyncSession,
    org_id: UUID,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Revenue breakdown per book (top 10)."""
    try:
        stmt = (
            select(
                SalesData.book_id,
                func.coalesce(func.sum(SalesData.revenue), 0).label("revenue"),
                func.coalesce(func.sum(SalesData.units), 0).label("units"),
            )
            .where(
                and_(
                    SalesData.org_id == org_id,
                    SalesData.date >= start,
                    SalesData.date <= end,
                )
            )
            .group_by(SalesData.book_id)
            .order_by(func.sum(SalesData.revenue).desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        return [
            {
                "book_id": str(row.book_id),
                "revenue": float(row.revenue),
                "units": int(row.units),
            }
            for row in result.all()
        ]
    except Exception:
        logger.debug("revenue_by_book query failed", exc_info=True)
        return []


async def _revenue_by_format(
    db: AsyncSession,
    org_id: UUID,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Revenue breakdown per format."""
    try:
        stmt = (
            select(
                SalesData.format,
                func.coalesce(func.sum(SalesData.revenue), 0).label("revenue"),
                func.coalesce(func.sum(SalesData.units), 0).label("units"),
            )
            .where(
                and_(
                    SalesData.org_id == org_id,
                    SalesData.date >= start,
                    SalesData.date <= end,
                )
            )
            .group_by(SalesData.format)
            .order_by(func.sum(SalesData.revenue).desc())
        )
        result = await db.execute(stmt)
        return [
            {
                "format": row.format or "Unknown",
                "revenue": float(row.revenue),
                "units": int(row.units),
            }
            for row in result.all()
        ]
    except Exception:
        logger.debug("revenue_by_format query failed", exc_info=True)
        return []


def _pct_change(current: float, previous: float) -> float | None:
    """Calculate percentage change; returns None when previous is zero."""
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


def _build_stat_cards(current: dict, previous: dict) -> list[dict]:
    """Build four KPI stat cards comparing current vs. previous period."""
    revenue_change = _pct_change(current["revenue"], previous["revenue"])
    units_change = _pct_change(float(current["units"]), float(previous["units"]))
    royalties_change = _pct_change(current["royalties"], previous["royalties"])
    kenp_change = _pct_change(float(current["kenp"]), float(previous["kenp"]))

    return [
        {
            "label": "Total Revenue",
            "value": round(current["revenue"], 2),
            "change_percent": revenue_change,
            "direction": "up" if (revenue_change or 0) > 0 else ("down" if (revenue_change or 0) < 0 else "flat"),
        },
        {
            "label": "Units Sold",
            "value": current["units"],
            "change_percent": units_change,
            "direction": "up" if (units_change or 0) > 0 else ("down" if (units_change or 0) < 0 else "flat"),
        },
        {
            "label": "Royalties",
            "value": round(current["royalties"], 2),
            "change_percent": royalties_change,
            "direction": "up" if (royalties_change or 0) > 0 else ("down" if (royalties_change or 0) < 0 else "flat"),
        },
        {
            "label": "KENP Read",
            "value": current["kenp"],
            "change_percent": kenp_change,
            "direction": "up" if (kenp_change or 0) > 0 else ("down" if (kenp_change or 0) < 0 else "flat"),
        },
    ]


def _generate_insights(
    current: dict,
    previous: dict,
    by_book: list[dict],
    by_format: list[dict],
) -> list[dict]:
    """Generate mock AI analytics insights based on data patterns."""
    insights: list[dict] = []

    # Revenue trend insight
    rev_change = _pct_change(current["revenue"], previous["revenue"])
    if rev_change is not None:
        if rev_change > 10:
            insights.append({
                "type": "positive_trend",
                "message": f"Revenue is up {rev_change}% compared to the previous period. Strong momentum!",
                "book_id": None,
                "metric": "revenue",
                "severity": "success",
            })
        elif rev_change < -10:
            insights.append({
                "type": "negative_trend",
                "message": f"Revenue declined {abs(rev_change)}% vs. the previous period. Consider reviewing pricing or promotions.",
                "book_id": None,
                "metric": "revenue",
                "severity": "warning",
            })
        else:
            insights.append({
                "type": "stable",
                "message": "Revenue is holding steady compared to the previous period.",
                "book_id": None,
                "metric": "revenue",
                "severity": "info",
            })

    # Top book insight
    if by_book:
        top = by_book[0]
        insights.append({
            "type": "top_performer",
            "message": f"Your top-performing book generated ${top['revenue']:.2f} in revenue this period.",
            "book_id": top["book_id"],
            "metric": "revenue",
            "severity": "info",
        })

    # Format insight
    if by_format:
        top_fmt = by_format[0]
        insights.append({
            "type": "format_leader",
            "message": f"The '{top_fmt['format']}' format leads with ${top_fmt['revenue']:.2f} in revenue.",
            "book_id": None,
            "metric": "format_revenue",
            "severity": "info",
        })

    # KENP insight
    kenp_change = _pct_change(float(current["kenp"]), float(previous["kenp"]))
    if kenp_change is not None and abs(kenp_change) > 20:
        direction = "increased" if kenp_change > 0 else "decreased"
        insights.append({
            "type": "kenp_alert",
            "message": f"KENP reads have {direction} by {abs(kenp_change)}%. Monitor Kindle Unlimited performance.",
            "book_id": None,
            "metric": "kenp_read",
            "severity": "warning" if kenp_change < 0 else "success",
        })

    return insights
