"""Integration tests for the Pricing Automation API endpoints.

Tests the full request/response cycle through FastAPI with mocked database layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import create_app
from app.core.dependencies import get_current_user
from app.modules.pricing_automation.schemas import (
    ABTestResponse,
    ABTestStatus,
    BookFormat,
    CompetitorPriceSummary,
    PricingRuleResponse,
    PromotionResponse,
    PromotionStatus,
    RuleStatus,
)

# ──────────────────── Test DB Setup ────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def book_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def mock_user(org_id):
    return {"user_id": uuid.uuid4(), "org_id": org_id, "role": "admin"}


@pytest_asyncio.fixture
async def mock_db():
    """Create an in-memory SQLite test database session."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False)

    @event.listens_for(test_engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Strip PG-specific server defaults for SQLite
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                sd = column.server_default
                if hasattr(sd, "arg") and hasattr(sd.arg, "text"):
                    if "gen_random_uuid" in str(sd.arg.text):
                        column.server_default = None

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def fastapi_app(mock_db, mock_user):
    """Create a FastAPI app with DB and auth overrides."""
    app = create_app()

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(fastapi_app):
    """Create an async test client."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ──────────────────── Simulation Endpoint ────────────────────


@pytest.mark.asyncio
class TestSimulateEndpoint:
    async def test_simulate_price_change(self, client: AsyncClient):
        """POST /api/v1/pricing/simulate returns simulation results."""
        response = await client.post(
            "/api/v1/pricing/simulate",
            json={
                "current_price": 4.99,
                "proposed_price": 2.99,
                "current_daily_sales": 10.0,
                "elasticity": -1.5,
                "book_format": "ebook",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_price"] == 4.99
        assert data["proposed_price"] == 2.99
        assert "current_metrics" in data
        assert "proposed_metrics" in data
        assert "recommended_price_points" in data
        assert len(data["recommended_price_points"]) > 0

    async def test_simulate_with_book_id(self, client: AsyncClient):
        """Simulation accepts an optional book_id."""
        bid = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/pricing/simulate",
            json={
                "book_id": bid,
                "current_price": 9.99,
                "proposed_price": 6.99,
                "current_daily_sales": 5.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == bid

    async def test_simulate_invalid_price(self, client: AsyncClient):
        """Negative prices should fail validation."""
        response = await client.post(
            "/api/v1/pricing/simulate",
            json={
                "current_price": -1.0,
                "proposed_price": 2.99,
                "current_daily_sales": 10.0,
            },
        )
        assert response.status_code == 422

    async def test_simulate_paperback(self, client: AsyncClient):
        """Simulation works for paperback format."""
        response = await client.post(
            "/api/v1/pricing/simulate",
            json={
                "current_price": 14.99,
                "proposed_price": 12.99,
                "book_format": "paperback",
                "current_daily_sales": 3.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_format"] == "paperback"


# ──────────────────── KU Calculator Endpoint ────────────────────


@pytest.mark.asyncio
class TestKUCalculatorEndpoint:
    async def test_ku_calculator_basic(self, client: AsyncClient):
        """POST /api/v1/pricing/ku-calculator returns comparison."""
        response = await client.post(
            "/api/v1/pricing/ku-calculator",
            json={
                "book_page_count": 300,
                "estimated_ku_reads_per_month": 100,
                "ku_page_rate": 0.0045,
                "wide_price": 4.99,
                "wide_monthly_sales": 50,
                "wide_royalty_rate": 0.70,
                "amazon_price": 4.99,
                "amazon_monthly_sales": 30,
                "amazon_royalty_rate": 0.70,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "ku_exclusive" in data
        assert "wide_distribution" in data
        assert "difference_monthly" in data
        assert "recommendation" in data
        assert "details" in data

    async def test_ku_calculator_zero_reads(self, client: AsyncClient):
        """Calculator handles zero KU reads."""
        response = await client.post(
            "/api/v1/pricing/ku-calculator",
            json={
                "book_page_count": 300,
                "estimated_ku_reads_per_month": 0,
                "wide_price": 4.99,
                "wide_monthly_sales": 50,
                "amazon_price": 4.99,
                "amazon_monthly_sales": 30,
            },
        )
        assert response.status_code == 200

    async def test_ku_calculator_validation(self, client: AsyncClient):
        """Invalid page count fails validation."""
        response = await client.post(
            "/api/v1/pricing/ku-calculator",
            json={
                "book_page_count": 0,  # Must be >= 1
                "estimated_ku_reads_per_month": 100,
                "wide_price": 4.99,
                "wide_monthly_sales": 50,
                "amazon_price": 4.99,
                "amazon_monthly_sales": 30,
            },
        )
        assert response.status_code == 422


# ──────────────────── Pricing Rules Endpoints (with mocked service) ────────────────────


@pytest.mark.asyncio
class TestPricingRulesEndpoints:
    async def test_create_rule(self, client: AsyncClient, org_id):
        """POST /api/v1/pricing/rules creates a rule."""
        from app.modules.pricing_automation.service import PricingAutomationService

        now = datetime.now(timezone.utc)
        rule_id = uuid.uuid4()

        mock_rule_response = PricingRuleResponse(
            id=rule_id,
            org_id=org_id,
            name="Test Rule",
            description="A test rule",
            book_id=None,
            strategy="competitive_match",
            status="draft",
            book_format="ebook",
            min_price=0.99,
            max_price=9.99,
            target_price=None,
            parameters={},
            is_auto_apply=False,
            last_applied_at=None,
            created_at=now,
            updated_at=now,
        )

        with patch.object(
            PricingAutomationService,
            "create_rule",
            new_callable=AsyncMock,
            return_value=mock_rule_response,
        ):
            response = await client.post(
                "/api/v1/pricing/rules",
                json={
                    "name": "Test Rule",
                    "description": "A test rule",
                    "strategy": "competitive_match",
                    "min_price": 0.99,
                    "max_price": 9.99,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Rule"
        assert data["strategy"] == "competitive_match"
        assert data["status"] == "draft"

    async def test_create_rule_validation_max_lt_min(self, client: AsyncClient):
        """Creating a rule with max_price < min_price fails."""
        response = await client.post(
            "/api/v1/pricing/rules",
            json={
                "name": "Bad Rule",
                "strategy": "competitive_match",
                "min_price": 9.99,
                "max_price": 0.99,
            },
        )
        assert response.status_code == 422

    async def test_list_rules(self, client: AsyncClient, org_id):
        """GET /api/v1/pricing/rules returns paginated results."""
        from app.modules.pricing_automation.service import PricingAutomationService

        now = datetime.now(timezone.utc)
        mock_rules = [
            PricingRuleResponse(
                id=uuid.uuid4(),
                org_id=org_id,
                name=f"Rule {i}",
                description=None,
                book_id=None,
                strategy="competitive_match",
                status="active",
                book_format="ebook",
                min_price=0.99,
                max_price=9.99,
                target_price=None,
                parameters={},
                is_auto_apply=False,
                last_applied_at=None,
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]

        with patch.object(
            PricingAutomationService,
            "list_rules",
            new_callable=AsyncMock,
            return_value=(mock_rules, 3),
        ):
            response = await client.get("/api/v1/pricing/rules")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total_count"] == 3
        assert len(data["items"]) == 3

    async def test_delete_rule_not_found(self, client: AsyncClient):
        """DELETE /api/v1/pricing/rules/{id} returns 404 when not found."""
        from app.modules.pricing_automation.service import PricingAutomationService

        with patch.object(
            PricingAutomationService,
            "delete_rule",
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = await client.delete(f"/api/v1/pricing/rules/{uuid.uuid4()}")

        assert response.status_code == 404


# ──────────────────── Promotion Endpoints ────────────────────


@pytest.mark.asyncio
class TestPromotionEndpoints:
    async def test_create_promotion(self, client: AsyncClient, org_id, book_id):
        """POST /api/v1/pricing/promotions schedules a promotion."""
        from app.modules.pricing_automation.service import PricingAutomationService

        now = datetime.now(timezone.utc)
        start = now + timedelta(days=7)
        end = now + timedelta(days=14)

        mock_promo = PromotionResponse(
            id=uuid.uuid4(),
            org_id=org_id,
            pricing_rule_id=None,
            book_id=book_id,
            name="Spring Sale",
            description=None,
            original_price=4.99,
            promo_price=0.99,
            book_format="ebook",
            start_date=start,
            end_date=end,
            status="scheduled",
            platform="amazon",
            notes=None,
            performance_data=None,
            created_at=now,
            updated_at=now,
        )

        with patch.object(
            PricingAutomationService,
            "create_promotion",
            new_callable=AsyncMock,
            return_value=mock_promo,
        ):
            response = await client.post(
                "/api/v1/pricing/promotions",
                json={
                    "book_id": str(book_id),
                    "name": "Spring Sale",
                    "original_price": 4.99,
                    "promo_price": 0.99,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Spring Sale"
        assert data["status"] == "scheduled"

    async def test_create_promotion_end_before_start(self, client: AsyncClient):
        """Creating promotion with end_date before start_date fails."""
        now = datetime.now(timezone.utc)
        response = await client.post(
            "/api/v1/pricing/promotions",
            json={
                "book_id": str(uuid.uuid4()),
                "name": "Bad Promo",
                "original_price": 4.99,
                "promo_price": 0.99,
                "start_date": (now + timedelta(days=14)).isoformat(),
                "end_date": (now + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 422

    async def test_create_promotion_promo_gte_original(self, client: AsyncClient):
        """Creating promotion with promo_price >= original_price fails."""
        now = datetime.now(timezone.utc)
        response = await client.post(
            "/api/v1/pricing/promotions",
            json={
                "book_id": str(uuid.uuid4()),
                "name": "Bad Promo",
                "original_price": 4.99,
                "promo_price": 5.99,
                "start_date": (now + timedelta(days=1)).isoformat(),
                "end_date": (now + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 422


# ──────────────────── A/B Test Endpoints ────────────────────


@pytest.mark.asyncio
class TestABTestEndpoints:
    async def test_create_ab_test(self, client: AsyncClient, org_id, book_id):
        """POST /api/v1/pricing/ab-test creates a test."""
        from app.modules.pricing_automation.service import PricingAutomationService

        now = datetime.now(timezone.utc)

        mock_test = ABTestResponse(
            id=uuid.uuid4(),
            org_id=org_id,
            pricing_rule_id=None,
            book_id=book_id,
            name="Price Test A vs B",
            description=None,
            price_a=2.99,
            price_b=4.99,
            book_format="ebook",
            status="draft",
            start_date=None,
            end_date=None,
            duration_days=14,
            results=None,
            winner=None,
            confidence_level=None,
            created_at=now,
            updated_at=now,
        )

        with patch.object(
            PricingAutomationService,
            "create_ab_test",
            new_callable=AsyncMock,
            return_value=mock_test,
        ):
            response = await client.post(
                "/api/v1/pricing/ab-test",
                json={
                    "book_id": str(book_id),
                    "name": "Price Test A vs B",
                    "price_a": 2.99,
                    "price_b": 4.99,
                    "duration_days": 14,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Price Test A vs B"
        assert data["price_a"] == 2.99
        assert data["price_b"] == 4.99
        assert data["status"] == "draft"


# ──────────────────── Competitor Endpoint ────────────────────


@pytest.mark.asyncio
class TestCompetitorEndpoint:
    async def test_get_competitors_empty(self, client: AsyncClient, org_id, book_id):
        """GET /api/v1/pricing/competitors/{book_id} returns summary."""
        from app.modules.pricing_automation.service import PricingAutomationService

        mock_summary = CompetitorPriceSummary(
            book_id=book_id,
            book_format="ebook",
            total_competitors=0,
            avg_price=0.0,
            median_price=0.0,
            min_price=0.0,
            max_price=0.0,
            price_percentile_25=0.0,
            price_percentile_75=0.0,
            avg_bsr=None,
            avg_review_rating=None,
            competitors=[],
        )

        with patch.object(
            PricingAutomationService,
            "get_competitor_prices",
            new_callable=AsyncMock,
            return_value=mock_summary,
        ):
            response = await client.get(f"/api/v1/pricing/competitors/{book_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_competitors"] == 0
        assert data["competitors"] == []
