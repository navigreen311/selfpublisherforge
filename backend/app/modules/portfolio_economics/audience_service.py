"""Audience DNA Builder: reader personas, also-bought intelligence, churn prediction.

Provides:
- Audience persona generation from genre and book data
- Also-bought graph analysis
- Audience growth tracking
- Churn prediction model
"""
from datetime import datetime, date, timedelta, timezone
from uuid import UUID, uuid4
from typing import Optional

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


def build_audience_personas(
    request: AudienceAnalyzeRequest,
) -> list[AudiencePersona]:
    """Build reader personas based on genre and book data.

    Uses genre-specific templates enhanced with book-specific data.
    """
    book_id = request.book_id or uuid4()
    templates = _get_persona_templates(request.genre)

    personas = []
    for template in templates:
        # Enhance with request-specific data
        discovery_channels = template["discovery_channels"].copy()
        motivations = template["motivations"].copy()
        pain_points = template["pain_points"].copy()

        # Add keyword-driven insights
        if request.keywords:
            motivations.append(f"Interest in: {', '.join(request.keywords[:3])}")

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

        persona = AudiencePersona(
            persona_id=uuid4(),
            book_id=book_id,
            name=template["name"],
            description=(
                f"A typical {request.genre} reader persona representing "
                f"approximately {template['percentage']:.0f}% of the target audience."
            ),
            age_range=age_range,
            gender_skew=gender_skew,
            reading_frequency=template["reading_frequency"],
            preferred_formats=template["preferred_formats"],
            price_sensitivity=template["price_sensitivity"],
            discovery_channels=discovery_channels,
            motivations=motivations,
            pain_points=pain_points,
            favorite_authors=[],  # Would be populated from market data
            percentage_of_audience=template["percentage"],
            created_at=datetime.now(timezone.utc),
        )
        personas.append(persona)

    return personas


def build_also_bought_intelligence(
    book_id: UUID,
    genre: str,
    comparable_asins: list[str] | None = None,
) -> AlsoBoughtIntelligence:
    """Build also-bought intelligence for a book.

    In production, this would query Amazon's Product Advertising API
    or a scraped database. Here we generate representative data.
    """
    # Generate representative also-bought data
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

    also_bought_items = []
    for i, author in enumerate(authors[:6]):
        also_bought_items.append(AlsoBoughtItem(
            asin=comparable_asins[i] if comparable_asins and i < len(comparable_asins) else f"B0{i:08d}",
            title=f"Popular {genre.title()} Title #{i + 1}",
            author=author,
            genre=genre,
            price=round(3.99 + (i * 0.5), 2),
            rating=round(4.0 + (i % 3) * 0.2, 1),
            review_count=500 + (i * 200),
            overlap_score=round(0.9 - (i * 0.12), 2),
        ))

    avg_price = sum(item.price for item in also_bought_items) / len(also_bought_items) if also_bought_items else 0.0
    avg_rating = sum(item.rating for item in also_bought_items) / len(also_bought_items) if also_bought_items else 0.0

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


def get_audience_growth(
    org_id: UUID,
    days: int = 90,
) -> AudienceGrowthResponse:
    """Get audience growth tracking data.

    In production, this would query analytics events. Here we generate
    representative trend data for the API shape.
    """
    today = date.today()
    start_date = today - timedelta(days=days)

    data_points = []
    base_readers = 100
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        # Simulate growth with some variance
        growth_factor = 1.0 + (i / days) * 0.3  # 30% growth over period
        total = int(base_readers * growth_factor)
        new = max(1, int(total * 0.05))  # ~5% new readers daily
        returning = total - new

        data_points.append(AudienceGrowthPoint(
            date=current_date,
            total_readers=total,
            new_readers=new,
            returning_readers=returning,
            engagement_rate=round(0.15 + (i / days) * 0.05, 3),  # 15-20%
            read_through_rate=round(0.6 + (i / days) * 0.1, 3),  # 60-70%
        ))

    total_audience = data_points[-1].total_readers if data_points else 0
    initial_audience = data_points[0].total_readers if data_points else 0
    growth_rate = (
        ((total_audience - initial_audience) / initial_audience)
        if initial_audience > 0 else 0.0
    )

    return AudienceGrowthResponse(
        org_id=org_id,
        period_start=start_date,
        period_end=today,
        data_points=data_points,
        total_audience_size=total_audience,
        growth_rate=round(growth_rate, 4),
        retention_rate=0.72,  # Would be calculated from real data
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
