"""Unit tests for the Backlist compounding revenue model."""
import pytest

from app.modules.portfolio_economics.backlist import (
    calculate_backlist_projection,
    _apply_decay,
    _apply_promotion_boost,
    _calculate_series_read_through,
    DEFAULT_MONTHLY_DECAY_RATE,
    PROMOTION_BOOST_MULTIPLIER,
    PROMOTION_FREQUENCY_MONTHS,
    REVENUE_FLOOR_MULTIPLIER,
    SERIES_READ_THROUGH_BASE,
    SERIES_READ_THROUGH_DECAY,
)
from app.modules.portfolio_economics.schemas import (
    BacklistProjection,
    ProjectionPeriod,
)


# ─── Decay Function Tests ────────────────────────────────────────────────────

class TestApplyDecay:
    def test_no_decay_at_month_0(self):
        result = _apply_decay(1000.0, 0, 0.05)
        assert result == 1000.0

    def test_decay_reduces_revenue(self):
        result = _apply_decay(1000.0, 6, 0.05)
        assert result < 1000.0

    def test_decay_has_floor(self):
        """Revenue should never drop below floor."""
        result = _apply_decay(1000.0, 100, 0.05)
        assert result >= 1000.0 * REVENUE_FLOOR_MULTIPLIER

    def test_higher_decay_rate_faster_decline(self):
        slow = _apply_decay(1000.0, 12, 0.03)
        fast = _apply_decay(1000.0, 12, 0.10)
        assert fast < slow

    def test_decay_formula_correctness(self):
        """Verify: base * (1 - rate)^month, but not below floor."""
        base = 1000.0
        rate = 0.05
        month = 3
        expected = base * ((1 - rate) ** month)
        result = _apply_decay(base, month, rate)
        assert result == pytest.approx(expected, abs=0.01)

    def test_zero_base_revenue(self):
        result = _apply_decay(0.0, 12, 0.05)
        assert result == 0.0

    def test_custom_floor_multiplier(self):
        result = _apply_decay(1000.0, 200, 0.1, floor_multiplier=0.3)
        assert result >= 300.0


# ─── Promotion Boost Tests ───────────────────────────────────────────────────

class TestApplyPromotionBoost:
    def test_no_boost_at_month_0(self):
        result = _apply_promotion_boost(0, 100.0)
        assert result == 100.0

    def test_boost_at_promotion_month(self):
        result = _apply_promotion_boost(PROMOTION_FREQUENCY_MONTHS, 100.0)
        assert result == pytest.approx(100.0 * PROMOTION_BOOST_MULTIPLIER)

    def test_tail_after_promotion(self):
        """Month after promotion should have tail effect."""
        result = _apply_promotion_boost(PROMOTION_FREQUENCY_MONTHS + 1, 100.0)
        assert result > 100.0
        assert result < 100.0 * PROMOTION_BOOST_MULTIPLIER

    def test_no_boost_non_promotion_month(self):
        result = _apply_promotion_boost(1, 100.0)
        assert result == 100.0

    def test_multiple_promotion_cycles(self):
        """Verify promotions repeat at the correct interval."""
        promo1 = _apply_promotion_boost(PROMOTION_FREQUENCY_MONTHS, 100.0)
        promo2 = _apply_promotion_boost(PROMOTION_FREQUENCY_MONTHS * 2, 100.0)
        assert promo1 == promo2


# ─── Series Read-Through Tests ───────────────────────────────────────────────

class TestCalculateSeriesReadThrough:
    def test_single_book_no_readthrough(self):
        result = _calculate_series_read_through(1, 100, 4.99, 0.7)
        assert result == 0.0

    def test_two_books_has_readthrough(self):
        result = _calculate_series_read_through(2, 100, 4.99, 0.7)
        assert result > 0.0

    def test_more_books_more_readthrough(self):
        rt_2 = _calculate_series_read_through(2, 100, 4.99, 0.7)
        rt_5 = _calculate_series_read_through(5, 100, 4.99, 0.7)
        assert rt_5 > rt_2

    def test_readthrough_diminishing_returns(self):
        """Each additional book should add less read-through revenue."""
        incremental = []
        for n in range(2, 7):
            prev = _calculate_series_read_through(n - 1, 100, 4.99, 0.7)
            curr = _calculate_series_read_through(n, 100, 4.99, 0.7)
            incremental.append(curr - prev)

        for i in range(1, len(incremental)):
            assert incremental[i] <= incremental[i - 1]

    def test_readthrough_uses_base_rate(self):
        """Book 2 should capture SERIES_READ_THROUGH_BASE of book 1 readers."""
        units = 100
        price = 4.99
        royalty = 0.7
        result = _calculate_series_read_through(2, units, price, royalty)
        expected_book2_units = int(units * SERIES_READ_THROUGH_BASE)
        expected_revenue = expected_book2_units * price * royalty
        assert result == pytest.approx(expected_revenue, abs=1.0)

    def test_zero_units(self):
        result = _calculate_series_read_through(3, 0, 4.99, 0.7)
        assert result == 0.0


# ─── Full Backlist Projection Tests ──────────────────────────────────────────

class TestCalculateBacklistProjection:
    def test_returns_backlist_projection(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        assert isinstance(result, BacklistProjection)

    def test_one_year_has_12_months(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        assert result.months == 12
        assert len(result.monthly_projections) == 12

    def test_three_year_has_36_months(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.THREE_YEAR,
        )
        assert result.months == 36
        assert len(result.monthly_projections) == 36

    def test_five_year_has_60_months(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.FIVE_YEAR,
        )
        assert result.months == 60
        assert len(result.monthly_projections) == 60

    def test_total_revenue_positive(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        assert result.total_projected_revenue > 0.0
        assert result.total_projected_royalty > 0.0

    def test_royalty_rate_applied(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=1000.0,
            royalty_rate=0.7,
            period=ProjectionPeriod.ONE_YEAR,
        )
        # Royalty should be approximately 70% of revenue (with decay)
        ratio = result.total_projected_royalty / result.total_projected_revenue
        assert ratio == pytest.approx(0.7, abs=0.01)

    def test_cumulative_increases_monotonically(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        for i in range(1, len(result.monthly_projections)):
            assert (
                result.monthly_projections[i]["cumulative_revenue"]
                >= result.monthly_projections[i - 1]["cumulative_revenue"]
            )

    def test_decay_reduces_monthly_revenue(self):
        """Monthly revenue should generally decrease due to decay (ignoring promotions)."""
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
            include_promotions=False,
        )
        first_month = result.monthly_projections[0]["revenue"]
        last_month = result.monthly_projections[-1]["revenue"]
        assert last_month <= first_month

    def test_promotions_create_spikes(self):
        """Promotion months should show revenue spikes."""
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
            include_promotions=True,
        )

        # Find promotion months (every PROMOTION_FREQUENCY_MONTHS)
        has_spike = False
        for proj in result.monthly_projections:
            month = proj["month"]
            if month > 0 and month % PROMOTION_FREQUENCY_MONTHS == 0:
                # Previous month (non-promo) should be lower
                prev = result.monthly_projections[month - 2] if month > 1 else None
                if prev:
                    if proj["revenue"] > prev["revenue"]:
                        has_spike = True
                        break

        assert has_spike, "Expected at least one promotion spike"

    def test_series_bonus_increases_revenue(self):
        without_series = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            royalty_rate=0.7,
            period=ProjectionPeriod.ONE_YEAR,
            num_books=3,
            is_series=False,
        )
        with_series = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            royalty_rate=0.7,
            period=ProjectionPeriod.ONE_YEAR,
            num_books=3,
            is_series=True,
            avg_price=4.99,
        )
        assert with_series.total_projected_revenue > without_series.total_projected_revenue

    def test_new_books_increase_revenue(self):
        without_new = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.THREE_YEAR,
            new_books_per_year=0,
        )
        with_new = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.THREE_YEAR,
            new_books_per_year=2,
            new_book_monthly_revenue=300.0,
        )
        assert with_new.total_projected_revenue > without_new.total_projected_revenue

    def test_compounding_factor_calculated(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        assert result.compounding_factor > 0.0

    def test_assumptions_captured(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
            royalty_rate=0.7,
            is_series=True,
        )
        assert "monthly_decay_rate" in result.assumptions
        assert "royalty_rate" in result.assumptions
        assert result.assumptions["is_series"] is True
        assert result.assumptions["royalty_rate"] == 0.7

    def test_average_monthly_revenue_calculated(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        expected_avg = result.total_projected_revenue / 12
        assert result.average_monthly_revenue == pytest.approx(expected_avg, abs=0.01)

    def test_zero_revenue_handled(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=0.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        assert result.total_projected_revenue == 0.0
        assert result.compounding_factor == 1.0

    def test_monthly_projection_structure(self):
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.ONE_YEAR,
        )
        for proj in result.monthly_projections:
            assert "month" in proj
            assert "revenue" in proj
            assert "royalty" in proj
            assert "cumulative_revenue" in proj
            assert "cumulative_royalty" in proj

    def test_revenue_has_floor(self):
        """Even after many months, revenue should not go to zero."""
        result = calculate_backlist_projection(
            current_monthly_revenue=500.0,
            period=ProjectionPeriod.FIVE_YEAR,
            include_promotions=False,
        )
        last_month = result.monthly_projections[-1]["revenue"]
        floor = 500.0 * REVENUE_FLOOR_MULTIPLIER
        assert last_month >= floor - 0.01  # Small tolerance for rounding
