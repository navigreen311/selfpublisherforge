"""Print Cost & Pricing Engine for Specialty Books.

Implements KDP cost formulas, pricing scenario generation, royalty
calculations, ink coverage cost adjustments, margin guardrails, and
a strategy advisor for different book types.

Usage::

    cost = calculate_print_cost(page_count=32, interior_type="premium_color")
    scenarios = generate_price_scenarios(cost, target_margins=[30, 50, 70])
    guardrails = margin_guardrails(list_price=9.99, cost=cost)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# KDP Print Cost Formulas (USD, as of 2026)
# ---------------------------------------------------------------------------

# Per-page rate + fixed cost per book
KDP_COST_FORMULAS: dict[str, dict[str, float]] = {
    "bw": {"per_page": 0.012, "fixed": 0.85},
    "black_white": {"per_page": 0.012, "fixed": 0.85},
    "premium_color": {"per_page": 0.07, "fixed": 0.85},
    "standard_color": {"per_page": 0.04, "fixed": 0.85},
    "color": {"per_page": 0.07, "fixed": 0.85},  # default color → premium
}

# KDP royalty rate for paperback
KDP_ROYALTY_RATE = 0.60

# Minimum viable margin percentage
MIN_VIABLE_MARGIN_PCT = 15.0

# Trim-size surcharge multipliers (applied to per-page cost)
_TRIM_SURCHARGES: dict[str, float] = {
    "8.5x11": 1.0,
    "8.5x8.5": 1.0,
    "6x9": 1.0,
    "5x8": 1.0,
    "5.5x8.5": 1.0,
    "10x8": 1.05,   # landscape slightly higher
    "8x10": 1.05,
    "7x10": 1.0,
}

# Marketplace adjustments (multiplier on base cost)
_MARKETPLACE_MULTIPLIERS: dict[str, float] = {
    "us": 1.0,
    "uk": 1.10,
    "eu": 1.12,
    "ca": 1.05,
    "au": 1.15,
    "jp": 1.20,
}

# Category average prices for strategy advisor
_CATEGORY_AVG_PRICES: dict[str, float] = {
    "childrens": 12.99,
    "coloring": 9.99,
    "puzzle": 8.99,
}


# ---------------------------------------------------------------------------
# Core cost calculation
# ---------------------------------------------------------------------------

def calculate_print_cost(
    page_count: int,
    interior_type: str = "bw",
    trim_size: str = "6x9",
    marketplace: str = "us",
) -> float:
    """Calculate KDP print cost for a book.

    Parameters
    ----------
    page_count:
        Total interior page count.
    interior_type:
        ``"bw"`` | ``"premium_color"`` | ``"standard_color"`` | ``"color"``.
    trim_size:
        Trim size string, e.g. ``"8.5x11"``, ``"6x9"``.
    marketplace:
        Target marketplace: ``"us"``, ``"uk"``, ``"eu"``, ``"ca"``,
        ``"au"``, ``"jp"``.

    Returns
    -------
    Print cost in USD, rounded to 2 decimal places.
    """
    formula = KDP_COST_FORMULAS.get(interior_type.lower())
    if formula is None:
        raise ValueError(
            f"Unknown interior_type '{interior_type}'. "
            f"Valid: {list(KDP_COST_FORMULAS.keys())}"
        )

    per_page = formula["per_page"]
    fixed = formula["fixed"]

    # Trim-size surcharge
    trim_mult = _TRIM_SURCHARGES.get(trim_size, 1.0)
    # Marketplace adjustment
    market_mult = _MARKETPLACE_MULTIPLIERS.get(marketplace.lower(), 1.0)

    cost = (per_page * trim_mult * page_count + fixed) * market_mult
    return round(cost, 2)


# ---------------------------------------------------------------------------
# Pricing scenarios
# ---------------------------------------------------------------------------

def generate_price_scenarios(
    cost: float,
    target_margins: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Generate pricing scenarios for given target margin percentages.

    Uses the KDP 60% royalty model: royalty = list_price * 0.6 - cost.

    Parameters
    ----------
    cost:
        Base print cost in USD.
    target_margins:
        List of desired profit-margin percentages (default [30, 50, 70]).

    Returns
    -------
    List of dicts, each with ``list_price``, ``royalty_rate``,
    ``royalty_amount``, and ``margin_pct``.
    """
    if target_margins is None:
        target_margins = [30, 50, 70]

    scenarios: list[dict[str, Any]] = []
    for margin_pct in sorted(target_margins):
        # royalty = list_price * 0.6 - cost
        # We want royalty / list_price >= margin_pct / 100
        # royalty = margin_pct/100 * list_price
        # => list_price * 0.6 - cost = margin_pct/100 * list_price
        # => list_price * (0.6 - margin_pct/100) = cost
        # => list_price = cost / (0.6 - margin_pct/100)
        divisor = KDP_ROYALTY_RATE - (margin_pct / 100.0)
        if divisor <= 0:
            # Margin target exceeds royalty rate; not achievable
            scenarios.append({
                "list_price": None,
                "royalty_rate": KDP_ROYALTY_RATE,
                "royalty_amount": None,
                "margin_pct": margin_pct,
                "note": (
                    f"A {margin_pct}% margin is not achievable with a "
                    f"{KDP_ROYALTY_RATE * 100:.0f}% royalty rate."
                ),
            })
            continue

        list_price = round(cost / divisor, 2)
        royalty_amount = round(list_price * KDP_ROYALTY_RATE - cost, 2)
        actual_margin = (
            round(royalty_amount / list_price * 100, 1) if list_price > 0 else 0.0
        )

        scenarios.append({
            "list_price": list_price,
            "royalty_rate": KDP_ROYALTY_RATE,
            "royalty_amount": royalty_amount,
            "margin_pct": actual_margin,
        })

    return scenarios


# ---------------------------------------------------------------------------
# Ink coverage cost factor
# ---------------------------------------------------------------------------

def ink_coverage_factor(pages_data: list[dict[str, Any]]) -> float:
    """Calculate a cost-adjustment factor based on average ink coverage.

    Heavy-ink pages can raise actual production cost.  Returns a multiplier
    (1.0 = baseline, up to ~1.25 for very heavy coverage).

    Parameters
    ----------
    pages_data:
        List of page dicts, each with optional ``ink_coverage_percent``
        (0-100 float).

    Returns
    -------
    Adjustment multiplier (>= 1.0).
    """
    if not pages_data:
        return 1.0

    coverages = [
        p.get("ink_coverage_percent", 20.0) for p in pages_data
    ]
    avg_coverage = sum(coverages) / len(coverages)

    # Baseline assumed at 20% coverage; above that, cost rises linearly
    if avg_coverage <= 20.0:
        return 1.0
    # Scale: every +20% coverage adds ~5% to cost, capped at 1.25
    factor = 1.0 + ((avg_coverage - 20.0) / 20.0) * 0.05
    return round(min(factor, 1.25), 4)


# ---------------------------------------------------------------------------
# Margin guardrails
# ---------------------------------------------------------------------------

def margin_guardrails(
    list_price: float,
    cost: float,
) -> dict[str, Any]:
    """Evaluate whether a list price is viable given print cost.

    Returns
    -------
    dict with ``viable``, ``min_price``, ``recommended_price``, ``warnings``.
    """
    royalty = list_price * KDP_ROYALTY_RATE - cost
    margin_pct = (royalty / list_price * 100) if list_price > 0 else 0.0

    # Minimum price: royalty >= 0  →  list_price >= cost / 0.6
    min_price = round(cost / KDP_ROYALTY_RATE, 2)
    # Recommended: at least 30% margin
    rec_divisor = KDP_ROYALTY_RATE - 0.30
    recommended_price = round(cost / rec_divisor, 2) if rec_divisor > 0 else min_price

    warnings: list[str] = []
    viable = True

    if royalty < 0:
        viable = False
        warnings.append(
            f"List price ${list_price:.2f} results in negative royalty "
            f"(${royalty:.2f}). Minimum price is ${min_price:.2f}."
        )
    elif margin_pct < MIN_VIABLE_MARGIN_PCT:
        warnings.append(
            f"Margin is only {margin_pct:.1f}% (below recommended "
            f"{MIN_VIABLE_MARGIN_PCT}%). Consider raising to ${recommended_price:.2f}."
        )

    if list_price > 50.0:
        warnings.append(
            "List price above $50 may reduce conversion on KDP."
        )

    return {
        "viable": viable,
        "min_price": min_price,
        "recommended_price": recommended_price,
        "current_royalty": round(royalty, 2),
        "current_margin_pct": round(margin_pct, 1),
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Strategy advisor
# ---------------------------------------------------------------------------

def strategy_advisor(
    book_type: str,
    page_count: int,
    audience: str = "adults",
    interior_type: str | None = None,
) -> dict[str, Any]:
    """Provide a pricing recommendation based on book type and audience.

    Parameters
    ----------
    book_type:
        ``"childrens"`` | ``"coloring"`` | ``"puzzle"``.
    page_count:
        Total interior page count.
    audience:
        ``"kids"``, ``"teens"``, ``"adults"``, ``"seniors"``.
    interior_type:
        Override interior type; defaults to ``"premium_color"`` for
        children's and ``"bw"`` for coloring/puzzle.

    Returns
    -------
    dict with ``recommended_price``, ``price_range``, ``cost``,
    ``interior_type``, ``notes``.
    """
    # Infer interior type
    if interior_type is None:
        if book_type == "childrens":
            interior_type = "premium_color"
        else:
            interior_type = "bw"

    cost = calculate_print_cost(page_count, interior_type)
    category_avg = _CATEGORY_AVG_PRICES.get(book_type, 9.99)

    # Generate 30% margin scenario
    scenarios = generate_price_scenarios(cost, target_margins=[30])
    rec_price = (
        scenarios[0]["list_price"]
        if scenarios and scenarios[0]["list_price"]
        else category_avg
    )

    # Clamp to category range
    price_floor = max(rec_price, cost / KDP_ROYALTY_RATE + 0.01)
    recommended = round(max(price_floor, category_avg * 0.75), 2)

    notes: list[str] = []
    if book_type == "childrens" and interior_type == "premium_color":
        notes.append(
            "Premium color interiors have high per-page costs. "
            "Keep page count ≤ 32 for best margins."
        )
    if book_type == "coloring":
        notes.append(
            "Coloring books use B&W interior. Single-sided printing means "
            "total page count = 2× coloring pages."
        )
    if audience in ("kids", "teens"):
        notes.append(
            "Lower price points ($5.99-$8.99) perform better for "
            "children/teen audiences on KDP."
        )
    if audience == "seniors":
        notes.append(
            "Large-print editions command a price premium ($9.99-$14.99)."
        )

    return {
        "recommended_price": recommended,
        "price_range": {
            "min": round(price_floor, 2),
            "max": round(category_avg * 1.5, 2),
        },
        "cost": cost,
        "interior_type": interior_type,
        "category_average": category_avg,
        "notes": notes,
    }
