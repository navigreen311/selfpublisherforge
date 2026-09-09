"""Tests for Portfolio Economics module -- router endpoints, services, and schemas.

Covers:
- Portfolio overview, greenlight, kill/scale, backlist, recommendations (portfolio_router)
- Audience analyze, personas, also-bought, growth, churn (audience_router)
- Seasonal calendar, niche seasonality, launch recommendation, events (seasonal_router)
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from app.main import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_user(org_id, user_id):
    return {"user_id": user_id, "org_id": org_id, "role": "owner"}


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()

    # Mock execute to return empty results for DB queries
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_result.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    return db


@pytest_asyncio.fixture
async def client(mock_db, mock_user) -> AsyncClient:
    """Yield an HTTP test client with auth and DB dependency overrides."""
    app = create_app()

    from app.core.dependencies import get_current_user
    from app.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Patch async_session in the audience_service module so that internal DB
    # calls (which bypass the FastAPI get_db dependency) raise SQLAlchemyError
    # instead of attempting a real connection.  The service catches
    # (SQLAlchemyError, OperationalError) and falls back to defaults.
    mock_session_factory = MagicMock()
    mock_session_factory.side_effect = SQLAlchemyError("mocked: no real DB in tests")

    transport = ASGITransport(app=app)
    with patch(
        "app.modules.portfolio_economics.audience_service.async_session",
        mock_session_factory,
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Portfolio Router Endpoints
# ---------------------------------------------------------------------------


class TestPortfolioOverviewEndpoint:
    """GET /api/v1/portfolio"""

    @pytest.mark.asyncio
    async def test_get_portfolio_overview_success(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/portfolio")
        assert resp.status_code == 200
        body = resp.json()
        data = body["data"]
        assert "total_books" in data
        assert "active_books" in data
        assert "total_revenue" in data
        assert "portfolio_roi" in data
        assert "top_performers" in data
        assert isinstance(data["top_performers"], list)
        assert "genre_distribution" in data

    @pytest.mark.asyncio
    async def test_portfolio_overview_returns_empty_portfolio(self, client: AsyncClient) -> None:
        """With no books in mock DB, should return an empty portfolio overview."""
        resp = await client.get("/api/v1/portfolio")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_books"] == 0


class TestGreenlightEndpoint:
    """POST /api/v1/portfolio/greenlight"""

    @pytest.mark.asyncio
    async def test_greenlight_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/portfolio/greenlight",
            json={
                "title": "Test Romance Novel",
                "genre": "romance",
                "estimated_word_count": 60000,
                "estimated_price": 4.99,
                "royalty_rate": 0.7,
                "estimated_production_cost": 500.0,
                "estimated_marketing_budget": 200.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Test Romance Novel"
        assert data["genre"] == "romance"
        assert 0 <= data["greenlight_score"] <= 100
        assert data["recommendation"] in ("go", "caution", "no-go")
        assert data["projected_monthly_units"] >= 1
        assert data["total_investment"] == 700.0
        assert "risk_factors" in data
        assert "opportunity_factors" in data

    @pytest.mark.asyncio
    async def test_greenlight_rejects_invalid_price(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/portfolio/greenlight",
            json={
                "title": "Cheap Book",
                "genre": "romance",
                "estimated_price": 0.50,  # Below 0.99 minimum
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_greenlight_missing_required_fields(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/portfolio/greenlight",
            json={"genre": "romance"},  # Missing title
        )
        assert resp.status_code == 422


class TestKillScaleEndpoint:
    """POST /api/v1/portfolio/kill-scale"""

    @pytest.mark.asyncio
    async def test_kill_scale_success(self, client: AsyncClient) -> None:
        book_id = str(uuid4())
        resp = await client.post(
            "/api/v1/portfolio/kill-scale",
            json={
                "book_id": book_id,
                "current_monthly_revenue": 200.0,
                "current_monthly_units": 40,
                "months_since_launch": 6,
                "total_investment": 800.0,
                "total_revenue_to_date": 1200.0,
                "trend_direction": "flat",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["book_id"] == book_id
        assert data["decision"] in ("kill", "scale", "maintain", "revive")
        assert 0 <= data["score"] <= 100
        assert "reasoning" in data
        assert "actions" in data
        assert isinstance(data["reasoning"], list)
        assert isinstance(data["actions"], list)

    @pytest.mark.asyncio
    async def test_kill_scale_strong_performer_gets_scale(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/portfolio/kill-scale",
            json={
                "book_id": str(uuid4()),
                "current_monthly_revenue": 800.0,
                "current_monthly_units": 160,
                "months_since_launch": 8,
                "total_investment": 600.0,
                "total_revenue_to_date": 6400.0,
                "trend_direction": "up",
                "review_rating": 4.6,
                "review_count": 200,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["decision"] == "scale"


class TestBacklistEndpoint:
    """GET /api/v1/portfolio/backlist"""

    @pytest.mark.asyncio
    async def test_backlist_one_year(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/portfolio/backlist",
            params={"current_monthly_revenue": 500.0, "period": "1y"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["months"] == 12
        assert len(data["monthly_projections"]) == 12
        assert data["total_projected_revenue"] > 0
        assert data["total_projected_royalty"] > 0
        assert data["compounding_factor"] > 0

    @pytest.mark.asyncio
    async def test_backlist_five_year_with_series(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/portfolio/backlist",
            params={
                "current_monthly_revenue": 500.0,
                "period": "5y",
                "num_books": 3,
                "is_series": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["months"] == 60
        assert len(data["monthly_projections"]) == 60


class TestRecommendationsEndpoint:
    """GET /api/v1/portfolio/recommendations"""

    @pytest.mark.asyncio
    async def test_get_recommendations(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/portfolio/recommendations")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        if data:
            rec = data[0]
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec


# ---------------------------------------------------------------------------
# Audience Router Endpoints
# ---------------------------------------------------------------------------


class TestAudienceAnalyzeEndpoint:
    """POST /api/v1/audience/analyze"""

    @pytest.mark.asyncio
    async def test_analyze_audience_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/audience/analyze",
            json={
                "genre": "romance",
                "book_description": "A second chance love story in Paris",
                "keywords": ["paris", "second chance", "billionaire"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        persona = data[0]
        assert "name" in persona
        assert "age_range" in persona
        assert "gender_skew" in persona
        assert "reading_frequency" in persona
        assert "discovery_channels" in persona
        assert "motivations" in persona
        assert "percentage_of_audience" in persona

    @pytest.mark.asyncio
    async def test_analyze_audience_missing_genre(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/audience/analyze", json={})
        assert resp.status_code == 422


class TestAlsoBoughtEndpoint:
    """GET /api/v1/audience/also-bought/{book_id}"""

    @pytest.mark.asyncio
    async def test_also_bought_success(self, client: AsyncClient) -> None:
        book_id = str(uuid4())
        resp = await client.get(
            f"/api/v1/audience/also-bought/{book_id}",
            params={"genre": "fantasy"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "also_bought" in data
        assert isinstance(data["also_bought"], list)
        assert len(data["also_bought"]) > 0
        assert "average_price" in data
        assert "audience_insights" in data
        assert "positioning_suggestions" in data


class TestChurnPredictionEndpoint:
    """POST /api/v1/audience/churn-prediction"""

    @pytest.mark.asyncio
    async def test_churn_high_risk(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/audience/churn-prediction",
            json={
                "days_since_last_purchase": 200,
                "total_purchases": 1,
                "average_rating_given": 2.5,
                "email_open_rate": 0.05,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["churn_risk"] in ("high", "critical")
        assert data["churn_probability"] > 0.5
        assert len(data["risk_factors"]) > 0
        assert len(data["retention_suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_churn_low_risk(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/audience/churn-prediction",
            json={
                "days_since_last_purchase": 5,
                "total_purchases": 20,
                "average_rating_given": 4.8,
                "series_completion_rate": 0.95,
                "email_open_rate": 0.50,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["churn_risk"] in ("low", "moderate")
        assert data["churn_probability"] < 0.3


# ---------------------------------------------------------------------------
# Seasonal Router Endpoints
# ---------------------------------------------------------------------------


class TestSeasonalCalendarEndpoint:
    """GET /api/v1/seasonal/calendar"""

    @pytest.mark.asyncio
    async def test_seasonal_calendar_success(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/seasonal/calendar", params={"year": 2025})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["year"] == 2025
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) > 0

    @pytest.mark.asyncio
    async def test_calendar_default_year(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/seasonal/calendar")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["year"] == date.today().year

    @pytest.mark.asyncio
    async def test_calendar_with_genre_filter(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/seasonal/calendar",
            params={"year": 2025, "genres": "romance,thriller"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "genre_seasonality" in data


class TestNicheSeasonalityEndpoint:
    """GET /api/v1/seasonal/niche/{genre}"""

    @pytest.mark.asyncio
    async def test_niche_seasonality_romance(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/seasonal/niche/romance")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["genre"] == "romance"
        assert "monthly_demand" in data
        assert len(data["monthly_demand"]) == 12
        assert "peak_months" in data
        assert "low_months" in data
        assert "best_launch_windows" in data

    @pytest.mark.asyncio
    async def test_niche_seasonality_horror_october_peak(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/seasonal/niche/horror")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["monthly_demand"]["October"] > 1.5


class TestLaunchRecommendEndpoint:
    """POST /api/v1/seasonal/recommend-launch"""

    @pytest.mark.asyncio
    async def test_recommend_launch_success(self, client: AsyncClient) -> None:
        earliest = (date.today() + timedelta(days=30)).isoformat()
        resp = await client.post(
            "/api/v1/seasonal/recommend-launch",
            json={
                "genre": "romance",
                "earliest_ready_date": earliest,
                "marketing_lead_time_days": 14,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "recommended_date" in data
        assert "alternative_dates" in data
        assert "season_type" in data
        assert data["season_type"] in ("peak", "shoulder", "off_peak")
        assert "confidence" in data
        assert "reasoning" in data
        assert "pre_launch_checklist" in data
        assert "marketing_timeline" in data

    @pytest.mark.asyncio
    async def test_recommend_launch_missing_genre(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/seasonal/recommend-launch",
            json={"earliest_ready_date": date.today().isoformat()},
        )
        assert resp.status_code == 422


class TestUpcomingEventsEndpoint:
    """GET /api/v1/seasonal/events"""

    @pytest.mark.asyncio
    async def test_upcoming_events_with_genres(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/seasonal/events",
            params={"genres": "romance,thriller", "days_ahead": 180},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_upcoming_events_no_genres_365_days(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/seasonal/events",
            params={"days_ahead": 365},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0  # 365 days should find events

    @pytest.mark.asyncio
    async def test_upcoming_events_validates_days(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/seasonal/events",
            params={"days_ahead": 3},  # Below minimum of 7
        )
        assert resp.status_code == 422
