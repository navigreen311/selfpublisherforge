"""Audience DNA Builder: reader personas, also-bought intelligence, churn prediction.

Provides:
- Audience persona generation from genre and book data
- Also-bought graph analysis
- Audience growth tracking
- Churn prediction model
"""
import logging
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.modules.analytics.models import AnalyticsEvent, RoyaltyRecord
from app.modules.review_intelligence.models import BookReview
from app.models.project import Book
from app.models.market import CompetitorBook

logger = logging.getLogger(__name__)

from app.modules.portfolio_economics.schemas import (
    AudienceAnalyzeRequest,
    AudiencePersona,
    AlsoBoughtItem,
    AlsoBoughtIntelligence,
    AudienceGrowthPoint,
    AudienceGrowthResponse,
    ChurnPredictionRequest,
    ChurnPredictionResult,
    ChurnRisk,
)


# ─── Genre Persona Templates ─────────────────────────────────────────────────

GENRE_PERSONAS: dict[str, list[dict]] = {
    "romance": [
        {
            "name": "The Devoted Romance Reader",
            "age_range": "25-45",
            "gender_skew": "85% female",
            "reading_frequency": "4-6 books/month",
            "preferred_formats": ["ebook", "audio"],
            "price_sensitivity": "medium",
            "discovery_channels": ["amazon_search", "bookstagram", "facebook_groups", "newsletters"],
            "motivations": ["Emotional escape", "HEA guarantee", "Character connection", "Comfort reading"],
            "pain_points": ["Cliffhangers without resolution", "Slow pacing", "Insta-love without development"],
            "percentage": 55.0,
        },
        {
            "name": "The Casual Romance Fan",
            "age_range": "30-55",
            "gender_skew": "80% female",
            "reading_frequency": "1-2 books/month",
            "preferred_formats": ["ebook", "paperback"],
            "price_sensitivity": "high",
            "discovery_channels": ["amazon_browse", "friend_recommendations", "library"],
            "motivations": ["Beach reads", "Quick entertainment", "Familiar tropes"],
            "pain_points": ["Overly explicit content", "Formulaic plots", "High prices"],
            "percentage": 30.0,
        },
        {
            "name": "The Kindle Unlimited Binger",
            "age_range": "22-40",
            "gender_skew": "75% female",
            "reading_frequency": "8-12 books/month",
            "preferred_formats": ["ebook"],
            "price_sensitivity": "low",
            "discovery_channels": ["kindle_unlimited", "also_bought", "amazon_recommendations"],
            "motivations": ["Volume reading", "Series binging", "Trope exploration"],
            "pain_points": ["Short books", "Lack of series", "KU exclusivity gaps"],
            "percentage": 15.0,
        },
    ],
    "thriller": [
        {
            "name": "The Thriller Enthusiast",
            "age_range": "30-60",
            "gender_skew": "55% male",
            "reading_frequency": "2-4 books/month",
            "preferred_formats": ["ebook", "audio", "paperback"],
            "price_sensitivity": "low",
            "discovery_channels": ["amazon_search", "goodreads", "airport_bookstores", "newsletters"],
            "motivations": ["Adrenaline rush", "Puzzle solving", "Page-turner experience"],
            "pain_points": ["Predictable twists", "Unrealistic plots", "Slow starts"],
            "percentage": 50.0,
        },
        {
            "name": "The Crime Fiction Crossover",
            "age_range": "35-65",
            "gender_skew": "50% female",
            "reading_frequency": "2-3 books/month",
            "preferred_formats": ["paperback", "audio"],
            "price_sensitivity": "medium",
            "discovery_channels": ["bookstores", "book_clubs", "library", "goodreads"],
            "motivations": ["Character-driven stories", "Procedural accuracy", "Series following"],
            "pain_points": ["Gratuitous violence", "Weak character development", "Plot holes"],
            "percentage": 35.0,
        },
        {
            "name": "The Audiobook Commuter",
            "age_range": "28-50",
            "gender_skew": "60% male",
            "reading_frequency": "1-2 books/month",
            "preferred_formats": ["audio"],
            "price_sensitivity": "medium",
            "discovery_channels": ["audible", "podcast_ads", "social_media"],
            "motivations": ["Commute entertainment", "Multitasking reading", "Narrator performance"],
            "pain_points": ["Poor narration", "Confusing POV shifts", "Too many characters"],
            "percentage": 15.0,
        },
    ],
    "default": [
        {
            "name": "The General Reader",
            "age_range": "25-55",
            "gender_skew": "55% female",
            "reading_frequency": "1-3 books/month",
            "preferred_formats": ["ebook", "paperback"],
            "price_sensitivity": "medium",
            "discovery_channels": ["amazon_search", "social_media", "friend_recommendations"],
            "motivations": ["Entertainment", "Learning", "Escapism"],
            "pain_points": ["Poor writing quality", "Misleading descriptions", "High prices"],
            "percentage": 60.0,
        },
        {
            "name": "The Kindle Unlimited Browser",
            "age_range": "22-45",
            "gender_skew": "60% female",
            "reading_frequency": "3-5 books/month",
            "preferred_formats": ["ebook"],
            "price_sensitivity": "low",
            "discovery_channels": ["kindle_unlimited", "also_bought", "amazon_recommendations"],
            "motivations": ["Discovery", "Volume reading", "Genre exploration"],
            "pain_points": ["Quality inconsistency", "Short page counts", "Series drops"],
            "percentage": 40.0,
        },
    ],
}


# ─── Churn Model Weights ─────────────────────────────────────────────────────

CHURN_WEIGHT_RECENCY = 0.30      # Days since last purchase
CHURN_WEIGHT_FREQUENCY = 0.25    # Total purchases
CHURN_WEIGHT_RATING = 0.15       # Average rating given
CHURN_WEIGHT_SERIES = 0.15       # Series completion rate
CHURN_WEIGHT_EMAIL = 0.15        # Email engagement


def _get_persona_templates(genre: str) -> list[dict]:
    """Get persona templates for a genre."""
    normalized = genre.lower().replace(" ", "_").replace("-", "_")
    return GENRE_PERSONAS.get(normalized, GENRE_PERSONAS["default"])


async def _fetch_book_insights(
    db: AsyncSession,
    book_id: UUID | None,
    genre: str,
) -> dict:
    """Query the database for book metadata, review sentiment, and sales data.

    Returns a dict with keys: keywords, themes, avg_rating, review_count,
    sentiment_positive_pct, total_units, avg_price, favorite_authors.
    """
    insights: dict = {
        "keywords": [],
        "themes": [],
        "avg_rating": None,
        "review_count": 0,
        "sentiment_positive_pct": 0.0,
        "total_units": 0,
        "avg_price": None,
        "favorite_authors": [],
    }

    if book_id is None:
        return insights

    # --- Book metadata (keywords, genre info from JSONB metadata) ---
    book_query = select(Book).where(
        and_(Book.id == book_id, Book.deleted_at.is_(None))
    )
    book_result = await db.execute(book_query)
    book = book_result.scalar_one_or_none()
    if book and book.metadata_:
        meta = book.metadata_
        insights["keywords"] = meta.get("keywords", [])

    # --- Review data: average rating, sentiment breakdown, themes ---
    review_stats_query = select(
        func.count(BookReview.id).label("review_count"),
        func.avg(BookReview.star_rating).label("avg_rating"),
    ).where(
        and_(
            BookReview.book_id == book_id,
            BookReview.deleted_at.is_(None),
        )
    )
    review_stats = await db.execute(review_stats_query)
    row = review_stats.one_or_none()
    if row and row.review_count and row.review_count > 0:
        insights["review_count"] = row.review_count
        insights["avg_rating"] = round(float(row.avg_rating), 2) if row.avg_rating else None

    # Sentiment distribution
    sentiment_query = select(
        BookReview.sentiment,
        func.count(BookReview.id).label("cnt"),
    ).where(
        and_(
            BookReview.book_id == book_id,
            BookReview.deleted_at.is_(None),
            BookReview.sentiment.isnot(None),
        )
    ).group_by(BookReview.sentiment)
    sentiment_result = await db.execute(sentiment_query)
    sentiment_rows = sentiment_result.all()
    total_sentiment = sum(r.cnt for r in sentiment_rows)
    positive_count = sum(r.cnt for r in sentiment_rows if r.sentiment == "positive")
    if total_sentiment > 0:
        insights["sentiment_positive_pct"] = round(positive_count / total_sentiment, 2)

    # Collect unique themes from reviews
    themes_query = select(BookReview.themes).where(
        and_(
            BookReview.book_id == book_id,
            BookReview.deleted_at.is_(None),
            BookReview.themes.isnot(None),
        )
    ).limit(50)
    themes_result = await db.execute(themes_query)
    all_themes: list[str] = []
    for (themes_data,) in themes_result.all():
        if isinstance(themes_data, dict):
            all_themes.extend(themes_data.get("themes", []))
        elif isinstance(themes_data, list):
            all_themes.extend(themes_data)
    # Deduplicate and take most common
    if all_themes:
        theme_counts: dict[str, int] = defaultdict(int)
        for t in all_themes:
            if isinstance(t, str):
                theme_counts[t] += 1
        sorted_themes = sorted(theme_counts, key=theme_counts.get, reverse=True)
        insights["themes"] = sorted_themes[:10]

    # --- Sales/royalty data ---
    sales_query = select(
        func.sum(RoyaltyRecord.net_units).label("total_units"),
        func.avg(RoyaltyRecord.list_price).label("avg_price"),
    ).where(
        and_(
            RoyaltyRecord.book_id == book_id,
            RoyaltyRecord.deleted_at.is_(None),
        )
    )
    sales_result = await db.execute(sales_query)
    sales_row = sales_result.one_or_none()
    if sales_row:
        if sales_row.total_units is not None:
            insights["total_units"] = int(sales_row.total_units)
        if sales_row.avg_price is not None:
            insights["avg_price"] = round(float(sales_row.avg_price), 2)

    return insights


async def build_audience_personas(
    request: AudienceAnalyzeRequest,
) -> list[AudiencePersona]:
    """Build reader personas based on genre, book metadata, reviews, and sales data.

    Queries the database for real book metadata, review sentiment, and sales
    patterns to enhance genre-specific persona templates. Falls back to
    template defaults when no database records exist.
    """
    book_id = request.book_id or uuid4()
    templates = _get_persona_templates(request.genre)

    # Fetch real data from the database
    insights: dict = {
        "keywords": [],
        "themes": [],
        "avg_rating": None,
        "review_count": 0,
        "sentiment_positive_pct": 0.0,
        "total_units": 0,
        "avg_price": None,
        "favorite_authors": [],
    }
    try:
        async with async_session() as db:
            insights = await _fetch_book_insights(db, request.book_id, request.genre)
    except (SQLAlchemyError, OperationalError) as e:
        logger.warning(
            "build_audience_personas: database query for book insights failed, using defaults",
            exc_info=True,
        )

    personas = []
    for template in templates:
        # Enhance with request-specific data
        discovery_channels = template["discovery_channels"].copy()
        motivations = template["motivations"].copy()
        pain_points = template["pain_points"].copy()

        # Add keyword-driven insights from request or database
        effective_keywords = request.keywords or insights.get("keywords", [])
        if effective_keywords:
            motivations.append(f"Interest in: {', '.join(effective_keywords[:3])}")

        # Add theme-driven insights from actual review data
        db_themes = insights.get("themes", [])
        if db_themes:
            motivations.append(f"Drawn to themes: {', '.join(db_themes[:3])}")

        # Adjust pain points based on review sentiment
        review_count = insights.get("review_count", 0)
        avg_rating = insights.get("avg_rating")
        if review_count > 0 and avg_rating is not None:
            if avg_rating < 3.5:
                pain_points.append(
                    f"Quality concerns reflected in {avg_rating:.1f}-star avg across {review_count} reviews"
                )
            elif avg_rating >= 4.5:
                motivations.append(
                    f"High reader satisfaction ({avg_rating:.1f} stars from {review_count} reviews)"
                )

        # Adjust price sensitivity based on real sales price data
        price_sensitivity = template["price_sensitivity"]
        real_avg_price = insights.get("avg_price")
        if real_avg_price is not None:
            if real_avg_price <= 2.99:
                price_sensitivity = "high"
            elif real_avg_price >= 6.99:
                price_sensitivity = "low"

        # Adjust for target demographics if provided
        age_range = template["age_range"]
        if request.target_age_range:
            age_range = request.target_age_range

        gender_skew = template["gender_skew"]
        if request.target_gender:
            if request.target_gender.lower() == "female":
                gender_skew = "80%+ female"
            elif request.target_gender.lower() == "male":
                gender_skew = "70%+ male"
            else:
                gender_skew = "balanced"

        # Adjust audience percentage based on real unit sales volume
        percentage = template["percentage"]
        total_units = insights.get("total_units", 0)
        if total_units > 0:
            # Use sales volume to shift emphasis toward the high-volume persona
            # (the first template in each genre list is typically the core buyer)
            pass  # Keep template percentages unless we have segment-level data

        persona = AudiencePersona(
            persona_id=uuid4(),
            book_id=book_id,
            name=template["name"],
            description=(
                f"A typical {request.genre} reader persona representing "
                f"approximately {percentage:.0f}% of the target audience."
                + (
                    f" Based on analysis of {review_count} reviews"
                    f" and {total_units} units sold."
                    if review_count > 0 or total_units > 0
                    else ""
                )
            ),
            age_range=age_range,
            gender_skew=gender_skew,
            reading_frequency=template["reading_frequency"],
            preferred_formats=template["preferred_formats"],
            price_sensitivity=price_sensitivity,
            discovery_channels=discovery_channels,
            motivations=motivations,
            pain_points=pain_points,
            favorite_authors=insights.get("favorite_authors", []),
            percentage_of_audience=percentage,
            created_at=datetime.now(timezone.utc),
        )
        personas.append(persona)

    return personas


async def build_also_bought_intelligence(
    book_id: UUID,
    genre: str,
    comparable_asins: list[str] | None = None,
) -> AlsoBoughtIntelligence:
    """Build also-bought intelligence for a book.

    Queries the competitor_books table for real comparable title data when
    ASINs are provided. Falls back to genre-based representative data
    when no competitor records exist.
    """
    also_bought_items: list[AlsoBoughtItem] = []

    # Attempt to fetch real competitor data from the database
    try:
        async with async_session() as db:
            if comparable_asins:
                comp_query = select(CompetitorBook).where(
                    and_(
                        CompetitorBook.asin.in_(comparable_asins),
                        CompetitorBook.deleted_at.is_(None),
                    )
                )
                comp_result = await db.execute(comp_query)
                comp_books = comp_result.scalars().all()

                for i, comp in enumerate(comp_books):
                    also_bought_items.append(AlsoBoughtItem(
                        asin=comp.asin,
                        title=comp.title,
                        author=comp.author or "Unknown",
                        genre=comp.category or genre,
                        price=round(float(comp.price), 2) if comp.price is not None else 0.0,
                        rating=round(float(comp.rating), 1) if comp.rating is not None else 0.0,
                        review_count=comp.reviews_count or 0,
                        overlap_score=round(max(0.0, 0.9 - (i * 0.12)), 2),
                    ))

            # If we still have ASINs without DB matches, or no ASINs given,
            # try to find competitor books in the same category
            if not also_bought_items:
                normalized_genre = genre.lower().replace(" ", "_").replace("-", "_")
                category_query = (
                    select(CompetitorBook)
                    .where(
                        and_(
                            CompetitorBook.deleted_at.is_(None),
                            func.lower(CompetitorBook.category).contains(normalized_genre),
                        )
                    )
                    .order_by(CompetitorBook.reviews_count.desc())
                    .limit(6)
                )
                cat_result = await db.execute(category_query)
                cat_books = cat_result.scalars().all()

                for i, comp in enumerate(cat_books):
                    also_bought_items.append(AlsoBoughtItem(
                        asin=comp.asin,
                        title=comp.title,
                        author=comp.author or "Unknown",
                        genre=comp.category or genre,
                        price=round(float(comp.price), 2) if comp.price is not None else 0.0,
                        rating=round(float(comp.rating), 1) if comp.rating is not None else 0.0,
                        review_count=comp.reviews_count or 0,
                        overlap_score=round(max(0.0, 0.9 - (i * 0.12)), 2),
                    ))
    except (SQLAlchemyError, OperationalError) as e:
        logger.warning(
            "build_also_bought_intelligence: database query for competitor data failed, falling back to genre-based defaults",
            exc_info=True,
        )

    # Fallback: genre-based representative data when no DB records found
    if not also_bought_items:
        genre_authors: dict[str, list[str]] = {
            "romance": ["Colleen Hoover", "Emily Henry", "Ali Hazelwood", "Ana Huang"],
            "thriller": ["James Patterson", "Lee Child", "Harlan Coben", "Karin Slaughter"],
            "mystery": ["Agatha Christie", "Louise Penny", "Tana French", "Ruth Ware"],
            "sci-fi": ["Andy Weir", "Blake Crouch", "Martha Wells", "Becky Chambers"],
            "fantasy": ["Brandon Sanderson", "Sarah J. Maas", "Rebecca Yarros", "Holly Black"],
            "default": ["Various Authors"],
        }

        normalized_genre = genre.lower().replace(" ", "_").replace("-", "_")
        authors = genre_authors.get(normalized_genre, genre_authors["default"])

        for i, author in enumerate(authors[:6]):
            also_bought_items.append(AlsoBoughtItem(
                asin=(
                    comparable_asins[i]
                    if comparable_asins and i < len(comparable_asins)
                    else f"B0{i:08d}"
                ),
                title=f"Popular {genre.title()} Title #{i + 1}",
                author=author,
                genre=genre,
                price=round(3.99 + (i * 0.5), 2),
                rating=round(4.0 + (i % 3) * 0.2, 1),
                review_count=500 + (i * 200),
                overlap_score=round(0.9 - (i * 0.12), 2),
            ))

    avg_price = (
        sum(item.price for item in also_bought_items) / len(also_bought_items)
        if also_bought_items
        else 0.0
    )
    avg_rating = (
        sum(item.rating for item in also_bought_items) / len(also_bought_items)
        if also_bought_items
        else 0.0
    )

    audience_insights = [
        f"Readers in {genre} typically buy {len(also_bought_items)}+ related titles",
        f"Average price point for comparable titles is ${avg_price:.2f}",
        f"Average rating for comparable titles is {avg_rating:.1f} stars",
    ]

    positioning_suggestions = [
        f"Price competitively around ${avg_price:.2f} to match reader expectations",
        "Use similar keywords and categories as top-performing comparable titles",
        "Consider similar cover design elements to signal genre correctly",
        "Study blurb structure of top comparable titles",
    ]

    return AlsoBoughtIntelligence(
        book_id=book_id,
        also_bought=also_bought_items,
        common_genres=[genre],
        average_price=round(avg_price, 2),
        average_rating=round(avg_rating, 1),
        audience_insights=audience_insights,
        positioning_suggestions=positioning_suggestions,
        analyzed_at=datetime.now(timezone.utc),
    )


async def get_audience_growth(
    org_id: UUID,
    days: int = 90,
) -> AudienceGrowthResponse:
    """Get audience growth tracking data from royalty records and analytics events.

    Queries RoyaltyRecord for unit sales aggregated by day, and AnalyticsEvent
    for engagement metrics. Returns zeros with a descriptive note when no
    historical data exists for the organization.
    """
    today = date.today()
    start_date = today - timedelta(days=days)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

    daily_units: dict[date, int] = {}
    daily_revenue: dict[date, float] = {}
    daily_engagement_events: dict[date, int] = {}
    daily_total_events: dict[date, int] = {}

    try:
        async with async_session() as db:
            # --- Royalty records: units sold per day ---
            royalty_query = select(
                func.date_trunc("day", RoyaltyRecord.period_start).label("day"),
                func.sum(RoyaltyRecord.net_units).label("units"),
                func.sum(RoyaltyRecord.net_revenue).label("revenue"),
            ).where(
                and_(
                    RoyaltyRecord.org_id == org_id,
                    RoyaltyRecord.period_start >= start_dt,
                    RoyaltyRecord.period_start <= end_dt,
                    RoyaltyRecord.deleted_at.is_(None),
                )
            ).group_by(func.date_trunc("day", RoyaltyRecord.period_start))

            royalty_result = await db.execute(royalty_query)
            for row in royalty_result.all():
                if row.day is not None:
                    d = row.day.date() if hasattr(row.day, "date") else row.day
                    daily_units[d] = int(row.units) if row.units else 0
                    daily_revenue[d] = float(row.revenue) if row.revenue else 0.0

            # --- Analytics events: engagement tracking ---
            engagement_query = select(
                func.date_trunc("day", AnalyticsEvent.occurred_at).label("day"),
                func.count(AnalyticsEvent.id).label("total_events"),
                func.count(AnalyticsEvent.id).filter(
                    AnalyticsEvent.event_type.in_([
                        "page_read", "book_open", "read_through",
                        "sample_download", "review_submitted",
                    ])
                ).label("engagement_events"),
            ).where(
                and_(
                    AnalyticsEvent.org_id == org_id,
                    AnalyticsEvent.occurred_at >= start_dt,
                    AnalyticsEvent.occurred_at <= end_dt,
                    AnalyticsEvent.deleted_at.is_(None),
                )
            ).group_by(func.date_trunc("day", AnalyticsEvent.occurred_at))

            engagement_result = await db.execute(engagement_query)
            for row in engagement_result.all():
                if row.day is not None:
                    d = row.day.date() if hasattr(row.day, "date") else row.day
                    daily_engagement_events[d] = int(row.engagement_events) if row.engagement_events else 0
                    daily_total_events[d] = int(row.total_events) if row.total_events else 0
    except (SQLAlchemyError, OperationalError) as e:
        logger.warning(
            "get_audience_growth: database query for royalty/analytics data failed, returning empty growth data",
            exc_info=True,
        )

    has_data = bool(daily_units or daily_engagement_events)

    # Build data points for each day in the period
    data_points: list[AudienceGrowthPoint] = []
    cumulative_readers = 0

    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_units = daily_units.get(current_date, 0)
        day_engagement = daily_engagement_events.get(current_date, 0)
        day_total_events = daily_total_events.get(current_date, 0)

        # New readers approximated from unit sales for the day
        new_readers = day_units
        cumulative_readers += new_readers

        # Returning readers estimated from engagement events minus new
        returning_readers = max(0, day_engagement - new_readers)

        total_readers = new_readers + returning_readers

        # Engagement rate: ratio of engagement events to total events
        engagement_rate = 0.0
        if day_total_events > 0:
            engagement_rate = round(day_engagement / day_total_events, 3)

        # Read-through rate: approximate from engagement vs readers
        read_through_rate = 0.0
        if cumulative_readers > 0 and day_engagement > 0:
            read_through_rate = round(
                min(1.0, day_engagement / max(1, cumulative_readers)),
                3,
            )

        data_points.append(AudienceGrowthPoint(
            date=current_date,
            total_readers=total_readers,
            new_readers=new_readers,
            returning_readers=returning_readers,
            engagement_rate=engagement_rate,
            read_through_rate=read_through_rate,
        ))

    total_audience = cumulative_readers

    # Calculate growth rate from first half vs second half of the period
    if has_data and len(data_points) >= 2:
        midpoint = len(data_points) // 2
        first_half_total = sum(dp.new_readers for dp in data_points[:midpoint])
        second_half_total = sum(dp.new_readers for dp in data_points[midpoint:])
        growth_rate = (
            ((second_half_total - first_half_total) / first_half_total)
            if first_half_total > 0
            else 0.0
        )
    else:
        growth_rate = 0.0

    # Retention rate: ratio of days with returning readers to days with any readers
    active_days = [dp for dp in data_points if dp.total_readers > 0]
    returning_days = [dp for dp in data_points if dp.returning_readers > 0]
    retention_rate = (
        round(len(returning_days) / len(active_days), 4)
        if active_days
        else 0.0
    )

    return AudienceGrowthResponse(
        org_id=org_id,
        period_start=start_date,
        period_end=today,
        data_points=data_points,
        total_audience_size=total_audience,
        growth_rate=round(growth_rate, 4),
        retention_rate=retention_rate,
    )


def predict_churn(request: ChurnPredictionRequest) -> ChurnPredictionResult:
    """Predict churn risk for a reader segment.

    Uses a weighted scoring model based on:
    - Recency: Days since last purchase (higher = more risk)
    - Frequency: Total purchases (higher = less risk)
    - Rating: Average rating given (higher = less risk)
    - Series completion: Series completion rate (higher = less risk)
    - Email engagement: Email open rate (higher = less risk)
    """
    risk_score = 0.0
    risk_factors = []
    retention_suggestions = []

    # Recency score (0-1, higher = more churn risk)
    if request.days_since_last_purchase > 180:
        recency_score = 1.0
        risk_factors.append(f"No purchase in {request.days_since_last_purchase} days (very inactive)")
    elif request.days_since_last_purchase > 90:
        recency_score = 0.75
        risk_factors.append(f"No purchase in {request.days_since_last_purchase} days (inactive)")
    elif request.days_since_last_purchase > 30:
        recency_score = 0.4
    else:
        recency_score = 0.1
    risk_score += recency_score * CHURN_WEIGHT_RECENCY

    # Frequency score (0-1, higher = less churn risk, inverted for scoring)
    if request.total_purchases == 0:
        frequency_score = 1.0
        risk_factors.append("No previous purchases")
    elif request.total_purchases < 3:
        frequency_score = 0.7
        risk_factors.append("Few purchases -- not yet a loyal reader")
    elif request.total_purchases < 10:
        frequency_score = 0.3
    else:
        frequency_score = 0.1
    risk_score += frequency_score * CHURN_WEIGHT_FREQUENCY

    # Rating score
    if request.average_rating_given is not None:
        if request.average_rating_given < 3.0:
            rating_score = 0.9
            risk_factors.append(f"Low average rating ({request.average_rating_given:.1f}) indicates dissatisfaction")
        elif request.average_rating_given < 4.0:
            rating_score = 0.5
        else:
            rating_score = 0.1
    else:
        rating_score = 0.5  # No data = neutral
    risk_score += rating_score * CHURN_WEIGHT_RATING

    # Series completion
    if request.series_completion_rate is not None:
        if request.series_completion_rate < 0.3:
            series_score = 0.8
            risk_factors.append("Low series completion rate suggests disengagement")
        elif request.series_completion_rate < 0.6:
            series_score = 0.4
        else:
            series_score = 0.1
    else:
        series_score = 0.5
    risk_score += series_score * CHURN_WEIGHT_SERIES

    # Email engagement
    if request.email_open_rate is not None:
        if request.email_open_rate < 0.1:
            email_score = 0.9
            risk_factors.append("Very low email engagement (<10% open rate)")
        elif request.email_open_rate < 0.25:
            email_score = 0.5
        else:
            email_score = 0.15
    else:
        email_score = 0.5
    risk_score += email_score * CHURN_WEIGHT_EMAIL

    # Determine churn risk level
    if risk_score >= 0.7:
        churn_risk = ChurnRisk.CRITICAL
        retention_suggestions.extend([
            "Send a personalized win-back email with an exclusive offer",
            "Offer a free short story or novella to re-engage",
            "Create a limited-time bundle deal",
        ])
    elif risk_score >= 0.5:
        churn_risk = ChurnRisk.HIGH
        retention_suggestions.extend([
            "Send a targeted email with new release announcements",
            "Offer early access to upcoming titles",
            "Run a re-engagement email sequence",
        ])
    elif risk_score >= 0.3:
        churn_risk = ChurnRisk.MODERATE
        retention_suggestions.extend([
            "Maintain regular newsletter cadence",
            "Share behind-the-scenes content to build connection",
            "Consider a reader survey to understand preferences",
        ])
    else:
        churn_risk = ChurnRisk.LOW
        retention_suggestions.extend([
            "Continue current engagement strategy",
            "Consider loyalty rewards for long-term readers",
            "Ask for reviews and referrals",
        ])

    # Estimate lifetime value
    avg_book_price = 4.99
    estimated_ltv = request.total_purchases * avg_book_price * 0.7  # 70% royalty
    if churn_risk in (ChurnRisk.LOW, ChurnRisk.MODERATE):
        # Project future purchases
        estimated_future_purchases = max(0, 12 - request.total_purchases) * 0.5
        estimated_ltv += estimated_future_purchases * avg_book_price * 0.7

    return ChurnPredictionResult(
        churn_risk=churn_risk,
        churn_probability=round(risk_score, 3),
        risk_factors=risk_factors,
        retention_suggestions=retention_suggestions,
        estimated_lifetime_value=round(estimated_ltv, 2),
        predicted_at=datetime.now(timezone.utc),
    )
