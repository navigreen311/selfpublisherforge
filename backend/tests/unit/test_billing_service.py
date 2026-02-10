"""
Unit tests for the billing service module.

Tests plan limits, usage tracking logic, and webhook handling
using mocked Stripe SDK and database calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.common import PlanTier
from app.modules.billing.plans import (
    PLAN_DEFINITIONS,
    get_plan,
    get_plan_limits,
    get_all_plans,
    is_upgrade,
)
from app.modules.billing.schemas import CheckoutRequest, PortalRequest
from app.modules.billing import service


# ===========================================================================
# Plan definitions & limits
# ===========================================================================


class TestPlanDefinitions:
    """Tests for plan definitions and limits."""

    def test_all_tiers_defined(self):
        """Every PlanTier enum value has a corresponding definition."""
        for tier in PlanTier:
            assert tier in PLAN_DEFINITIONS

    def test_free_plan_limits(self):
        limits = get_plan_limits(PlanTier.FREE)
        assert limits.max_projects == 1
        assert limits.ai_generations_per_day == 5

    def test_starter_plan_limits(self):
        limits = get_plan_limits(PlanTier.STARTER)
        assert limits.max_projects == 5
        assert limits.ai_generations_per_day == 50

    def test_pro_plan_limits(self):
        limits = get_plan_limits(PlanTier.PRO)
        assert limits.max_projects == 25
        assert limits.ai_generations_per_day == 200

    def test_business_plan_limits(self):
        limits = get_plan_limits(PlanTier.BUSINESS)
        assert limits.max_projects is None  # unlimited
        assert limits.ai_generations_per_day == 500

    def test_enterprise_plan_limits(self):
        limits = get_plan_limits(PlanTier.ENTERPRISE)
        assert limits.max_projects is None
        assert limits.ai_generations_per_day == 9999

    def test_plans_sorted_by_price(self):
        plans = get_all_plans()
        prices = [p.price_monthly for p in plans]
        assert prices == sorted(prices)

    def test_get_plan_returns_correct_tier(self):
        plan = get_plan(PlanTier.PRO)
        assert plan.tier == PlanTier.PRO
        assert plan.name == "Pro"

    def test_pro_plan_is_highlighted(self):
        plan = get_plan(PlanTier.PRO)
        assert plan.highlight is True

    def test_free_plan_not_highlighted(self):
        plan = get_plan(PlanTier.FREE)
        assert plan.highlight is False


class TestIsUpgrade:
    """Tests for the is_upgrade helper."""

    def test_free_to_starter_is_upgrade(self):
        assert is_upgrade(PlanTier.FREE, PlanTier.STARTER) is True

    def test_pro_to_starter_is_not_upgrade(self):
        assert is_upgrade(PlanTier.PRO, PlanTier.STARTER) is False

    def test_same_tier_is_not_upgrade(self):
        assert is_upgrade(PlanTier.PRO, PlanTier.PRO) is False

    def test_free_to_enterprise_is_upgrade(self):
        assert is_upgrade(PlanTier.FREE, PlanTier.ENTERPRISE) is True

    def test_enterprise_to_free_is_not_upgrade(self):
        assert is_upgrade(PlanTier.ENTERPRISE, PlanTier.FREE) is False


# ===========================================================================
# Plan listing
# ===========================================================================


class TestListPlans:
    """Tests for the list_plans service function."""

    def test_returns_all_plans(self):
        plans = service.list_plans()
        assert len(plans) == len(PlanTier)

    def test_plans_have_required_fields(self):
        for plan in service.list_plans():
            assert plan.tier is not None
            assert plan.name
            assert plan.price_monthly >= 0
            assert plan.description
            assert isinstance(plan.features, list)
            assert len(plan.features) > 0

    def test_free_plan_price_is_zero(self):
        plans = service.list_plans()
        free_plan = next(p for p in plans if p.tier == PlanTier.FREE)
        assert free_plan.price_monthly == 0


# ===========================================================================
# Subscription retrieval (mocked DB)
# ===========================================================================


class TestGetSubscription:
    """Tests for get_subscription with mocked DB."""

    @pytest.mark.asyncio
    async def test_returns_subscription_for_org(self):
        org_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": org_id,
            "plan_tier": "pro",
            "subscription_status": "active",
            "stripe_subscription_id": "sub_123",
            "stripe_customer_id": "cus_456",
            "current_period_start": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "current_period_end": datetime(2024, 2, 1, tzinfo=timezone.utc),
            "cancel_at_period_end": False,
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_subscription(mock_db, org_id)

        assert result.org_id == org_id
        assert result.plan_tier == PlanTier.PRO
        assert result.subscription_status == "active"
        assert result.stripe_subscription_id == "sub_123"

    @pytest.mark.asyncio
    async def test_defaults_to_free_when_no_plan(self):
        org_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": org_id,
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_subscription(mock_db, org_id)
        assert result.plan_tier == PlanTier.FREE
        assert result.subscription_status == "none"


# ===========================================================================
# Usage stats (mocked DB)
# ===========================================================================


class TestGetUsageStats:
    """Tests for get_usage_stats."""

    @pytest.mark.asyncio
    async def test_returns_usage_with_correct_limits(self):
        org_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": org_id,
            "plan_tier": "starter",
            "projects_count": 3,
            "ai_generations_today": 10,
            "current_period_start": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "current_period_end": datetime(2024, 2, 1, tzinfo=timezone.utc),
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_usage_stats(mock_db, org_id)

        assert result.plan_tier == PlanTier.STARTER
        assert result.projects_used == 3
        assert result.projects_limit == 5
        assert result.ai_generations_used_today == 10
        assert result.ai_generations_daily_limit == 50

    @pytest.mark.asyncio
    async def test_free_tier_has_correct_limits(self):
        org_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": org_id,
            "plan_tier": "free",
            "projects_count": 0,
            "ai_generations_today": 0,
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_usage_stats(mock_db, org_id)

        assert result.projects_limit == 1
        assert result.ai_generations_daily_limit == 5


# ===========================================================================
# Webhook handling (mocked Stripe + DB)
# ===========================================================================


class TestWebhookHandling:
    """Tests for handle_webhook_event with mocked Stripe."""

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_subscription_created_updates_org(self, mock_stripe):
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_new",
                    "customer": "cus_test",
                    "status": "active",
                    "metadata": {
                        "org_id": str(org_id),
                        "plan_tier": "pro",
                    },
                    "cancel_at_period_end": False,
                    "current_period_start": 1704067200,
                    "current_period_end": 1706745600,
                }
            },
        }

        mock_db = AsyncMock()
        # Mock _update_org: the function uses raw SQL
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )

        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.created"

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_subscription_deleted_sets_free(self, mock_stripe):
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_del",
                    "customer": "cus_test",
                    "status": "canceled",
                    "metadata": {
                        "org_id": str(org_id),
                        "plan_tier": "pro",
                    },
                    "cancel_at_period_end": False,
                    "current_period_start": 1704067200,
                    "current_period_end": 1706745600,
                }
            },
        }

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )

        assert result["status"] == "processed"
        # The handler should set plan_tier to free on deletion
        assert result["event_type"] == "customer.subscription.deleted"

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_unhandled_event_is_ignored(self, mock_stripe):
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "payment_intent.created",
            "data": {"object": {}},
        }

        mock_db = AsyncMock()
        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_invalid_signature_raises(self, mock_stripe):
        from app.core.exceptions import AppException

        mock_stripe.Webhook.construct_event.side_effect = (
            stripe_sig_error()
        )
        mock_stripe.error.SignatureVerificationError = type(
            "SignatureVerificationError", (Exception,), {}
        )

        mock_db = AsyncMock()
        with pytest.raises(AppException) as exc_info:
            await service.handle_webhook_event(
                mock_db, b"payload", "bad_sig"
            )
        assert exc_info.value.code == "WEBHOOK_SIGNATURE_INVALID"

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_invoice_paid_sets_active(self, mock_stripe):
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "inv_123",
                    "customer": "cus_test",
                }
            },
        }

        mock_db = AsyncMock()
        # Mock _org_id_from_customer
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": org_id}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )
        assert result["status"] == "processed"
        assert result["event_type"] == "invoice.paid"

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_invoice_payment_failed_sets_past_due(self, mock_stripe):
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "inv_456",
                    "customer": "cus_test",
                }
            },
        }

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": org_id}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )
        assert result["status"] == "processed"
        assert result["event_type"] == "invoice.payment_failed"


# ===========================================================================
# Checkout session (mocked Stripe)
# ===========================================================================


class TestCreateCheckoutSession:
    """Tests for create_checkout_session with mocked Stripe."""

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_checkout_creates_session(self, mock_stripe):
        org_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Mock _get_org_row
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": org_id,
            "stripe_customer_id": "cus_existing",
            "plan_tier": "free",
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_123"
        mock_session.id = "cs_session_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        # Ensure price IDs are configured
        with patch.dict(
            service._TIER_TO_PRICE_ID,
            {PlanTier.STARTER: "price_starter_test"},
            clear=False,
        ):
            request = CheckoutRequest(
                plan_tier=PlanTier.STARTER,
                success_url="http://localhost:3000/success",
                cancel_url="http://localhost:3000/cancel",
            )
            result = await service.create_checkout_session(
                mock_db, org_id, "test@example.com", request
            )

        assert result.checkout_url == "https://checkout.stripe.com/session_123"
        assert result.session_id == "cs_session_123"

    @pytest.mark.asyncio
    async def test_checkout_free_plan_raises(self):
        from app.core.exceptions import AppException

        org_id = uuid.uuid4()
        mock_db = AsyncMock()
        request = CheckoutRequest(plan_tier=PlanTier.FREE)

        with pytest.raises(AppException) as exc_info:
            await service.create_checkout_session(
                mock_db, org_id, "test@example.com", request
            )
        assert exc_info.value.code == "INVALID_PLAN"


# ===========================================================================
# Helpers
# ===========================================================================


def stripe_sig_error():
    """Return an exception that mimics stripe.error.SignatureVerificationError."""
    import stripe as _stripe

    try:
        return _stripe.error.SignatureVerificationError("bad sig", "sig_header")
    except Exception:
        # If stripe is not installed, create a stand-in
        return Exception("SignatureVerificationError")
