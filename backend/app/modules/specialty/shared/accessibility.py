"""
Accessibility Pack

Generates dyslexia-friendly, large print, and high contrast variants
of specialty books.  Includes WCAG compliance checking.
"""

import copy

# ---------------------------------------------------------------------------
# Accessibility constants
# ---------------------------------------------------------------------------

# Dyslexia-friendly settings
DYSLEXIA_SETTINGS = {
    "font_family": "OpenDyslexic",
    "line_spacing_multiplier": 1.5,
    "letter_spacing_increase_pct": 15,
    "text_align": "left",
    "background_color": "#FFFDF5",
    "text_color": "#333333",
    "avoid_italics": True,
    "avoid_all_caps": True,
    "max_line_length_chars": 60,
}

# Large print settings (APH -- American Printing House for the Blind)
LARGE_PRINT_SETTINGS = {
    "min_body_font_pt": 18,
    "min_heading_font_pt": 24,
    "contrast_ratio_min": 7.0,  # WCAG AAA
    "wcag_level": "AAA",
    "line_spacing_multiplier": 1.4,
    "min_margin_inches": 0.75,
    "font_family": "APHont",
    "fallback_font_family": "Verdana",
    "text_color": "#000000",
    "background_color": "#FFFFFF",
    "aph_compliant": True,
}

# High contrast settings
HIGH_CONTRAST_SETTINGS = {
    "background_color": "#FFFFFF",
    "text_color": "#000000",
    "grid_line_min_width_px": 2,
    "bold_numbers": True,
    "bold_instructions": True,
    "remove_decorative_elements": True,
    "border_width_px": 3,
    "contrast_ratio_min": 21.0,  # Maximum possible contrast
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _relative_luminance(hex_color: str) -> float:
    """Compute relative luminance from a hex colour string."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    def linearize(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def _contrast_ratio(color1: str, color2: str) -> float:
    """Compute WCAG contrast ratio between two hex colours."""
    l1 = _relative_luminance(color1)
    l2 = _relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def _apply_letter_spacing(text: str, increase_pct: int) -> dict:
    """Return CSS letter-spacing value for the given increase."""
    return {"letter_spacing": f"{increase_pct / 100.0:.2f}em"}


def _deep_copy_book(book_data: dict) -> dict:
    """Create a deep copy of book data to avoid mutating the original."""
    return copy.deepcopy(book_data)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_dyslexia_variant(book_data: dict) -> dict:
    """
    Generate a dyslexia-friendly variant of the book.

    Applies: OpenDyslexic font, 1.5x line spacing, +15% letter spacing,
    left-aligned text, off-white background (#FFFDF5).

    Parameters
    ----------
    book_data : dict
        Full book data with ``pages`` list. Each page may have
        ``text_content``, ``text_font_size``, ``text_color``,
        ``background_color``, ``text_align``, ``font_family``.

    Returns
    -------
    dict
        Modified book data with dyslexia-friendly settings applied,
        plus a ``variant_metadata`` section.
    """
    variant = _deep_copy_book(book_data)
    settings = DYSLEXIA_SETTINGS
    changes: list[str] = []

    # Apply global settings
    variant["font_family"] = settings["font_family"]
    variant["background_color"] = settings["background_color"]
    changes.append(f"Font changed to {settings['font_family']}")
    changes.append(f"Background set to {settings['background_color']}")

    for page_idx, page in enumerate(variant.get("pages", [])):
        # Font
        page["font_family"] = settings["font_family"]

        # Line spacing
        original_spacing = page.get("line_spacing", 1.0)
        page["line_spacing"] = round(original_spacing * settings["line_spacing_multiplier"], 2)

        # Letter spacing
        page["letter_spacing_pct"] = settings["letter_spacing_increase_pct"]

        # Alignment
        page["text_align"] = settings["text_align"]

        # Background
        page["background_color"] = settings["background_color"]

        # Text colour for readability
        page["text_color"] = settings["text_color"]

        # Remove italics
        if settings["avoid_italics"]:
            page["font_style"] = "normal"

        # Remove all-caps
        text = page.get("text_content", "")
        if settings["avoid_all_caps"] and text == text.upper() and len(text) > 3:
            page["text_content"] = text.capitalize()

    changes.extend(
        [
            f"Line spacing multiplied by {settings['line_spacing_multiplier']}x",
            f"Letter spacing increased by {settings['letter_spacing_increase_pct']}%",
            f"Text alignment set to {settings['text_align']}",
            "Italics removed",
            "All-caps converted to sentence case",
        ]
    )

    variant["variant_metadata"] = {
        "variant_type": "dyslexia_friendly",
        "settings_applied": settings,
        "changes": changes,
        "total_pages_modified": len(variant.get("pages", [])),
    }

    return variant


def generate_large_print_variant(book_data: dict) -> dict:
    """
    Generate a large print variant following APH guidelines.

    Applies: 18pt body minimum, 7:1 contrast ratio (WCAG AAA),
    APH-compliant font and spacing.

    Parameters
    ----------
    book_data : dict
        Full book data with ``pages`` list.

    Returns
    -------
    dict
        Modified book data with large print settings applied.
    """
    variant = _deep_copy_book(book_data)
    settings = LARGE_PRINT_SETTINGS
    changes: list[str] = []
    font_adjustments = 0

    variant["font_family"] = settings["font_family"]
    variant["background_color"] = settings["background_color"]

    for page in variant.get("pages", []):
        # Font family
        page["font_family"] = settings["font_family"]
        page["fallback_font_family"] = settings["fallback_font_family"]

        # Enforce minimum font size
        current_size = page.get("text_font_size", 12)
        elem_type = page.get("element_type", "body")
        min_size = (
            settings["min_heading_font_pt"] if elem_type in ("heading", "title") else settings["min_body_font_pt"]
        )

        if current_size < min_size:
            page["text_font_size"] = min_size
            font_adjustments += 1

        # Contrast enforcement
        text_color = page.get("text_color", "#000000")
        bg_color = page.get("background_color", "#FFFFFF")
        ratio = _contrast_ratio(text_color, bg_color)
        if ratio < settings["contrast_ratio_min"]:
            page["text_color"] = settings["text_color"]
            page["background_color"] = settings["background_color"]

        # Line spacing
        original_spacing = page.get("line_spacing", 1.0)
        page["line_spacing"] = max(original_spacing, settings["line_spacing_multiplier"])

        # Margins
        page["min_margin_inches"] = settings["min_margin_inches"]

    changes.extend(
        [
            f"Font changed to {settings['font_family']}",
            f"Minimum body font: {settings['min_body_font_pt']}pt",
            f"Minimum heading font: {settings['min_heading_font_pt']}pt",
            f"Contrast ratio enforced: {settings['contrast_ratio_min']}:1 (WCAG {settings['wcag_level']})",
            f"Font sizes adjusted on {font_adjustments} pages",
            f"Line spacing minimum: {settings['line_spacing_multiplier']}",
            f"Margins minimum: {settings['min_margin_inches']}in",
            "APH guidelines applied",
        ]
    )

    variant["variant_metadata"] = {
        "variant_type": "large_print",
        "settings_applied": settings,
        "changes": changes,
        "total_pages_modified": len(variant.get("pages", [])),
        "font_adjustments": font_adjustments,
        "aph_compliant": settings["aph_compliant"],
    }

    return variant


def generate_high_contrast_variant(book_data: dict) -> dict:
    """
    Generate a high-contrast variant.

    Applies: pure black on white, 2px minimum grid lines, bold numbers
    and instructions, removal of decorative elements.

    Parameters
    ----------
    book_data : dict
        Full book data with ``pages`` list.

    Returns
    -------
    dict
        Modified book data with high contrast settings applied.
    """
    variant = _deep_copy_book(book_data)
    settings = HIGH_CONTRAST_SETTINGS
    changes: list[str] = []
    decorative_removed = 0

    for page in variant.get("pages", []):
        # Enforce pure black on white
        page["text_color"] = settings["text_color"]
        page["background_color"] = settings["background_color"]

        # Grid lines
        if page.get("grid_line_width"):
            if page["grid_line_width"] < settings["grid_line_min_width_px"]:
                page["grid_line_width"] = settings["grid_line_min_width_px"]
        page["grid_line_color"] = settings["text_color"]

        # Bold numbers and instructions
        if settings["bold_numbers"]:
            page["number_font_weight"] = "bold"
        if settings["bold_instructions"]:
            page["instruction_font_weight"] = "bold"

        # Border
        page["border_width"] = settings["border_width_px"]
        page["border_color"] = settings["text_color"]

        # Remove decorative elements
        if settings["remove_decorative_elements"]:
            elements = page.get("elements", [])
            filtered = [e for e in elements if e.get("type") not in ("decoration", "watermark", "background_pattern")]
            removed = len(elements) - len(filtered)
            decorative_removed += removed
            page["elements"] = filtered

    changes.extend(
        [
            f"Background: {settings['background_color']} (pure white)",
            f"Text: {settings['text_color']} (pure black)",
            f"Grid lines minimum: {settings['grid_line_min_width_px']}px",
            "Numbers bolded" if settings["bold_numbers"] else "Numbers unchanged",
            "Instructions bolded" if settings["bold_instructions"] else "Instructions unchanged",
            f"Decorative elements removed: {decorative_removed}",
            f"Border: {settings['border_width_px']}px solid black",
        ]
    )

    variant["variant_metadata"] = {
        "variant_type": "high_contrast",
        "settings_applied": settings,
        "changes": changes,
        "total_pages_modified": len(variant.get("pages", [])),
        "decorative_elements_removed": decorative_removed,
        "contrast_ratio": _contrast_ratio(settings["text_color"], settings["background_color"]),
    }

    return variant


def check_accessibility_compliance(book_data: dict, variant_type: str) -> dict:
    """
    Verify that a book meets accessibility standards for the given variant.

    Parameters
    ----------
    book_data : dict
        Book data (possibly already transformed by a variant generator).
    variant_type : str
        One of ``"dyslexia_friendly"``, ``"large_print"``,
        ``"high_contrast"``.

    Returns
    -------
    dict
        ``{"compliant": bool, "issues": list[dict], "score": int,
        "variant_type": str, "checks_performed": int}``.
    """
    issues: list[dict] = []
    checks_performed = 0

    pages = book_data.get("pages", [])

    if variant_type == "dyslexia_friendly":
        settings = DYSLEXIA_SETTINGS

        for page_idx, page in enumerate(pages):
            # Check font
            checks_performed += 1
            if page.get("font_family") != settings["font_family"]:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "font_family",
                        "expected": settings["font_family"],
                        "actual": page.get("font_family", "unknown"),
                        "severity": "error",
                    }
                )

            # Check line spacing
            checks_performed += 1
            spacing = page.get("line_spacing", 1.0)
            min_spacing = settings["line_spacing_multiplier"]
            if spacing < min_spacing:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "line_spacing",
                        "expected": f">= {min_spacing}",
                        "actual": spacing,
                        "severity": "error",
                    }
                )

            # Check alignment
            checks_performed += 1
            if page.get("text_align", "left") != settings["text_align"]:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "text_align",
                        "expected": settings["text_align"],
                        "actual": page.get("text_align", "unknown"),
                        "severity": "warning",
                    }
                )

            # Check background
            checks_performed += 1
            if page.get("background_color", "").upper() != settings["background_color"].upper():
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "background_color",
                        "expected": settings["background_color"],
                        "actual": page.get("background_color", "unknown"),
                        "severity": "warning",
                    }
                )

            # Check italics
            checks_performed += 1
            if settings["avoid_italics"] and page.get("font_style") == "italic":
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "no_italics",
                        "expected": "normal",
                        "actual": "italic",
                        "severity": "warning",
                    }
                )

    elif variant_type == "large_print":
        settings = LARGE_PRINT_SETTINGS

        for page_idx, page in enumerate(pages):
            # Font size
            checks_performed += 1
            font_size = page.get("text_font_size", 12)
            elem_type = page.get("element_type", "body")
            min_size = (
                settings["min_heading_font_pt"] if elem_type in ("heading", "title") else settings["min_body_font_pt"]
            )
            if font_size < min_size:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "font_size",
                        "expected": f">= {min_size}pt",
                        "actual": f"{font_size}pt",
                        "severity": "error",
                    }
                )

            # Contrast ratio
            checks_performed += 1
            text_color = page.get("text_color", "#000000")
            bg_color = page.get("background_color", "#FFFFFF")
            ratio = _contrast_ratio(text_color, bg_color)
            if ratio < settings["contrast_ratio_min"]:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "contrast_ratio",
                        "expected": f">= {settings['contrast_ratio_min']}:1",
                        "actual": f"{ratio}:1",
                        "severity": "error",
                    }
                )

            # Line spacing
            checks_performed += 1
            spacing = page.get("line_spacing", 1.0)
            if spacing < settings["line_spacing_multiplier"]:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "line_spacing",
                        "expected": f">= {settings['line_spacing_multiplier']}",
                        "actual": spacing,
                        "severity": "warning",
                    }
                )

    elif variant_type == "high_contrast":
        settings = HIGH_CONTRAST_SETTINGS

        for page_idx, page in enumerate(pages):
            # Colour check
            checks_performed += 1
            if page.get("text_color", "").upper() != settings["text_color"].upper():
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "text_color",
                        "expected": settings["text_color"],
                        "actual": page.get("text_color", "unknown"),
                        "severity": "error",
                    }
                )

            checks_performed += 1
            if page.get("background_color", "").upper() != settings["background_color"].upper():
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "background_color",
                        "expected": settings["background_color"],
                        "actual": page.get("background_color", "unknown"),
                        "severity": "error",
                    }
                )

            # Grid line width
            checks_performed += 1
            grid_w = page.get("grid_line_width")
            if grid_w is not None and grid_w < settings["grid_line_min_width_px"]:
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "grid_line_width",
                        "expected": f">= {settings['grid_line_min_width_px']}px",
                        "actual": f"{grid_w}px",
                        "severity": "error",
                    }
                )

            # Bold numbers
            checks_performed += 1
            if settings["bold_numbers"] and page.get("number_font_weight") != "bold":
                issues.append(
                    {
                        "page": page_idx + 1,
                        "check": "bold_numbers",
                        "expected": "bold",
                        "actual": page.get("number_font_weight", "normal"),
                        "severity": "warning",
                    }
                )

            # Decorative elements
            checks_performed += 1
            if settings["remove_decorative_elements"]:
                decorative = [
                    e
                    for e in page.get("elements", [])
                    if e.get("type") in ("decoration", "watermark", "background_pattern")
                ]
                if decorative:
                    issues.append(
                        {
                            "page": page_idx + 1,
                            "check": "decorative_elements",
                            "expected": "none",
                            "actual": f"{len(decorative)} found",
                            "severity": "warning",
                        }
                    )
    else:
        issues.append(
            {
                "page": 0,
                "check": "variant_type",
                "expected": "dyslexia_friendly | large_print | high_contrast",
                "actual": variant_type,
                "severity": "error",
            }
        )
        checks_performed += 1

    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")

    # Score: 100 minus penalties
    score = max(0, 100 - (error_count * 15) - (warning_count * 5))

    return {
        "compliant": error_count == 0,
        "issues": issues,
        "score": score,
        "variant_type": variant_type,
        "checks_performed": checks_performed,
        "errors": error_count,
        "warnings": warning_count,
    }
