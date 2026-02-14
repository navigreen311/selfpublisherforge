"""Pydantic v2 schemas for the Product Page Conversion Lab."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
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
    asin: str | None = Field(None, min_length=10, max_length=10, pattern=r"^[A-Z0-9]{10}$")
    url: str | None = Field(None, max_length=500)
    book_id: UUID | None = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"asin": "B09V2KKG1D"},
            {"url": "https://www.amazon.com/dp/B09V2KKG1D"},
        ]
    })


class BlurbGenerateRequest(BaseModel):
    """Request to generate optimized blurb variations."""
    book_id: UUID | None = None
    current_blurb: str = Field(..., min_length=10, max_length=5000)
    genre: Genre = Genre.OTHER
    target_audience: str | None = Field(None, max_length=500)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    tone: str | None = Field(None, max_length=100)
    num_variants: int = Field(default=3, ge=1, le=5)


class ABTestCreateRequest(BaseModel):
    """Request to create an A/B test for blurbs."""
    book_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    variant_a: str = Field(..., min_length=10, max_length=5000)
    variant_b: str = Field(..., min_length=10, max_length=5000)
    duration_days: int = Field(default=7, ge=1, le=90)


class ABTestUpdateRequest(BaseModel):
    """Request to update an existing A/B test."""
    name: str | None = Field(None, min_length=1, max_length=200)
    variant_a: str | None = Field(None, min_length=10, max_length=5000)
    variant_b: str | None = Field(None, min_length=10, max_length=5000)
    duration_days: int | None = Field(None, ge=1, le=90)
    status: ABTestStatus | None = None


class LookInsideAnalyzeRequest(BaseModel):
    """Request to analyze the Look Inside preview effectiveness."""
    book_id: UUID | None = None
    preview_text: str = Field(..., min_length=50, max_length=20000)
    genre: Genre = Genre.OTHER
    chapter_titles: list[str] = Field(default_factory=list)


class MobileCheckRequest(BaseModel):
    """Request to check listing appearance on mobile."""
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: str | None = Field(None, max_length=500)
    blurb: str = Field(..., min_length=10, max_length=5000)
    author_name: str = Field(..., min_length=1, max_length=200)
    cover_image_url: str | None = Field(None, max_length=1000)
    price: float | None = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Sub-models for analysis results
# ---------------------------------------------------------------------------

class Recommendation(BaseModel):
    """A single recommendation for improving a listing element."""
    area: str
    severity: str = Field(..., pattern=r"^(critical|warning|info)$")
    message: str
    suggestion: str
    current_value: str | None = None
    recommended_value: str | None = None


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
    category_rank_potential: str | None = None


class PriceAnalysis(BaseModel):
    """Analysis of the listing's pricing."""
    score: float = Field(..., ge=0, le=100)
    current_price: float | None = None
    genre_avg_price: float | None = None
    suggested_range: str | None = None
    issues: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ListingAnalysis(BaseModel):
    """Full listing analysis response."""
    model_config = ConfigDict(from_attributes=True)

    asin: str | None = None
    title: str | None = None
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
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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
    winner: str | None = None
    confidence: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ABTestResultsResponse(BaseModel):
    """Detailed A/B test results with statistical analysis."""
    test_id: UUID
    name: str
    status: ABTestStatus
    variant_a: ABTestVariantResult
    variant_b: ABTestVariantResult
    winner: str | None = None
    confidence: float | None = None
    is_statistically_significant: bool = False
    sample_size_sufficient: bool = False
    minimum_sample_needed: int = 100
    days_running: int | None = None
    days_remaining: int | None = None


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
    truncated_text: str | None = None


class MobileCheckResult(BaseModel):
    """Mobile conversion check results."""
    overall_score: float = Field(..., ge=0, le=100)
    title_display: MobileTruncation
    subtitle_display: MobileTruncation | None = None
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
    listing_score: float | None = None
    blurb_score: float | None = None
    mobile_score: float | None = None
    look_inside_score: float | None = None
    overall_score: float = Field(..., ge=0, le=100)
    last_analyzed_at: datetime | None = None
    recommendations_count: int = 0


# ---------------------------------------------------------------------------
# Additional schemas for keyword optimization and A+ content
# ---------------------------------------------------------------------------

class OptimizeKeywordsRequest(BaseModel):
    """Request to optimize backend keywords."""
    book_id: UUID | None = None
    current_keywords: list[str] = Field(default_factory=list)
    genre: str = Field(default="other", max_length=100)
    title: str = Field(default="", max_length=500)


class KeywordRecommendation(BaseModel):
    """A single keyword recommendation."""
    keyword: str
    search_volume: int = 0
    competition: str = "medium"  # low, medium, high
    relevance: int = Field(default=3, ge=1, le=5)


class OptimizeKeywordsResponse(BaseModel):
    """Response with keyword recommendations."""
    recommended: list[KeywordRecommendation] = Field(default_factory=list)
    optimal_seven: list[str] = Field(default_factory=list)
    analysis_notes: str = ""


class APlusModuleSpec(BaseModel):
    """A single A+ content module specification."""
    module_type: str  # hero_banner, comparison_chart, feature_grid, author_story, social_proof
    title: str
    content: str = ""
    image_spec: dict = Field(default_factory=dict)  # {width, height}
    ai_copy: str = ""


class APlusPlanRequest(BaseModel):
    """Request to generate an A+ content plan."""
    book_id: UUID | None = None
    book_title: str = Field(default="", max_length=500)
    genre: str = Field(default="other", max_length=100)


class APlusPlanResponse(BaseModel):
    """Response with A+ content plan."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    modules: list[APlusModuleSpec] = Field(default_factory=list)
    status: str = "draft"


class ListingAnalysisListItem(BaseModel):
    """Summary item for listing analysis list."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asin: str | None = None
    overall_score: int | None = None
    created_at: datetime


class GenerateBlurbEnhancedRequest(BaseModel):
    """Enhanced blurb generation request with style options."""
    book_id: UUID | None = None
    title: str = Field(default="", max_length=500)
    selling_points: str = Field(default="", max_length=2000)
    target_reader: str = Field(default="", max_length=500)
    tone: str = Field(default="professional", max_length=100)
    style: str = Field(default="benefit_led", pattern=r"^(story_led|benefit_led|problem_solution)$")
    current_blurb: str | None = Field(None, max_length=5000)


class BlurbVersionResponse(BaseModel):
    """A single generated blurb version."""
    style: str
    html_content: str
    plain_content: str
    score: int = Field(default=0, ge=0, le=100)
    word_count: int = 0


class GenerateBlurbEnhancedResponse(BaseModel):
    """Response with multiple blurb versions."""
    versions: list[BlurbVersionResponse] = Field(default_factory=list)
