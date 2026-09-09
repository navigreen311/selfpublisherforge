"""Multi-Distributor Preflight & Export.

Runs distributor-specific validation checks and produces compliant
export files for KDP, IngramSpark, and B&N Press.

Blueprint refs: 12.5
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.enums import PreflightStatus
from app.modules.specialty.models.shared import DistributorPreflight

# ---------------------------------------------------------------------------
# Distributor specifications
# ---------------------------------------------------------------------------

DISTRIBUTORS: dict[str, dict[str, Any]] = {
    "kdp": {
        "name": "Amazon KDP",
        "formats": ["PDF"],
        "max_file_size_mb": 650,
        "cover_specs": {
            "format": "PDF",
            "min_dpi": 300,
            "color_space": "RGB_or_CMYK",
            "bleed": 0.125,  # inches
        },
        "interior_specs": {
            "min_dpi": 300,
            "color_spaces": ["RGB", "CMYK"],
            "min_pages": 24,
            "max_pages": 828,
            "bleed": 0.125,
        },
        "page_count_limits": {
            "color": {"min": 24, "max": 550},
            "bw": {"min": 24, "max": 828},
        },
        "trim_sizes": [
            "5x8",
            "5.25x8",
            "5.5x8.5",
            "6x9",
            "6.14x9.21",
            "6.69x9.61",
            "7x10",
            "7.44x9.69",
            "7.5x9.25",
            "8x10",
            "8.25x6",
            "8.25x8.25",
            "8.5x8.5",
            "8.5x11",
        ],
    },
    "ingram_spark": {
        "name": "IngramSpark",
        "formats": ["PDF/X-1a"],
        "max_file_size_mb": 2048,
        "cover_specs": {
            "format": "PDF/X-1a",
            "min_dpi": 300,
            "color_space": "CMYK",
            "bleed": 0.125,
            "icc_profile": "GRACoL2006_Coated1v2",
        },
        "interior_specs": {
            "min_dpi": 300,
            "color_spaces": ["CMYK"],
            "pdf_standard": "PDF/X-1a",
            "icc_profile_required": True,
            "bleed": 0.125,
        },
        "page_count_limits": {
            "color": {"min": 24, "max": 800},
            "bw": {"min": 24, "max": 1200},
        },
        "trim_sizes": [
            "5x8",
            "5.25x8",
            "5.5x8.5",
            "6x9",
            "6.14x9.21",
            "7x10",
            "7.5x9.25",
            "8x10",
            "8.5x11",
        ],
    },
    "bn_press": {
        "name": "Barnes & Noble Press",
        "formats": ["EPUB", "PDF"],
        "max_file_size_mb": 650,
        "cover_specs": {
            "format": "JPEG_or_PNG",
            "min_dpi": 300,
            "min_width": 1400,
            "min_height": 1400,
            "color_space": "RGB",
        },
        "interior_specs": {
            "print_format": "PDF",
            "ebook_format": "EPUB",
            "epub_version": "3.0",
            "min_dpi": 300,
            "color_spaces": ["RGB", "CMYK"],
        },
        "page_count_limits": {
            "color": {"min": 24, "max": 400},
            "bw": {"min": 24, "max": 750},
        },
        "trim_sizes": [
            "5x8",
            "5.5x8.5",
            "6x9",
            "8x10",
            "8.5x11",
        ],
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PreflightCheck:
    """A single check within a preflight run."""

    name: str
    passed: bool
    message: str
    severity: str = "error"  # error | warning | info


@dataclass
class PreflightResult:
    """Aggregate result of a distributor preflight."""

    status: str  # passed | failed | warnings
    distributor: str
    checks: list[PreflightCheck]
    issues: list[PreflightCheck]


@dataclass
class ExportResult:
    """Result of a distributor-specific export."""

    distributor: str
    format: str
    file_url: str | None
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------


def _run_kdp_checks(book_data: dict[str, Any]) -> list[PreflightCheck]:
    """KDP-specific validation: page count limits, file size, cover dimensions."""
    checks: list[PreflightCheck] = []
    spec = DISTRIBUTORS["kdp"]

    # Page count check
    page_count = book_data.get("page_count", 0)
    interior_type = book_data.get("interior_type", "bw")
    limits = spec["page_count_limits"].get(interior_type, spec["page_count_limits"]["bw"])

    if page_count < limits["min"]:
        checks.append(
            PreflightCheck(
                name="kdp_page_count_min",
                passed=False,
                message=f"KDP requires at least {limits['min']} pages for {interior_type} interiors. Book has {page_count}.",
            )
        )
    elif page_count > limits["max"]:
        checks.append(
            PreflightCheck(
                name="kdp_page_count_max",
                passed=False,
                message=f"KDP allows at most {limits['max']} pages for {interior_type} interiors. Book has {page_count}.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="kdp_page_count",
                passed=True,
                message=f"Page count {page_count} is within KDP limits for {interior_type} interiors.",
            )
        )

    # File size check
    file_size_mb = book_data.get("file_size_mb", 0)
    if file_size_mb > spec["max_file_size_mb"]:
        checks.append(
            PreflightCheck(
                name="kdp_file_size",
                passed=False,
                message=f"File size {file_size_mb}MB exceeds KDP limit of {spec['max_file_size_mb']}MB.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="kdp_file_size",
                passed=True,
                message=f"File size {file_size_mb}MB is within KDP limits.",
            )
        )

    # Cover dimensions / DPI check
    cover_dpi = book_data.get("cover_dpi", 300)
    if cover_dpi < spec["cover_specs"]["min_dpi"]:
        checks.append(
            PreflightCheck(
                name="kdp_cover_dpi",
                passed=False,
                message=f"Cover DPI ({cover_dpi}) is below KDP minimum of {spec['cover_specs']['min_dpi']}.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="kdp_cover_dpi",
                passed=True,
                message=f"Cover DPI ({cover_dpi}) meets KDP requirements.",
            )
        )

    # Trim size check
    trim_size = book_data.get("trim_size", "")
    if trim_size and trim_size not in spec["trim_sizes"]:
        checks.append(
            PreflightCheck(
                name="kdp_trim_size",
                passed=False,
                message=f"Trim size '{trim_size}' is not available on KDP.",
            )
        )
    elif trim_size:
        checks.append(
            PreflightCheck(
                name="kdp_trim_size",
                passed=True,
                message=f"Trim size '{trim_size}' is supported on KDP.",
            )
        )

    return checks


def _run_ingram_checks(book_data: dict[str, Any]) -> list[PreflightCheck]:
    """IngramSpark-specific: PDF/X-1a requirement, ICC profiles, CMYK."""
    checks: list[PreflightCheck] = []
    spec = DISTRIBUTORS["ingram_spark"]

    # PDF standard check
    pdf_standard = book_data.get("pdf_standard", "")
    if pdf_standard != "PDF/X-1a":
        checks.append(
            PreflightCheck(
                name="ingram_pdf_standard",
                passed=False,
                message="IngramSpark requires PDF/X-1a format. Current format: " f"'{pdf_standard or 'standard PDF'}'.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="ingram_pdf_standard",
                passed=True,
                message="PDF is in PDF/X-1a format.",
            )
        )

    # ICC profile check
    has_icc = book_data.get("icc_profile_embedded", False)
    if not has_icc:
        checks.append(
            PreflightCheck(
                name="ingram_icc_profile",
                passed=False,
                message="IngramSpark requires embedded ICC color profiles. No ICC profile found.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="ingram_icc_profile",
                passed=True,
                message="ICC color profile is embedded.",
            )
        )

    # Color space must be CMYK
    color_space = book_data.get("color_space", "RGB")
    if color_space != "CMYK":
        checks.append(
            PreflightCheck(
                name="ingram_color_space",
                passed=False,
                message=f"IngramSpark requires CMYK color space. Current: {color_space}.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="ingram_color_space",
                passed=True,
                message="Color space is CMYK.",
            )
        )

    # Page count
    page_count = book_data.get("page_count", 0)
    interior_type = book_data.get("interior_type", "bw")
    limits = spec["page_count_limits"].get(interior_type, spec["page_count_limits"]["bw"])
    if page_count < limits["min"] or page_count > limits["max"]:
        checks.append(
            PreflightCheck(
                name="ingram_page_count",
                passed=False,
                message=f"Page count {page_count} is outside IngramSpark limits ({limits['min']}-{limits['max']}).",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="ingram_page_count",
                passed=True,
                message=f"Page count {page_count} is within IngramSpark limits.",
            )
        )

    return checks


def _run_bn_checks(book_data: dict[str, Any]) -> list[PreflightCheck]:
    """B&N Press-specific: EPUB specs, cover requirements."""
    checks: list[PreflightCheck] = []
    spec = DISTRIBUTORS["bn_press"]

    # Cover image dimensions
    cover_width = book_data.get("cover_width_px", 0)
    cover_height = book_data.get("cover_height_px", 0)
    min_w = spec["cover_specs"]["min_width"]
    min_h = spec["cover_specs"]["min_height"]
    if cover_width < min_w or cover_height < min_h:
        checks.append(
            PreflightCheck(
                name="bn_cover_dimensions",
                passed=False,
                message=f"B&N Press requires cover image at least {min_w}x{min_h}px. "
                f"Current: {cover_width}x{cover_height}px.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="bn_cover_dimensions",
                passed=True,
                message=f"Cover dimensions ({cover_width}x{cover_height}px) meet B&N requirements.",
            )
        )

    # EPUB version (for ebook)
    epub_version = book_data.get("epub_version", "")
    if epub_version and epub_version != spec["interior_specs"]["epub_version"]:
        checks.append(
            PreflightCheck(
                name="bn_epub_version",
                passed=False,
                message=f"B&N Press requires EPUB {spec['interior_specs']['epub_version']}. "
                f"Current: EPUB {epub_version}.",
            )
        )
    elif epub_version:
        checks.append(
            PreflightCheck(
                name="bn_epub_version",
                passed=True,
                message=f"EPUB version {epub_version} is supported.",
            )
        )

    # Page count
    page_count = book_data.get("page_count", 0)
    interior_type = book_data.get("interior_type", "bw")
    limits = spec["page_count_limits"].get(interior_type, spec["page_count_limits"]["bw"])
    if page_count < limits["min"] or page_count > limits["max"]:
        checks.append(
            PreflightCheck(
                name="bn_page_count",
                passed=False,
                message=f"Page count {page_count} is outside B&N Press limits ({limits['min']}-{limits['max']}).",
            )
        )
    elif page_count > 0:
        checks.append(
            PreflightCheck(
                name="bn_page_count",
                passed=True,
                message=f"Page count {page_count} is within B&N Press limits.",
            )
        )

    return checks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_distributor_preflight(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    distributor: str,
    book_data: dict[str, Any] | None = None,
) -> PreflightResult:
    """Run distributor-specific preflight checks and persist results.

    Parameters
    ----------
    db:
        Async database session.
    book_type:
        One of ``childrens``, ``coloring``, ``puzzle``.
    book_id:
        The book to validate.
    distributor:
        Target distributor key (``kdp``, ``ingram_spark``, ``bn_press``).
    book_data:
        Optional dict with book metadata for checks (page_count,
        file_size_mb, cover_dpi, trim_size, etc.).  In production this
        would be fetched from the database.
    """
    if distributor not in DISTRIBUTORS:
        raise ValueError(f"Unknown distributor: {distributor}. Valid: {list(DISTRIBUTORS.keys())}")

    data = book_data or {}

    # Run distributor-specific checks.
    if distributor == "kdp":
        checks = _run_kdp_checks(data)
    elif distributor == "ingram_spark":
        checks = _run_ingram_checks(data)
    elif distributor == "bn_press":
        checks = _run_bn_checks(data)
    else:
        checks = []

    issues = [c for c in checks if not c.passed]
    status = "passed" if not issues else "failed"

    # Check for warnings-only (all issues are severity=warning).
    if issues and all(i.severity == "warning" for i in issues):
        status = "warnings"

    # Persist preflight result.
    row = DistributorPreflight(
        book_type=book_type,
        book_id=book_id,
        distributor=distributor,
        status=PreflightStatus(status) if status in ("passed", "failed") else PreflightStatus.warnings,
        checks={
            "results": [
                {"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity} for c in checks
            ]
        },
        issues={"items": [{"name": i.name, "message": i.message, "severity": i.severity} for i in issues]},
    )
    db.add(row)
    await db.flush()

    return PreflightResult(
        status=status,
        distributor=distributor,
        checks=checks,
        issues=issues,
    )


def export_for_distributor(
    book_data: dict[str, Any],
    distributor: str,
) -> ExportResult:
    """Prepare a book export formatted for a specific distributor.

    In production this would invoke the PDF generation pipeline with
    distributor-specific settings (e.g. PDF/X-1a for IngramSpark,
    CMYK conversion, ICC profile embedding).

    Currently returns a metadata structure describing what would be
    produced.
    """
    if distributor not in DISTRIBUTORS:
        raise ValueError(f"Unknown distributor: {distributor}")

    spec = DISTRIBUTORS[distributor]

    # Determine output format.
    output_format = spec["formats"][0]

    metadata: dict[str, Any] = {
        "distributor": distributor,
        "distributor_name": spec["name"],
        "output_format": output_format,
        "color_space": spec.get("interior_specs", {}).get("color_spaces", ["RGB"])[0],
        "bleed": spec.get("interior_specs", {}).get("bleed", 0.125),
        "dpi": spec.get("interior_specs", {}).get("min_dpi", 300),
    }

    # IngramSpark-specific extras.
    if distributor == "ingram_spark":
        metadata["pdf_standard"] = "PDF/X-1a"
        metadata["icc_profile"] = spec["cover_specs"].get("icc_profile")

    return ExportResult(
        distributor=distributor,
        format=output_format,
        file_url=None,  # Would be populated after actual file generation.
        metadata=metadata,
    )
