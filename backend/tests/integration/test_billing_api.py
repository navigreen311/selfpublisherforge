"""
Integration tests for billing API endpoints.

Uses a mocked Stripe SDK and mocked database to test the FastAPI
router endpoints end-to-end via the test client.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user, require_role
from app.core.error_handler import register_error_handlers
from app.database import get_db
from app.modules.billing.router import router
from app.schemas.common import PlanTier

# ===========================================================================
# Fixtures
# ===========================================================================

TEST_ORG_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()

TEST_USER = {
    "user_id": TEST_USER_ID,
    "org_id": TEST_ORG_ID,
    "role": "owner",
    "email": "owner@example.com",
}

TEST_ORG_ROW = {
    "id": TEST_ORG_ID,
    "plan_tier": "pro",
    "subscription_status": "active",
    "stripe_subscription_id": "sub_test_123",
    "stripe_customer_id": "cus_test_456",
    "current_period_start": datetime(2024, 1, 1, tzinfo=UTC),
    "current_period_end": datetime(2024, 2, 1, tzinfo=UTC),
    "cancel_at_period_end": False,
    "projects_count": 10,
    "ai_generations_today": 42,
}


def _make_mock_db():
    """Create a mock async DB session that returns TEST_ORG_ROW."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = TEST_ORG_ROW
    # An unset MagicMock answers scalar_one_or_none() with another MagicMock,
    # which `is not None` — so `is_event_processed` reported every webhook as
    # already seen and the handler returned "duplicate" for events it had
    # never processed. The default for a stand-in database is no rows.
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    return mock_db


def _create_test_app() -> FastAPI:
    """Build a minimal FastAPI app with billing router for testing."""
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1/billing", tags=["billing"])

    # Override dependencies
    mock_db = _make_mock_db()

    async def override_get_db():
        yield mock_db

    async def override_get_current_user():
        return TEST_USER

    def override_require_role(*roles):
        async def checker():
            return TEST_USER

        return checker

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_role] = override_require_role

    return app


@pytest.fixture
def client():
    """Return a TestClient for the billing test app."""
    app = _create_test_app()
    with patch(
        "app.modules.billing.service._ensure_stripe_configured",
        return_value=None,
    ):
        yield TestClient(app)


# ===========================================================================
# GET /plans
# ===========================================================================


class TestListPlansEndpoint:
    """Tests for GET /api/v1/billing/plans."""

    def test_list_plans_returns_200(self, client):
        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

    def test_list_plans_returns_all_tiers(self, client):
        response = client.get("/api/v1/billing/plans")
        data = response.json()
        tiers = {p["tier"] for p in data}
        assert "free" in tiers
        assert "starter" in tiers
        assert "pro" in tiers
        assert "business" in tiers
        assert "enterprise" in tiers

    def test_plan_has_required_fields(self, client):
        response = client.get("/api/v1/billing/plans")
        data = response.json()
        for plan in data:
            assert "tier" in plan
            assert "name" in plan
            assert "price_monthly" in plan
            assert "description" in plan
            assert "features" in plan
            assert "max_projects" in plan
            assert "ai_generations_per_day" in plan

    def test_free_plan_has_zero_price(self, client):
        response = client.get("/api/v1/billing/plans")
        data = response.json()
        free = next(p for p in data if p["tier"] == "free")
        assert free["price_monthly"] == 0


# ===========================================================================
# GET /subscription
# ===========================================================================


class TestGetSubscriptionEndpoint:
    """Tests for GET /api/v1/billing/subscription."""

    def test_get_subscription_returns_200(self, client):
        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200

    def test_subscription_has_plan_tier(self, client):
        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "active"

    def test_subscription_has_stripe_ids(self, client):
        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["stripe_subscription_id"] == "sub_test_123"
        assert data["stripe_customer_id"] == "cus_test_456"


# ===========================================================================
# POST /subscribe
# ===========================================================================


class TestSubscribeEndpoint:
    """Tests for POST /api/v1/billing/subscribe."""

    @patch("app.modules.billing.service.stripe")
    def test_subscribe_creates_checkout_session(self, mock_stripe, client):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch.dict(
            "app.modules.billing.service._TIER_TO_PRICE_ID",
            {PlanTier.STARTER: "price_starter"},
            clear=False,
        ):
            response = client.post(
                "/api/v1/billing/subscribe",
                json={
                    "plan_tier": "starter",
                    "success_url": "http://localhost:3000/success",
                    "cancel_url": "http://localhost:3000/cancel",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["checkout_url"] == "https://checkout.stripe.com/test"
        assert data["session_id"] == "cs_test"

    def test_subscribe_free_plan_returns_400(self, client):
        response = client.post(
            "/api/v1/billing/subscribe",
            json={"plan_tier": "free"},
        )
        # Should be 400 because you cannot checkout for the Free plan
        assert response.status_code in (400, 422)


# ===========================================================================
# POST /portal
# ===========================================================================


class TestPortalEndpoint:
    """Tests for POST /api/v1/billing/portal."""

    @patch("app.modules.billing.service.stripe")
    def test_portal_creates_session(self, mock_stripe, client):
        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/portal"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        response = client.post(
            "/api/v1/billing/portal",
            json={"return_url": "http://localhost:3000/settings/billing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["portal_url"] == "https://billing.stripe.com/portal"


# ===========================================================================
# GET /usage
# ===========================================================================


class TestUsageEndpoint:
    """Tests for GET /api/v1/billing/usage."""

    def test_get_usage_returns_200(self, client):
        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

    def test_usage_has_correct_fields(self, client):
        response = client.get("/api/v1/billing/usage")
        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["projects_used"] == 10
        assert data["projects_limit"] == 25  # Pro limit
        assert data["ai_generations_used_today"] == 42
        assert data["ai_generations_daily_limit"] == 200  # Pro limit


# ===========================================================================
# GET /invoices
# ===========================================================================


class TestInvoicesEndpoint:
    """Tests for GET /api/v1/billing/invoices."""

    @patch("app.modules.billing.service.stripe")
    def test_list_invoices_returns_200(self, mock_stripe, client):
        mock_result = MagicMock()
        mock_result.data = []
        mock_result.has_more = False
        mock_stripe.Invoice.list.return_value = mock_result

        response = client.get("/api/v1/billing/invoices")
        assert response.status_code == 200
        data = response.json()
        assert data["invoices"] == []
        assert data["has_more"] is False

    @patch("app.modules.billing.service.stripe")
    def test_list_invoices_with_data(self, mock_stripe, client):
        mock_inv = MagicMock()
        mock_inv.id = "inv_001"
        mock_inv.number = "INV-001"
        mock_inv.status = "paid"
        mock_inv.amount_due = 7900
        mock_inv.amount_paid = 7900
        mock_inv.currency = "usd"
        mock_inv.created = 1704067200
        mock_inv.period_start = 1704067200
        mock_inv.period_end = 1706745600
        mock_inv.hosted_invoice_url = "https://invoice.stripe.com/i/001"
        mock_inv.invoice_pdf = "https://invoice.stripe.com/i/001/pdf"

        mock_result = MagicMock()
        mock_result.data = [mock_inv]
        mock_result.has_more = False
        mock_stripe.Invoice.list.return_value = mock_result

        response = client.get("/api/v1/billing/invoices")
        assert response.status_code == 200
        data = response.json()
        assert len(data["invoices"]) == 1
        assert data["invoices"][0]["id"] == "inv_001"
        assert data["invoices"][0]["amount_due"] == 7900


# ===========================================================================
# POST /webhook
# ===========================================================================


class TestWebhookEndpoint:
    """Tests for POST /api/v1/billing/webhook."""

    @patch("app.modules.billing.service.stripe")
    def test_webhook_processes_event(self, mock_stripe, client):
        mock_stripe.Webhook.construct_event.return_value = {
            # Real Stripe events carry a top-level evt_ id, and the handler
            # dedupes on it — billing_events has a unique constraint. The mock
            # omitted it entirely, so the webhook raised KeyError; a fixed
            # literal then collided with whatever earlier test had recorded it,
            # and the handler correctly answered "duplicate".
            "id": f"evt_test_{uuid.uuid4()}",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_wh",
                    "customer": "cus_wh",
                    "status": "active",
                    "metadata": {
                        "org_id": str(TEST_ORG_ID),
                        "plan_tier": "pro",
                    },
                    "cancel_at_period_end": False,
                    "current_period_start": 1704067200,
                    "current_period_end": 1706745600,
                }
            },
        }

        response = client.post(
            "/api/v1/billing/webhook",
            content=b'{"test": true}',
            headers={"stripe-signature": "test_sig"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
