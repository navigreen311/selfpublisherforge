"""Sales data service for Analytics module."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_sales_data(
    db: AsyncSession,
    org_id,
    period: str = "30d",
    book_id=None,
    marketplace=None,
):
    """Return daily sales data with totals and marketplace breakdown."""
    days = int(period.replace("d", "")) if period.endswith("d") else 30
    start_date = datetime.utcnow() - timedelta(days=days)

    # Try to get from sales_data table, fallback to royalty_records
    from app.modules.analytics.models import SalesData

    try:
        stmt = select(SalesData).where(
            SalesData.org_id == org_id,
            SalesData.date >= start_date,
        )
        if book_id:
            stmt = stmt.where(SalesData.book_id == book_id)
        if marketplace:
            stmt = stmt.where(SalesData.marketplace == marketplace)
        stmt = stmt.order_by(SalesData.date.desc())
        result = await db.execute(stmt)
        records = result.scalars().all()
    except Exception:
        logger.warning("Failed to query sales_data table, falling back to empty", exc_info=True)
        records = []

    # Build daily breakdown
    daily_map: dict[str, dict] = {}
    for r in records:
        date_str = r.date.strftime("%Y-%m-%d") if hasattr(r.date, "strftime") else str(r.date)
        if date_str not in daily_map:
            daily_map[date_str] = {
                "date": date_str,
                "kindle_units": 0,
                "print_units": 0,
                "audio_units": 0,
                "kenp_read": 0,
                "revenue": Decimal("0.00"),
                "royalties": Decimal("0.00"),
            }
        fmt = (r.format or "").lower()
        if "kindle" in fmt or "ebook" in fmt:
            daily_map[date_str]["kindle_units"] += r.units
        elif "print" in fmt or "paper" in fmt:
            daily_map[date_str]["print_units"] += r.units
        elif "audio" in fmt:
            daily_map[date_str]["audio_units"] += r.units
        daily_map[date_str]["kenp_read"] += r.kenp_read
        daily_map[date_str]["revenue"] += Decimal(str(r.revenue))
        daily_map[date_str]["royalties"] += Decimal(str(r.royalties))

    daily_data = sorted(daily_map.values(), key=lambda x: x["date"], reverse=True)

    # Convert Decimals to float for JSON serialisation in totals
    total_units = sum(r.units for r in records)
    total_revenue = sum(Decimal(str(r.revenue)) for r in records)
    total_royalties = sum(Decimal(str(r.royalties)) for r in records)

    # Marketplace breakdown
    mp_map: dict[str, dict] = {}
    for r in records:
        mp = r.marketplace or "US"
        if mp not in mp_map:
            mp_map[mp] = {"marketplace": mp, "revenue": Decimal("0.00"), "units": 0}
        mp_map[mp]["revenue"] += Decimal(str(r.revenue))
        mp_map[mp]["units"] += r.units

    return {
        "daily_data": daily_data,
        "totals": {
            "units": total_units,
            "revenue": round(float(cast("float", total_revenue)), 2),
            "royalties": round(float(cast("float", total_royalties)), 2),
        },
        "by_marketplace": sorted(
            [
                {"marketplace": v["marketplace"], "revenue": float(v["revenue"]), "units": v["units"]}
                for v in mp_map.values()
            ],
            key=lambda x: x["revenue"],
            reverse=True,
        ),
    }
