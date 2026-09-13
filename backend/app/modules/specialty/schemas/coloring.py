"""Pydantic v2 schemas for the Coloring Book Creator."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Audience(str, Enum):
    KIDS = "kids"  # 3-8
    TEENS = "teens"  # 9-14
    ADULTS = "adults"  # 15+


class LineStyle(str, Enum):
    CLEAN_OUTLINES = "clean-outlines"
    SKETCHY_HAND_DRAWN = "sketchy-hand-drawn"
    WHIMSICAL_DECORATIVE = "whimsical-decorative"
    REALISTIC_DETAILED = "realistic-detailed"
    ZENTANGLE = "zentangle"
    BOLD_SIMPLE = "bold-simple"


class ColoringPageType(str, Enum):
    COLORING = "coloring"
    TITLE = "title"
    BELONGS_TO = "belongs-to"
    COLOR_TEST = "color-test"
    PROGRESS_TRACKER = "progress-tracker"
    CERTIFICATE = "certificate"
    DIFFICULTY_RATING = "difficulty-rating"
    BLANK_BACK = "blank-back"


class QualityStep(str, Enum):
    """Steps in the 7-step line art quality pipeline."""

    GENERATE = "generate"
    AUTO_CLEAN = "auto-clean"
    STROKE_UNIFORMITY = "stroke-uniformity"
    CLOSED_SHAPES = "closed-shapes"
    SPECK_REMOVAL = "speck-removal"
    BACKGROUND = "background"
    QUALITY_CHECK = "quality-check"


class ColoringBookStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ColoringExportFormat(str, Enum):
    PRINT_PDF = "print-pdf"
    INDIVIDUAL_PNG = "individual-png"
    SVG_VECTOR = "svg-vector"
    DIGITAL_PDF = "digital-pdf"


class VariationMode(str, Enum):
    """Controls how batch generation prevents similar compositions."""

    DIVERSE = "diverse"
    THEMED = "themed"
    PROGRESSIVE = "progressive"


class ColoringSimulationMedia(str, Enum):
    """Media types for coloring simulation preview."""

    MARKER = "marker"
    CRAYON = "crayon"
    COLORED_PENCIL = "colored-pencil"


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


class ColoringBookCreate(BaseModel):
    """Create a new coloring book project."""

    title: str = Field(..., min_length=1, max_length=300, description="Book title")
    subtitle: str | None = Field(None, max_length=300, description="Optional subtitle")
    audience: Audience = Field(..., description="Target audience")
    page_count: int = Field(..., ge=20, le=60, description="Number of coloring pages")
    trim_size: str = Field(..., max_length=20, description="Trim size, e.g. '8.5x11'")
    line_style: LineStyle = Field(..., description="Line art style")
    line_weight: float = Field(
        2.0,
        ge=0.5,
        le=5.0,
        description="Line weight / thickness in points",
    )
    complexity: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Complexity slider (0 = simple, 1 = highly detailed)",
    )
    stroke_uniformity: bool = Field(True, description="Enforce uniform stroke thickness across pages")
    single_sided: bool = Field(True, description="Single-sided layout with blank backs (enforced for print)")
    theme_description: str | None = Field(
        None, max_length=2000, description="Overall theme or description for content generation"
    )
    series_id: UUID | None = Field(None, description="Series ID if part of a multi-volume set")
    volume_number: int | None = Field(None, ge=1, description="Volume number within the series")


class ColoringBookUpdate(BaseModel):
    """Update a coloring book. All fields optional."""

    title: str | None = Field(None, min_length=1, max_length=300)
    subtitle: str | None = Field(None, max_length=300)
    audience: Audience | None = None
    page_count: int | None = Field(None, ge=20, le=60)
    trim_size: str | None = Field(None, max_length=20)
    line_style: LineStyle | None = None
    line_weight: float | None = Field(None, ge=0.5, le=5.0)
    complexity: float | None = Field(None, ge=0.0, le=1.0)
    stroke_uniformity: bool | None = None
    single_sided: bool | None = None
    theme_description: str | None = Field(None, max_length=2000)
    series_id: UUID | None = None
    volume_number: int | None = Field(None, ge=1)


class ColoringBookResponse(BaseModel):
    """Full coloring book record returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    title: str
    subtitle: str | None = None
    audience: Audience
    page_count: int
    trim_size: str
    line_style: LineStyle
    line_weight: float
    complexity: float
    stroke_uniformity: bool
    single_sided: bool
    theme_description: str | None = None
    series_id: UUID | None = None
    volume_number: int | None = None
    status: ColoringBookStatus
    qa_score: float | None = Field(None, ge=0, le=100, description="Overall QA score")
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


class ColoringPageResponse(BaseModel):
    """Full coloring page record with quality pipeline data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    page_number: int
    page_type: ColoringPageType
    illustration_prompt: str | None = None
    illustration_url: str | None = Field(None, description="URL of the raw generated image")
    cleaned_url: str | None = Field(None, description="URL after line-art cleanup pipeline")
    vectorized_url: str | None = Field(None, description="URL of the SVG vectorized version")
    illustration_model: str | None = None
    illustration_seed: int | None = None
    # Quality pipeline scores
    line_quality_score: float | None = Field(None, ge=0, le=100)
    closed_shapes_score: float | None = Field(None, ge=0, le=100)
    stroke_uniformity_score: float | None = Field(None, ge=0, le=100)
    speck_count: int | None = Field(None, ge=0, description="Number of stray specks detected")
    ink_density: float | None = Field(None, ge=0, le=100, description="Ink density percentage")
    background_pure_white: bool | None = None
    complexity_score: float | None = Field(None, ge=0, le=100)
    quality_pipeline_step: QualityStep | None = Field(None, description="Last completed pipeline step")
    quality_passed: bool | None = Field(None, description="True if final quality check passed")
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Line Art Generation & Cleanup
# ---------------------------------------------------------------------------


class GenerateLineArtRequest(BaseModel):
    """Generate line art for a single coloring page."""

    description: str = Field(..., min_length=1, max_length=2000, description="Description of the image to generate")
    line_style: LineStyle | None = Field(None, description="Override book-level line style for this page")
    complexity: float | None = Field(None, ge=0.0, le=1.0, description="Override complexity for this page")
    run_cleanup: bool = Field(True, description="Automatically run the cleanup pipeline after generation")


class CleanLinesRequest(BaseModel):
    """Run the line art cleanup pipeline on a page."""

    steps: list[QualityStep] | None = Field(
        None,
        description="Specific pipeline steps to run; None = run all steps",
    )
    line_weight_override: float | None = Field(None, ge=0.5, le=5.0, description="Override target line weight")


class VectorizeRequest(BaseModel):
    """Convert a coloring page to SVG vectors."""

    output_format: str = Field("svg", description="Output format: 'svg' or 'pdf'")
    simplify_paths: bool = Field(True, description="Simplify vector paths for smaller file size")
    stroke_width: float | None = Field(None, ge=0.5, le=5.0, description="Override stroke width in vectors")


# ---------------------------------------------------------------------------
# Quality Check
# ---------------------------------------------------------------------------


class QualityStepResult(BaseModel):
    """Result of a single quality pipeline step."""

    step: QualityStep
    passed: bool
    score: float | None = Field(None, ge=0, le=100)
    issues_found: int = Field(0, ge=0)
    details: str | None = None


class QualityIssue(BaseModel):
    """A specific quality issue found on a page."""

    issue_type: str = Field(
        ...,
        description="e.g. 'gray-artifact', 'open-shape', 'uneven-stroke', 'stray-speck', 'high-ink-density'",
    )
    severity: str = Field(..., description="'info', 'warning', or 'error'")
    description: str
    location: str | None = Field(None, description="Area of the page affected")
    auto_fixable: bool = False


class QualityCheckResponse(BaseModel):
    """Per-page quality check result."""

    score: float = Field(..., ge=0, le=100, description="Overall page quality score")
    steps: list[QualityStepResult] = Field(..., description="Result of each pipeline step")
    issues: list[QualityIssue] = Field(default_factory=list, description="All quality issues found")
    passed: bool = Field(..., description="True if the page passes all critical checks")


# ---------------------------------------------------------------------------
# Batch Generation
# ---------------------------------------------------------------------------


class BatchGenerateRequest(BaseModel):
    """Batch generate all coloring pages for a book."""

    descriptions: list[str] = Field(
        ...,
        min_length=1,
        description="Description for each page to generate",
    )
    variation_mode: VariationMode = Field(
        VariationMode.DIVERSE,
        description="How to prevent similar compositions across pages",
    )
    run_auto_qa: bool = Field(True, description="Auto-run quality pipeline on each generated page")
    cost_estimate_only: bool = Field(False, description="If true, return cost estimate without generating")


class PageBatchStatus(BaseModel):
    """Status of a single page within a batch job."""

    page_number: int
    description: str
    status: str = Field(..., description="'pending', 'generating', 'cleaning', 'completed', 'failed'")
    quality_score: float | None = Field(None, ge=0, le=100)
    error: str | None = None


class BatchStatusResponse(BaseModel):
    """Current status of a batch generation job."""

    job_id: UUID
    status: str = Field(
        ..., description="Overall status: 'pending', 'processing', 'completed', 'paused', 'cancelled', 'failed'"
    )
    progress: float = Field(0, ge=0, le=100, description="Completion percentage")
    total_pages: int = Field(..., ge=0)
    completed_pages: int = Field(0, ge=0)
    per_page_status: list[PageBatchStatus] = Field(default_factory=list)
    estimated_cost_cents: int | None = None
    spent_cents: int | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Series Planning
# ---------------------------------------------------------------------------


class PlanSeriesRequest(BaseModel):
    """Plan a multi-volume coloring book series."""

    series_name: str = Field(..., min_length=1, max_length=300, description="Series name")
    total_volumes: int = Field(..., ge=2, le=50, description="Number of volumes planned")
    themes: list[str] = Field(..., min_length=1, description="Theme for each volume")
    pages_per_volume: int = Field(30, ge=20, le=60, description="Pages per volume")
    branding_locked: bool = Field(True, description="Lock branding across volumes (title font, position, spine)")


class VolumePlan(BaseModel):
    """Plan for a single volume in the series."""

    volume_number: int
    theme: str
    pages: int
    status: str = Field("planned", description="'planned', 'in-progress', 'completed'")
    book_id: UUID | None = Field(None, description="Book ID once created")


class SeriesPlanResponse(BaseModel):
    """Full series plan with all volumes."""

    series_id: UUID
    series_name: str
    total_volumes: int
    volumes: list[VolumePlan] = Field(default_factory=list)
    branding_locked: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Quality Dashboard (Book-Level)
# ---------------------------------------------------------------------------


class ComplexityBucket(BaseModel):
    """A bucket in the complexity histogram."""

    range_label: str = Field(..., description="e.g. '0-20 (Very Simple)'")
    count: int = Field(..., ge=0, description="Number of pages in this bucket")


class PrintQualitySummary(BaseModel):
    """Aggregated print quality metrics across all pages."""

    line_quality_avg: float = Field(..., ge=0, le=100)
    closed_shapes_avg: float = Field(..., ge=0, le=100)
    stroke_uniformity_avg: float = Field(..., ge=0, le=100)
    ink_density_avg: float = Field(..., ge=0, le=100)
    small_areas_flagged: int = Field(0, ge=0, description="Pages with areas too small to color")


class QualityDashboardResponse(BaseModel):
    """Book-level quality dashboard data."""

    overall_score: float = Field(..., ge=0, le=100, description="Aggregated quality score")
    total_pages: int = Field(..., ge=0)
    pages_passed: int = Field(..., ge=0)
    pages_with_issues: int = Field(..., ge=0)
    complexity_histogram: list[ComplexityBucket] = Field(
        default_factory=list, description="Distribution of page complexity"
    )
    theme_cohesion: float = Field(..., ge=0, le=100, description="How well pages feel like a cohesive set")
    print_quality_summary: PrintQualitySummary
    duplicate_pages_detected: int = Field(0, ge=0, description="Number of visually duplicate pages detected")


# ---------------------------------------------------------------------------
# Export & Preflight
# ---------------------------------------------------------------------------


class ExportRequest(BaseModel):
    """Export a coloring book."""

    format: ColoringExportFormat = Field(..., description="Export format")
    dpi: int = Field(300, ge=72, le=600, description="Output resolution")
    include_bleed: bool = Field(True, description="Include bleed area")
    include_blank_backs: bool = Field(True, description="Include blank back pages for single-sided print")
    include_bonus_pages: bool = Field(True, description="Include title, belongs-to, and other bonus pages")


class PreflightCheck(BaseModel):
    """A single preflight check result."""

    check_name: str
    passed: bool
    severity: str = Field(..., description="'info', 'warning', or 'error'")
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class PreflightRequest(BaseModel):
    """Run full preflight on a coloring book."""

    book_id: UUID


class PreflightReport(BaseModel):
    """Full preflight report for a coloring book."""

    checks: list[PreflightCheck] = Field(..., description="Individual check results")
    passed: bool = Field(..., description="True if all critical checks passed")
    issues: list[str] = Field(default_factory=list)
    total_checks: int = Field(..., ge=0)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
