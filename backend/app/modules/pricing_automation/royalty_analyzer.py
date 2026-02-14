"""Royalty analysis engine.

Provides per-book royalty breakdown with format-specific rates, units,
revenue, and royalty amounts.  Includes optimization tips based on KDP
pricing tiers ($2.99-$9.99 for 70% royalty) and print cost calculations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Try to import SalesData if it exists in the analytics module; fall back gracefully.
try:
    from app.modules.analytics.models import SalesData  # type: ignore[import-untyped]
except ImportError:
    SalesData = None  # type: ignore[assignment,misc]


# KDP royalty tiers for ebooks
ROYALTY_70_MIN = 2.99
ROYALTY_70_MAX = 9.99


def _ebook_royalty_rate(price: float) -> float:
    """Return the KDP ebook royalty rate for a given price."""
    if ROYALTY_70_MIN <= price <= ROYALTY_70_MAX:
        return 0.70
    return 0.35


def _format_royalty_rate(fmt: str, price: float) -> float:
    """Return the royalty rate based on format and price."""
    fmt_lower = fmt.lower() if fmt else "ebook"
    if fmt_lower == "ebook":
        return _ebook_royalty_rate(price)
    if fmt_lower == "paperback":
        return 0.60  # 60% minus printing cost (simplified)
    if fmt_lower == "hardcover":
        return 0.35
    if fmt_lower == "audiobook":
        return 0.40
    return 0.35


def _generate_optimization_tips(rows: list[dict]) -> list[str]:
    """Generate optimization tips based on current pricing data."""
    tips: list[str] = []

    for row in rows:
        price = row.get("price", 0)
        fmt = row.get("format", "ebook")
        title = row.get("book_title", "Unknown")

        if fmt.lower() == "ebook":
            if price < ROYALTY_70_MIN:
                tips.append(
                    f"'{title}' is priced at ${price:.2f} (35% royalty). "
                    f"Raising to ${ROYALTY_70_MIN:.2f} would qualify for the 70% royalty tier, "
                    f"potentially doubling your per-unit royalty."
                )
            elif price > ROYALTY_70_MAX:
                tips.append(
                    f"'{title}' is priced at ${price:.2f} (35% royalty). "
                    f"Lowering to ${ROYALTY_70_MAX:.2f} or below would qualify for the 70% "
                    f"royalty tier on KDP."
                )
        elif fmt.lower() == "paperback":
            if price < 7.99:
                tips.append(
                    f"'{title}' paperback at ${price:.2f} may have thin margins after "
                    f"printing costs. Consider raising to at least $7.99 for better "
                    f"profitability."
                )

    if not tips:
        tips.append(
            "All books are priced within optimal royalty tiers. "
            "Consider A/B testing price points to maximize revenue."
        )

    return tips


async def get_royalty_analysis(
    db: AsyncSession, org_id: UUID, period: str = "30d"
) -> dict:
    """Return per-book royalty breakdown with optimization tips.

    If SalesData model is available, queries actual sales records.
    Otherwise returns a mock/demo analysis structure.
    """
    # Parse period
    period_stripped = period.strip().lower()
    if period_stripped.endswith("d"):
        days = int(period_stripped[:-1])
    elif period_stripped.endswith("w"):
        days = int(period_stripped[:-1]) * 7
    elif period_stripped.endswith("m"):
        days = int(period_stripped[:-1]) * 30
    else:
        days = 30
    cutoff = datetime.now(UTC) - timedelta(days=days)

    rows: list[dict] = []
    total_revenue = 0.0
    total_royalty = 0.0
    total_units = 0

    if SalesData is not None:
        # Query actual sales data
        query = (
            select(SalesData)
            .where(SalesData.org_id == org_id)
            .where(SalesData.created_at >= cutoff)
            .where(SalesData.deleted_at.is_(None))
        )
        result = await db.execute(query)
        sales_records = result.scalars().all()

        # Aggregate by book_id + format
        book_agg: dict[tuple, dict] = {}
        for record in sales_records:
            key = (str(record.book_id), getattr(record, "format", "ebook") or "ebook")
            if key not in book_agg:
                book_agg[key] = {
                    "book_id": str(record.book_id),
                    "book_title": getattr(record, "book_title", f"Book {str(record.book_id)[:8]}"),
                    "format": key[1],
                    "units": 0,
                    "revenue": 0.0,
                }
            agg = book_agg[key]
            units = getattr(record, "units", 0) or 0
            revenue = float(getattr(record, "revenue", 0) or 0)
            agg["units"] += units
            agg["revenue"] += revenue

        for key, agg in book_agg.items():
            price = round(agg["revenue"] / agg["units"], 2) if agg["units"] > 0 else 0.0
            rate = _format_royalty_rate(agg["format"], price)
            royalty = round(agg["revenue"] * rate, 2)
            row = {
                "book_id": agg["book_id"],
                "book_title": agg["book_title"],
                "price": price,
                "format": agg["format"],
                "royalty_rate": rate,
                "units": agg["units"],
                "revenue": round(agg["revenue"], 2),
                "royalty": royalty,
            }
            rows.append(row)
            total_revenue += agg["revenue"]
            total_royalty += royalty
            total_units += agg["units"]
    else:
        # No SalesData model available — return empty analysis
        pass

    effective_rate = round(total_royalty / total_revenue, 4) if total_revenue > 0 else 0.0
    tips = _generate_optimization_tips(rows)

    return {
        "rows": rows,
        "totals": {
            "total_units": total_units,
            "total_revenue": round(total_revenue, 2),
            "total_royalty": round(total_royalty, 2),
        },
        "effective_rate": effective_rate,
        "optimization_tips": tips,
    }
