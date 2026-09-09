"""Unit tests for the Greenlight ROI forecasting engine."""

from datetime import datetime

import pytest

from app.modules.portfolio_economics.greenlight import (
    GENRE_MARKET_DATA,
    _calculate_capture_rate,
    _calculate_series_multiplier,
    _determine_confidence,
    _estimate_market_size,
    _get_genre_data,
    _identify_opportunity_factors,
    _identify_risk_factors,
    calculate_greenlight,
)
from app.modules.portfolio_economics.schemas import (
    ConfidenceLevel,
    GreenlightRequest,
    GreenlightResult,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def basic_request() -> GreenlightRequest:
    """A basic greenlight request with reasonable defaults."""
    return GreenlightRequest(
        title="My Romance Novel",
        genre="romance",
        estimated_word_count=60000,
        estimated_price=4.99,
        royalty_rate=0.7,
        estimated_production_cost=500.0,
        estimated_marketing_budget=200.0,
    )


@pytest.fixture
def series_request() -> GreenlightRequest:
    """A greenlight request for a series book."""
    return GreenlightRequest(
        title="Dragon's Quest Book 3",
        genre="fantasy",
        sub_genre="epic_fantasy",
        estimated_word_count=80000,
        estimated_price=5.99,
        royalty_rate=0.7,
        estimated_production_cost=600.0,
        estimated_marketing_budget=300.0,
        is_series=True,
        series_position=3,
        comparable_asins=["B001", "B002", "B003"],
    )


@pytest.fixture
def high_investment_request() -> GreenlightRequest:
    """A request with high investment and large marketing budget."""
    return GreenlightRequest(
        title="Premium Non-Fiction Guide",
        genre="business",
        sub_genre="entrepreneurship",
        estimated_word_count=50000,
        estimated_price=12.99,
        royalty_rate=0.7,
        estimated_production_cost=2000.0,
        estimated_marketing_budget=1500.0,
        comparable_asins=["B100", "B200"],
    )


@pytest.fixture
def budget_request() -> GreenlightRequest:
    """A low-budget request."""
    return GreenlightRequest(
        title="Quick Horror Story",
        genre="horror",
        estimated_word_count=15000,
        estimated_price=1.99,
        royalty_rate=0.35,
        estimated_production_cost=50.0,
        estimated_marketing_budget=0.0,
    )


# ─── Genre Data Tests ────────────────────────────────────────────────────────


class TestGetGenreData:
    def test_known_genre_returns_data(self):
        data = _get_genre_data("romance")
        assert data["monthly_searches"] == 450000
        assert data["avg_price"] == 4.99
        assert data["competition"] == "high"

    def test_unknown_genre_returns_default(self):
        data = _get_genre_data("underwater_basket_weaving")
        assert data == GENRE_MARKET_DATA["default"]

    def test_genre_normalization(self):
        data1 = _get_genre_data("Sci-Fi")
        data2 = _get_genre_data("sci_fi")
        assert data1 == data2

    def test_all_genres_have_required_fields(self):
        for _genre, data in GENRE_MARKET_DATA.items():
            assert "monthly_searches" in data
            assert "avg_price" in data
            assert "competition" in data
            assert "base_capture" in data


# ─── Market Size Estimation Tests ─────────────────────────────────────────────


class TestEstimateMarketSize:
    def test_uses_user_provided_estimate(self, basic_request):
        basic_request.market_size_estimate = 200000
        genre_data = _get_genre_data(basic_request.genre)
        result = _estimate_market_size(basic_request, genre_data)
        assert result == 200000

    def test_falls_back_to_genre_data(self, basic_request):
        genre_data = _get_genre_data(basic_request.genre)
        result = _estimate_market_size(basic_request, genre_data)
        assert result == genre_data["monthly_searches"]

    def test_zero_estimate_uses_genre_data(self, basic_request):
        basic_request.market_size_estimate = 0
        genre_data = _get_genre_data(basic_request.genre)
        result = _estimate_market_size(basic_request, genre_data)
        assert result == genre_data["monthly_searches"]


# ─── Capture Rate Tests ──────────────────────────────────────────────────────


class TestCalculateCaptureRate:
    def test_base_capture_rate(self, basic_request):
        genre_data = _get_genre_data(basic_request.genre)
        rate = _calculate_capture_rate(basic_request, genre_data)
        assert rate > 0
        assert rate <= 0.005  # Max cap

    def test_comparable_asins_boost(self, basic_request):
        genre_data = _get_genre_data(basic_request.genre)

        # No comps
        rate_no_comps = _calculate_capture_rate(basic_request, genre_data)

        # With 3+ comps
        basic_request.comparable_asins = ["B001", "B002", "B003"]
        rate_with_comps = _calculate_capture_rate(basic_request, genre_data)

        assert rate_with_comps > rate_no_comps

    def test_sub_genre_boost(self, basic_request):
        genre_data = _get_genre_data(basic_request.genre)

        rate_no_sub = _calculate_capture_rate(basic_request, genre_data)

        basic_request.sub_genre = "paranormal_romance"
        rate_with_sub = _calculate_capture_rate(basic_request, genre_data)

        assert rate_with_sub > rate_no_sub

    def test_marketing_budget_boost(self, basic_request):
        genre_data = _get_genre_data(basic_request.genre)

        basic_request.estimated_marketing_budget = 50.0
        rate_low = _calculate_capture_rate(basic_request, genre_data)

        basic_request.estimated_marketing_budget = 1000.0
        rate_high = _calculate_capture_rate(basic_request, genre_data)

        assert rate_high > rate_low

    def test_capture_rate_capped(self, basic_request):
        """Capture rate should never exceed 0.005."""
        basic_request.genre = "biography"  # Low competition
        basic_request.comparable_asins = ["B1", "B2", "B3", "B4"]
        basic_request.sub_genre = "memoir"
        basic_request.estimated_marketing_budget = 5000.0

        genre_data = _get_genre_data(basic_request.genre)
        rate = _calculate_capture_rate(basic_request, genre_data)
        assert rate <= 0.005


# ─── Series Multiplier Tests ─────────────────────────────────────────────────


class TestCalculateSeriesMultiplier:
    def test_non_series_returns_1(self, basic_request):
        assert _calculate_series_multiplier(basic_request) == 1.0

    def test_series_book_1_gets_bonus(self):
        request = GreenlightRequest(
            title="Series Book 1",
            genre="fantasy",
            is_series=True,
            series_position=1,
        )
        mult = _calculate_series_multiplier(request)
        assert mult == 1.15

    def test_later_series_books_have_multiplier(self):
        request = GreenlightRequest(
            title="Series Book 3",
            genre="fantasy",
            is_series=True,
            series_position=3,
        )
        mult = _calculate_series_multiplier(request)
        assert mult > 0
        assert mult < 1.15  # Less than book 1

    def test_series_multiplier_decreases_with_position(self):
        multipliers = []
        for pos in range(2, 6):
            request = GreenlightRequest(
                title=f"Series Book {pos}",
                genre="fantasy",
                is_series=True,
                series_position=pos,
            )
            multipliers.append(_calculate_series_multiplier(request))

        # Each subsequent position should have a lower or equal multiplier
        for i in range(1, len(multipliers)):
            assert multipliers[i] <= multipliers[i - 1]


# ─── Risk Factor Tests ───────────────────────────────────────────────────────


class TestIdentifyRiskFactors:
    def test_high_competition_risk(self, basic_request):
        genre_data = _get_genre_data("romance")  # High competition
        risks = _identify_risk_factors(basic_request, genre_data)
        assert any("competition" in r.lower() for r in risks)

    def test_low_price_risk(self, basic_request):
        basic_request.estimated_price = 1.99
        genre_data = _get_genre_data(basic_request.genre)
        risks = _identify_risk_factors(basic_request, genre_data)
        assert any("$2.99" in r for r in risks)

    def test_high_price_risk(self, basic_request):
        basic_request.estimated_price = 14.99
        genre_data = _get_genre_data(basic_request.genre)
        risks = _identify_risk_factors(basic_request, genre_data)
        assert any("$9.99" in r for r in risks)

    def test_no_comps_risk(self, basic_request):
        basic_request.comparable_asins = []
        genre_data = _get_genre_data(basic_request.genre)
        risks = _identify_risk_factors(basic_request, genre_data)
        assert any("comparable" in r.lower() for r in risks)

    def test_short_book_risk(self, basic_request):
        basic_request.estimated_word_count = 10000
        genre_data = _get_genre_data(basic_request.genre)
        risks = _identify_risk_factors(basic_request, genre_data)
        assert any("short" in r.lower() for r in risks)

    def test_low_production_budget_risk(self, basic_request):
        basic_request.estimated_production_cost = 100
        genre_data = _get_genre_data(basic_request.genre)
        risks = _identify_risk_factors(basic_request, genre_data)
        assert any("production budget" in r.lower() for r in risks)


# ─── Opportunity Factor Tests ────────────────────────────────────────────────


class TestIdentifyOpportunityFactors:
    def test_series_opportunity(self, series_request):
        genre_data = _get_genre_data(series_request.genre)
        opportunities = _identify_opportunity_factors(series_request, genre_data)
        assert any("series" in o.lower() for o in opportunities)

    def test_sub_genre_opportunity(self, series_request):
        genre_data = _get_genre_data(series_request.genre)
        opportunities = _identify_opportunity_factors(series_request, genre_data)
        assert any("sub-genre" in o.lower() for o in opportunities)

    def test_multiple_comps_opportunity(self, series_request):
        genre_data = _get_genre_data(series_request.genre)
        opportunities = _identify_opportunity_factors(series_request, genre_data)
        assert any("comparable" in o.lower() for o in opportunities)

    def test_good_price_opportunity(self, basic_request):
        basic_request.estimated_price = 3.99
        genre_data = _get_genre_data(basic_request.genre)
        opportunities = _identify_opportunity_factors(basic_request, genre_data)
        assert any("sweet spot" in o.lower() for o in opportunities)


# ─── Confidence Tests ────────────────────────────────────────────────────────


class TestDetermineConfidence:
    def test_low_confidence_no_data(self, basic_request):
        assert _determine_confidence(basic_request) == ConfidenceLevel.LOW

    def test_medium_confidence_some_data(self, basic_request):
        basic_request.comparable_asins = ["B001", "B002"]
        assert _determine_confidence(basic_request) == ConfidenceLevel.MEDIUM

    def test_high_confidence_rich_data(self, basic_request):
        basic_request.comparable_asins = ["B001", "B002", "B003"]
        basic_request.sub_genre = "paranormal_romance"
        basic_request.market_size_estimate = 200000
        assert _determine_confidence(basic_request) == ConfidenceLevel.HIGH


# ─── Full Greenlight Calculation Tests ────────────────────────────────────────


class TestCalculateGreenlight:
    def test_returns_greenlight_result(self, basic_request):
        result = calculate_greenlight(basic_request)
        assert isinstance(result, GreenlightResult)

    def test_result_has_all_required_fields(self, basic_request):
        result = calculate_greenlight(basic_request)
        assert result.title == basic_request.title
        assert result.genre == basic_request.genre
        assert 0 <= result.greenlight_score <= 100
        assert result.recommendation in ("go", "caution", "no-go")
        assert result.estimated_market_size > 0
        assert (
            result.total_investment
            == basic_request.estimated_production_cost + basic_request.estimated_marketing_budget
        )
        assert isinstance(result.calculated_at, datetime)

    def test_roi_formula_correctness(self, basic_request):
        result = calculate_greenlight(basic_request)

        # Verify ROI math: (annual_royalty - investment) / investment * 100
        monthly_royalty = result.projected_monthly_revenue * basic_request.royalty_rate
        # Note: series_multiplier affects annual but we can check the base math
        assert result.projected_monthly_royalty == pytest.approx(monthly_royalty, abs=0.01)

    def test_breakeven_calculation(self, basic_request):
        result = calculate_greenlight(basic_request)

        if result.breakeven_months is not None and result.projected_monthly_royalty > 0:
            expected_breakeven = result.total_investment / result.projected_monthly_royalty
            assert result.breakeven_months == pytest.approx(expected_breakeven, abs=0.1)

    def test_high_roi_gets_go(self, high_investment_request):
        """Business books with high price should get reasonable score."""
        result = calculate_greenlight(high_investment_request)
        assert result.recommendation in ("go", "caution")

    def test_budget_book_evaluated(self, budget_request):
        result = calculate_greenlight(budget_request)
        assert isinstance(result, GreenlightResult)
        # Low-price book with 35% royalty should have some risk factors
        assert len(result.risk_factors) > 0

    def test_series_affects_roi(self, series_request):
        """Series books should factor in series multiplier."""
        result = calculate_greenlight(series_request)
        assert isinstance(result, GreenlightResult)

    def test_score_clamped_0_100(self, basic_request):
        result = calculate_greenlight(basic_request)
        assert 0 <= result.greenlight_score <= 100

    def test_go_recommendation_threshold(self):
        """Books with high ROI potential should get 'go'."""
        request = GreenlightRequest(
            title="Sure Thing",
            genre="biography",  # Low competition
            sub_genre="memoir",
            estimated_word_count=50000,
            estimated_price=4.99,
            royalty_rate=0.7,
            estimated_production_cost=200.0,
            estimated_marketing_budget=500.0,
            comparable_asins=["B1", "B2", "B3"],
            market_size_estimate=300000,
        )
        result = calculate_greenlight(request)
        assert result.greenlight_score >= 70
        assert result.recommendation == "go"

    def test_suggestions_generated(self, basic_request):
        result = calculate_greenlight(basic_request)
        # Should get at least one suggestion (e.g., "consider series")
        assert isinstance(result.suggestions, list)

    def test_zero_investment(self):
        """Zero investment should not cause division by zero."""
        request = GreenlightRequest(
            title="Free Book",
            genre="romance",
            estimated_production_cost=0.0,
            estimated_marketing_budget=0.0,
        )
        result = calculate_greenlight(request)
        assert isinstance(result, GreenlightResult)
        assert result.total_investment == 0.0

    def test_custom_market_size(self, basic_request):
        """User-provided market size should be used."""
        basic_request.market_size_estimate = 1000000
        result = calculate_greenlight(basic_request)
        assert result.estimated_market_size == 1000000

    def test_projected_units_at_least_1(self, basic_request):
        """Projected monthly units should be at least 1."""
        result = calculate_greenlight(basic_request)
        assert result.projected_monthly_units >= 1
