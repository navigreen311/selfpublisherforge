"""Unit tests for the Portfolio Economics service layer.

Covers audience personas, portfolio overview, kill/scale decisions,
seasonal analysis, and greenlight/backlist calculations.

All tests use mocked functions -- stateless calculations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.modules.portfolio_economics import service

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def book_id():
    return uuid.uuid4()


# ===========================================================================
# Tests: build_audience_personas
# ===========================================================================


class TestBuildAudiencePersonas:
    """Tests for service.build_audience_personas."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.audience_service.build_audience_personas")
    async def test_returns_audience_personas(
        self,
        mock_build_personas,
        org_id,
        book_id,
    ):
        """build_audience_personas should return list of personas."""
        mock_build_personas.return_value = [
            MagicMock(
                persona_name="Thriller Enthusiast",
                size=5000,
                engagement_score=0.85,
                demographics={"age": "35-50", "gender": "mixed"},
                preferences=["fast pacing", "plot twists"],
            ),
        ]

        result = await service.build_audience_personas(
            org_id=org_id,
            book_id=book_id,
        )

        assert len(result) == 1
        assert result[0].persona_name == "Thriller Enthusiast"
        mock_build_personas.assert_awaited_once()


# ===========================================================================
# Tests: get_audience_growth
# ===========================================================================


class TestGetAudienceGrowth:
    """Tests for service.get_audience_growth."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.audience_service.get_audience_growth")
    async def test_returns_audience_growth_data(
        self,
        mock_get_audience_growth,
        org_id,
        book_id,
    ):
        """get_audience_growth should return growth metrics."""
        mock_get_audience_growth.return_value = MagicMock(
            total_audience=10000,
            growth_rate=0.15,
            churn_rate=0.05,
            net_growth=1000,
        )

        result = await service.get_audience_growth(
            org_id=org_id,
            book_id=book_id,
            period_days=30,
        )

        assert result.total_audience == 10000
        assert result.growth_rate == 0.15
        mock_get_audience_growth.assert_awaited_once()


# ===========================================================================
# Tests: predict_churn
# ===========================================================================


class TestPredictChurn:
    """Tests for service.predict_churn."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.audience_service.predict_churn")
    async def test_returns_churn_prediction(
        self,
        mock_predict_churn,
        org_id,
        book_id,
    ):
        """predict_churn should return churn prediction."""
        mock_predict_churn.return_value = MagicMock(
            churn_probability=0.25,
            risk_factors=["low engagement", "no recent purchases"],
            recommendations=["Email campaign", "Discount offer"],
        )

        result = await service.predict_churn(
            org_id=org_id,
            book_id=book_id,
        )

        assert result.churn_probability == 0.25
        assert len(result.risk_factors) == 2
        mock_predict_churn.assert_awaited_once()


# ===========================================================================
# Tests: build_portfolio_overview
# ===========================================================================


class TestBuildPortfolioOverview:
    """Tests for service.build_portfolio_overview."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.portfolio_service.build_portfolio_overview")
    async def test_returns_portfolio_overview(
        self,
        mock_build_overview,
        org_id,
    ):
        """build_portfolio_overview should return portfolio metrics."""
        mock_build_overview.return_value = MagicMock(
            total_books=15,
            total_revenue=Decimal("50000.00"),
            avg_revenue_per_book=Decimal("3333.33"),
            top_performer_id=uuid.uuid4(),
            underperformers=[],
        )

        result = await service.build_portfolio_overview(org_id=org_id)

        assert result.total_books == 15
        assert result.total_revenue == Decimal("50000.00")
        mock_build_overview.assert_awaited_once()


# ===========================================================================
# Tests: calculate_kill_scale
# ===========================================================================


class TestCalculateKillScale:
    """Tests for service.calculate_kill_scale."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.portfolio_service.calculate_kill_scale")
    async def test_returns_kill_scale_decision(
        self,
        mock_calculate_kill_scale,
        org_id,
        book_id,
    ):
        """calculate_kill_scale should return decision recommendation."""
        mock_calculate_kill_scale.return_value = MagicMock(
            book_id=book_id,
            decision="scale",
            confidence=0.85,
            reasoning="Strong performance with high ROI",
            metrics={
                "roi": 3.5,
                "revenue_trend": "up",
                "review_velocity": "high",
            },
        )

        result = await service.calculate_kill_scale(
            org_id=org_id,
            book_id=book_id,
        )

        assert result.decision == "scale"
        assert result.confidence == 0.85
        mock_calculate_kill_scale.assert_awaited_once()


# ===========================================================================
# Tests: generate_portfolio_recommendations
# ===========================================================================


class TestGeneratePortfolioRecommendations:
    """Tests for service.generate_portfolio_recommendations."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.portfolio_service.generate_portfolio_recommendations")
    async def test_returns_portfolio_recommendations(
        self,
        mock_generate_recommendations,
        org_id,
    ):
        """generate_portfolio_recommendations should return actionable recommendations."""
        mock_generate_recommendations.return_value = [
            MagicMock(
                category="diversification",
                recommendation="Expand into romance genre",
                priority="high",
                expected_impact="15% revenue increase",
            ),
            MagicMock(
                category="optimization",
                recommendation="Sunset underperforming series",
                priority="medium",
                expected_impact="Reduce overhead by 10%",
            ),
        ]

        result = await service.generate_portfolio_recommendations(org_id=org_id)

        assert len(result) == 2
        assert result[0].category == "diversification"
        mock_generate_recommendations.assert_awaited_once()


# ===========================================================================
# Tests: get_seasonal_calendar
# ===========================================================================


class TestGenerateSeasonalCalendar:
    """Tests for service.get_seasonal_calendar."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.seasonal_service.get_seasonal_calendar")
    async def test_returns_seasonal_calendar(
        self,
        mock_generate_calendar,
    ):
        """get_seasonal_calendar should return calendar with peak periods."""
        mock_generate_calendar.return_value = MagicMock(
            niche="romance",
            peak_months=["February", "December"],
            low_months=["August"],
            events=[
                MagicMock(
                    name="Valentine's Day",
                    date=datetime(2025, 2, 14, tzinfo=UTC),
                    impact="high",
                ),
            ],
        )

        result = await service.get_seasonal_calendar(niche="romance", year=2025)

        assert result.niche == "romance"
        assert len(result.peak_months) == 2
        mock_generate_calendar.assert_awaited_once()


# ===========================================================================
# Tests: get_niche_seasonality
# ===========================================================================


class TestGetNicheSeasonality:
    """Tests for service.get_niche_seasonality."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.seasonal_service.get_niche_seasonality")
    async def test_returns_niche_seasonality_data(
        self,
        mock_get_seasonality,
        org_id,
    ):
        """get_niche_seasonality should return seasonality metrics."""
        mock_get_seasonality.return_value = MagicMock(
            niche="thriller",
            seasonal_index_by_month={
                "January": 0.8,
                "February": 0.9,
                "March": 1.2,
            },
            best_launch_months=["March", "October"],
        )

        result = await service.get_niche_seasonality(org_id=org_id, niche="thriller")

        assert result.niche == "thriller"
        assert len(result.best_launch_months) == 2
        mock_get_seasonality.assert_awaited_once()


# ===========================================================================
# Tests: recommend_launch_date
# ===========================================================================


class TestGenerateLaunchRecommendations:
    """Tests for service.recommend_launch_date."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.seasonal_service.recommend_launch_date")
    async def test_returns_launch_recommendations(
        self,
        mock_recommend_launch_date,
    ):
        """recommend_launch_date should return recommended launch dates."""
        mock_recommend_launch_date.return_value = [
            MagicMock(
                recommended_date=datetime(2025, 10, 1, tzinfo=UTC),
                reasoning="High seasonal demand for thriller genre",
                expected_impact=0.3,
            ),
        ]

        result = await service.recommend_launch_date(
            niche="thriller",
            current_date=datetime(2025, 8, 1, tzinfo=UTC),
        )

        assert len(result) == 1
        assert result[0].reasoning is not None
        mock_recommend_launch_date.assert_awaited_once()


# ===========================================================================
# Tests: calculate_backlist_projection
# ===========================================================================


class TestCalculateBacklistProjection:
    """Tests for service.calculate_backlist_projection."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.backlist.calculate_backlist_projection")
    async def test_returns_backlist_projection(
        self,
        mock_calculate_backlist,
        org_id,
        book_id,
    ):
        """calculate_backlist_projection should return revenue projections."""
        mock_calculate_backlist.return_value = MagicMock(
            book_id=book_id,
            projected_revenue_12_months=Decimal("5000.00"),
            decay_rate=0.05,
            monthly_projections=[
                MagicMock(month=1, revenue=Decimal("500.00")),
                MagicMock(month=2, revenue=Decimal("475.00")),
            ],
        )

        result = await service.calculate_backlist_projection(
            org_id=org_id,
            book_id=book_id,
            months=12,
        )

        assert result.projected_revenue_12_months == Decimal("5000.00")
        assert len(result.monthly_projections) == 2
        mock_calculate_backlist.assert_awaited_once()


# ===========================================================================
# Tests: calculate_greenlight
# ===========================================================================


class TestCalculateGreenlight:
    """Tests for service.calculate_greenlight."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.greenlight.calculate_greenlight")
    async def test_returns_greenlight_decision(
        self,
        mock_calculate_greenlight,
    ):
        """calculate_greenlight should return go/no-go recommendation."""
        mock_calculate_greenlight.return_value = MagicMock(
            decision="greenlight",
            confidence=0.78,
            estimated_roi=2.5,
            break_even_units=500,
            reasoning="Strong market demand and low competition",
            risk_factors=["Seasonal dependency"],
        )

        result = await service.calculate_greenlight(
            niche="thriller",
            estimated_production_cost=Decimal("2000.00"),
            target_price=Decimal("4.99"),
            estimated_market_size=50000,
        )

        assert result.decision == "greenlight"
        assert result.confidence == 0.78
        mock_calculate_greenlight.assert_awaited_once()


# ===========================================================================
# Tests: build_also_bought_intelligence
# ===========================================================================


class TestBuildAlsoBoughtIntelligence:
    """Tests for service.build_also_bought_intelligence."""

    @pytest.mark.asyncio
    @patch("app.modules.portfolio_economics.audience_service.build_also_bought_intelligence")
    async def test_returns_also_bought_intelligence(
        self,
        mock_build_also_bought,
        org_id,
        book_id,
    ):
        """build_also_bought_intelligence should return cross-sell insights."""
        mock_build_also_bought.return_value = MagicMock(
            book_id=book_id,
            top_also_bought=[
                MagicMock(title="Related Book 1", frequency=150),
                MagicMock(title="Related Book 2", frequency=120),
            ],
            cross_sell_opportunities=["Bundle with Related Book 1"],
        )

        result = await service.build_also_bought_intelligence(
            org_id=org_id,
            book_id=book_id,
        )

        assert len(result.top_also_bought) == 2
        assert len(result.cross_sell_opportunities) > 0
        mock_build_also_bought.assert_awaited_once()
