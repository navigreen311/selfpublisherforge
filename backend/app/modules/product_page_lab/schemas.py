"""Pydantic v2 schemas for the Product Page Conversion Lab."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Genre(str, Enum):
    ROMANCE = "romance"
    THRILLER = "thriller"
    MYSTERY = "mystery"
    FANTASY = "fantasy"
    SCIENCE_FICTION = "science_fiction"
    LITERARY_FICTION = "literary_fiction"
    NON_FICTION = "non_fiction"
    SELF_HELP = "self_help"
    MEMOIR = "memoir"
    HORROR = "horror"
    YOUNG_ADULT = "young_adult"
    CHILDREN = "children"
    HISTORICAL_FICTION = "historical_fiction"
    OTHER = "other"


class ABTestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class DeviceType(str, Enum):
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ListingAnalyzeRequest(BaseModel):
    """Request to analyze an Amazon listing by ASIN or URL."""
    asin: Optional[str] = Field(None, min_length=10, max_length=10, pattern=r"^[A-Z0-9]{10}$")
    url: Optional[str] = Field(None, max_length=500)
    book_id: Optional[UUID] = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"asin": "B09V2KKG1D"},
            {"url": "https://www.amazon.com/dp/B09V2KKG1D"},
        ]
    })


class BlurbGenerateRequest(BaseModel):
    """Request to generate optimized blurb variations."""
    book_id: Optional[UUID] = None
    current_blurb: str = Field(..., min_length=10, max_length=5000)
    genre: Genre = Genre.OTHER
    target_audience: Optional[str] = Field(None, max_length=500)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    tone: Optional[str] = Field(None, max_length=100)
    num_variants: int = Field(default=3, ge=1, le=5)


class ABTestCreateRequest(BaseModel):
    """Request to create an A/B test for blurbs."""
    book_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    variant_a: str = Field(..., min_length=10, max_length=5000)
    variant_b: str = Field(..., min_length=10, max_length=5000)
    duration_days: int = Field(default=7, ge=1, le=90)


class LookInsideAnalyzeRequest(BaseModel):
    """Request to analyze the Look Inside preview effectiveness."""
    book_id: Optional[UUID] = None
    preview_text: str = Field(..., min_length=50, max_length=20000)
    genre: Genre = Genre.OTHER
    chapter_titles: list[str] = Field(default_factory=list)


class MobileCheckRequest(BaseModel):
    """Request to check listing appearance on mobile."""
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    blurb: str = Field(..., min_length=10, max_length=5000)
    author_name: str = Field(..., min_length=1, max_length=200)
    cover_image_url: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Sub-models for analysis results
# ---------------------------------------------------------------------------

class Recommendation(BaseModel):
    """A single recommendation for improving a listing element."""
    area: str
    severity: str = Field(..., pattern=r"^(critical|warning|info)$")
    message: str
    suggestion: str
    current_value: Optional[str] = None
    recommended_value: Optional[str] = None


class TitleAnalysis(BaseModel):
    """Analysis of the listing title."""
    score: float = Field(..., ge=0, le=100)
    length: int
    has_keywords: bool
    keyword_matches: list[str] = Field(default_factory=list)
    power_words: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class BlurbAnalysis(BaseModel):
    """Analysis of the listing blurb/description."""
    score: float = Field(..., ge=0, le=100)
    word_count: int
    has_hook: bool
    has_bullet_points: bool
    has_cta: bool
    has_html_formatting: bool
    readability_grade: float
    emotional_words: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class KeywordAnalysis(BaseModel):
    """Analysis of keyword usage in the listing."""
    score: float = Field(..., ge=0, le=100)
    keywords_found: list[str] = Field(default_factory=list)
    keyword_density: float
    missing_high_value_keywords: list[str] = Field(default_factory=list)
    over_stuffed: bool = False


class CategoryAnalysis(BaseModel):
    """Analysis of the listing's category fit."""
    score: float = Field(..., ge=0, le=100)
    current_categories: list[str] = Field(default_factory=list)
    suggested_categories: list[str] = Field(default_factory=list)
    category_rank_potential: Optional[str] = None


class PriceAnalysis(BaseModel):
    """Analysis of the listing's pricing."""
    score: float = Field(..., ge=0, le=100)
    current_price: Optional[float] = None
    genre_avg_price: Optional[float] = None
    suggested_range: Optional[str] = None
    issues: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ListingAnalysis(BaseModel):
    """Full listing analysis response."""
    model_config = ConfigDict(from_attributes=True)

    asin: Optional[str] = None
    title: Optional[str] = None
    title_score: float = Field(..., ge=0, le=100)
    blurb_score: float = Field(..., ge=0, le=100)
    keyword_score: float = Field(..., ge=0, le=100)
    category_score: float = Field(..., ge=0, le=100)
    price_score: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    title_analysis: TitleAnalysis
    blurb_analysis: BlurbAnalysis
    keyword_analysis: KeywordAnalysis
    category_analysis: CategoryAnalysis
    price_analysis: PriceAnalysis
    recommendations: list[Recommendation] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class BlurbVariant(BaseModel):
    """A single generated blurb variant."""
    variant_id: str
    content: str
    style: str
    hook_type: str
    estimated_conversion_score: float = Field(..., ge=0, le=100)
    highlights: list[str] = Field(default_factory=list)


class BlurbGenerateResponse(BaseModel):
    """Response with generated blurb variants."""
    original_score: float = Field(..., ge=0, le=100)
    variants: list[BlurbVariant]
    generation_metadata: dict = Field(default_factory=dict)


class ABTestVariantResult(BaseModel):
    """Results for a single A/B test variant."""
    variant_label: str
    content: str
    impressions: int = 0
    clicks: int = 0
    click_through_rate: float = 0.0
    conversion_rate: float = 0.0
    estimated_score: float = Field(default=0.0, ge=0, le=100)


class ABTestResponse(BaseModel):
    """A/B test configuration and results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    name: str
    status: ABTestStatus
    variant_a: ABTestVariantResult
    variant_b: ABTestVariantResult
    winner: Optional[str] = None
    confidence: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LookInsideSection(BaseModel):
    """Analysis of a section of the Look Inside preview."""
    section: str
    score: float = Field(..., ge=0, le=100)
    feedback: str
    suggestions: list[str] = Field(default_factory=list)


class LookInsideAnalysis(BaseModel):
    """Look Inside preview analysis response."""
    overall_score: float = Field(..., ge=0, le=100)
    hook_strength: float = Field(..., ge=0, le=100)
    first_page_impact: float = Field(..., ge=0, le=100)
    pacing_score: float = Field(..., ge=0, le=100)
    toc_effectiveness: float = Field(..., ge=0, le=100)
    sections: list[LookInsideSection] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)


class MobileTruncation(BaseModel):
    """Analysis of text truncation on mobile."""
    field: str
    original_length: int
    visible_length: int
    is_truncated: bool
    visible_text: str
    truncated_text: Optional[str] = None


class MobileCheckResult(BaseModel):
    """Mobile conversion check results."""
    overall_score: float = Field(..., ge=0, le=100)
    title_display: MobileTruncation
    subtitle_display: Optional[MobileTruncation] = None
    blurb_fold_point: int
    blurb_above_fold: str
    blurb_above_fold_word_count: int
    cover_aspect_ratio_ok: bool = True
    cover_readable_at_thumbnail: bool = True
    price_visibility: str = "good"
    buy_button_proximity: str = "optimal"
    recommendations: list[Recommendation] = Field(default_factory=list)
    device_previews: dict[str, dict] = Field(default_factory=dict)


class ConversionScores(BaseModel):
    """Aggregate conversion optimization scores for a book."""
    book_id: UUID
    listing_score: Optional[float] = None
    blurb_score: Optional[float] = None
    mobile_score: Optional[float] = None
    look_inside_score: Optional[float] = None
    overall_score: float = Field(..., ge=0, le=100)
    last_analyzed_at: Optional[datetime] = None
    recommendations_count: int = 0
