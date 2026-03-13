"""Pydantic schemas for the Coloring Book Creator."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas_shared import PreflightCheck, TrimSize


class ColoringAudience(str, Enum):
    TODDLER = "toddler"
    KIDS = "kids"
    TEEN = "teen"
    ADULT = "adult"


class LineStyle(str, Enum):
    CLEAN_VECTOR = "clean_vector"
    HAND_DRAWN = "hand_drawn"
    MANDALA = "mandala"
    ZENTANGLE = "zentangle"
    REALISTIC = "realistic"
    CARTOON = "cartoon"


class ColoringPageType(str, Enum):
    COLORING = "coloring"
    COVER = "cover"
    TITLE = "title"
    BACK_COVER = "back_cover"
    INSTRUCTION = "instruction"


class ColoringMedium(str, Enum):
    MARKER = "marker"
    CRAYON = "crayon"
    PENCIL = "pencil"
    WATERCOLOR = "watercolor"


class ColoringExportFormat(str, Enum):
    PRINT_PDF = "print_pdf"
    KPF = "kpf"
    FIXED_EPUB = "fixed_epub"
    PNG = "png"
    SVG = "svg"


class ColoringBookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    audience: ColoringAudience = ColoringAudience.ADULT
    page_count: int = Field(30, ge=10, le=200)
    trim_size: TrimSize = TrimSize.SIZE_8_5X11
    line_style: LineStyle = LineStyle.CLEAN_VECTOR
    line_weight: float = Field(2.0, ge=0.5, le=10.0)
    complexity: str = Field("medium", pattern="^(simple|medium|complex)$")
    stroke_uniformity: float = Field(0.9, ge=0.0, le=1.0)
    single_sided: bool = True
    theme: str | None = Field(None, max_length=255)
    template_id: UUID | None = None


class ColoringBookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    audience: ColoringAudience | None = None
    page_count: int | None = Field(None, ge=10, le=200)
    trim_size: TrimSize | None = None
    line_style: LineStyle | None = None
    line_weight: float | None = Field(None, ge=0.5, le=10.0)
    complexity: str | None = Field(None, pattern="^(simple|medium|complex)$")
    stroke_uniformity: float | None = Field(None, ge=0.0, le=1.0)
    single_sided: bool | None = None
    theme: str | None = Field(None, max_length=255)


class ColoringBookResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    subtitle: str | None = None
    author: str
    audience: ColoringAudience
    page_count: int
    trim_size: TrimSize
    line_style: LineStyle
    line_weight: float
    complexity: str
    stroke_uniformity: float
    single_sided: bool = True
    theme: str | None = None
    template_id: UUID | None = None
    status: str = "draft"
    qa_score: float | None = Field(None, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ColoringBookListResponse(BaseModel):
    items: list[ColoringBookResponse]
    total: int


class ColoringPageResponse(BaseModel):
    id: UUID
    book_id: UUID
    page_number: int
    page_type: ColoringPageType
    illustration_prompt: str | None = None
    illustration_url: str | None = None
    cleaned_url: str | None = None
    vectorized_url: str | None = None
    illustration_model: str | None = None
    illustration_seed: int | None = None
    line_quality: float | None = Field(None, ge=0.0, le=100.0)
    closed_shapes: float | None = Field(None, ge=0.0, le=100.0)
    stroke_uniform: float | None = Field(None, ge=0.0, le=100.0)
    speck_free: float | None = Field(None, ge=0.0, le=100.0)
    ink_density: float | None = Field(None, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class GenerateLineArtRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    style_override: LineStyle | None = None
    complexity_override: str | None = Field(None, pattern="^(simple|medium|complex)$")
    seed: int | None = None


class GenerateLineArtResponse(BaseModel):
    page_id: UUID
    illustration_url: str
    seed: int
    model: str
    provenance_id: UUID | None = None


class PipelineStep(BaseModel):
    step_name: str
    before_url: str
    after_url: str
    metrics_delta: dict[str, float] | None = None


class CleanLinesResponse(BaseModel):
    page_id: UUID
    pipeline_steps: list[PipelineStep] = Field(default_factory=list)
    final_url: str
    quality_before: float = Field(..., ge=0.0, le=100.0)
    quality_after: float = Field(..., ge=0.0, le=100.0)


class VectorizeResponse(BaseModel):
    page_id: UUID
    svg_url: str
    node_count: int | None = None
    file_size_bytes: int | None = None


class QualityMetric(BaseModel):
    name: str
    score: float = Field(..., ge=0.0, le=100.0)
    passed: bool = True
    threshold: float = Field(70.0, ge=0.0, le=100.0)


class QualityIssue(BaseModel):
    page_number: int | None = None
    metric: str
    description: str
    severity: str = Field("warning", pattern="^(info|warning|error)$")
    auto_fixable: bool = False


class QualityCheckResponse(BaseModel):
    book_id: UUID
    page_id: UUID | None = None
    overall_score: float = Field(..., ge=0.0, le=100.0)
    metrics: list[QualityMetric] = Field(default_factory=list)
    issues: list[QualityIssue] = Field(default_factory=list)
    passed: bool = True


class PageDescription(BaseModel):
    page_number: int = Field(..., ge=1)
    prompt: str = Field(..., min_length=1, max_length=2000)
    complexity_override: str | None = Field(None, pattern="^(simple|medium|complex)$")


class BatchGenerateRequest(BaseModel):
    page_descriptions: list[PageDescription] = Field(..., min_length=1)
    variation_mode: bool = False
    auto_clean: bool = True


class BatchGenerateResponse(BaseModel):
    job_id: UUID
    total_pages: int
    estimated_seconds: int | None = None


class PageBatchStatus(BaseModel):
    page_number: int
    status: str
    illustration_url: str | None = None
    error: str | None = None


class BatchStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress: float = Field(0.0, ge=0.0, le=100.0)
    pages_total: int = 0
    pages_completed: int = 0
    per_page_status: list[PageBatchStatus] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ColoringSimulationRequest(BaseModel):
    medium: ColoringMedium
    color_scheme: str | None = Field(None, max_length=255)
    custom_colors: list[str] | None = None


class ColoringSimulationResponse(BaseModel):
    page_id: UUID
    medium: ColoringMedium
    preview_url: str
    colors_used: list[str] = Field(default_factory=list)


class SeriesPlanRequest(BaseModel):
    series_name: str = Field(..., min_length=1, max_length=255)
    total_volumes: int = Field(..., ge=2, le=50)
    themes: list[str] = Field(..., min_length=1)
    pages_per_volume: int = Field(30, ge=10, le=200)
    naming_format: str | None = Field(None, max_length=255)
    branding_config: dict[str, Any] | None = None


class VolumePlan(BaseModel):
    volume_number: int
    title: str
    theme: str
    page_count: int
    description: str | None = None


class SeriesPlanResponse(BaseModel):
    series_id: UUID | None = None
    series_name: str
    volumes: list[VolumePlan] = Field(default_factory=list)
    total_pages: int = 0


class VolumeFactoryResponse(BaseModel):
    book_id: UUID
    volume_number: int
    title: str
    page_count: int
    status: str = "draft"
    created_at: datetime


class ColoringExportRequest(BaseModel):
    format: ColoringExportFormat


class ColoringExportResponse(BaseModel):
    book_id: UUID
    format: ColoringExportFormat
    url: str
    file_size_bytes: int | None = None
    preflight_results: list[PreflightCheck] | None = None


class ColoringPreflightResponse(BaseModel):
    book_id: UUID
    checks: list[PreflightCheck] = Field(default_factory=list)
    all_passed: bool = False
    total_checks: int = 0
    passed_count: int = 0
    failed_count: int = 0
