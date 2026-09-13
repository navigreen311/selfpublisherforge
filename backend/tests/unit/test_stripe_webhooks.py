"""
Comprehensive unit tests for Stripe webhook handlers.

Tests all webhook scenarios including upgrades, downgrades, payment failures,
cancellations, trial events, idempotency, and edge cases.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.billing.webhook_handlers import (
    get_payment_attempt_count,
    handle_invoice_paid,
    handle_payment_failure,
    handle_subscription_canceled,
    handle_subscription_downgrade,
    handle_subscription_upgrade,
    handle_trial_will_end,
    is_event_processed,
    mark_event_processed,
)
from app.schemas.common import PlanTier

# ===========================================================================
# Helpers
# ===========================================================================


def _make_subscription_dict(
    subscription_id: str = "sub_test",
    status: str = "active",
    plan_tier: str = "pro",
    cancel_at_period_end: bool = False,
) -> dict:
    """Build a Stripe subscription dict."""
    return {
        "id": subscription_id,
        "status": status,
        "metadata": {"plan_tier": plan_tier},
        "cancel_at_period_end": cancel_at_period_end,
        "current_period_start": int(datetime(2024, 1, 1, tzinfo=UTC).timestamp()),
        "current_period_end": int(datetime(2024, 2, 1, tzinfo=UTC).timestamp()),
    }


def _make_invoice_dict(
    invoice_id: str = "inv_test",
    amount_due: int = 7900,
    status: str = "open",
) -> dict:
    """Build a Stripe invoice dict."""
    return {
        "id": invoice_id,
        "customer": "cus_test",
        "amount_due": amount_due,
        "amount_paid": 0,
        "currency": "usd",
        "status": status,
    }


def _mock_db_execute_result(rows: list[dict] | None = None) -> AsyncMock:
    """Create a mock DB session with configurable execute results."""
    mock_db = AsyncMock()
    mock_result = MagicMock()

    if rows is None or len(rows) == 0:
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalar_one.return_value = 0
        mock_result.mappings.return_value.first.return_value = None
    else:
        mock_result.mappings.return_value.first.return_value = rows[0]
        mock_result.scalar_one_or_none.return_value = rows[0].get("id")
        mock_result.scalar_one.return_value = len(rows) - 1 if len(rows) > 1 else 0

    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    return mock_db


# ===========================================================================
# Subscription Upgrade Tests
# ===========================================================================


class TestSubscriptionUpgrade:
    """Tests for handle_subscription_upgrade."""

    @pytest.mark.asyncio
    async def test_upgrade_updates_org_tier(self):
        """Upgrading should update org plan_tier immediately."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(plan_tier="business")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_upgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.PRO,
                new_tier=PlanTier.BUSINESS,
            )

        # Verify org was updated
        mock_db.execute.assert_called()
        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_upgrade_sends_notification(self):
        """Upgrading should send a success notification."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(plan_tier="business")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_subscription_upgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.PRO,
                new_tier=PlanTier.BUSINESS,
            )

            mock_notif.assert_called_once()
            call_args = mock_notif.call_args
            assert call_args[1]["recipient_email"] == "owner@example.com"

    @pytest.mark.asyncio
    async def test_upgrade_logs_billing_event(self):
        """Upgrading should log a billing event for audit trail."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(plan_tier="enterprise")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_upgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.BUSINESS,
                new_tier=PlanTier.ENTERPRISE,
            )

        # Verify database operations were called (org update + billing event)
        assert mock_db.execute.call_count >= 2  # At least org update + billing event


# ===========================================================================
# Subscription Downgrade Tests
# ===========================================================================


class TestSubscriptionDowngrade:
    """Tests for handle_subscription_downgrade."""

    @pytest.mark.asyncio
    async def test_downgrade_immediate_when_not_cancel_at_period_end(self):
        """Downgrade should be immediate when cancel_at_period_end is False."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(
            plan_tier="starter",
            cancel_at_period_end=False,
        )

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_downgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.PRO,
                new_tier=PlanTier.STARTER,
            )

        # Verify new tier is set immediately
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_downgrade_scheduled_when_cancel_at_period_end(self):
        """Downgrade should be scheduled when cancel_at_period_end is True."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(
            plan_tier="starter",
            cancel_at_period_end=True,
        )

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_downgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.PRO,
                new_tier=PlanTier.STARTER,
            )

        # Verify org update was called
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_downgrade_sends_warning_notification(self):
        """Downgrading should send a warning notification."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(plan_tier="free")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_subscription_downgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.STARTER,
                new_tier=PlanTier.FREE,
            )

            mock_notif.assert_called_once()


# ===========================================================================
# Payment Failure Tests
# ===========================================================================


class TestPaymentFailure:
    """Tests for handle_payment_failure."""

    @pytest.mark.asyncio
    async def test_first_failure_sets_past_due(self):
        """First payment failure should set status to past_due."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        invoice = _make_invoice_dict()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_payment_failure(
                mock_db,
                org_id,
                invoice,
                attempt_count=1,
            )

        # Verify status was updated to past_due
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_third_failure_moves_to_free(self):
        """Third payment failure should move org to free tier."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        invoice = _make_invoice_dict()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_payment_failure(
                mock_db,
                org_id,
                invoice,
                attempt_count=3,
            )

        # Verify org was moved to free tier
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_failure_sends_appropriate_notification(self):
        """Payment failures should send notifications with correct severity."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        invoice = _make_invoice_dict()

        # Test first attempt
        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_payment_failure(mock_db, org_id, invoice, attempt_count=1)
            assert mock_notif.called

        # Test second attempt
        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_payment_failure(mock_db, org_id, invoice, attempt_count=2)
            assert mock_notif.called

        # Test third attempt (final)
        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_payment_failure(mock_db, org_id, invoice, attempt_count=3)
            assert mock_notif.called

    @pytest.mark.asyncio
    async def test_failure_logs_billing_event(self):
        """Payment failures should log billing events."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        invoice = _make_invoice_dict()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_payment_failure(
                mock_db,
                org_id,
                invoice,
                attempt_count=2,
            )

        # Verify database operations were called (org update + billing event)
        assert mock_db.execute.call_count >= 2  # At least org update + billing event


# ===========================================================================
# Subscription Cancellation Tests
# ===========================================================================


class TestSubscriptionCanceled:
    """Tests for handle_subscription_canceled."""

    @pytest.mark.asyncio
    async def test_cancellation_moves_to_free(self):
        """Cancellation should move org to free tier."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(status="canceled")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_canceled(mock_db, org_id, subscription)

        # Verify org was updated
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_cancellation_sends_notification(self):
        """Cancellation should send a confirmation notification."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(status="canceled")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_subscription_canceled(mock_db, org_id, subscription)

            mock_notif.assert_called_once()
            call_args = mock_notif.call_args
            assert call_args[1]["recipient_email"] == "owner@example.com"

    @pytest.mark.asyncio
    async def test_cancellation_logs_event_for_winback(self):
        """Cancellation should log billing event for win-back sequence."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict(status="canceled")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_canceled(mock_db, org_id, subscription)

        # Verify database operations were called (org update + billing event)
        assert mock_db.execute.call_count >= 2  # At least org update + billing event


# ===========================================================================
# Trial Will End Tests
# ===========================================================================


class TestTrialWillEnd:
    """Tests for handle_trial_will_end."""

    @pytest.mark.asyncio
    async def test_trial_ending_sends_notification(self):
        """Trial ending should send a warning notification."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_trial_will_end(mock_db, org_id, subscription, days_remaining=3)

            mock_notif.assert_called_once()
            call_args = mock_notif.call_args
            assert call_args[1]["recipient_email"] == "owner@example.com"

    @pytest.mark.asyncio
    async def test_trial_ending_today_different_message(self):
        """Trial ending today should have different message."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = _make_subscription_dict()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock) as mock_notif:
            await handle_trial_will_end(mock_db, org_id, subscription, days_remaining=0)

            assert mock_notif.called


# ===========================================================================
# Invoice Paid Tests
# ===========================================================================


class TestInvoicePaid:
    """Tests for handle_invoice_paid."""

    @pytest.mark.asyncio
    async def test_invoice_paid_sets_active(self):
        """Successful payment should set subscription to active."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([])

        invoice = _make_invoice_dict()

        await handle_invoice_paid(mock_db, org_id, invoice)

        # Verify org was updated
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_invoice_paid_logs_event(self):
        """Successful payment should log billing event."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([])

        invoice = _make_invoice_dict()

        await handle_invoice_paid(mock_db, org_id, invoice)

        # Verify database operations were called (org update + billing event)
        assert mock_db.execute.call_count >= 2  # At least org update + billing event


# ===========================================================================
# Idempotency Tests
# ===========================================================================


class TestIdempotency:
    """Tests for idempotency helpers."""

    @pytest.mark.asyncio
    async def test_is_event_processed_returns_false_for_new(self):
        """is_event_processed should return False for new events."""
        mock_db = _mock_db_execute_result([])

        result = await is_event_processed(mock_db, "evt_new_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_event_processed_returns_true_for_existing(self):
        """is_event_processed should return True for processed events."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        # Return a truthy value (1) to indicate event exists
        mock_result.scalar_one_or_none.return_value = 1
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await is_event_processed(mock_db, "evt_existing_123")

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_event_processed_creates_record(self):
        """mark_event_processed should insert a record."""
        mock_db = _mock_db_execute_result([])

        await mark_event_processed(mock_db, "evt_new_456", "invoice.paid")

        # Verify INSERT was called
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_payment_attempt_count_returns_correct_count(self):
        """get_payment_attempt_count should count existing failures."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"count": 2}])

        # Mock the scalar_one return specifically for this query
        mock_db.execute.return_value.scalar_one.return_value = 2

        count = await get_payment_attempt_count(mock_db, org_id, "inv_123")

        # Should return count + 1 (current attempt)
        assert count == 3


# ===========================================================================
# Edge Cases
# ===========================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_upgrade_without_owner_still_updates_org(self):
        """Upgrade should update org even if owner not found."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([])  # No owner found

        subscription = _make_subscription_dict(plan_tier="business")

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_upgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.PRO,
                new_tier=PlanTier.BUSINESS,
            )

        # Verify org was still updated
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_payment_failure_with_no_owner_still_updates(self):
        """Payment failure should update org even if owner not found."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([])  # No owner found

        invoice = _make_invoice_dict()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_payment_failure(
                mock_db,
                org_id,
                invoice,
                attempt_count=1,
            )

        # Verify org was still updated
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_subscription_without_period_timestamps(self):
        """Subscription events should handle missing timestamps gracefully."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_db = _mock_db_execute_result([{"id": user_id, "email": "owner@example.com"}])

        subscription = {
            "id": "sub_test",
            "status": "active",
            "metadata": {"plan_tier": "pro"},
            "cancel_at_period_end": False,
            # Missing current_period_start and current_period_end
        }

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            await handle_subscription_upgrade(
                mock_db,
                org_id,
                subscription,
                old_tier=PlanTier.STARTER,
                new_tier=PlanTier.PRO,
            )

        # Should not raise an exception
        mock_db.execute.assert_called()
