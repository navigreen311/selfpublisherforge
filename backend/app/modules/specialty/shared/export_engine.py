"""Shared Export Engine for specialty book types.

Produces structured manifests for PDF rendering, PDF/X-1a compliance,
PNG page export, and export metadata calculation.  Each book type
(children's, coloring, puzzle) delegates to these functions so that
page ordering, bleed calculations, crop/registration marks, and
print-cost estimation are consistent across the platform.

Blueprint refs: 12.1 - 12.5
"""
from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DPI = 300

# Standard bleed for print-on-demand (inches per side)
BLEED_IN = 0.125

# Standard registration mark inset from trim edge (inches)
REGISTRATION_MARK_INSET_IN = 0.25

# IngramSpark PDF/X-1a ICC profile
ICC_PROFILE_GRACOL = "GRACoL2006_Coated1v2"

# Spine width per page (inches) – 60# uncoated stock
SPINE_WIDTH_PER_PAGE_IN = 0.002252

# Estimated file sizes per page at 300 DPI (MB)
_FILE_SIZE_ESTIMATES_MB: dict[str, float] = {
    "childrens": 2.5,   # full-color illustrations
    "coloring": 0.8,    # B&W line art
    "puzzles": 0.3,     # text-heavy layout
}

# Estimated print cost per page (USD) by interior type
_PRINT_COST_PER_PAGE: dict[str, float] = {
    "color": 0.07,
    "bw": 0.012,
}

# Base fixed print cost (cover + setup)
_PRINT_COST_BASE: float = 0.85


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_trim_size(trim_size: str) -> tuple[float, float]:
    """Parse a trim size string like '8.5x11' into (width_in, height_in)."""
    parts = trim_size.split("x")
    width = float(parts[0]) if len(parts) > 0 else 8.5
    height = float(parts[1]) if len(parts) > 1 else 11.0
    return width, height


def _in_to_px(inches: float, dpi: int = DPI) -> int:
    """Convert inches to pixels at the given DPI."""
    return int(round(inches * dpi))


def _crop_mark_positions(
    trim_w: float, trim_h: float, bleed: float = BLEED_IN,
) -> list[dict[str, Any]]:
    """Calculate crop mark positions at the four corners of the trim area.

    Crop marks sit in the bleed zone and indicate where to cut.
    Returns coordinates in inches relative to the full (bleed-inclusive) page.
    """
    mark_length = 0.25  # inches

    marks: list[dict[str, Any]] = []
    corners = [
        ("top_left", bleed, bleed),
        ("top_right", bleed + trim_w, bleed),
        ("bottom_left", bleed, bleed + trim_h),
        ("bottom_right", bleed + trim_w, bleed + trim_h),
    ]
    for name, x, y in corners:
        marks.append({
            "corner": name,
            "x_in": round(x, 4),
            "y_in": round(y, 4),
            "mark_length_in": mark_length,
            "orientation": "cross",
        })
    return marks


def _registration_marks(
    full_w: float, full_h: float,
) -> list[dict[str, Any]]:
    """Place registration marks (circles + crosshairs) for CMYK plate alignment.

    One mark centered on each edge of the page, inset from the bleed edge.
    """
    inset = REGISTRATION_MARK_INSET_IN
    diameter = 0.125  # inches

    return [
        {"edge": "top", "x_in": round(full_w / 2, 4), "y_in": round(inset, 4), "diameter_in": diameter},
        {"edge": "bottom", "x_in": round(full_w / 2, 4), "y_in": round(full_h - inset, 4), "diameter_in": diameter},
        {"edge": "left", "x_in": round(inset, 4), "y_in": round(full_h / 2, 4), "diameter_in": diameter},
        {"edge": "right", "x_in": round(full_w - inset, 4), "y_in": round(full_h / 2, 4), "diameter_in": diameter},
    ]


def _get_book_field(book: Any, field: str, default: Any = None) -> Any:
    """Retrieve a field from a book that may be a dict or ORM object."""
    if isinstance(book, dict):
        return book.get(field, default)
    return getattr(book, field, default)


# ---------------------------------------------------------------------------
# 1. generate_pdf_manifest
# ---------------------------------------------------------------------------

def generate_pdf_manifest(
    book_type: str,
    book_data: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a structured PDF manifest that a renderer could consume.

    Parameters
    ----------
    book_type:
        One of ``childrens``, ``coloring``, ``puzzles``.
    book_data:
        Book metadata dict.  Expected keys vary by type but typically
        include ``trim_size``, ``pages`` (list of page dicts), and
        type-specific fields (``answer_key_position``, ``single_sided``,
        etc.).
    options:
        Optional overrides: ``dpi``, ``include_bleed``, ``color_profile``.

    Returns
    -------
    dict
        Structured manifest with page dimensions, ordered page list
        (front matter, content, blanks, back matter, answer keys),
        crop marks, and registration marks.
    """
    options = options or {}
    dpi = options.get("dpi", DPI)
    include_bleed = options.get("include_bleed", True)
    color_profile = options.get("color_profile", "CMYK")

    trim_size = book_data.get("trim_size", "8.5x11")
    trim_w, trim_h = _parse_trim_size(trim_size)

    bleed = BLEED_IN if include_bleed else 0.0
    full_w = trim_w + 2 * bleed
    full_h = trim_h + 2 * bleed

    pages_input = book_data.get("pages", [])

    # ----- Build ordered page list -----
    ordered_pages: list[dict[str, Any]] = []
    page_seq = 0

    # Front matter
    front_matter = book_data.get("front_matter", [])
    if not front_matter:
        # Default front matter: title page
        front_matter = [{"type": "title_page", "label": "Title Page"}]

    for fm in front_matter:
        page_seq += 1
        ordered_pages.append({
            "sequence": page_seq,
            "section": "front_matter",
            "type": fm.get("type", "front_matter"),
            "label": fm.get("label", f"Front Matter {page_seq}"),
            "content": fm.get("content"),
            "is_blank": False,
        })

    # Content pages
    single_sided = book_type == "coloring" or book_data.get("single_sided", False)
    coloring_margin_extra = 0.25 if book_type == "coloring" else 0.0

    for p in pages_input:
        page_seq += 1
        page_entry: dict[str, Any] = {
            "sequence": page_seq,
            "section": "content",
            "type": p.get("page_type", "content"),
            "page_number": p.get("page_number"),
            "label": p.get("label", f"Page {p.get('page_number', page_seq)}"),
            "image_url": p.get("image_url") or p.get("illustration_url"),
            "text_content": p.get("text_content"),
            "layout": p.get("layout"),
            "is_blank": False,
        }
        ordered_pages.append(page_entry)

        # Insert blank back for single-sided books (coloring)
        if single_sided:
            page_seq += 1
            ordered_pages.append({
                "sequence": page_seq,
                "section": "content",
                "type": "blank_back",
                "label": "Blank",
                "is_blank": True,
            })

    # Answer key section (puzzles)
    answer_key_position = book_data.get("answer_key_position", "back_of_book")
    answer_pages_data = book_data.get("answer_pages", [])
    if book_type == "puzzles" and answer_key_position != "none":
        # If no explicit answer pages provided, generate placeholders
        puzzle_count = book_data.get("puzzle_count", len(pages_input))
        if not answer_pages_data:
            answers_needed = max(1, math.ceil(puzzle_count / 4))
            answer_pages_data = [
                {"type": "answer_key", "label": f"Answer Key {i + 1}"}
                for i in range(answers_needed)
            ]

        # Insert answer key separator page
        page_seq += 1
        ordered_pages.append({
            "sequence": page_seq,
            "section": "answer_key",
            "type": "answer_key_header",
            "label": "Answer Key",
            "is_blank": False,
        })

        for ak in answer_pages_data:
            page_seq += 1
            ordered_pages.append({
                "sequence": page_seq,
                "section": "answer_key",
                "type": "answer_key",
                "label": ak.get("label", f"Answers {page_seq}"),
                "content": ak.get("content"),
                "is_blank": False,
            })

    # Back matter
    back_matter = book_data.get("back_matter", [])
    for bm in back_matter:
        page_seq += 1
        ordered_pages.append({
            "sequence": page_seq,
            "section": "back_matter",
            "type": bm.get("type", "back_matter"),
            "label": bm.get("label", f"Back Matter {page_seq}"),
            "content": bm.get("content"),
            "is_blank": False,
        })

    # ----- Margins -----
    if book_type == "coloring":
        margins = {
            "top_in": 0.5,
            "bottom_in": 0.5,
            "outer_in": 0.5,
            "inner_in": 0.75,  # +0.25in at spine for coloring safety
        }
    else:
        margins = {
            "top_in": 0.5,
            "bottom_in": 0.5,
            "outer_in": 0.5,
            "inner_in": 0.5,
        }

    # ----- Assemble manifest -----
    total_pages = len(ordered_pages)

    return {
        "manifest_id": str(uuid.uuid4()),
        "book_type": book_type,
        "generated_at": datetime.now(UTC).isoformat(),
        "format": "pdf",
        "color_profile": color_profile,
        "dpi": dpi,
        "dimensions": {
            "trim_width_in": trim_w,
            "trim_height_in": trim_h,
            "bleed_in": bleed,
            "full_width_in": round(full_w, 4),
            "full_height_in": round(full_h, 4),
            "full_width_px": _in_to_px(full_w, dpi),
            "full_height_px": _in_to_px(full_h, dpi),
        },
        "margins": margins,
        "single_sided": single_sided,
        "crop_marks": _crop_mark_positions(trim_w, trim_h, bleed) if include_bleed else [],
        "registration_marks": _registration_marks(full_w, full_h) if include_bleed else [],
        "pages": ordered_pages,
        "total_pages": total_pages,
        "page_counts": {
            "front_matter": sum(1 for p in ordered_pages if p["section"] == "front_matter"),
            "content": sum(1 for p in ordered_pages if p["section"] == "content" and not p["is_blank"]),
            "blank_backs": sum(1 for p in ordered_pages if p["is_blank"]),
            "answer_key": sum(1 for p in ordered_pages if p["section"] == "answer_key"),
            "back_matter": sum(1 for p in ordered_pages if p["section"] == "back_matter"),
        },
    }


# ---------------------------------------------------------------------------
# 2. generate_pdfx1a_manifest
# ---------------------------------------------------------------------------

def generate_pdfx1a_manifest(
    book_type: str,
    book_data: dict[str, Any],
) -> dict[str, Any]:
    """Build an IngramSpark-compatible PDF/X-1a manifest.

    Enforces CMYK-only color space and references the required ICC profile.

    Parameters
    ----------
    book_type:
        One of ``childrens``, ``coloring``, ``puzzles``.
    book_data:
        Book metadata dict (same as ``generate_pdf_manifest``).

    Returns
    -------
    dict
        PDF/X-1a manifest with ICC profile reference, output intent,
        and CMYK enforcement flags, wrapping the base PDF manifest.
    """
    # Generate the base manifest with CMYK forced
    base_manifest = generate_pdf_manifest(
        book_type,
        book_data,
        options={"include_bleed": True, "color_profile": "CMYK"},
    )

    trim_size = book_data.get("trim_size", "8.5x11")
    trim_w, trim_h = _parse_trim_size(trim_size)

    return {
        "manifest_id": str(uuid.uuid4()),
        "book_type": book_type,
        "generated_at": datetime.now(UTC).isoformat(),
        "pdf_standard": "PDF/X-1a:2001",
        "pdf_version": "1.3",
        "compliance": {
            "color_space": "CMYK",
            "rgb_objects_allowed": False,
            "spot_colors_allowed": False,
            "transparency_allowed": False,
            "icc_profile": ICC_PROFILE_GRACOL,
            "icc_profile_class": "output",
            "rendering_intent": "RelativeColorimetric",
        },
        "output_intent": {
            "type": "GTS_PDFX",
            "output_condition": "CGATS TR 006",
            "output_condition_identifier": "CGATS TR 006",
            "registry_name": "http://www.color.org",
            "info": "GRACoL2006 (ISO 12647-2:2004)",
            "icc_profile": ICC_PROFILE_GRACOL,
        },
        "trim_box": {
            "width_in": trim_w,
            "height_in": trim_h,
            "origin_x_in": BLEED_IN,
            "origin_y_in": BLEED_IN,
        },
        "bleed_box": {
            "width_in": round(trim_w + 2 * BLEED_IN, 4),
            "height_in": round(trim_h + 2 * BLEED_IN, 4),
            "origin_x_in": 0,
            "origin_y_in": 0,
        },
        "base_manifest": base_manifest,
    }


# ---------------------------------------------------------------------------
# 3. generate_png_pages
# ---------------------------------------------------------------------------

def generate_png_pages(
    book_type: str,
    book_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate a per-page PNG export manifest.

    Each entry describes a single page image at 300 DPI with proper
    dimensions and a deterministic storage path.

    Parameters
    ----------
    book_type:
        One of ``childrens``, ``coloring``, ``puzzles``.
    book_data:
        Book metadata dict.

    Returns
    -------
    list[dict]
        One dict per page with dimensions, DPI, and storage path.
    """
    trim_size = book_data.get("trim_size", "8.5x11")
    trim_w, trim_h = _parse_trim_size(trim_size)

    full_w = trim_w + 2 * BLEED_IN
    full_h = trim_h + 2 * BLEED_IN
    width_px = _in_to_px(full_w)
    height_px = _in_to_px(full_h)

    book_id = book_data.get("id", book_data.get("book_id", "unknown"))
    pages_input = book_data.get("pages", [])

    # Build full ordered page list via the PDF manifest for consistency
    pdf_manifest = generate_pdf_manifest(book_type, book_data)
    ordered_pages = pdf_manifest["pages"]

    result: list[dict[str, Any]] = []
    for page in ordered_pages:
        seq = page["sequence"]
        storage_path = (
            f"exports/{book_type}/{book_id}/pages/"
            f"page_{seq:04d}.png"
        )
        result.append({
            "sequence": seq,
            "section": page["section"],
            "type": page["type"],
            "label": page["label"],
            "is_blank": page["is_blank"],
            "dimensions": {
                "width_px": width_px,
                "height_px": height_px,
                "dpi": DPI,
            },
            "color_mode": "Grayscale" if book_type == "coloring" else "CMYK",
            "storage_path": storage_path,
            "source_image_url": page.get("image_url"),
        })

    return result


# ---------------------------------------------------------------------------
# 4. calculate_export_metadata
# ---------------------------------------------------------------------------

def calculate_export_metadata(
    book_type: str,
    book_data: dict[str, Any],
) -> dict[str, Any]:
    """Calculate comprehensive export metadata for a book.

    Computes total page count (including blanks, bonus, answer pages),
    file size estimate, print cost estimate, trim dimensions, and
    spine width.

    Parameters
    ----------
    book_type:
        One of ``childrens``, ``coloring``, ``puzzles``.
    book_data:
        Book metadata dict.

    Returns
    -------
    dict
        Export metadata with counts, estimates, and dimensions.
    """
    # Use the PDF manifest to get authoritative page counts
    pdf_manifest = generate_pdf_manifest(book_type, book_data)
    page_counts = pdf_manifest["page_counts"]
    total_pages = pdf_manifest["total_pages"]
    dims = pdf_manifest["dimensions"]

    # Spine width
    spine_width_in = round(total_pages * SPINE_WIDTH_PER_PAGE_IN, 4)

    # File size estimate
    per_page_mb = _FILE_SIZE_ESTIMATES_MB.get(book_type, 1.0)
    estimated_file_size_mb = round(total_pages * per_page_mb, 2)

    # Print cost estimate
    interior_type = book_data.get("interior_type", "bw")
    if book_type == "childrens":
        interior_type = "color"
    cost_per_page = _PRINT_COST_PER_PAGE.get(interior_type, _PRINT_COST_PER_PAGE["bw"])
    estimated_print_cost = round(_PRINT_COST_BASE + total_pages * cost_per_page, 2)

    return {
        "book_type": book_type,
        "total_pages": total_pages,
        "page_counts": page_counts,
        "dimensions": {
            "trim_width_in": dims["trim_width_in"],
            "trim_height_in": dims["trim_height_in"],
            "bleed_in": dims["bleed_in"],
            "spine_width_in": spine_width_in,
        },
        "estimates": {
            "file_size_mb": estimated_file_size_mb,
            "print_cost_usd": estimated_print_cost,
            "interior_type": interior_type,
        },
    }
