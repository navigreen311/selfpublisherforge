"""Pricing strategy implementations.

Each strategy calculates a recommended price based on different market signals:
- Competitive Match: match or undercut category average
- Value-Based: premium pricing for high-review books
- Penetration: low launch price, raise after reviews accumulate
- Dynamic: adjust based on BSR trends
- Promotional: scheduled price drops for visibility
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyContext:
    """Contextual data available to pricing strategies."""

    current_price: float
    min_price: float
    max_price: float
    book_format: str = "ebook"
    # Competitor data
    competitor_avg_price: float | None = None
    competitor_median_price: float | None = None
    competitor_min_price: float | None = None
    competitor_max_price: float | None = None
    # Book metrics
    review_count: int = 0
    review_rating: float = 0.0
    bsr_rank: int | None = None
    bsr_trend: list[int] = field(default_factory=list)  # recent BSR values
    days_since_launch: int = 0
    # Custom parameters from the rule
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyResult:
    """Output from a pricing strategy calculation."""

    recommended_price: float
    strategy_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    adjustments: list[str] = field(default_factory=list)


def _clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(value, max_val))


def _round_price(price: float) -> float:
    """Round to common book pricing (e.g., $X.99 pattern)."""
    rounded = round(price, 2)
    # Snap to .99 endings for ebooks under $10
    if rounded < 10.0:
        base = math.floor(rounded)
        if rounded - base > 0.50:
            return base + 0.99
        return base + 0.49 if base > 0 else 0.99
    return rounded


class PricingStrategy(ABC):
    """Base class for all pricing strategies."""

    @abstractmethod
    def calculate(self, context: StrategyContext) -> StrategyResult:
        """Calculate the recommended price given the context."""
        ...


class CompetitiveMatchStrategy(PricingStrategy):
    """Match or undercut the category average price.

    Parameters (from context.parameters):
        undercut_pct (float): Percentage to undercut the average. Default 0.05 (5%).
        use_median (bool): Use median instead of average. Default False.
    """

    def calculate(self, context: StrategyContext) -> StrategyResult:
        undercut_pct = context.parameters.get("undercut_pct", 0.05)
        use_median = context.parameters.get("use_median", False)

        reference_price = context.competitor_median_price if use_median else context.competitor_avg_price
        adjustments: list[str] = []

        if reference_price is None:
            return StrategyResult(
                recommended_price=context.current_price,
                strategy_name="competitive_match",
                confidence=0.1,
                reasoning="No competitor data available; keeping current price.",
            )

        target = reference_price * (1.0 - undercut_pct)
        adjustments.append(
            f"Undercut {'median' if use_median else 'average'} (${reference_price:.2f}) by {undercut_pct*100:.0f}%"
        )

        recommended = _clamp(_round_price(target), context.min_price, context.max_price)
        confidence = 0.7 if reference_price else 0.3

        return StrategyResult(
            recommended_price=recommended,
            strategy_name="competitive_match",
            confidence=confidence,
            reasoning=(
                f"Competitive match targets {undercut_pct*100:.0f}% below the "
                f"{'median' if use_median else 'average'} competitor price of "
                f"${reference_price:.2f}, yielding ${recommended:.2f}."
            ),
            adjustments=adjustments,
        )


class ValueBasedStrategy(PricingStrategy):
    """Premium pricing for books with strong reviews.

    Parameters:
        review_threshold (int): Minimum reviews for premium pricing. Default 50.
        rating_threshold (float): Minimum rating for premium pricing. Default 4.0.
        premium_pct (float): Percentage premium over competitor average. Default 0.15.
    """

    def calculate(self, context: StrategyContext) -> StrategyResult:
        review_threshold = context.parameters.get("review_threshold", 50)
        rating_threshold = context.parameters.get("rating_threshold", 4.0)
        premium_pct = context.parameters.get("premium_pct", 0.15)

        adjustments: list[str] = []
        base_price = context.competitor_avg_price or context.current_price

        qualifies_for_premium = context.review_count >= review_threshold and context.review_rating >= rating_threshold

        if qualifies_for_premium:
            # Scale premium based on how far above thresholds
            review_factor = min(context.review_count / (review_threshold * 5), 1.0)
            rating_factor = min((context.review_rating - rating_threshold) / (5.0 - rating_threshold), 1.0)
            effective_premium = premium_pct * (0.5 + 0.25 * review_factor + 0.25 * rating_factor)
            target = base_price * (1.0 + effective_premium)
            adjustments.append(
                f"Premium of {effective_premium*100:.1f}% applied "
                f"({context.review_count} reviews, {context.review_rating:.1f} rating)"
            )
            confidence = 0.7 + 0.2 * review_factor
        else:
            target = base_price
            adjustments.append(
                f"Does not meet premium criteria "
                f"({context.review_count}/{review_threshold} reviews, "
                f"{context.review_rating:.1f}/{rating_threshold:.1f} rating)"
            )
            confidence = 0.5

        recommended = _clamp(_round_price(target), context.min_price, context.max_price)

        return StrategyResult(
            recommended_price=recommended,
            strategy_name="value_based",
            confidence=confidence,
            reasoning=(
                f"Value-based pricing {'applies premium' if qualifies_for_premium else 'at baseline'} "
                f"of ${recommended:.2f} based on {context.review_count} reviews "
                f"and {context.review_rating:.1f} average rating."
            ),
            adjustments=adjustments,
        )


class PenetrationStrategy(PricingStrategy):
    """Low launch price that increases as reviews accumulate.

    Parameters:
        launch_price (float): Initial low price. Default 0.99.
        review_milestones (list[dict]): List of {reviews: int, price_pct: float}.
            Default milestones at 10, 25, 50, 100 reviews.
    """

    DEFAULT_MILESTONES = [
        {"reviews": 10, "price_pct": 0.50},
        {"reviews": 25, "price_pct": 0.70},
        {"reviews": 50, "price_pct": 0.85},
        {"reviews": 100, "price_pct": 1.00},
    ]

    def calculate(self, context: StrategyContext) -> StrategyResult:
        launch_price = context.parameters.get("launch_price", 0.99)
        milestones = context.parameters.get("review_milestones", self.DEFAULT_MILESTONES)
        adjustments: list[str] = []

        # Determine the applicable milestone
        price_pct = 0.0
        active_milestone = None
        for milestone in sorted(milestones, key=lambda m: m["reviews"]):
            if context.review_count >= milestone["reviews"]:
                price_pct = milestone["price_pct"]
                active_milestone = milestone
            else:
                break

        if active_milestone is None:
            # Below first milestone, use launch price
            target = launch_price
            adjustments.append(f"Below first milestone; using launch price ${launch_price:.2f}")
            confidence = 0.8
        else:
            target_range = context.max_price - launch_price
            target = launch_price + (target_range * price_pct)
            adjustments.append(
                f"Milestone reached: {active_milestone['reviews']} reviews -> " f"{price_pct*100:.0f}% of target range"
            )
            confidence = 0.7

        recommended = _clamp(_round_price(target), context.min_price, context.max_price)

        return StrategyResult(
            recommended_price=recommended,
            strategy_name="penetration",
            confidence=confidence,
            reasoning=(
                f"Penetration pricing at ${recommended:.2f} based on "
                f"{context.review_count} reviews (launch: ${launch_price:.2f}, "
                f"target max: ${context.max_price:.2f})."
            ),
            adjustments=adjustments,
        )


class DynamicStrategy(PricingStrategy):
    """Adjust price based on BSR (Best Sellers Rank) trends.

    Parameters:
        bsr_sensitivity (float): How aggressively to react. Default 0.5.
        lookback_window (int): Number of BSR data points for trend. Default 7.
    """

    def calculate(self, context: StrategyContext) -> StrategyResult:
        bsr_sensitivity = context.parameters.get("bsr_sensitivity", 0.5)
        adjustments: list[str] = []

        if not context.bsr_trend or len(context.bsr_trend) < 2:
            return StrategyResult(
                recommended_price=context.current_price,
                strategy_name="dynamic",
                confidence=0.2,
                reasoning="Insufficient BSR trend data for dynamic pricing.",
            )

        # Calculate BSR trend: lower BSR = better rank = more sales
        recent = context.bsr_trend[-3:] if len(context.bsr_trend) >= 3 else context.bsr_trend
        older = context.bsr_trend[: -len(recent)] if len(context.bsr_trend) > len(recent) else recent

        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)

        bsr_change = 0.0 if avg_older == 0 else (avg_recent - avg_older) / avg_older

        # Negative bsr_change means rank improved (lower number = better)
        # If rank improved: we can raise price slightly
        # If rank worsened: we should lower price to boost sales
        price_adjustment = -bsr_change * bsr_sensitivity

        # Cap adjustment at +/- 20%
        price_adjustment = max(-0.20, min(0.20, price_adjustment))
        target = context.current_price * (1.0 + price_adjustment)

        adjustments.append(
            f"BSR trend: {'improving' if bsr_change < 0 else 'declining'} "
            f"({bsr_change*100:+.1f}%) -> price adjustment: {price_adjustment*100:+.1f}%"
        )

        recommended = _clamp(_round_price(target), context.min_price, context.max_price)
        confidence = min(0.8, 0.4 + 0.1 * len(context.bsr_trend))

        return StrategyResult(
            recommended_price=recommended,
            strategy_name="dynamic",
            confidence=confidence,
            reasoning=(
                f"Dynamic pricing adjusts from ${context.current_price:.2f} to "
                f"${recommended:.2f} based on BSR trend "
                f"({'improving' if bsr_change < 0 else 'declining'})."
            ),
            adjustments=adjustments,
        )


class PromotionalStrategy(PricingStrategy):
    """Calculate promotional pricing for visibility boosts.

    Parameters:
        discount_pct (float): Discount percentage. Default 0.33.
        floor_price (float): Minimum promotional price. Default 0.99.
    """

    def calculate(self, context: StrategyContext) -> StrategyResult:
        discount_pct = context.parameters.get("discount_pct", 0.33)
        floor_price = context.parameters.get("floor_price", 0.99)
        adjustments: list[str] = []

        target = context.current_price * (1.0 - discount_pct)
        adjustments.append(f"Applied {discount_pct*100:.0f}% promotional discount")

        if target < floor_price:
            target = floor_price
            adjustments.append(f"Adjusted to floor price ${floor_price:.2f}")

        recommended = _clamp(_round_price(target), context.min_price, context.max_price)

        return StrategyResult(
            recommended_price=recommended,
            strategy_name="promotional",
            confidence=0.8,
            reasoning=(
                f"Promotional pricing: ${context.current_price:.2f} -> "
                f"${recommended:.2f} ({discount_pct*100:.0f}% off for visibility boost)."
            ),
            adjustments=adjustments,
        )


# ──────────────────── Strategy Registry ────────────────────

STRATEGY_MAP: dict[str, type[PricingStrategy]] = {
    "competitive_match": CompetitiveMatchStrategy,
    "value_based": ValueBasedStrategy,
    "penetration": PenetrationStrategy,
    "dynamic": DynamicStrategy,
    "promotional": PromotionalStrategy,
}


def get_strategy(strategy_name: str) -> PricingStrategy:
    """Get a strategy instance by name.

    Args:
        strategy_name: One of the registered strategy names.

    Returns:
        An instance of the requested PricingStrategy.

    Raises:
        ValueError: If the strategy name is not recognized.
    """
    cls = STRATEGY_MAP.get(strategy_name)
    if cls is None:
        raise ValueError(f"Unknown pricing strategy '{strategy_name}'. " f"Available: {list(STRATEGY_MAP.keys())}")
    return cls()


def calculate_price(strategy_name: str, context: StrategyContext) -> StrategyResult:
    """Convenience function to calculate price using a named strategy."""
    strategy = get_strategy(strategy_name)
    return strategy.calculate(context)
