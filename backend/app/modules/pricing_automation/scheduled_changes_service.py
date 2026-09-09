"""Service for managing scheduled price changes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pricing_automation.models import ScheduledPriceChange


async def create_scheduled_change(db: AsyncSession, org_id: UUID, data: dict) -> dict:
    """Create a new scheduled price change."""
    change = ScheduledPriceChange(
        org_id=org_id,
        book_id=data["book_id"],
        current_price=data.get("current_price"),
        new_price=data["new_price"],
        reason=data.get("reason"),
        execute_at=data["execute_at"],
        revert_price=data.get("revert_price"),
        revert_at=data.get("revert_at"),
        status="pending",
    )
    db.add(change)
    await db.flush()
    await db.refresh(change)
    return _to_dict(change)


async def list_scheduled_changes(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID | None = None,
    status: str = "pending",
) -> list[dict]:
    """List scheduled price changes for an organization."""
    query = (
        select(ScheduledPriceChange)
        .where(ScheduledPriceChange.org_id == org_id)
        .where(ScheduledPriceChange.deleted_at.is_(None))
    )
    if book_id is not None:
        query = query.where(ScheduledPriceChange.book_id == book_id)
    if status:
        query = query.where(ScheduledPriceChange.status == status)
    query = query.order_by(ScheduledPriceChange.execute_at.asc())
    result = await db.execute(query)
    changes = result.scalars().all()
    return [_to_dict(c) for c in changes]


async def cancel_scheduled_change(db: AsyncSession, org_id: UUID, change_id: UUID) -> bool:
    """Cancel a scheduled price change."""
    result = await db.execute(
        select(ScheduledPriceChange)
        .where(ScheduledPriceChange.id == change_id)
        .where(ScheduledPriceChange.org_id == org_id)
        .where(ScheduledPriceChange.deleted_at.is_(None))
        .where(ScheduledPriceChange.status == "pending")
    )
    change = result.scalar_one_or_none()
    if change is None:
        return False

    change.status = "cancelled"
    change.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


def _to_dict(change: ScheduledPriceChange) -> dict:
    """Convert a ScheduledPriceChange ORM instance to a dict."""
    return {
        "id": change.id,
        "org_id": change.org_id,
        "book_id": change.book_id,
        "current_price": change.current_price,
        "new_price": change.new_price,
        "reason": change.reason,
        "execute_at": change.execute_at,
        "revert_price": change.revert_price,
        "revert_at": change.revert_at,
        "status": change.status,
        "executed_at": change.executed_at,
        "created_at": change.created_at,
    }
