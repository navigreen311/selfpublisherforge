"""Unit tests for the Portfolio Economics service and router.

Tests cover:
- Portfolio overview returning real data from book list (service layer)
- Portfolio overview with empty book data (service layer)
- Authentication enforcement (router returns 403 without token)
- Kill/scale decision logic (service layer)
- Portfolio recommendations generation (service layer)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

import pytest

from app.modules.portfolio_economics.portfolio_service import (
    build_portfolio_overview,
    calculate_kill_scale,
    generate_portfolio_recommendations,
)
from app.modules.portfolio_economics.schemas import (
    BookSummary,
    ConfidenceLevel,
    DecisionType,
    KillScaleRequest,
    PortfolioOverview,
    PortfolioRecommendation,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def sample_books() -> list[dict]:
    """Two sample books for building a portfolio overview."""
    return [
        {
            "book_id": uuid.uuid4(),
            "title": "Romance Bestseller",
            "genre": "romance",
            "monthly_revenue": 450.0,
            "monthly_units": 90,
            "total_revenue": 5400.0,
            "total_investment": 800.0,
            "launch_date": date(2024, 1, 15),
            "status": "active",
        },
        {
            "book_id": uuid.uuid4(),
            "title": "Thriller Hit",
            "genre": "thriller",
            "monthly_revenue": 280.0,
            "monthly_units": 55,
            "total_revenue": 3360.0,
            "total_investment": 600.0,
            "launch_date": date(2024, 6, 1),
            "status": "active",
        },
    ]


# ---------------------------------------------------------------------------
# Tests: Portfolio overview returns real data
# ---------------------------------------------------------------------------


class TestGetPortfolioOverviewReturnsRealData:
    """Verify build_portfolio_overview returns structured portfolio data
    when provided with book records."""

    def test_overview_contains_expected_fields(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        assert isinstance(overview, PortfolioOverview)
        assert overview.org_id == org_id
        assert overview.total_books == 2
        assert overview.active_books == 2
        assert overview.total_revenue > 0
        assert overview.total_investment > 0
        assert overview.portfolio_roi != 0.0
        assert overview.monthly_revenue > 0
        assert len(overview.top_performers) > 0
        assert overview.genre_distribution != {}
        assert overview.revenue_by_genre != {}

    def test_overview_correct_totals(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        assert overview.total_revenue == pytest.approx(5400.0 + 3360.0, abs=0.01)
        assert overview.total_investment == pytest.approx(800.0 + 600.0, abs=0.01)
        assert overview.monthly_revenue == pytest.approx(450.0 + 280.0, abs=0.01)

    def test_overview_roi_calculated(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        expected_roi = ((5400 + 3360 - 800 - 600) / (800 + 600)) * 100
        assert overview.portfolio_roi == pytest.approx(expected_roi, abs=0.1)

    def test_overview_top_performers_sorted(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        assert len(overview.top_performers) == 2
        # Top performer should have highest monthly_revenue
        assert overview.top_performers[0].monthly_revenue >= overview.top_performers[1].monthly_revenue

    def test_overview_genre_distribution(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        assert overview.genre_distribution == {"romance": 1, "thriller": 1}
        assert overview.revenue_by_genre["romance"] == pytest.approx(5400.0, abs=0.01)
        assert overview.revenue_by_genre["thriller"] == pytest.approx(3360.0, abs=0.01)

    def test_overview_book_summaries_have_roi(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        for book in overview.top_performers:
            assert isinstance(book, BookSummary)
            assert isinstance(book.roi, float)

    def test_overview_updated_at_set(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        assert isinstance(overview.updated_at, datetime)


# ---------------------------------------------------------------------------
# Tests: Portfolio overview with empty data
# ---------------------------------------------------------------------------


class TestGetPortfolioOverviewEmpty:
    """Verify the service handles an empty book list gracefully."""

    def test_build_overview_empty_books(self, org_id: uuid.UUID):
        """Empty books should return zeroed-out overview."""
        overview = build_portfolio_overview(org_id, [])
        assert overview.org_id == org_id
        assert overview.total_books == 0
        assert overview.active_books == 0
        assert overview.total_revenue == 0.0
        assert overview.total_investment == 0.0
        assert overview.portfolio_roi == 0.0
        assert overview.monthly_revenue == 0.0
        assert overview.top_performers == []
        assert overview.underperformers == []
        assert overview.genre_distribution == {}
        assert overview.revenue_by_genre == {}

    def test_build_overview_zero_investment_no_crash(self, org_id: uuid.UUID):
        """Zero total investment should not cause division by zero."""
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": "Free Book",
                "genre": "romance",
                "monthly_revenue": 100.0,
                "monthly_units": 20,
                "total_revenue": 1200.0,
                "total_investment": 0.0,
                "status": "active",
            },
        ]
        overview = build_portfolio_overview(org_id, books)
        assert overview.portfolio_roi == 0.0  # Graceful fallback
        assert overview.total_books == 1

    def test_build_overview_mixed_status(self, org_id: uuid.UUID):
        """Only active books should contribute to monthly_revenue."""
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": "Active Book",
                "genre": "romance",
                "monthly_revenue": 300.0,
                "monthly_units": 60,
                "total_revenue": 3600.0,
                "total_investment": 500.0,
                "status": "active",
            },
            {
                "book_id": uuid.uuid4(),
                "title": "Archived Book",
                "genre": "thriller",
                "monthly_revenue": 50.0,
                "monthly_units": 10,
                "total_revenue": 600.0,
                "total_investment": 400.0,
                "status": "archived",
            },
        ]
        overview = build_portfolio_overview(org_id, books)
        assert overview.total_books == 2
        assert overview.active_books == 1
        assert overview.monthly_revenue == pytest.approx(300.0, abs=0.01)

    def test_build_overview_single_inactive_book(self, org_id: uuid.UUID):
        """A portfolio with only inactive books should have 0 monthly revenue."""
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": "Paused Book",
                "genre": "scifi",
                "monthly_revenue": 200.0,
                "monthly_units": 40,
                "total_revenue": 2400.0,
                "total_investment": 500.0,
                "status": "paused",
            },
        ]
        overview = build_portfolio_overview(org_id, books)
        assert overview.total_books == 1
        assert overview.active_books == 0
        assert overview.monthly_revenue == 0.0

    def test_build_overview_underperformers_only_with_many_books(self, org_id: uuid.UUID):
        """Underperformers list should be empty when total books <= 5."""
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": f"Book {i}",
                "genre": "romance",
                "monthly_revenue": float(i * 100),
                "monthly_units": i * 20,
                "total_revenue": float(i * 1200),
                "total_investment": 500.0,
                "status": "active",
            }
            for i in range(1, 4)  # 3 books
        ]
        overview = build_portfolio_overview(org_id, books)
        assert overview.underperformers == []  # <= 5 books, so no underperformers

    def test_build_overview_underperformers_with_many_books(self, org_id: uuid.UUID):
        """With >5 books, underperformers should be populated."""
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": f"Book {i}",
                "genre": "romance",
                "monthly_revenue": float(i * 50),
                "monthly_units": i * 10,
                "total_revenue": float(i * 600),
                "total_investment": 500.0,
                "status": "active",
            }
            for i in range(1, 8)  # 7 books
        ]
        overview = build_portfolio_overview(org_id, books)
        assert len(overview.underperformers) > 0


# ---------------------------------------------------------------------------
# Tests: Authentication enforcement
# ---------------------------------------------------------------------------


class TestGetPortfolioOverviewRequiresAuth:
    """Verify the portfolio endpoints enforce authentication.

    The app uses middleware-level authentication. Requests without a valid
    token receive 403 Forbidden. These tests use a bare ASGI client
    (no auth headers) to confirm the auth gate.
    """

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_403(self):
        """Without a token, the middleware returns 403."""
        from httpx import ASGITransport, AsyncClient

        from app.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/portfolio",
                params={"org_id": str(uuid.uuid4())},
            )
        # The app enforces auth middleware: unauthenticated = 403
        assert response.status_code in (401, 403), (
            f"Expected 401 or 403, got {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_recommendations_unauthenticated_returns_403(self):
        """Recommendations GET endpoint should enforce auth like overview."""
        from httpx import ASGITransport, AsyncClient

        from app.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/portfolio/recommendations",
                params={"org_id": str(uuid.uuid4())},
            )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_overview_without_org_id_returns_error(self):
        """Missing org_id on the overview endpoint should not return 200.
        The middleware enforces auth before the route parameter validation."""
        from httpx import ASGITransport, AsyncClient

        from app.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio")
        # Without auth or org_id, the middleware gate returns 403
        assert response.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Tests: Kill/Scale service logic
# ---------------------------------------------------------------------------


class TestKillScaleService:
    """Test the kill/scale decision logic directly."""

    def test_strong_book_gets_scale(self):
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=800.0,
            current_monthly_units=160,
            months_since_launch=6,
            total_investment=600.0,
            total_revenue_to_date=4800.0,
            trend_direction="up",
            review_rating=4.5,
            review_count=150,
        )
        decision = calculate_kill_scale(request)
        assert decision.decision == DecisionType.SCALE
        assert decision.score >= 70

    def test_weak_book_gets_kill(self):
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=10.0,
            current_monthly_units=2,
            months_since_launch=12,
            total_investment=1000.0,
            total_revenue_to_date=200.0,
            trend_direction="down",
            review_rating=2.5,
            review_count=3,
        )
        decision = calculate_kill_scale(request)
        assert decision.decision in (DecisionType.KILL, DecisionType.REVIVE)
        assert decision.score < 45

    def test_series_book_1_protected_from_kill(self):
        """Book 1 of a series should be protected from kill (maintained instead)."""
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=10.0,
            current_monthly_units=2,
            months_since_launch=12,
            total_investment=1000.0,
            total_revenue_to_date=200.0,
            trend_direction="down",
            review_rating=2.5,
            review_count=3,
            is_series=True,
            series_position=1,
        )
        decision = calculate_kill_scale(request)
        assert decision.decision == DecisionType.MAINTAIN
        assert any("series" in r.lower() for r in decision.reasoning)

    def test_decision_has_reasoning_and_actions(self):
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=150.0,
            current_monthly_units=30,
            months_since_launch=6,
            total_investment=800.0,
            total_revenue_to_date=900.0,
            trend_direction="flat",
        )
        decision = calculate_kill_scale(request)
        assert len(decision.reasoning) > 0
        assert len(decision.actions) > 0
        assert isinstance(decision.calculated_at, datetime)

    def test_decision_score_clamped(self):
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=5000.0,
            current_monthly_units=1000,
            months_since_launch=24,
            total_investment=100.0,
            total_revenue_to_date=60000.0,
            trend_direction="up",
            review_rating=5.0,
            review_count=500,
        )
        decision = calculate_kill_scale(request)
        assert 0 <= decision.score <= 100

    def test_confidence_high_with_sufficient_data(self):
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=200.0,
            current_monthly_units=40,
            months_since_launch=8,
            total_investment=500.0,
            total_revenue_to_date=1600.0,
            trend_direction="flat",
            review_count=25,
        )
        decision = calculate_kill_scale(request)
        assert decision.confidence == ConfidenceLevel.HIGH

    def test_confidence_low_with_little_data(self):
        request = KillScaleRequest(
            book_id=uuid.uuid4(),
            current_monthly_revenue=100.0,
            current_monthly_units=20,
            months_since_launch=1,
            total_investment=500.0,
            total_revenue_to_date=100.0,
            trend_direction="flat",
            review_count=2,
        )
        decision = calculate_kill_scale(request)
        assert decision.confidence == ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# Tests: Portfolio recommendations
# ---------------------------------------------------------------------------


class TestPortfolioRecommendations:
    """Test the recommendation generation logic."""

    def test_single_genre_recommends_diversification(self, org_id: uuid.UUID):
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": f"Book {i}",
                "genre": "romance",
                "monthly_revenue": 200.0,
                "monthly_units": 40,
                "total_revenue": 2400.0,
                "total_investment": 500.0,
                "status": "active",
            }
            for i in range(3)
        ]
        overview = build_portfolio_overview(org_id, books)
        recommendations = generate_portfolio_recommendations(overview)
        categories = [r.category for r in recommendations]
        assert "diversification" in categories

    def test_negative_roi_recommends_optimization(self, org_id: uuid.UUID):
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": "Loss Leader",
                "genre": "romance",
                "monthly_revenue": 10.0,
                "monthly_units": 2,
                "total_revenue": 120.0,
                "total_investment": 1000.0,
                "status": "active",
            },
        ]
        overview = build_portfolio_overview(org_id, books)
        recommendations = generate_portfolio_recommendations(overview)
        categories = [r.category for r in recommendations]
        assert "optimization" in categories

    def test_small_portfolio_recommends_growth(self, org_id: uuid.UUID):
        books = [
            {
                "book_id": uuid.uuid4(),
                "title": "Book 1",
                "genre": "romance",
                "monthly_revenue": 500.0,
                "monthly_units": 100,
                "total_revenue": 6000.0,
                "total_investment": 500.0,
                "status": "active",
            },
        ]
        overview = build_portfolio_overview(org_id, books)
        recommendations = generate_portfolio_recommendations(overview)
        categories = [r.category for r in recommendations]
        assert "growth" in categories

    def test_recommendations_have_required_fields(self, org_id: uuid.UUID, sample_books: list[dict]):
        overview = build_portfolio_overview(org_id, sample_books)
        recommendations = generate_portfolio_recommendations(overview)
        for rec in recommendations:
            assert isinstance(rec, PortfolioRecommendation)
            assert rec.category in ("diversification", "optimization", "growth", "risk")
            assert rec.priority in ("high", "medium", "low")
            assert len(rec.title) > 0
            assert len(rec.description) > 0

    def test_empty_portfolio_returns_growth_recommendation(self, org_id: uuid.UUID):
        overview = build_portfolio_overview(org_id, [])
        recommendations = generate_portfolio_recommendations(overview)
        # An empty portfolio (0 books < 5) should recommend growth
        categories = [r.category for r in recommendations]
        assert "growth" in categories
