"""
Billing service -- handles Stripe customer creation, checkout sessions,
portal sessions, webhook event processing, and usage tracking.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.schemas.common import PlanTier
from app.modules.billing.plans import (
    PLAN_DEFINITIONS,
    get_plan_limits,
)
from app.modules.billing.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    InvoiceItem,
    InvoiceListResponse,
    PlanInfo,
    PortalRequest,
    PortalResponse,
    SubscriptionResponse,
    UsageStats,
)

logger = logging.getLogger(__name__)
settings = get_settings()

_stripe_configured = False


def _ensure_stripe_configured() -> None:
    """Lazily configure the Stripe API key on first use.

    Raises a clear error when the key is missing or still set to a
    placeholder value, instead of failing cryptically at call time.
    """
    global _stripe_configured
    if _stripe_configured:
        return

    key = settings.STRIPE_SECRET_KEY
    if not key or key.startswith("sk_test_PLACEHOLDER") or key == "CHANGE_ME":
        raise AppException(
            status_code=500,
            code="STRIPE_NOT_CONFIGURED",
            message="Stripe is not configured. Set STRIPE_SECRET_KEY in environment.",
        )

    stripe.api_key = key
    _stripe_configured = True

# ---------------------------------------------------------------------------
# Mapping: PlanTier -> Stripe Price ID (read from settings)
# ---------------------------------------------------------------------------

_TIER_TO_PRICE_ID: dict[PlanTier, str] = {}


def _resolve_price_ids() -> dict[PlanTier, str]:
    """Lazily resolve Stripe price IDs from settings."""
    global _TIER_TO_PRICE_ID
    if _TIER_TO_PRICE_ID:
        return _TIER_TO_PRICE_ID
    mapping: dict[PlanTier, str] = {}
    if settings.STRIPE_PRICE_STARTER:
        mapping[PlanTier.STARTER] = settings.STRIPE_PRICE_STARTER
    if settings.STRIPE_PRICE_PRO:
        mapping[PlanTier.PRO] = settings.STRIPE_PRICE_PRO
    if settings.STRIPE_PRICE_BUSINESS:
        mapping[PlanTier.BUSINESS] = settings.STRIPE_PRICE_BUSINESS
    if settings.STRIPE_PRICE_ENTERPRISE:
        mapping[PlanTier.ENTERPRISE] = settings.STRIPE_PRICE_ENTERPRISE
    _TIER_TO_PRICE_ID = mapping
    return mapping


def _price_id_for_tier(tier: PlanTier) -> str:
    prices = _resolve_price_ids()
    price_id = prices.get(tier)
    if not price_id:
        raise AppException(
            status_code=400,
            code="INVALID_PLAN",
            message=f"No Stripe price configured for plan tier: {tier.value}",
        )
    return price_id


# ---------------------------------------------------------------------------
# Plan listing
# ---------------------------------------------------------------------------


def list_plans() -> list[PlanInfo]:
    """Return all available plans as PlanInfo objects."""
    plans: list[PlanInfo] = []
    for defn in sorted(PLAN_DEFINITIONS.values(), key=lambda p: p.price_monthly):
        plans.append(
            PlanInfo(
                tier=defn.tier,
                name=defn.name,
                price_monthly=defn.price_monthly,
                description=defn.description,
                max_projects=defn.limits.max_projects,
                ai_generations_per_day=defn.limits.ai_generations_per_day,
                features=defn.limits.features,
                highlight=defn.highlight,
            )
        )
    return plans


# ---------------------------------------------------------------------------
# Subscription retrieval
# ---------------------------------------------------------------------------


async def get_subscription(
    db: AsyncSession,
    org_id: UUID,
) -> SubscriptionResponse:
    """Get the current subscription info for an organization.

    Reads organization data from the DB.  The organization table is expected
    to have columns: plan_tier, subscription_status, stripe_subscription_id,
    stripe_customer_id, current_period_start, current_period_end,
    cancel_at_period_end.
    """
    row = await _get_org_row(db, org_id)
    return SubscriptionResponse(
        org_id=org_id,
        plan_tier=PlanTier(row.get("plan_tier", "free")),
        subscription_status=row.get("subscription_status", "none"),
        stripe_subscription_id=row.get("stripe_subscription_id"),
        stripe_customer_id=row.get("stripe_customer_id"),
        current_period_start=row.get("current_period_start"),
        current_period_end=row.get("current_period_end"),
        cancel_at_period_end=row.get("cancel_at_period_end", False),
    )


# ---------------------------------------------------------------------------
# Stripe Checkout session
# ---------------------------------------------------------------------------


async def create_checkout_session(
    db: AsyncSession,
    org_id: UUID,
    user_email: str,
    request: CheckoutRequest,
) -> CheckoutResponse:
    """Create a Stripe Checkout session for upgrading / subscribing."""
    _ensure_stripe_configured()
    if request.plan_tier == PlanTier.FREE:
        raise AppException(
            status_code=400,
            code="INVALID_PLAN",
            message="Cannot checkout for the Free plan.",
        )

    price_id = _price_id_for_tier(request.plan_tier)
    customer_id = await _ensure_stripe_customer(db, org_id, user_email)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        metadata={"org_id": str(org_id), "plan_tier": request.plan_tier.value},
    )

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


# ---------------------------------------------------------------------------
# Stripe Billing Portal session
# ---------------------------------------------------------------------------


async def create_portal_session(
    db: AsyncSession,
    org_id: UUID,
    request: PortalRequest,
) -> PortalResponse:
    """Create a Stripe Billing Portal session so users can manage payments."""
    _ensure_stripe_configured()
    row = await _get_org_row(db, org_id)
    customer_id = row.get("stripe_customer_id")
    if not customer_id:
        raise AppException(
            status_code=400,
            code="NO_CUSTOMER",
            message="No Stripe customer found. Please subscribe to a plan first.",
        )

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.return_url,
    )
    return PortalResponse(portal_url=session.url)


# ---------------------------------------------------------------------------
# Usage tracking
# ---------------------------------------------------------------------------


async def get_usage_stats(
    db: AsyncSession,
    org_id: UUID,
) -> UsageStats:
    """Retrieve current usage stats for an organization."""
    row = await _get_org_row(db, org_id)
    tier = PlanTier(row.get("plan_tier", "free"))
    limits = get_plan_limits(tier)

    # Read usage counters from the database.
    # In a full implementation these would come from dedicated usage tables.
    projects_used = row.get("projects_count", 0)
    ai_generations_used_today = row.get("ai_generations_today", 0)

    return UsageStats(
        org_id=org_id,
        plan_tier=tier,
        projects_used=projects_used,
        projects_limit=limits.max_projects,
        ai_generations_used_today=ai_generations_used_today,
        ai_generations_daily_limit=limits.ai_generations_per_day,
        current_period_start=row.get("current_period_start"),
        current_period_end=row.get("current_period_end"),
    )


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------


async def list_invoices(
    db: AsyncSession,
    org_id: UUID,
    limit: int = 10,
) -> InvoiceListResponse:
    """Fetch invoices for the organization from Stripe."""
    _ensure_stripe_configured()
    row = await _get_org_row(db, org_id)
    customer_id = row.get("stripe_customer_id")
    if not customer_id:
        return InvoiceListResponse(invoices=[], has_more=False)

    result = stripe.Invoice.list(customer=customer_id, limit=limit)
    invoices: list[InvoiceItem] = []
    for inv in result.data:
        invoices.append(
            InvoiceItem(
                id=inv.id,
                number=inv.number,
                status=inv.status or "unknown",
                amount_due=inv.amount_due,
                amount_paid=inv.amount_paid,
                currency=inv.currency or "usd",
                created=datetime.fromtimestamp(inv.created, tz=timezone.utc),
                period_start=datetime.fromtimestamp(inv.period_start, tz=timezone.utc),
                period_end=datetime.fromtimestamp(inv.period_end, tz=timezone.utc),
                hosted_invoice_url=inv.hosted_invoice_url,
                invoice_pdf=inv.invoice_pdf,
            )
        )
    return InvoiceListResponse(invoices=invoices, has_more=result.has_more)


# ---------------------------------------------------------------------------
# Webhook handling
# ---------------------------------------------------------------------------

HANDLED_EVENTS = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
}


async def handle_webhook_event(
    db: AsyncSession,
    payload: bytes,
    sig_header: str,
) -> dict[str, str]:
    """Verify and process a Stripe webhook event.

    Returns a dict with at minimum ``{"status": "..."}`` indicating
    the processing result.
    """
    _ensure_stripe_configured()
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError:
        raise AppException(
            status_code=400,
            code="WEBHOOK_SIGNATURE_INVALID",
            message="Invalid Stripe webhook signature.",
        )

    event_type: str = event["type"]
    logger.info("Received Stripe webhook event: %s", event_type)

    if event_type not in HANDLED_EVENTS:
        return {"status": "ignored", "event_type": event_type}

    data_object: dict[str, Any] = event["data"]["object"]

    if event_type.startswith("customer.subscription."):
        await _handle_subscription_event(db, event_type, data_object)
    elif event_type == "invoice.paid":
        await _handle_invoice_paid(db, data_object)
    elif event_type == "invoice.payment_failed":
        await _handle_invoice_payment_failed(db, data_object)

    return {"status": "processed", "event_type": event_type}


# ---------------------------------------------------------------------------
# Internal webhook handlers
# ---------------------------------------------------------------------------


async def _handle_subscription_event(
    db: AsyncSession,
    event_type: str,
    subscription: dict[str, Any],
) -> None:
    """Process subscription created / updated / deleted events."""
    org_id_str = subscription.get("metadata", {}).get("org_id")
    if not org_id_str:
        # Try to resolve from customer
        customer_id = subscription.get("customer")
        org_id_str = await _org_id_from_customer(db, customer_id)

    if not org_id_str:
        logger.warning("No org_id found for subscription event %s", event_type)
        return

    org_id = UUID(org_id_str) if isinstance(org_id_str, str) else org_id_str

    status = subscription.get("status", "active")
    plan_tier_value = subscription.get("metadata", {}).get("plan_tier")
    cancel_at_period_end = subscription.get("cancel_at_period_end", False)

    # Derive period timestamps
    current_period_start = None
    current_period_end = None
    if subscription.get("current_period_start"):
        current_period_start = datetime.fromtimestamp(
            subscription["current_period_start"], tz=timezone.utc
        )
    if subscription.get("current_period_end"):
        current_period_end = datetime.fromtimestamp(
            subscription["current_period_end"], tz=timezone.utc
        )

    update_data: dict[str, Any] = {
        "subscription_status": status,
        "stripe_subscription_id": subscription.get("id"),
        "cancel_at_period_end": cancel_at_period_end,
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
    }
    if plan_tier_value:
        update_data["plan_tier"] = plan_tier_value

    if event_type == "customer.subscription.deleted":
        update_data["subscription_status"] = "canceled"
        update_data["plan_tier"] = PlanTier.FREE.value

    await _update_org(db, org_id, update_data)
    logger.info(
        "Processed %s for org %s -> status=%s",
        event_type,
        org_id,
        update_data["subscription_status"],
    )


async def _handle_invoice_paid(
    db: AsyncSession,
    invoice: dict[str, Any],
) -> None:
    """Handle a successful invoice payment."""
    customer_id = invoice.get("customer")
    org_id_str = await _org_id_from_customer(db, customer_id)
    if org_id_str:
        logger.info("Invoice paid for org %s: %s", org_id_str, invoice.get("id"))
        # Ensure subscription is active
        await _update_org(db, UUID(org_id_str), {"subscription_status": "active"})


async def _handle_invoice_payment_failed(
    db: AsyncSession,
    invoice: dict[str, Any],
) -> None:
    """Handle a failed invoice payment."""
    customer_id = invoice.get("customer")
    org_id_str = await _org_id_from_customer(db, customer_id)
    if org_id_str:
        logger.warning(
            "Invoice payment failed for org %s: %s",
            org_id_str,
            invoice.get("id"),
        )
        await _update_org(db, UUID(org_id_str), {"subscription_status": "past_due"})


# ---------------------------------------------------------------------------
# Stripe customer helpers
# ---------------------------------------------------------------------------


async def _ensure_stripe_customer(
    db: AsyncSession,
    org_id: UUID,
    email: str,
) -> str:
    """Return the Stripe customer ID for an org, creating one if needed."""
    _ensure_stripe_configured()
    row = await _get_org_row(db, org_id)
    existing_customer_id = row.get("stripe_customer_id")
    if existing_customer_id:
        return existing_customer_id

    customer = stripe.Customer.create(
        email=email,
        metadata={"org_id": str(org_id)},
    )
    await _update_org(db, org_id, {"stripe_customer_id": customer.id})
    return customer.id


# ---------------------------------------------------------------------------
# Database helpers (raw SQL to avoid depending on an ORM model from W02)
# ---------------------------------------------------------------------------


async def _get_org_row(db: AsyncSession, org_id: UUID) -> dict[str, Any]:
    """Fetch organization row as a dict.

    Uses raw SQL so we do not depend on a SQLAlchemy model that is
    owned by the organizations / W02 module.
    """
    from sqlalchemy import text

    row = await db.execute(
        text(
            "SELECT * FROM organizations WHERE id = :org_id AND deleted_at IS NULL LIMIT 1"
        ),
        {"org_id": str(org_id)},
    )
    result = row.mappings().first()
    if not result:
        raise AppException(
            status_code=404,
            code="ORG_NOT_FOUND",
            message=f"Organization {org_id} not found.",
        )
    return dict(result)


async def _update_org(
    db: AsyncSession,
    org_id: UUID,
    data: dict[str, Any],
) -> None:
    """Update columns on the organizations table."""
    from sqlalchemy import text

    if not data:
        return
    set_clauses = ", ".join(f"{key} = :{key}" for key in data)
    params = {**data, "org_id": str(org_id)}
    await db.execute(
        text(f"UPDATE organizations SET {set_clauses}, updated_at = NOW() WHERE id = :org_id"),
        params,
    )
    await db.flush()


async def _org_id_from_customer(
    db: AsyncSession,
    customer_id: str | None,
) -> str | None:
    """Resolve an org_id from a Stripe customer ID."""
    if not customer_id:
        return None
    from sqlalchemy import text

    row = await db.execute(
        text(
            "SELECT id FROM organizations WHERE stripe_customer_id = :cid AND deleted_at IS NULL LIMIT 1"
        ),
        {"cid": customer_id},
    )
    result = row.mappings().first()
    return str(result["id"]) if result else None
