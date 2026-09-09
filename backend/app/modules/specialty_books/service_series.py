"""Service layer for Series Branding, Bundles, ISBN, Back Matter, and Multi-Distributor.

Implements blueprint sections 12.1-12.6:
- 12.1 Series Branding Manager
- 12.2 Back Matter CTA Engine
- 12.3 Bundle / Box Set Creator
- 12.4 ISBN & Barcode Management
- 12.5 Multi-Distributor Preflight
- 12.6 Review Feedback Loop
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty_books.models_series import (
    BackMatterTemplate,
    BackMatterTemplateType,
    BookBundle,
    BookSeries,
    BookType,
    DistributorPreflight,
    DistributorTarget,
    ISBNPool,
    ISBNStatus,
)

logger = logging.getLogger(__name__)


# ── 12.1 Series Branding Manager ────────────────────────────────────────────


async def create_series(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Create a new book series with naming rules and branding config.

    Parameters
    ----------
    data : dict
        Required: name, book_type.
        Optional: naming_format, branding_config, branding_locked.
        branding_config keys: title_font, title_position, author_position,
                              volume_badge_style, spine_layout, color_scheme.
    """
    series = BookSeries(
        org_id=org_id,
        name=data["name"],
        book_type=data.get("book_type", BookType.COLORING.value),
        naming_format=data.get("naming_format", "{Series Name} Vol. {N}: {Subtitle}"),
        branding_config=data.get("branding_config"),
        branding_locked=data.get("branding_locked", False),
        volume_count=0,
    )
    db.add(series)
    await db.flush()

    logger.info("Created series %s for org %s", series.id, org_id)
    return _series_to_dict(series)


async def get_series(
    db: AsyncSession,
    series_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Fetch a single series by ID."""
    stmt = select(BookSeries).where(
        BookSeries.id == series_id,
        BookSeries.org_id == org_id,
        BookSeries.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()
    if series is None:
        return None
    return _series_to_dict(series)


async def update_series_branding(
    db: AsyncSession,
    series_id: uuid.UUID,
    org_id: uuid.UUID,
    branding_updates: dict[str, Any],
) -> dict[str, Any]:
    """Update branding config on a series.  Raises if branding is locked."""
    stmt = select(BookSeries).where(
        BookSeries.id == series_id,
        BookSeries.org_id == org_id,
        BookSeries.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()
    if series is None:
        raise ValueError(f"Series {series_id} not found")

    if series.branding_locked:
        locked_keys = set((series.branding_config or {}).keys())
        attempted_keys = set(branding_updates.keys())
        conflicts = locked_keys & attempted_keys
        if conflicts:
            raise ValueError(f"Branding is locked. Cannot modify: {', '.join(sorted(conflicts))}")

    existing = dict(series.branding_config or {})
    existing.update(branding_updates)
    series.branding_config = existing
    await db.flush()

    return _series_to_dict(series)


def _series_to_dict(series: BookSeries) -> dict[str, Any]:
    return {
        "id": series.id,
        "org_id": series.org_id,
        "name": series.name,
        "book_type": series.book_type,
        "naming_format": series.naming_format,
        "branding_config": series.branding_config,
        "branding_locked": series.branding_locked,
        "volume_count": series.volume_count,
        "created_at": series.created_at,
    }


# ── 12.1b Theme Coherence Scorer ────────────────────────────────────────────


async def check_series_coherence(
    db: AsyncSession,
    series_id: uuid.UUID,
    org_id: uuid.UUID,
    volumes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score naming / cover / spine consistency across volumes.

    Parameters
    ----------
    volumes : list[dict] | None
        Pre-fetched volume dicts with keys: title, volume_number, metadata.
        If None, returns a basic check using only the series record.

    Returns
    -------
    dict with score (0-100), issues: [{volume, issue_type, description}].
    """
    stmt = select(BookSeries).where(
        BookSeries.id == series_id,
        BookSeries.org_id == org_id,
        BookSeries.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()
    if series is None:
        raise ValueError(f"Series {series_id} not found")

    issues: list[dict[str, Any]] = []
    score = 100

    if volumes is None or len(volumes) < 2:
        return {"score": score, "issues": [], "volume_count": len(volumes or [])}

    branding_config = series.branding_config or {}

    # Check naming consistency
    for vol in volumes:
        title = vol.get("title", "")
        if series.name and series.name not in title:
            issues.append(
                {
                    "volume": vol.get("volume_number"),
                    "issue_type": "naming",
                    "description": f"Title '{title}' does not contain series name '{series.name}'",
                }
            )
            score -= 10

    # Check branding consistency (if locked)
    if series.branding_locked and branding_config:
        expected_font = branding_config.get("title_font")
        expected_spine = branding_config.get("spine_layout")
        for vol in volumes:
            vol_meta = vol.get("metadata") or {}
            vol_branding = vol_meta.get("branding", {})
            if expected_font and vol_branding.get("title_font") != expected_font:
                issues.append(
                    {
                        "volume": vol.get("volume_number"),
                        "issue_type": "cover_template",
                        "description": (
                            f"Title font mismatch: expected '{expected_font}', "
                            f"found '{vol_branding.get('title_font', 'none')}'"
                        ),
                    }
                )
                score -= 15
            if expected_spine and vol_branding.get("spine_layout") != expected_spine:
                issues.append(
                    {
                        "volume": vol.get("volume_number"),
                        "issue_type": "spine",
                        "description": (
                            f"Spine layout mismatch: expected '{expected_spine}', "
                            f"found '{vol_branding.get('spine_layout', 'none')}'"
                        ),
                    }
                )
                score -= 10

    score = max(0, min(100, score))
    return {
        "score": score,
        "issues": issues,
        "volume_count": len(volumes),
    }


# ── 12.2 Back Matter CTA Engine ─────────────────────────────────────────────

# Template content generators keyed by type
_BACK_MATTER_GENERATORS: dict[str, Any] = {}


def _register_generator(template_type: str):
    """Decorator to register a back-matter content generator."""

    def decorator(func):
        _BACK_MATTER_GENERATORS[template_type] = func
        return func

    return decorator


@_register_generator(BackMatterTemplateType.ALSO_IN_SERIES.value)
def _gen_also_in_series(context: dict[str, Any]) -> str:
    series_name = context.get("series_name", "This Series")
    volumes = context.get("volumes", [])
    lines = [f"Also in {series_name}:", ""]
    for vol in volumes:
        lines.append(f"  - {vol.get('title', 'Untitled')}")
    if not volumes:
        lines.append("  More volumes coming soon!")
    return "\n".join(lines)


@_register_generator(BackMatterTemplateType.ABOUT_SERIES.value)
def _gen_about_series(context: dict[str, Any]) -> str:
    series_name = context.get("series_name", "This Series")
    description = context.get("series_description", "")
    return f"About {series_name}\n\n{description}" if description else f"About {series_name}"


@_register_generator(BackMatterTemplateType.EMAIL_CTA.value)
def _gen_email_cta(context: dict[str, Any]) -> str:
    cta_url = context.get("cta_url", "https://example.com/signup")
    lines = [
        "Join Our Reader Community!",
        "",
        "Get free bonus content, new release alerts, and exclusive deals.",
        "",
        f"Sign up at: {cta_url}",
        "",
        "Or scan the QR code on this page!",
    ]
    return "\n".join(lines)


@_register_generator(BackMatterTemplateType.REVIEW_REQUEST.value)
def _gen_review_request(context: dict[str, Any]) -> str:
    lines = [
        "Did You Enjoy This Book?",
        "",
        "Your review helps other readers discover books they'll love.",
        "",
        "Please take a moment to leave an honest review on Amazon.",
        "Even a short sentence makes a big difference!",
        "",
        "Thank you for your support!",
    ]
    return "\n".join(lines)


@_register_generator(BackMatterTemplateType.ABOUT_AUTHOR.value)
def _gen_about_author(context: dict[str, Any]) -> str:
    author_name = context.get("author_name", "The Author")
    bio = context.get("author_bio", "")
    return f"About {author_name}\n\n{bio}" if bio else f"About {author_name}"


async def generate_back_matter(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
    templates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate back-matter pages for a book from selected template types.

    Parameters
    ----------
    templates : list[dict]
        Each dict has at minimum: template_type (str).
        Optional keys depend on template type: cta_url, author_name,
        author_bio, series_name, series_description, volumes.

    Returns
    -------
    list of generated page dicts with template_type, content, qr_code_url (if applicable).
    """
    generated_pages: list[dict[str, Any]] = []

    for tmpl in templates:
        template_type = tmpl.get("template_type", "")
        generator = _BACK_MATTER_GENERATORS.get(template_type)
        if generator is None:
            logger.warning("Unknown back-matter template type: %s", template_type)
            continue

        context = dict(tmpl)
        content = generator(context)

        qr_code_url = None
        if template_type == BackMatterTemplateType.EMAIL_CTA.value:
            cta_url = tmpl.get("cta_url", "https://example.com/signup")
            qr_data = generate_qr_code(cta_url)
            qr_code_url = qr_data.get("qr_code_data_uri")

        # Persist template record
        record = BackMatterTemplate(
            org_id=org_id,
            template_type=template_type,
            content=content,
            cta_url=tmpl.get("cta_url"),
            qr_code_url=qr_code_url,
        )
        db.add(record)
        await db.flush()

        generated_pages.append(
            {
                "id": record.id,
                "template_type": template_type,
                "content": content,
                "qr_code_url": qr_code_url,
            }
        )

    logger.info(
        "Generated %d back-matter pages for %s/%s",
        len(generated_pages),
        book_type,
        book_id,
    )
    return generated_pages


# ── 12.2b QR Code Generation ────────────────────────────────────────────────


def generate_qr_code(
    url: str,
    size_px: int = 300,
    error_correction: str = "M",
) -> dict[str, Any]:
    """Generate a QR code image from a URL.

    Returns a dict with qr_code_data_uri (base64-encoded PNG) and metadata.
    Uses a deterministic placeholder; in production would use the ``qrcode`` library.
    """
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]

    # Build a placeholder data-URI (in production: qrcode.make(url) -> PNG -> base64)
    payload = f"QR|{error_correction}|{size_px}|{url}".encode()
    b64 = base64.b64encode(payload).decode()
    qr_data_uri = f"data:image/png;base64,{b64}"

    return {
        "qr_code_data_uri": qr_data_uri,
        "url_encoded": url,
        "size_px": size_px,
        "error_correction": error_correction,
        "hash": url_hash,
    }


# ── 12.3 Bundle / Box Set Creator ───────────────────────────────────────────


async def create_bundle(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Combine multiple volumes into a 'Complete Collection' bundle.

    Parameters
    ----------
    data : dict
        Required: title, book_type, volume_ids (list[UUID]).
        Optional: series_id, config, volume_page_counts (list[dict] with
        title & page_count per volume for offline calculation).
    """
    volume_ids = data.get("volume_ids", [])
    book_type = data.get("book_type", BookType.COLORING.value)
    config = data.get("config") or {}
    volume_page_counts = data.get("volume_page_counts", [])

    total_pages = 0
    combined_toc: list[dict[str, Any]] = []
    section_dividers: list[dict[str, Any]] = []

    for idx, vid in enumerate(volume_ids):
        vol_info = (
            volume_page_counts[idx]
            if idx < len(volume_page_counts)
            else {"title": f"Volume {idx + 1}", "page_count": 0}
        )
        vol_pages = vol_info.get("page_count", 0)
        combined_toc.append(
            {
                "volume_index": idx + 1,
                "volume_title": vol_info.get("title", f"Volume {idx + 1}"),
                "start_page": total_pages + 1,
                "page_count": vol_pages,
            }
        )
        if idx > 0:
            section_dividers.append(
                {
                    "after_page": total_pages,
                    "title": vol_info.get("title", f"Volume {idx + 1}"),
                }
            )
        total_pages += vol_pages

    # Add divider pages to total
    total_pages += len(section_dividers)

    # If puzzle books, note combined answer key
    combined_answer_key = False
    if book_type == BookType.PUZZLE.value:
        combined_answer_key = config.get("combined_answers", True)

    enriched_config = {
        **config,
        "combined_toc": combined_toc,
        "section_dividers": section_dividers,
        "combined_answer_key": combined_answer_key,
    }

    bundle = BookBundle(
        org_id=org_id,
        title=data["title"],
        book_type=book_type,
        volume_ids=[str(v) for v in volume_ids],
        series_id=data.get("series_id"),
        config=enriched_config,
        total_pages=total_pages,
    )
    db.add(bundle)
    await db.flush()

    logger.info(
        "Created bundle %s with %d volumes, %d pages",
        bundle.id,
        len(volume_ids),
        total_pages,
    )
    return _bundle_to_dict(bundle)


async def get_bundle(
    db: AsyncSession,
    bundle_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Fetch a bundle by ID."""
    stmt = select(BookBundle).where(
        BookBundle.id == bundle_id,
        BookBundle.org_id == org_id,
        BookBundle.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    bundle = result.scalar_one_or_none()
    if bundle is None:
        return None
    return _bundle_to_dict(bundle)


def _bundle_to_dict(bundle: BookBundle) -> dict[str, Any]:
    return {
        "id": bundle.id,
        "org_id": bundle.org_id,
        "title": bundle.title,
        "book_type": bundle.book_type,
        "volume_ids": bundle.volume_ids,
        "series_id": bundle.series_id,
        "config": bundle.config,
        "total_pages": bundle.total_pages,
        "created_at": bundle.created_at,
    }


# ── 12.4 ISBN & Barcode Management ──────────────────────────────────────────


async def manage_isbn(
    db: AsyncSession,
    org_id: uuid.UUID,
    action: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """ISBN pool management: add, assign, generate barcode, query status.

    Actions
    -------
    - ``add_to_pool``: bulk-add ISBNs.  data.isbns, data.publisher_name
    - ``assign``: assign ISBN to book.  data.isbn (optional), data.book_type, data.book_id
    - ``generate_barcode``: generate EAN-13 barcode.  data.isbn
    - ``get_status``: query ISBN status.  data.isbn
    """
    if action == "add_to_pool":
        return await _isbn_add_to_pool(db, org_id, data)
    if action == "assign":
        return await _isbn_assign(db, org_id, data)
    if action == "generate_barcode":
        return _isbn_generate_barcode(data.get("isbn", ""))
    if action == "get_status":
        return await _isbn_get_status(db, org_id, data.get("isbn", ""))
    raise ValueError(f"Unknown ISBN action: {action}")


async def _isbn_add_to_pool(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Add ISBNs to the org's pool."""
    isbns = data.get("isbns", [])
    publisher_name = data.get("publisher_name", "")
    added: list[dict[str, Any]] = []

    for isbn_str in isbns:
        isbn_str = isbn_str.strip()
        if not _validate_isbn13(isbn_str):
            logger.warning("Invalid ISBN-13 skipped: %s", isbn_str)
            continue
        record = ISBNPool(
            org_id=org_id,
            isbn=isbn_str,
            publisher_name=publisher_name,
            status=ISBNStatus.AVAILABLE.value,
        )
        db.add(record)
        await db.flush()
        added.append({"id": record.id, "isbn": isbn_str, "status": record.status})

    return {"added": added, "count": len(added)}


async def _isbn_assign(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Assign an ISBN from the pool (or a specific one) to a book."""
    specific_isbn = data.get("isbn")
    book_type = data.get("book_type", "")
    book_id = data.get("book_id")

    if specific_isbn:
        stmt = select(ISBNPool).where(
            ISBNPool.isbn == specific_isbn,
            ISBNPool.org_id == org_id,
            ISBNPool.deleted_at.is_(None),
        )
    else:
        # Auto-assign: pick next available
        stmt = (
            select(ISBNPool)
            .where(
                ISBNPool.org_id == org_id,
                ISBNPool.status == ISBNStatus.AVAILABLE.value,
                ISBNPool.deleted_at.is_(None),
            )
            .order_by(ISBNPool.created_at)
            .limit(1)
        )

    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise ValueError("No available ISBN found in pool")

    if record.status != ISBNStatus.AVAILABLE.value:
        raise ValueError(f"ISBN {record.isbn} is not available (status={record.status})")

    record.status = ISBNStatus.ASSIGNED.value
    record.assigned_to_book_type = book_type
    record.assigned_to_book_id = book_id

    # Auto-generate barcode
    barcode_data = _isbn_generate_barcode(record.isbn)
    record.barcode_url = barcode_data.get("barcode_data_uri")

    await db.flush()

    return {
        "id": record.id,
        "isbn": record.isbn,
        "publisher_name": record.publisher_name,
        "assigned_to_book_type": record.assigned_to_book_type,
        "assigned_to_book_id": record.assigned_to_book_id,
        "barcode_url": record.barcode_url,
        "status": record.status,
    }


async def _isbn_get_status(
    db: AsyncSession,
    org_id: uuid.UUID,
    isbn: str,
) -> dict[str, Any]:
    """Query the status of an ISBN."""
    stmt = select(ISBNPool).where(
        ISBNPool.isbn == isbn,
        ISBNPool.org_id == org_id,
        ISBNPool.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise ValueError(f"ISBN {isbn} not found in pool")

    return {
        "id": record.id,
        "isbn": record.isbn,
        "status": record.status,
        "assigned_to_book_type": record.assigned_to_book_type,
        "assigned_to_book_id": record.assigned_to_book_id,
        "barcode_url": record.barcode_url,
    }


def _validate_isbn13(isbn: str) -> bool:
    """Validate an ISBN-13 string using check-digit verification."""
    if not re.match(r"^\d{13}$", isbn):
        return False
    total = 0
    for i, ch in enumerate(isbn):
        digit = int(ch)
        total += digit if i % 2 == 0 else digit * 3
    return total % 10 == 0


def _isbn_generate_barcode(isbn: str) -> dict[str, Any]:
    """Generate an EAN-13 barcode image from an ISBN.

    In production this would use ``python-barcode`` or ``reportlab``.
    Returns a deterministic placeholder data URI.
    """
    payload = f"EAN13|{isbn}".encode()
    b64 = base64.b64encode(payload).decode()
    data_uri = f"data:image/png;base64,{b64}"
    return {
        "isbn": isbn,
        "barcode_data_uri": data_uri,
        "format": "EAN-13",
        "valid": _validate_isbn13(isbn),
        "placement_guide": {
            "position": "back_cover_bottom_right",
            "min_width_mm": 36,
            "min_height_mm": 26,
            "quiet_zone_mm": 5,
        },
    }


# ── 12.5 Multi-Distributor Preflight ────────────────────────────────────────

# Distributor-specific check definitions
_KDP_CHECKS: list[tuple[str, str]] = [
    ("margins", 'Interior margins meet KDP minimums (0.375" inside, 0.25" outside)'),
    ("dpi", "Image resolution >= 300 DPI"),
    ("page_count", "Page count within KDP limits (24-828 pages)"),
    ("file_size", "PDF file size under 650 MB"),
    ("bleed", 'Bleed extends 0.125" on trim edges'),
    ("cover_dimensions", "Cover matches calculated dimensions for trim + page count"),
    ("font_embedding", "All fonts embedded in PDF"),
]

_INGRAM_CHECKS: list[tuple[str, str]] = [
    *_KDP_CHECKS,
    ("pdf_x1a", "PDF/X-1a compliance verified"),
    ("icc_profile", "ICC color profile (FOGRA39 or GRACoL) embedded"),
    ("ink_density", "Total ink density under 300%"),
    ("transparency", "No transparency in final output"),
    ("overprint", "Overprint settings verified"),
]

_BN_CHECKS: list[tuple[str, str]] = [
    ("margins", "Interior margins meet B&N Press minimums"),
    ("dpi", "Image resolution >= 300 DPI"),
    ("page_count", "Page count within B&N limits (24-800 pages)"),
    ("file_size", "PDF file size under 400 MB"),
    ("cover_format", "Cover submitted as separate PDF"),
    ("font_embedding", "All fonts embedded in PDF"),
    ("isbn", "Valid ISBN-13 assigned"),
]


async def run_distributor_preflight(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
    distributor: str,
    page_count: int = 0,
) -> dict[str, Any]:
    """Run distributor-specific preflight checks.

    Parameters
    ----------
    page_count : int
        Page count for the book (avoids DB lookup when testing).

    Returns
    -------
    dict with distributor, status (PASSED/FAILED), checks, export_url.
    """
    check_defs = _get_checks_for_distributor(distributor)
    checks_result: list[dict[str, Any]] = []

    book_info: dict[str, Any] = {
        "book_type": book_type,
        "book_id": book_id,
        "page_count": page_count,
        "trim_size": "8.5x11",
    }

    for check_name, description in check_defs:
        passed, details = _run_single_check(check_name, book_info, distributor)
        checks_result.append(
            {
                "name": check_name,
                "passed": passed,
                "details": details,
                "severity": "error" if not passed else "info",
            }
        )

    all_passed = all(c["passed"] for c in checks_result)
    status = "PASSED" if all_passed else "FAILED"

    export_url = None
    if all_passed:
        export_url = f"/exports/{book_type}/{book_id}/{distributor}/print-ready.pdf"

    # Persist preflight record
    record = DistributorPreflight(
        org_id=org_id,
        book_type=book_type,
        book_id=book_id,
        distributor=distributor,
        status=status,
        checks=checks_result,
        issues=[c for c in checks_result if not c["passed"]],
        exported_url=export_url,
    )
    db.add(record)
    await db.flush()

    return {
        "id": record.id,
        "distributor": distributor,
        "status": status,
        "checks": checks_result,
        "export_url": export_url,
        "all_passed": all_passed,
    }


def _get_checks_for_distributor(distributor: str) -> list[tuple[str, str]]:
    if distributor == DistributorTarget.KDP.value:
        return _KDP_CHECKS
    if distributor == DistributorTarget.INGRAM_SPARK.value:
        return _INGRAM_CHECKS
    if distributor == DistributorTarget.BN_PRESS.value:
        return _BN_CHECKS
    return _KDP_CHECKS


def _run_single_check(
    check_name: str,
    book_info: dict[str, Any],
    distributor: str,
) -> tuple[bool, str]:
    """Execute a single preflight check.  Returns (passed, details)."""
    page_count = book_info.get("page_count", 0)

    if check_name == "page_count":
        if distributor == DistributorTarget.BN_PRESS.value:
            ok = 24 <= page_count <= 800
            return ok, f"Page count: {page_count} (B&N range: 24-800)"
        ok = 24 <= page_count <= 828
        return ok, f"Page count: {page_count} (range: 24-828)"

    if check_name == "dpi":
        return True, "All images >= 300 DPI (simulated check)"
    if check_name == "margins":
        return True, "Margins meet distributor minimums (simulated check)"
    if check_name == "file_size":
        return True, "File size within limits (simulated check)"
    if check_name == "bleed":
        return True, 'Bleed extends 0.125" on trim edges (simulated check)'
    if check_name == "cover_dimensions":
        return True, "Cover dimensions match specification (simulated check)"
    if check_name == "font_embedding":
        return True, "All fonts embedded (simulated check)"
    if check_name == "pdf_x1a":
        return True, "PDF/X-1a compliance verified (simulated check)"
    if check_name == "icc_profile":
        return True, "ICC color profile embedded (simulated check)"
    if check_name == "ink_density":
        return True, "Total ink density under 300% (simulated check)"
    if check_name == "transparency":
        return True, "No transparency detected (simulated check)"
    if check_name == "overprint":
        return True, "Overprint settings verified (simulated check)"
    if check_name == "cover_format":
        return True, "Cover submitted as separate PDF (simulated check)"
    if check_name == "isbn":
        return True, "Valid ISBN-13 assigned (simulated check)"

    return True, f"Check '{check_name}' passed (simulated)"


# ── 12.6 Review Feedback Loop ───────────────────────────────────────────────

# Complaint -> fix mapping database
_COMPLAINT_MAPPINGS: dict[str, dict[str, Any]] = {
    "pages thin": {
        "suggested_fix": "Upgrade paper type from standard to premium/thick",
        "automated_action": "suggest_paper_upgrade",
        "automated_action_available": True,
    },
    "colors washed": {
        "suggested_fix": "Run CMYK soft-proof and adjust color profiles",
        "automated_action": "run_cmyk_softproof",
        "automated_action_available": True,
    },
    "text too small": {
        "suggested_fix": "Check font sizes and consider generating large-print variant",
        "automated_action": "check_font_sizes",
        "automated_action_available": True,
    },
    "puzzles too easy": {
        "suggested_fix": "Recalibrate difficulty upward; increase grid sizes or reduce hints",
        "automated_action": "recalibrate_difficulty_up",
        "automated_action_available": True,
    },
    "puzzles too hard": {
        "suggested_fix": "Recalibrate difficulty downward; add hints or reduce grid complexity",
        "automated_action": "recalibrate_difficulty_down",
        "automated_action_available": True,
    },
    "answers wrong": {
        "suggested_fix": "Re-verify all answer keys against puzzle grids",
        "automated_action": "reverify_answer_keys",
        "automated_action_available": True,
    },
    "print quality poor": {
        "suggested_fix": "Check image DPI and run preflight; ensure 300+ DPI throughout",
        "automated_action": "run_dpi_check",
        "automated_action_available": True,
    },
    "spine text unreadable": {
        "suggested_fix": "Increase spine font size or adjust spine layout",
        "automated_action": "adjust_spine_layout",
        "automated_action_available": False,
    },
    "binding loose": {
        "suggested_fix": "Consider upgrading to case laminate or hardcover binding",
        "automated_action": None,
        "automated_action_available": False,
    },
}


async def process_review_feedback(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
    complaints: list[str],
) -> dict[str, Any]:
    """Map common reader complaints to actionable fixes.

    Parameters
    ----------
    complaints : list[str]
        Free-text complaint phrases (e.g. "pages thin", "colors washed").

    Returns
    -------
    dict with mappings: [{complaint, suggested_fix, automated_action_available}]
    """
    mappings: list[dict[str, Any]] = []

    for complaint in complaints:
        complaint_lower = complaint.strip().lower()
        match = _find_best_complaint_match(complaint_lower)
        if match:
            mappings.append(
                {
                    "complaint": complaint,
                    "suggested_fix": match["suggested_fix"],
                    "automated_action": match.get("automated_action"),
                    "automated_action_available": match["automated_action_available"],
                }
            )
        else:
            mappings.append(
                {
                    "complaint": complaint,
                    "suggested_fix": "Manual review recommended - no automated fix available",
                    "automated_action": None,
                    "automated_action_available": False,
                }
            )

    logger.info(
        "Processed %d review complaints for %s/%s, %d matched",
        len(complaints),
        book_type,
        book_id,
        sum(1 for m in mappings if m["automated_action_available"]),
    )

    return {"mappings": mappings}


def _find_best_complaint_match(complaint: str) -> dict[str, Any] | None:
    """Find the best matching complaint template using substring matching."""
    # Exact match first
    if complaint in _COMPLAINT_MAPPINGS:
        return _COMPLAINT_MAPPINGS[complaint]

    # Substring/keyword match
    best_match = None
    best_score = 0
    for key, mapping in _COMPLAINT_MAPPINGS.items():
        key_words = set(key.split())
        complaint_words = set(complaint.split())
        overlap = len(key_words & complaint_words)
        if overlap > best_score:
            best_score = overlap
            best_match = mapping

    return best_match if best_score > 0 else None
