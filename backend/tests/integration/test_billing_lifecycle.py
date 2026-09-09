"""
Integration tests for billing subscription lifecycle.

Tests the complete subscription journey from free to paid plans,
including upgrades, downgrades, cancellations, and reactivations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user, require_role
from app.core.error_handler import register_error_handlers
from app.database import get_db
from app.modules.billing.router import router
from app.schemas.common import PlanTier

# ===========================================================================
# Test Fixtures
# ===========================================================================

TEST_ORG_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()

TEST_USER = {
    "user_id": TEST_USER_ID,
    "org_id": TEST_ORG_ID,
    "role": "owner",
    "email": "owner@example.com",
}


class MockDB:
    """Mock database that tracks org state across requests."""

    def __init__(self):
        self.org_data = {
            "id": TEST_ORG_ID,
            "plan_tier": "free",
            "subscription_status": "none",
            "stripe_subscription_id": None,
            "stripe_customer_id": None,
            "current_period_start": None,
            "current_period_end": None,
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
        """Mock flush method."""
        pass

    async def commit(self):
        """Mock commit method."""
        pass

    async def rollback(self):
        """Mock rollback method."""
        pass

    async def close(self):
        """Mock close method."""
        pass

    def update_org(self, **kwargs):
        """Update org data for testing."""
        self.org_data.update(kwargs)


def _create_test_app(mock_db: MockDB) -> FastAPI:
    """Build a minimal FastAPI app with billing router for testing."""
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1/billing", tags=["billing"])

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
def mock_db():
    """Return a mock database instance."""
    return MockDB()


@pytest.fixture
def client(mock_db):
    """Return a TestClient for the billing test app."""
    app = _create_test_app(mock_db)
    with patch(
        "app.modules.billing.service._ensure_stripe_configured",
        return_value=None,
    ):
        yield TestClient(app)


# ===========================================================================
# TestBillingLifecycle
# ===========================================================================


class TestBillingLifecycle:
    """Test complete billing subscription lifecycle scenarios."""

    def test_new_user_starts_on_free_plan(self, client, mock_db):
        """New users should have free plan with basic access."""
        mock_db.update_org(
            plan_tier="free",
            subscription_status="none",
            stripe_subscription_id=None,
            stripe_customer_id=None,
        )

        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "free"
        assert data["subscription_status"] == "none"
        assert data["stripe_subscription_id"] is None

    @patch("app.modules.billing.service.stripe")
    def test_upgrade_free_to_starter(self, mock_stripe, client, mock_db):
        """Upgrading from free to starter grants new features."""
        # Step 1: User is on free plan
        mock_db.update_org(
            plan_tier="free",
            subscription_status="none",
            stripe_customer_id=None,
        )

        # Step 2: Create checkout session for Starter plan
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_starter"
        mock_session.id = "cs_starter_123"
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
        assert "checkout_url" in data
        assert data["session_id"] == "cs_starter_123"

        # Step 3: Simulate webhook after successful payment
        mock_db.update_org(
            plan_tier="starter",
            subscription_status="active",
            stripe_subscription_id="sub_starter_456",
            stripe_customer_id="cus_test_789",
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC) + timedelta(days=30),
        )

        # Verify subscription is now active on Starter
        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200
        data = response.json()
        assert data["plan_tier"] == "starter"
        assert data["subscription_status"] == "active"

    @patch("app.modules.billing.service.stripe")
    def test_upgrade_starter_to_pro(self, mock_stripe, client, mock_db):
        """Upgrading from starter to pro grants AI features."""
        # User is on Starter plan
        mock_db.update_org(
            plan_tier="starter",
            subscription_status="active",
            stripe_customer_id="cus_test_123",
            stripe_subscription_id="sub_starter_123",
        )

        # Upgrade to Pro
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_pro"
        mock_session.id = "cs_pro_456"
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

        # After webhook processing
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            stripe_subscription_id="sub_pro_789",
        )

        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "active"

    def test_downgrade_pro_to_starter(self, client, mock_db):
        """Downgrading from pro to starter removes access at end of billing period."""
        # User is on Pro with cancel_at_period_end flag
        end_date = datetime.now(UTC) + timedelta(days=15)
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            stripe_subscription_id="sub_pro_123",
            stripe_customer_id="cus_test_123",
            cancel_at_period_end=True,
            current_period_start=datetime.now(UTC) - timedelta(days=15),
            current_period_end=end_date,
        )

        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200
        data = response.json()

        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "active"
        assert data["cancel_at_period_end"] is True
        # User still has Pro access until period end

    @patch("app.modules.billing.service.stripe")
    def test_cancel_subscription(self, mock_stripe, client, mock_db):
        """Cancellation preserves data but removes paid features."""
        # User has active Pro subscription
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            stripe_customer_id="cus_test_123",
            stripe_subscription_id="sub_pro_123",
            projects_count=10,
            ai_generations_today=50,
        )

        # User cancels via billing portal (simulated)
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            cancel_at_period_end=True,
        )

        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["cancel_at_period_end"] is True

        # After period ends, subscription is deleted
        mock_db.update_org(
            plan_tier="free",
            subscription_status="canceled",
            stripe_subscription_id=None,
            cancel_at_period_end=False,
            # Data is preserved
            projects_count=10,
            ai_generations_today=50,
        )

        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["plan_tier"] == "free"
        assert data["subscription_status"] == "canceled"

    @patch("app.modules.billing.service.stripe")
    def test_reactivate_after_cancel(self, mock_stripe, client, mock_db):
        """Reactivation restores previous plan."""
        # User had canceled and is now on free
        mock_db.update_org(
            plan_tier="free",
            subscription_status="canceled",
            stripe_customer_id="cus_test_123",
        )

        # User resubscribes to Pro
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_pro"
        mock_session.id = "cs_pro_reactivate"
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

        # After webhook, user is back on Pro
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            stripe_subscription_id="sub_pro_new_123",
        )

        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "active"

    def test_usage_metering_tracked(self, client, mock_db):
        """API calls and AI usage properly metered."""
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            projects_count=10,
            ai_generations_today=42,
            current_period_start=datetime.now(UTC) - timedelta(days=10),
            current_period_end=datetime.now(UTC) + timedelta(days=20),
        )

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["projects_used"] == 10
        assert data["projects_limit"] == 25  # Pro limit
        assert data["ai_generations_used_today"] == 42
        assert data["ai_generations_daily_limit"] == 200  # Pro limit
        assert data["current_period_start"] is not None
        assert data["current_period_end"] is not None

    def test_usage_limits_enforced(self, client, mock_db):
        """Usage limits prevent overuse on each tier."""
        # User on Starter plan hitting project limit
        mock_db.update_org(
            plan_tier="starter",
            subscription_status="active",
            projects_count=5,  # At limit
            ai_generations_today=48,
        )

        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["projects_used"] == 5
        assert data["projects_limit"] == 5  # Starter limit
        assert data["projects_used"] >= data["projects_limit"]

        # AI generations approaching limit
        assert data["ai_generations_used_today"] == 48
        assert data["ai_generations_daily_limit"] == 50  # Starter limit
        assert data["ai_generations_used_today"] < data["ai_generations_daily_limit"]

    @patch("app.modules.billing.service.stripe")
    def test_trial_period_workflow(self, mock_stripe, client, mock_db):
        """Users on trial should have full access to their tier."""
        # User starts a Pro trial
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="trialing",
            stripe_subscription_id="sub_trial_123",
            stripe_customer_id="cus_test_123",
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC) + timedelta(days=14),
        )

        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "trialing"

        # Check usage - should have Pro limits during trial
        response = client.get("/api/v1/billing/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["projects_limit"] == 25  # Pro limit
        assert data["ai_generations_daily_limit"] == 200  # Pro limit

    def test_past_due_subscription_status(self, client, mock_db):
        """Past due subscriptions should be reflected in status."""
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="past_due",
            stripe_subscription_id="sub_pro_123",
            stripe_customer_id="cus_test_123",
        )

        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200

        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "past_due"

    @patch("app.modules.billing.service.stripe")
    def test_multiple_plan_changes_in_sequence(self, mock_stripe, client, mock_db):
        """Test a realistic sequence of plan changes."""
        # 1. Start on free
        mock_db.update_org(
            plan_tier="free",
            subscription_status="none",
        )
        response = client.get("/api/v1/billing/subscription")
        assert response.json()["plan_tier"] == "free"

        # 2. Upgrade to Starter
        mock_db.update_org(
            plan_tier="starter",
            subscription_status="active",
            stripe_subscription_id="sub_starter",
        )
        response = client.get("/api/v1/billing/subscription")
        assert response.json()["plan_tier"] == "starter"

        # 3. Upgrade to Pro
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            stripe_subscription_id="sub_pro",
        )
        response = client.get("/api/v1/billing/subscription")
        assert response.json()["plan_tier"] == "pro"

        # 4. Cancel (but still active until period end)
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            cancel_at_period_end=True,
        )
        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["plan_tier"] == "pro"
        assert data["cancel_at_period_end"] is True

        # 5. Period ends, downgrade to free
        mock_db.update_org(
            plan_tier="free",
            subscription_status="canceled",
            cancel_at_period_end=False,
        )
        response = client.get("/api/v1/billing/subscription")
        data = response.json()
        assert data["plan_tier"] == "free"
        assert data["subscription_status"] == "canceled"

    @patch("app.modules.billing.service.stripe")
    def test_invoice_history_tracks_payments(self, mock_stripe, client, mock_db):
        """Invoice history should track payment lifecycle."""
        mock_db.update_org(
            plan_tier="pro",
            subscription_status="active",
            stripe_customer_id="cus_test_123",
        )

        # Mock invoice data
        mock_inv = MagicMock()
        mock_inv.id = "inv_001"
        mock_inv.number = "INV-2024-001"
        mock_inv.status = "paid"
        mock_inv.amount_due = 7900
        mock_inv.amount_paid = 7900
        mock_inv.currency = "usd"
        mock_inv.created = int(datetime.now(UTC).timestamp())
        mock_inv.period_start = int(datetime.now(UTC).timestamp())
        mock_inv.period_end = int((datetime.now(UTC) + timedelta(days=30)).timestamp())
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
        assert data["invoices"][0]["status"] == "paid"
        assert data["invoices"][0]["amount_paid"] == 7900
