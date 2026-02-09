"""Pydantic v2 schemas for Review Intelligence module."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Enums ---


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class AlertType(str, Enum):
    NEGATIVE_SPIKE = "negative_spike"
    VELOCITY_DROP = "velocity_drop"
    RATING_DECLINE = "rating_decline"
    COMPETITOR_SURGE = "competitor_surge"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VelocityPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class VelocityTrend(str, Enum):
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"


class ReviewSource(str, Enum):
    AMAZON = "amazon"
    GOODREADS = "goodreads"
    BOOKBUB = "bookbub"
    APPLE_BOOKS = "apple_books"
    BARNES_NOBLE = "barnes_noble"
    KOBO = "kobo"
    OTHER = "other"


# --- Review Schemas ---


class ReviewBase(BaseModel):
    book_id: UUID
    source: ReviewSource
    source_review_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewer_profile_url: Optional[str] = None
    star_rating: float = Field(..., ge=0.0, le=5.0)
    title: Optional[str] = None
    body: Optional[str] = None
    review_date: Optional[datetime] = None
    verified_purchase: bool = False
    helpful_count: int = 0
    is_competitor: bool = False


class ReviewRead(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    sentiment: Optional[SentimentLabel] = None
    sentiment_score: Optional[float] = None
    themes: Optional[dict] = None
    analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ReviewListParams(BaseModel):
    cursor: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    source: Optional[ReviewSource] = None
    min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    max_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    sentiment: Optional[SentimentLabel] = None
    is_competitor: Optional[bool] = None
    sort_by: str = "review_date"
    sort_dir: str = "desc"


# --- Sentiment Schemas ---


class ThemeItem(BaseModel):
    theme: str
    count: int
    sentiment: SentimentLabel
    example_quotes: list[str] = []


class SentimentBreakdown(BaseModel):
    positive_count: int
    neutral_count: int
    negative_count: int
    mixed_count: int
    total_count: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    mixed_pct: float
    avg_sentiment_score: float
    themes: list[ThemeItem] = []


class SentimentAnalysisResult(BaseModel):
    sentiment: SentimentLabel
    score: float = Field(..., ge=-1.0, le=1.0)
    themes: list[str] = []
    key_phrases: list[str] = []
    complaints: list[str] = []
    praise: list[str] = []


class BatchAnalysisRequest(BaseModel):
    review_ids: Optional[list[UUID]] = None
    book_id: Optional[UUID] = None
    limit: int = Field(default=50, ge=1, le=200)


class BatchAnalysisResponse(BaseModel):
    total_analyzed: int
    sentiment_breakdown: SentimentBreakdown
    top_themes: list[ThemeItem] = []
    top_complaints: list[str] = []
    top_praise: list[str] = []
    actionable_insights: list[str] = []


# --- Velocity Schemas ---


class VelocityDataPoint(BaseModel):
    period_start: datetime
    period_end: datetime
    review_count: int
    avg_rating: Optional[float] = None
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0


class VelocityReport(BaseModel):
    book_id: UUID
    period: VelocityPeriod
    data_points: list[VelocityDataPoint] = []
    current_rate: float  # reviews per period
    previous_rate: float  # reviews per previous period
    change_pct: float  # percentage change
    trend: VelocityTrend
    anomalies: list[dict] = []


# --- Alert Schemas ---


class ReviewAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    data: Optional[dict] = None
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class AlertListParams(BaseModel):
    cursor: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    alert_type: Optional[AlertType] = None
    severity: Optional[AlertSeverity] = None
    is_acknowledged: Optional[bool] = False
    book_id: Optional[UUID] = None


# --- Reputation Schemas ---


class ReputationScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    overall_score: float
    avg_rating: float
    total_reviews: int
    sentiment_ratio: float
    velocity_trend: VelocityTrend
    health_grade: str
    details: Optional[dict] = None
    last_calculated_at: datetime
    created_at: datetime
    updated_at: datetime


class ReputationHealthMetrics(BaseModel):
    book_id: UUID
    overall_score: float = Field(..., ge=0.0, le=100.0)
    avg_rating: float
    total_reviews: int
    sentiment_ratio: float
    velocity_trend: VelocityTrend
    health_grade: str
    rating_distribution: dict[str, int] = {}
    recent_trend: str = ""
    recommendations: list[str] = []


# --- Review Acquisition Schemas ---


class AcquisitionTipsRequest(BaseModel):
    book_id: UUID
    current_review_count: Optional[int] = None
    genre: Optional[str] = None
    target_audience: Optional[str] = None
    budget: Optional[str] = None  # low, medium, high


class AcquisitionTip(BaseModel):
    category: str  # e.g. "email outreach", "social media", "ARC teams"
    tip: str
    effort_level: str  # low, medium, high
    expected_impact: str  # low, medium, high
    details: str = ""


class AcquisitionTipsResponse(BaseModel):
    book_id: UUID
    tips: list[AcquisitionTip] = []
    estimated_review_potential: int = 0
    summary: str = ""
