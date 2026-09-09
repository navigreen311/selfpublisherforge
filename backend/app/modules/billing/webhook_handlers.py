"""
Dedicated Stripe webhook handlers for billing events.

Handles subscription upgrades, downgrades, payment failures, cancellations,
and trial events with proper idempotency, notifications, and logging.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.plans import get_plan_limits
from app.modules.notifications.models import NotificationType
from app.modules.notifications.service import create_notification
from app.schemas.common import PlanTier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Webhook Event Handlers
# ---------------------------------------------------------------------------


async def handle_subscription_upgrade(
    db: AsyncSession,
    org_id: UUID,
    subscription: dict[str, Any],
    old_tier: PlanTier,
    new_tier: PlanTier,
) -> None:
    """Handle subscription upgrade to a higher tier.

    - Update org subscription record immediately
    - Grant access to new tier modules
    - Send upgrade confirmation notification
    - Log billing event
    """
    logger.info(
        "Processing subscription upgrade for org %s: %s -> %s",
        org_id,
        old_tier.value,
        new_tier.value,
    )

    # Update organization
    status = subscription.get("status", "active")
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
            "plan_tier": new_tier.value,
            "subscription_status": status,
            "stripe_subscription_id": subscription.get("id"),
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
        },
    )

    # Log billing event
    await _log_billing_event(
        db,
        org_id,
        event_type="subscription_upgraded",
        event_data={
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "subscription_id": subscription.get("id"),
        },
        stripe_event_id=subscription.get("id"),  # Will be updated with actual event ID
    )

    # Get org owner for notification
    user_id, user_email = await _get_org_owner(db, org_id)
    if user_id:
        new_limits = get_plan_limits(new_tier)
        await create_notification(
            db,
            payload=type(
                "Payload",
                (),
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "type": NotificationType.SUCCESS,
                    "title": f"Upgraded to {new_tier.value.title()} Plan",
                    "message": (
                        f'Your subscription has been upgraded. You now have access to '
                        f'{new_limits.max_projects or "unlimited"} projects and '
                        f'{new_limits.ai_generations_per_day} AI generations per day.'
                    ),
                    "data": {
                        "tier": new_tier.value,
                        "max_projects": new_limits.max_projects,
                        "ai_generations_per_day": new_limits.ai_generations_per_day,
                    },
                },
            )(),
            recipient_email=user_email,
        )

    logger.info("Subscription upgrade completed for org %s", org_id)


async def handle_subscription_downgrade(
    db: AsyncSession,
    org_id: UUID,
    subscription: dict[str, Any],
    old_tier: PlanTier,
    new_tier: PlanTier,
) -> None:
    """Handle subscription downgrade to a lower tier.

    - Schedule downgrade for end of billing period
    - Show warning about features that will be lost
    - Send downgrade notification
    - Grace period handling (if cancel_at_period_end is true)
    """
    logger.info(
        "Processing subscription downgrade for org %s: %s -> %s",
        org_id,
        old_tier.value,
        new_tier.value,
    )

    cancel_at_period_end = subscription.get("cancel_at_period_end", False)
    current_period_end = None

    if subscription.get("current_period_end"):
        current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=UTC)

    # If cancel_at_period_end, keep current tier until period ends
    tier_to_set = old_tier.value if cancel_at_period_end else new_tier.value

    await _update_org(
        db,
        org_id,
        {
            "plan_tier": tier_to_set,
            "subscription_status": subscription.get("status", "active"),
            "stripe_subscription_id": subscription.get("id"),
            "cancel_at_period_end": cancel_at_period_end,
            "current_period_end": current_period_end,
        },
    )

    # Log billing event
    await _log_billing_event(
        db,
        org_id,
        event_type="subscription_downgraded",
        event_data={
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "scheduled": cancel_at_period_end,
            "effective_date": current_period_end.isoformat() if current_period_end else None,
        },
        stripe_event_id=subscription.get("id"),
    )

    # Get org owner for notification
    user_id, user_email = await _get_org_owner(db, org_id)
    if user_id:
        old_limits = get_plan_limits(old_tier)
        new_limits = get_plan_limits(new_tier)

        message = f"Your subscription will be downgraded to {new_tier.value.title()} plan"
        if cancel_at_period_end and current_period_end:
            message += f' on {current_period_end.strftime("%B %d, %Y")}'
        message += (
            f'. Projects will be limited to {new_limits.max_projects or "unlimited"} '
            f'(currently {old_limits.max_projects or "unlimited"}).'
        )

        await create_notification(
            db,
            payload=type(
                "Payload",
                (),
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "type": NotificationType.WARNING,
                    "title": "Subscription Downgrade Scheduled",
                    "message": message,
                    "data": {
                        "old_tier": old_tier.value,
                        "new_tier": new_tier.value,
                        "effective_date": current_period_end.isoformat() if current_period_end else None,
                    },
                },
            )(),
            recipient_email=user_email,
        )

    logger.info("Subscription downgrade processed for org %s", org_id)


async def handle_payment_failure(
    db: AsyncSession,
    org_id: UUID,
    invoice: dict[str, Any],
    attempt_count: int,
) -> None:
    """Handle invoice payment failure.

    - Update subscription status to past_due
    - Send payment failure email (1st, 2nd, 3rd attempt)
    - After 3 failures, move to unpaid status
    - Restrict access to free tier modules only after 3 failures
    - Log all payment attempts
    """
    logger.warning(
        "Payment failure for org %s: invoice %s (attempt %d)",
        org_id,
        invoice.get("id"),
        attempt_count,
    )

    # Determine status based on attempt count
    if attempt_count >= 3:
        new_status = "unpaid"
        # Move to free tier after 3 failed attempts
        await _update_org(
            db,
            org_id,
            {
                "subscription_status": new_status,
                "plan_tier": PlanTier.FREE.value,
            },
        )
    else:
        new_status = "past_due"
        await _update_org(
            db,
            org_id,
            {
                "subscription_status": new_status,
            },
        )

    # Log billing event
    await _log_billing_event(
        db,
        org_id,
        event_type="payment_failed",
        event_data={
            "invoice_id": invoice.get("id"),
            "attempt_count": attempt_count,
            "amount_due": invoice.get("amount_due"),
            "status": new_status,
        },
        stripe_event_id=invoice.get("id"),
    )

    # Get org owner for notification
    user_id, user_email = await _get_org_owner(db, org_id)
    if user_id:
        if attempt_count >= 3:
            title = "Payment Failed - Account Downgraded"
            message = (
                "We were unable to process your payment after 3 attempts. "
                "Your account has been downgraded to the Free tier. "
                "Please update your payment method to restore your subscription."
            )
            notif_type = NotificationType.ERROR
        elif attempt_count == 2:
            title = "Payment Failed - Final Attempt"
            message = (
                "We were unable to process your payment (attempt 2 of 3). "
                "Please update your payment method immediately to avoid service interruption."
            )
            notif_type = NotificationType.WARNING
        else:
            title = "Payment Failed"
            message = (
                f"We were unable to process your payment (attempt {attempt_count} of 3). "
                "Please check your payment method."
            )
            notif_type = NotificationType.WARNING

        await create_notification(
            db,
            payload=type(
                "Payload",
                (),
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "type": notif_type,
                    "title": title,
                    "message": message,
                    "data": {
                        "invoice_id": invoice.get("id"),
                        "attempt_count": attempt_count,
                        "amount_due": invoice.get("amount_due"),
                    },
                },
            )(),
            recipient_email=user_email,
        )

    logger.info("Payment failure processed for org %s (attempt %d)", org_id, attempt_count)


async def handle_subscription_canceled(
    db: AsyncSession,
    org_id: UUID,
    subscription: dict[str, Any],
) -> None:
    """Handle subscription cancellation.

    - Move org to free tier
    - Preserve data (don't delete anything)
    - Send cancellation confirmation
    - Trigger win-back email sequence after 7 days (via event log)
    """
    logger.info(
        "Processing subscription cancellation for org %s: sub %s",
        org_id,
        subscription.get("id"),
    )

    await _update_org(
        db,
        org_id,
        {
            "plan_tier": PlanTier.FREE.value,
            "subscription_status": "canceled",
            "stripe_subscription_id": subscription.get("id"),
            "cancel_at_period_end": False,
        },
    )

    # Log billing event (will trigger win-back sequence)
    await _log_billing_event(
        db,
        org_id,
        event_type="subscription_canceled",
        event_data={
            "subscription_id": subscription.get("id"),
            "canceled_at": datetime.now(UTC).isoformat(),
        },
        stripe_event_id=subscription.get("id"),
    )

    # Get org owner for notification
    user_id, user_email = await _get_org_owner(db, org_id)
    if user_id:
        await create_notification(
            db,
            payload=type(
                "Payload",
                (),
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "type": NotificationType.INFO,
                    "title": "Subscription Canceled",
                    "message": (
                        "Your subscription has been canceled. Your account has been moved to the Free tier. "
                        "All your data has been preserved and you can resubscribe at any time."
                    ),
                    "data": {
                        "subscription_id": subscription.get("id"),
                    },
                },
            )(),
            recipient_email=user_email,
        )

    logger.info("Subscription cancellation processed for org %s", org_id)


async def handle_trial_will_end(
    db: AsyncSession,
    org_id: UUID,
    subscription: dict[str, Any],
    days_remaining: int,
) -> None:
    """Handle trial ending soon.

    - Send reminder 3 days before trial ends
    - Send reminder on trial end day
    """
    logger.info(
        "Trial ending soon for org %s: %d days remaining",
        org_id,
        days_remaining,
    )

    # Get org owner for notification
    user_id, user_email = await _get_org_owner(db, org_id)
    if user_id:
        if days_remaining == 0:
            title = "Trial Ends Today"
            message = "Your trial ends today. Subscribe now to continue using premium features."
        else:
            title = f"Trial Ends in {days_remaining} Days"
            message = f"Your trial ends in {days_remaining} days. Subscribe now to keep your premium features."

        await create_notification(
            db,
            payload=type(
                "Payload",
                (),
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "type": NotificationType.WARNING,
                    "title": title,
                    "message": message,
                    "data": {
                        "days_remaining": days_remaining,
                        "subscription_id": subscription.get("id"),
                    },
                },
            )(),
            recipient_email=user_email,
        )

    # Log billing event
    await _log_billing_event(
        db,
        org_id,
        event_type="trial_will_end",
        event_data={
            "days_remaining": days_remaining,
            "subscription_id": subscription.get("id"),
        },
        stripe_event_id=subscription.get("id"),
    )

    logger.info("Trial ending notification sent for org %s", org_id)


async def handle_invoice_paid(
    db: AsyncSession,
    org_id: UUID,
    invoice: dict[str, Any],
) -> None:
    """Handle successful invoice payment.

    - Ensure subscription is active
    - Clear any past_due status
    - Log successful payment
    """
    logger.info("Invoice paid for org %s: %s", org_id, invoice.get("id"))

    await _update_org(
        db,
        org_id,
        {
            "subscription_status": "active",
        },
    )

    # Log billing event
    await _log_billing_event(
        db,
        org_id,
        event_type="invoice_paid",
        event_data={
            "invoice_id": invoice.get("id"),
            "amount_paid": invoice.get("amount_paid"),
            "currency": invoice.get("currency"),
        },
        stripe_event_id=invoice.get("id"),
    )


# ---------------------------------------------------------------------------
# Idempotency helpers
# ---------------------------------------------------------------------------


async def is_event_processed(
    db: AsyncSession,
    stripe_event_id: str,
) -> bool:
    """Check if a Stripe webhook event has already been processed.

    Returns True if the event ID exists in billing_events table.
    """
    result = await db.execute(
        text("SELECT 1 FROM billing_events WHERE stripe_event_id = :event_id LIMIT 1"),
        {"event_id": stripe_event_id},
    )
    return result.scalar_one_or_none() is not None


async def mark_event_processed(
    db: AsyncSession,
    stripe_event_id: str,
    event_type: str,
) -> None:
    """Mark a Stripe webhook event as processed for idempotency.

    This is a simple marker. The actual event data is logged via _log_billing_event.
    """
    await db.execute(
        text(
            """
            INSERT INTO billing_events (org_id, event_type, stripe_event_id, event_data, created_at)
            VALUES (
                '00000000-0000-0000-0000-000000000000',
                :event_type,
                :stripe_event_id,
                '{}',
                NOW()
            )
            ON CONFLICT (stripe_event_id) DO NOTHING
            """
        ),
        {
            "event_type": event_type,
            "stripe_event_id": stripe_event_id,
        },
    )


async def get_payment_attempt_count(
    db: AsyncSession,
    org_id: UUID,
    invoice_id: str,
) -> int:
    """Get the number of payment failure attempts for an invoice.

    Counts billing_events with event_type='payment_failed' for this invoice.
    """
    result = await db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM billing_events
            WHERE org_id = :org_id
            AND event_type = 'payment_failed'
            AND event_data->>'invoice_id' = :invoice_id
            """
        ),
        {
            "org_id": str(org_id),
            "invoice_id": invoice_id,
        },
    )
    count = result.scalar_one()
    # Return count + 1 because this is the current attempt
    return (count or 0) + 1


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def _update_org(
    db: AsyncSession,
    org_id: UUID,
    data: dict[str, Any],
) -> None:
    """Update columns on the organizations table."""
    if not data:
        return
    set_clauses = ", ".join(f"{key} = :{key}" for key in data)
    params = {**data, "org_id": str(org_id)}
    # Dynamic column names, but values are parameterized (safe from SQL injection)
    await db.execute(
        text(f"UPDATE organizations SET {set_clauses}, updated_at = NOW() WHERE id = :org_id"),  # noqa: S608
        params,
    )
    await db.flush()


async def _get_org_owner(
    db: AsyncSession,
    org_id: UUID,
) -> tuple[UUID | None, str | None]:
    """Get the owner user_id and email for an organization.

    Returns (user_id, email) or (None, None) if not found.
    """
    result = await db.execute(
        text(
            """
            SELECT u.id, u.email
            FROM users u
            JOIN organization_members om ON u.id = om.user_id
            WHERE om.org_id = :org_id AND om.role = 'owner'
            LIMIT 1
            """
        ),
        {"org_id": str(org_id)},
    )
    row = result.mappings().first()
    if row:
        user_id_value = row.get("id") or row.get(0)
        email_value = row.get("email") or row.get(1)
        if user_id_value and email_value:
            return UUID(str(user_id_value)), email_value
    return None, None


async def _log_billing_event(
    db: AsyncSession,
    org_id: UUID,
    event_type: str,
    event_data: dict[str, Any],
    stripe_event_id: str | None = None,
) -> None:
    """Log a billing event for audit trail and win-back triggers.

    Creates a record in the billing_events table.
    """
    import json

    await db.execute(
        text(
            """
            INSERT INTO billing_events (org_id, event_type, event_data, stripe_event_id, created_at)
            VALUES (:org_id, :event_type, :event_data::jsonb, :stripe_event_id, NOW())
            ON CONFLICT (stripe_event_id) DO NOTHING
            """
        ),
        {
            "org_id": str(org_id),
            "event_type": event_type,
            "event_data": json.dumps(event_data),
            "stripe_event_id": stripe_event_id,
        },
    )
    await db.flush()
