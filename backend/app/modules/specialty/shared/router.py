"""FastAPI router for shared Specialty Books endpoints.

Cross-cutting services used by Children's, Coloring, and Puzzle book studios:
metadata advisor, provenance, originality fingerprinting, pricing, color
management, batch factory, templates, series, back matter, accessibility,
device preview, layout protection, and export utilities.

Blueprint refs: 6.1-6.5, 7.1-7.4, 8.1-8.2, 9.1-9.3, 10.1-10.3, 11.1-11.3,
12.1-12.6, 14.4
"""
from __future__ import annotations

import base64
import dataclasses
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.shared import (
    accessibility,
    back_matter,
    batch_factory,
    color_management,
    device_preview,
    fingerprinting,
    kindle_export,
    layout_protection,
    print_pricing,
    provenance,
    series_manager,
    spam_detector,
    template_marketplace,
)
from app.modules.specialty.shared import distributor as distributor_svc
from app.modules.specialty.shared import metadata_advisor as metadata_advisor_svc

router = APIRouter(prefix="/specialty", tags=["specialty"])


# ---------------------------------------------------------------------------
# KDP Category & Metadata Advisor (6.3)
# ---------------------------------------------------------------------------


@router.post(
    "/metadata-advisor",
    response_model=SuccessResponse[dict],
    summary="AI recommend BISAC categories, keywords, and subtitle optimizations",
)
async def metadata_advisor(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analyze book metadata and return AI-recommended BISAC categories,
    7 KDP keywords, subtitle optimization suggestions, and compliance checks.
    """
    title = payload.get("title", "")
    description = payload.get("description")
    book_type = payload.get("book_type", "childrens")
    audience = payload.get("audience")
    themes = payload.get("themes")
    subtitle = payload.get("subtitle")
    keywords = payload.get("keywords")

    categories_prompt = metadata_advisor_svc.recommend_categories(
        title=title,
        description=description,
        book_type=book_type,
        audience=audience,
    )
    keywords_prompt = metadata_advisor_svc.generate_keywords(
        title=title,
        description=description,
        themes=themes,
        book_type=book_type,
    )
    subtitle_prompt = metadata_advisor_svc.optimize_subtitle(
        title=title,
        book_type=book_type,
        audience=audience,
    )
    compliance = metadata_advisor_svc.check_metadata_compliance(
        title=title,
        subtitle=subtitle,
        description=description,
        keywords=keywords,
    )

    return SuccessResponse(data={
        "categories": categories_prompt,
        "keywords": keywords_prompt,
        "subtitle_suggestions": subtitle_prompt,
        "compliance": compliance,
    })


# ---------------------------------------------------------------------------
# Asset Provenance & Rights Ledger (6.2)
# ---------------------------------------------------------------------------


@router.get(
    "/{book_type}/{book_id}/provenance",
    response_model=SuccessResponse[dict],
    summary="View provenance records for a book",
)
async def get_provenance(
    book_type: str,
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    records = await provenance.get_provenance(db, book_type, book_id)
    return SuccessResponse(data={"records": [vars(r) for r in records]})


@router.post(
    "/{book_type}/{book_id}/provenance/export",
    response_model=SuccessResponse[dict],
    summary="Export provenance compliance report",
)
async def export_provenance(
    book_type: str,
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    report = await provenance.export_provenance_report(db, book_type, book_id)
    return SuccessResponse(data=report)


# ---------------------------------------------------------------------------
# Originality Fingerprinting & Spam Detection (7.1-7.4)
# ---------------------------------------------------------------------------


@router.post(
    "/originality/fingerprint",
    response_model=SuccessResponse[dict],
    summary="Generate originality fingerprint for a book",
)
async def originality_fingerprint(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate pHash (images), grid hash (puzzles), Jaccard (word lists),
    and n-gram (text) fingerprints for duplicate detection.
    """
    content_type = payload.get("content_type", "text")
    content_data = payload.get("content_data", "")

    result = fingerprinting.generate_fingerprint(
        content_type=content_type,
        content_data=content_data,
    )
    return SuccessResponse(data=dataclasses.asdict(result))


@router.post(
    "/originality/compare",
    response_model=SuccessResponse[dict],
    summary="Compare two books for similarity",
)
async def originality_compare(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Compare originality fingerprints between two books and return a
    cross-book similarity matrix with component-level scores.
    """
    book_id = UUID(payload["book_id"])
    org_id = current_user["org_id"]

    comparisons = await fingerprinting.cross_book_comparison(
        db=db,
        org_id=org_id,
        book_id=book_id,
    )
    return SuccessResponse(data={
        "book_id": str(book_id),
        "comparisons": [
            {"other_book_id": str(other_id), "similarity": score}
            for other_id, score in comparisons
        ],
    })


@router.post(
    "/originality/spam-check",
    response_model=SuccessResponse[dict],
    summary="Run KDP spam risk analysis",
)
async def originality_spam_check(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analyze interior originality, metadata quality, minor-edit detection,
    and content substance to produce a KDP spam risk score.
    """
    book_type = payload.get("book_type", "childrens")
    book_id = UUID(payload["book_id"])
    org_id = current_user["org_id"]

    report = await spam_detector.calculate_spam_risk(
        db=db,
        book_type=book_type,
        book_id=book_id,
        org_id=org_id,
        title=payload.get("title", ""),
        keywords=payload.get("keywords"),
        description=payload.get("description", ""),
    )
    return SuccessResponse(data=report.to_dict())


# ---------------------------------------------------------------------------
# Print Cost & Pricing Engine (8.1)
# ---------------------------------------------------------------------------


@router.post(
    "/pricing/calculate",
    response_model=SuccessResponse[dict],
    summary="Calculate print cost and pricing scenarios",
)
async def pricing_calculate(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Calculate KDP print cost using page count, trim size, interior type,
    and ink coverage.  Returns cost breakdown, 3 pricing scenarios (minimum,
    recommended, premium), and margin guardrails.
    """
    page_count = payload.get("page_count", 0)
    interior_type = payload.get("interior_type", "bw")
    trim_size = payload.get("trim_size", "6x9")
    marketplace = payload.get("marketplace", "us")
    target_margins = payload.get("target_margins")

    cost = print_pricing.calculate_print_cost(
        page_count=page_count,
        interior_type=interior_type,
        trim_size=trim_size,
        marketplace=marketplace,
    )
    scenarios = print_pricing.generate_price_scenarios(
        cost=cost,
        target_margins=target_margins,
    )

    return SuccessResponse(data={
        "cost": cost,
        "scenarios": scenarios,
        "page_count": page_count,
        "interior_type": interior_type,
        "trim_size": trim_size,
        "marketplace": marketplace,
    })


@router.post(
    "/pricing/ink-coverage",
    response_model=SuccessResponse[dict],
    summary="Analyze ink coverage per page",
)
async def pricing_ink_coverage(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analyze ink coverage for each page of a book.  Returns per-page
    percentages and an aggregate ink density score.
    """
    pages_data = payload.get("pages_data", [])

    report = color_management.analyze_ink_coverage(pages_data)
    ink_factor = print_pricing.ink_coverage_factor(pages_data)

    return SuccessResponse(data={
        "pages": report,
        "ink_coverage_factor": ink_factor,
    })


# ---------------------------------------------------------------------------
# CMYK / Soft-Proof Workflow (8.2)
# ---------------------------------------------------------------------------


@router.post(
    "/color/soft-proof",
    response_model=SuccessResponse[dict],
    summary="CMYK soft-proof simulation",
)
async def color_soft_proof(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate side-by-side RGB vs CMYK soft-proof with out-of-gamut
    warnings, shadow crush detection, and ink density analysis.
    """
    page_data = payload.get("page_data", payload)

    result = color_management.soft_proof_data(page_data)
    return SuccessResponse(data=result)


@router.post(
    "/color/auto-adjust",
    response_model=SuccessResponse[dict],
    summary="Auto-fix gamut, ink density, and shadow issues",
)
async def color_auto_adjust(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Automatically adjust colors to fix out-of-gamut values, excessive
    ink density, and shadow crush in preparation for CMYK printing.
    """
    page_data = payload.get("page_data", payload)

    result = color_management.auto_adjust_colors(page_data)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Batch Factory Mode (6.4)
# ---------------------------------------------------------------------------


@router.post(
    "/batch",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a batch factory job",
)
async def create_batch_job(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a multi-volume batch generation job with cost guardrails,
    auto-QA per page, and queue management (pause/cancel).
    """
    org_id = current_user["org_id"]
    book_type = payload.get("book_type", "coloring")
    config = payload.get("config", payload)
    budget_limit_cents = payload.get("budget_limit_cents")

    result = await batch_factory.create_batch_job(
        db=db,
        org_id=org_id,
        book_type=book_type,
        config=config,
        budget_limit_cents=budget_limit_cents,
    )
    return SuccessResponse(data=result)


@router.get(
    "/batch/{job_id}/status",
    response_model=SuccessResponse[dict],
    summary="Get batch job status",
)
async def get_batch_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return current status, progress, and cost tracking for a batch job."""
    result = await batch_factory.get_batch_status(db=db, job_id=job_id)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Template & Pack Marketplace (6.5)
# ---------------------------------------------------------------------------


@router.get(
    "/templates",
    response_model=SuccessResponse[list[dict]],
    summary="List available templates and packs",
)
async def list_templates(
    book_type: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List available page layout templates, theme packs, and style packs
    filtered by book type and category.
    """
    templates = template_marketplace.get_templates(
        book_type=book_type,
        category=category,
    )
    return SuccessResponse(data=[dataclasses.asdict(t) for t in templates])


# ---------------------------------------------------------------------------
# Series Branding Manager (12.1)
# ---------------------------------------------------------------------------


@router.post(
    "/series",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a book series",
)
async def create_series(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new series with naming rules, cover template lock, spine
    preview settings, and theme coherence configuration.
    """
    org_id = current_user["org_id"]

    result = await series_manager.create_series(
        db=db,
        org_id=org_id,
        name=payload.get("name", ""),
        book_type=payload.get("book_type", "childrens"),
        naming_format=payload.get("naming_format"),
        branding_config=payload.get("branding_config"),
    )
    return SuccessResponse(data=dataclasses.asdict(result))


@router.get(
    "/series/{series_id}",
    response_model=SuccessResponse[dict],
    summary="Get series detail",
)
async def get_series(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return series metadata, branding config, and volume list."""
    result = await series_manager.get_series(db=db, series_id=series_id)
    return SuccessResponse(data=dataclasses.asdict(result))


@router.post(
    "/series/{series_id}/coherence-check",
    response_model=SuccessResponse[dict],
    summary="Check series consistency",
)
async def series_coherence_check(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Run a coherence check across all volumes in a series, validating
    branding, naming format, spine layout, and theme consistency.
    """
    result = await series_manager.check_coherence(db=db, series_id=series_id)
    return SuccessResponse(data=dataclasses.asdict(result))


# ---------------------------------------------------------------------------
# Back Matter CTA Engine (12.2)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/generate-back-matter",
    response_model=SuccessResponse[dict],
    summary="Generate back matter pages",
)
async def generate_back_matter(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate back matter pages including Also in Series, About Series,
    Email CTA, Review Request, and About Author sections.
    """
    pages: list[dict[str, Any]] = []

    # Also in Series
    series_id = payload.get("series_id")
    if series_id:
        series_uuid = UUID(series_id) if isinstance(series_id, str) else series_id
        also_page = await back_matter.generate_also_in_series(
            db=db, series_id=series_uuid, current_book_id=book_id,
        )
        pages.append(dataclasses.asdict(also_page))

        about_series_page = await back_matter.generate_about_series(
            db=db, series_id=series_uuid,
        )
        pages.append(dataclasses.asdict(about_series_page))

    # Email CTA
    cta_url = payload.get("cta_url")
    if cta_url:
        email_page = back_matter.generate_email_cta(cta_url=cta_url)
        pages.append(dataclasses.asdict(email_page))

    # Review Request
    if payload.get("include_review_request", True):
        review_page = back_matter.generate_review_request()
        pages.append(dataclasses.asdict(review_page))

    # About Author
    author_info = payload.get("author_info")
    if author_info:
        author_page = back_matter.generate_about_author(author_info=author_info)
        pages.append(dataclasses.asdict(author_page))

    return SuccessResponse(data={"pages": pages})


# ---------------------------------------------------------------------------
# QR Code Generation (12.2)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/generate-qr-code",
    response_model=SuccessResponse[dict],
    summary="Generate QR code from CTA URL",
)
async def generate_qr_code(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a print-ready QR code from a CTA URL for back matter pages."""
    url = payload.get("url", "")
    box_size = payload.get("box_size", 10)
    border = payload.get("border", 4)

    qr_data = back_matter.generate_qr_code(
        url=url,
        box_size=box_size,
        border=border,
    )
    return SuccessResponse(data={
        "qr_code_base64": qr_data,
        "url": url,
    })


# ---------------------------------------------------------------------------
# Accessibility Pack (11.1-11.3)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/generate-accessible-variant",
    response_model=SuccessResponse[dict],
    summary="Create accessible edition",
)
async def generate_accessible_variant(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create an accessible variant (dyslexia-friendly, large print, or
    high contrast) of an existing book.  Returns a new book copy with
    adjusted formatting - the original is unchanged.
    """
    variant_type = payload.get("variant_type", "dyslexia_friendly")
    book_data = payload.get("book_data", payload)

    if variant_type == "dyslexia_friendly":
        result = accessibility.generate_dyslexia_variant(book_data)
    elif variant_type == "large_print":
        result = accessibility.generate_large_print_variant(book_data)
    elif variant_type == "high_contrast":
        result = accessibility.generate_high_contrast_variant(book_data)
    else:
        result = accessibility.generate_dyslexia_variant(book_data)

    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Device Preview System (9.2)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/device-preview",
    response_model=SuccessResponse[dict],
    summary="Generate device-accurate preview images",
)
async def device_preview_endpoint(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate preview images for up to 6 devices: Kindle Fire HD 10,
    Kindle Fire HD 8, Kindle Paperwhite, iPad, iPad Mini, and iPhone.
    """
    page_data = (payload or {}).get("page_data", payload or {})
    device = (payload or {}).get("device")

    if device:
        result = device_preview.generate_preview(
            page_data=page_data,
            device=device,
        )
    else:
        result = device_preview.generate_all_previews(page_data=page_data)

    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Safe-Zone Heatmap Overlay (10.1)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/safe-zone-heatmap",
    response_model=SuccessResponse[dict],
    summary="Generate safe-zone heatmap overlay",
)
async def safe_zone_heatmap(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate color-coded bleed/trim/safe/gutter zone overlay with
    face and text detection highlighting.
    """
    data = payload or {}
    page_data = data.get("page_data", data)
    trim_size = data.get("trim_size", "8.5x11")

    result = layout_protection.generate_safe_zone_heatmap(
        page_data=page_data,
        trim_size=trim_size,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Gutter Collision Detector (10.2)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/gutter-check",
    response_model=SuccessResponse[dict],
    summary="Detect gutter collisions",
)
async def gutter_check(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Detect faces and text near the fold gutter and suggest auto-shift
    corrections.
    """
    data = payload or {}
    page_data = data.get("page_data", data)
    spine_width = data.get("spine_width", 0.5)

    collisions = layout_protection.check_gutter_collision(
        page_data=page_data,
        spine_width=spine_width,
    )
    return SuccessResponse(data={"collisions": collisions})


# ---------------------------------------------------------------------------
# Auto-Reflow for Alternate Trim Sizes (10.3)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/reflow",
    response_model=SuccessResponse[dict],
    summary="Reflow book to alternate trim size",
)
async def reflow(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Convert a book between trim sizes with auto-repositioned text
    and scaled illustrations.  Creates a new book copy.
    """
    book_data = payload.get("book_data", payload)
    target_trim_size = payload.get("target_trim_size", "6x9")

    result = layout_protection.auto_reflow(
        book_data=book_data,
        target_trim_size=target_trim_size,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Multi-Distributor Preflight (12.5)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/distributor-preflight",
    response_model=SuccessResponse[dict],
    summary="Run distributor-specific preflight",
)
async def distributor_preflight(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Run preflight checks for a specific distributor (KDP, IngramSpark,
    or B&N Press) and generate per-distributor export files (including
    PDF/X-1a for IngramSpark).
    """
    distributor = payload.get("distributor", "kdp")
    book_data = payload.get("book_data")

    result = await distributor_svc.run_distributor_preflight(
        db=db,
        book_type=book_type,
        book_id=book_id,
        distributor=distributor,
        book_data=book_data,
    )
    return SuccessResponse(data={
        "status": result.status,
        "distributor": result.distributor,
        "checks": [
            {"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity}
            for c in result.checks
        ],
        "issues": [
            {"name": i.name, "message": i.message, "severity": i.severity}
            for i in result.issues
        ],
    })


# ---------------------------------------------------------------------------
# Fixed-Layout Kindle Export (9.1)
# ---------------------------------------------------------------------------


@router.post(
    "/{book_type}/{book_id}/export-kindle",
    response_model=SuccessResponse[dict],
    summary="Fixed-layout KPF/EPUB export",
)
async def export_kindle(
    book_type: str,
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate fixed-layout KPF and/or EPUB 3 files with read order
    mapping, text pop-up support, and read-aloud sync data.
    """
    data = payload or {}
    book_data = data.get("book_data", data)
    export_format = data.get("format", "kpf")

    if export_format == "epub":
        file_bytes = kindle_export.generate_fixed_epub(
            book_type=book_type,
            book_data=book_data,
        )
    else:
        file_bytes = kindle_export.generate_kpf(
            book_type=book_type,
            book_data=book_data,
        )

    encoded = base64.b64encode(file_bytes).decode("ascii")

    return SuccessResponse(data={
        "format": export_format,
        "file_base64": encoded,
        "file_size_bytes": len(file_bytes),
        "book_type": book_type,
        "book_id": str(book_id),
    })
