"""Pydantic v2 schemas for the Cover Design Studio."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CoverGenre(str, Enum):
    ROMANCE = "romance"
    THRILLER = "thriller"
    MYSTERY = "mystery"
    SCI_FI = "sci-fi"
    FANTASY = "fantasy"
    HORROR = "horror"
    LITERARY_FICTION = "literary-fiction"
    NONFICTION = "nonfiction"
    SELF_HELP = "self-help"
    BUSINESS = "business"
    CHILDRENS = "childrens"
    YOUNG_ADULT = "young-adult"
    MEMOIR = "memoir"
    COOKBOOK = "cookbook"
    OTHER = "other"


class CoverStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class CoverPlatform(str, Enum):
    AMAZON_KDP = "amazon-kdp"
    INGRAM_SPARK = "ingram-spark"
    BARNES_NOBLE = "barnes-noble"
    APPLE_BOOKS = "apple-books"
    GOOGLE_PLAY = "google-play"
    CUSTOM = "custom"


class CoverArtStyle(str, Enum):
    PHOTOREALISTIC = "photorealistic"
    ILLUSTRATED = "illustrated"
    MINIMALIST = "minimalist"
    ABSTRACT = "abstract"
    TYPOGRAPHY_FOCUSED = "typography-focused"
    VINTAGE = "vintage"
    MODERN = "modern"
    WATERCOLOR = "watercolor"
    DIGITAL_ART = "digital-art"
    MIXED_MEDIA = "mixed-media"


class CoverFormat(str, Enum):
    PRINT = "print"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"
    BOTH = "both"


class ExportFormat(str, Enum):
    PNG_72 = "png_72"
    PNG_300 = "png_300"
    PDF = "pdf"
    JPEG = "jpeg"


class ABTestStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


# ---------------------------------------------------------------------------
# Request schemas - Cover CRUD
# ---------------------------------------------------------------------------


class CoverCreate(BaseModel):
    """Request body for creating a new cover."""

    book_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    author_name: str = Field(..., min_length=1, max_length=200)
    genre: CoverGenre
    platform: CoverPlatform = CoverPlatform.AMAZON_KDP
    image_url: str | None = None
    thumbnail_url: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    dpi: int = 300
    bleed_px: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    editor_state: dict[str, Any] | None = Field(
        None,
        description="JSONB editor state (layers, elements, canvas settings)",
    )


class CoverUpdate(BaseModel):
    """Request body for updating an existing cover."""

    title: str | None = Field(None, min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    author_name: str | None = Field(None, min_length=1, max_length=200)
    genre: CoverGenre | None = None
    status: CoverStatus | None = None
    platform: CoverPlatform | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    dpi: int | None = None
    bleed_px: int | None = None
    metadata: dict[str, Any] | None = None
    editor_state: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CoverGenerateRequest(BaseModel):
    """Request body for generating an AI cover concept."""

    book_id: UUID | None = None
    project_id: UUID | None = Field(
        None,
        description="Optional project to associate the cover with",
    )
    title: str = Field(..., min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    author_name: str = Field(..., min_length=1, max_length=200)
    genre: CoverGenre
    description: str | None = Field(
        None,
        max_length=2000,
        description="Detailed description of desired cover concept",
    )
    mood: str | None = Field(
        None,
        max_length=200,
        description="Mood/tone keywords, e.g. dark, moody, suspenseful",
    )
    style_keywords: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Visual style keywords",
    )
    art_style: CoverArtStyle | None = Field(
        None,
        description="Preferred artistic style for the cover",
    )
    color_palette: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Hex color codes or named colours",
    )
    reference_image_urls: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="URLs of reference images for style inspiration",
    )
    format: CoverFormat = Field(
        CoverFormat.PRINT,
        description="Target format (print, ebook, both)",
    )
    trim_size: str | None = Field(
        None,
        description="Book trim size (e.g., 6x9, 5.5x8.5)",
    )
    page_count: int | None = Field(
        None,
        ge=1,
        le=2000,
        description="Book page count for spine width calculation",
    )
    paper_type: str | None = Field(
        None,
        description="Paper type (e.g., white, cream, standard)",
    )
    variations_count: int = Field(
        2,
        ge=2,
        le=8,
        description="Number of variations to generate (2, 4, 6, or 8)",
    )
    platform: CoverPlatform = CoverPlatform.AMAZON_KDP
    additional_instructions: str | None = Field(None, max_length=2000)


class CoverVariationRequest(BaseModel):
    """Request body for generating variations of an existing cover."""

    variation_count: int = Field(3, ge=1, le=10)
    variation_type: str = Field(
        "style",
        description="Type of variation: 'style', 'color', 'layout', 'typography'",
    )
    instructions: str | None = Field(None, max_length=2000)


class CompetitorCoverAnalysisRequest(BaseModel):
    """Request body for analysing competitor covers."""

    genre: CoverGenre
    niche_keywords: list[str] = Field(..., min_length=1, max_length=20)
    competitor_image_urls: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="URLs of competitor cover images to analyse",
    )
    max_results: int = Field(10, ge=1, le=50)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CoverDimensions(BaseModel):
    width_px: int
    height_px: int
    dpi: int = 300
    bleed_px: int = 0


class CoverResponse(BaseModel):
    """Represents a single generated cover."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID | None = None
    title: str
    subtitle: str | None = None
    author_name: str
    genre: CoverGenre
    status: CoverStatus
    image_url: str | None = None
    thumbnail_url: str | None = None
    prompt_used: str | None = None
    dimensions: CoverDimensions | None = None
    platform: CoverPlatform
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CoverTemplateResponse(BaseModel):
    """A cover template entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    genre: CoverGenre
    description: str
    thumbnail_url: str | None = None
    dimensions: CoverDimensions
    font_recommendations: list[str] = Field(default_factory=list)
    layout_guidance: str | None = None
    tags: list[str] = Field(default_factory=list)


class ColorAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hex_code: str
    percentage: float
    name: str | None = None


class CompetitorCoverAnalysis(BaseModel):
    """Result of analysing a single competitor cover."""

    model_config = ConfigDict(from_attributes=True)

    image_url: str | None = None
    dominant_colors: list[ColorAnalysis] = Field(default_factory=list)
    text_placement: str | None = None
    imagery_style: str | None = None
    overall_mood: str | None = None
    font_style: str | None = None
    effectiveness_score: float | None = Field(None, ge=0, le=10)


class CompetitorAnalysisResponse(BaseModel):
    """Aggregated competitor cover analysis."""

    model_config = ConfigDict(from_attributes=True)

    genre: CoverGenre
    niche_keywords: list[str]
    analyses: list[CompetitorCoverAnalysis] = Field(default_factory=list)
    trends: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


# Additional response and request schemas added for comprehensive coverage


class CoverGenerateJobResponse(BaseModel):
    """Response after initiating cover generation job."""

    job_id: str = Field(..., description="Unique job ID for tracking generation")
    message: str = Field(
        default="Cover generation job started",
        description="Status message",
    )
    estimated_time_seconds: int | None = Field(
        None,
        description="Estimated completion time in seconds",
    )


class CoverGenerateStatusResponse(BaseModel):
    """Status response for a cover generation job."""

    job_id: str
    status: CoverStatus
    progress: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Completion percentage (0-100)",
    )
    message: str | None = None
    covers: list[CoverResponse] = Field(
        default_factory=list,
        description="Generated covers (populated when completed)",
    )
    error: str | None = Field(
        None,
        description="Error message if status is FAILED",
    )
    created_at: datetime
    updated_at: datetime


class CoverDetailResponse(CoverResponse):
    """Detailed cover response including editor state."""

    editor_state: dict[str, Any] | None = Field(
        None,
        description="Full editor state with layers and canvas settings",
    )
    variations: list[CoverResponse] = Field(
        default_factory=list,
        description="Cover variations derived from this cover",
    )
    parent_cover_id: UUID | None = Field(
        None,
        description="ID of parent cover if this is a variation",
    )


class CoverListResponse(BaseModel):
    """Paginated list of covers."""

    covers: list[CoverResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool


class CoverTemplateListResponse(BaseModel):
    """List of cover templates."""

    templates: list[CoverTemplateResponse]
    total: int
    filters_applied: dict[str, Any] | None = None


class CoverEditorStateUpdate(BaseModel):
    """Request body for updating cover editor state."""

    state: dict[str, Any] = Field(
        ...,
        description="Complete editor state as JSONB (layers, elements, canvas)",
    )


class CoverExportRequest(BaseModel):
    """Request body for exporting a cover."""

    format: ExportFormat = Field(
        ExportFormat.PNG_300,
        description="Export format (png_72, png_300, pdf, jpeg)",
    )
    include_bleed: bool = Field(
        False,
        description="Include bleed area in export",
    )
    watermark: bool = Field(
        False,
        description="Add watermark to the export",
    )


class CoverExportResponse(BaseModel):
    """Response after exporting a cover."""

    download_url: str = Field(..., description="URL to download the exported file")
    format: ExportFormat
    file_size_bytes: int | None = None
    expires_at: datetime | None = Field(
        None,
        description="URL expiration timestamp",
    )


class ABTestCreate(BaseModel):
    """Request body for creating an A/B test."""

    name: str = Field(..., min_length=1, max_length=200)
    cover_ids: list[UUID] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of cover IDs to test (minimum 2)",
    )
    description: str | None = Field(None, max_length=1000)


class ABTestVoteRequest(BaseModel):
    """Request body for voting in an A/B test."""

    cover_id: UUID = Field(..., description="ID of the cover being voted for")
    voter_metadata: dict[str, Any] | None = Field(
        None,
        description="Optional metadata about voter (IP, user agent, etc.)",
    )


class ABTestVoteResponse(BaseModel):
    """Response after submitting a vote."""

    success: bool
    message: str = "Vote recorded successfully"
    total_votes: int | None = None


class CoverVoteStats(BaseModel):
    """Vote statistics for a single cover in an A/B test."""

    cover_id: UUID
    votes: int
    percentage: float = Field(..., ge=0, le=100)
    thumbnail_url: str | None = None


class ABTestResponse(BaseModel):
    """Response for an A/B test."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    description: str | None = None
    cover_ids: list[UUID]
    status: ABTestStatus
    share_token: str = Field(
        ...,
        description="Unique token for sharing the test publicly",
    )
    share_url: str = Field(
        ...,
        description="Public URL for the A/B test voting page",
    )
    votes: list[CoverVoteStats] = Field(
        default_factory=list,
        description="Vote statistics per cover",
    )
    total_votes: int = 0
    winner_cover_id: UUID | None = Field(
        None,
        description="ID of winning cover (if test is completed)",
    )
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class ABTestListResponse(BaseModel):
    """Paginated list of A/B tests."""

    tests: list[ABTestResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool
