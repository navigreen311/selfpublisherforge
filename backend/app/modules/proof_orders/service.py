"""Service layer for the Proof Orders module.

This is a SCAFFOLD. The "order placed" response (tracking number,
estimated delivery) is mocked — no real print provider API is called.
Swap ``_mock_provider_order`` for a real integration before shipping.
"""

from __future__ import annotations

import random
import string
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.proof_orders.models import ProofOrder
from app.modules.proof_orders.schemas import (
    Checklist,
    IssuesLevel,
    ProofCostEstimate,
    ProofOrderCreate,
    ProofReviewUpdate,
    ShippingMethod,
)


_CENTS = Decimal("0.01")


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENTS, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Cost model (KDP print rates, approximate; documented as estimate).
# ---------------------------------------------------------------------------

_SHIPPING_COSTS = {
    ShippingMethod.STANDARD: Decimal("3.99"),
    ShippingMethod.EXPEDITED: Decimal("7.99"),
    ShippingMethod.PRIORITY: Decimal("14.99"),
}

_SHIPPING_DAYS = {
    ShippingMethod.STANDARD: 7,
    ShippingMethod.EXPEDITED: 4,
    ShippingMethod.PRIORITY: 2,
}


def estimate_cost(
    page_count: int | None,
    interior_type: str | None,
    shipping_method: ShippingMethod,
) -> ProofCostEstimate:
    pages = page_count or 100
    itype = (interior_type or "black_white").lower()
    # KDP-style per-page pricing (US paperback).
    if itype == "premium_color":
        per_page = Decimal("0.065")
        fixed = Decimal("1.00")
    elif itype == "standard_color":
        per_page = Decimal("0.040")
        fixed = Decimal("0.85")
    else:
        per_page = Decimal("0.012")
        fixed = Decimal("0.85")
    print_cost = fixed + per_page * Decimal(pages)
    ship = _SHIPPING_COSTS[shipping_method]
    return ProofCostEstimate(
        print_cost=_q(print_cost),
        shipping_cost=_q(ship),
        total=_q(print_cost + ship),
    )


# ---------------------------------------------------------------------------
# Mocked print-provider integration
# ---------------------------------------------------------------------------

def _mock_provider_order(method: ShippingMethod) -> dict[str, Any]:
    """Return a realistic-looking mocked provider response.

    TODO: Replace with real print provider API call
          (Lulu / KDP POD / IngramSpark).
    """
    tracking = "1Z" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    eta = date.today() + timedelta(days=_SHIPPING_DAYS[method])
    return {
        "tracking_number": tracking,
        "estimated_delivery": eta,
        "status": "ordered",
    }


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def get_by_publishing(
    db: AsyncSession, org_id: UUID, publishing_id: UUID
) -> ProofOrder | None:
    stmt = (
        select(ProofOrder)
        .where(
            and_(
                ProofOrder.org_id == org_id,
                ProofOrder.publishing_id == publishing_id,
            )
        )
        .order_by(ProofOrder.ordered_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().first()


async def create_order(
    db: AsyncSession,
    org_id: UUID,
    publishing_id: UUID,
    payload: ProofOrderCreate,
    *,
    book_id: UUID | None = None,
) -> ProofOrder:
    cost = estimate_cost(payload.page_count, payload.interior_type, payload.shipping_method)
    provider = _mock_provider_order(payload.shipping_method)

    default_checklist = {k: False for k in Checklist.model_fields.keys()}

    order = ProofOrder(
        org_id=org_id,
        publishing_id=publishing_id,
        book_id=book_id,
        interior_file_url=payload.interior_file_url,
        cover_file_url=payload.cover_file_url,
        trim_size=payload.trim_size,
        page_count=payload.page_count,
        interior_type=payload.interior_type,
        shipping_name=payload.shipping_address.name,
        shipping_address=payload.shipping_address.address,
        shipping_city=payload.shipping_address.city,
        shipping_state=payload.shipping_address.state,
        shipping_zip=payload.shipping_address.zip,
        shipping_method=payload.shipping_method.value,
        print_cost=cost.print_cost,
        shipping_cost=cost.shipping_cost,
        cost=cost.total,
        tracking_number=provider["tracking_number"],
        estimated_delivery=provider["estimated_delivery"],
        status=provider["status"],
        checklist=default_checklist,
        approved=False,
        skipped=False,
    )
    db.add(order)
    await db.flush()
    return order


async def skip_proof(
    db: AsyncSession, org_id: UUID, publishing_id: UUID, reason: str | None = None
) -> ProofOrder:
    """Record a skipped proof. Creates a no-cost ProofOrder stub so
    downstream gating logic can check approval/skip uniformly."""
    order = ProofOrder(
        org_id=org_id,
        publishing_id=publishing_id,
        interior_file_url="",
        cover_file_url="",
        status="skipped",
        skipped=True,
        approved=True,  # Skipping unblocks publishing.
        approved_at=datetime.now(timezone.utc),
        notes=reason,
        cost=Decimal("0.00"),
        checklist={},
    )
    db.add(order)
    await db.flush()
    return order


async def update_review(
    db: AsyncSession,
    org_id: UUID,
    publishing_id: UUID,
    payload: ProofReviewUpdate,
) -> ProofOrder | None:
    order = await get_by_publishing(db, org_id, publishing_id)
    if order is None:
        return None
    order.checklist = payload.checklist.model_dump()
    order.issues = payload.issues.value
    if payload.notes is not None:
        order.notes = payload.notes

    if payload.approved:
        # Approval gate: require all checklist items checked AND issues != 'major'.
        if not payload.checklist.all_checked():
            raise ValueError("Cannot approve: not all checklist items are checked.")
        if payload.issues == IssuesLevel.MAJOR:
            raise ValueError("Cannot approve: major issues reported.")
        order.approved = True
        order.approved_at = datetime.now(timezone.utc)
        order.status = "approved"
    else:
        order.approved = False
        order.approved_at = None
        if payload.issues == IssuesLevel.MAJOR:
            order.status = "rejected"
        elif order.status == "approved":
            order.status = "ordered"

    await db.flush()
    return order


async def can_publish(
    db: AsyncSession, org_id: UUID, publishing_id: UUID
) -> bool:
    """Approval gate helper: publishing can proceed iff the proof is
    approved OR explicitly skipped."""
    order = await get_by_publishing(db, org_id, publishing_id)
    if order is None:
        return False
    return order.approved or order.skipped
