"""Pydantic schemas for Coloring Book quality pipeline and batch generation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ColoringMedium(str, Enum):
    MARKER = "marker"
    CRAYON = "crayon"
    COLORED_PENCIL = "colored_pencil"


class VariationMode(str, Enum):
    NONE = "none"
    MILD = "mild"
    STRONG = "strong"


class PipelineStepName(str, Enum):
    GENERATE = "generate"
    AUTO_CLEAN = "auto_clean"
    STROKE_UNIFORMITY = "stroke_uniformity"
    CLOSED_SHAPES = "closed_shapes"
    SPECK_REMOVAL = "speck_removal"
    BACKGROUND = "background"
    QUALITY_CHECK = "quality_check"


class ComplexityBucket(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    DETAILED = "detailed"
    INTRICATE = "intricate"


class GenerateLineArtRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    style_hints: dict[str, Any] | None = Field(None, description="Optional style hints")


class GenerateLineArtResponse(BaseModel):
    page_id: UUID
    illustration_url: str
    illustration_model: str
    illustration_seed: int | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PipelineStepResult(BaseModel):
    step: PipelineStepName
    passed: bool
    details: str | None = None
    before_value: Any | None = None
    after_value: Any | None = None
    duration_ms: int | None = None


class QualityPipelineResponse(BaseModel):
    page_id: UUID
    overall_passed: bool
    steps: list[PipelineStepResult]
    cleaned_url: str | None = None
    run_at: datetime


class VectorizeResponse(BaseModel):
    page_id: UUID
    vectorized_url: str
    format: str = Field(default="svg", description="svg or pdf")
    path_count: int | None = None


class InkDensityResult(BaseModel):
    page_id: UUID
    ink_coverage_pct: float = Field(..., ge=0.0, le=100.0)
    passed: bool
    threshold_pct: float = 40.0
    heavy_regions: list[dict[str, Any]] = Field(default_factory=list)


class DuplicatePair(BaseModel):
    page_a_id: UUID
    page_b_id: UUID
    similarity_score: float = Field(..., ge=0.0, le=100.0)
    method: str = Field(default="phash", description="phash or ssim")


class DuplicateDetectionResponse(BaseModel):
    book_id: UUID
    total_pages: int
    duplicate_pairs: list[DuplicatePair] = Field(default_factory=list)
    has_duplicates: bool = False


class ThemeCohesionResponse(BaseModel):
    book_id: UUID
    cohesion_score: float = Field(..., ge=0.0, le=100.0)
    analysis: str | None = None
    outlier_page_ids: list[UUID] = Field(default_factory=list)


class ColoringSimulationRequest(BaseModel):
    medium: ColoringMedium


class ColoringSimulationResponse(BaseModel):
    page_id: UUID
    medium: ColoringMedium
    simulation_url: str
    created_at: datetime


class ComplexityBucketCount(BaseModel):
    bucket: ComplexityBucket
    count: int
    page_ids: list[UUID] = Field(default_factory=list)


class ComplexityHistogramResponse(BaseModel):
    book_id: UUID
    total_pages: int
    distribution: list[ComplexityBucketCount] = Field(default_factory=list)


class BatchPageDescription(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)
    complexity: ComplexityBucket | None = None


class BatchGenerateRequest(BaseModel):
    descriptions: list[BatchPageDescription] = Field(..., min_length=1, max_length=60)
    variation_mode: VariationMode = VariationMode.MILD
    auto_qa: bool = Field(default=True, description="Run quality pipeline after generation")


class BatchGenerateResponse(BaseModel):
    job_id: UUID
    book_id: UUID
    total_pages: int
    estimated_cost_cents: int | None = None
    status: str = "queued"
    created_at: datetime


class BatchPageStatus(BaseModel):
    page_number: int
    page_id: UUID | None = None
    status: str = "pending"
    qa_passed: bool | None = None
    error: str | None = None


class BatchStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    total_pages: int = 0
    pages_completed: int = 0
    pages_failed: int = 0
    page_statuses: list[BatchPageStatus] = Field(default_factory=list)
    estimated_cost_cents: int | None = None
    spent_cents: int = 0


class PrintQualitySummary(BaseModel):
    line_quality_score: float = Field(0.0, ge=0.0, le=100.0)
    closed_shapes_score: float = Field(0.0, ge=0.0, le=100.0)
    stroke_uniformity_score: float = Field(0.0, ge=0.0, le=100.0)
    ink_density_score: float = Field(0.0, ge=0.0, le=100.0)
    small_areas_score: float = Field(0.0, ge=0.0, le=100.0)


class QualityDashboardResponse(BaseModel):
    book_id: UUID
    overall_score: float = Field(0.0, ge=0.0, le=100.0)
    total_pages: int = 0
    pages_passed: int = 0
    pages_failed: int = 0
    complexity_distribution: list[ComplexityBucketCount] = Field(default_factory=list)
    theme_cohesion: float = Field(0.0, ge=0.0, le=100.0)
    print_quality: PrintQualitySummary = Field(default_factory=PrintQualitySummary)
    duplicate_pairs_count: int = 0
    recommendations: list[str] = Field(default_factory=list)


class PageQualityCheckResponse(BaseModel):
    page_id: UUID
    overall_passed: bool
    ink_density: InkDensityResult | None = None
    pipeline: QualityPipelineResponse | None = None
    complexity_bucket: ComplexityBucket | None = None
