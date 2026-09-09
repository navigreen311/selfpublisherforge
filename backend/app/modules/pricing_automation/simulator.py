"""Revenue impact simulation engine.

Models price elasticity curves and projects sales/revenue at various price points.
Uses standard economic elasticity formula:
    % change in quantity = elasticity * % change in price
"""

from __future__ import annotations

from app.modules.pricing_automation.schemas import (
    BookFormat,
    PricePoint,
    PriceSimulationRequest,
    PriceSimulationResponse,
)

# KDP royalty tiers
ROYALTY_35_RANGE = (0.99, 2.98)
ROYALTY_70_RANGE = (2.99, 9.99)


def _get_royalty_rate(price: float, book_format: BookFormat) -> float:
    """Determine the KDP royalty rate based on price and format.

    For ebooks on Amazon KDP:
      - $0.99 - $2.98  ->  35% royalty
      - $2.99 - $9.99  ->  70% royalty
      - Above $9.99    ->  35% royalty

    Paperback and hardcover typically have different (lower) margins.
    Audiobook royalties vary by platform.
    """
    if book_format == BookFormat.EBOOK:
        if ROYALTY_70_RANGE[0] <= price <= ROYALTY_70_RANGE[1]:
            return 0.70
        return 0.35
    if book_format == BookFormat.PAPERBACK:
        # Approximate: 60% of list - printing cost. Simplified to ~40%.
        return 0.40
    if book_format == BookFormat.HARDCOVER:
        return 0.35
    if book_format == BookFormat.AUDIOBOOK:
        # ACX/Audible typical split
        return 0.40
    return 0.35


def _estimate_sales_change(
    current_price: float,
    new_price: float,
    current_daily_sales: float,
    elasticity: float,
) -> float:
    """Estimate new daily sales using price elasticity of demand.

    Formula: new_sales = current_sales * (1 + elasticity * pct_price_change)
    Elasticity is typically negative (higher price -> lower demand).
    """
    if current_price <= 0:
        return current_daily_sales

    pct_change = (new_price - current_price) / current_price
    new_sales = current_daily_sales * (1.0 + elasticity * pct_change)
    return max(0.0, new_sales)


def _build_price_point(
    price: float,
    daily_sales: float,
    book_format: BookFormat,
    royalty_override: float | None = None,
) -> PricePoint:
    """Build a PricePoint with calculated revenue and royalty metrics."""
    royalty_rate = royalty_override if royalty_override is not None else _get_royalty_rate(price, book_format)
    daily_revenue = price * daily_sales
    daily_royalties = daily_revenue * royalty_rate
    return PricePoint(
        price=round(price, 2),
        estimated_daily_sales=round(daily_sales, 2),
        estimated_daily_revenue=round(daily_revenue, 2),
        estimated_monthly_revenue=round(daily_revenue * 30, 2),
        royalty_rate=round(royalty_rate, 4),
        estimated_daily_royalties=round(daily_royalties, 2),
        estimated_monthly_royalties=round(daily_royalties * 30, 2),
    )


def simulate_price_change(request: PriceSimulationRequest) -> PriceSimulationResponse:
    """Run a full price simulation comparing current vs proposed price.

    Also generates recommended price points across the min-max range.
    """
    current = request.current_price
    proposed = request.proposed_price
    daily_sales = request.current_daily_sales
    elasticity = request.elasticity
    fmt = request.book_format

    # Current metrics
    current_point = _build_price_point(current, daily_sales, fmt, request.royalty_rate)

    # Proposed metrics
    proposed_daily_sales = _estimate_sales_change(current, proposed, daily_sales, elasticity)
    proposed_point = _build_price_point(proposed, proposed_daily_sales, fmt, request.royalty_rate)

    # Revenue & royalty change percentages
    revenue_change_pct = (
        (
            (proposed_point.estimated_monthly_revenue - current_point.estimated_monthly_revenue)
            / current_point.estimated_monthly_revenue
            * 100
        )
        if current_point.estimated_monthly_revenue > 0
        else 0.0
    )
    royalty_change_pct = (
        (
            (proposed_point.estimated_monthly_royalties - current_point.estimated_monthly_royalties)
            / current_point.estimated_monthly_royalties
            * 100
        )
        if current_point.estimated_monthly_royalties > 0
        else 0.0
    )

    # Breakeven sales: how many daily sales at proposed price to match current daily royalties
    proposed_royalty_rate = (
        request.royalty_rate if request.royalty_rate is not None else _get_royalty_rate(proposed, fmt)
    )
    breakeven_sales = (
        current_point.estimated_daily_royalties / (proposed * proposed_royalty_rate)
        if proposed > 0 and proposed_royalty_rate > 0
        else 0.0
    )

    # Generate recommended price points across a useful range
    recommended = _generate_recommended_price_points(
        current_price=current,
        current_daily_sales=daily_sales,
        elasticity=elasticity,
        book_format=fmt,
        royalty_override=request.royalty_rate,
    )

    price_change_pct = ((proposed - current) / current * 100) if current > 0 else 0.0

    return PriceSimulationResponse(
        book_id=request.book_id,
        current_price=current,
        proposed_price=proposed,
        price_change_pct=round(price_change_pct, 2),
        book_format=fmt,
        elasticity=elasticity,
        current_metrics=current_point,
        proposed_metrics=proposed_point,
        revenue_change_pct=round(revenue_change_pct, 2),
        royalty_change_pct=round(royalty_change_pct, 2),
        breakeven_sales=round(breakeven_sales, 2),
        recommended_price_points=recommended,
    )


def _generate_recommended_price_points(
    current_price: float,
    current_daily_sales: float,
    elasticity: float,
    book_format: BookFormat,
    royalty_override: float | None = None,
    num_points: int = 7,
) -> list[PricePoint]:
    """Generate price points across a sensible range around the current price.

    Covers common ebook price points: $0.99, $1.99, $2.99, $3.99, $4.99, $6.99, $9.99
    """
    if book_format == BookFormat.EBOOK:
        candidate_prices = [0.99, 1.99, 2.99, 3.99, 4.99, 6.99, 9.99]
    elif book_format == BookFormat.PAPERBACK:
        candidate_prices = [7.99, 9.99, 12.99, 14.99, 17.99, 19.99, 24.99]
    elif book_format == BookFormat.HARDCOVER:
        candidate_prices = [14.99, 17.99, 19.99, 24.99, 29.99, 34.99, 39.99]
    elif book_format == BookFormat.AUDIOBOOK:
        candidate_prices = [3.99, 6.99, 9.99, 14.99, 19.99, 24.99, 29.99]
    else:
        candidate_prices = [0.99, 2.99, 4.99, 6.99, 9.99, 14.99, 19.99]

    points: list[PricePoint] = []
    for price in candidate_prices:
        daily = _estimate_sales_change(current_price, price, current_daily_sales, elasticity)
        point = _build_price_point(price, daily, book_format, royalty_override)
        points.append(point)

    # Sort by estimated monthly royalties descending
    points.sort(key=lambda p: p.estimated_monthly_royalties, reverse=True)
    return points
