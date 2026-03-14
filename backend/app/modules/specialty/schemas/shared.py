"""Pydantic v2 schemas for Specialty Books shared / cross-cutting systems."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BookType(str, Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


class Distributor(str, Enum):
    KDP = "kdp"
    INGRAM_SPARK = "ingram-spark"
    BARNES_NOBLE = "barnes-noble"


class AccessibleVariantType(str, Enum):
    DYSLEXIA_FRIENDLY = "dyslexia-friendly"
    LARGE_PRINT = "large-print"
    HIGH_CONTRAST = "high-contrast"


class BackMatterType(str, Enum):
    ALSO_IN_SERIES = "also-in-series"
    ABOUT_SERIES = "about-series"
    EMAIL_CTA = "email-cta"
    REVIEW_REQUEST = "review-request"
    ABOUT_AUTHOR = "about-author"


class BatchJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SpamRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ColorProfile(str, Enum):
    SRGB = "sRGB"
    ADOBE_RGB = "adobe-rgb"
    CMYK = "cmyk"


# ---------------------------------------------------------------------------
# KDP Metadata Advisor
# ---------------------------------------------------------------------------


class MetadataAdvisorRequest(BaseModel):
    """Request AI-recommended categories, keywords, and subtitle suggestions."""

    book_type: BookType = Field(..., description="Type of specialty book")
    title: str = Field(..., min_length=1, max_length=300, description="Book title")
    subtitle: str | None = Field(None, max_length=300, description="Current subtitle, if any")
    description: str | None = Field(None, max_length=4000, description="Book description or summary")
    themes: list[str] = Field(default_factory=list, description="Themes or topics in the book")
    audience: str | None = Field(None, max_length=100, description="Target audience description")


class CategorySuggestion(BaseModel):
    """A suggested BISAC / KDP category."""

    category_path: str = Field(..., description="Full category path, e.g. 'Children's Books > Ages 3-5'")
    relevance_score: float = Field(..., ge=0, le=1, description="How relevant this category is")
    rationale: str = Field(..., description="Why this category was suggested")


class MetadataAdvisorResponse(BaseModel):
    """AI-recommended metadata for KDP listing optimization."""

    categories: list[CategorySuggestion] = Field(
        ..., description="Recommended BISAC/KDP categories ranked by relevance"
    )
    keywords: list[str] = Field(
        ..., max_length=7, description="Up to 7 KDP backend keywords"
    )
    subtitle_suggestions: list[str] = Field(
        default_factory=list, description="AI-generated subtitle alternatives"
    )
    compliance_notes: list[str] = Field(
        default_factory=list, description="Any KDP compliance warnings"
    )


# ---------------------------------------------------------------------------
# Asset Provenance & Rights Ledger
# ---------------------------------------------------------------------------


class ProvenanceResponse(BaseModel):
    """Provenance record for a generated asset."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_type: BookType
    book_id: UUID
    page_id: UUID | None = None
    asset_type: str = Field(..., description="e.g. 'illustration', 'line-art', 'puzzle-grid'")
    model: str = Field(..., description="AI model used for generation")
    prompt_text: str | None = None
    prompt_hash: str | None = Field(None, description="SHA-256 hash of the prompt")
    seed: int | None = None
    settings: dict[str, Any] = Field(default_factory=dict, description="Generation settings")
    generation_date: datetime
    status: str = Field(..., description="e.g. 'active', 'superseded'")
    created_at: datetime
    updated_at: datetime


class ProvenanceExportResponse(BaseModel):
    """Exportable compliance report for all assets in a book."""

    book_type: BookType
    book_id: UUID
    total_assets: int = Field(..., ge=0)
    assets: list[ProvenanceResponse] = Field(default_factory=list)
    font_licenses: list[dict[str, Any]] = Field(
        default_factory=list, description="Font license details for all fonts used"
    )
    export_url: str | None = Field(None, description="URL to download the full report PDF")
    generated_at: datetime


# ---------------------------------------------------------------------------
# Originality Fingerprinting & Spam Detection
# ---------------------------------------------------------------------------


class FingerprintRequest(BaseModel):
    """Generate an originality fingerprint for a book."""

    book_type: BookType
    book_id: UUID


class FingerprintResponse(BaseModel):
    """Originality fingerprint result."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_type: BookType
    book_id: UUID
    content_type: str = Field(..., description="e.g. 'image', 'grid', 'text'")
    phash: str | None = Field(None, description="Perceptual hash for images")
    data_hash: str | None = Field(None, description="Structural hash for grids/puzzles")
    ngram_fingerprint: str | None = Field(None, description="N-gram fingerprint for text")
    jaccard_vector: dict[str, Any] | None = Field(
        None, description="Jaccard similarity vector for word lists"
    )
    created_at: datetime


class CompareRequest(BaseModel):
    """Compare two books for similarity."""

    book_a_type: BookType
    book_a_id: UUID
    book_b_type: BookType
    book_b_id: UUID


class SimilarityDetail(BaseModel):
    """Detail of similarity between two items."""

    dimension: str = Field(..., description="e.g. 'visual', 'text', 'structure'")
    score: float = Field(..., ge=0, le=1, description="Similarity score (1.0 = identical)")
    details: str = Field(..., description="Human-readable explanation")


class CompareResponse(BaseModel):
    """Similarity comparison result between two books."""

    overall_similarity: float = Field(..., ge=0, le=1, description="Overall similarity score")
    dimension_scores: list[SimilarityDetail] = Field(default_factory=list)
    is_duplicate_risk: bool = Field(..., description="True if similarity exceeds safe threshold")
    recommendation: str = Field(..., description="Suggested action")


class SpamCheckRequest(BaseModel):
    """Run KDP spam risk analysis on a book."""

    book_type: BookType
    book_id: UUID


class SpamCheckResponse(BaseModel):
    """KDP spam risk analysis result."""

    risk_level: SpamRiskLevel
    overall_score: float = Field(..., ge=0, le=100, description="Spam risk score (0=safe, 100=high risk)")
    interior_originality_score: float = Field(..., ge=0, le=100)
    metadata_quality_score: float = Field(..., ge=0, le=100)
    content_substance_score: float = Field(..., ge=0, le=100)
    minor_edit_detection: bool = Field(
        ..., description="True if book appears to be a minor edit of another"
    )
    issues: list[str] = Field(default_factory=list, description="Specific spam risk issues found")
    recommendations: list[str] = Field(
        default_factory=list, description="Steps to reduce spam risk"
    )


# ---------------------------------------------------------------------------
# Print Cost & Pricing Engine
# ---------------------------------------------------------------------------


class PricingCalculateRequest(BaseModel):
    """Calculate print cost and pricing scenarios."""

    book_type: BookType
    page_count: int = Field(..., ge=1, description="Total interior page count")
    trim_size: str = Field(..., description="e.g. '8.5x11', '6x9'")
    interior_type: str = Field(
        "bw", description="'bw' (black & white) or 'color' (premium color)"
    )
    ink_coverage_percent: float | None = Field(
        None, ge=0, le=100, description="Average ink coverage per page"
    )
    target_price: float | None = Field(None, ge=0, description="Desired list price in USD")
    distributor: Distributor = Distributor.KDP


class PricingScenario(BaseModel):
    """A pricing scenario with calculated margins."""

    list_price: float = Field(..., ge=0, description="List price in USD")
    print_cost: float = Field(..., ge=0, description="Printing cost in USD")
    royalty_rate: float = Field(..., ge=0, le=1, description="Royalty percentage")
    royalty_amount: float = Field(..., description="Royalty per sale in USD")
    margin_percent: float = Field(..., description="Profit margin percentage")


class MarginAnalysis(BaseModel):
    """Detailed margin analysis."""

    break_even_price: float = Field(..., ge=0, description="Minimum price to break even")
    recommended_price: float = Field(..., ge=0, description="Suggested optimal price")
    category_avg_price: float | None = Field(None, ge=0, description="Average price in category")
    margin_at_target: float | None = Field(None, description="Margin at target price, if provided")


class PricingCalculateResponse(BaseModel):
    """Print cost calculation with pricing scenarios."""

    cost: float = Field(..., ge=0, description="Base print cost in USD")
    scenarios: list[PricingScenario] = Field(
        ..., description="Multiple pricing scenarios from aggressive to premium"
    )
    margin_analysis: MarginAnalysis
    distributor: Distributor
    warnings: list[str] = Field(
        default_factory=list, description="Cost or pricing warnings"
    )


# ---------------------------------------------------------------------------
# Ink Coverage & CMYK / Soft-Proof
# ---------------------------------------------------------------------------


class InkCoverageRequest(BaseModel):
    """Analyze ink coverage for pages."""

    book_type: BookType
    book_id: UUID
    page_ids: list[UUID] | None = Field(
        None, description="Specific pages to analyze; None = all pages"
    )


class PageInkCoverage(BaseModel):
    """Ink coverage data for a single page."""

    page_id: UUID
    page_number: int
    coverage_percent: float = Field(..., ge=0, le=100)
    is_within_limit: bool = Field(..., description="True if coverage is acceptable for print")
    details: dict[str, float] = Field(
        default_factory=dict,
        description="Per-channel coverage (C, M, Y, K) for color interiors",
    )


class InkCoverageResponse(BaseModel):
    """Ink coverage analysis result."""

    book_id: UUID
    average_coverage: float = Field(..., ge=0, le=100)
    max_coverage: float = Field(..., ge=0, le=100)
    pages: list[PageInkCoverage] = Field(default_factory=list)
    estimated_cost_impact: float | None = Field(
        None, description="Additional cost from high ink coverage"
    )


class SoftProofRequest(BaseModel):
    """Request CMYK soft-proof simulation for a page."""

    book_type: BookType
    book_id: UUID
    page_id: UUID
    color_profile: ColorProfile = ColorProfile.CMYK


class GamutWarning(BaseModel):
    """An out-of-gamut color warning."""

    region: str = Field(..., description="Area of the page with the issue")
    original_color: str = Field(..., description="Original RGB hex color")
    cmyk_equivalent: str = Field(..., description="Closest CMYK representation")
    delta_e: float = Field(..., ge=0, description="Color difference (Delta E)")


class SoftProofResponse(BaseModel):
    """CMYK soft-proof simulation result."""

    page_id: UUID
    proof_image_url: str = Field(..., description="URL of the CMYK soft-proof image")
    side_by_side_url: str | None = Field(
        None, description="URL of RGB vs CMYK comparison image"
    )
    gamut_warnings: list[GamutWarning] = Field(default_factory=list)
    shadow_crush_detected: bool = Field(
        ..., description="True if dark areas may lose detail in print"
    )
    ink_density_ok: bool = Field(
        ..., description="True if total ink density is within safe limits"
    )


class ColorAutoAdjustRequest(BaseModel):
    """Auto-fix gamut, ink density, and shadow issues."""

    book_type: BookType
    book_id: UUID
    page_id: UUID
    fix_gamut: bool = Field(True, description="Fix out-of-gamut colors")
    fix_shadows: bool = Field(True, description="Fix shadow crush issues")
    fix_ink_density: bool = Field(True, description="Fix excessive ink density")


class ColorAutoAdjustResponse(BaseModel):
    """Result of automatic color adjustments."""

    page_id: UUID
    adjusted_image_url: str = Field(..., description="URL of the adjusted image")
    changes_made: list[str] = Field(
        default_factory=list, description="List of adjustments applied"
    )
    before_after_url: str | None = Field(
        None, description="Side-by-side comparison URL"
    )


# ---------------------------------------------------------------------------
# Batch Factory
# ---------------------------------------------------------------------------


class BatchCreateRequest(BaseModel):
    """Create a batch generation job."""

    book_type: BookType
    batch_config: dict[str, Any] = Field(
        ..., description="Configuration for the batch job (volumes, themes, etc.)"
    )
    budget_limit_cents: int | None = Field(
        None, ge=0, description="Maximum spend in cents; None = unlimited"
    )
    volumes_total: int = Field(..., ge=1, le=100, description="Number of volumes to generate")


class BatchCreateResponse(BaseModel):
    """Response after creating a batch job."""

    job_id: UUID
    status: BatchJobStatus
    volumes_total: int
    estimated_cost_cents: int | None = None
    created_at: datetime


class BatchStatusResponse(BaseModel):
    """Current status of a batch job."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    status: BatchJobStatus
    volumes_total: int
    volumes_completed: int = Field(0, ge=0)
    pages_total: int = Field(0, ge=0)
    pages_completed: int = Field(0, ge=0)
    spent_cents: int = Field(0, ge=0)
    budget_limit_cents: int | None = None
    errors: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Series & Branding
# ---------------------------------------------------------------------------


class SeriesCreate(BaseModel):
    """Create a new book series."""

    name: str = Field(..., min_length=1, max_length=300, description="Series name")
    book_type: BookType
    naming_format: str | None = Field(
        None,
        max_length=200,
        description="Volume naming template, e.g. '{series} - Volume {n}'",
    )
    branding_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Branding rules: title font/position, spine layout, volume badge, etc.",
    )
    branding_locked: bool = Field(
        False, description="Lock branding so volumes cannot deviate"
    )


class SeriesResponse(BaseModel):
    """Series details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    book_type: BookType
    naming_format: str | None = None
    branding_config: dict[str, Any] = Field(default_factory=dict)
    branding_locked: bool
    volume_count: int = Field(0, ge=0)
    created_at: datetime
    updated_at: datetime


class CoherenceIssue(BaseModel):
    """A single coherence issue in a series."""

    volume_id: UUID
    issue_type: str = Field(..., description="e.g. 'title-font', 'spine-layout', 'theme-drift'")
    severity: str = Field(..., description="'warning' or 'error'")
    description: str
    auto_fixable: bool = False


class CoherenceCheckResponse(BaseModel):
    """Series consistency / coherence check result."""

    series_id: UUID
    overall_coherent: bool
    issues: list[CoherenceIssue] = Field(default_factory=list)
    theme_cohesion_score: float = Field(..., ge=0, le=100)
    auto_fixable_count: int = Field(0, ge=0)


# ---------------------------------------------------------------------------
# Back Matter CTA & QR Code
# ---------------------------------------------------------------------------


class BackMatterRequest(BaseModel):
    """Generate back matter pages for a book."""

    book_type: BookType
    book_id: UUID
    template_type: BackMatterType
    content: str | None = Field(None, max_length=4000, description="Custom content text")
    cta_url: str | None = Field(None, description="URL for call-to-action link")
    include_qr_code: bool = Field(False, description="Generate a QR code for the CTA URL")


class BackMatterResponse(BaseModel):
    """Generated back matter page."""

    template_type: BackMatterType
    content: str = Field(..., description="Rendered back matter content")
    page_image_url: str | None = Field(None, description="URL of the rendered page image")
    qr_code_url: str | None = Field(None, description="URL of the generated QR code image")


class QRCodeRequest(BaseModel):
    """Generate a QR code image."""

    url: str = Field(..., description="URL to encode in the QR code")
    size_px: int = Field(300, ge=100, le=1000, description="QR code image size in pixels")
    foreground_color: str = Field("#000000", description="QR code foreground hex color")
    background_color: str = Field("#FFFFFF", description="QR code background hex color")


class QRCodeResponse(BaseModel):
    """Generated QR code."""

    qr_code_url: str = Field(..., description="URL of the generated QR code image")
    url_encoded: str = Field(..., description="The URL encoded in the QR code")


# ---------------------------------------------------------------------------
# Accessible Variants
# ---------------------------------------------------------------------------


class AccessibleVariantRequest(BaseModel):
    """Create an accessible edition of a book."""

    book_type: BookType
    book_id: UUID
    variant_type: AccessibleVariantType
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Variant-specific settings (e.g. scale for large print, font for dyslexia)",
    )


class AccessibleVariantResponse(BaseModel):
    """Created accessible variant."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_book_type: BookType
    source_book_id: UUID
    variant_type: AccessibleVariantType
    variant_book_id: UUID = Field(..., description="ID of the newly created variant book")
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# ---------------------------------------------------------------------------
# Template Marketplace
# ---------------------------------------------------------------------------


class TemplateResponse(BaseModel):
    """A template or pack available in the marketplace."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    book_type: BookType
    description: str
    thumbnail_url: str | None = None
    template_type: str = Field(..., description="e.g. 'page-layout', 'theme-pack', 'style-pack'")
    settings: dict[str, Any] = Field(
        default_factory=dict, description="Pre-filled wizard settings"
    )
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
