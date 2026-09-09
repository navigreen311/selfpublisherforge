"""Validation rule definitions for KDP submission requirements.

Contains trim sizes, margin specs, bleed requirements, spine calculations,
file format rules, and all KDP-specific constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PaperType(str, Enum):
    WHITE = "white"
    CREAM = "cream"


class ColorMode(str, Enum):
    CMYK = "cmyk"
    RGB = "rgb"


class BookFormat(str, Enum):
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    EBOOK = "ebook"


class CoverType(str, Enum):
    PRINT = "print"
    EBOOK = "ebook"


# ---------------------------------------------------------------------------
# Trim-size definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrimSize:
    """KDP trim size with associated margin requirements (inches)."""

    width: float
    height: float
    min_inside_margin: float
    min_outside_margin: float
    min_top_margin: float
    min_bottom_margin: float
    label: str = ""


# Official KDP trim sizes with minimum margin requirements.
# Inside margins scale with page count; these are base minimums.
TRIM_SIZES: dict[str, TrimSize] = {
    "5x8": TrimSize(
        width=5.0,
        height=8.0,
        min_inside_margin=0.375,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='5" x 8"',
    ),
    "5.06x7.81": TrimSize(
        width=5.06,
        height=7.81,
        min_inside_margin=0.375,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='5.06" x 7.81"',
    ),
    "5.25x8": TrimSize(
        width=5.25,
        height=8.0,
        min_inside_margin=0.375,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='5.25" x 8"',
    ),
    "5.5x8.5": TrimSize(
        width=5.5,
        height=8.5,
        min_inside_margin=0.375,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='5.5" x 8.5"',
    ),
    "6x9": TrimSize(
        width=6.0,
        height=9.0,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='6" x 9"',
    ),
    "6.14x9.21": TrimSize(
        width=6.14,
        height=9.21,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='6.14" x 9.21"',
    ),
    "6.69x9.61": TrimSize(
        width=6.69,
        height=9.61,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='6.69" x 9.61"',
    ),
    "7x10": TrimSize(
        width=7.0,
        height=10.0,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='7" x 10"',
    ),
    "7.44x9.69": TrimSize(
        width=7.44,
        height=9.69,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='7.44" x 9.69"',
    ),
    "7.5x9.25": TrimSize(
        width=7.5,
        height=9.25,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='7.5" x 9.25"',
    ),
    "8x10": TrimSize(
        width=8.0,
        height=10.0,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='8" x 10"',
    ),
    "8.5x11": TrimSize(
        width=8.5,
        height=11.0,
        min_inside_margin=0.5,
        min_outside_margin=0.25,
        min_top_margin=0.25,
        min_bottom_margin=0.25,
        label='8.5" x 11"',
    ),
}


# ---------------------------------------------------------------------------
# Inside margin page-count scaling (KDP rules)
# ---------------------------------------------------------------------------


def get_inside_margin(base_margin: float, page_count: int) -> float:
    """Return the required inside (gutter) margin based on page count.

    KDP requires larger inside margins for thicker books so the text
    is not swallowed by the binding.
    """
    if page_count <= 150:
        return base_margin
    if page_count <= 300:
        return base_margin + 0.125
    if page_count <= 500:
        return base_margin + 0.25
    return base_margin + 0.375


# ---------------------------------------------------------------------------
# Bleed
# ---------------------------------------------------------------------------

BLEED_SIZE: float = 0.125  # inches on each side for full-bleed covers/interiors


# ---------------------------------------------------------------------------
# Spine width calculation
# ---------------------------------------------------------------------------

# Thickness per page (in inches) by paper type
PAGE_THICKNESS: dict[PaperType, float] = {
    PaperType.WHITE: 0.002252,
    PaperType.CREAM: 0.0025,
}


def calculate_spine_width(page_count: int, paper_type: PaperType) -> float:
    """Calculate spine width in inches given page count and paper type."""
    thickness = PAGE_THICKNESS.get(paper_type, PAGE_THICKNESS[PaperType.WHITE])
    return round(page_count * thickness, 4)


# ---------------------------------------------------------------------------
# Page count limits
# ---------------------------------------------------------------------------

MIN_PAGE_COUNT: int = 24
MAX_PAGE_COUNT_WHITE: int = 828
MAX_PAGE_COUNT_CREAM: int = 828


def get_max_page_count(paper_type: PaperType) -> int:
    if paper_type == PaperType.CREAM:
        return MAX_PAGE_COUNT_CREAM
    return MAX_PAGE_COUNT_WHITE


# ---------------------------------------------------------------------------
# Image / DPI rules
# ---------------------------------------------------------------------------

MIN_PRINT_DPI: int = 300
MIN_EBOOK_DPI: int = 72
MAX_EBOOK_IMAGE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

ALLOWED_EBOOK_IMAGE_FORMATS: set[str] = {"JPEG", "JPG", "PNG"}
ALLOWED_PRINT_COVER_FORMATS: set[str] = {"TIFF", "PNG"}
ALLOWED_EBOOK_COVER_FORMATS: set[str] = {"JPEG", "JPG"}


# ---------------------------------------------------------------------------
# Cover dimension rules
# ---------------------------------------------------------------------------


def expected_print_cover_width(trim_width: float, spine_width: float) -> float:
    """Full wrap cover width = front + spine + back + bleed on both edges."""
    return (trim_width * 2) + spine_width + (BLEED_SIZE * 2)


def expected_print_cover_height(trim_height: float) -> float:
    """Full cover height = trim height + bleed top & bottom."""
    return trim_height + (BLEED_SIZE * 2)


COVER_DIMENSION_TOLERANCE: float = 0.03  # inches tolerance


# ---------------------------------------------------------------------------
# Safe zone – text should not be in this area (measured from trim edge)
# ---------------------------------------------------------------------------

SAFE_ZONE_INCHES: float = 0.125


# ---------------------------------------------------------------------------
# Color-space rules
# ---------------------------------------------------------------------------

COVER_COLOR_SPACE: str = "CMYK"
INTERIOR_COLOR_SPACE: str = "RGB"


# ---------------------------------------------------------------------------
# Ebook constraints
# ---------------------------------------------------------------------------

MAX_EBOOK_FILE_SIZE_BYTES: int = 650 * 1024 * 1024  # 650 MB
RECOMMENDED_MIN_FONT_SIZE_PT: float = 7.0

DISALLOWED_EBOOK_ELEMENTS: list[str] = [
    "javascript",
    "<script",
    "external stylesheet",
]


# ---------------------------------------------------------------------------
# Compliance / policy rules
# ---------------------------------------------------------------------------


@dataclass
class ComplianceRule:
    pattern: str
    description: str
    severity: str = "error"  # error | warning


TRADEMARK_PATTERNS: list[ComplianceRule] = [
    ComplianceRule(
        pattern=r"\bkindle\s+unlimited\b",
        description="'Kindle Unlimited' is a trademarked term and cannot appear in titles/subtitles",
    ),
    ComplianceRule(
        pattern=r"\bkindle\s+edition\b",
        description="'Kindle Edition' is auto-applied by Amazon; do not include in title",
    ),
    ComplianceRule(
        pattern=r"\bamazon\s+bestseller\b",
        description="Claiming 'Amazon Bestseller' in title/subtitle requires verification",
        severity="warning",
    ),
    ComplianceRule(
        pattern=r"#1\s+best\s*seller",
        description="Claiming '#1 Bestseller' in title/subtitle may violate policy",
        severity="warning",
    ),
    ComplianceRule(
        pattern=r"\bkindle\b",
        description="The word 'Kindle' is trademarked; avoid in titles unless referencing the device contextually",
        severity="warning",
    ),
]

CONTENT_POLICY_PATTERNS: list[ComplianceRule] = [
    ComplianceRule(
        pattern=r"\bpublic\s+domain\b.*\boriginal\b",
        description="Claiming public-domain work as original may violate content policy",
        severity="warning",
    ),
]

DESCRIPTION_DISALLOWED_HTML: list[str] = [
    "<script",
    "<iframe",
    "<form",
    "<input",
    "<style",
    "javascript:",
    "onclick",
    "onerror",
    "onload",
]

DESCRIPTION_ALLOWED_HTML_TAGS: set[str] = {
    "b",
    "i",
    "u",
    "br",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ol",
    "ul",
    "li",
    "em",
    "strong",
    "a",
}
