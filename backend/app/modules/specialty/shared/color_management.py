"""CMYK & Color Management for Specialty Books.

Provides RGB-to-CMYK conversion, gamut checking, ink density analysis,
shadow-crush detection, soft-proof data generation, and automatic
CMYK-safe colour adjustment.

Usage::

    c, m, y, k = rgb_to_cmyk(255, 102, 0)
    density = calculate_ink_density(c, m, y, k)
    report = analyze_ink_coverage(pages_data)
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum recommended total ink coverage for offset/digital print
MAX_INK_DENSITY = 300.0

# Shadow crush threshold — dark colours above this may lose detail
SHADOW_CRUSH_THRESHOLD = 280.0

# Delta-E threshold above which a colour is considered out-of-gamut
# (simplified; real profiles use ICC, but this covers common violations)
GAMUT_DELTA_E_THRESHOLD = 5.0

# sRGB gamut boundary approximation for CMYK: highly saturated
# colours in sRGB that CMYK cannot reproduce.
# Stored as (R, G, B) tuples that are known problem colours.
_KNOWN_OOG_RANGES: list[dict[str, Any]] = [
    # Vivid blues/violets
    {"r_range": (0, 80), "g_range": (0, 80), "b_range": (200, 255), "label": "vivid blue"},
    # Electric greens
    {"r_range": (0, 80), "g_range": (200, 255), "b_range": (0, 80), "label": "electric green"},
    # Neon/fluorescent colours
    {"r_range": (200, 255), "g_range": (0, 60), "b_range": (200, 255), "label": "neon magenta"},
    {"r_range": (0, 60), "g_range": (200, 255), "b_range": (200, 255), "label": "neon cyan"},
]


# ---------------------------------------------------------------------------
# RGB → CMYK Conversion
# ---------------------------------------------------------------------------

def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[float, float, float, float]:
    """Convert an RGB colour (0-255 per channel) to CMYK (0-100 per channel).

    Uses the standard formulaic conversion (no ICC profile). Results are
    percentages in the range 0-100.

    Parameters
    ----------
    r, g, b:
        Red, green, blue channel values (0-255).

    Returns
    -------
    Tuple of ``(C, M, Y, K)`` as floats 0-100, rounded to 2 decimals.
    """
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    k = 1.0 - max(r_norm, g_norm, b_norm)
    if k >= 1.0:
        return (0.0, 0.0, 0.0, 100.0)

    c = (1.0 - r_norm - k) / (1.0 - k)
    m = (1.0 - g_norm - k) / (1.0 - k)
    y = (1.0 - b_norm - k) / (1.0 - k)

    return (
        round(c * 100, 2),
        round(m * 100, 2),
        round(y * 100, 2),
        round(k * 100, 2),
    )


# ---------------------------------------------------------------------------
# Ink Density
# ---------------------------------------------------------------------------

def calculate_ink_density(c: float, m: float, y: float, k: float) -> float:
    """Calculate total ink coverage percentage.

    Parameters
    ----------
    c, m, y, k:
        CMYK channel values (0-100 each).

    Returns
    -------
    Total ink density as a percentage (0-400 theoretical max).
    Values above 300% are generally problematic for print.
    """
    return round(c + m + y + k, 2)


# ---------------------------------------------------------------------------
# Gamut Checking
# ---------------------------------------------------------------------------

def _is_out_of_gamut(r: int, g: int, b: int) -> bool:
    """Quick heuristic check whether an RGB colour is likely out of CMYK gamut."""
    for oog in _KNOWN_OOG_RANGES:
        if (
            oog["r_range"][0] <= r <= oog["r_range"][1]
            and oog["g_range"][0] <= g <= oog["g_range"][1]
            and oog["b_range"][0] <= b <= oog["b_range"][1]
        ):
            return True

    # Additional heuristic: very high saturation in sRGB
    max_ch = max(r, g, b)
    min_ch = min(r, g, b)
    if max_ch > 0:
        saturation = (max_ch - min_ch) / max_ch
        # Highly saturated, bright colours are risky
        if saturation > 0.85 and max_ch > 200:
            return True

    return False


def _suggest_cmyk_alternative(
    r: int, g: int, b: int,
) -> dict[str, Any]:
    """Suggest a CMYK-safe alternative for an out-of-gamut RGB colour.

    Desaturates the colour slightly to bring it within gamut.
    """
    # Simple desaturation: move each channel toward the mean
    mean_val = (r + g + b) / 3.0
    factor = 0.80  # pull 20% toward mean
    adj_r = int(round(r * factor + mean_val * (1 - factor)))
    adj_g = int(round(g * factor + mean_val * (1 - factor)))
    adj_b = int(round(b * factor + mean_val * (1 - factor)))
    adj_r = max(0, min(255, adj_r))
    adj_g = max(0, min(255, adj_g))
    adj_b = max(0, min(255, adj_b))

    c, m, y, k = rgb_to_cmyk(adj_r, adj_g, adj_b)
    return {
        "original_rgb": (r, g, b),
        "adjusted_rgb": (adj_r, adj_g, adj_b),
        "cmyk": (c, m, y, k),
        "ink_density": calculate_ink_density(c, m, y, k),
    }


def check_gamut(
    rgb_colors: list[tuple[int, int, int]],
) -> list[dict[str, Any]]:
    """Check a list of RGB colours for CMYK gamut violations.

    Parameters
    ----------
    rgb_colors:
        List of ``(R, G, B)`` tuples, each channel 0-255.

    Returns
    -------
    List of dicts for out-of-gamut colours, each with
    ``original_rgb``, ``adjusted_rgb``, ``cmyk``, ``ink_density``.
    Only colours that are out of gamut are returned.
    """
    results: list[dict[str, Any]] = []
    for r, g, b in rgb_colors:
        if _is_out_of_gamut(r, g, b):
            results.append(_suggest_cmyk_alternative(r, g, b))
    return results


# ---------------------------------------------------------------------------
# Ink Coverage Analysis (per-page)
# ---------------------------------------------------------------------------

def analyze_ink_coverage(
    pages_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Produce a per-page ink density report.

    Parameters
    ----------
    pages_data:
        List of page dicts. Each should contain:

        - ``page_number`` (int)
        - ``avg_cmyk`` (tuple/list of C, M, Y, K) **or**
          ``ink_coverage_percent`` (float)

    Returns
    -------
    List of dicts, one per page, with ``page_number``, ``ink_density``,
    ``within_limit``, ``c``, ``m``, ``y``, ``k``.
    """
    results: list[dict[str, Any]] = []
    for page in pages_data:
        page_num = page.get("page_number", 0)
        cmyk = page.get("avg_cmyk")
        if cmyk and len(cmyk) == 4:
            c, m, y, k = cmyk
        else:
            # Fallback: estimate from ink_coverage_percent
            coverage = page.get("ink_coverage_percent", 20.0)
            # Distribute evenly across channels (rough estimate)
            c = m = y = coverage * 0.25
            k = coverage * 0.25
            c, m, y, k = (
                round(c, 2), round(m, 2), round(y, 2), round(k, 2)
            )

        density = calculate_ink_density(c, m, y, k)
        results.append({
            "page_number": page_num,
            "ink_density": density,
            "within_limit": density <= MAX_INK_DENSITY,
            "c": c,
            "m": m,
            "y": y,
            "k": k,
        })

    return results


# ---------------------------------------------------------------------------
# Shadow Crush Detection
# ---------------------------------------------------------------------------

def check_shadow_crush(
    colors: list[tuple[int, int, int]],
) -> list[dict[str, Any]]:
    """Flag dark RGB colours that will lose detail in CMYK print.

    Shadow crush occurs when the total ink density exceeds ~280%,
    causing dark areas to merge into a featureless black.

    Parameters
    ----------
    colors:
        List of ``(R, G, B)`` tuples.

    Returns
    -------
    List of flagged colours with ``rgb``, ``cmyk``, ``ink_density``,
    ``warning``.
    """
    flagged: list[dict[str, Any]] = []
    for r, g, b in colors:
        c, m, y, k = rgb_to_cmyk(r, g, b)
        density = calculate_ink_density(c, m, y, k)
        if density > SHADOW_CRUSH_THRESHOLD:
            flagged.append({
                "rgb": (r, g, b),
                "cmyk": (c, m, y, k),
                "ink_density": density,
                "warning": (
                    f"Total ink density {density:.1f}% exceeds "
                    f"{SHADOW_CRUSH_THRESHOLD}% threshold. "
                    "Dark detail may be lost in print."
                ),
            })
    return flagged


# ---------------------------------------------------------------------------
# Soft-Proof Data
# ---------------------------------------------------------------------------

def soft_proof_data(page_data: dict[str, Any]) -> dict[str, Any]:
    """Generate soft-proof simulation data for a single page.

    Parameters
    ----------
    page_data:
        Page dict with optional keys:

        - ``dominant_colors`` — list of ``(R, G, B)`` tuples
        - ``avg_cmyk`` — ``(C, M, Y, K)`` tuple
        - ``ink_coverage_percent`` — float

    Returns
    -------
    dict with ``original_rgb``, ``simulated_cmyk``, ``out_of_gamut_areas``,
    ``ink_density``, ``issues``.
    """
    dominant = page_data.get("dominant_colors", [])
    issues: list[str] = []

    # Convert dominant colours
    cmyk_colors: list[dict[str, Any]] = []
    oog_areas: list[dict[str, Any]] = []
    for rgb in dominant:
        if len(rgb) < 3:
            continue
        r, g, b = rgb[0], rgb[1], rgb[2]
        c, m, y, k = rgb_to_cmyk(r, g, b)
        density = calculate_ink_density(c, m, y, k)
        cmyk_colors.append({
            "rgb": (r, g, b),
            "cmyk": (c, m, y, k),
            "ink_density": density,
        })
        if _is_out_of_gamut(r, g, b):
            alt = _suggest_cmyk_alternative(r, g, b)
            oog_areas.append(alt)
            issues.append(
                f"RGB({r},{g},{b}) is out of CMYK gamut — "
                f"suggested alternative: RGB{alt['adjusted_rgb']}"
            )
        if density > MAX_INK_DENSITY:
            issues.append(
                f"RGB({r},{g},{b}) → ink density {density:.1f}% "
                f"exceeds {MAX_INK_DENSITY}% limit."
            )
        if density > SHADOW_CRUSH_THRESHOLD:
            issues.append(
                f"RGB({r},{g},{b}) may cause shadow crush "
                f"(ink density {density:.1f}%)."
            )

    # Overall page ink density
    page_cmyk = page_data.get("avg_cmyk")
    if page_cmyk and len(page_cmyk) == 4:
        page_density = calculate_ink_density(*page_cmyk)
    else:
        page_density = page_data.get("ink_coverage_percent", 0.0)

    return {
        "original_rgb": [c["rgb"] for c in cmyk_colors],
        "simulated_cmyk": [c["cmyk"] for c in cmyk_colors],
        "out_of_gamut_areas": oog_areas,
        "ink_density": page_density,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Auto-Adjust Colours
# ---------------------------------------------------------------------------

def auto_adjust_colors(page_data: dict[str, Any]) -> dict[str, Any]:
    """Adjust page colours to be CMYK-safe.

    Performs three corrections:
    1. Brings out-of-gamut colours into gamut (desaturation).
    2. Reduces ink density on colours exceeding 300%.
    3. Lightens shadow-crush candidates.

    Parameters
    ----------
    page_data:
        Page dict with ``dominant_colors`` (list of ``(R,G,B)`` tuples).

    Returns
    -------
    dict with ``adjusted_colors``, ``changes_made``, ``original_colors``.
    """
    dominant = page_data.get("dominant_colors", [])
    adjusted: list[tuple[int, int, int]] = []
    changes: list[str] = []

    for rgb in dominant:
        if len(rgb) < 3:
            adjusted.append(tuple(rgb[:3]))  # type: ignore[arg-type]
            continue
        r, g, b = rgb[0], rgb[1], rgb[2]
        modified = False

        # 1. Gamut fix
        if _is_out_of_gamut(r, g, b):
            alt = _suggest_cmyk_alternative(r, g, b)
            r, g, b = alt["adjusted_rgb"]
            changes.append(
                f"Desaturated RGB{rgb[:3]} → RGB({r},{g},{b}) for gamut safety."
            )
            modified = True

        # 2. Ink density fix
        c, m, y, k = rgb_to_cmyk(r, g, b)
        density = calculate_ink_density(c, m, y, k)
        if density > MAX_INK_DENSITY:
            # Reduce by lightening
            scale = MAX_INK_DENSITY / density
            c2 = round(c * scale, 2)
            m2 = round(m * scale, 2)
            y2 = round(y * scale, 2)
            # Convert back to approximate RGB
            k2 = k  # keep K channel
            r2 = int(round(255 * (1 - c2 / 100) * (1 - k2 / 100)))
            g2 = int(round(255 * (1 - m2 / 100) * (1 - k2 / 100)))
            b2 = int(round(255 * (1 - y2 / 100) * (1 - k2 / 100)))
            r, g, b = (
                max(0, min(255, r2)),
                max(0, min(255, g2)),
                max(0, min(255, b2)),
            )
            changes.append(
                f"Reduced ink density from {density:.1f}% → "
                f"≤{MAX_INK_DENSITY}% on RGB({r},{g},{b})."
            )
            modified = True

        # 3. Shadow crush fix
        if not modified:
            c, m, y, k = rgb_to_cmyk(r, g, b)
            density = calculate_ink_density(c, m, y, k)
        else:
            c, m, y, k = rgb_to_cmyk(r, g, b)
            density = calculate_ink_density(c, m, y, k)

        if density > SHADOW_CRUSH_THRESHOLD:
            # Lighten slightly
            lighten = 1.15
            r = max(0, min(255, int(round(r * lighten))))
            g = max(0, min(255, int(round(g * lighten))))
            b = max(0, min(255, int(round(b * lighten))))
            changes.append(
                f"Lightened dark colour to avoid shadow crush → "
                f"RGB({r},{g},{b})."
            )

        adjusted.append((r, g, b))

    return {
        "adjusted_colors": adjusted,
        "changes_made": changes,
        "original_colors": [tuple(c[:3]) for c in dominant if len(c) >= 3],
    }
