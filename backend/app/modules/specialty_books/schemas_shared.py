"""Pydantic schemas shared across all specialty book types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BookType(str, Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


class AssetType(str, Enum):
    ILLUSTRATION = "illustration"
    LINE_ART = "line_art"
    PUZZLE_GRID = "puzzle_grid"
    COVER = "cover"
    BACK_MATTER = "back_matter"


class BatchJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DistributorTarget(str, Enum):
    KDP = "kdp"
    INGRAM_SPARK = "ingram_spark"
    BN_PRESS = "bn_press"


class VariantType(str, Enum):
    DYSLEXIA_FRIENDLY = "dyslexia_friendly"
    LARGE_PRINT = "large_print"
    HIGH_CONTRAST = "high_contrast"


class InteriorType(str, Enum):
    BLACK_WHITE = "black_white"
    STANDARD_COLOR = "standard_color"
    PREMIUM_COLOR = "premium_color"


class BackMatterType(str, Enum):
    ABOUT_AUTHOR = "about_author"
    ALSO_BY = "also_by"
    CTA_PAGE = "cta_page"
    COLORING_TEST = "coloring_test"
    BONUS_PUZZLE = "bonus_puzzle"


class TrimSize(str, Enum):
    SIZE_5X8 = "5x8"
    SIZE_5_5X8_5 = "5.5x8.5"
    SIZE_6X9 = "6x9"
    SIZE_7X10 = "7x10"
    SIZE_8X10 = "8x10"
    SIZE_8_5X8_5 = "8.5x8.5"
    SIZE_8_5X11 = "8.5x11"


class ProvenanceRecord(BaseModel):
    id: UUID
    org_id: UUID
    book_type: BookType
    book_id: UUID
    page_id: UUID | None = None
    asset_type: AssetType
    model: str
    prompt_text: str
    prompt_hash: str
    seed: int | None = None
    settings: dict[str, Any] | None = None
    generation_timestamp: datetime
    license_type: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProvenanceExportResponse(BaseModel):
    book_type: BookType
    book_id: UUID
    records: list[ProvenanceRecord]
    total: int
    exported_at: datetime


class MetadataAdvisorRequest(BaseModel):
    book_type: BookType
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    audience: str | None = Field(None, max_length=100)
    themes: list[str] | None = None


class MetadataAdvisorResponse(BaseModel):
    bisac_categories: list[str]
    keywords: list[str] = Field(default_factory=list)
    subtitle_suggestions: list[str] = Field(default_factory=list)
    age_range_suggestion: str | None = None
    series_name_suggestions: list[str] | None = None


class OriginalityFingerprintResponse(BaseModel):
    book_type: BookType
    book_id: UUID
    overall_score: float = Field(..., ge=0.0, le=100.0)
    component_scores: dict[str, float] = Field(default_factory=dict)
    fingerprint_hash: str
    generated_at: datetime


class OriginalityCompareResponse(BaseModel):
    book_a_id: UUID
    book_b_id: UUID
    similarity_score: float = Field(..., ge=0.0, le=100.0)
    matching_sections: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str


class SpamCheckResponse(BaseModel):
    book_type: BookType
    book_id: UUID
    risk_score: float = Field(..., ge=0.0, le=100.0)
    flags: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str
    safe_to_publish: bool


class PrintCostCalculateRequest(BaseModel):
    page_count: int = Field(..., ge=1, le=1000)
    interior_type: InteriorType
    trim_size: TrimSize
    marketplace: str = Field("us", max_length=10)
    target_list_price: float | None = Field(None, ge=0.99)


class PricingScenario(BaseModel):
    list_price: float
    printing_cost: float
    royalty_rate: float
    royalty_amount: float
    net_profit: float


class PrintCostResponse(BaseModel):
    printing_cost: float
    minimum_list_price: float
    scenarios: list[PricingScenario] = Field(default_factory=list)
    recommended_price: float | None = None
    interior_type: InteriorType
    page_count: int


class PageInkCoverage(BaseModel):
    page_number: int
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)
    exceeds_threshold: bool = False


class InkCoverageResponse(BaseModel):
    book_id: UUID
    average_coverage: float = Field(..., ge=0.0, le=100.0)
    max_coverage: float = Field(..., ge=0.0, le=100.0)
    per_page: list[PageInkCoverage] = Field(default_factory=list)
    threshold: float = 60.0
    pages_exceeding: int = 0


class SoftProofResponse(BaseModel):
    book_id: UUID
    page_number: int | None = None
    cmyk_preview_url: str
    out_of_gamut_warnings: list[dict[str, Any]] = Field(default_factory=list)
    auto_adjust_available: bool = False
    shadow_crush_detected: bool = False
    ink_density_ok: bool = True


class BatchJobCreate(BaseModel):
    book_type: BookType
    batch_config: dict[str, Any] = Field(...)
    budget_limit_cents: int | None = Field(None, ge=0)


class BatchJobResponse(BaseModel):
    id: UUID
    org_id: UUID
    book_type: BookType
    batch_config: dict[str, Any]
    budget_limit_cents: int | None = None
    spent_cents: int = 0
    status: BatchJobStatus
    volumes_total: int = 0
    volumes_completed: int = 0
    pages_total: int = 0
    pages_completed: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BatchJobStatusResponse(BaseModel):
    id: UUID
    status: BatchJobStatus
    progress: float = Field(0.0, ge=0.0, le=100.0)
    volumes_total: int = 0
    volumes_completed: int = 0
    pages_total: int = 0
    pages_completed: int = 0
    spent_cents: int = 0
    errors: list[str] = Field(default_factory=list)
    updated_at: datetime


class TemplateItem(BaseModel):
    id: UUID
    name: str
    book_type: BookType
    description: str | None = None
    thumbnail_url: str | None = None
    category: str | None = None
    is_premium: bool = False
    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    items: list[TemplateItem]
    total: int


class SeriesCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    book_type: BookType
    naming_format: str | None = Field(None, max_length=255)
    branding_config: dict[str, Any] | None = None
    branding_locked: bool = False


class SeriesResponse(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    book_type: BookType
    naming_format: str | None = None
    branding_config: dict[str, Any] | None = None
    branding_locked: bool = False
    volume_count: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CoherenceCheckResponse(BaseModel):
    series_id: UUID
    coherent: bool
    issues: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class BackMatterGenerateRequest(BaseModel):
    template_type: BackMatterType
    content: str | None = Field(None, max_length=5000)
    cta_url: str | None = Field(None, max_length=500)
    include_qr_code: bool = False


class BackMatterGenerateResponse(BaseModel):
    template_type: BackMatterType
    content: str
    preview_url: str | None = None
    qr_code_url: str | None = None


class QRCodeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    size_px: int = Field(300, ge=100, le=1000)
    error_correction: str = Field("M", pattern="^[LMQH]$")


class QRCodeResponse(BaseModel):
    qr_code_url: str
    url_encoded: str
    size_px: int


class AccessibleVariantRequest(BaseModel):
    variant_type: VariantType
    settings: dict[str, Any] | None = None


class AccessibleVariantResponse(BaseModel):
    id: UUID
    source_book_type: BookType
    source_book_id: UUID
    variant_type: VariantType
    variant_book_id: UUID
    settings: dict[str, Any] | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ISBNAssignRequest(BaseModel):
    book_type: BookType
    book_id: UUID
    publisher_name: str = Field(..., min_length=1, max_length=255)
    isbn: str | None = Field(None, pattern=r"^\d{13}$")


class ISBNAssignResponse(BaseModel):
    id: UUID
    isbn: str
    publisher_name: str
    assigned_to_book_type: BookType
    assigned_to_book_id: UUID
    barcode_url: str | None = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class BundleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    book_type: BookType
    volume_ids: list[UUID] = Field(..., min_length=1)
    series_id: UUID | None = None
    config: dict[str, Any] | None = None


class BundleResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    book_type: BookType
    volume_ids: list[UUID]
    series_id: UUID | None = None
    config: dict[str, Any] | None = None
    total_pages: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PreflightCheck(BaseModel):
    name: str
    passed: bool
    details: str | None = None
    severity: str = Field("info", pattern="^(info|warning|error)$")


class DistributorPreflightResponse(BaseModel):
    id: UUID
    book_type: BookType
    book_id: UUID
    distributor: DistributorTarget
    status: str
    checks: list[PreflightCheck] = Field(default_factory=list)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    exported_url: str | None = None
    all_passed: bool = False
    model_config = ConfigDict(from_attributes=True)
