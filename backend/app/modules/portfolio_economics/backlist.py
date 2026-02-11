"""Backlist compounding revenue model.

Models how a backlist of books generates compounding revenue over time,
accounting for:
- Monthly decay rate (natural sales decline over time)
- Promotion boosts (periodic sales spikes from promotions)
- Series multiplier (read-through revenue from series)
- New title injection (adding new books to the portfolio)
"""

from app.modules.portfolio_economics.schemas import (
    BacklistProjection,
    ProjectionPeriod,
)

# ─── Constants ────────────────────────────────────────────────────────────────

# Monthly decay rate for organic book sales (sales decline after launch)
DEFAULT_MONTHLY_DECAY_RATE = 0.05  # 5% monthly decline in organic sales

# Promotion boost parameters
PROMOTION_BOOST_MULTIPLIER = 2.5   # Spike during promotion month
PROMOTION_FREQUENCY_MONTHS = 3     # How often promotions occur
PROMOTION_TAIL_MONTHS = 1          # How long the tail effect lasts
PROMOTION_TAIL_MULTIPLIER = 1.3    # Multiplier during tail period

# Series read-through parameters
SERIES_READ_THROUGH_BASE = 0.65    # % of book 1 buyers who buy book 2
SERIES_READ_THROUGH_DECAY = 0.85   # Each subsequent book retains this % of previous

# New book launch parameters
NEW_BOOK_LAUNCH_MULTIPLIER = 3.0   # Initial sales spike for new release
NEW_BOOK_LAUNCH_DECAY_MONTHS = 3   # Months until new book settles to baseline

# Floor on monthly revenue -- books never fully die
REVENUE_FLOOR_MULTIPLIER = 0.15    # Minimum 15% of peak revenue


PERIOD_MONTHS: dict[ProjectionPeriod, int] = {
    ProjectionPeriod.ONE_YEAR: 12,
    ProjectionPeriod.THREE_YEAR: 36,
    ProjectionPeriod.FIVE_YEAR: 60,
}


def _apply_decay(
    base_revenue: float,
    month: int,
    decay_rate: float,
    floor_multiplier: float = REVENUE_FLOOR_MULTIPLIER,
) -> float:
    """Apply monthly decay to revenue with a floor.

    Revenue decays exponentially but never drops below floor_multiplier * base.
    """
    decayed = base_revenue * ((1 - decay_rate) ** month)
    floor = base_revenue * floor_multiplier
    return max(decayed, floor)


def _apply_promotion_boost(month: int, base_monthly: float) -> float:
    """Calculate promotion boost for a given month."""
    # Promotion every PROMOTION_FREQUENCY_MONTHS months
    if month > 0 and month % PROMOTION_FREQUENCY_MONTHS == 0:
        return base_monthly * PROMOTION_BOOST_MULTIPLIER
    # Tail effect in the month after a promotion
    if month > 1 and (month - 1) % PROMOTION_FREQUENCY_MONTHS == 0:
        return base_monthly * PROMOTION_TAIL_MULTIPLIER
    return base_monthly


def _calculate_series_read_through(
    book_count: int,
    book1_monthly_units: int,
    avg_price: float,
    royalty_rate: float,
) -> float:
    """Calculate additional monthly revenue from series read-through.

    Each subsequent book gets a percentage of book 1 buyers based on
    read-through rates.
    """
    if book_count <= 1:
        return 0.0

    additional_revenue = 0.0
    current_read_through = SERIES_READ_THROUGH_BASE

    for position in range(2, book_count + 1):
        additional_units = int(book1_monthly_units * current_read_through)
        additional_revenue += additional_units * avg_price * royalty_rate
        current_read_through *= SERIES_READ_THROUGH_DECAY

    return additional_revenue


def calculate_backlist_projection(
    current_monthly_revenue: float,
    royalty_rate: float = 0.7,
    period: ProjectionPeriod = ProjectionPeriod.ONE_YEAR,
    num_books: int = 1,
    avg_price: float = 4.99,
    is_series: bool = False,
    monthly_decay_rate: float = DEFAULT_MONTHLY_DECAY_RATE,
    include_promotions: bool = True,
    new_books_per_year: int = 0,
    new_book_monthly_revenue: float = 0.0,
) -> BacklistProjection:
    """Calculate backlist compounding revenue projection.

    Args:
        current_monthly_revenue: Current total monthly gross revenue
        royalty_rate: Royalty rate (0.35 or 0.70)
        period: Projection period (1y, 3y, 5y)
        num_books: Current number of books in portfolio
        avg_price: Average book price
        is_series: Whether books are part of a series
        monthly_decay_rate: Monthly sales decay rate
        include_promotions: Whether to model periodic promotions
        new_books_per_year: Expected new books per year
        new_book_monthly_revenue: Expected monthly revenue for each new book

    Returns:
        BacklistProjection with month-by-month forecasts
    """
    months = PERIOD_MONTHS[period]
    monthly_projections = []
    cumulative_revenue = 0.0
    cumulative_royalty = 0.0

    # Track each "cohort" of books: existing + new releases
    # Each cohort has its own decay curve
    cohorts: list[dict] = [
        {
            "label": "existing_backlist",
            "start_month": 0,
            "base_monthly_revenue": current_monthly_revenue,
        }
    ]

    # Schedule new book releases
    if new_books_per_year > 0 and new_book_monthly_revenue > 0:
        release_interval = max(1, 12 // new_books_per_year)
        for year in range(months // 12 + 1):
            for release in range(new_books_per_year):
                release_month = year * 12 + (release * release_interval) + release_interval
                if release_month < months:
                    cohorts.append({
                        "label": f"new_book_y{year + 1}_r{release + 1}",
                        "start_month": release_month,
                        "base_monthly_revenue": new_book_monthly_revenue,
                    })

    # Series read-through bonus (applied monthly to book 1 revenue)
    series_bonus = 0.0
    if is_series and num_books > 1:
        book1_monthly_units = max(1, int(current_monthly_revenue / avg_price / num_books))
        series_bonus = _calculate_series_read_through(
            num_books, book1_monthly_units, avg_price, royalty_rate
        )

    for month in range(1, months + 1):
        month_revenue = 0.0

        for cohort in cohorts:
            if month < cohort["start_month"]:
                continue

            cohort_age = month - cohort["start_month"]
            base = cohort["base_monthly_revenue"]

            # Apply new book launch spike
            if cohort["start_month"] > 0 and cohort_age <= NEW_BOOK_LAUNCH_DECAY_MONTHS:
                launch_factor = NEW_BOOK_LAUNCH_MULTIPLIER * (
                    (NEW_BOOK_LAUNCH_DECAY_MONTHS - cohort_age + 1) / NEW_BOOK_LAUNCH_DECAY_MONTHS
                )
                cohort_revenue = base * max(1.0, launch_factor)
            else:
                # Apply natural decay
                effective_age = cohort_age
                if cohort["start_month"] > 0:
                    effective_age = cohort_age - NEW_BOOK_LAUNCH_DECAY_MONTHS
                    effective_age = max(0, effective_age)
                cohort_revenue = _apply_decay(base, effective_age, monthly_decay_rate)

            # Apply promotion boost
            if include_promotions:
                cohort_revenue = _apply_promotion_boost(cohort_age, cohort_revenue)

            month_revenue += cohort_revenue

        # Add series read-through bonus (decays more slowly)
        if series_bonus > 0:
            decayed_bonus = _apply_decay(
                series_bonus, month, monthly_decay_rate * 0.5
            )
            month_revenue += decayed_bonus

        month_royalty = month_revenue * royalty_rate
        cumulative_revenue += month_revenue
        cumulative_royalty += month_royalty

        monthly_projections.append({
            "month": month,
            "revenue": round(month_revenue, 2),
            "royalty": round(month_royalty, 2),
            "cumulative_revenue": round(cumulative_revenue, 2),
            "cumulative_royalty": round(cumulative_royalty, 2),
        })

    average_monthly = cumulative_revenue / months if months > 0 else 0.0

    # Compounding factor: how much more revenue we get vs. simple linear projection
    linear_projection = current_monthly_revenue * months
    compounding_factor = (
        cumulative_revenue / linear_projection
        if linear_projection > 0 else 1.0
    )

    assumptions = {
        "monthly_decay_rate": monthly_decay_rate,
        "royalty_rate": royalty_rate,
        "include_promotions": include_promotions,
        "promotion_frequency_months": PROMOTION_FREQUENCY_MONTHS if include_promotions else None,
        "promotion_boost_multiplier": PROMOTION_BOOST_MULTIPLIER if include_promotions else None,
        "is_series": is_series,
        "num_books": num_books,
        "new_books_per_year": new_books_per_year,
        "revenue_floor_multiplier": REVENUE_FLOOR_MULTIPLIER,
    }

    return BacklistProjection(
        period=period,
        months=months,
        monthly_projections=monthly_projections,
        total_projected_revenue=round(cumulative_revenue, 2),
        total_projected_royalty=round(cumulative_royalty, 2),
        average_monthly_revenue=round(average_monthly, 2),
        compounding_factor=round(compounding_factor, 4),
        assumptions=assumptions,
    )
