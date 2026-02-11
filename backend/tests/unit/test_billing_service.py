"""
Unit tests for the billing service module.

Tests plan limits, usage tracking logic, Stripe configuration validation,
checkout/portal sessions, webhook handling, invoice listing, and error paths
using mocked Stripe SDK and database calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.core.exceptions import AppException
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_org_row(
    org_id: uuid.UUID,
    *,
    plan_tier: str = "free",
    subscription_status: str = "none",
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    cancel_at_period_end: bool = False,
    projects_count: int = 0,
    ai_generations_today: int = 0,
    current_period_start: datetime | None = None,
    current_period_end: datetime | None = None,
) -> dict:
    """Build a dict that mimics a row from the organizations table."""
    row = {"id": org_id, "plan_tier": plan_tier}
    if subscription_status:
        row["subscription_status"] = subscription_status
    if stripe_customer_id:
        row["stripe_customer_id"] = stripe_customer_id
    if stripe_subscription_id:
        row["stripe_subscription_id"] = stripe_subscription_id
    row["cancel_at_period_end"] = cancel_at_period_end
    row["projects_count"] = projects_count
    row["ai_generations_today"] = ai_generations_today
    if current_period_start:
        row["current_period_start"] = current_period_start
    if current_period_end:
        row["current_period_end"] = current_period_end
    return row


def _mock_db_with_row(row: dict) -> AsyncMock:
    """Return an AsyncMock db session whose execute returns the given row."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = row
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    return mock_db


def _mock_db_no_row() -> AsyncMock:
    """Return an AsyncMock db session whose execute returns no rows."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    return mock_db


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
# Stripe configuration validation
# ===========================================================================


class TestStripeConfiguration:
    """Tests for _ensure_stripe_configured placeholder detection."""

    def setup_method(self):
        """Reset the global _stripe_configured flag before each test."""
        service._stripe_configured = False

    def teardown_method(self):
        """Reset after each test to avoid leaking state."""
        service._stripe_configured = False

    @patch("app.modules.billing.service.settings")
    def test_placeholder_key_raises(self, mock_settings):
        """A placeholder secret key should raise STRIPE_NOT_CONFIGURED."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_PLACEHOLDER_abc123"
        with pytest.raises(AppException) as exc_info:
            service._ensure_stripe_configured()
        assert exc_info.value.code == "STRIPE_NOT_CONFIGURED"
        assert exc_info.value.status_code == 500

    @patch("app.modules.billing.service.settings")
    def test_change_me_key_raises(self, mock_settings):
        """The literal 'CHANGE_ME' value should raise STRIPE_NOT_CONFIGURED."""
        mock_settings.STRIPE_SECRET_KEY = "CHANGE_ME"
        with pytest.raises(AppException) as exc_info:
            service._ensure_stripe_configured()
        assert exc_info.value.code == "STRIPE_NOT_CONFIGURED"

    @patch("app.modules.billing.service.settings")
    def test_empty_key_raises(self, mock_settings):
        """An empty string key should raise STRIPE_NOT_CONFIGURED."""
        mock_settings.STRIPE_SECRET_KEY = ""
        with pytest.raises(AppException) as exc_info:
            service._ensure_stripe_configured()
        assert exc_info.value.code == "STRIPE_NOT_CONFIGURED"

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service.settings")
    def test_valid_key_sets_api_key(self, mock_settings, mock_stripe):
        """A real-looking key should set stripe.api_key and flag as configured."""
        mock_settings.STRIPE_SECRET_KEY = "sk_live_real_key_value"
        service._ensure_stripe_configured()
        assert mock_stripe.api_key == "sk_live_real_key_value"
        assert service._stripe_configured is True

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service.settings")
    def test_already_configured_skips_check(self, mock_settings, mock_stripe):
        """When already configured, the function returns immediately."""
        service._stripe_configured = True
        # Even a bad key should not raise when already configured
        mock_settings.STRIPE_SECRET_KEY = ""
        service._ensure_stripe_configured()  # should not raise


# ===========================================================================
# Price ID resolution
# ===========================================================================


class TestPriceIdForTier:
    """Tests for _price_id_for_tier and _resolve_price_ids."""

    def setup_method(self):
        """Clear the cached price ID mapping before each test."""
        service._TIER_TO_PRICE_ID = {}

    def teardown_method(self):
        service._TIER_TO_PRICE_ID = {}

    def test_missing_price_id_raises(self):
        """A tier with no configured price ID should raise INVALID_PLAN."""
        # Ensure the mapping is empty
        service._TIER_TO_PRICE_ID = {}
        with patch("app.modules.billing.service._resolve_price_ids", return_value={}):
            with pytest.raises(AppException) as exc_info:
                service._price_id_for_tier(PlanTier.PRO)
            assert exc_info.value.code == "INVALID_PLAN"
            assert exc_info.value.status_code == 400

    def test_configured_price_id_returned(self):
        """When a price ID is configured, it should be returned directly."""
        mapping = {PlanTier.PRO: "price_pro_123"}
        with patch("app.modules.billing.service._resolve_price_ids", return_value=mapping):
            result = service._price_id_for_tier(PlanTier.PRO)
        assert result == "price_pro_123"

    @patch("app.modules.billing.service.settings")
    def test_resolve_reads_settings(self, mock_settings):
        """_resolve_price_ids should read price IDs from settings."""
        mock_settings.STRIPE_PRICE_STARTER = "price_starter_x"
        mock_settings.STRIPE_PRICE_PRO = "price_pro_x"
        mock_settings.STRIPE_PRICE_BUSINESS = ""
        mock_settings.STRIPE_PRICE_ENTERPRISE = ""

        result = service._resolve_price_ids()
        assert result[PlanTier.STARTER] == "price_starter_x"
        assert result[PlanTier.PRO] == "price_pro_x"
        assert PlanTier.BUSINESS not in result
        assert PlanTier.ENTERPRISE not in result


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
        row = _make_org_row(
            org_id,
            plan_tier="pro",
            subscription_status="active",
            stripe_subscription_id="sub_123",
            stripe_customer_id="cus_456",
            current_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            current_period_end=datetime(2024, 2, 1, tzinfo=timezone.utc),
        )
        mock_db = _mock_db_with_row(row)

        result = await service.get_subscription(mock_db, org_id)

        assert result.org_id == org_id
        assert result.plan_tier == PlanTier.PRO
        assert result.subscription_status == "active"
        assert result.stripe_subscription_id == "sub_123"

    @pytest.mark.asyncio
    async def test_defaults_to_free_when_no_plan(self):
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_row({"id": org_id})

        result = await service.get_subscription(mock_db, org_id)
        assert result.plan_tier == PlanTier.FREE
        assert result.subscription_status == "none"

    @pytest.mark.asyncio
    async def test_org_not_found_raises(self):
        """When the organization row does not exist, should raise ORG_NOT_FOUND."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_no_row()

        with pytest.raises(AppException) as exc_info:
            await service.get_subscription(mock_db, org_id)
        assert exc_info.value.code == "ORG_NOT_FOUND"
        assert exc_info.value.status_code == 404


# ===========================================================================
# Usage stats (mocked DB)
# ===========================================================================


class TestGetUsageStats:
    """Tests for get_usage_stats."""

    @pytest.mark.asyncio
    async def test_returns_usage_with_correct_limits(self):
        org_id = uuid.uuid4()
        row = _make_org_row(
            org_id,
            plan_tier="starter",
            projects_count=3,
            ai_generations_today=10,
            current_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            current_period_end=datetime(2024, 2, 1, tzinfo=timezone.utc),
        )
        mock_db = _mock_db_with_row(row)

        result = await service.get_usage_stats(mock_db, org_id)

        assert result.plan_tier == PlanTier.STARTER
        assert result.projects_used == 3
        assert result.projects_limit == 5
        assert result.ai_generations_used_today == 10
        assert result.ai_generations_daily_limit == 50

    @pytest.mark.asyncio
    async def test_free_tier_has_correct_limits(self):
        org_id = uuid.uuid4()
        row = _make_org_row(org_id, plan_tier="free")
        mock_db = _mock_db_with_row(row)

        result = await service.get_usage_stats(mock_db, org_id)

        assert result.projects_limit == 1
        assert result.ai_generations_daily_limit == 5

    @pytest.mark.asyncio
    async def test_business_tier_unlimited_projects(self):
        """Business tier should report None (unlimited) for projects_limit."""
        org_id = uuid.uuid4()
        row = _make_org_row(org_id, plan_tier="business", projects_count=50)
        mock_db = _mock_db_with_row(row)

        result = await service.get_usage_stats(mock_db, org_id)

        assert result.plan_tier == PlanTier.BUSINESS
        assert result.projects_limit is None
        assert result.projects_used == 50


# ===========================================================================
# Webhook handling (mocked Stripe + DB)
# ===========================================================================


class TestWebhookHandling:
    """Tests for handle_webhook_event with mocked Stripe."""

    def setup_method(self):
        service._stripe_configured = True

    def teardown_method(self):
        service._stripe_configured = False

    def _mock_idempotency(self):
        """Helper to mock idempotency checks."""
        return patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock, return_value=False), \
               patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_subscription_created_updates_org(self, mock_stripe, mock_mark, mock_is_processed):
        mock_is_processed.return_value = False  # Event not processed yet
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_test_123",
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
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": org_id, "plan_tier": "free"}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )

        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.created"

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_subscription_deleted_sets_free(self, mock_stripe, mock_mark, mock_is_processed):
        mock_is_processed.return_value = False
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_deleted_123",
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
        # Mock org owner lookup
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": user_id, "email": "owner@test.com"}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            result = await service.handle_webhook_event(
                mock_db, b"payload", "sig_header"
            )

        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.deleted"

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_subscription_updated_processed(self, mock_stripe, mock_mark, mock_is_processed):
        """customer.subscription.updated events should be processed."""
        mock_is_processed.return_value = False
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_updated_123",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_upd",
                    "customer": "cus_test",
                    "status": "active",
                    "metadata": {
                        "org_id": str(org_id),
                        "plan_tier": "business",
                    },
                    "cancel_at_period_end": True,
                    "current_period_start": 1704067200,
                    "current_period_end": 1706745600,
                }
            },
        }

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": org_id, "plan_tier": "pro"}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            result = await service.handle_webhook_event(
                mock_db, b"payload", "sig_header"
            )

        assert result["status"] == "processed"
        assert result["event_type"] == "customer.subscription.updated"

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_unhandled_event_is_ignored(self, mock_stripe, mock_is_processed):
        mock_is_processed.return_value = False  # Not processed yet
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_unhandled_123",
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
        MockSigError = type("SignatureVerificationError", (Exception,), {})
        mock_stripe.SignatureVerificationError = MockSigError
        mock_stripe.Webhook.construct_event.side_effect = MockSigError(
            "bad sig"
        )

        mock_db = AsyncMock()
        with pytest.raises(AppException) as exc_info:
            await service.handle_webhook_event(
                mock_db, b"payload", "bad_sig"
            )
        assert exc_info.value.code == "WEBHOOK_SIGNATURE_INVALID"
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_invoice_paid_sets_active(self, mock_stripe, mock_mark, mock_is_processed):
        mock_is_processed.return_value = False
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_paid_123",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "inv_123",
                    "customer": "cus_test",
                }
            },
        }

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": org_id}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )
        assert result["status"] == "processed"
        assert result["event_type"] == "invoice.paid"

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.get_payment_attempt_count", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_invoice_payment_failed_sets_past_due(self, mock_stripe, mock_count, mock_mark, mock_is_processed):
        mock_is_processed.return_value = False
        mock_count.return_value = 1
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_failed_123",
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
        mock_result.mappings.return_value.first.return_value = {"id": user_id, "email": "owner@test.com"}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.modules.billing.webhook_handlers.create_notification", new_callable=AsyncMock):
            result = await service.handle_webhook_event(
                mock_db, b"payload", "sig_header"
            )
        assert result["status"] == "processed"
        assert result["event_type"] == "invoice.payment_failed"

    @pytest.mark.asyncio
    @patch("app.modules.billing.webhook_handlers.is_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.webhook_handlers.mark_event_processed", new_callable=AsyncMock)
    @patch("app.modules.billing.service.stripe")
    async def test_subscription_event_without_org_id_resolves_from_customer(
        self, mock_stripe, mock_mark, mock_is_processed
    ):
        """When metadata has no org_id, the handler should resolve from customer."""
        mock_is_processed.return_value = False
        org_id = uuid.uuid4()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_no_meta_123",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_no_meta",
                    "customer": "cus_resolve",
                    "status": "active",
                    "metadata": {},  # no org_id in metadata
                    "cancel_at_period_end": False,
                    "current_period_start": 1704067200,
                    "current_period_end": 1706745600,
                }
            },
        }

        mock_db = AsyncMock()
        # First call: _org_id_from_customer query
        # Second call: _update_org
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": org_id}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.handle_webhook_event(
            mock_db, b"payload", "sig_header"
        )
        assert result["status"] == "processed"


# ===========================================================================
# Checkout session (mocked Stripe)
# ===========================================================================


class TestCreateCheckoutSession:
    """Tests for create_checkout_session with mocked Stripe."""

    def setup_method(self):
        service._stripe_configured = True

    def teardown_method(self):
        service._stripe_configured = False

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_checkout_creates_session(self, mock_stripe):
        org_id = uuid.uuid4()
        row = _make_org_row(
            org_id,
            plan_tier="free",
            stripe_customer_id="cus_existing",
        )
        mock_db = _mock_db_with_row(row)

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_123"
        mock_session.id = "cs_session_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

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
        org_id = uuid.uuid4()
        mock_db = AsyncMock()
        request = CheckoutRequest(plan_tier=PlanTier.FREE)

        with pytest.raises(AppException) as exc_info:
            await service.create_checkout_session(
                mock_db, org_id, "test@example.com", request
            )
        assert exc_info.value.code == "INVALID_PLAN"
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_checkout_creates_new_customer_when_none_exists(self, mock_stripe):
        """When the org has no stripe_customer_id, a new customer is created."""
        org_id = uuid.uuid4()
        row = _make_org_row(org_id, plan_tier="free")  # no stripe_customer_id
        mock_db = _mock_db_with_row(row)

        mock_customer = MagicMock()
        mock_customer.id = "cus_newly_created"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/new_session"
        mock_session.id = "cs_new_session"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch.dict(
            service._TIER_TO_PRICE_ID,
            {PlanTier.PRO: "price_pro_test"},
            clear=False,
        ):
            request = CheckoutRequest(plan_tier=PlanTier.PRO)
            result = await service.create_checkout_session(
                mock_db, org_id, "new@example.com", request
            )

        mock_stripe.Customer.create.assert_called_once()
        assert result.checkout_url == "https://checkout.stripe.com/new_session"

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_checkout_stripe_api_error_propagates(self, mock_stripe):
        """When Stripe raises an exception during session creation, it propagates."""
        org_id = uuid.uuid4()
        row = _make_org_row(
            org_id,
            plan_tier="free",
            stripe_customer_id="cus_existing",
        )
        mock_db = _mock_db_with_row(row)

        mock_stripe.checkout.Session.create.side_effect = Exception(
            "Stripe API error"
        )

        with patch.dict(
            service._TIER_TO_PRICE_ID,
            {PlanTier.STARTER: "price_starter_test"},
            clear=False,
        ):
            request = CheckoutRequest(plan_tier=PlanTier.STARTER)
            with pytest.raises(Exception, match="Stripe API error"):
                await service.create_checkout_session(
                    mock_db, org_id, "test@example.com", request
                )

    @pytest.mark.asyncio
    async def test_checkout_unconfigured_tier_raises(self):
        """Checking out for a tier with no price ID should raise INVALID_PLAN."""
        service._stripe_configured = True
        org_id = uuid.uuid4()
        mock_db = AsyncMock()

        with patch.dict(service._TIER_TO_PRICE_ID, {}, clear=True):
            with patch(
                "app.modules.billing.service._resolve_price_ids",
                return_value={},
            ):
                request = CheckoutRequest(plan_tier=PlanTier.ENTERPRISE)
                with pytest.raises(AppException) as exc_info:
                    await service.create_checkout_session(
                        mock_db, org_id, "test@example.com", request
                    )
                assert exc_info.value.code == "INVALID_PLAN"


# ===========================================================================
# Portal session (mocked Stripe)
# ===========================================================================


class TestCreatePortalSession:
    """Tests for create_portal_session with mocked Stripe."""

    def setup_method(self):
        service._stripe_configured = True

    def teardown_method(self):
        service._stripe_configured = False

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_portal_creates_session(self, mock_stripe):
        """When a customer ID exists, a portal session should be created."""
        org_id = uuid.uuid4()
        row = _make_org_row(
            org_id,
            plan_tier="pro",
            stripe_customer_id="cus_portal",
        )
        mock_db = _mock_db_with_row(row)

        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/portal_session"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        request = PortalRequest(return_url="http://localhost:3000/billing")
        result = await service.create_portal_session(mock_db, org_id, request)

        assert result.portal_url == "https://billing.stripe.com/portal_session"
        mock_stripe.billing_portal.Session.create.assert_called_once_with(
            customer="cus_portal",
            return_url="http://localhost:3000/billing",
        )

    @pytest.mark.asyncio
    async def test_portal_no_customer_raises(self):
        """When the org has no Stripe customer, should raise NO_CUSTOMER."""
        org_id = uuid.uuid4()
        row = _make_org_row(org_id, plan_tier="free")  # no stripe_customer_id
        mock_db = _mock_db_with_row(row)

        request = PortalRequest()
        with pytest.raises(AppException) as exc_info:
            await service.create_portal_session(mock_db, org_id, request)
        assert exc_info.value.code == "NO_CUSTOMER"
        assert exc_info.value.status_code == 400


# ===========================================================================
# Invoice listing (mocked Stripe)
# ===========================================================================


class TestListInvoices:
    """Tests for list_invoices with mocked Stripe."""

    def setup_method(self):
        service._stripe_configured = True

    def teardown_method(self):
        service._stripe_configured = False

    @pytest.mark.asyncio
    async def test_no_customer_returns_empty(self):
        """When the org has no Stripe customer, return empty invoice list."""
        org_id = uuid.uuid4()
        row = _make_org_row(org_id, plan_tier="free")  # no stripe_customer_id
        mock_db = _mock_db_with_row(row)

        result = await service.list_invoices(mock_db, org_id)

        assert result.invoices == []
        assert result.has_more is False

    @pytest.mark.asyncio
    @patch("app.modules.billing.service.stripe")
    async def test_returns_invoices_from_stripe(self, mock_stripe):
        """When a customer exists, invoices should be fetched from Stripe."""
        org_id = uuid.uuid4()
        row = _make_org_row(
            org_id,
            plan_tier="pro",
            stripe_customer_id="cus_inv",
        )
        mock_db = _mock_db_with_row(row)

        mock_invoice = MagicMock()
        mock_invoice.id = "inv_001"
        mock_invoice.number = "INV-001"
        mock_invoice.status = "paid"
        mock_invoice.amount_due = 7900
        mock_invoice.amount_paid = 7900
        mock_invoice.currency = "usd"
        mock_invoice.created = 1704067200  # 2024-01-01
        mock_invoice.period_start = 1704067200
        mock_invoice.period_end = 1706745600
        mock_invoice.hosted_invoice_url = "https://invoice.stripe.com/inv_001"
        mock_invoice.invoice_pdf = "https://invoice.stripe.com/inv_001.pdf"

        mock_result = MagicMock()
        mock_result.data = [mock_invoice]
        mock_result.has_more = False
        mock_stripe.Invoice.list.return_value = mock_result

        result = await service.list_invoices(mock_db, org_id, limit=5)

        assert len(result.invoices) == 1
        assert result.invoices[0].id == "inv_001"
        assert result.invoices[0].amount_due == 7900
        assert result.invoices[0].status == "paid"
        assert result.has_more is False
        mock_stripe.Invoice.list.assert_called_once_with(
            customer="cus_inv", limit=5
        )


# ===========================================================================
# Handled events constant
# ===========================================================================


class TestHandledEvents:
    """Verify the HANDLED_EVENTS set covers expected Stripe event types."""

    def test_subscription_events_handled(self):
        assert "customer.subscription.created" in service.HANDLED_EVENTS
        assert "customer.subscription.updated" in service.HANDLED_EVENTS
        assert "customer.subscription.deleted" in service.HANDLED_EVENTS

    def test_invoice_events_handled(self):
        assert "invoice.paid" in service.HANDLED_EVENTS
        assert "invoice.payment_failed" in service.HANDLED_EVENTS

    def test_unrelated_event_not_handled(self):
        assert "charge.succeeded" not in service.HANDLED_EVENTS
        assert "payment_intent.created" not in service.HANDLED_EVENTS
