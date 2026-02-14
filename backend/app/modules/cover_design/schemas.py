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


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CoverGenerateRequest(BaseModel):
    """Request body for generating an AI cover concept."""

    book_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    author_name: str = Field(..., min_length=1, max_length=200)
    genre: CoverGenre
    mood: str | None = Field(
        None,
        max_length=200,
        description="Mood/tone keywords, e.g. 'dark, moody, suspenseful'",
    )
    style_keywords: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Visual style keywords",
    )
    color_palette: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Hex color codes or named colours",
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


# ---------------------------------------------------------------------------
# Editor & Export schemas
# ---------------------------------------------------------------------------


class EditorState(BaseModel):
    """Editor state for a cover design."""

    layers: list[dict[str, Any]] = Field(default_factory=list)
    canvas_dimensions: dict[str, int] | None = None
    active_layer_id: str | None = None
    zoom_level: float = 1.0
    history: list[dict[str, Any]] = Field(default_factory=list)
    custom_data: dict[str, Any] = Field(default_factory=dict)


class UpdateEditorStateRequest(BaseModel):
    """Request to update editor state."""

    editor_state: EditorState


class ExportFormat(str, Enum):
    PNG = "png"
    JPG = "jpg"
    PDF = "pdf"
    PSD = "psd"


class ExportRequest(BaseModel):
    """Request to export a cover design."""

    format: ExportFormat = ExportFormat.PNG
    dpi: int = Field(300, ge=72, le=600)
    include_bleed: bool = False
    color_profile: str | None = Field(None, description="e.g., 'sRGB', 'Adobe RGB'")


class ExportResponse(BaseModel):
    """Response containing export URL and metadata."""

    export_url: str
    format: ExportFormat
    file_size_bytes: int
    dimensions: CoverDimensions
    created_at: datetime


# ---------------------------------------------------------------------------
# AB Testing schemas
# ---------------------------------------------------------------------------


class ABTestStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    DRAFT = "draft"


class CreateABTestRequest(BaseModel):
    """Request to create an A/B test."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    cover_a_id: UUID
    cover_b_id: UUID
    target_audience: str | None = Field(None, max_length=500)
    duration_days: int = Field(7, ge=1, le=90)
    public_url_enabled: bool = True


class ABTestResponse(BaseModel):
    """Response for an A/B test."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    description: str | None
    cover_a_id: UUID
    cover_b_id: UUID
    status: ABTestStatus
    votes_a: int = 0
    votes_b: int = 0
    public_url: str | None
    target_audience: str | None
    duration_days: int
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VoteRequest(BaseModel):
    """Request to vote on an A/B test."""

    choice: str = Field(..., pattern="^(a|b)$", description="Must be 'a' or 'b'")
    voter_fingerprint: str | None = Field(None, max_length=500, description="Optional fingerprint to prevent duplicate votes")


class VoteResponse(BaseModel):
    """Response after voting."""

    success: bool
    message: str
    current_votes_a: int
    current_votes_b: int


class EndABTestRequest(BaseModel):
    """Request to end an A/B test."""

    winner: str | None = Field(None, pattern="^(a|b|tie)$", description="Declare winner: 'a', 'b', or 'tie'")
    notes: str | None = Field(None, max_length=2000)


# ---------------------------------------------------------------------------
# List/Query schemas
# ---------------------------------------------------------------------------


class CoverListSortBy(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TITLE = "title"
    STATUS = "status"


class CoverFormat(str, Enum):
    ALL = "all"
    EBOOK = "ebook"
    PRINT = "print"
    AUDIOBOOK = "audiobook"


# ---------------------------------------------------------------------------
# Generation Job schemas
# ---------------------------------------------------------------------------


class GenerationJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationJobResponse(BaseModel):
    """Response for async cover generation job."""

    job_id: str
    status: GenerationJobStatus
    progress: int = Field(0, ge=0, le=100)
    cover_id: UUID | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
