"""Service layer for series read-through rate analytics."""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.series_analytics.schemas import (
    FunnelStep,
    PerVolumeStat,
    ReadThroughRate,
    RevenuePerBook,
    SeriesAnalyticsResponse,
)


def _period_to_days(period: str) -> int:
    return {"30d": 30, "90d": 90, "1y": 365}.get(period, 90)


async def get_series_analytics(
    db: AsyncSession,
    org_id: UUID,
    series_id: UUID,
    period: str = "90d",
) -> SeriesAnalyticsResponse:
    """Aggregate read-through / funnel metrics for a single series."""
    days = _period_to_days(period)
    period_start = date.today() - timedelta(days=days)

    # Series exists & in org
    try:
        series_row = (
            await db.execute(
                text("SELECT id, name FROM series WHERE id = :sid AND org_id = :oid"),
                {"sid": str(series_id), "oid": str(org_id)},
            )
        ).first()
    except SQLAlchemyError:
        series_row = None

    series_name = series_row.name if series_row else "Series"

    # Per-volume aggregates (books + rollups, gracefully degrade to zeros).
    per_vol: list[PerVolumeStat] = []
    funnel: list[FunnelStep] = []
    revenue_per_book: list[RevenuePerBook] = []
    try:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT b.id AS book_id,
                           b.title AS title,
                           b.series_order AS series_order,
                           b.status AS status,
                           COALESCE(SUM(s.unique_buyers), 0) AS unique_buyers,
                           COALESCE(SUM(s.units_sold), 0) AS units_sold,
                           COALESCE(SUM(s.revenue), 0) AS revenue,
                           AVG(s.bsr_avg) AS bsr_avg,
                           MAX(s.review_count) AS review_count,
                           AVG(s.rating_avg) AS rating_avg
                      FROM books b
                      LEFT JOIN series_sales_data s
                             ON s.book_id = b.id
                            AND s.period_start >= :period_start
                     WHERE b.series_id = :sid
                       AND b.deleted_at IS NULL
                  GROUP BY b.id, b.title, b.series_order, b.status
                  ORDER BY COALESCE(b.series_order, 999) ASC, b.title ASC
                    """
                ),
                {"sid": str(series_id), "period_start": period_start},
            )
        ).mappings().all()
    except SQLAlchemyError:
        rows = []

    for i, r in enumerate(rows):
        order = r["series_order"] if r["series_order"] is not None else (i + 1)
        book_id = r["book_id"]
        title = r["title"] or f"Volume {order}"
        units = int(r["units_sold"] or 0)
        rev = float(r["revenue"] or 0)
        buyers = int(r["unique_buyers"] or 0)

        per_vol.append(
            PerVolumeStat(
                book_id=book_id,
                title=title,
                series_order=order,
                units_sold=units,
                revenue=rev,
                bsr_avg=int(r["bsr_avg"]) if r["bsr_avg"] is not None else None,
                review_count=int(r["review_count"]) if r["review_count"] is not None else None,
                rating_avg=float(r["rating_avg"]) if r["rating_avg"] is not None else None,
                status=str(r["status"]) if r["status"] is not None else None,
            )
        )
        funnel.append(
            FunnelStep(
                book_id=book_id,
                title=title,
                series_order=order,
                unique_buyers=buyers,
                units_sold=units,
                revenue=rev,
            )
        )
        revenue_per_book.append(
            RevenuePerBook(
                book_id=book_id,
                title=title,
                series_order=order,
                revenue=rev,
            )
        )

    # Sort funnel by series_order (ascending).
    funnel.sort(key=lambda f: f.series_order)
    per_vol.sort(key=lambda p: p.series_order)
    revenue_per_book.sort(key=lambda p: p.series_order)

    # Read-through rates between consecutive volumes.
    read_through: list[ReadThroughRate] = []
    for i in range(len(funnel) - 1):
        a, b = funnel[i], funnel[i + 1]
        rate = (b.unique_buyers / a.unique_buyers) if a.unique_buyers else 0.0
        read_through.append(
            ReadThroughRate(
                from_order=a.series_order,
                to_order=b.series_order,
                from_title=a.title,
                to_title=b.title,
                rate=round(rate, 4),
                healthy=rate >= 0.5,
            )
        )

    overall = 0.0
    if len(funnel) >= 2 and funnel[0].unique_buyers:
        overall = funnel[-1].unique_buyers / funnel[0].unique_buyers

    # Average revenue per Vol 1 buyer: sum of revenues / V1 buyers.
    v1_buyers = funnel[0].unique_buyers if funnel else 0
    total_revenue = sum(f.revenue for f in funnel)
    total_units = sum(f.units_sold for f in funnel)
    avg_rev_v1 = (total_revenue / v1_buyers) if v1_buyers else 0.0

    return SeriesAnalyticsResponse(
        series_id=series_id,
        series_name=series_name,
        period=period,
        funnel=funnel,
        read_through_rates=read_through,
        overall_read_through=round(overall, 4),
        avg_revenue_per_vol1_buyer=round(avg_rev_v1, 2),
        revenue_per_book=revenue_per_book,
        per_volume_stats=per_vol,
        total_units=total_units,
        total_revenue=round(total_revenue, 2),
    )
