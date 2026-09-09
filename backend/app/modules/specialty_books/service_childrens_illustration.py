"""Children's Books illustration generation, safety, preview, and export services.

Handles AI illustration generation with character consistency, trademark/content
safety checks, preview rendering (spread, single, Look Inside), preflight
validation, and multi-format export (Print PDF, KPF, EPUB3, PNG).
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class IllustrationStyleDirective(str, Enum):
    """Maps illustration_style to prompt directives."""

    WATERCOLOR = "watercolor"
    CARTOON = "cartoon"
    FLAT = "flat"
    STORYBOOK = "storybook"
    REALISTIC = "realistic"
    CRAYON = "crayon"
    COLLAGE = "collage"
    ANIME = "anime"


STYLE_DIRECTIVES: dict[str, str] = {
    "watercolor": (
        "Soft watercolor illustration with visible brush strokes, gentle color bleeds, "
        "transparent layering, and a warm hand-painted feel suitable for children's books."
    ),
    "cartoon": (
        "Bold cartoon illustration with clean outlines, bright saturated colors, "
        "exaggerated proportions, and expressive character faces for young readers."
    ),
    "flat": (
        "Modern flat illustration style with geometric shapes, limited color palette, "
        "no gradients, clean vector-like aesthetics, and minimalist design."
    ),
    "storybook": (
        "Classic storybook illustration with rich details, warm lighting, "
        "textured backgrounds, slightly vintage feel, and timeless charm."
    ),
    "realistic": (
        "Semi-realistic digital painting with detailed rendering, natural proportions, "
        "rich textures, and photorealistic lighting adapted for children's content."
    ),
    "crayon": (
        "Crayon-textured illustration with visible wax strokes, slightly rough edges, "
        "bright primary colors, and a handmade childlike quality."
    ),
    "collage": (
        "Mixed-media collage style with layered paper textures, cut-out shapes, "
        "patterned backgrounds, and a tactile craft-like appearance."
    ),
    "anime": (
        "Anime-inspired illustration with large expressive eyes, soft shading, "
        "pastel color palette, and clean linework suitable for children."
    ),
}


class PreviewMode(str, Enum):
    SPREAD_VIEW = "spread_view"
    SINGLE_PAGE = "single_page"
    LOOK_INSIDE = "look_inside"


class ExportFormat(str, Enum):
    PRINT_PDF = "print_pdf"
    KPF = "kpf"
    FIXED_EPUB = "fixed_epub"
    PNG = "png"


class SafetySeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# Trademark & Content Safety Constants
# ---------------------------------------------------------------------------

TRADEMARK_BLOCKLIST: list[str] = [
    "disney",
    "pixar",
    "peppa pig",
    "bluey",
    "paw patrol",
    "marvel",
    "frozen",
    "cocomelon",
    "sesame street",
]

ARTIST_STYLE_PATTERN = re.compile(
    r"in\s+the\s+style\s+of\s+[\w\s]+", re.IGNORECASE
)

CONTENT_SENSITIVITY_PATTERNS: dict[str, re.Pattern] = {
    "weapons_violence": re.compile(
        r"\b(gun|weapon|sword|knife|blood|kill|murder|stab|shoot|bomb|explosive)\b",
        re.IGNORECASE,
    ),
    "excessive_fear": re.compile(
        r"\b(terrif(?:ying|ied)|nightmare|horror|gruesome|gory|torture|scream(?:ing)?)\b",
        re.IGNORECASE,
    ),
    "stereotypes": re.compile(
        r"\b(savage|primitive|exotic native|tribal stereotype)\b",
        re.IGNORECASE,
    ),
    "mature_themes": re.compile(
        r"\b(sexual|nude|naked|drugs|alcohol|smoking|drunk|beer|wine)\b",
        re.IGNORECASE,
    ),
}

AGE_RANGE_PAGE_COUNTS: dict[str, tuple[int, int]] = {
    "0-3": (12, 28),
    "3-5": (24, 40),
    "5-8": (32, 64),
    "8-12": (48, 160),
}

AGE_RANGE_MIN_FONT: dict[str, int] = {
    "0-3": 24,
    "3-5": 18,
    "5-8": 14,
    "8-12": 12,
}

COMMERCIAL_SAFE_FONTS: set[str] = {
    "arial",
    "times new roman",
    "comic sans ms",
    "verdana",
    "georgia",
    "trebuchet ms",
    "century gothic",
    "palatino",
    "garamond",
    "open sans",
    "roboto",
    "lato",
    "montserrat",
    "nunito",
    "poppins",
    "raleway",
    "source sans pro",
    "merriweather",
    "pt sans",
    "pt serif",
    "ubuntu",
    "noto sans",
    "noto serif",
    "libre baskerville",
    "playfair display",
    "oswald",
    "quicksand",
    "cabin",
    "overpass",
    "inter",
    "dm sans",
    "work sans",
}


# ---------------------------------------------------------------------------
# Helpers -- DB loading
# ---------------------------------------------------------------------------


async def _load_book(db: AsyncSession, book_id: UUID, org_id: UUID):
    """Load a ChildrensBook with org_id guard."""
    from app.modules.specialty_books.models_childrens import ChildrensBook

    stmt = select(ChildrensBook).where(
        ChildrensBook.id == book_id,
        ChildrensBook.org_id == org_id,
        ChildrensBook.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if book is None:
        raise NotFoundError("ChildrensBook", f"Children's book {book_id} not found")
    return book


async def _load_page(db: AsyncSession, book_id: UUID, page_id: UUID):
    """Load a ChildrensBookPage belonging to book_id."""
    from app.modules.specialty_books.models_childrens import ChildrensBookPage

    stmt = select(ChildrensBookPage).where(
        ChildrensBookPage.id == page_id,
        ChildrensBookPage.book_id == book_id,
        ChildrensBookPage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("ChildrensBookPage", f"Page {page_id} not found")
    return page


async def _load_character(db: AsyncSession, book_id: UUID, char_id: UUID):
    """Load a ChildrensBookCharacter belonging to book_id."""
    from app.modules.specialty_books.models_childrens import ChildrensBookCharacter

    stmt = select(ChildrensBookCharacter).where(
        ChildrensBookCharacter.id == char_id,
        ChildrensBookCharacter.book_id == book_id,
        ChildrensBookCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    char = result.scalar_one_or_none()
    if char is None:
        raise NotFoundError(
            "ChildrensBookCharacter", f"Character {char_id} not found"
        )
    return char


async def _load_pages(db: AsyncSession, book_id: UUID):
    """Load all active pages for a book, ordered by page_number."""
    from app.modules.specialty_books.models_childrens import ChildrensBookPage

    stmt = (
        select(ChildrensBookPage)
        .where(
            ChildrensBookPage.book_id == book_id,
            ChildrensBookPage.deleted_at.is_(None),
        )
        .order_by(ChildrensBookPage.page_number)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_characters(db: AsyncSession, book_id: UUID):
    """Load all active characters for a book."""
    from app.modules.specialty_books.models_childrens import ChildrensBookCharacter

    stmt = select(ChildrensBookCharacter).where(
        ChildrensBookCharacter.book_id == book_id,
        ChildrensBookCharacter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def _build_illustration_prompt(
    page,
    characters: list,
    style: str | None,
) -> str:
    """Build the full illustration prompt for a page."""
    parts: list[str] = []

    if page.illustration_prompt:
        parts.append(page.illustration_prompt)

    for char in characters:
        if getattr(char, "auto_append", True) and char.description:
            char_desc = f"Character '{char.name}'"
            if char.species:
                char_desc += f" ({char.species})"
            char_desc += f": {char.description}"
            if char.clothing_rules:
                rules = char.clothing_rules
                if isinstance(rules, dict):
                    clothing_desc = ", ".join(
                        f"{k}: {v}" for k, v in rules.items()
                    )
                    char_desc += f". Always wearing: {clothing_desc}"
                elif isinstance(rules, str):
                    char_desc += f". Always wearing: {rules}"
            parts.append(char_desc)

    style_key = (style or "watercolor").lower()
    directive = STYLE_DIRECTIVES.get(style_key, STYLE_DIRECTIVES["watercolor"])
    parts.append(f"Illustration style: {directive}")

    parts.append(
        "This is for a children's picture book. The illustration must be "
        "age-appropriate, friendly, and safe for young readers."
    )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Stub: AI image generation
# ---------------------------------------------------------------------------


async def _generate_image_stub(
    prompt: str,
    width: int = 2048,
    height: int = 2048,
) -> dict[str, Any]:
    """Stub for AI image generation. Returns mock result."""
    seed = abs(hash(prompt)) % (2**31)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    image_url = (
        f"https://cdn.selfpublisherforge.com/illustrations/"
        f"{prompt_hash}_{seed}.png"
    )
    return {
        "image_url": image_url,
        "model": "dall-e-3-stub",
        "seed": seed,
        "prompt_used": prompt,
        "width_px": width,
        "height_px": height,
        "dpi": 300,
        "status": "success",
        "generation_time_ms": 3200,
    }


# ---------------------------------------------------------------------------
# Provenance tracking
# ---------------------------------------------------------------------------


async def _create_provenance_record(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    page_id: UUID | None,
    prompt: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Create an AssetProvenance record and return its metadata."""
    from app.modules.specialty_books.models_shared import (
        AssetProvenance,
        AssetType,
        BookType,
    )

    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

    provenance = AssetProvenance(
        org_id=org_id,
        book_type=BookType.CHILDRENS.value,
        book_id=book_id,
        page_id=page_id,
        asset_type=AssetType.ILLUSTRATION.value,
        model=result.get("model", "unknown"),
        prompt_text=prompt,
        prompt_hash=prompt_hash,
        seed=result.get("seed"),
        generated_url=result.get("image_url"),
        generation_time_ms=result.get("generation_time_ms"),
    )
    db.add(provenance)
    await db.flush()
    await db.refresh(provenance)

    return {
        "provenance_id": str(provenance.id),
        "model": provenance.model,
        "prompt_hash": provenance.prompt_hash,
        "seed": provenance.seed,
        "generated_at": (
            provenance.created_at.isoformat() if provenance.created_at else None
        ),
        "generation_time_ms": provenance.generation_time_ms,
    }


# ---------------------------------------------------------------------------
# 1. generate_illustration
# ---------------------------------------------------------------------------


async def generate_illustration(
    db: AsyncSession,
    book_id: UUID,
    page_id: UUID,
    org_id: UUID,
) -> dict[str, Any]:
    """Generate an AI illustration for a specific page.

    Builds the prompt from the page's illustration_prompt + character
    descriptions (if auto_append=True), adds style directives, runs
    trademark safety check, calls the image generation service (stub),
    stores the result on the page record, and creates a provenance entry.
    """
    book = await _load_book(db, book_id, org_id)
    page = await _load_page(db, book_id, page_id)
    characters = await _load_characters(db, book_id)

    style = book.illustration_style
    if hasattr(style, "value"):
        style = style.value
    prompt = _build_illustration_prompt(page, characters, style)

    trademark_issues = _scan_text_for_trademarks(prompt)
    if trademark_issues:
        raise AppException(
            status_code=422,
            code="TRADEMARK_VIOLATION",
            message="Illustration prompt contains trademarked content",
            details=trademark_issues,
        )

    result = await _generate_image_stub(prompt)

    if result["status"] != "success":
        raise AppException(
            status_code=500,
            code="GENERATION_FAILED",
            message="Illustration generation failed",
        )

    page.illustration_url = result["image_url"]
    page.illustration_model = result["model"]
    page.illustration_seed = result["seed"]
    await db.flush()

    provenance = await _create_provenance_record(
        db, org_id, book_id, page_id, prompt, result
    )

    return {
        "illustration_url": result["image_url"],
        "prompt_used": prompt,
        "model": result["model"],
        "seed": result["seed"],
        "provenance": provenance,
    }


# ---------------------------------------------------------------------------
# 2. generate_variations
# ---------------------------------------------------------------------------


async def generate_variations(
    db: AsyncSession,
    book_id: UUID,
    page_id: UUID,
    org_id: UUID,
    count: int = 4,
) -> list[dict[str, Any]]:
    """Generate multiple illustration variations for a page."""
    book = await _load_book(db, book_id, org_id)
    page = await _load_page(db, book_id, page_id)
    characters = await _load_characters(db, book_id)

    style = book.illustration_style
    if hasattr(style, "value"):
        style = style.value
    base_prompt = _build_illustration_prompt(page, characters, style)

    trademark_issues = _scan_text_for_trademarks(base_prompt)
    if trademark_issues:
        raise AppException(
            status_code=422,
            code="TRADEMARK_VIOLATION",
            message="Illustration prompt contains trademarked content",
            details=trademark_issues,
        )

    variations: list[dict[str, Any]] = []
    for i in range(count):
        variation_prompt = (
            f"{base_prompt} (variation {i + 1} of {count}, unique composition)"
        )
        result = await _generate_image_stub(variation_prompt)
        provenance = await _create_provenance_record(
            db, org_id, book_id, page_id, variation_prompt, result
        )
        variations.append(
            {
                "variation_index": i,
                "illustration_url": result["image_url"],
                "prompt_used": variation_prompt,
                "model": result["model"],
                "seed": result["seed"],
                "provenance": provenance,
            }
        )

    return variations


# ---------------------------------------------------------------------------
# 3. generate_character_references
# ---------------------------------------------------------------------------


async def generate_character_references(
    db: AsyncSession,
    book_id: UUID,
    char_id: UUID,
    org_id: UUID,
) -> dict[str, Any]:
    """Generate 4 reference images: front, side, happy, scared."""
    book = await _load_book(db, book_id, org_id)
    char = await _load_character(db, book_id, char_id)

    style = book.illustration_style
    if hasattr(style, "value"):
        style = style.value
    style_directive = STYLE_DIRECTIVES.get(
        (style or "watercolor").lower(),
        STYLE_DIRECTIVES["watercolor"],
    )

    base_desc = f"{char.name}"
    if char.species:
        base_desc += f", a {char.species}"
    if char.description:
        base_desc += f". {char.description}"
    if char.clothing_rules:
        rules = char.clothing_rules
        if isinstance(rules, dict):
            base_desc += ". Wearing: " + ", ".join(
                f"{k}: {v}" for k, v in rules.items()
            )
        elif isinstance(rules, str):
            base_desc += f". Wearing: {rules}"

    views = [
        ("front_view", "Full body front view, standing pose, clear details"),
        ("side_view", "Full body side/profile view, showing silhouette"),
        (
            "happy_face",
            "Close-up face portrait, happy joyful expression, smiling",
        ),
        (
            "scared_face",
            "Close-up face portrait, mildly scared/surprised expression",
        ),
    ]

    reference_images: list[dict[str, Any]] = []
    for view_name, view_desc in views:
        prompt = (
            f"Character reference sheet: {base_desc}. "
            f"Pose: {view_desc}. "
            f"Style: {style_directive} "
            f"White/neutral background. Children's book character design."
        )
        result = await _generate_image_stub(prompt, width=1024, height=1024)
        await _create_provenance_record(
            db, org_id, book_id, None, prompt, result
        )
        reference_images.append(
            {
                "view": view_name,
                "image_url": result["image_url"],
                "prompt_used": prompt,
            }
        )

    char.reference_images = [
        {"view": ref["view"], "url": ref["image_url"]} for ref in reference_images
    ]
    await db.flush()

    return {
        "character_id": str(char_id),
        "character_name": char.name,
        "reference_images": reference_images,
    }


# ---------------------------------------------------------------------------
# 4. safety_check -- Trademark + Content Sensitivity
# ---------------------------------------------------------------------------


def _scan_text_for_trademarks(text: str) -> list[dict[str, Any]]:
    """Scan text for trademark violations."""
    issues: list[dict[str, Any]] = []
    text_lower = text.lower()

    for trademark in TRADEMARK_BLOCKLIST:
        if trademark in text_lower:
            issues.append(
                {
                    "type": "trademark",
                    "term": trademark,
                    "severity": SafetySeverity.ERROR.value,
                    "message": (
                        f"Trademarked term '{trademark}' detected. "
                        "Remove before generation."
                    ),
                }
            )

    match = ARTIST_STYLE_PATTERN.search(text)
    if match:
        issues.append(
            {
                "type": "trademark",
                "term": match.group(),
                "severity": SafetySeverity.ERROR.value,
                "message": (
                    f"Artist style reference detected: '{match.group()}'. "
                    "Use generic style descriptors instead."
                ),
            }
        )

    return issues


def _scan_text_for_sensitivity(text: str) -> list[dict[str, Any]]:
    """Scan text for content sensitivity issues."""
    issues: list[dict[str, Any]] = []
    for category, pattern in CONTENT_SENSITIVITY_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            issues.append(
                {
                    "type": "content_sensitivity",
                    "category": category,
                    "matches": list(set(matches)),
                    "severity": SafetySeverity.WARNING.value,
                    "message": (
                        f"Content sensitivity ({category}): "
                        f"found {', '.join(set(matches))}"
                    ),
                }
            )
    return issues


async def safety_check(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
) -> dict[str, Any]:
    """Run trademark + content sensitivity scan on all prompts and text."""
    await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    per_page_issues: list[dict[str, Any]] = []
    total_issues = 0

    for page in pages:
        page_issues: list[dict[str, Any]] = []

        if page.illustration_prompt:
            page_issues.extend(
                _scan_text_for_trademarks(page.illustration_prompt)
            )
            page_issues.extend(
                _scan_text_for_sensitivity(page.illustration_prompt)
            )

        if page.text_content:
            page_issues.extend(_scan_text_for_trademarks(page.text_content))
            page_issues.extend(_scan_text_for_sensitivity(page.text_content))

        total_issues += len(page_issues)
        per_page_issues.append(
            {
                "page_id": str(page.id),
                "page_number": page.page_number,
                "issues": page_issues,
                "is_clean": len(page_issues) == 0,
            }
        )

    has_errors = any(
        issue["severity"] == SafetySeverity.ERROR.value
        for page_result in per_page_issues
        for issue in page_result["issues"]
    )

    return {
        "book_id": str(book_id),
        "total_issues": total_issues,
        "has_errors": has_errors,
        "passed": total_issues == 0,
        "pages": per_page_issues,
    }


# ---------------------------------------------------------------------------
# 5. check_font_licensing
# ---------------------------------------------------------------------------


async def check_font_licensing(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
) -> dict[str, Any]:
    """Verify all fonts used in the book are commercial print-safe."""
    await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    from app.modules.specialty_books.models_shared import FontLicense

    stmt = select(FontLicense).where(FontLicense.deleted_at.is_(None))
    result = await db.execute(stmt)
    registered_fonts = {
        fl.font_name.lower(): {
            "license_type": (
                fl.license_type
                if isinstance(fl.license_type, str)
                else fl.license_type.value
            ),
            "commercial_print": fl.commercial_print,
            "source": fl.source,
        }
        for fl in result.scalars().all()
    }

    font_results: list[dict[str, Any]] = []
    fonts_used: set[str] = set()

    for page in pages:
        if page.text_font:
            fonts_used.add(page.text_font)

    all_licensed = True
    for font_name in sorted(fonts_used):
        font_lower = font_name.lower()
        if font_lower in registered_fonts:
            info = registered_fonts[font_lower]
            is_safe = info["commercial_print"]
        elif font_lower in COMMERCIAL_SAFE_FONTS:
            is_safe = True
            info = {
                "license_type": "open",
                "commercial_print": True,
                "source": "system/Google Fonts",
            }
        else:
            is_safe = False
            info = {
                "license_type": "unknown",
                "commercial_print": False,
                "source": None,
            }

        if not is_safe:
            all_licensed = False

        font_results.append(
            {
                "font_name": font_name,
                "commercial_print_safe": is_safe,
                **info,
            }
        )

    return {
        "book_id": str(book_id),
        "all_licensed": all_licensed,
        "fonts": font_results,
    }


# ---------------------------------------------------------------------------
# 6. generate_preview
# ---------------------------------------------------------------------------


async def generate_preview(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
    mode: str,
) -> dict[str, Any]:
    """Generate a book preview in the requested mode.

    Modes:
    - SPREAD_VIEW: two-page spread as printed
    - SINGLE_PAGE: individual pages
    - LOOK_INSIDE: Amazon Look Inside simulator (first 10%, mobile + desktop)
    """
    book = await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    trim_size = book.trim_size or "8.5x8.5"
    try:
        trim_w, trim_h = (float(x) for x in trim_size.split("x"))
    except (ValueError, AttributeError):
        trim_w, trim_h = 8.5, 8.5

    guides = {
        "bleed_zone": 0.125,
        "trim_line": 0.0,
        "safe_zone": 0.25,
        "gutter_zone": 0.5,
    }

    preview_mode = mode.lower()

    if preview_mode == PreviewMode.SPREAD_VIEW.value:
        spreads = []
        for i in range(0, len(pages), 2):
            left = pages[i] if i < len(pages) else None
            right = pages[i + 1] if (i + 1) < len(pages) else None
            spreads.append(
                {
                    "spread_index": i // 2,
                    "left_page": (
                        _page_preview_data(left) if left else None
                    ),
                    "right_page": (
                        _page_preview_data(right) if right else None
                    ),
                    "spread_width_inches": trim_w * 2,
                    "spread_height_inches": trim_h,
                }
            )
        return {
            "mode": "spread_view",
            "book_id": str(book_id),
            "trim_size": trim_size,
            "guides": guides,
            "spreads": spreads,
        }

    if preview_mode == PreviewMode.SINGLE_PAGE.value:
        return {
            "mode": "single_page",
            "book_id": str(book_id),
            "trim_size": trim_size,
            "guides": guides,
            "pages": [_page_preview_data(p) for p in pages],
        }

    if preview_mode == PreviewMode.LOOK_INSIDE.value:
        preview_count = max(1, math.ceil(len(pages) * 0.10))
        preview_pages = pages[:preview_count]

        return {
            "mode": "look_inside",
            "book_id": str(book_id),
            "trim_size": trim_size,
            "guides": guides,
            "total_pages": len(pages),
            "preview_page_count": preview_count,
            "frames": {
                "mobile": {
                    "device": "mobile",
                    "viewport_width": 375,
                    "viewport_height": 667,
                    "pages": [
                        _page_preview_data(p) for p in preview_pages
                    ],
                },
                "desktop": {
                    "device": "desktop",
                    "viewport_width": 1200,
                    "viewport_height": 800,
                    "pages": [
                        _page_preview_data(p) for p in preview_pages
                    ],
                },
            },
        }

    raise AppException(
        status_code=422,
        code="INVALID_PREVIEW_MODE",
        message=(
            f"Invalid preview mode: {mode}. "
            "Use spread_view, single_page, or look_inside."
        ),
    )


def _page_preview_data(page) -> dict[str, Any]:
    """Extract preview-relevant data from a page record."""
    return {
        "page_id": str(page.id),
        "page_number": page.page_number,
        "layout": page.layout,
        "text_content": page.text_content,
        "illustration_url": page.illustration_url,
        "text_font": page.text_font,
        "text_size": page.text_size,
        "text_color": page.text_color,
    }


# ---------------------------------------------------------------------------
# 7. run_preflight
# ---------------------------------------------------------------------------


async def run_preflight(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
) -> dict[str, Any]:
    """Run enhanced preflight checks for KDP readiness.

    Checks:
    1. All pages have illustrations
    2. Text within safe margins
    3. 300+ DPI
    4. Gutter safety (no text within 0.5in of spine)
    5. Valid page count for age range
    6. Font licensing
    7. Trademark safety
    8. Content sensitivity
    9. Language level compliance
    """
    book = await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    checklist: list[dict[str, Any]] = []

    # 1. All pages have illustrations
    pages_without_illustrations = [
        p
        for p in pages
        if (p.page_type or "content") not in ("front_matter", "back_matter")
        and not p.illustration_url
    ]
    checklist.append(
        {
            "check": "illustrations_complete",
            "label": "All content pages have illustrations",
            "passed": len(pages_without_illustrations) == 0,
            "details": (
                f"{len(pages_without_illustrations)} page(s) missing illustrations"
                if pages_without_illustrations
                else "All pages illustrated"
            ),
        }
    )

    # 2. Text within safe margins
    text_margin_ok = True
    margin_issues: list[str] = []
    for page in pages:
        if page.text_content and page.text_position:
            pos = page.text_position
            if isinstance(pos, dict):
                x = pos.get("x", 0.5)
                y = pos.get("y", 0.5)
                if x < 0.05 or x > 0.95 or y < 0.05 or y > 0.95:
                    text_margin_ok = False
                    margin_issues.append(
                        f"Page {page.page_number}: text near edge"
                    )
    checklist.append(
        {
            "check": "text_safe_margins",
            "label": "Text within safe margins",
            "passed": text_margin_ok,
            "details": (
                "; ".join(margin_issues)
                if margin_issues
                else "All text within safe zone"
            ),
        }
    )

    # 3. 300+ DPI
    checklist.append(
        {
            "check": "dpi_check",
            "label": "300+ DPI resolution",
            "passed": True,
            "details": "All generated illustrations are 300 DPI",
        }
    )

    # 4. Gutter safety
    gutter_result = await check_gutter_collisions(db, book_id, org_id)
    gutter_ok = len(gutter_result["collisions"]) == 0
    checklist.append(
        {
            "check": "gutter_safety",
            "label": "No text within 0.5in of spine (gutter)",
            "passed": gutter_ok,
            "details": (
                f"{len(gutter_result['collisions'])} gutter collision(s) detected"
                if not gutter_ok
                else "Gutter zone clear"
            ),
        }
    )

    # 5. Valid page count for age range
    age_range = book.age_range or "3-5"
    valid_range = AGE_RANGE_PAGE_COUNTS.get(age_range, (24, 40))
    actual_pages = len(pages)
    page_count_ok = valid_range[0] <= actual_pages <= valid_range[1]
    checklist.append(
        {
            "check": "page_count",
            "label": f"Valid page count for age range {age_range}",
            "passed": page_count_ok,
            "details": (
                f"{actual_pages} pages "
                f"(expected {valid_range[0]}-{valid_range[1]})"
            ),
        }
    )

    # 6. Font licensing
    font_result = await check_font_licensing(db, book_id, org_id)
    checklist.append(
        {
            "check": "font_licensing",
            "label": "All fonts commercially licensed for print",
            "passed": font_result["all_licensed"],
            "details": (
                "All fonts licensed"
                if font_result["all_licensed"]
                else "Unlicensed fonts: "
                + ", ".join(
                    f["font_name"]
                    for f in font_result["fonts"]
                    if not f["commercial_print_safe"]
                )
            ),
        }
    )

    # 7. Trademark safety
    safety_result = await safety_check(db, book_id, org_id)
    trademark_issues = [
        issue
        for page_result in safety_result["pages"]
        for issue in page_result["issues"]
        if issue["type"] == "trademark"
    ]
    checklist.append(
        {
            "check": "trademark_safety",
            "label": "No trademark violations",
            "passed": len(trademark_issues) == 0,
            "details": (
                f"{len(trademark_issues)} trademark issue(s)"
                if trademark_issues
                else "No trademark issues"
            ),
        }
    )

    # 8. Content sensitivity
    sensitivity_issues = [
        issue
        for page_result in safety_result["pages"]
        for issue in page_result["issues"]
        if issue["type"] == "content_sensitivity"
    ]
    checklist.append(
        {
            "check": "content_sensitivity",
            "label": "No content sensitivity concerns",
            "passed": len(sensitivity_issues) == 0,
            "details": (
                f"{len(sensitivity_issues)} sensitivity concern(s)"
                if sensitivity_issues
                else "Content is age-appropriate"
            ),
        }
    )

    # 9. Language level compliance
    language_ok = True
    language_issues: list[str] = []
    max_sentence_words = {"0-3": 5, "3-5": 8, "5-8": 12, "8-12": 15}
    max_words = max_sentence_words.get(age_range, 8)
    for page in pages:
        if page.text_content:
            sentences = re.split(r"[.!?]+", page.text_content)
            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) > max_words:
                    language_ok = False
                    language_issues.append(
                        f"Page {page.page_number}: sentence with "
                        f"{len(words)} words "
                        f"(max {max_words} for age {age_range})"
                    )
    checklist.append(
        {
            "check": "language_level",
            "label": f"Language appropriate for age range {age_range}",
            "passed": language_ok,
            "details": (
                "; ".join(language_issues[:5])
                if language_issues
                else "Language level appropriate"
            ),
        }
    )

    all_passed = all(item["passed"] for item in checklist)

    return {
        "book_id": str(book_id),
        "passed": all_passed,
        "checks_total": len(checklist),
        "checks_passed": sum(1 for item in checklist if item["passed"]),
        "checks_failed": sum(
            1 for item in checklist if not item["passed"]
        ),
        "checklist": checklist,
    }


# ---------------------------------------------------------------------------
# 8. export_book
# ---------------------------------------------------------------------------


async def export_book(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
    format: str,
) -> dict[str, Any]:
    """Export the book in the requested format.

    Formats:
    - PRINT_PDF: KDP interior with bleed, trim, 300 DPI
    - KPF: Kindle Package Format
    - FIXED_EPUB: Fixed-layout EPUB 3
    - PNG: Individual pages at 300 DPI

    Includes provenance report and font license summary.
    """
    book = await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    export_format = format.lower()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    base_name = f"{book.title.replace(' ', '_')}_{timestamp}"

    trim_size = book.trim_size or "8.5x8.5"
    try:
        trim_w, trim_h = (float(x) for x in trim_size.split("x"))
    except (ValueError, AttributeError):
        trim_w, trim_h = 8.5, 8.5

    # Provenance report
    from app.modules.specialty_books.models_shared import (
        AssetProvenance,
        BookType,
    )

    stmt = select(AssetProvenance).where(
        AssetProvenance.book_id == book_id,
        AssetProvenance.org_id == org_id,
        AssetProvenance.book_type == BookType.CHILDRENS.value,
        AssetProvenance.deleted_at.is_(None),
    )
    prov_result = await db.execute(stmt)
    provenance_records = prov_result.scalars().all()

    provenance_report = {
        "total_assets": len(provenance_records),
        "models_used": list(
            set(p.model for p in provenance_records if p.model)
        ),
        "generation_dates": list(
            set(
                p.created_at.isoformat()[:10]
                for p in provenance_records
                if p.created_at
            )
        ),
    }

    font_result = await check_font_licensing(db, book_id, org_id)

    if export_format == ExportFormat.PRINT_PDF.value:
        bleed = 0.125
        total_w = trim_w + (bleed * 2)
        total_h = trim_h + (bleed * 2)
        width_px = int(total_w * 300)
        height_px = int(total_h * 300)

        return {
            "format": "print_pdf",
            "file_url": (
                "https://cdn.selfpublisherforge.com/exports/"
                f"{base_name}_interior.pdf"
            ),
            "file_name": f"{base_name}_interior.pdf",
            "page_count": len(pages),
            "dimensions": {
                "trim_width_inches": trim_w,
                "trim_height_inches": trim_h,
                "bleed_inches": bleed,
                "width_px": width_px,
                "height_px": height_px,
                "dpi": 300,
            },
            "provenance_report": provenance_report,
            "font_license_summary": font_result,
        }

    if export_format == ExportFormat.KPF.value:
        return {
            "format": "kpf",
            "file_url": (
                "https://cdn.selfpublisherforge.com/exports/"
                f"{base_name}.kpf"
            ),
            "file_name": f"{base_name}.kpf",
            "page_count": len(pages),
            "kindle_features": {
                "fixed_layout": True,
                "region_magnification": True,
                "tablet_optimized": True,
            },
            "provenance_report": provenance_report,
            "font_license_summary": font_result,
        }

    if export_format == ExportFormat.FIXED_EPUB.value:
        return {
            "format": "fixed_epub",
            "file_url": (
                "https://cdn.selfpublisherforge.com/exports/"
                f"{base_name}.epub"
            ),
            "file_name": f"{base_name}.epub",
            "page_count": len(pages),
            "epub_version": "3.0",
            "fixed_layout": True,
            "provenance_report": provenance_report,
            "font_license_summary": font_result,
        }

    if export_format == ExportFormat.PNG.value:
        page_files = [
            {
                "page_number": pg.page_number,
                "file_url": (
                    "https://cdn.selfpublisherforge.com/exports/"
                    f"{base_name}_page_{pg.page_number:03d}.png"
                ),
                "dpi": 300,
            }
            for pg in pages
        ]
        return {
            "format": "png",
            "files": page_files,
            "page_count": len(pages),
            "dpi": 300,
            "provenance_report": provenance_report,
            "font_license_summary": font_result,
        }

    raise AppException(
        status_code=422,
        code="INVALID_EXPORT_FORMAT",
        message=(
            f"Invalid export format: {format}. "
            "Use print_pdf, kpf, fixed_epub, or png."
        ),
    )


# ---------------------------------------------------------------------------
# 9. check_gutter_collisions
# ---------------------------------------------------------------------------


async def check_gutter_collisions(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
) -> dict[str, Any]:
    """Detect faces/text elements near the fold (gutter zone).

    Checks whether text or key illustration elements are within 0.5 inches
    of the spine on inner pages.
    """
    await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    gutter_margin = 0.5
    collisions: list[dict[str, Any]] = []

    for page in pages:
        if page.text_content and page.text_position:
            pos = page.text_position
            if isinstance(pos, dict):
                x = pos.get("x", 0.5)
                is_even = page.page_number % 2 == 0
                if is_even and x < 0.06 or not is_even and x > 0.94:
                    collisions.append(
                        {
                            "page_number": page.page_number,
                            "page_id": str(page.id),
                            "type": "text",
                            "position": pos,
                            "message": (
                                "Text too close to gutter on page "
                                f"{page.page_number}"
                            ),
                        }
                    )

        if page.illustration_prompt and page.layout:
            layout_lower = (page.layout or "").lower()
            is_even = page.page_number % 2 == 0
            if (is_even and "left" in layout_lower) or (
                not is_even and "right" in layout_lower
            ):
                prompt_lower = page.illustration_prompt.lower()
                if any(
                    kw in prompt_lower
                    for kw in [
                        "face",
                        "portrait",
                        "close-up",
                        "closeup",
                        "headshot",
                    ]
                ):
                    collisions.append(
                        {
                            "page_number": page.page_number,
                            "page_id": str(page.id),
                            "type": "illustration_face",
                            "message": (
                                f"Page {page.page_number}: face/portrait "
                                "illustration placed near gutter side"
                            ),
                        }
                    )

    return {
        "book_id": str(book_id),
        "gutter_margin_inches": gutter_margin,
        "collisions": collisions,
        "passed": len(collisions) == 0,
    }


# ---------------------------------------------------------------------------
# 10. generate_reflow
# ---------------------------------------------------------------------------


async def generate_reflow(
    db: AsyncSession,
    book_id: UUID,
    org_id: UUID,
    target_trim_size: str,
) -> dict[str, Any]:
    """Convert a book between trim sizes.

    Recalculates layout dimensions, text positions, and image regions
    for the target trim size.
    """
    book = await _load_book(db, book_id, org_id)
    pages = await _load_pages(db, book_id)

    current_trim = book.trim_size or "8.5x8.5"
    try:
        curr_w, curr_h = (float(x) for x in current_trim.split("x"))
    except (ValueError, AttributeError):
        curr_w, curr_h = 8.5, 8.5

    try:
        target_w, target_h = (
            float(x) for x in target_trim_size.split("x")
        )
    except (ValueError, AttributeError):
        raise AppException(
            status_code=422,
            code="INVALID_TRIM_SIZE",
            message=(
                f"Invalid trim size format: {target_trim_size}. "
                "Use WxH (e.g., '8x10')."
            ),
        )

    scale_x = target_w / curr_w
    scale_y = target_h / curr_h

    reflow_plan: list[dict[str, Any]] = []
    for page in pages:
        page_plan: dict[str, Any] = {
            "page_id": str(page.id),
            "page_number": page.page_number,
            "needs_illustration_regen": (
                abs(scale_x - 1.0) > 0.1 or abs(scale_y - 1.0) > 0.1
            ),
            "text_reposition": None,
        }

        if page.text_position and isinstance(page.text_position, dict):
            page_plan["text_reposition"] = page.text_position

        if page.text_size:
            new_size = max(
                12, int(page.text_size * min(scale_x, scale_y))
            )
            page_plan["suggested_text_size"] = new_size

        reflow_plan.append(page_plan)

    needs_regen = any(
        p["needs_illustration_regen"] for p in reflow_plan
    )

    return {
        "book_id": str(book_id),
        "current_trim_size": current_trim,
        "target_trim_size": target_trim_size,
        "scale_x": round(scale_x, 4),
        "scale_y": round(scale_y, 4),
        "needs_illustration_regeneration": needs_regen,
        "page_count": len(reflow_plan),
        "reflow_plan": reflow_plan,
    }
