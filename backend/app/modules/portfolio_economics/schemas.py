"""Pydantic v2 schemas for Portfolio Economics, Audience DNA, and Seasonal Calendar."""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from uuid import UUID
from enum import Enum
from typing import Optional


# ─── Enums ────────────────────────────────────────────────────────────────────

class DecisionType(str, Enum):
    KILL = "kill"
    SCALE = "scale"
    MAINTAIN = "maintain"
    REVIVE = "revive"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SeasonType(str, Enum):
    PEAK = "peak"
    SHOULDER = "shoulder"
    OFF_PEAK = "off_peak"


class ChurnRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectionPeriod(str, Enum):
    ONE_YEAR = "1y"
    THREE_YEAR = "3y"
    FIVE_YEAR = "5y"


# ─── Portfolio Economics Schemas ──────────────────────────────────────────────

class GreenlightRequest(BaseModel):
    """Request to evaluate a book idea's ROI potential."""
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=500, description="Working title of the book")
    genre: str = Field(..., min_length=1, max_length=200, description="Primary genre/niche")
    sub_genre: Optional[str] = Field(None, max_length=200, description="Sub-genre or niche")
    estimated_word_count: int = Field(50000, ge=5000, le=500000, description="Target word count")
    estimated_price: float = Field(4.99, ge=0.99, le=99.99, description="Planned retail price (USD)")
    royalty_rate: float = Field(0.7, ge=0.0, le=1.0, description="Expected royalty rate (0.35 or 0.70)")
    estimated_production_cost: float = Field(500.0, ge=0.0, description="Cover, editing, formatting costs")
    estimated_marketing_budget: float = Field(200.0, ge=0.0, description="Launch marketing spend")
    is_series: bool = Field(False, description="Part of a series")
    series_position: Optional[int] = Field(None, ge=1, description="Position in series if applicable")
    comparable_asins: list[str] = Field(default_factory=list, description="ASINs of comparable titles")
    market_size_estimate: Optional[int] = Field(None, ge=0, description="Estimated monthly searches or market size")


class GreenlightResult(BaseModel):
    """ROI forecast for a book idea."""
    model_config = ConfigDict(from_attributes=True)

    title: str
    genre: str
    greenlight_score: float = Field(..., ge=0.0, le=100.0, description="Overall greenlight score 0-100")
    recommendation: str = Field(..., description="go / caution / no-go")
    confidence: ConfidenceLevel

    # Financial projections
    estimated_market_size: int = Field(..., description="Estimated monthly market demand")
    estimated_capture_rate: float = Field(..., ge=0.0, le=1.0, description="Expected market share capture")
    projected_monthly_units: int = Field(..., ge=0, description="Projected monthly unit sales")
    projected_monthly_revenue: float = Field(..., ge=0.0, description="Projected monthly gross revenue")
    projected_monthly_royalty: float = Field(..., ge=0.0, description="Projected monthly royalty income")
    total_investment: float = Field(..., ge=0.0, description="Total upfront investment")
    breakeven_months: Optional[float] = Field(None, ge=0.0, description="Months to break even")
    first_year_roi: float = Field(..., description="Projected first-year ROI percentage")
    first_year_profit: float = Field(..., description="Projected first-year net profit")

    # Risk factors
    risk_factors: list[str] = Field(default_factory=list, description="Identified risk factors")
    opportunity_factors: list[str] = Field(default_factory=list, description="Identified opportunities")
    suggestions: list[str] = Field(default_factory=list, description="Suggestions to improve ROI")

    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class KillScaleRequest(BaseModel):
    """Request for kill/scale analysis on an existing book."""
    model_config = ConfigDict(from_attributes=True)

    book_id: UUID
    current_monthly_revenue: float = Field(..., ge=0.0)
    current_monthly_units: int = Field(..., ge=0)
    months_since_launch: int = Field(..., ge=1)
    total_investment: float = Field(..., ge=0.0)
    total_revenue_to_date: float = Field(..., ge=0.0)
    monthly_marketing_spend: float = Field(0.0, ge=0.0)
    trend_direction: str = Field("flat", description="up / flat / down")
    review_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_count: int = Field(0, ge=0)
    is_series: bool = False
    series_position: Optional[int] = Field(None, ge=1)


class KillScaleDecision(BaseModel):
    """Kill or scale recommendation for a book."""
    model_config = ConfigDict(from_attributes=True)

    book_id: UUID
    decision: DecisionType
    confidence: ConfidenceLevel
    score: float = Field(..., ge=0.0, le=100.0, description="Decision score 0-100")

    # Financial analysis
    current_roi: float = Field(..., description="Current ROI percentage")
    projected_6m_revenue: float = Field(..., ge=0.0)
    projected_12m_revenue: float = Field(..., ge=0.0)
    monthly_revenue_trend: float = Field(..., description="Monthly revenue change rate")

    # Recommendations
    reasoning: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list, description="Recommended actions")
    estimated_additional_investment: Optional[float] = Field(None, ge=0.0)
    estimated_additional_return: Optional[float] = Field(None)

    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class BacklistProjection(BaseModel):
    """Revenue projection for backlist compounding."""
    model_config = ConfigDict(from_attributes=True)

    period: ProjectionPeriod
    months: int
    monthly_projections: list[dict] = Field(
        default_factory=list,
        description="Month-by-month revenue projections [{month, revenue, cumulative}]"
    )
    total_projected_revenue: float = Field(..., ge=0.0)
    total_projected_royalty: float = Field(..., ge=0.0)
    average_monthly_revenue: float = Field(..., ge=0.0)
    compounding_factor: float = Field(
        ..., ge=0.0,
        description="Revenue growth multiplier from backlist effects"
    )
    assumptions: dict = Field(default_factory=dict)


class BookSummary(BaseModel):
    """Summary of a book in the portfolio."""
    model_config = ConfigDict(from_attributes=True)

    book_id: UUID
    title: str
    genre: str
    launch_date: Optional[date] = None
    monthly_revenue: float = 0.0
    monthly_units: int = 0
    total_revenue: float = 0.0
    roi: float = 0.0
    status: str = "active"


class PortfolioOverview(BaseModel):
    """Full portfolio overview with aggregated metrics."""
    model_config = ConfigDict(from_attributes=True)

    org_id: UUID
    total_books: int = 0
    active_books: int = 0
    total_revenue: float = 0.0
    total_investment: float = 0.0
    portfolio_roi: float = 0.0
    monthly_revenue: float = 0.0
    monthly_trend: float = 0.0
    top_performers: list[BookSummary] = Field(default_factory=list)
    underperformers: list[BookSummary] = Field(default_factory=list)
    genre_distribution: dict[str, int] = Field(default_factory=dict)
    revenue_by_genre: dict[str, float] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PortfolioRecommendation(BaseModel):
    """AI-generated recommendation for portfolio optimization."""
    model_config = ConfigDict(from_attributes=True)

    category: str = Field(..., description="diversification / optimization / growth / risk")
    priority: str = Field(..., description="high / medium / low")
    title: str
    description: str
    estimated_impact: Optional[str] = None
    actions: list[str] = Field(default_factory=list)


# ─── Audience DNA Schemas ─────────────────────────────────────────────────────

class AudienceAnalyzeRequest(BaseModel):
    """Request to build audience profile from book data."""
    model_config = ConfigDict(from_attributes=True)

    book_id: Optional[UUID] = None
    genre: str = Field(..., min_length=1, max_length=200)
    sub_genre: Optional[str] = Field(None, max_length=200)
    book_description: Optional[str] = Field(None, max_length=5000)
    keywords: list[str] = Field(default_factory=list)
    comparable_asins: list[str] = Field(default_factory=list)
    target_age_range: Optional[str] = Field(None, description="e.g., '25-45'")
    target_gender: Optional[str] = Field(None, description="e.g., 'female', 'male', 'all'")


class AudiencePersona(BaseModel):
    """Reader persona profile."""
    model_config = ConfigDict(from_attributes=True)

    persona_id: UUID
    book_id: UUID
    name: str = Field(..., description="Persona name e.g. 'Avid Romance Reader'")
    description: str
    age_range: str = Field(..., description="e.g., '25-45'")
    gender_skew: str = Field(..., description="e.g., '70% female'")
    reading_frequency: str = Field(..., description="e.g., '3-5 books/month'")
    preferred_formats: list[str] = Field(default_factory=list, description="['ebook', 'paperback', 'audio']")
    price_sensitivity: str = Field(..., description="low / medium / high")
    discovery_channels: list[str] = Field(
        default_factory=list,
        description="How they find books: ['amazon_search', 'bookstagram', 'newsletters']"
    )
    motivations: list[str] = Field(default_factory=list, description="Why they read this genre")
    pain_points: list[str] = Field(default_factory=list, description="What frustrates them")
    favorite_authors: list[str] = Field(default_factory=list)
    percentage_of_audience: float = Field(..., ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlsoBoughtItem(BaseModel):
    """A single also-bought title."""
    model_config = ConfigDict(from_attributes=True)

    asin: str
    title: str
    author: str
    genre: str
    price: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    overlap_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="How much audience overlap exists"
    )


class AlsoBoughtIntelligence(BaseModel):
    """Also-bought analysis for a book."""
    model_config = ConfigDict(from_attributes=True)

    book_id: UUID
    also_bought: list[AlsoBoughtItem] = Field(default_factory=list)
    common_genres: list[str] = Field(default_factory=list)
    average_price: float = 0.0
    average_rating: float = 0.0
    audience_insights: list[str] = Field(default_factory=list)
    positioning_suggestions: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class AudienceGrowthPoint(BaseModel):
    """A single data point in audience growth tracking."""
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_readers: int = 0
    new_readers: int = 0
    returning_readers: int = 0
    engagement_rate: float = 0.0
    read_through_rate: float = 0.0


class AudienceGrowthResponse(BaseModel):
    """Audience growth tracking response."""
    model_config = ConfigDict(from_attributes=True)

    org_id: UUID
    period_start: date
    period_end: date
    data_points: list[AudienceGrowthPoint] = Field(default_factory=list)
    total_audience_size: int = 0
    growth_rate: float = 0.0
    retention_rate: float = 0.0


class ChurnPredictionRequest(BaseModel):
    """Request for churn prediction."""
    model_config = ConfigDict(from_attributes=True)

    book_id: Optional[UUID] = None
    genre: Optional[str] = None
    days_since_last_purchase: int = Field(0, ge=0)
    total_purchases: int = Field(0, ge=0)
    average_rating_given: Optional[float] = Field(None, ge=1.0, le=5.0)
    series_completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    email_open_rate: Optional[float] = Field(None, ge=0.0, le=1.0)


class ChurnPredictionResult(BaseModel):
    """Churn prediction result."""
    model_config = ConfigDict(from_attributes=True)

    churn_risk: ChurnRisk
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    risk_factors: list[str] = Field(default_factory=list)
    retention_suggestions: list[str] = Field(default_factory=list)
    estimated_lifetime_value: float = Field(0.0, ge=0.0)
    predicted_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Seasonal Calendar Schemas ────────────────────────────────────────────────

class SeasonalEvent(BaseModel):
    """A seasonal event relevant to publishing."""
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    name: str
    description: str
    start_date: date
    end_date: date
    genres_affected: list[str] = Field(default_factory=list)
    impact_level: str = Field(..., description="high / medium / low")
    demand_multiplier: float = Field(1.0, ge=0.0, description="Multiplier on normal demand")
    recommendations: list[str] = Field(default_factory=list)
    is_recurring: bool = True


class NicheSeasonality(BaseModel):
    """Seasonality data for a specific niche/genre."""
    model_config = ConfigDict(from_attributes=True)

    genre: str
    monthly_demand: dict[str, float] = Field(
        default_factory=dict,
        description="Month name -> relative demand index (1.0 = average)"
    )
    peak_months: list[str] = Field(default_factory=list)
    low_months: list[str] = Field(default_factory=list)
    seasonal_events: list[SeasonalEvent] = Field(default_factory=list)
    best_launch_windows: list[dict] = Field(
        default_factory=list,
        description="[{start_month, end_month, reason}]"
    )
    avoid_windows: list[dict] = Field(
        default_factory=list,
        description="[{start_month, end_month, reason}]"
    )


class LaunchRecommendRequest(BaseModel):
    """Request for launch date recommendation."""
    model_config = ConfigDict(from_attributes=True)

    genre: str = Field(..., min_length=1, max_length=200)
    sub_genre: Optional[str] = Field(None, max_length=200)
    book_type: str = Field("ebook", description="ebook / paperback / hardcover / audio")
    is_series: bool = False
    series_position: Optional[int] = Field(None, ge=1)
    earliest_ready_date: date = Field(..., description="Earliest date the book could be ready")
    marketing_lead_time_days: int = Field(14, ge=0, le=180)
    target_audience_timezone: str = Field("US", description="Primary audience region")


class LaunchRecommendation(BaseModel):
    """Recommended launch date with reasoning."""
    model_config = ConfigDict(from_attributes=True)

    recommended_date: date
    alternative_dates: list[date] = Field(default_factory=list)
    season_type: SeasonType
    demand_index: float = Field(..., ge=0.0, description="Expected demand relative to average")
    confidence: ConfidenceLevel

    reasoning: list[str] = Field(default_factory=list)
    competing_events: list[str] = Field(default_factory=list)
    favorable_events: list[str] = Field(default_factory=list)

    pre_launch_checklist: list[dict] = Field(
        default_factory=list,
        description="[{days_before, action, description}]"
    )
    marketing_timeline: list[dict] = Field(
        default_factory=list,
        description="[{date, action, channel}]"
    )

    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class SeasonalCalendarResponse(BaseModel):
    """Full seasonal calendar response."""
    model_config = ConfigDict(from_attributes=True)

    year: int
    events: list[SeasonalEvent] = Field(default_factory=list)
    user_genres: list[str] = Field(default_factory=list)
    genre_seasonality: dict[str, NicheSeasonality] = Field(default_factory=dict)
