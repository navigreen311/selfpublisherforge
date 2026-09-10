"""Unit tests for the Portfolio Economics calculations.

These are stateless calculations over request models, so the tests call the
real functions rather than patching them.

The previous version of this file patched each function and then asserted on
its own MagicMock's return value, which tested nothing about the code; worse,
the patches never took effect, because `service.py` re-exports the sub-service
functions by binding them at import time. It also called an async, keyword-
argument API (`service.calculate_kill_scale(org_id=..., book_id=...)`) that has
never existed — every real function here takes a request model, and the router
imports them straight from the sub-service modules.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from app.modules.portfolio_economics.backlist import calculate_backlist_projection
from app.modules.portfolio_economics.greenlight import calculate_greenlight
from app.modules.portfolio_economics.portfolio_service import (
    build_portfolio_overview,
    calculate_kill_scale,
    generate_portfolio_recommendations,
)
from app.modules.portfolio_economics.schemas import (
    ChurnPredictionRequest,
    DecisionType,
    GreenlightRequest,
    KillScaleRequest,
    LaunchRecommendRequest,
    ProjectionPeriod,
)
from app.modules.portfolio_economics.seasonal_service import (
    get_niche_seasonality,
    get_seasonal_calendar,
    recommend_launch_date,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def kill_scale_request(**overrides) -> KillScaleRequest:
    payload = {
        "book_id": uuid.uuid4(),
        "current_monthly_revenue": 500.0,
        "current_monthly_units": 100,
        "months_since_launch": 12,
        "total_investment": 2000.0,
        "total_revenue_to_date": 8000.0,
        "monthly_marketing_spend": 50.0,
        "trend_direction": "up",
        "review_rating": 4.5,
        "review_count": 120,
    }
    payload.update(overrides)
    return KillScaleRequest(**payload)


def book_row(**overrides) -> dict:
    payload = {
        "book_id": uuid.uuid4(),
        "title": "A Book",
        "genre": "thriller",
        "monthly_revenue": 400.0,
        "monthly_units": 80,
        "total_revenue": 6000.0,
        "total_investment": 2000.0,
        "launch_date": datetime(2025, 1, 1, tzinfo=UTC),
        # The router maps BookStatus.PUBLISHED to "active" before calling in;
        # monthly_revenue only counts rows in that state.
        "status": "active",
    }
    payload.update(overrides)
    return payload


# ===========================================================================
# calculate_kill_scale
# ===========================================================================


class TestCalculateKillScale:
    def test_strong_performer_is_scaled(self):
        result = calculate_kill_scale(kill_scale_request())

        assert result.decision == DecisionType.SCALE
        assert result.current_roi > 0
        assert 0 <= result.score <= 100

    def test_loss_making_declining_book_is_killed(self):
        result = calculate_kill_scale(
            kill_scale_request(
                current_monthly_revenue=10.0,
                current_monthly_units=2,
                total_investment=5000.0,
                total_revenue_to_date=400.0,
                trend_direction="down",
                review_rating=2.5,
                review_count=6,
            )
        )

        assert result.decision == DecisionType.KILL
        assert result.current_roi < 0

    def test_roi_is_a_percentage_of_investment(self):
        result = calculate_kill_scale(kill_scale_request(total_investment=1000.0, total_revenue_to_date=1500.0))

        # (1500 - 1000) / 1000 * 100
        assert result.current_roi == pytest.approx(50.0)

    def test_zero_investment_does_not_divide_by_zero(self):
        result = calculate_kill_scale(kill_scale_request(total_investment=0.0, total_revenue_to_date=100.0))

        assert result.current_roi == 100.0

    def test_decision_carries_the_book_id(self):
        book_id = uuid.uuid4()
        result = calculate_kill_scale(kill_scale_request(book_id=book_id))

        assert result.book_id == book_id


# ===========================================================================
# build_portfolio_overview / generate_portfolio_recommendations
# ===========================================================================


class TestPortfolioOverview:
    def test_empty_portfolio_returns_zeroed_overview(self):
        org_id = uuid.uuid4()
        overview = build_portfolio_overview(org_id, [])

        assert overview.org_id == org_id
        assert overview.total_books == 0
        assert overview.total_revenue == 0.0

    def test_totals_are_summed_across_books(self):
        overview = build_portfolio_overview(
            uuid.uuid4(),
            [
                book_row(total_revenue=6000.0, total_investment=2000.0, monthly_revenue=400.0),
                book_row(total_revenue=4000.0, total_investment=1000.0, monthly_revenue=200.0),
            ],
        )

        assert overview.total_books == 2
        assert overview.total_revenue == pytest.approx(10000.0)
        assert overview.total_investment == pytest.approx(3000.0)
        assert overview.monthly_revenue == pytest.approx(600.0)

    def test_monthly_revenue_counts_active_books_only(self):
        overview = build_portfolio_overview(
            uuid.uuid4(),
            [
                book_row(monthly_revenue=400.0, status="active"),
                book_row(monthly_revenue=200.0, status="draft"),
            ],
        )

        assert overview.total_books == 2
        assert overview.active_books == 1
        assert overview.monthly_revenue == pytest.approx(400.0)

    def test_single_genre_portfolio_is_told_to_diversify(self):
        overview = build_portfolio_overview(
            uuid.uuid4(),
            [book_row(genre="thriller"), book_row(genre="thriller")],
        )

        recommendations = generate_portfolio_recommendations(overview)

        assert any("divers" in r.title.lower() or "divers" in r.description.lower() for r in recommendations)


# ===========================================================================
# calculate_greenlight
# ===========================================================================


class TestCalculateGreenlight:
    def test_returns_a_scored_recommendation(self):
        result = calculate_greenlight(GreenlightRequest(title="Night Terminal", genre="thriller"))

        assert result.title == "Night Terminal"
        assert 0.0 <= result.greenlight_score <= 100.0
        assert result.recommendation in {"go", "caution", "no-go"}
        assert result.estimated_market_size > 0

    def test_a_costlier_book_never_scores_higher_than_a_cheap_one(self):
        cheap = calculate_greenlight(
            GreenlightRequest(
                title="Cheap", genre="thriller", estimated_production_cost=200.0, estimated_marketing_budget=100.0
            )
        )
        pricey = calculate_greenlight(
            GreenlightRequest(
                title="Pricey", genre="thriller", estimated_production_cost=20000.0, estimated_marketing_budget=10000.0
            )
        )

        assert pricey.greenlight_score <= cheap.greenlight_score


# ===========================================================================
# calculate_backlist_projection
# ===========================================================================


class TestBacklistProjection:
    def test_projects_the_requested_number_of_months(self):
        projection = calculate_backlist_projection(
            current_monthly_revenue=1000.0,
            period=ProjectionPeriod.ONE_YEAR,
        )

        assert projection.months == 12
        assert len(projection.monthly_projections) == 12
        assert projection.total_projected_revenue > 0

    def test_royalty_is_a_share_of_revenue(self):
        projection = calculate_backlist_projection(
            current_monthly_revenue=1000.0,
            royalty_rate=0.7,
            period=ProjectionPeriod.ONE_YEAR,
        )

        assert projection.total_projected_royalty < projection.total_projected_revenue

    def test_revenue_decays_month_over_month_without_new_books(self):
        projection = calculate_backlist_projection(
            current_monthly_revenue=1000.0,
            period=ProjectionPeriod.ONE_YEAR,
            include_promotions=False,
            new_books_per_year=0,
        )

        first = projection.monthly_projections[0]["revenue"]
        last = projection.monthly_projections[-1]["revenue"]
        assert last < first


# ===========================================================================
# Seasonal
# ===========================================================================


class TestSeasonal:
    def test_calendar_is_built_for_the_requested_year(self):
        calendar = get_seasonal_calendar(2026)

        assert calendar.year == 2026
        assert len(calendar.events) > 0

    def test_niche_seasonality_names_peak_and_low_months(self):
        seasonality = get_niche_seasonality("romance")

        assert seasonality.genre == "romance"
        assert len(seasonality.monthly_demand) == 12
        assert seasonality.peak_months
        assert seasonality.low_months
        assert not set(seasonality.peak_months) & set(seasonality.low_months)

    def test_launch_recommendation_is_not_before_the_book_is_ready(self):
        ready = date(2026, 3, 1)
        recommendation = recommend_launch_date(LaunchRecommendRequest(genre="thriller", earliest_ready_date=ready))

        assert recommendation.recommended_date >= ready


# ===========================================================================
# Churn
# ===========================================================================


class TestChurnPrediction:
    def test_a_lapsed_reader_scores_higher_risk_than_an_active_one(self):
        from app.modules.portfolio_economics.audience_service import predict_churn

        active = predict_churn(ChurnPredictionRequest(days_since_last_purchase=5, total_purchases=12))
        lapsed = predict_churn(ChurnPredictionRequest(days_since_last_purchase=400, total_purchases=1))

        assert lapsed.churn_probability > active.churn_probability
