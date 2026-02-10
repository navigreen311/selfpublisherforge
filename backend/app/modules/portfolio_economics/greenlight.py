"""Pre-writing ROI forecast engine.

Core formula:
    projected_roi = (market_size * capture_rate * price * royalty_rate - costs) / costs * 100

Factors considered:
- Market size estimation from genre data
- Capture rate based on competition and quality signals
- Series multiplier for series books
- Seasonal adjustments
- Risk scoring
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional

from app.modules.portfolio_economics.schemas import (
    GreenlightRequest,
    GreenlightResult,
    ConfidenceLevel,
)


# ─── Genre Market Data (baseline estimates) ───────────────────────────────────

GENRE_MARKET_DATA: dict[str, dict] = {
    "romance": {"monthly_searches": 450000, "avg_price": 4.99, "competition": "high", "base_capture": 0.0003},
    "thriller": {"monthly_searches": 320000, "avg_price": 5.99, "competition": "high", "base_capture": 0.0004},
    "mystery": {"monthly_searches": 280000, "avg_price": 4.99, "competition": "high", "base_capture": 0.0004},
    "sci-fi": {"monthly_searches": 200000, "avg_price": 4.99, "competition": "medium", "base_capture": 0.0006},
    "fantasy": {"monthly_searches": 350000, "avg_price": 5.99, "competition": "high", "base_capture": 0.0004},
    "horror": {"monthly_searches": 150000, "avg_price": 3.99, "competition": "medium", "base_capture": 0.0007},
    "literary_fiction": {"monthly_searches": 120000, "avg_price": 6.99, "competition": "medium", "base_capture": 0.0005},
    "non-fiction": {"monthly_searches": 500000, "avg_price": 9.99, "competition": "high", "base_capture": 0.0003},
    "self-help": {"monthly_searches": 400000, "avg_price": 7.99, "competition": "very_high", "base_capture": 0.0002},
    "children": {"monthly_searches": 250000, "avg_price": 3.99, "competition": "medium", "base_capture": 0.0005},
    "ya": {"monthly_searches": 300000, "avg_price": 4.99, "competition": "high", "base_capture": 0.0004},
    "erotica": {"monthly_searches": 180000, "avg_price": 3.99, "competition": "medium", "base_capture": 0.0008},
    "biography": {"monthly_searches": 100000, "avg_price": 9.99, "competition": "low", "base_capture": 0.0008},
    "business": {"monthly_searches": 350000, "avg_price": 12.99, "competition": "high", "base_capture": 0.0003},
    "default": {"monthly_searches": 100000, "avg_price": 4.99, "competition": "medium", "base_capture": 0.0005},
}

# Series position multipliers (later books get read-through bonus)
SERIES_MULTIPLIER: dict[int, float] = {
    1: 1.0,
    2: 0.65,
    3: 0.55,
    4: 0.50,
    5: 0.45,
}

COMPETITION_CAPTURE_MODIFIER: dict[str, float] = {
    "low": 1.5,
    "medium": 1.0,
    "high": 0.7,
    "very_high": 0.4,
}


def _get_genre_data(genre: str) -> dict:
    """Get market data for a genre, falling back to defaults."""
    normalized = genre.lower().replace(" ", "_").replace("-", "_")
    return GENRE_MARKET_DATA.get(normalized, GENRE_MARKET_DATA["default"])


def _estimate_market_size(request: GreenlightRequest, genre_data: dict) -> int:
    """Estimate monthly market size for the book."""
    if request.market_size_estimate is not None and request.market_size_estimate > 0:
        return request.market_size_estimate
    return genre_data["monthly_searches"]


def _calculate_capture_rate(
    request: GreenlightRequest,
    genre_data: dict,
) -> float:
    """Estimate the capture rate based on genre, competition, and signals."""
    base_rate = genre_data["base_capture"]
    competition = genre_data["competition"]
    modifier = COMPETITION_CAPTURE_MODIFIER.get(competition, 1.0)

    rate = base_rate * modifier

    # Comparable ASINs provide signal -- more comps = better targeting
    if len(request.comparable_asins) >= 3:
        rate *= 1.2
    elif len(request.comparable_asins) >= 1:
        rate *= 1.1

    # Sub-genre targeting typically improves capture
    if request.sub_genre:
        rate *= 1.15

    # Higher marketing budget improves initial capture
    if request.estimated_marketing_budget >= 1000:
        rate *= 1.3
    elif request.estimated_marketing_budget >= 500:
        rate *= 1.15
    elif request.estimated_marketing_budget >= 200:
        rate *= 1.05

    # Cap the capture rate at a reasonable maximum
    return min(rate, 0.005)


def _calculate_series_multiplier(request: GreenlightRequest) -> float:
    """Calculate the revenue multiplier from being in a series."""
    if not request.is_series:
        return 1.0

    position = request.series_position or 1
    # Later books in a series benefit from read-through on earlier books
    if position == 1:
        # First book gets a "series promise" bump -- readers more willing to try
        return 1.15
    else:
        # Later books benefit from existing readership
        base_multiplier = SERIES_MULTIPLIER.get(position, 0.40)
        # But they also get read-through from book 1 buyers
        read_through_bonus = 1.0 + (0.3 / position)
        return base_multiplier * read_through_bonus


def _identify_risk_factors(request: GreenlightRequest, genre_data: dict) -> list[str]:
    """Identify risk factors for the book idea."""
    risks = []

    if genre_data["competition"] in ("high", "very_high"):
        risks.append(f"High competition in {request.genre} genre")

    if request.estimated_price < 2.99:
        risks.append("Price below $2.99 reduces royalty rate to 35%")
    elif request.estimated_price > 9.99:
        risks.append("Price above $9.99 reduces royalty rate to 35% on KDP")

    if request.estimated_production_cost < 200:
        risks.append("Low production budget may affect quality (cover, editing)")

    if request.estimated_marketing_budget < 100:
        risks.append("Minimal marketing budget limits launch visibility")

    if not request.comparable_asins:
        risks.append("No comparable titles provided -- market validation uncertain")

    if request.estimated_word_count < 20000:
        risks.append("Short book length may limit perceived value")
    elif request.estimated_word_count > 200000:
        risks.append("Very long book increases production time and costs")

    if request.is_series and request.series_position and request.series_position > 1:
        risks.append("Later series books depend on existing readership funnel")

    return risks


def _identify_opportunity_factors(
    request: GreenlightRequest, genre_data: dict
) -> list[str]:
    """Identify opportunity factors for the book idea."""
    opportunities = []

    if genre_data["competition"] == "low":
        opportunities.append(f"Low competition in {request.genre} -- easier to gain visibility")

    if request.is_series:
        opportunities.append("Series format provides read-through revenue compounding")

    if request.sub_genre:
        opportunities.append(f"Sub-genre targeting ({request.sub_genre}) may reduce competition")

    if len(request.comparable_asins) >= 3:
        opportunities.append("Multiple comparable titles suggest validated market demand")

    if request.estimated_marketing_budget >= 500:
        opportunities.append("Solid marketing budget supports strong launch")

    if 2.99 <= request.estimated_price <= 4.99:
        opportunities.append("Price point is in the sweet spot for impulse purchases")

    if request.royalty_rate >= 0.7:
        opportunities.append("70% royalty rate maximizes per-unit profit")

    return opportunities


def _generate_suggestions(
    request: GreenlightRequest,
    roi: float,
    breakeven_months: Optional[float],
) -> list[str]:
    """Generate actionable suggestions to improve the ROI."""
    suggestions = []

    if request.estimated_price < 2.99:
        suggestions.append("Consider pricing at $2.99+ to qualify for 70% royalty rate")

    if request.estimated_price > 9.99:
        suggestions.append("Consider pricing at $9.99 or below to maintain 70% royalty rate")

    if not request.is_series:
        suggestions.append("Consider writing this as part of a series to leverage read-through revenue")

    if request.estimated_marketing_budget < 200:
        suggestions.append("Increase launch marketing budget to at least $200 for better initial visibility")

    if roi < 50 and request.estimated_production_cost > 1000:
        suggestions.append("Look for ways to reduce production costs without sacrificing quality")

    if breakeven_months and breakeven_months > 12:
        suggestions.append("Long break-even period; consider lower price or larger marketing push at launch")

    if not request.comparable_asins:
        suggestions.append("Research and add comparable titles to validate market demand")

    return suggestions


def _determine_confidence(request: GreenlightRequest) -> ConfidenceLevel:
    """Determine the confidence level of the forecast."""
    score = 0

    if request.comparable_asins:
        score += len(request.comparable_asins)  # +1 per comp, up to reasonable amount
    if request.sub_genre:
        score += 1
    if request.market_size_estimate and request.market_size_estimate > 0:
        score += 3  # User-provided market data is a strong signal
    if request.is_series:
        score += 1

    if score >= 5:
        return ConfidenceLevel.HIGH
    elif score >= 2:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def calculate_greenlight(request: GreenlightRequest) -> GreenlightResult:
    """Calculate greenlight score and ROI forecast for a book idea.

    Core formula:
        monthly_revenue = market_size * capture_rate * price
        monthly_royalty = monthly_revenue * royalty_rate
        annual_royalty = monthly_royalty * 12 * series_multiplier
        roi = (annual_royalty - total_investment) / total_investment * 100
    """
    genre_data = _get_genre_data(request.genre)

    # Core calculations
    market_size = _estimate_market_size(request, genre_data)
    capture_rate = _calculate_capture_rate(request, genre_data)
    series_mult = _calculate_series_multiplier(request)

    projected_monthly_units = max(1, int(market_size * capture_rate))
    projected_monthly_revenue = projected_monthly_units * request.estimated_price
    projected_monthly_royalty = projected_monthly_revenue * request.royalty_rate

    total_investment = request.estimated_production_cost + request.estimated_marketing_budget
    annual_royalty = projected_monthly_royalty * 12 * series_mult

    if total_investment > 0:
        first_year_roi = ((annual_royalty - total_investment) / total_investment) * 100
        breakeven_months = (
            total_investment / projected_monthly_royalty
            if projected_monthly_royalty > 0 else None
        )
    else:
        first_year_roi = float("inf") if annual_royalty > 0 else 0.0
        breakeven_months = 0.0

    first_year_profit = annual_royalty - total_investment

    # Score calculation (0-100)
    score = 50.0  # Base score

    # ROI contribution (+/- 25 points)
    if first_year_roi > 200:
        score += 25
    elif first_year_roi > 100:
        score += 20
    elif first_year_roi > 50:
        score += 15
    elif first_year_roi > 0:
        score += 5
    elif first_year_roi > -25:
        score -= 5
    elif first_year_roi > -50:
        score -= 15
    else:
        score -= 25

    # Break-even time contribution (+/- 10 points)
    if breakeven_months is not None:
        if breakeven_months <= 2:
            score += 10
        elif breakeven_months <= 6:
            score += 5
        elif breakeven_months <= 12:
            score += 0
        else:
            score -= 10

    # Series bonus (+5)
    if request.is_series:
        score += 5

    # Competition penalty/bonus (+/- 5)
    if genre_data["competition"] == "low":
        score += 5
    elif genre_data["competition"] == "very_high":
        score -= 5

    # Comparable data bonus (+5)
    if len(request.comparable_asins) >= 3:
        score += 5

    # Clamp to 0-100
    score = max(0.0, min(100.0, score))

    # Recommendation
    if score >= 70:
        recommendation = "go"
    elif score >= 45:
        recommendation = "caution"
    else:
        recommendation = "no-go"

    confidence = _determine_confidence(request)
    risk_factors = _identify_risk_factors(request, genre_data)
    opportunity_factors = _identify_opportunity_factors(request, genre_data)
    suggestions = _generate_suggestions(request, first_year_roi, breakeven_months)

    return GreenlightResult(
        title=request.title,
        genre=request.genre,
        greenlight_score=round(score, 1),
        recommendation=recommendation,
        confidence=confidence,
        estimated_market_size=market_size,
        estimated_capture_rate=round(capture_rate, 6),
        projected_monthly_units=projected_monthly_units,
        projected_monthly_revenue=round(projected_monthly_revenue, 2),
        projected_monthly_royalty=round(projected_monthly_royalty, 2),
        total_investment=round(total_investment, 2),
        breakeven_months=round(breakeven_months, 1) if breakeven_months is not None else None,
        first_year_roi=round(first_year_roi, 1),
        first_year_profit=round(first_year_profit, 2),
        risk_factors=risk_factors,
        opportunity_factors=opportunity_factors,
        suggestions=suggestions,
        calculated_at=datetime.now(timezone.utc),
    )
