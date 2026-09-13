"""Pydantic schemas for KDP validation requests and responses."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(str, Enum):
    PRINT = "print"
    EBOOK = "ebook"
    COVER = "cover"
    COMPLIANCE = "compliance"
    FULL = "full"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNINGS = "warnings"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class ValidationIssue(BaseModel):
    """A single validation finding."""

    severity: Severity
    rule: str
    message: str
    location: str | None = None
    details: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Print validation
# ---------------------------------------------------------------------------


class PrintValidationRequest(BaseModel):
    """Request body for print file validation."""

    trim_size: str = Field(..., description="Trim size key, e.g. '6x9'")
    page_count: int = Field(..., ge=1, description="Total page count (must be even)")
    paper_type: str = Field(default="white", description="'white' or 'cream'")
    has_bleed: bool = Field(default=False, description="Whether interior uses full bleed")
    inside_margin: float = Field(..., ge=0, description="Inside (gutter) margin in inches")
    outside_margin: float = Field(..., ge=0, description="Outside margin in inches")
    top_margin: float = Field(..., ge=0, description="Top margin in inches")
    bottom_margin: float = Field(..., ge=0, description="Bottom margin in inches")
    image_dpi: int | None = Field(default=None, ge=1, description="Lowest image DPI found")
    fonts_embedded: bool = Field(default=True, description="Whether all fonts are embedded")
    color_space: str | None = Field(default=None, description="Detected color space, e.g. 'RGB'")


# ---------------------------------------------------------------------------
# Ebook validation
# ---------------------------------------------------------------------------


class EbookImageInfo(BaseModel):
    filename: str
    format: str
    size_bytes: int
    dpi: int | None = None


class EbookLinkInfo(BaseModel):
    href: str
    text: str | None = None
    is_internal: bool = True
    is_valid: bool = True


class EbookValidationRequest(BaseModel):
    """Request body for ebook validation."""

    has_ncx_toc: bool = Field(default=False, description="NCX table of contents present")
    has_html_toc: bool = Field(default=False, description="HTML TOC present")
    images: list[EbookImageInfo] = Field(default_factory=list)
    links: list[EbookLinkInfo] = Field(default_factory=list)
    has_javascript: bool = Field(default=False)
    has_external_resources: bool = Field(default=False)
    min_font_size_pt: float | None = Field(default=None, ge=0)
    file_size_bytes: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Cover validation
# ---------------------------------------------------------------------------


class CoverValidationRequest(BaseModel):
    """Request body for cover validation."""

    cover_type: str = Field(default="print", description="'print' or 'ebook'")
    width_inches: float = Field(..., gt=0)
    height_inches: float = Field(..., gt=0)
    dpi: int = Field(..., ge=1)
    file_format: str = Field(..., description="Image format, e.g. 'TIFF', 'PNG', 'JPEG'")
    color_space: str | None = Field(default=None, description="e.g. 'CMYK', 'RGB'")
    trim_size: str | None = Field(default=None, description="Trim size key for dimension check")
    page_count: int | None = Field(default=None, ge=1)
    paper_type: str = Field(default="white")
    has_text_in_bleed: bool = Field(default=False, description="Whether text exists in bleed area")


# ---------------------------------------------------------------------------
# Compliance scan
# ---------------------------------------------------------------------------


class ComplianceScanRequest(BaseModel):
    """Request body for compliance scanning."""

    title: str = Field(default="")
    subtitle: str = Field(default="")
    description: str = Field(default="")
    keywords: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    content_sample: str = Field(default="", description="Sample of book content for policy check")


# ---------------------------------------------------------------------------
# Full validation
# ---------------------------------------------------------------------------


class FullValidationRequest(BaseModel):
    """Combined request for full pre-flight validation."""

    print_validation: PrintValidationRequest | None = None
    ebook_validation: EbookValidationRequest | None = None
    cover_validation: CoverValidationRequest | None = None
    compliance_scan: ComplianceScanRequest | None = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ValidationResult(BaseModel):
    """Result of a single validation type."""

    validation_type: ValidationType
    status: ValidationStatus
    issues: list[ValidationIssue] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)


class FullValidationResponse(BaseModel):
    """Aggregated response for full pre-flight validation."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    overall_status: ValidationStatus
    results: list[ValidationResult] = Field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationResultResponse(BaseModel):
    """Response when retrieving stored validation results."""

    id: uuid.UUID
    overall_status: ValidationStatus
    results: list[ValidationResult]
    total_errors: int
    total_warnings: int
    created_at: datetime
