"""
Billing API router -- exposes endpoints for plan listing, subscription
management, Stripe checkout, billing portal, usage stats, invoices,
and webhook handling.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.team.permissions import require_permission
from app.modules.billing import service
from app.modules.billing.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    InvoiceListResponse,
    PlanInfo,
    PortalRequest,
    PortalResponse,
    SubscriptionResponse,
    UsageStats,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /plans -- public (no auth required)
# ---------------------------------------------------------------------------

@router.get(
    "/plans",
    response_model=list[PlanInfo],
    summary="List billing plans",
    description="Return all available billing plans. Public endpoint, no auth required.",
)
async def list_plans() -> list[PlanInfo]:
    """Return all available billing plans."""
    return service.list_plans()


# ---------------------------------------------------------------------------
# GET /subscription
# ---------------------------------------------------------------------------

@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Get current subscription",
    description="Get the current subscription details for the user's organization.",
)
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Get the current subscription for the user's organization."""
    return await service.get_subscription(db, current_user["org_id"])


# ---------------------------------------------------------------------------
# POST /subscribe -- creates a Stripe Checkout session
# ---------------------------------------------------------------------------

@router.post(
    "/subscribe",
    response_model=CheckoutResponse,
    summary="Create checkout session",
    description="Create a Stripe Checkout session for subscribing or upgrading. Requires admin or owner role.",
    dependencies=[Depends(require_permission("billing", "create"))],
)
async def create_checkout(
    body: CheckoutRequest,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for subscribing / upgrading."""
    return await service.create_checkout_session(
        db=db,
        org_id=current_user["org_id"],
        user_email=current_user.get("email", ""),
        request=body,
    )


# ---------------------------------------------------------------------------
# POST /portal -- creates a Stripe billing portal session
# ---------------------------------------------------------------------------

@router.post(
    "/portal",
    response_model=PortalResponse,
    summary="Create billing portal session",
    description="Create a Stripe billing portal session for managing payment methods.",
)
async def create_portal(
    body: PortalRequest,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
) -> PortalResponse:
    """Create a Stripe billing portal session for managing payment methods."""
    return await service.create_portal_session(
        db=db,
        org_id=current_user["org_id"],
        request=body,
    )


# ---------------------------------------------------------------------------
# POST /webhook -- Stripe webhook handler (no auth, uses signature)
# ---------------------------------------------------------------------------

@router.post(
    "/webhook",
    summary="Stripe webhook",
    description="Handle incoming Stripe webhook events. Authenticated via Stripe signature, not JWT.",
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    return await service.handle_webhook_event(db, payload, sig_header)


# ---------------------------------------------------------------------------
# GET /usage
# ---------------------------------------------------------------------------

@router.get(
    "/usage",
    response_model=UsageStats,
    summary="Get usage statistics",
    description="Get current usage statistics (API calls, storage, AI tokens) for the organization.",
)
async def get_usage(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageStats:
    """Get current usage statistics for the user's organization."""
    return await service.get_usage_stats(db, current_user["org_id"])


# ---------------------------------------------------------------------------
# GET /invoices
# ---------------------------------------------------------------------------

@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="List invoices for the user's organization.",
)
async def list_invoices(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvoiceListResponse:
    """List invoices for the user's organization."""
    return await service.list_invoices(db, current_user["org_id"], limit=limit)
