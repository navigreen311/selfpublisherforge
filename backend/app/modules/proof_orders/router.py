"""FastAPI router for the Proof Orders module.

Endpoints (prefix /api/v1/publishing):
  POST   /{publishing_id}/order-proof
  POST   /{publishing_id}/skip-proof
  GET    /{publishing_id}/proof-status
  PATCH  /{publishing_id}/proof-review
  POST   /estimate-proof-cost       (helper, no publishing_id required)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.proof_orders import service
from app.modules.proof_orders.schemas import (
    ProofCostEstimate,
    ProofOrderCreate,
    ProofOrderOut,
    ProofOrderSkip,
    ProofReviewUpdate,
    ShippingMethod,
)

router = APIRouter()


@router.post(
    "/estimate-proof-cost",
    response_model=ProofCostEstimate,
)
async def estimate_proof_cost(
    page_count: int = Query(..., ge=24, le=828),
    interior_type: str = Query("black_white"),
    shipping_method: ShippingMethod = Query(ShippingMethod.STANDARD),
    current_user: dict = Depends(get_current_user),
) -> ProofCostEstimate:
    return service.estimate_cost(page_count, interior_type, shipping_method)


@router.post(
    "/{publishing_id}/order-proof",
    response_model=ProofOrderOut,
    status_code=status.HTTP_201_CREATED,
)
async def order_proof(
    publishing_id: UUID,
    payload: ProofOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ProofOrderOut:
    order = await service.create_order(
        db, current_user["org_id"], publishing_id, payload
    )
    return ProofOrderOut.model_validate(order)


@router.post(
    "/{publishing_id}/skip-proof",
    response_model=ProofOrderOut,
    status_code=status.HTTP_201_CREATED,
)
async def skip_proof(
    publishing_id: UUID,
    payload: ProofOrderSkip,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ProofOrderOut:
    order = await service.skip_proof(
        db, current_user["org_id"], publishing_id, payload.reason
    )
    return ProofOrderOut.model_validate(order)


@router.get(
    "/{publishing_id}/proof-status",
    response_model=ProofOrderOut,
)
async def proof_status(
    publishing_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ProofOrderOut:
    order = await service.get_by_publishing(
        db, current_user["org_id"], publishing_id
    )
    if order is None:
        raise HTTPException(status_code=404, detail="No proof order for this publishing")
    return ProofOrderOut.model_validate(order)


@router.patch(
    "/{publishing_id}/proof-review",
    response_model=ProofOrderOut,
)
async def proof_review(
    publishing_id: UUID,
    payload: ProofReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ProofOrderOut:
    try:
        order = await service.update_review(
            db, current_user["org_id"], publishing_id, payload
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if order is None:
        raise HTTPException(status_code=404, detail="Proof order not found")
    return ProofOrderOut.model_validate(order)
