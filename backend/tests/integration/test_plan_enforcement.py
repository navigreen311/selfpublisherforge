"""
Integration tests for billing plan tier enforcement.

Tests that each plan tier correctly grants/restricts access to features
based on the subscription level.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.billing.router import router
from app.core.error_handler import register_error_handlers
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.schemas.common import PlanTier


# ===========================================================================
# Test Fixtures
# ===========================================================================

TEST_ORG_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()


def create_test_user(role: str = "owner", plan_tier: str = "free"):
    """Create a test user with specified role and plan tier."""
    return {
        "user_id": TEST_USER_ID,
        "org_id": TEST_ORG_ID,
        "role": role,
        "email": f"{role}@example.com",
        "plan_tier": plan_tier,
    }


class MockDB:
    """Mock database that tracks org state."""

    def __init__(self, plan_tier: str = "free", subscription_status: str = "none"):
        self.org_data = {
            "id": TEST_ORG_ID,
            "plan_tier": plan_tier,
            "subscription_status": subscription_status,
            "stripe_subscription_id": f"sub_{plan_tier}_123" if plan_tier != "free" else None,
            "stripe_customer_id": f"cus_{plan_tier}_456" if plan_tier != "free" else None,
            "current_period_start": datetime.now(timezone.utc) if plan_tier != "free" else None,
            "current_period_end": datetime.now(timezone.utc) + timedelta(days=30) if plan_tier != "free" else None,
            "cancel_at_period_end": False,
            "projects_count": 0,
            "ai_generations_today": 0,
        }

    async def execute(self, query, params=None):
        """Mock execute method."""
        result = MagicMock()
        result.mappings.return_value.first.return_value = self.org_data.copy()
        return result

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


def _create_test_app(mock_db: MockDB, test_user: dict) -> FastAPI:
    """Build a minimal FastAPI app with billing router for testing."""
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1/billing", tags=["billing"])

    async def override_get_db():
        yield mock_db

    async def override_get_current_user():
        return test_user

    def override_require_role(*roles):
        async def checker():
            return test_user
        return checker

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_role] = override_require_role

    return app


def create_client(plan_tier: str = "free", subscription_status: str = "none"):
    """Create a test client for a specific plan tier."""
    mock_db = MockDB(plan_tier=plan_tier, subscription_status=subscription_status)
    test_user = create_test_user(plan_tier=plan_tier)
    app = _create_test_app(mock_db, test_user)

    with patch(
        "app.modules.billing.service._ensure_stripe_configured",
        return_value=None,
    ):
        return TestClient(app)


# ===========================================================================
# TestPlanEnforcement
# ===========================================================================


class TestPlanEnforcement:
    """Test access control based on plan tiers."""

    def test_free_user_has_basic_limits(self):
        """Free users should have access to basic features only."""
        client = create_client(plan_tier="free")

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "free"
        assert data["projects_limit"] == 1
        assert data["ai_generations_daily_limit"] == 5

    def test_free_user_can_view_plans(self):
        """Free users can view available plans to upgrade."""
        client = create_client(plan_tier="free")

        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()
        assert len(plans) == 5
        tiers = {p["tier"] for p in plans}
        assert "free" in tiers
        assert "starter" in tiers
        assert "pro" in tiers

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service._ensure_stripe_configured")
    def test_free_user_can_upgrade_to_starter(self, mock_ensure, mock_stripe):
        """Free users should be able to start a subscription."""
        client = create_client(plan_tier="free")

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session"
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

    def test_starter_has_increased_limits(self):
        """Starter users should have access to increased limits."""
        client = create_client(plan_tier="starter", subscription_status="active")

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "starter"
        assert data["projects_limit"] == 5
        assert data["ai_generations_daily_limit"] == 50

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service._ensure_stripe_configured")
    def test_starter_can_access_billing_portal(self, mock_ensure, mock_stripe):
        """Starter users can access billing portal to manage subscription."""
        client = create_client(plan_tier="starter", subscription_status="active")

        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/portal"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        response = client.post(
            "/api/v1/billing/portal",
            json={"return_url": "http://localhost:3000/settings/billing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "portal_url" in data

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service._ensure_stripe_configured")
    def test_starter_can_upgrade_to_pro(self, mock_ensure, mock_stripe):
        """Starter users should be able to upgrade to Pro."""
        client = create_client(plan_tier="starter", subscription_status="active")

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_pro"
        mock_session.id = "cs_pro"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch.dict(
            "app.modules.billing.service._TIER_TO_PRICE_ID",
            {PlanTier.PRO: "price_pro"},
            clear=False,
        ):
            response = client.post(
                "/api/v1/billing/subscribe",
                json={
                    "plan_tier": "pro",
                    "success_url": "http://localhost:3000/success",
                    "cancel_url": "http://localhost:3000/cancel",
                },
            )

        assert response.status_code == 200

    def test_pro_has_advanced_limits(self):
        """Pro users should have access to advanced features and limits."""
        client = create_client(plan_tier="pro", subscription_status="active")

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["projects_limit"] == 25
        assert data["ai_generations_daily_limit"] == 200

    def test_pro_plan_features_listed(self):
        """Pro plan should include advanced features in plan listing."""
        client = create_client(plan_tier="pro")

        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()
        pro_plan = next(p for p in plans if p["tier"] == "pro")

        assert pro_plan["price_monthly"] == 7900
        assert "Cover design AI" in pro_plan["features"]
        assert "Market intelligence" in pro_plan["features"]
        assert pro_plan["highlight"] is True  # Pro is highlighted

    def test_business_has_unlimited_projects(self):
        """Business users should have unlimited projects."""
        client = create_client(plan_tier="business", subscription_status="active")

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "business"
        assert data["projects_limit"] is None  # Unlimited
        assert data["ai_generations_daily_limit"] == 500

    def test_business_plan_features(self):
        """Business plan should include team and API features."""
        client = create_client(plan_tier="business")

        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()
        business_plan = next(p for p in plans if p["tier"] == "business")

        assert business_plan["price_monthly"] == 19900
        assert "Unlimited projects" in business_plan["features"]
        assert "Team collaboration" in business_plan["features"]
        assert "API access" in business_plan["features"]

    def test_enterprise_has_highest_limits(self):
        """Enterprise users should have the highest limits."""
        client = create_client(plan_tier="enterprise", subscription_status="active")

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "enterprise"
        assert data["projects_limit"] is None  # Unlimited
        assert data["ai_generations_daily_limit"] == 9999

    def test_enterprise_plan_features(self):
        """Enterprise plan should include premium features."""
        client = create_client(plan_tier="enterprise")

        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()
        enterprise_plan = next(p for p in plans if p["tier"] == "enterprise")

        assert enterprise_plan["price_monthly"] == 49900
        assert "SSO & SAML" in enterprise_plan["features"]
        assert "SLA guarantee" in enterprise_plan["features"]
        assert "On-premise option" in enterprise_plan["features"]

    def test_expired_subscription_reflected_in_status(self):
        """Expired subscriptions should be reflected in the subscription status."""
        mock_db = MockDB(plan_tier="pro", subscription_status="canceled")
        mock_db.org_data.update({
            "stripe_subscription_id": None,
            "current_period_end": datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        })

        test_user = create_test_user(plan_tier="pro")
        app = _create_test_app(mock_db, test_user)

        with patch("app.modules.billing.service._ensure_stripe_configured", return_value=None):
            client = TestClient(app)
            response = client.get("/api/v1/billing/subscription")

            assert response.status_code == 200
            data = response.json()
            assert data["subscription_status"] == "canceled"

    def test_trial_user_has_full_pro_access(self):
        """Trial users should get Pro-level access during trial period."""
        client = create_client(plan_tier="pro", subscription_status="trialing")

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["projects_limit"] == 25
        assert data["ai_generations_daily_limit"] == 200

    def test_incomplete_subscription_status(self):
        """Incomplete subscriptions (payment pending) should be handled."""
        mock_db = MockDB(plan_tier="starter", subscription_status="incomplete")
        mock_db.org_data["stripe_subscription_id"] = "sub_incomplete_123"

        test_user = create_test_user(plan_tier="starter")
        app = _create_test_app(mock_db, test_user)

        with patch("app.modules.billing.service._ensure_stripe_configured", return_value=None):
            client = TestClient(app)
            response = client.get("/api/v1/billing/subscription")

            assert response.status_code == 200
            data = response.json()
            assert data["subscription_status"] == "incomplete"
            # User should still be on starter tier (pending payment)
            assert data["plan_tier"] == "starter"

    def test_all_tiers_ordered_by_price(self):
        """Plans should be returned in order by price."""
        client = create_client(plan_tier="free")

        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()
        prices = [p["price_monthly"] for p in plans]

        # Should be sorted from cheapest to most expensive
        assert prices == sorted(prices)
        assert prices[0] == 0  # Free
        assert prices[-1] == 49900  # Enterprise

    def test_usage_tracking_per_tier(self):
        """Each tier should track usage correctly."""
        # Test multiple tiers
        tiers = [
            ("free", 1, 5),
            ("starter", 5, 50),
            ("pro", 25, 200),
            ("business", None, 500),
            ("enterprise", None, 9999),
        ]

        for tier, expected_projects, expected_ai in tiers:
            client = create_client(plan_tier=tier, subscription_status="active" if tier != "free" else "none")

            response = client.get("/api/v1/billing/usage")
            assert response.status_code == 200

            data = response.json()
            assert data["plan_tier"] == tier
            assert data["projects_limit"] == expected_projects
            assert data["ai_generations_daily_limit"] == expected_ai

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service._ensure_stripe_configured")
    def test_cannot_checkout_for_free_plan(self, mock_ensure, mock_stripe):
        """Users should not be able to create checkout session for free plan."""
        client = create_client(plan_tier="free")

        response = client.post(
            "/api/v1/billing/subscribe",
            json={
                "plan_tier": "free",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel",
            },
        )

        # Should return validation error (422) or bad request (400)
        assert response.status_code in (400, 422)

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service._ensure_stripe_configured")
    def test_invoices_only_for_paying_customers(self, mock_ensure, mock_stripe):
        """Only users with Stripe customers should have invoices."""
        # Free user with no Stripe customer
        client = create_client(plan_tier="free", subscription_status="none")

        response = client.get("/api/v1/billing/invoices")
        assert response.status_code == 200

        data = response.json()
        assert data["invoices"] == []
        assert data["has_more"] is False

    @patch("app.modules.billing.service.stripe")
    @patch("app.modules.billing.service._ensure_stripe_configured")
    def test_pro_user_can_view_invoices(self, mock_ensure, mock_stripe):
        """Pro users with subscriptions can view their invoices."""
        client = create_client(plan_tier="pro", subscription_status="active")

        mock_inv = MagicMock()
        mock_inv.id = "inv_001"
        mock_inv.number = "INV-001"
        mock_inv.status = "paid"
        mock_inv.amount_due = 7900
        mock_inv.amount_paid = 7900
        mock_inv.currency = "usd"
        mock_inv.created = int(datetime.now(timezone.utc).timestamp())
        mock_inv.period_start = int(datetime.now(timezone.utc).timestamp())
        mock_inv.period_end = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
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
        assert data["invoices"][0]["amount_paid"] == 7900

    def test_plan_metadata_completeness(self):
        """All plans should have complete metadata."""
        client = create_client(plan_tier="free")

        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()

        required_fields = [
            "tier", "name", "price_monthly", "description",
            "max_projects", "ai_generations_per_day", "features"
        ]

        for plan in plans:
            for field in required_fields:
                assert field in plan, f"Plan {plan['tier']} missing field: {field}"

            # Features should be a non-empty list
            assert isinstance(plan["features"], list)
            assert len(plan["features"]) > 0

    def test_subscription_period_dates(self):
        """Active subscriptions should have period start and end dates."""
        client = create_client(plan_tier="pro", subscription_status="active")

        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200

        data = response.json()
        assert data["current_period_start"] is not None
        assert data["current_period_end"] is not None

        # Parse dates to ensure they're valid
        start = datetime.fromisoformat(data["current_period_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(data["current_period_end"].replace("Z", "+00:00"))

        # End should be after start
        assert end > start
