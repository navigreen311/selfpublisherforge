"""Seasonal Publishing Calendar: niche seasonality, event calendar, launch date optimization.

Provides:
- Full seasonal calendar with genre-specific events
- Niche seasonality data (monthly demand indices)
- AI-recommended launch dates
- Upcoming events relevant to user's genres
"""
from datetime import datetime, date, timedelta
from uuid import uuid4
from typing import Optional

from app.modules.portfolio_economics.schemas import (
    SeasonalEvent,
    NicheSeasonality,
    LaunchRecommendRequest,
    LaunchRecommendation,
    SeasonalCalendarResponse,
    SeasonType,
    ConfidenceLevel,
)


# ─── Seasonal Events Database ────────────────────────────────────────────────

UNIVERSAL_EVENTS: list[dict] = [
    {
        "event_id": "new_year",
        "name": "New Year / New You",
        "description": "Spike in self-help, fitness, and productivity books",
        "month_start": 1, "day_start": 1,
        "month_end": 1, "day_end": 31,
        "genres_affected": ["self-help", "non-fiction", "business", "health"],
        "impact_level": "high",
        "demand_multiplier": 1.8,
        "recommendations": [
            "Launch self-improvement titles in early January",
            "Run promotions on backlist self-help titles",
            "Target 'new year resolution' keywords",
        ],
    },
    {
        "event_id": "valentines",
        "name": "Valentine's Day Season",
        "description": "Major romance book buying season",
        "month_start": 2, "day_start": 1,
        "month_end": 2, "day_end": 14,
        "genres_affected": ["romance", "erotica", "poetry"],
        "impact_level": "high",
        "demand_multiplier": 2.0,
        "recommendations": [
            "Launch romance titles 2-3 weeks before Valentine's Day",
            "Create Valentine's themed promotions",
            "Bundle romance series for gifting",
        ],
    },
    {
        "event_id": "spring_break",
        "name": "Spring Break Reading",
        "description": "Increased beach read and travel book sales",
        "month_start": 3, "day_start": 15,
        "month_end": 4, "day_end": 15,
        "genres_affected": ["romance", "thriller", "mystery", "ya"],
        "impact_level": "medium",
        "demand_multiplier": 1.3,
        "recommendations": [
            "Promote beach reads and page-turners",
            "Run price promotions on series starters",
        ],
    },
    {
        "event_id": "summer_reading",
        "name": "Summer Reading Season",
        "description": "Peak reading period -- vacations and leisure time",
        "month_start": 6, "day_start": 1,
        "month_end": 8, "day_end": 31,
        "genres_affected": ["romance", "thriller", "mystery", "fantasy", "ya", "children"],
        "impact_level": "high",
        "demand_multiplier": 1.5,
        "recommendations": [
            "Launch big titles in late May or early June",
            "Participate in summer reading promotions",
            "Target vacation and beach read keywords",
        ],
    },
    {
        "event_id": "back_to_school",
        "name": "Back to School",
        "description": "Spike in children's, YA, and educational books",
        "month_start": 8, "day_start": 15,
        "month_end": 9, "day_end": 15,
        "genres_affected": ["children", "ya", "non-fiction", "self-help"],
        "impact_level": "medium",
        "demand_multiplier": 1.4,
        "recommendations": [
            "Launch children's and YA titles before school starts",
            "Promote educational and study-related content",
        ],
    },
    {
        "event_id": "halloween",
        "name": "Halloween / Spooky Season",
        "description": "Major spike in horror, thriller, and supernatural books",
        "month_start": 10, "day_start": 1,
        "month_end": 10, "day_end": 31,
        "genres_affected": ["horror", "thriller", "mystery", "fantasy", "ya"],
        "impact_level": "high",
        "demand_multiplier": 2.2,
        "recommendations": [
            "Launch horror titles in late September",
            "Run spooky season promotions",
            "Create Halloween-themed social media content",
        ],
    },
    {
        "event_id": "holiday_gift",
        "name": "Holiday Gift Season",
        "description": "Massive spike in book sales for gifting -- biggest sales period of the year",
        "month_start": 11, "day_start": 15,
        "month_end": 12, "day_end": 25,
        "genres_affected": [
            "romance", "thriller", "mystery", "fantasy", "sci-fi",
            "non-fiction", "children", "ya", "biography", "business",
        ],
        "impact_level": "high",
        "demand_multiplier": 2.5,
        "recommendations": [
            "Ensure paperback editions are available for gifting",
            "Run Black Friday / Cyber Monday ebook promotions",
            "Create gift bundles and box sets",
            "Launch major titles by early November",
        ],
    },
    {
        "event_id": "prime_day",
        "name": "Amazon Prime Day",
        "description": "Spike in ebook and Kindle device sales",
        "month_start": 7, "day_start": 10,
        "month_end": 7, "day_end": 15,
        "genres_affected": [
            "romance", "thriller", "mystery", "fantasy", "sci-fi",
            "non-fiction", "self-help",
        ],
        "impact_level": "medium",
        "demand_multiplier": 1.6,
        "recommendations": [
            "Run Kindle Countdown Deals",
            "Promote series starters at $0.99",
            "New Kindle owners need books -- push visibility",
        ],
    },
]


# ─── Genre Monthly Demand Indices ────────────────────────────────────────────
# 1.0 = average month; >1.0 = above average; <1.0 = below average

GENRE_MONTHLY_DEMAND: dict[str, dict[str, float]] = {
    "romance": {
        "January": 1.1, "February": 1.5, "March": 1.0, "April": 0.9,
        "May": 1.0, "June": 1.3, "July": 1.3, "August": 1.2,
        "September": 0.9, "October": 0.8, "November": 1.1, "December": 1.4,
    },
    "thriller": {
        "January": 0.9, "February": 0.9, "March": 1.0, "April": 1.0,
        "May": 1.1, "June": 1.3, "July": 1.2, "August": 1.1,
        "September": 1.0, "October": 1.3, "November": 1.1, "December": 1.2,
    },
    "mystery": {
        "January": 1.0, "February": 0.9, "March": 1.0, "April": 1.0,
        "May": 1.1, "June": 1.2, "July": 1.2, "August": 1.1,
        "September": 1.0, "October": 1.2, "November": 1.1, "December": 1.3,
    },
    "horror": {
        "January": 0.7, "February": 0.6, "March": 0.7, "April": 0.7,
        "May": 0.8, "June": 0.8, "July": 0.9, "August": 1.0,
        "September": 1.3, "October": 2.2, "November": 0.9, "December": 0.8,
    },
    "fantasy": {
        "January": 1.0, "February": 0.9, "March": 1.0, "April": 1.0,
        "May": 1.1, "June": 1.2, "July": 1.2, "August": 1.1,
        "September": 1.0, "October": 1.1, "November": 1.2, "December": 1.5,
    },
    "sci-fi": {
        "January": 1.0, "February": 0.9, "March": 1.0, "April": 1.0,
        "May": 1.1, "June": 1.2, "July": 1.2, "August": 1.0,
        "September": 1.0, "October": 1.0, "November": 1.1, "December": 1.3,
    },
    "self-help": {
        "January": 1.8, "February": 1.3, "March": 1.1, "April": 1.0,
        "May": 0.9, "June": 0.9, "July": 0.8, "August": 0.9,
        "September": 1.1, "October": 0.9, "November": 1.0, "December": 1.0,
    },
    "non-fiction": {
        "January": 1.3, "February": 1.0, "March": 1.0, "April": 1.0,
        "May": 1.0, "June": 0.9, "July": 0.9, "August": 1.0,
        "September": 1.1, "October": 1.0, "November": 1.2, "December": 1.4,
    },
    "children": {
        "January": 0.8, "February": 0.9, "March": 1.0, "April": 1.1,
        "May": 1.0, "June": 1.3, "July": 1.3, "August": 1.4,
        "September": 1.0, "October": 1.0, "November": 1.3, "December": 1.8,
    },
    "ya": {
        "January": 0.9, "February": 1.0, "March": 1.0, "April": 1.0,
        "May": 1.1, "June": 1.3, "July": 1.3, "August": 1.2,
        "September": 1.1, "October": 1.1, "November": 1.1, "December": 1.4,
    },
    "business": {
        "January": 1.5, "February": 1.2, "March": 1.1, "April": 1.0,
        "May": 1.0, "June": 0.9, "July": 0.8, "August": 0.9,
        "September": 1.1, "October": 1.0, "November": 1.1, "December": 1.2,
    },
    "biography": {
        "January": 0.9, "February": 1.0, "March": 1.0, "April": 1.0,
        "May": 1.0, "June": 1.0, "July": 0.9, "August": 0.9,
        "September": 1.0, "October": 1.1, "November": 1.3, "December": 1.5,
    },
}

DEFAULT_MONTHLY_DEMAND: dict[str, float] = {
    "January": 1.0, "February": 1.0, "March": 1.0, "April": 1.0,
    "May": 1.0, "June": 1.1, "July": 1.1, "August": 1.0,
    "September": 1.0, "October": 1.0, "November": 1.1, "December": 1.3,
}

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _get_monthly_demand(genre: str) -> dict[str, float]:
    """Get monthly demand data for a genre."""
    normalized = genre.lower().replace(" ", "_").replace("-", "_")
    return GENRE_MONTHLY_DEMAND.get(normalized, DEFAULT_MONTHLY_DEMAND)


def _build_event_for_year(event_data: dict, year: int) -> SeasonalEvent:
    """Build a SeasonalEvent from template data for a specific year."""
    return SeasonalEvent(
        event_id=f"{event_data['event_id']}_{year}",
        name=event_data["name"],
        description=event_data["description"],
        start_date=date(year, event_data["month_start"], event_data["day_start"]),
        end_date=date(year, event_data["month_end"], event_data["day_end"]),
        genres_affected=event_data["genres_affected"],
        impact_level=event_data["impact_level"],
        demand_multiplier=event_data["demand_multiplier"],
        recommendations=event_data["recommendations"],
        is_recurring=True,
    )


def get_seasonal_calendar(
    year: int,
    user_genres: list[str] | None = None,
) -> SeasonalCalendarResponse:
    """Build a full seasonal calendar for the given year.

    Filters events to genres the user writes in, and includes
    genre-specific seasonality data.
    """
    all_events = [_build_event_for_year(ev, year) for ev in UNIVERSAL_EVENTS]

    # Filter to relevant genres if specified
    if user_genres:
        normalized_genres = [g.lower().replace(" ", "_").replace("-", "_") for g in user_genres]
        relevant_events = [
            ev for ev in all_events
            if any(
                g in [ng.replace("_", "-") for ng in normalized_genres]
                or g in normalized_genres
                for g in ev.genres_affected
            )
            or not ev.genres_affected  # Universal events always included
        ]
    else:
        relevant_events = all_events

    # Build genre seasonality data
    genre_seasonality = {}
    for genre in (user_genres or []):
        genre_seasonality[genre] = get_niche_seasonality(genre, year)

    return SeasonalCalendarResponse(
        year=year,
        events=relevant_events,
        user_genres=user_genres or [],
        genre_seasonality=genre_seasonality,
    )


def get_niche_seasonality(genre: str, year: int | None = None) -> NicheSeasonality:
    """Get seasonality data for a specific genre/niche."""
    monthly_demand = _get_monthly_demand(genre)

    # Identify peak and low months
    avg_demand = sum(monthly_demand.values()) / 12
    peak_months = [m for m, d in monthly_demand.items() if d >= avg_demand * 1.15]
    low_months = [m for m, d in monthly_demand.items() if d <= avg_demand * 0.85]

    # Get relevant events
    target_year = year or date.today().year
    normalized = genre.lower().replace(" ", "_").replace("-", "_")
    seasonal_events = [
        _build_event_for_year(ev, target_year)
        for ev in UNIVERSAL_EVENTS
        if normalized in ev["genres_affected"]
        or genre.lower() in ev["genres_affected"]
    ]

    # Determine best launch windows
    best_launch_windows = []
    sorted_months = sorted(monthly_demand.items(), key=lambda x: x[1], reverse=True)
    top_months = sorted_months[:3]

    for month_name, demand in top_months:
        month_idx = MONTH_NAMES.index(month_name) + 1
        # Best to launch 2-4 weeks before peak
        launch_month_idx = month_idx - 1 if month_idx > 1 else 12
        launch_month = MONTH_NAMES[launch_month_idx - 1]
        best_launch_windows.append({
            "start_month": launch_month,
            "end_month": month_name,
            "reason": f"Demand peaks in {month_name} (index: {demand:.1f}x average)",
        })

    # Determine windows to avoid
    avoid_windows = []
    bottom_months = sorted_months[-2:]
    for month_name, demand in bottom_months:
        avoid_windows.append({
            "start_month": month_name,
            "end_month": month_name,
            "reason": f"Low demand in {month_name} (index: {demand:.1f}x average)",
        })

    return NicheSeasonality(
        genre=genre,
        monthly_demand=monthly_demand,
        peak_months=peak_months,
        low_months=low_months,
        seasonal_events=seasonal_events,
        best_launch_windows=best_launch_windows,
        avoid_windows=avoid_windows,
    )


def recommend_launch_date(request: LaunchRecommendRequest) -> LaunchRecommendation:
    """Recommend the optimal launch date for a book.

    Considers:
    - Genre seasonality (monthly demand indices)
    - Upcoming events (favorable and competing)
    - Day of week preferences (Tuesday-Thursday launches perform best)
    - Marketing lead time
    - Series timing
    """
    monthly_demand = _get_monthly_demand(request.genre)
    earliest = request.earliest_ready_date

    # Evaluate each month from earliest ready date over next 6 months
    candidates: list[dict] = []

    for months_ahead in range(0, 7):
        candidate_date = earliest + timedelta(days=months_ahead * 30)
        month_name = MONTH_NAMES[candidate_date.month - 1]
        demand = monthly_demand.get(month_name, 1.0)

        # Score this launch window
        score = demand * 100  # Base score from demand

        # Prefer Tuesday, Wednesday, Thursday launches
        # Adjust candidate to nearest Tue-Thu
        day_of_week = candidate_date.weekday()
        if day_of_week == 0:  # Monday -> Tuesday
            candidate_date += timedelta(days=1)
        elif day_of_week == 4:  # Friday -> Thursday
            candidate_date -= timedelta(days=1)
        elif day_of_week == 5:  # Saturday -> Tuesday
            candidate_date += timedelta(days=3)
        elif day_of_week == 6:  # Sunday -> Tuesday
            candidate_date += timedelta(days=2)

        # Check for events
        normalized_genre = request.genre.lower().replace(" ", "_").replace("-", "_")
        year = candidate_date.year
        favorable_events = []
        competing_events = []

        for ev in UNIVERSAL_EVENTS:
            ev_start = date(year, ev["month_start"], ev["day_start"])
            ev_end = date(year, ev["month_end"], ev["day_end"])
            is_relevant = (
                normalized_genre in ev["genres_affected"]
                or request.genre.lower() in ev["genres_affected"]
            )

            # Check if launch is 1-4 weeks before event
            days_before = (ev_start - candidate_date).days
            if 7 <= days_before <= 28 and is_relevant:
                favorable_events.append(ev["name"])
                score += 15

            # Check if launch overlaps with event
            if ev_start <= candidate_date <= ev_end:
                if is_relevant:
                    favorable_events.append(f"During {ev['name']}")
                    score += 10
                else:
                    competing_events.append(ev["name"])
                    score -= 5

        # Marketing lead time check
        if candidate_date < earliest + timedelta(days=request.marketing_lead_time_days):
            score -= 20  # Insufficient lead time

        # Series timing bonus
        if request.is_series and request.series_position and request.series_position > 1:
            # Later series books should launch quickly after previous
            score += 5

        candidates.append({
            "date": candidate_date,
            "score": score,
            "demand": demand,
            "favorable_events": favorable_events,
            "competing_events": competing_events,
        })

    # Sort by score, pick the best
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]

    # Determine season type
    if best["demand"] >= 1.3:
        season_type = SeasonType.PEAK
    elif best["demand"] >= 0.9:
        season_type = SeasonType.SHOULDER
    else:
        season_type = SeasonType.OFF_PEAK

    # Build reasoning
    reasoning = []
    month_name = MONTH_NAMES[best["date"].month - 1]
    reasoning.append(
        f"{month_name} has a demand index of {best['demand']:.1f}x for {request.genre}"
    )
    if best["favorable_events"]:
        reasoning.append(f"Favorable events: {', '.join(best['favorable_events'])}")
    if best["competing_events"]:
        reasoning.append(f"Competing events to watch: {', '.join(best['competing_events'])}")
    reasoning.append(
        f"Launch on {best['date'].strftime('%A')} -- mid-week launches typically perform best"
    )

    # Confidence
    if len(candidates) >= 3 and candidates[0]["score"] > candidates[1]["score"] * 1.15:
        confidence = ConfidenceLevel.HIGH
    elif len(candidates) >= 2:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.LOW

    # Alternative dates
    alternative_dates = [c["date"] for c in candidates[1:4]]

    # Pre-launch checklist
    pre_launch_checklist = [
        {"days_before": 60, "action": "Finalize cover design", "description": "Cover should be ready for pre-order and promotional materials"},
        {"days_before": 45, "action": "Set up pre-order", "description": "Create pre-order listing on Amazon and other platforms"},
        {"days_before": 30, "action": "Begin ARC distribution", "description": "Send advance reader copies to reviewers and influencers"},
        {"days_before": 21, "action": "Launch cover reveal", "description": "Share cover on social media and in newsletter"},
        {"days_before": 14, "action": "Start pre-launch marketing", "description": "Begin countdown posts, email sequences, and ads"},
        {"days_before": 7, "action": "Final promotional push", "description": "Increase ad spend, send launch week emails"},
        {"days_before": 1, "action": "Pre-launch day prep", "description": "Prepare launch day posts, verify all links work"},
        {"days_before": 0, "action": "LAUNCH DAY", "description": "Execute launch plan, engage with readers, monitor sales"},
    ]

    # Marketing timeline
    launch_date = best["date"]
    marketing_timeline = [
        {"date": (launch_date - timedelta(days=30)).isoformat(), "action": "ARC distribution begins", "channel": "email"},
        {"date": (launch_date - timedelta(days=21)).isoformat(), "action": "Cover reveal", "channel": "social_media"},
        {"date": (launch_date - timedelta(days=14)).isoformat(), "action": "Pre-launch email sequence starts", "channel": "email"},
        {"date": (launch_date - timedelta(days=7)).isoformat(), "action": "Amazon ads go live", "channel": "amazon_ads"},
        {"date": (launch_date - timedelta(days=3)).isoformat(), "action": "Countdown posts", "channel": "social_media"},
        {"date": launch_date.isoformat(), "action": "Launch day blitz", "channel": "all"},
        {"date": (launch_date + timedelta(days=3)).isoformat(), "action": "Follow-up engagement", "channel": "social_media"},
        {"date": (launch_date + timedelta(days=7)).isoformat(), "action": "Post-launch review request", "channel": "email"},
    ]

    return LaunchRecommendation(
        recommended_date=best["date"],
        alternative_dates=alternative_dates,
        season_type=season_type,
        demand_index=best["demand"],
        confidence=confidence,
        reasoning=reasoning,
        competing_events=best["competing_events"],
        favorable_events=best["favorable_events"],
        pre_launch_checklist=pre_launch_checklist,
        marketing_timeline=marketing_timeline,
        calculated_at=datetime.utcnow(),
    )


def get_upcoming_events(
    genres: list[str],
    days_ahead: int = 90,
) -> list[SeasonalEvent]:
    """Get upcoming events relevant to the user's genres."""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    current_year = today.year

    events = []
    normalized_genres = [g.lower().replace(" ", "_").replace("-", "_") for g in genres]

    for ev_data in UNIVERSAL_EVENTS:
        # Check current year and next year
        for year in [current_year, current_year + 1]:
            ev = _build_event_for_year(ev_data, year)

            # Check if event is in the lookup window
            if ev.end_date < today or ev.start_date > end_date:
                continue

            # Check if event is relevant to user's genres
            is_relevant = any(
                g in normalized_genres
                or g.replace("-", "_") in normalized_genres
                for g in ev.genres_affected
            )

            if is_relevant or not genres:  # Show all if no genres specified
                events.append(ev)

    # Sort by start date
    events.sort(key=lambda e: e.start_date)
    return events
