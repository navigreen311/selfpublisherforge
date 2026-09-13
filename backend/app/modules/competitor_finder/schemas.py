"""Pydantic v2 schemas for the Competitor Weakness Finder module."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WeaknessCategory(str, Enum):
    CONTENT_QUALITY = "content_quality"
    FORMAT_LAYOUT = "format_layout"
    MISSING_FEATURES = "missing_features"
    PRICING = "pricing"
    COVERAGE_GAPS = "coverage_gaps"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AlertType(str, Enum):
    PRICE_CHANGE = "price_change"
    BSR_SHIFT = "bsr_shift"
    NEW_BOOK = "new_book"
    REVIEW_SPIKE = "review_spike"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CompetitorAnalyzeRequest(BaseModel):
    """Request to deep-analyze a single competitor book."""

    book_id: UUID
    include_opportunity: bool = Field(
        default=True,
        description="Also generate an opportunity blueprint after analysis",
    )
    max_reviews: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of reviews to analyze",
    )


class BatchAnalyzeRequest(BaseModel):
    """Request to analyze the top N books in a category."""

    category: str = Field(..., min_length=1, max_length=300)
    top_n: int = Field(default=10, ge=1, le=50)
    include_opportunity: bool = True


class GapAnalysisRequest(BaseModel):
    """Request for cover/title/content gap analysis in a niche."""

    niche: str = Field(..., min_length=1, max_length=300)
    category: str | None = Field(default=None, max_length=300)
    book_ids: list[UUID] | None = Field(
        default=None,
        description="Specific book IDs to include; if omitted, auto-discover from niche",
    )
    max_books: int = Field(default=20, ge=2, le=100)


# ---------------------------------------------------------------------------
# Evidence and sub-schemas
# ---------------------------------------------------------------------------


class ReviewEvidence(BaseModel):
    """An excerpt from a review used as evidence for a weakness signal."""

    review_id: UUID | None = None
    excerpt: str
    rating: int | None = None
    helpful_votes: int = 0


class WeaknessSignalSchema(BaseModel):
    """A single detected weakness signal."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID
    category: WeaknessCategory
    severity: Severity
    signal_text: str
    evidence: list[ReviewEvidence] | None = None
    frequency: int = 1
    confidence: float = 0.0
    actionable: bool = True
    suggestion: str | None = None
    created_at: datetime
    updated_at: datetime


class WeaknessSignalCreate(BaseModel):
    """Internal schema for creating a weakness signal."""

    category: WeaknessCategory
    severity: Severity
    signal_text: str
    evidence: list[dict] | None = None
    frequency: int = 1
    confidence: float = 0.0
    actionable: bool = True
    suggestion: str | None = None


# ---------------------------------------------------------------------------
# Opportunity Blueprint
# ---------------------------------------------------------------------------


class ContentStrategy(BaseModel):
    """AI-generated content strategy details."""

    key_topics: list[str] = Field(default_factory=list)
    unique_angles: list[str] = Field(default_factory=list)
    depth_level: str = "intermediate"
    suggested_length: str | None = None
    structure_notes: str | None = None


class PricingStrategy(BaseModel):
    """AI-generated pricing strategy."""

    recommended_price: float | None = None
    price_range_low: float | None = None
    price_range_high: float | None = None
    rationale: str | None = None
    bundle_suggestions: list[str] = Field(default_factory=list)


class OpportunityBlueprintSchema(BaseModel):
    """Full opportunity blueprint for beating a competitor."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID
    title_suggestions: list[str] | None = None
    content_strategy: ContentStrategy | dict | None = None
    format_recommendations: list[str] | None = None
    pricing_strategy: PricingStrategy | dict | None = None
    differentiators: list[str] | None = None
    target_audience: str | None = None
    estimated_opportunity_score: float | None = None
    full_blueprint: dict | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Competitor Analysis (main response)
# ---------------------------------------------------------------------------


class CompetitorBookBrief(BaseModel):
    """Brief view of a competitor book embedded in analysis responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asin: str
    title: str
    author: str | None = None
    bsr: int | None = None
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None


class CompetitorAnalysisSchema(BaseModel):
    """Full analysis result for a competitor book."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    status: AnalysisStatus
    overall_score: float | None = None
    sentiment_score: float | None = None
    weakness_count: int = 0
    strength_count: int = 0
    review_summary: str | None = None
    positioning_analysis: dict | None = None
    metadata_json: dict | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class CompetitorAnalysisDetail(CompetitorAnalysisSchema):
    """Analysis with embedded weaknesses and opportunity."""

    weaknesses: list[WeaknessSignalSchema] = Field(default_factory=list)
    opportunity: OpportunityBlueprintSchema | None = None


# ---------------------------------------------------------------------------
# Gap Analysis
# ---------------------------------------------------------------------------


class CoverGap(BaseModel):
    """A detected gap in cover design across a niche."""

    gap_type: str
    description: str
    prevalence: float = 0.0  # 0-1 how common
    opportunity: str | None = None


class TitleGap(BaseModel):
    """A detected gap in title/subtitle patterns across a niche."""

    gap_type: str
    description: str
    missing_keywords: list[str] = Field(default_factory=list)
    opportunity: str | None = None


class ContentGap(BaseModel):
    """A detected gap in content coverage across a niche."""

    topic: str
    description: str
    demand_signal: str | None = None
    competitor_coverage: float = 0.0  # 0-1 how many competitors cover this


class GapAnalysisSchema(BaseModel):
    """Full gap analysis result for a niche."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    niche: str
    category: str | None = None
    books_analyzed: int = 0
    cover_gaps: list[CoverGap | dict] | None = None
    title_gaps: list[TitleGap | dict] | None = None
    content_gaps: list[ContentGap | dict] | None = None
    summary: str | None = None
    recommendations: list[str] | None = None
    status: str = "pending"
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Competitor Alerts
# ---------------------------------------------------------------------------


class CompetitorAlertSchema(BaseModel):
    """A single competitor alert."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID | None = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str | None = None
    data: dict | None = None
    read: bool = False
    dismissed: bool = False
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Batch / list responses
# ---------------------------------------------------------------------------


class BatchAnalyzeResponse(BaseModel):
    """Response for a batch analysis request."""

    task_id: str
    analyses_created: int
    book_ids: list[UUID]
    message: str = "Batch analysis started"
