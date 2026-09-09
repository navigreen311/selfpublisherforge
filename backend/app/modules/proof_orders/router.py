"""FastAPI router for the print proof ordering flow.

Endpoints (after prefix "/api/v1/proof-orders" applied by main.py):
    POST   /                 Create a new proof order
    GET    /                 List proof orders for current org
    GET    /{id}             Get a single proof order
    PATCH  /{id}/status      Update proof order status
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db

from .models import PROOF_ORDER_STATUSES, ProofOrder
from .schemas import (
    ProofOrderCreate,
    ProofOrderListResponse,
    ProofOrderOut,
    ProofOrderStatusUpdate,
)

router = APIRouter()


def _format_address(addr) -> str:
    parts = [addr.address]
    if addr.city:
        parts.append(addr.city)
    if addr.state:
        parts.append(addr.state)
    if addr.zip:
        parts.append(addr.zip)
    if addr.country:
        parts.append(addr.country)
    return ", ".join(p for p in parts if p)


@router.post(
    "",
    response_model=ProofOrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a proof order",
)
async def create_proof_order(
    payload: ProofOrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProofOrder:
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="Organization context required")

    order = ProofOrder(
        org_id=current_user["org_id"],
        publishing_id=payload.publishing_id,
        book_id=payload.book_id,
        quantity=payload.quantity,
        platform=payload.platform,
        interior_file_url=payload.interior_file_url,
        cover_file_url=payload.cover_file_url,
        shipping_name=payload.shipping_address.name,
        shipping_address=_format_address(payload.shipping_address),
        shipping_method=payload.shipping_method or "standard",
        billing=payload.billing.model_dump(mode="json") if payload.billing else {},
        notes=payload.notes,
        status="ordered",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.get(
    "",
    response_model=ProofOrderListResponse,
    summary="List proof orders",
)
async def list_proof_orders(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status"),
    publishing_id: UUID | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProofOrderListResponse:
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="Organization context required")

    clauses = [ProofOrder.org_id == current_user["org_id"]]
    if status_filter:
        clauses.append(ProofOrder.status == status_filter)
    if publishing_id:
        clauses.append(ProofOrder.publishing_id == publishing_id)

    count_stmt = select(func.count()).select_from(ProofOrder).where(and_(*clauses))
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ProofOrder)
        .where(and_(*clauses))
        .order_by(ProofOrder.ordered_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return ProofOrderListResponse(
        items=[ProofOrderOut.model_validate(r) for r in rows],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get(
    "/{order_id}",
    response_model=ProofOrderOut,
    summary="Get a proof order by ID",
)
async def get_proof_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProofOrder:
    stmt = select(ProofOrder).where(
        ProofOrder.id == order_id,
        ProofOrder.org_id == current_user["org_id"],
    )
    order = (await db.execute(stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Proof order not found")
    return order


@router.patch(
    "/{order_id}/status",
    response_model=ProofOrderOut,
    summary="Update proof order status",
)
async def update_proof_order_status(
    order_id: UUID,
    payload: ProofOrderStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProofOrder:
    if payload.status not in PROOF_ORDER_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status: {payload.status}")

    stmt = select(ProofOrder).where(
        ProofOrder.id == order_id,
        ProofOrder.org_id == current_user["org_id"],
    )
    order = (await db.execute(stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Proof order not found")

    order.status = payload.status
    if payload.tracking_number is not None:
        order.tracking_number = payload.tracking_number
    if payload.estimated_delivery is not None:
        order.estimated_delivery = payload.estimated_delivery
    if payload.notes is not None:
        order.notes = payload.notes
    if payload.status == "approved":
        order.approved = True
        order.approved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(order)
    return order
