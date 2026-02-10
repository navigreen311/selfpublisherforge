"""Competitor cover analysis module.

Analyses competitor covers to extract dominant colours, text placement,
imagery style, and provides recommendations for a given niche.
"""
from __future__ import annotations

import io
import logging
import math
from collections import Counter
from typing import Any

import httpx
from PIL import Image, ImageStat

from app.modules.cover_design.schemas import (
    ColorAnalysis,
    CompetitorCoverAnalysis,
    CompetitorAnalysisResponse,
    CoverGenre,
)

logger = logging.getLogger(__name__)

_IMAGE_DOWNLOAD_TIMEOUT = 15.0  # seconds
_QUANTIZE_COLOUR_COUNT = 8  # max dominant colours to extract
_ANALYSIS_THUMBNAIL_SIZE = (150, 150)  # resize target for fast processing


# ---------------------------------------------------------------------------
# Named colour lookup
# ---------------------------------------------------------------------------

_NAMED_COLOURS: dict[str, str] = {
    "#000000": "Black",
    "#FFFFFF": "White",
    "#FF0000": "Red",
    "#00FF00": "Green",
    "#0000FF": "Blue",
    "#FFD700": "Gold",
    "#800020": "Burgundy",
    "#1B1B3A": "Dark Navy",
    "#2C3E50": "Charcoal",
    "#E74C3C": "Crimson",
    "#3498DB": "Sky Blue",
    "#2ECC71": "Emerald",
    "#F39C12": "Amber",
    "#9B59B6": "Purple",
    "#1ABC9C": "Teal",
}


def _closest_named_colour(hex_code: str) -> str | None:
    """Return the closest named colour using Euclidean distance in RGB space."""
    exact = _NAMED_COLOURS.get(hex_code.upper())
    if exact:
        return exact

    try:
        r1 = int(hex_code[1:3], 16)
        g1 = int(hex_code[3:5], 16)
        b1 = int(hex_code[5:7], 16)
    except (ValueError, IndexError):
        return None

    best_name: str | None = None
    best_dist = float("inf")
    for ref_hex, name in _NAMED_COLOURS.items():
        r2 = int(ref_hex[1:3], 16)
        g2 = int(ref_hex[3:5], 16)
        b2 = int(ref_hex[5:7], 16)
        dist = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
        if dist < best_dist:
            best_dist = dist
            best_name = name

    # Only assign a name if the colour is reasonably close (threshold ~80 in RGB space)
    if best_dist <= 80:
        return best_name
    return None


# ---------------------------------------------------------------------------
# Image downloading
# ---------------------------------------------------------------------------


async def _download_image(url: str) -> Image.Image:
    """Download an image from *url* and return a PIL Image.

    Raises ``httpx.HTTPStatusError`` on non-2xx responses and
    ``PIL.UnidentifiedImageError`` if the payload is not a valid image.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=_IMAGE_DOWNLOAD_TIMEOUT) as client:
        response = await client.get(url)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))


# ---------------------------------------------------------------------------
# Colour extraction helpers
# ---------------------------------------------------------------------------


def _extract_dominant_colors(img: Image.Image, max_colors: int = _QUANTIZE_COLOUR_COUNT) -> list[ColorAnalysis]:
    """Extract dominant colours from a PIL Image using quantization.

    The image is resized to a small thumbnail first to speed up processing,
    then quantized to *max_colors* colours.  The pixel frequency of each
    quantized colour is converted to a percentage.
    """
    # Work on a small copy in RGB mode
    working = img.copy()
    working = working.convert("RGB")
    working.thumbnail(_ANALYSIS_THUMBNAIL_SIZE)

    # Quantize to a limited palette
    quantized = working.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()
    if palette_data is None:
        return []

    # Count pixel frequencies per palette index
    pixel_counts: Counter[int] = Counter(quantized.getdata())
    total_pixels = sum(pixel_counts.values()) or 1

    colors: list[ColorAnalysis] = []
    for index, count in pixel_counts.most_common(max_colors):
        r = palette_data[index * 3]
        g = palette_data[index * 3 + 1]
        b = palette_data[index * 3 + 2]
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        percentage = round((count / total_pixels) * 100, 1)
        name = _closest_named_colour(hex_code)
        colors.append(ColorAnalysis(hex_code=hex_code, percentage=percentage, name=name))

    return colors


def _compute_brightness(img: Image.Image) -> float:
    """Return perceived brightness (0-255) of the image."""
    grey = img.convert("L")
    stat = ImageStat.Stat(grey)
    return stat.mean[0]


def _compute_contrast(img: Image.Image) -> float:
    """Return the standard deviation of luminance as a simple contrast metric."""
    grey = img.convert("L")
    stat = ImageStat.Stat(grey)
    return stat.stddev[0]


def _infer_mood_from_image(brightness: float, contrast: float) -> str:
    """Infer a coarse mood descriptor from brightness and contrast values."""
    if brightness < 80:
        mood = "Dark"
    elif brightness < 160:
        mood = "Balanced"
    else:
        mood = "Bright"

    if contrast > 70:
        mood += ", high-contrast"
    elif contrast < 35:
        mood += ", muted"

    return mood


# ---------------------------------------------------------------------------
# Single-cover analysis
# ---------------------------------------------------------------------------


async def analyze_single_cover(
    image_url: str,
) -> CompetitorCoverAnalysis:
    """Analyse a single competitor cover image.

    Downloads the image, extracts dominant colours, brightness, contrast,
    and infers a basic mood from the image data.  If the image cannot be
    downloaded or processed, a partial result with error information is
    returned instead of raising.
    """
    try:
        img = await _download_image(image_url)
    except Exception:
        logger.exception("Failed to download cover image: %s", image_url)
        return CompetitorCoverAnalysis(
            image_url=image_url,
            dominant_colors=[],
            overall_mood="Unable to analyse — image download failed",
        )

    try:
        dominant_colors = _extract_dominant_colors(img)
        brightness = _compute_brightness(img)
        contrast = _compute_contrast(img)
        mood = _infer_mood_from_image(brightness, contrast)
    except Exception:
        logger.exception("Failed to process cover image: %s", image_url)
        return CompetitorCoverAnalysis(
            image_url=image_url,
            dominant_colors=[],
            overall_mood="Unable to analyse — image processing failed",
        )

    return CompetitorCoverAnalysis(
        image_url=image_url,
        dominant_colors=dominant_colors,
        text_placement=None,  # requires vision-model analysis
        imagery_style=None,  # requires vision-model analysis
        overall_mood=mood,
        font_style=None,  # requires vision-model analysis
        effectiveness_score=None,  # requires vision-model analysis
    )


# ---------------------------------------------------------------------------
# Batch analysis + recommendations
# ---------------------------------------------------------------------------


async def analyze_competitor_covers(
    genre: CoverGenre,
    niche_keywords: list[str],
    image_urls: list[str] | None = None,
    max_results: int = 10,
) -> CompetitorAnalysisResponse:
    """Analyse multiple competitor covers and synthesise recommendations.

    Parameters
    ----------
    genre:
        The target genre.
    niche_keywords:
        Keywords describing the specific niche.
    image_urls:
        Optional list of competitor cover image URLs to analyse directly.
    max_results:
        Max covers to analyse (if doing automated search).
    """
    analyses: list[CompetitorCoverAnalysis] = []

    if image_urls:
        for url in image_urls[:max_results]:
            analysis = await analyze_single_cover(url)
            analyses.append(analysis)
    else:
        logger.info(
            "No image URLs provided for %s / %s — automated cover search is not yet available.",
            genre,
            niche_keywords,
        )

    # Synthesise trends and recommendations
    trends = _synthesise_trends(analyses, genre)
    recommendations = _generate_recommendations(analyses, genre, niche_keywords)

    return CompetitorAnalysisResponse(
        genre=genre,
        niche_keywords=niche_keywords,
        analyses=analyses,
        trends=trends,
        recommendations=recommendations,
    )


def _synthesise_trends(
    analyses: list[CompetitorCoverAnalysis],
    genre: CoverGenre,
) -> dict[str, Any]:
    """Extract aggregate trends from multiple cover analyses."""
    if not analyses:
        return {}

    # Collect all colours
    all_colours: dict[str, float] = {}
    mood_counts: dict[str, int] = {}
    style_counts: dict[str, int] = {}

    for a in analyses:
        for c in a.dominant_colors:
            name = c.name or c.hex_code
            all_colours[name] = all_colours.get(name, 0) + c.percentage

        if a.overall_mood:
            mood_counts[a.overall_mood] = mood_counts.get(a.overall_mood, 0) + 1
        if a.imagery_style:
            style_counts[a.imagery_style] = style_counts.get(a.imagery_style, 0) + 1

    # Normalise colour percentages
    total = sum(all_colours.values()) or 1.0
    top_colours = sorted(all_colours.items(), key=lambda x: x[1], reverse=True)[:5]

    avg_score = None
    scores = [a.effectiveness_score for a in analyses if a.effectiveness_score is not None]
    if scores:
        avg_score = round(sum(scores) / len(scores), 1)

    return {
        "dominant_colours": [{"name": name, "weight": round(pct / total * 100, 1)} for name, pct in top_colours],
        "common_moods": sorted(mood_counts, key=mood_counts.get, reverse=True),  # type: ignore[arg-type]
        "common_styles": sorted(style_counts, key=style_counts.get, reverse=True),  # type: ignore[arg-type]
        "average_effectiveness": avg_score,
        "sample_size": len(analyses),
    }


def _generate_recommendations(
    analyses: list[CompetitorCoverAnalysis],
    genre: CoverGenre,
    niche_keywords: list[str],
) -> list[str]:
    """Generate actionable recommendations based on the analysis."""
    recommendations: list[str] = []

    # Genre-specific base recommendations
    genre_tips = _GENRE_RECOMMENDATIONS.get(genre, [])
    recommendations.extend(genre_tips)

    # Data-driven recommendations
    if analyses:
        scores = [a.effectiveness_score for a in analyses if a.effectiveness_score is not None]
        if scores:
            avg = sum(scores) / len(scores)
            if avg < 5:
                recommendations.append(
                    "Competitor covers score below average — there is an opportunity "
                    "to stand out with a polished, professional design."
                )
            elif avg > 7:
                recommendations.append(
                    "Competitors have strong covers — ensure your design is equally "
                    "polished to compete effectively."
                )

    recommendations.append(
        f"Target keywords: {', '.join(niche_keywords)}. "
        "Ensure your cover visually communicates these themes at thumbnail size."
    )

    return recommendations


_GENRE_RECOMMENDATIONS: dict[CoverGenre, list[str]] = {
    CoverGenre.ROMANCE: [
        "Use warm, inviting colours — pinks, reds, golds, and warm neutrals.",
        "Elegant script fonts for the title help signal the romance genre.",
        "Ensure the design is appealing at thumbnail size on mobile devices.",
    ],
    CoverGenre.THRILLER: [
        "Use high-contrast, dark designs with bold sans-serif typography.",
        "A single, striking focal element draws the eye at thumbnail size.",
        "Desaturated or monochrome palettes with one accent colour work well.",
    ],
    CoverGenre.MYSTERY: [
        "Create intrigue with partial reveals, shadows, or silhouettes.",
        "Muted or noir palettes set the right tone for mystery readers.",
    ],
    CoverGenre.SCI_FI: [
        "Cool blues, purples, and neon accents signal science fiction.",
        "Futuristic or geometric typography reinforces the genre.",
    ],
    CoverGenre.FANTASY: [
        "Rich, saturated colours and ornate details appeal to fantasy readers.",
        "Consider an illustrated style — it performs well in fantasy niches.",
    ],
    CoverGenre.NONFICTION: [
        "Keep the design clean and authoritative. Strong title typography is key.",
        "Use solid or gradient backgrounds to project professionalism.",
    ],
    CoverGenre.CHILDRENS: [
        "Bright, primary colours and illustrated characters are essential.",
        "The title font should be large, playful, and highly readable.",
    ],
}
