"""Service for price change history tracking."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pricing_automation.models import PriceChangeHistory


def _parse_period(period: str) -> timedelta:
    """Parse a period string like '90d', '30d', '7d' into a timedelta."""
    period = period.strip().lower()
    if period.endswith("d"):
        days = int(period[:-1])
        return timedelta(days=days)
    if period.endswith("w"):
        weeks = int(period[:-1])
        return timedelta(weeks=weeks)
    if period.endswith("m"):
        months = int(period[:-1])
        return timedelta(days=months * 30)
    # Default to 90 days
    return timedelta(days=90)


async def get_price_history(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID | None = None,
    period: str = "90d",
) -> list[dict]:
    """Get price change history for an organization, optionally filtered by book."""
    delta = _parse_period(period)
    cutoff = datetime.now(UTC) - delta

    query = (
        select(PriceChangeHistory)
        .where(PriceChangeHistory.org_id == org_id)
        .where(PriceChangeHistory.created_at >= cutoff)
    )
    if book_id is not None:
        query = query.where(PriceChangeHistory.book_id == book_id)
    query = query.order_by(PriceChangeHistory.created_at.desc())
    result = await db.execute(query)
    entries = result.scalars().all()
    return [_to_dict(e) for e in entries]


async def record_price_change(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    old_price: float | None,
    new_price: float,
    reason: str | None = None,
    source: str = "manual",
) -> dict:
    """Record a price change in history."""
    # Calculate revenue impact percentage
    revenue_impact_pct = None
    if old_price and old_price > 0:
        revenue_impact_pct = round(((new_price - old_price) / old_price) * 100, 2)

    entry = PriceChangeHistory(
        org_id=org_id,
        book_id=book_id,
        old_price=old_price,
        new_price=new_price,
        reason=reason,
        source=source,
        revenue_impact_pct=revenue_impact_pct,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return _to_dict(entry)


def _to_dict(entry: PriceChangeHistory) -> dict:
    """Convert a PriceChangeHistory ORM instance to a dict."""
    return {
        "id": entry.id,
        "book_id": entry.book_id,
        "old_price": entry.old_price,
        "new_price": entry.new_price,
        "reason": entry.reason,
        "source": entry.source,
        "revenue_impact_pct": entry.revenue_impact_pct,
        "created_at": entry.created_at,
    }
