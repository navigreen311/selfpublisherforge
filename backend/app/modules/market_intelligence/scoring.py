"""Niche scoring algorithm for the Market Intelligence Engine.

Computes three scores (0-100 each):
  * **demand_score** -- derived from search volume, BSR distribution, and trend
  * **supply_score** -- derived from title count, review barriers, and quality gaps
  * **opportunity_score** -- the composite score:  demand * (1 - supply_difficulty)

Higher opportunity_score means the niche is more attractive.
"""

from __future__ import annotations

import math
import os
import statistics
from dataclasses import dataclass, field

DEMAND_MIDPOINT = int(os.environ.get("MI_DEMAND_MIDPOINT", "5000"))
COMPETITION_MIDPOINT = int(os.environ.get("MI_COMPETITION_MIDPOINT", "50000"))
OPPORTUNITY_MIDPOINT = int(os.environ.get("MI_OPPORTUNITY_MIDPOINT", "500"))


@dataclass
class NicheMetrics:
    """Raw metrics collected for a niche / category."""

    # Demand signals
    avg_monthly_search_volume: float = 0
    bsr_values: list[int] = field(default_factory=list)
    trend_slope: float = 0  # positive = growing, negative = declining

    # Supply signals
    total_competing_titles: int = 0
    avg_review_count: float = 0
    avg_rating: float = 0
    top_10_avg_reviews: float = 0  # avg reviews of top-10 competitors

    # Optional revenue hints
    avg_price: float = 0


@dataclass
class NicheScores:
    demand_score: float = 0
    supply_score: float = 0  # lower = less competition = better for author
    opportunity_score: float = 0
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _sigmoid_scale(x: float, midpoint: float, steepness: float = 1.0) -> float:
    """Return a 0-100 value using a sigmoid centred at *midpoint*."""
    try:
        return 100.0 / (1.0 + math.exp(-steepness * (x - midpoint)))
    except OverflowError:
        return 0.0 if x < midpoint else 100.0


# ---------------------------------------------------------------------------
# Public scoring function
# ---------------------------------------------------------------------------

def calculate_niche_scores(metrics: NicheMetrics) -> NicheScores:
    """Compute demand, supply, and opportunity scores from raw niche metrics."""

    demand = _compute_demand(metrics)
    supply = _compute_supply(metrics)
    opportunity = _compute_opportunity(demand, supply)
    recommendation = _generate_recommendation(demand, supply, opportunity)

    return NicheScores(
        demand_score=round(demand, 2),
        supply_score=round(supply, 2),
        opportunity_score=round(opportunity, 2),
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# Demand score (0-100)  -- higher = more demand
# ---------------------------------------------------------------------------

def _compute_demand(m: NicheMetrics) -> float:
    # 1. Search volume component (40 %)
    #    sigmoid centred at 5000 monthly searches
    sv_score = _sigmoid_scale(m.avg_monthly_search_volume, midpoint=DEMAND_MIDPOINT, steepness=0.0006)

    # 2. BSR component (40 %)
    #    Lower average BSR => more demand
    if m.bsr_values:
        median_bsr = statistics.median(m.bsr_values)
        # sigmoid: median BSR of 50k maps to ~50
        bsr_score = 100 - _sigmoid_scale(median_bsr, midpoint=COMPETITION_MIDPOINT, steepness=0.00004)
    else:
        bsr_score = 50  # neutral when no data

    # 3. Trend component (20 %)
    #    Positive slope is good, negative is bad.
    #    slope of +0.1 => score ~65;  -0.1 => ~35
    trend_score = _clamp(50 + m.trend_slope * 150)

    demand = sv_score * 0.40 + bsr_score * 0.40 + trend_score * 0.20
    return _clamp(demand)


# ---------------------------------------------------------------------------
# Supply score (0-100) -- higher = MORE competition (harder to enter)
# ---------------------------------------------------------------------------

def _compute_supply(m: NicheMetrics) -> float:
    # 1. Title count component (35 %)
    title_score = _sigmoid_scale(m.total_competing_titles, midpoint=OPPORTUNITY_MIDPOINT, steepness=0.006)

    # 2. Review barrier component (40 %)
    #    High average reviews in top-10 means hard to break in
    review_barrier = _sigmoid_scale(m.top_10_avg_reviews, midpoint=200, steepness=0.015)

    # 3. Quality saturation (25 %)
    #    Higher avg rating in the category -> less quality gap
    quality_saturation = _clamp((m.avg_rating / 5.0) * 100) if m.avg_rating else 50

    supply = title_score * 0.35 + review_barrier * 0.40 + quality_saturation * 0.25
    return _clamp(supply)


# ---------------------------------------------------------------------------
# Opportunity score
# ---------------------------------------------------------------------------

def _compute_opportunity(demand: float, supply: float) -> float:
    """opportunity = demand * (1 - supply_difficulty / 100)"""
    supply_difficulty = supply / 100.0
    opp = demand * (1 - supply_difficulty * 0.7)  # 0.7 dampening factor
    return _clamp(opp)


# ---------------------------------------------------------------------------
# Recommendation text
# ---------------------------------------------------------------------------

def _generate_recommendation(demand: float, supply: float, opportunity: float) -> str:
    if opportunity >= 75:
        return (
            "Excellent opportunity. High demand with manageable competition. "
            "Strongly consider entering this niche."
        )
    if opportunity >= 55:
        return (
            "Good opportunity. Solid demand exists but competition is moderate. "
            "Differentiate with quality content and strong positioning."
        )
    if opportunity >= 35:
        return (
            "Moderate opportunity. Demand is present but competition is notable. "
            "Success requires a strong unique angle and marketing effort."
        )
    return (
        "Challenging niche. Either demand is low or competition is very high. "
        "Consider refining your niche or exploring adjacent categories."
    )
