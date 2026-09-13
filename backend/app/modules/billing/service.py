"""
Billing service -- handles Stripe customer creation, checkout sessions,
portal sessions, webhook event processing, and usage tracking.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.sql import assert_known_columns
from app.models.organization import Organization as _OrgModel
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
from app.schemas.common import PlanTier

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
    placeholder_patterns = ["PLACEHOLDER", "CHANGE_ME", "YOUR_", "REPLACE_", "TODO", "XXX"]
    if not key or any(p in key.upper() for p in placeholder_patterns):
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
                created=datetime.fromtimestamp(inv.created, tz=UTC),
                period_start=datetime.fromtimestamp(inv.period_start, tz=UTC),
                period_end=datetime.fromtimestamp(inv.period_end, tz=UTC),
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
    "customer.subscription.trial_will_end",
    "invoice.paid",
    "invoice.payment_failed",
}


async def handle_webhook_event(
    db: AsyncSession,
    payload: bytes,
    sig_header: str,
) -> dict[str, str]:
    """Verify and process a Stripe webhook event with idempotency.

    Returns a dict with at minimum ``{"status": "..."}`` indicating
    the processing result.

    Features:
    - Signature verification
    - Idempotency via event ID tracking
    - Upgrade/downgrade detection
    - Payment failure retry tracking
    - Trial ending notifications
    """
    _ensure_stripe_configured()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise AppException(
            status_code=400,
            code="WEBHOOK_SIGNATURE_INVALID",
            message="Invalid Stripe webhook signature.",
        ) from None

    event_id: str = event["id"]
    event_type: str = event["type"]
    logger.info("Received Stripe webhook event: %s (id: %s)", event_type, event_id)

    # Check idempotency - has this event already been processed?
    from app.modules.billing.webhook_handlers import is_event_processed, mark_event_processed

    if await is_event_processed(db, event_id):
        logger.info("Event %s already processed, skipping", event_id)
        return {"status": "duplicate", "event_type": event_type, "event_id": event_id}

    if event_type not in HANDLED_EVENTS:
        return {"status": "ignored", "event_type": event_type}

    data_object: dict[str, Any] = event["data"]["object"]

    # Process the event
    if event_type.startswith("customer.subscription."):
        await _handle_subscription_event(db, event_type, data_object, event_id)
    elif event_type == "invoice.paid":
        await _handle_invoice_paid(db, data_object, event_id)
    elif event_type == "invoice.payment_failed":
        await _handle_invoice_payment_failed(db, data_object, event_id)

    # Mark event as processed for idempotency
    await mark_event_processed(db, event_id, event_type)
    await db.commit()

    return {"status": "processed", "event_type": event_type, "event_id": event_id}


# ---------------------------------------------------------------------------
# Internal webhook handlers
# ---------------------------------------------------------------------------


async def _handle_subscription_event(
    db: AsyncSession,
    event_type: str,
    subscription: dict[str, Any],
    event_id: str,
) -> None:
    """Process subscription created / updated / deleted events with upgrade/downgrade detection."""
    from app.modules.billing.plans import is_upgrade
    from app.modules.billing.webhook_handlers import (
        handle_subscription_canceled,
        handle_subscription_downgrade,
        handle_subscription_upgrade,
        handle_trial_will_end,
    )

    # Resolve org_id
    org_id_str = subscription.get("metadata", {}).get("org_id")
    if not org_id_str:
        # Try to resolve from customer
        customer_id = subscription.get("customer")
        org_id_str = await _org_id_from_customer(db, customer_id)

    if not org_id_str:
        logger.warning("No org_id found for subscription event %s", event_type)
        return

    org_id = UUID(org_id_str) if isinstance(org_id_str, str) else org_id_str

    # Special handling for specific events
    if event_type == "customer.subscription.deleted":
        await handle_subscription_canceled(db, org_id, subscription)
        return

    if event_type == "customer.subscription.trial_will_end":
        # Calculate days remaining
        trial_end = subscription.get("trial_end")
        if trial_end:
            days_remaining = max(0, int((trial_end - datetime.now(UTC).timestamp()) / 86400))
            await handle_trial_will_end(db, org_id, subscription, days_remaining)
        return

    # For created/updated events, detect upgrade/downgrade
    plan_tier_value = subscription.get("metadata", {}).get("plan_tier")
    if not plan_tier_value:
        # If no plan tier in metadata, fall back to basic update
        logger.warning("No plan_tier in subscription metadata for event %s", event_type)
        status = subscription.get("status", "active")
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)

        current_period_start = None
        current_period_end = None
        if subscription.get("current_period_start"):
            current_period_start = datetime.fromtimestamp(subscription["current_period_start"], tz=UTC)
        if subscription.get("current_period_end"):
            current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=UTC)

        await _update_org(
            db,
            org_id,
            {
                "subscription_status": status,
                "stripe_subscription_id": subscription.get("id"),
                "cancel_at_period_end": cancel_at_period_end,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
            },
        )
        return

    new_tier = PlanTier(plan_tier_value)

    # Get current tier
    org_row = await _get_org_row(db, org_id)
    old_tier = PlanTier(org_row.get("plan_tier", "free"))

    # Detect upgrade vs downgrade
    if old_tier != new_tier:
        if is_upgrade(old_tier, new_tier):
            await handle_subscription_upgrade(db, org_id, subscription, old_tier, new_tier)
        else:
            await handle_subscription_downgrade(db, org_id, subscription, old_tier, new_tier)
    else:
        # Same tier, just update subscription data
        status = subscription.get("status", "active")
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)

        current_period_start = None
        current_period_end = None
        if subscription.get("current_period_start"):
            current_period_start = datetime.fromtimestamp(subscription["current_period_start"], tz=UTC)
        if subscription.get("current_period_end"):
            current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=UTC)

        await _update_org(
            db,
            org_id,
            {
                "subscription_status": status,
                "stripe_subscription_id": subscription.get("id"),
                "cancel_at_period_end": cancel_at_period_end,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
            },
        )

    logger.info(
        "Processed %s for org %s: %s -> %s",
        event_type,
        org_id,
        old_tier.value,
        new_tier.value,
    )


async def _handle_invoice_paid(
    db: AsyncSession,
    invoice: dict[str, Any],
    event_id: str,
) -> None:
    """Handle a successful invoice payment."""
    from app.modules.billing.webhook_handlers import handle_invoice_paid

    customer_id = invoice.get("customer")
    org_id_str = await _org_id_from_customer(db, customer_id)
    if org_id_str:
        org_id = UUID(org_id_str)
        await handle_invoice_paid(db, org_id, invoice)


async def _handle_invoice_payment_failed(
    db: AsyncSession,
    invoice: dict[str, Any],
    event_id: str,
) -> None:
    """Handle a failed invoice payment with retry tracking."""
    from app.modules.billing.webhook_handlers import (
        get_payment_attempt_count,
        handle_payment_failure,
    )

    customer_id = invoice.get("customer")
    org_id_str = await _org_id_from_customer(db, customer_id)
    if org_id_str:
        org_id = UUID(org_id_str)
        invoice_id = invoice.get("id")

        # Get attempt count for this invoice
        attempt_count = await get_payment_attempt_count(db, org_id, str(invoice_id))

        await handle_payment_failure(db, org_id, invoice, attempt_count)


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
        return cast("str", existing_customer_id)

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
        text("SELECT * FROM organizations WHERE id = :org_id AND deleted_at IS NULL LIMIT 1"),
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
    assert_known_columns(_OrgModel, data)
    set_clauses = ", ".join(f"{key} = :{key}" for key in data)
    params = {**data, "org_id": str(org_id)}
    await db.execute(
        text(f"UPDATE organizations SET {set_clauses}, updated_at = NOW() WHERE id = :org_id"),  # noqa: S608  # column names validated by assert_known_columns; values are bound
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
        text("SELECT id FROM organizations WHERE stripe_customer_id = :cid AND deleted_at IS NULL LIMIT 1"),
        {"cid": customer_id},
    )
    result = row.mappings().first()
    return str(result["id"]) if result else None
