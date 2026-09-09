"""Print Production Preflight v2 for Specialty Books.

Runs comprehensive pre-export validation covering DPI, margins, bleed,
gutter safety, spine width, page count, font licensing, trademark safety,
content sensitivity, language level (children's), and grayscale verification.

Usage::

    report = run_preflight("childrens", book_data)
    if not report["passed"]:
        for blocker in report["blockers"]:
            print(blocker["name"], blocker["details"])
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Spine width multipliers (inches per page)
SPINE_WIDTH_PER_PAGE_BW = 0.0025
SPINE_WIDTH_PER_PAGE_COLOR = 0.002252

# Minimum DPI for print-ready output
MIN_DPI = 300

# Minimum bleed margin (inches)
MIN_BLEED_MARGIN = 0.125

# Gutter safety zone – no content within this distance of the spine (inches)
GUTTER_SAFETY_INCHES = 0.5

# KDP page-count limits (paperback)
KDP_MIN_PAGES = 24
KDP_MAX_PAGES = 828

# Maximum total ink density for CMYK printing
MAX_INK_DENSITY_PERCENT = 300

# Trademarked terms that must not appear in prompts or text
_TRADEMARK_BLOCKLIST: list[str] = [
    "disney",
    "pixar",
    "peppa pig",
    "bluey",
    "paw patrol",
    "marvel",
    "frozen",
    "cocomelon",
    "sesame street",
    "pokemon",
    "pokémon",
    "hello kitty",
    "spongebob",
    "barbie",
    "lego",
    "transformers",
    "harry potter",
    "winnie the pooh",
    "mickey mouse",
    "spider-man",
    "spiderman",
    "batman",
    "superman",
    "in the style of",
]

# Words / patterns flagged during content sensitivity checks
_SENSITIVITY_PATTERNS: list[str] = [
    r"\bgun\b",
    r"\bknife\b",
    r"\bknives\b",
    r"\bweapon\b",
    r"\bkill(?:ed|ing|s)?\b",
    r"\bblood\b",
    r"\bdeath\b",
    r"\bdie[ds]?\b",
    r"\bviolence\b",
    r"\bnaked\b",
    r"\bnude\b",
    r"\bdrug\b",
    r"\balcohol\b",
    r"\bcigarette\b",
    r"\bsmoking\b",
]

# Children's age-band language limits (max sentence words)
_LANGUAGE_LIMITS: dict[str, dict[str, Any]] = {
    "board": {"max_sentence_words": 5, "max_word_length": 5},
    "picture": {"max_sentence_words": 8, "max_word_length": 7},
    "early_reader": {"max_sentence_words": 12, "max_word_length": 9},
    "chapter": {"max_sentence_words": 15, "max_word_length": None},
}

# Severity levels
SEVERITY_BLOCKER = "blocker"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class PreflightCheck:
    """Result of a single preflight check."""

    name: str
    status: str  # "passed" | "failed" | "warning"
    details: str
    severity: str = SEVERITY_INFO  # "blocker" | "warning" | "info"

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "severity": self.severity,
        }


@dataclass
class PreflightReport:
    """Aggregated preflight report."""

    passed: bool = True
    checks: list[PreflightCheck] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)
    blockers: list[dict[str, str]] = field(default_factory=list)
    look_inside_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [c.to_dict() for c in self.checks],
            "warnings": self.warnings,
            "blockers": self.blockers,
            "look_inside_data": self.look_inside_data,
        }


# ---------------------------------------------------------------------------
# Internal check helpers
# ---------------------------------------------------------------------------


def _add_check(report: PreflightReport, check: PreflightCheck) -> None:
    """Append *check* and update report-level aggregation."""
    report.checks.append(check)
    if check.status == "failed":
        entry = {"name": check.name, "details": check.details}
        if check.severity == SEVERITY_BLOCKER:
            report.blockers.append(entry)
            report.passed = False
        else:
            report.warnings.append(entry)
    elif check.status == "warning":
        report.warnings.append({"name": check.name, "details": check.details})


def _check_dpi(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Verify all pages meet minimum DPI."""
    pages = book_data.get("pages", [])
    low_dpi_pages: list[int] = []
    for page in pages:
        dpi = page.get("dpi", MIN_DPI)
        if dpi < MIN_DPI:
            low_dpi_pages.append(page.get("page_number", 0))

    if low_dpi_pages:
        _add_check(
            report,
            PreflightCheck(
                name="dpi_check",
                status="failed",
                details=f"Pages with DPI below {MIN_DPI}: {low_dpi_pages}",
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="dpi_check",
                status="passed",
                details=f"All pages meet minimum {MIN_DPI} DPI requirement.",
            ),
        )


def _check_margins(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Verify bleed margins are at least MIN_BLEED_MARGIN inches."""
    pages = book_data.get("pages", [])
    bad_pages: list[int] = []
    for page in pages:
        margins = page.get("margins", {})
        for side in ("top", "bottom", "left", "right"):
            margin_val = margins.get(side, MIN_BLEED_MARGIN)
            if margin_val < MIN_BLEED_MARGIN:
                bad_pages.append(page.get("page_number", 0))
                break

    if bad_pages:
        _add_check(
            report,
            PreflightCheck(
                name="margin_bleed_check",
                status="failed",
                details=(f"Pages with margins below {MIN_BLEED_MARGIN}in bleed: " f"{bad_pages}"),
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="margin_bleed_check",
                status="passed",
                details=f"All pages have at least {MIN_BLEED_MARGIN}in bleed margins.",
            ),
        )


def _check_gutter_safety(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Ensure no content falls within GUTTER_SAFETY_INCHES of the spine."""
    pages = book_data.get("pages", [])
    violations: list[int] = []
    for page in pages:
        gutter_clearance = page.get("gutter_clearance_inches")
        if gutter_clearance is not None and gutter_clearance < GUTTER_SAFETY_INCHES:
            violations.append(page.get("page_number", 0))

    if violations:
        _add_check(
            report,
            PreflightCheck(
                name="gutter_safety_check",
                status="failed",
                details=(f"Content within {GUTTER_SAFETY_INCHES}in of spine on pages: " f"{violations}"),
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="gutter_safety_check",
                status="passed",
                details=f"No content within {GUTTER_SAFETY_INCHES}in of the spine.",
            ),
        )


def calculate_spine_width(page_count: int, interior_type: str = "bw") -> float:
    """Calculate spine width in inches.

    Parameters
    ----------
    page_count:
        Total interior page count.
    interior_type:
        ``"bw"`` for black-and-white or ``"color"``/``"premium_color"``
        /``"standard_color"`` for colour interiors.

    Returns
    -------
    Spine width in inches, rounded to 4 decimal places.
    """
    if interior_type in ("color", "premium_color", "standard_color"):
        multiplier = SPINE_WIDTH_PER_PAGE_COLOR
    else:
        multiplier = SPINE_WIDTH_PER_PAGE_BW
    return round(page_count * multiplier, 4)


def _check_spine_width(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Calculate and report spine width."""
    page_count = book_data.get("page_count", 0)
    interior_type = book_data.get("interior_type", "bw")
    spine = calculate_spine_width(page_count, interior_type)
    _add_check(
        report,
        PreflightCheck(
            name="spine_width_calculation",
            status="passed",
            details=f"Spine width: {spine}in ({page_count} pages, {interior_type} interior).",
        ),
    )


def _check_page_count(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Validate page count (must be even and within KDP limits)."""
    page_count = book_data.get("page_count", 0)
    issues: list[str] = []

    if page_count % 2 != 0:
        issues.append(f"Page count ({page_count}) must be a multiple of 2.")

    if page_count < KDP_MIN_PAGES:
        issues.append(f"Page count ({page_count}) is below KDP minimum of {KDP_MIN_PAGES}.")

    if page_count > KDP_MAX_PAGES:
        issues.append(f"Page count ({page_count}) exceeds KDP maximum of {KDP_MAX_PAGES}.")

    if issues:
        _add_check(
            report,
            PreflightCheck(
                name="page_count_check",
                status="failed",
                details=" ".join(issues),
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="page_count_check",
                status="passed",
                details=f"Page count ({page_count}) is valid for KDP.",
            ),
        )


def _check_font_licensing(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Verify all fonts are cleared for commercial print use."""
    fonts = book_data.get("fonts", [])
    if not fonts:
        _add_check(
            report,
            PreflightCheck(
                name="font_licensing_check",
                status="warning",
                details="No font information provided. Verify fonts are print-safe.",
                severity=SEVERITY_WARNING,
            ),
        )
        return

    unsafe_fonts: list[str] = []
    for font in fonts:
        if isinstance(font, dict):
            if not font.get("commercial_print", False):
                unsafe_fonts.append(font.get("name", "Unknown"))
        elif isinstance(font, str):
            # String-only entries are assumed unchecked
            unsafe_fonts.append(font)

    if unsafe_fonts:
        _add_check(
            report,
            PreflightCheck(
                name="font_licensing_check",
                status="failed",
                details=f"Fonts not cleared for commercial print: {unsafe_fonts}",
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="font_licensing_check",
                status="passed",
                details="All fonts are cleared for commercial print use.",
            ),
        )


def _check_trademark_safety(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Scan text and prompts for trademarked terms."""
    text_fields: list[str] = []

    # Gather all text content
    for page in book_data.get("pages", []):
        if page.get("text_content"):
            text_fields.append(page["text_content"])
        if page.get("illustration_prompt"):
            text_fields.append(page["illustration_prompt"])

    # Also check title, subtitle, description
    for key in ("title", "subtitle", "description"):
        val = book_data.get(key)
        if val:
            text_fields.append(val)

    combined = " ".join(text_fields).lower()
    found: list[str] = [term for term in _TRADEMARK_BLOCKLIST if term in combined]

    if found:
        _add_check(
            report,
            PreflightCheck(
                name="trademark_safety_check",
                status="failed",
                details=f"Trademarked terms detected: {found}",
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="trademark_safety_check",
                status="passed",
                details="No trademarked terms detected in text or prompts.",
            ),
        )


def _check_content_sensitivity(book_data: dict[str, Any], report: PreflightReport) -> None:
    """Flag potentially inappropriate content for the target audience."""
    text_fields: list[str] = []
    for page in book_data.get("pages", []):
        if page.get("text_content"):
            text_fields.append(page["text_content"])

    for key in ("title", "subtitle", "description"):
        val = book_data.get(key)
        if val:
            text_fields.append(val)

    combined = " ".join(text_fields)
    flagged: list[str] = []
    for pattern in _SENSITIVITY_PATTERNS:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        if matches:
            flagged.extend(matches)

    if flagged:
        _add_check(
            report,
            PreflightCheck(
                name="content_sensitivity_check",
                status="warning",
                details=f"Potentially sensitive terms found: {list(set(flagged))}",
                severity=SEVERITY_WARNING,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="content_sensitivity_check",
                status="passed",
                details="No sensitive content flags raised.",
            ),
        )


def _check_language_level(book_data: dict[str, Any], report: PreflightReport) -> None:
    """For children's books, verify text meets age-band language rules."""
    age_range = book_data.get("age_range")
    if not age_range:
        return  # Not a children's book or age range not set

    rules = _LANGUAGE_LIMITS.get(age_range)
    if not rules:
        return

    pages = book_data.get("pages", [])
    violations: list[str] = []
    word_re = re.compile(r"[a-zA-Z'\u2019]+")
    sentence_re = re.compile(r"[.!?]+")

    for page in pages:
        text = page.get("text_content", "")
        if not text:
            continue
        page_num = page.get("page_number", "?")
        sentences = [s.strip() for s in sentence_re.split(text) if s.strip()]
        for sentence in sentences:
            words = word_re.findall(sentence)
            max_sw = rules["max_sentence_words"]
            if max_sw and len(words) > max_sw:
                violations.append(
                    f"Page {page_num}: sentence with {len(words)} words " f"(max {max_sw} for {age_range})"
                )
            max_wl = rules["max_word_length"]
            if max_wl:
                for word in words:
                    if len(word) > max_wl:
                        violations.append(
                            f"Page {page_num}: word '{word}' has {len(word)} " f"letters (max {max_wl} for {age_range})"
                        )

    if violations:
        _add_check(
            report,
            PreflightCheck(
                name="language_level_check",
                status="warning",
                details=(
                    f"{len(violations)} language-level violation(s) for "
                    f"age range '{age_range}'. First 5: " + "; ".join(violations[:5])
                ),
                severity=SEVERITY_WARNING,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="language_level_check",
                status="passed",
                details=f"Text meets language requirements for age range '{age_range}'.",
            ),
        )


def _check_grayscale(book_data: dict[str, Any], report: PreflightReport) -> None:
    """For B&W books, flag any pages that contain color pixels."""
    interior_type = book_data.get("interior_type", "bw")
    if interior_type not in ("bw", "black_white", "grayscale"):
        return  # Only relevant for B&W interiors

    pages = book_data.get("pages", [])
    color_pages: list[int] = []
    for page in pages:
        if page.get("has_color_pixels", False):
            color_pages.append(page.get("page_number", 0))

    if color_pages:
        _add_check(
            report,
            PreflightCheck(
                name="grayscale_verification",
                status="failed",
                details=(
                    f"Color pixels detected in B&W interior on pages: {color_pages}. "
                    "Convert to grayscale before export."
                ),
                severity=SEVERITY_BLOCKER,
            ),
        )
    else:
        _add_check(
            report,
            PreflightCheck(
                name="grayscale_verification",
                status="passed",
                details="All pages verified as grayscale for B&W interior.",
            ),
        )


# ---------------------------------------------------------------------------
# Look Inside Simulator Data
# ---------------------------------------------------------------------------


def _extract_look_inside_data(book_data: dict[str, Any]) -> dict[str, Any]:
    """Extract data for the first ~10% of pages (Amazon Look Inside preview).

    Returns summary info about the preview pages: count, text excerpts,
    whether illustrations are present, and a basic hook-strength indicator.
    """
    pages = book_data.get("pages", [])
    if not pages:
        return {"preview_page_count": 0, "pages": [], "hook_score": 0}

    preview_count = max(1, math.ceil(len(pages) * 0.10))
    preview_pages = sorted(pages, key=lambda p: p.get("page_number", 0))[:preview_count]

    preview_info: list[dict[str, Any]] = []
    for page in preview_pages:
        preview_info.append(
            {
                "page_number": page.get("page_number"),
                "has_illustration": bool(page.get("illustration_url")),
                "text_excerpt": (page.get("text_content", "") or "")[:200],
                "layout": page.get("layout"),
            }
        )

    # Simple hook score heuristic
    hook_score = 50.0
    if preview_pages:
        first_text = (preview_pages[0].get("text_content", "") or "").strip()
        if first_text.endswith("?"):
            hook_score += 15.0
        if "!" in first_text:
            hook_score += 10.0
        if preview_pages[0].get("illustration_url"):
            hook_score += 10.0
        # Cliffhanger at boundary
        last_text = (preview_pages[-1].get("text_content", "") or "").strip()
        if last_text.endswith(("?", "...", "\u2026")):
            hook_score += 15.0

    return {
        "preview_page_count": preview_count,
        "total_pages": len(pages),
        "pages": preview_info,
        "hook_score": min(100.0, round(hook_score, 1)),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_preflight(book_type: str, book_data: dict[str, Any]) -> dict[str, Any]:
    """Run the full Print Production Preflight v2 suite.

    Parameters
    ----------
    book_type:
        One of ``"childrens"``, ``"coloring"``, or ``"puzzle"``.
    book_data:
        Dictionary describing the book. Expected keys:

        - ``page_count`` (int) — total interior pages
        - ``interior_type`` (str) — ``"bw"`` | ``"color"`` | ``"premium_color"``
          | ``"standard_color"``
        - ``pages`` (list[dict]) — per-page data, each with optional keys:
          ``page_number``, ``dpi``, ``margins`` (dict of top/bottom/left/right),
          ``gutter_clearance_inches``, ``text_content``, ``illustration_prompt``,
          ``illustration_url``, ``layout``, ``has_color_pixels``
        - ``fonts`` (list[dict|str]) — font info with ``name`` and
          ``commercial_print`` boolean
        - ``age_range`` (str, children's only) — ``"board"`` | ``"picture"``
          | ``"early_reader"`` | ``"chapter"``
        - ``title``, ``subtitle``, ``description`` (str, optional)

    Returns
    -------
    dict matching the PreflightReport structure:
        ``{passed, checks, warnings, blockers, look_inside_data}``
    """
    report = PreflightReport()

    # Core print checks
    _check_dpi(book_data, report)
    _check_margins(book_data, report)
    _check_gutter_safety(book_data, report)
    _check_spine_width(book_data, report)
    _check_page_count(book_data, report)

    # Licensing & safety
    _check_font_licensing(book_data, report)
    _check_trademark_safety(book_data, report)
    _check_content_sensitivity(book_data, report)

    # Children's-specific
    if book_type == "childrens":
        _check_language_level(book_data, report)

    # B&W grayscale verification
    _check_grayscale(book_data, report)

    # Look Inside simulator data
    report.look_inside_data = _extract_look_inside_data(book_data)

    return report.to_dict()
