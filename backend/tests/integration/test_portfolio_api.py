"""Integration tests for Portfolio Economics, Audience DNA, and Seasonal Calendar API endpoints."""
import uuid

import pytest
import pytest_asyncio
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport
from app.main import create_app


# ─── Fixtures ─────────────────────────────────────────────────────────────────

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


@pytest.fixture
def book_id():
    return str(uuid4())


@pytest_asyncio.fixture
async def client(mock_db, mock_user):
    """Create an async HTTP client with auth and DB dependency overrides."""
    app = create_app()

    from app.database import get_db
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Portfolio Endpoints ─────────────────────────────────────────────────────

class TestPortfolioOverview:
    @pytest.mark.asyncio
    async def test_get_portfolio_overview(self, client):
        response = await client.get("/api/v1/portfolio")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_books" in data
        assert "total_revenue" in data
        assert "portfolio_roi" in data
        assert "top_performers" in data

    @pytest.mark.asyncio
    async def test_portfolio_overview_returns_empty_portfolio(self, client):
        """With no books in DB, should return an empty portfolio overview."""
        response = await client.get("/api/v1/portfolio")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_books"] == 0


class TestGreenlightGate:
    @pytest.mark.asyncio
    async def test_greenlight_basic(self, client):
        response = await client.post(
            "/api/v1/portfolio/greenlight",
            json={
                "title": "My Test Book",
                "genre": "romance",
                "estimated_word_count": 60000,
                "estimated_price": 4.99,
                "royalty_rate": 0.7,
                "estimated_production_cost": 500.0,
                "estimated_marketing_budget": 200.0,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "My Test Book"
        assert data["genre"] == "romance"
        assert 0 <= data["greenlight_score"] <= 100
        assert data["recommendation"] in ("go", "caution", "no-go")
        assert data["estimated_market_size"] > 0
        assert data["projected_monthly_units"] >= 1

    @pytest.mark.asyncio
    async def test_greenlight_with_series(self, client):
        response = await client.post(
            "/api/v1/portfolio/greenlight",
            json={
                "title": "Series Book 1",
                "genre": "fantasy",
                "is_series": True,
                "series_position": 1,
                "comparable_asins": ["B001", "B002", "B003"],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "Series Book 1"

    @pytest.mark.asyncio
    async def test_greenlight_validates_price(self, client):
        response = await client.post(
            "/api/v1/portfolio/greenlight",
            json={
                "title": "Bad Price Book",
                "genre": "romance",
                "estimated_price": 0.50,  # Below minimum
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_greenlight_missing_title(self, client):
        response = await client.post(
            "/api/v1/portfolio/greenlight",
            json={"genre": "romance"},
        )
        assert response.status_code == 422


class TestKillScale:
    @pytest.mark.asyncio
    async def test_kill_scale_basic(self, client, book_id):
        response = await client.post(
            "/api/v1/portfolio/kill-scale",
            json={
                "book_id": book_id,
                "current_monthly_revenue": 150.0,
                "current_monthly_units": 30,
                "months_since_launch": 6,
                "total_investment": 800.0,
                "total_revenue_to_date": 900.0,
                "trend_direction": "flat",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["book_id"] == book_id
        assert data["decision"] in ("kill", "scale", "maintain", "revive")
        assert 0 <= data["score"] <= 100
        assert "reasoning" in data
        assert "actions" in data

    @pytest.mark.asyncio
    async def test_kill_scale_declining_book(self, client, book_id):
        response = await client.post(
            "/api/v1/portfolio/kill-scale",
            json={
                "book_id": book_id,
                "current_monthly_revenue": 20.0,
                "current_monthly_units": 4,
                "months_since_launch": 12,
                "total_investment": 1000.0,
                "total_revenue_to_date": 400.0,
                "trend_direction": "down",
                "review_rating": 3.0,
                "review_count": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["decision"] in ("kill", "revive")

    @pytest.mark.asyncio
    async def test_kill_scale_strong_book(self, client, book_id):
        response = await client.post(
            "/api/v1/portfolio/kill-scale",
            json={
                "book_id": book_id,
                "current_monthly_revenue": 800.0,
                "current_monthly_units": 160,
                "months_since_launch": 6,
                "total_investment": 600.0,
                "total_revenue_to_date": 4800.0,
                "trend_direction": "up",
                "review_rating": 4.5,
                "review_count": 150,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["decision"] == "scale"


class TestBacklistProjection:
    @pytest.mark.asyncio
    async def test_backlist_one_year(self, client):
        response = await client.get(
            "/api/v1/portfolio/backlist",
            params={
                "current_monthly_revenue": 500.0,
                "period": "1y",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["months"] == 12
        assert len(data["monthly_projections"]) == 12
        assert data["total_projected_revenue"] > 0

    @pytest.mark.asyncio
    async def test_backlist_five_year(self, client):
        response = await client.get(
            "/api/v1/portfolio/backlist",
            params={
                "current_monthly_revenue": 500.0,
                "period": "5y",
                "num_books": 3,
                "is_series": True,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["months"] == 60
        assert len(data["monthly_projections"]) == 60

    @pytest.mark.asyncio
    async def test_backlist_with_new_books(self, client):
        response = await client.get(
            "/api/v1/portfolio/backlist",
            params={
                "current_monthly_revenue": 500.0,
                "period": "3y",
                "new_books_per_year": 2,
                "new_book_monthly_revenue": 300.0,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_projected_revenue"] > 0


class TestPortfolioRecommendations:
    @pytest.mark.asyncio
    async def test_get_recommendations(self, client):
        response = await client.get("/api/v1/portfolio/recommendations")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        # Should get at least one recommendation
        if data:
            rec = data[0]
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec


# ─── Audience DNA Endpoints ──────────────────────────────────────────────────

class TestAudienceAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_audience(self, client):
        response = await client.post(
            "/api/v1/audience/analyze",
            json={
                "genre": "romance",
                "book_description": "A love story set in Paris",
                "keywords": ["paris", "love", "second chance"],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

        persona = data[0]
        assert "name" in persona
        assert "age_range" in persona
        assert "gender_skew" in persona
        assert "reading_frequency" in persona
        assert "discovery_channels" in persona
        assert "motivations" in persona

    @pytest.mark.asyncio
    async def test_analyze_audience_missing_genre(self, client):
        response = await client.post(
            "/api/v1/audience/analyze",
            json={},
        )
        assert response.status_code == 422


class TestAudiencePersonas:
    @pytest.mark.asyncio
    async def test_get_personas(self, client, book_id):
        response = await client.get(
            f"/api/v1/audience/personas/{book_id}",
            params={"genre": "thriller"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_personas_default_genre(self, client, book_id):
        response = await client.get(f"/api/v1/audience/personas/{book_id}")
        assert response.status_code == 200


class TestAlsoBought:
    @pytest.mark.asyncio
    async def test_get_also_bought(self, client, book_id):
        response = await client.get(
            f"/api/v1/audience/also-bought/{book_id}",
            params={"genre": "fantasy"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "also_bought" in data
        assert "average_price" in data
        assert "audience_insights" in data
        assert "positioning_suggestions" in data
        assert isinstance(data["also_bought"], list)


class TestAudienceGrowth:
    @pytest.mark.asyncio
    async def test_audience_growth(self, client, org_id):
        response = await client.get(
            "/api/v1/audience/growth",
            params={"org_id": str(org_id), "days": 30},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "data_points" in data
        assert "total_audience_size" in data
        assert "growth_rate" in data
        assert len(data["data_points"]) == 30

    @pytest.mark.asyncio
    async def test_audience_growth_validates_days(self, client, org_id):
        response = await client.get(
            "/api/v1/audience/growth",
            params={"org_id": str(org_id), "days": 3},  # Below minimum
        )
        assert response.status_code == 422


class TestChurnPrediction:
    @pytest.mark.asyncio
    async def test_churn_prediction_high_risk(self, client):
        response = await client.post(
            "/api/v1/audience/churn-prediction",
            json={
                "days_since_last_purchase": 200,
                "total_purchases": 1,
                "average_rating_given": 2.5,
                "email_open_rate": 0.05,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["churn_risk"] in ("high", "critical")
        assert data["churn_probability"] > 0.5
        assert len(data["risk_factors"]) > 0
        assert len(data["retention_suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_churn_prediction_low_risk(self, client):
        response = await client.post(
            "/api/v1/audience/churn-prediction",
            json={
                "days_since_last_purchase": 5,
                "total_purchases": 15,
                "average_rating_given": 4.8,
                "series_completion_rate": 0.9,
                "email_open_rate": 0.45,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["churn_risk"] in ("low", "moderate")
        assert data["churn_probability"] < 0.3


# ─── Seasonal Calendar Endpoints ─────────────────────────────────────────────

class TestSeasonalCalendar:
    @pytest.mark.asyncio
    async def test_get_calendar(self, client):
        response = await client.get(
            "/api/v1/seasonal/calendar",
            params={"year": 2025},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["year"] == 2025
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) > 0

    @pytest.mark.asyncio
    async def test_calendar_with_genres(self, client):
        response = await client.get(
            "/api/v1/seasonal/calendar",
            params={"year": 2025, "genres": "romance,thriller"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "genre_seasonality" in data

    @pytest.mark.asyncio
    async def test_calendar_default_year(self, client):
        response = await client.get("/api/v1/seasonal/calendar")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["year"] == date.today().year


class TestNicheSeasonality:
    @pytest.mark.asyncio
    async def test_niche_seasonality(self, client):
        response = await client.get("/api/v1/seasonal/niche/romance")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["genre"] == "romance"
        assert "monthly_demand" in data
        assert len(data["monthly_demand"]) == 12
        assert "peak_months" in data
        assert "low_months" in data
        assert "best_launch_windows" in data

    @pytest.mark.asyncio
    async def test_niche_seasonality_horror(self, client):
        response = await client.get("/api/v1/seasonal/niche/horror")
        assert response.status_code == 200
        data = response.json()["data"]
        # October should be peak for horror
        assert data["monthly_demand"]["October"] > 1.5


class TestLaunchRecommendation:
    @pytest.mark.asyncio
    async def test_recommend_launch(self, client):
        earliest = (date.today() + timedelta(days=30)).isoformat()
        response = await client.post(
            "/api/v1/seasonal/recommend-launch",
            json={
                "genre": "romance",
                "earliest_ready_date": earliest,
                "marketing_lead_time_days": 14,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "recommended_date" in data
        assert "alternative_dates" in data
        assert "season_type" in data
        assert "confidence" in data
        assert "reasoning" in data
        assert "pre_launch_checklist" in data
        assert "marketing_timeline" in data

    @pytest.mark.asyncio
    async def test_recommend_launch_with_series(self, client):
        earliest = (date.today() + timedelta(days=14)).isoformat()
        response = await client.post(
            "/api/v1/seasonal/recommend-launch",
            json={
                "genre": "fantasy",
                "is_series": True,
                "series_position": 2,
                "earliest_ready_date": earliest,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recommend_launch_missing_genre(self, client):
        response = await client.post(
            "/api/v1/seasonal/recommend-launch",
            json={
                "earliest_ready_date": date.today().isoformat(),
            },
        )
        assert response.status_code == 422


class TestUpcomingEvents:
    @pytest.mark.asyncio
    async def test_upcoming_events(self, client):
        response = await client.get(
            "/api/v1/seasonal/events",
            params={"genres": "romance,thriller", "days_ahead": 180},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_upcoming_events_no_genres(self, client):
        response = await client.get(
            "/api/v1/seasonal/events",
            params={"days_ahead": 365},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        # With 365 days and no genre filter, should find events
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_upcoming_events_validates_days(self, client):
        response = await client.get(
            "/api/v1/seasonal/events",
            params={"days_ahead": 3},  # Below minimum
        )
        assert response.status_code == 422
