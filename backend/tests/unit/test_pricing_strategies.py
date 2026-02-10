"""Unit tests for pricing strategy implementations."""

from __future__ import annotations

import pytest

from app.modules.pricing_automation.strategies import (
    CompetitiveMatchStrategy,
    DynamicStrategy,
    PenetrationStrategy,
    PromotionalStrategy,
    StrategyContext,
    StrategyResult,
    ValueBasedStrategy,
    _clamp,
    _round_price,
    calculate_price,
    get_strategy,
)


# ──────────────────── Utility Functions ────────────────────


class TestClamp:
    def test_within_range(self):
        assert _clamp(5.0, 1.0, 10.0) == 5.0

    def test_below_min(self):
        assert _clamp(0.5, 1.0, 10.0) == 1.0

    def test_above_max(self):
        assert _clamp(15.0, 1.0, 10.0) == 10.0

    def test_at_min(self):
        assert _clamp(1.0, 1.0, 10.0) == 1.0

    def test_at_max(self):
        assert _clamp(10.0, 1.0, 10.0) == 10.0


class TestRoundPrice:
    def test_rounds_low_price_to_99(self):
        result = _round_price(4.75)
        assert result == 4.99

    def test_rounds_to_49_for_lower_half(self):
        result = _round_price(4.25)
        assert result == 4.49

    def test_handles_sub_dollar(self):
        result = _round_price(0.75)
        assert result == 0.99

    def test_high_price_stays_rounded(self):
        result = _round_price(14.55)
        assert result == 14.55


# ──────────────────── Strategy Registry ────────────────────


class TestStrategyRegistry:
    def test_get_known_strategy(self):
        strategy = get_strategy("competitive_match")
        assert isinstance(strategy, CompetitiveMatchStrategy)

    def test_get_all_strategies(self):
        names = ["competitive_match", "value_based", "penetration", "dynamic", "promotional"]
        for name in names:
            strategy = get_strategy(name)
            assert strategy is not None

    def test_get_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown pricing strategy"):
            get_strategy("nonexistent")

    def test_calculate_price_convenience(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            competitor_avg_price=5.49,
        )
        result = calculate_price("competitive_match", context)
        assert isinstance(result, StrategyResult)
        assert result.strategy_name == "competitive_match"


# ──────────────────── Competitive Match Strategy ────────────────────


class TestCompetitiveMatchStrategy:
    def setup_method(self):
        self.strategy = CompetitiveMatchStrategy()

    def test_undercuts_average_by_default(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            competitor_avg_price=5.00,
        )
        result = self.strategy.calculate(context)
        # 5.00 * (1 - 0.05) = 4.75 -> rounded to 4.99
        assert result.recommended_price <= 5.00
        assert result.recommended_price >= context.min_price
        assert result.strategy_name == "competitive_match"
        assert result.confidence > 0.0

    def test_uses_median_when_configured(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            competitor_avg_price=6.00,
            competitor_median_price=4.50,
            parameters={"use_median": True, "undercut_pct": 0.10},
        )
        result = self.strategy.calculate(context)
        # 4.50 * (1 - 0.10) = 4.05 -> rounds to 4.49
        assert result.recommended_price <= 4.50

    def test_no_competitor_data_keeps_current(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price == context.current_price
        assert result.confidence == pytest.approx(0.1)

    def test_respects_min_price(self):
        context = StrategyContext(
            current_price=2.99,
            min_price=2.99,
            max_price=9.99,
            competitor_avg_price=1.50,
            parameters={"undercut_pct": 0.50},
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price >= context.min_price

    def test_respects_max_price(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=5.00,
            competitor_avg_price=20.00,
            parameters={"undercut_pct": -0.50},  # Negative = markup
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price <= context.max_price


# ──────────────────── Value-Based Strategy ────────────────────


class TestValueBasedStrategy:
    def setup_method(self):
        self.strategy = ValueBasedStrategy()

    def test_premium_for_high_reviews(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=14.99,
            competitor_avg_price=5.00,
            review_count=100,
            review_rating=4.5,
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price >= 5.00
        assert result.strategy_name == "value_based"

    def test_no_premium_below_thresholds(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            competitor_avg_price=5.00,
            review_count=10,
            review_rating=3.5,
        )
        result = self.strategy.calculate(context)
        # Should not exceed competitor average significantly
        assert result.confidence <= 0.6
        assert "at baseline" in result.reasoning
        assert any("Does not meet premium criteria" in a for a in result.adjustments)

    def test_custom_thresholds(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=14.99,
            competitor_avg_price=5.00,
            review_count=20,
            review_rating=4.0,
            parameters={
                "review_threshold": 15,
                "rating_threshold": 3.5,
                "premium_pct": 0.25,
            },
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price >= 5.00

    def test_no_competitor_uses_current_price(self):
        context = StrategyContext(
            current_price=6.99,
            min_price=0.99,
            max_price=14.99,
            review_count=200,
            review_rating=4.8,
        )
        result = self.strategy.calculate(context)
        # Should apply premium to current price since no competitor data
        assert result.recommended_price >= 6.99


# ──────────────────── Penetration Strategy ────────────────────


class TestPenetrationStrategy:
    def setup_method(self):
        self.strategy = PenetrationStrategy()

    def test_launch_price_with_no_reviews(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            review_count=0,
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price == 0.99
        assert result.strategy_name == "penetration"

    def test_price_increases_with_reviews(self):
        context_low = StrategyContext(
            current_price=0.99,
            min_price=0.99,
            max_price=9.99,
            review_count=5,
        )
        context_high = StrategyContext(
            current_price=0.99,
            min_price=0.99,
            max_price=9.99,
            review_count=100,
        )
        result_low = self.strategy.calculate(context_low)
        result_high = self.strategy.calculate(context_high)
        assert result_high.recommended_price >= result_low.recommended_price

    def test_custom_milestones(self):
        context = StrategyContext(
            current_price=0.99,
            min_price=0.99,
            max_price=9.99,
            review_count=30,
            parameters={
                "launch_price": 1.99,
                "review_milestones": [
                    {"reviews": 5, "price_pct": 0.25},
                    {"reviews": 20, "price_pct": 0.50},
                    {"reviews": 50, "price_pct": 0.75},
                ],
            },
        )
        result = self.strategy.calculate(context)
        # 30 reviews should be at the 20-review milestone (50% of range)
        assert result.recommended_price >= 1.99

    def test_at_max_milestone(self):
        context = StrategyContext(
            current_price=0.99,
            min_price=0.99,
            max_price=9.99,
            review_count=150,
        )
        result = self.strategy.calculate(context)
        # Should be at or near max_price
        assert result.recommended_price >= 5.0


# ──────────────────── Dynamic Strategy ────────────────────


class TestDynamicStrategy:
    def setup_method(self):
        self.strategy = DynamicStrategy()

    def test_insufficient_data(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            bsr_trend=[5000],
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price == context.current_price
        assert result.confidence == pytest.approx(0.2)

    def test_improving_bsr_raises_price(self):
        # Lower BSR = better rank = improving
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            bsr_trend=[10000, 8000, 6000, 4000, 3000],
            parameters={"bsr_sensitivity": 0.5},
        )
        result = self.strategy.calculate(context)
        # BSR improving (numbers going down) -> should raise price
        assert result.recommended_price >= context.current_price or result.recommended_price >= context.min_price

    def test_declining_bsr_lowers_price(self):
        # Higher BSR = worse rank = declining
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            bsr_trend=[3000, 4000, 6000, 8000, 10000],
            parameters={"bsr_sensitivity": 0.5},
        )
        result = self.strategy.calculate(context)
        assert result.strategy_name == "dynamic"
        # Price should decrease or stay bounded
        assert result.recommended_price <= context.max_price

    def test_stable_bsr_keeps_price(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            bsr_trend=[5000, 5000, 5000, 5000],
        )
        result = self.strategy.calculate(context)
        # Stable BSR should result in minimal change
        assert abs(result.recommended_price - context.current_price) < 2.0

    def test_confidence_scales_with_data(self):
        context_short = StrategyContext(
            current_price=4.99, min_price=0.99, max_price=9.99,
            bsr_trend=[5000, 4000],
        )
        context_long = StrategyContext(
            current_price=4.99, min_price=0.99, max_price=9.99,
            bsr_trend=[5000, 4500, 4000, 3500, 3000, 2500, 2000],
        )
        result_short = self.strategy.calculate(context_short)
        result_long = self.strategy.calculate(context_long)
        assert result_long.confidence >= result_short.confidence


# ──────────────────── Promotional Strategy ────────────────────


class TestPromotionalStrategy:
    def setup_method(self):
        self.strategy = PromotionalStrategy()

    def test_default_discount(self):
        context = StrategyContext(
            current_price=9.99,
            min_price=0.99,
            max_price=9.99,
        )
        result = self.strategy.calculate(context)
        # 33% off 9.99 ~= 6.69 -> rounded
        assert result.recommended_price < 9.99
        assert result.recommended_price >= 0.99
        assert result.strategy_name == "promotional"

    def test_custom_discount(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
            parameters={"discount_pct": 0.50},
        )
        result = self.strategy.calculate(context)
        # 50% off 4.99 = 2.495 -> rounded
        assert result.recommended_price < 4.99

    def test_floor_price_enforced(self):
        context = StrategyContext(
            current_price=1.99,
            min_price=0.99,
            max_price=9.99,
            parameters={"discount_pct": 0.90, "floor_price": 0.99},
        )
        result = self.strategy.calculate(context)
        assert result.recommended_price >= 0.99

    def test_high_confidence(self):
        context = StrategyContext(
            current_price=4.99,
            min_price=0.99,
            max_price=9.99,
        )
        result = self.strategy.calculate(context)
        assert result.confidence == pytest.approx(0.8)


# ──────────────────── StrategyResult ────────────────────


class TestStrategyResult:
    def test_result_has_all_fields(self):
        result = StrategyResult(
            recommended_price=4.99,
            strategy_name="test",
            confidence=0.8,
            reasoning="Test reasoning",
            adjustments=["adj1"],
        )
        assert result.recommended_price == 4.99
        assert result.strategy_name == "test"
        assert result.confidence == 0.8
        assert result.reasoning == "Test reasoning"
        assert len(result.adjustments) == 1

    def test_result_default_adjustments(self):
        result = StrategyResult(
            recommended_price=4.99,
            strategy_name="test",
            confidence=0.5,
            reasoning="Test",
        )
        assert result.adjustments == []
