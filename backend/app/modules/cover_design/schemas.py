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
