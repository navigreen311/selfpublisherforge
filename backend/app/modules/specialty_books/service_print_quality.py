"""Print Quality Systems: KDP cost engine, CMYK soft-proof, ink coverage analysis.

Implements blueprint sections 8.1-8.3:
  8.1 Print Cost & Pricing Engine
  8.2 CMYK / Soft-Proof Workflow
  8.3 Ink Coverage Analysis
"""

from __future__ import annotations

import logging
import math
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# -- KDP Cost Constants ----------------------------------------------------

# Per-page printing costs by interior type (USD)
PER_PAGE_COST: dict[str, float] = {
    "black_white": 0.012,
    "standard_color": 0.07,
    "premium_color": 0.075,
}

# Fixed cost by trim size (USD)
FIXED_COST_BY_TRIM: dict[str, float] = {
    "5x8": 0.85,
    "5.5x8.5": 0.85,
    "6x9": 0.85,
    "7x10": 0.85,
    "8x10": 0.85,
    "8.5x8.5": 0.85,
    "8.5x11": 0.85,
}

DEFAULT_FIXED_COST = 0.85

MARGIN_SCENARIOS = [0.0, 0.30, 0.50, 0.70]

INK_COVERAGE_COST_FACTOR = 0.0005

KDP_MIN_PAGES = 24
KDP_MAX_PAGES = 828

KDP_ROYALTY_35 = 0.35
KDP_ROYALTY_70 = 0.70

# Category norm pricing (from blueprint section 2.3)
CATEGORY_NORMS: dict[str, dict[str, Any]] = {
    "childrens_picture": {"interior_type": "premium_color", "price_low": 9.99, "price_high": 14.99},
    "childrens_board": {"interior_type": "premium_color", "price_low": 7.99, "price_high": 9.99},
    "adult_coloring": {"interior_type": "black_white", "price_low": 7.99, "price_high": 12.99},
    "kids_coloring": {"interior_type": "black_white", "price_low": 5.99, "price_high": 8.99},
    "word_search": {"interior_type": "black_white", "price_low": 6.99, "price_high": 9.99},
    "crossword": {"interior_type": "black_white", "price_low": 7.99, "price_high": 12.99},
    "sudoku": {"interior_type": "black_white", "price_low": 6.99, "price_high": 9.99},
    "maze": {"interior_type": "black_white", "price_low": 5.99, "price_high": 8.99},
    "large_print_puzzle": {"interior_type": "black_white", "price_low": 9.99, "price_high": 14.99},
}

# Spine width multipliers (inches per page)
SPINE_WIDTH_WHITE = 0.002252
SPINE_WIDTH_CREAM = 0.0025

# CMYK constants
MAX_INK_DENSITY_PCT = 300.0
HEAVY_INK_THRESHOLD = 80.0
LIGHT_INK_THRESHOLD = 5.0
SHADOW_CRUSH_LUMINANCE = 15

# Print spec validation constants
MIN_DPI = 300
MIN_MARGIN_TOP_BOTTOM = 0.25
MIN_MARGIN_OUTSIDE = 0.375
GUTTER_SMALL = 0.625
BLEED_SIZE = 0.125
MAX_FILE_SIZE_MB = 650

KDP_ACCEPTED_TRIM_SIZES = [
    "5x8",
    "5.06x7.81",
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
]


# =========================================================================
# 1. Print Cost & Pricing Engine (blueprint 8.1)
# =========================================================================


def calculate_print_cost(
    page_count: int,
    interior_type: str,
    trim_size: str,
    marketplace: str = "us",
    ink_coverage_pct: float | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Calculate KDP printing cost and pricing scenarios."""
    warnings: list[str] = []

    if page_count < KDP_MIN_PAGES:
        warnings.append(f"Page count {page_count} is below KDP minimum of {KDP_MIN_PAGES}.")
    if page_count > KDP_MAX_PAGES:
        warnings.append(f"Page count {page_count} exceeds KDP maximum of {KDP_MAX_PAGES}.")

    per_page = PER_PAGE_COST.get(interior_type, PER_PAGE_COST["black_white"])
    fixed = FIXED_COST_BY_TRIM.get(trim_size, DEFAULT_FIXED_COST)
    base_cost = fixed + (per_page * page_count)

    ink_cost_adjustment = 0.0
    if ink_coverage_pct is not None and ink_coverage_pct > 50.0:
        ink_cost_adjustment = (ink_coverage_pct - 50.0) * INK_COVERAGE_COST_FACTOR * page_count
    total_cost = round(base_cost + ink_cost_adjustment, 2)

    scenarios: list[dict[str, Any]] = []
    for margin_pct in MARGIN_SCENARIOS:
        if margin_pct >= 1.0:
            continue
        target_price = round(total_cost / (1.0 - margin_pct), 2)
        price = max(target_price, 0.99)
        royalty_35 = round(price * KDP_ROYALTY_35 - total_cost, 2)
        royalty_70 = round(price * KDP_ROYALTY_70 - total_cost, 2)
        effective_margin = round(royalty_70 / price * 100, 2) if price > 0 else 0.0
        scenarios.append(
            {
                "target_margin": f"{int(margin_pct * 100)}%",
                "price": price,
                "royalty_35": royalty_35,
                "royalty_70": royalty_70,
                "margin": effective_margin,
            }
        )

    recommended_price: float | None = None
    if category and category in CATEGORY_NORMS:
        norms = CATEGORY_NORMS[category]
        mid = round((norms["price_low"] + norms["price_high"]) / 2, 2)
        recommended_price = mid
        if mid < total_cost * 1.3:
            warnings.append(
                f"Category norm mid-price ${mid} may not provide 30% margin " f"over printing cost ${total_cost}."
            )
    else:
        recommended_price = round(total_cost / 0.50, 2)

    if recommended_price is not None and recommended_price < total_cost:
        warnings.append("Recommended price is below printing cost.")
    breakeven_price = round(total_cost / 0.60, 2)
    if recommended_price is not None and recommended_price < breakeven_price:
        warnings.append(f"Suggested price ${recommended_price} is below breakeven (${breakeven_price} at 60% royalty).")

    return {
        "base_cost": round(base_cost, 2),
        "ink_cost_adjustment": round(ink_cost_adjustment, 2),
        "total_cost": total_cost,
        "scenarios": scenarios,
        "recommended_price": recommended_price,
        "warnings": warnings,
        "page_count": page_count,
        "interior_type": interior_type,
        "trim_size": trim_size,
        "marketplace": marketplace,
    }


# =========================================================================
# 2. Ink Coverage Analysis (blueprint 8.3)
# =========================================================================


def analyze_ink_coverage(pages_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyse per-page ink coverage."""
    per_page: list[dict[str, Any]] = []
    coverages: list[float] = []

    for page in pages_data:
        page_num = page.get("page_num", 0)
        if "coverage_pct" in page and page["coverage_pct"] is not None:
            coverage = float(page["coverage_pct"])
        elif page.get("pixel_data"):
            pixels = page["pixel_data"]
            inked = sum(1 for p in pixels if p < 128)
            coverage = round((inked / len(pixels)) * 100, 2)
        else:
            coverage = 0.0

        per_page.append(
            {
                "page_num": page_num,
                "coverage_pct": round(coverage, 2),
                "heavy_warning": coverage > HEAVY_INK_THRESHOLD,
                "light_warning": coverage < LIGHT_INK_THRESHOLD,
            }
        )
        coverages.append(coverage)

    avg = round(sum(coverages) / len(coverages), 2) if coverages else 0.0
    return {
        "per_page": per_page,
        "average": avg,
        "max": round(max(coverages), 2) if coverages else 0.0,
        "min": round(min(coverages), 2) if coverages else 0.0,
    }


# =========================================================================
# 3. CMYK Soft-Proof Workflow (blueprint 8.2)
# =========================================================================


def _rgb_to_cmyk(r: int, g: int, b: int) -> tuple[float, float, float, float]:
    """Convert RGB (0-255) to CMYK (0-100 each)."""
    r_n, g_n, b_n = r / 255.0, g / 255.0, b / 255.0
    k = 1.0 - max(r_n, g_n, b_n)
    if k >= 1.0:
        return (0.0, 0.0, 0.0, 100.0)
    c = (1.0 - r_n - k) / (1.0 - k) * 100.0
    m = (1.0 - g_n - k) / (1.0 - k) * 100.0
    y = (1.0 - b_n - k) / (1.0 - k) * 100.0
    return (round(c, 2), round(m, 2), round(y, 2), round(k * 100.0, 2))


def _cmyk_to_rgb(c: float, m: float, y: float, k: float) -> tuple[int, int, int]:
    """Convert CMYK (0-100 each) back to approximate RGB (0-255)."""
    c_n, m_n, y_n, k_n = c / 100.0, m / 100.0, y / 100.0, k / 100.0
    r = int(round(255.0 * (1.0 - c_n) * (1.0 - k_n)))
    g = int(round(255.0 * (1.0 - m_n) * (1.0 - k_n)))
    b = int(round(255.0 * (1.0 - y_n) * (1.0 - k_n)))
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def _ink_density(c: float, m: float, y: float, k: float) -> float:
    """Total ink density as a percentage (C+M+Y+K)."""
    return c + m + y + k


def _is_out_of_gamut(r: int, g: int, b: int) -> bool:
    """Detect if an RGB colour is out of CMYK gamut via round-trip check."""
    cmyk = _rgb_to_cmyk(r, g, b)
    r2, g2, b2 = _cmyk_to_rgb(*cmyk)
    dist = math.sqrt((r - r2) ** 2 + (g - g2) ** 2 + (b - b2) ** 2)
    return dist > 10.0


def generate_soft_proof(
    image_data: list[dict[str, Any]],
    profile: str = "US_SWOP_v2",
) -> dict[str, Any]:
    """Simulate RGB -> CMYK conversion and detect print issues."""
    out_of_gamut_areas: list[dict[str, Any]] = []
    shadow_crush_warnings: list[dict[str, Any]] = []
    ink_density_issues: list[dict[str, Any]] = []

    for px in image_data:
        r, g, b = px.get("r", 0), px.get("g", 0), px.get("b", 0)
        page, x, y = px.get("page", 1), px.get("x", 0), px.get("y", 0)
        cmyk = _rgb_to_cmyk(r, g, b)
        nearest_rgb = _cmyk_to_rgb(*cmyk)

        if _is_out_of_gamut(r, g, b):
            out_of_gamut_areas.append(
                {
                    "page": page,
                    "x": x,
                    "y": y,
                    "original_rgb": [r, g, b],
                    "nearest_cmyk": list(cmyk),
                }
            )

        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        if luminance < SHADOW_CRUSH_LUMINANCE and (r > 0 or g > 0 or b > 0):
            shadow_crush_warnings.append(
                {
                    "page": page,
                    "x": x,
                    "y": y,
                    "luminance": round(luminance, 2),
                }
            )

        density = _ink_density(*cmyk)
        if density > MAX_INK_DENSITY_PCT:
            ink_density_issues.append(
                {
                    "page": page,
                    "x": x,
                    "y": y,
                    "density": round(density, 2),
                    "cmyk": list(cmyk),
                }
            )

    return {
        "cmyk_preview_url": f"/api/v1/specialty/color/preview/{profile}/cmyk_proof.png",
        "out_of_gamut_areas": out_of_gamut_areas,
        "shadow_crush_warnings": shadow_crush_warnings,
        "ink_density_issues": ink_density_issues,
    }


# =========================================================================
# 4. Auto-Adjust Color
# =========================================================================


def auto_adjust_color(image_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Auto-fix gamut, ink density, and shadow crush issues."""
    adjusted: list[dict[str, Any]] = []
    changes_log: list[dict[str, Any]] = []

    for px in image_data:
        r, g, b = px.get("r", 0), px.get("g", 0), px.get("b", 0)
        page, x, y = px.get("page", 1), px.get("x", 0), px.get("y", 0)
        original = {"r": r, "g": g, "b": b}

        cmyk = _rgb_to_cmyk(r, g, b)

        if _is_out_of_gamut(r, g, b):
            r, g, b = _cmyk_to_rgb(*cmyk)
            changes_log.append(
                {
                    "page": page,
                    "x": x,
                    "y": y,
                    "type": "gamut_mapping",
                    "original": original,
                    "adjusted": {"r": r, "g": g, "b": b},
                }
            )

        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        if luminance < SHADOW_CRUSH_LUMINANCE and (r > 0 or g > 0 or b > 0):
            scale = SHADOW_CRUSH_LUMINANCE / max(luminance, 1)
            r = min(255, int(r * scale))
            g = min(255, int(g * scale))
            b = min(255, int(b * scale))
            changes_log.append(
                {
                    "page": page,
                    "x": x,
                    "y": y,
                    "type": "shadow_lighten",
                    "original": original,
                    "adjusted": {"r": r, "g": g, "b": b},
                }
            )

        cmyk = _rgb_to_cmyk(r, g, b)
        density = _ink_density(*cmyk)
        if density > MAX_INK_DENSITY_PCT:
            reduction = density / MAX_INK_DENSITY_PCT
            r, g, b = _cmyk_to_rgb(cmyk[0] / reduction, cmyk[1] / reduction, cmyk[2] / reduction, cmyk[3] / reduction)
            changes_log.append(
                {
                    "page": page,
                    "x": x,
                    "y": y,
                    "type": "ink_density_reduction",
                    "original_density": round(density, 2),
                    "adjusted": {"r": r, "g": g, "b": b},
                }
            )

        adjusted.append({"page": page, "x": x, "y": y, "r": r, "g": g, "b": b})

    return {
        "adjusted_pixels": adjusted,
        "changes_log": changes_log,
        "total_changes": len(changes_log),
    }


# =========================================================================
# 5. Spine Width Calculator
# =========================================================================


def calculate_spine_width(page_count: int, paper_type: str = "white") -> dict[str, Any]:
    """Calculate book spine width based on page count and paper type."""
    multiplier = SPINE_WIDTH_CREAM if paper_type == "cream" else SPINE_WIDTH_WHITE
    width_inches = round(page_count * multiplier, 4)
    width_mm = round(width_inches * 25.4, 2)
    return {
        "spine_width_inches": width_inches,
        "spine_width_mm": width_mm,
        "page_count": page_count,
        "paper_type": paper_type,
    }


# =========================================================================
# 6. Grayscale Preview
# =========================================================================


def generate_grayscale_preview(image_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert colour pixel data to grayscale for B&W preview."""
    grayscale_pixels: list[dict[str, Any]] = []
    for px in image_data:
        r, g, b = px.get("r", 0), px.get("g", 0), px.get("b", 0)
        gray = max(0, min(255, int(round(0.299 * r + 0.587 * g + 0.114 * b))))
        grayscale_pixels.append(
            {
                "page": px.get("page", 1),
                "x": px.get("x", 0),
                "y": px.get("y", 0),
                "r": gray,
                "g": gray,
                "b": gray,
            }
        )
    return {"grayscale_pixels": grayscale_pixels, "total_pixels": len(grayscale_pixels)}


# =========================================================================
# 7. Comprehensive Print Specification Validation
# =========================================================================


async def validate_print_specs(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
    *,
    dpi: int = 300,
    margins: dict[str, float] | None = None,
    has_bleed: bool = False,
    bleed_size: float = 0.0,
    trim_size: str = "6x9",
    page_count: int = 0,
    file_size_mb: float = 0.0,
) -> dict[str, Any]:
    """Run comprehensive print specification validation."""
    checks: list[dict[str, Any]] = []

    # DPI
    dpi_pass = dpi >= MIN_DPI
    checks.append(
        {
            "name": "dpi_check",
            "passed": dpi_pass,
            "detail": f"DPI={dpi}, required>={MIN_DPI}",
            "severity": "error" if not dpi_pass else "info",
        }
    )

    # Margins
    if margins is None:
        margins = {}
    top = margins.get("top", MIN_MARGIN_TOP_BOTTOM)
    bottom = margins.get("bottom", MIN_MARGIN_TOP_BOTTOM)
    outside = margins.get("outside", MIN_MARGIN_OUTSIDE)
    gutter = margins.get("gutter", GUTTER_SMALL)
    required_gutter = GUTTER_SMALL if page_count <= 150 else 0.875

    for name, val, req in [
        ("margin_top", top, MIN_MARGIN_TOP_BOTTOM),
        ("margin_bottom", bottom, MIN_MARGIN_TOP_BOTTOM),
        ("margin_outside", outside, MIN_MARGIN_OUTSIDE),
        ("margin_gutter", gutter, required_gutter),
    ]:
        p = val >= req
        checks.append(
            {
                "name": name,
                "passed": p,
                "detail": f"{name}={val}, required>={req}",
                "severity": "error" if not p else "info",
            }
        )

    # Bleed
    if has_bleed:
        bp = abs(bleed_size - BLEED_SIZE) < 0.01
        checks.append(
            {
                "name": "bleed_check",
                "passed": bp,
                "detail": f"bleed={bleed_size}, required={BLEED_SIZE}",
                "severity": "error" if not bp else "info",
            }
        )
    else:
        checks.append({"name": "bleed_check", "passed": True, "detail": "No bleed specified", "severity": "info"})

    # Trim size
    tp = trim_size in KDP_ACCEPTED_TRIM_SIZES
    checks.append(
        {"name": "trim_size", "passed": tp, "detail": f"trim={trim_size}", "severity": "error" if not tp else "info"}
    )

    # Page count
    pp = KDP_MIN_PAGES <= page_count <= KDP_MAX_PAGES
    checks.append(
        {
            "name": "page_count",
            "passed": pp,
            "detail": f"pages={page_count}, range={KDP_MIN_PAGES}-{KDP_MAX_PAGES}",
            "severity": "error" if not pp else "info",
        }
    )

    # File size
    fp = file_size_mb <= MAX_FILE_SIZE_MB
    checks.append(
        {
            "name": "file_size",
            "passed": fp,
            "detail": f"size={file_size_mb}MB, max={MAX_FILE_SIZE_MB}MB",
            "severity": "error" if not fp else "info",
        }
    )

    all_passed = all(c["passed"] for c in checks)
    return {
        "book_type": book_type,
        "book_id": str(book_id),
        "org_id": str(org_id),
        "checks": checks,
        "all_passed": all_passed,
        "total_checks": len(checks),
        "passed_count": sum(1 for c in checks if c["passed"]),
        "failed_count": sum(1 for c in checks if not c["passed"]),
    }
