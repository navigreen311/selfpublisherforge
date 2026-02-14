"""CRUD service for pricing strategies."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pricing_automation.models import PricingStrategy


async def create_strategy(db: AsyncSession, org_id: UUID, data: dict) -> dict:
    """Create a new pricing strategy."""
    strategy = PricingStrategy(
        org_id=org_id,
        type=data["type"],
        name=data.get("name"),
        book_ids=data.get("book_ids", []),
        config=data.get("config", {}),
        status="active",
    )
    db.add(strategy)
    await db.flush()
    await db.refresh(strategy)
    return _to_dict(strategy)


async def list_strategies(
    db: AsyncSession, org_id: UUID, status: str | None = None
) -> list[dict]:
    """List pricing strategies for an organization."""
    query = (
        select(PricingStrategy)
        .where(PricingStrategy.org_id == org_id)
        .where(PricingStrategy.deleted_at.is_(None))
    )
    if status is not None:
        query = query.where(PricingStrategy.status == status)
    query = query.order_by(PricingStrategy.created_at.desc())
    result = await db.execute(query)
    strategies = result.scalars().all()
    return [_to_dict(s) for s in strategies]


async def get_strategy(db: AsyncSession, org_id: UUID, strategy_id: UUID) -> dict | None:
    """Get a single pricing strategy by ID."""
    result = await db.execute(
        select(PricingStrategy)
        .where(PricingStrategy.id == strategy_id)
        .where(PricingStrategy.org_id == org_id)
        .where(PricingStrategy.deleted_at.is_(None))
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        return None
    return _to_dict(strategy)


async def update_strategy(
    db: AsyncSession, org_id: UUID, strategy_id: UUID, data: dict
) -> dict | None:
    """Update an existing pricing strategy."""
    result = await db.execute(
        select(PricingStrategy)
        .where(PricingStrategy.id == strategy_id)
        .where(PricingStrategy.org_id == org_id)
        .where(PricingStrategy.deleted_at.is_(None))
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        return None

    for field_name, value in data.items():
        if value is not None:
            setattr(strategy, field_name, value)

    await db.flush()
    await db.refresh(strategy)
    return _to_dict(strategy)


async def delete_strategy(db: AsyncSession, org_id: UUID, strategy_id: UUID) -> bool:
    """Soft-delete a pricing strategy."""
    result = await db.execute(
        select(PricingStrategy)
        .where(PricingStrategy.id == strategy_id)
        .where(PricingStrategy.org_id == org_id)
        .where(PricingStrategy.deleted_at.is_(None))
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        return False

    strategy.deleted_at = datetime.now(UTC)
    strategy.status = "archived"
    await db.flush()
    return True


async def run_strategy(db: AsyncSession, org_id: UUID, strategy_id: UUID) -> dict | None:
    """Execute a strategy check (mock result).

    In production this would apply the strategy logic to each associated book.
    For now it updates last_run_at and returns a summary.
    """
    result = await db.execute(
        select(PricingStrategy)
        .where(PricingStrategy.id == strategy_id)
        .where(PricingStrategy.org_id == org_id)
        .where(PricingStrategy.deleted_at.is_(None))
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        return None

    now = datetime.now(UTC)
    strategy.last_run_at = now
    await db.flush()
    await db.refresh(strategy)

    return {
        "strategy_id": str(strategy.id),
        "type": strategy.type,
        "books_evaluated": len(strategy.book_ids) if strategy.book_ids else 0,
        "recommendations": [
            {
                "book_id": book_id,
                "current_price": None,
                "recommended_price": None,
                "reason": f"Strategy '{strategy.type}' evaluated — no live market data available.",
            }
            for book_id in (strategy.book_ids or [])
        ],
        "run_at": now.isoformat(),
    }


def _to_dict(strategy: PricingStrategy) -> dict:
    """Convert a PricingStrategy ORM instance to a dict."""
    return {
        "id": strategy.id,
        "org_id": strategy.org_id,
        "type": strategy.type,
        "name": strategy.name,
        "book_ids": strategy.book_ids or [],
        "config": strategy.config or {},
        "status": strategy.status,
        "last_run_at": strategy.last_run_at,
        "next_run_at": strategy.next_run_at,
        "created_at": strategy.created_at,
        "updated_at": strategy.updated_at,
    }
