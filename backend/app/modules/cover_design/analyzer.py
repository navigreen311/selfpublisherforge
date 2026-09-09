"""Competitor cover analysis module.

Analyses competitor covers to extract dominant colours, text placement,
imagery style, and provides recommendations for a given niche.
"""

from __future__ import annotations

import io
import logging
import math
from collections import Counter
from typing import Any, TypedDict

import httpx
from PIL import Image, ImageStat

from app.modules.cover_design.schemas import (
    ColorAnalysis,
    CompetitorAnalysisResponse,
    CompetitorCoverAnalysis,
    CoverGenre,
)

logger = logging.getLogger(__name__)

_IMAGE_DOWNLOAD_TIMEOUT = 15.0  # seconds
_QUANTIZE_COLOUR_COUNT = 8  # max dominant colours to extract
_ANALYSIS_THUMBNAIL_SIZE = (150, 150)  # resize target for fast processing


# ---------------------------------------------------------------------------
# Type definitions for enhanced analysis
# ---------------------------------------------------------------------------


class CoverData(TypedDict, total=False):
    """Structured data for a single competitor cover."""

    title: str
    cover_url: str
    bsr: int | None  # Best Seller Rank
    dominant_colors: list[ColorAnalysis]
    brightness: float
    contrast: float
    mood: str


class TypographyPattern(TypedDict):
    """Typography pattern analysis."""

    serif_percentage: float
    sans_serif_percentage: float
    bold_percentage: float
    light_percentage: float
    script_percentage: float


class LayoutPattern(TypedDict):
    """Layout pattern analysis."""

    centered_title_percentage: float
    top_title_percentage: float
    bottom_title_percentage: float
    image_placement: dict[str, float]  # 'top', 'center', 'bottom', 'full'


class ImageStyleBreakdown(TypedDict):
    """Image style breakdown."""

    photography_percentage: float
    illustration_percentage: float
    abstract_percentage: float
    typography_only_percentage: float


class GenreAnalysisResult(TypedDict):
    """Complete analysis result for analyze_genre_covers."""

    top_covers: list[CoverData]
    dominant_colors: list[dict[str, Any]]  # Color name and percentage
    typography_patterns: TypographyPattern
    layout_patterns: LayoutPattern
    image_style_breakdown: ImageStyleBreakdown
    ai_recommendations: list[str]
    sample_size: int


class CoverGeneratorPresets(TypedDict):
    """Pre-filled form data for cover generator."""

    color_palette: list[str]
    style_keywords: list[str]
    mood: str
    typography_recommendation: str
    layout_recommendation: str
    additional_instructions: str


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
    except (httpx.HTTPError, OSError, Image.UnidentifiedImageError) as exc:
        logger.exception("Failed to download cover image %s: %s", image_url, exc)
        return CompetitorCoverAnalysis(
            image_url=image_url,
            dominant_colors=[],
            overall_mood="Unable to analyse — image download failed",
            effectiveness_score=0.0,
        )

    try:
        dominant_colors = _extract_dominant_colors(img)
        brightness = _compute_brightness(img)
        contrast = _compute_contrast(img)
        mood = _infer_mood_from_image(brightness, contrast)
    except (ValueError, TypeError, OSError, IndexError) as exc:
        logger.exception("Failed to process cover image %s: %s", image_url, exc)
        return CompetitorCoverAnalysis(
            image_url=image_url,
            dominant_colors=[],
            overall_mood="Unable to analyse — image processing failed",
            effectiveness_score=0.0,
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
                    "Competitors have strong covers — ensure your design is equally " "polished to compete effectively."
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

# ---------------------------------------------------------------------------
# Enhanced Genre Cover Analysis
# ---------------------------------------------------------------------------


async def analyze_genre_covers(
    genre: CoverGenre,
    subcategory: str | None = None,
    cover_data_list: list[dict[str, Any]] | None = None,
) -> GenreAnalysisResult:
    """Analyze top competitor covers in a genre/subcategory and return structured design patterns.

    This function provides comprehensive analysis including:
    - Top 20 cover data with BSR rankings
    - Dominant colors with percentages
    - Typography patterns (serif vs sans-serif, bold vs light, etc.)
    - Layout patterns (title placement, image positioning)
    - Image style breakdown (photography, illustration, etc.)
    - AI-generated recommendations customized to the genre

    Parameters
    ----------
    genre:
        The target genre to analyze.
    subcategory:
        Optional subcategory within the genre for more targeted analysis.
    cover_data_list:
        Optional list of cover data dicts with keys: title, cover_url, bsr.
        If not provided, simulated data will be generated (placeholder for future API integration).

    Returns
    -------
    GenreAnalysisResult:
        Structured analysis results with all design pattern data.
    """
    # If no cover data provided, use placeholder (in production, this would fetch from Amazon API)
    if not cover_data_list:
        logger.info(
            "No cover data provided for %s%s — using simulated data. "
            "In production, this would integrate with Amazon Product Advertising API.",
            genre,
            f" / {subcategory}" if subcategory else "",
        )
        cover_data_list = _generate_placeholder_cover_data(genre, subcategory)

    # Limit to top 20
    cover_data_list = cover_data_list[:20]

    # Analyze each cover image
    analyzed_covers: list[CoverData] = []
    all_colors: dict[str, float] = {}

    for cover_info in cover_data_list:
        cover_url = cover_info.get("cover_url", "")
        if not cover_url:
            continue

        try:
            img = await _download_image(cover_url)
            dominant_colors = _extract_dominant_colors(img)
            brightness = _compute_brightness(img)
            contrast = _compute_contrast(img)
            mood = _infer_mood_from_image(brightness, contrast)

            cover_data: CoverData = {
                "title": cover_info.get("title", "Unknown"),
                "cover_url": cover_url,
                "bsr": cover_info.get("bsr"),
                "dominant_colors": dominant_colors,
                "brightness": brightness,
                "contrast": contrast,
                "mood": mood,
            }
            analyzed_covers.append(cover_data)

            # Aggregate colors
            for color in dominant_colors:
                color_name = color.name or color.hex_code
                all_colors[color_name] = all_colors.get(color_name, 0) + color.percentage

        except (httpx.HTTPError, OSError, Image.UnidentifiedImageError, ValueError, TypeError) as exc:
            logger.warning("Failed to analyze cover %s: %s", cover_url, exc)
            continue

    # Calculate dominant colors across all covers
    total_color_weight = sum(all_colors.values()) or 1.0
    dominant_colors_result = [
        {"name": name, "percentage": round((weight / total_color_weight) * 100, 1)}
        for name, weight in sorted(all_colors.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Analyze typography patterns (placeholder - requires vision model in production)
    typography_patterns = _analyze_typography_patterns(analyzed_covers, genre)

    # Analyze layout patterns (placeholder - requires vision model in production)
    layout_patterns = _analyze_layout_patterns(analyzed_covers, genre)

    # Analyze image style breakdown (placeholder - requires vision model in production)
    image_style_breakdown = _analyze_image_styles(analyzed_covers, genre)

    # Generate AI recommendations
    ai_recommendations = _generate_ai_recommendations(
        genre=genre,
        subcategory=subcategory,
        analyzed_covers=analyzed_covers,
        dominant_colors=dominant_colors_result,
        typography_patterns=typography_patterns,
        layout_patterns=layout_patterns,
        image_style_breakdown=image_style_breakdown,
    )

    return GenreAnalysisResult(
        top_covers=analyzed_covers,
        dominant_colors=dominant_colors_result,
        typography_patterns=typography_patterns,
        layout_patterns=layout_patterns,
        image_style_breakdown=image_style_breakdown,
        ai_recommendations=ai_recommendations,
        sample_size=len(analyzed_covers),
    )


def _generate_placeholder_cover_data(genre: CoverGenre, subcategory: str | None) -> list[dict[str, Any]]:
    """Generate placeholder cover data for testing (replace with real API in production)."""
    # In production, this would call Amazon Product Advertising API or scrape bestseller lists
    logger.info("Generating placeholder data for %s%s", genre, f" / {subcategory}" if subcategory else "")
    return []


def _analyze_typography_patterns(covers: list[CoverData], genre: CoverGenre) -> TypographyPattern:
    """Analyze typography patterns across covers.

    Note: This is a placeholder implementation. In production, this would use
    a vision model to detect font styles from cover images.
    """
    # Genre-based heuristics (placeholder)
    if genre == CoverGenre.ROMANCE:
        return TypographyPattern(
            serif_percentage=25.0,
            sans_serif_percentage=30.0,
            bold_percentage=40.0,
            light_percentage=35.0,
            script_percentage=45.0,
        )
    if genre == CoverGenre.THRILLER:
        return TypographyPattern(
            serif_percentage=20.0,
            sans_serif_percentage=75.0,
            bold_percentage=80.0,
            light_percentage=10.0,
            script_percentage=5.0,
        )
    if genre == CoverGenre.FANTASY:
        return TypographyPattern(
            serif_percentage=60.0,
            sans_serif_percentage=30.0,
            bold_percentage=50.0,
            light_percentage=25.0,
            script_percentage=15.0,
        )
    return TypographyPattern(
        serif_percentage=40.0,
        sans_serif_percentage=50.0,
        bold_percentage=45.0,
        light_percentage=30.0,
        script_percentage=10.0,
    )


def _analyze_layout_patterns(covers: list[CoverData], genre: CoverGenre) -> LayoutPattern:
    """Analyze layout patterns across covers.

    Note: This is a placeholder implementation. In production, this would use
    a vision model to detect layout elements from cover images.
    """
    # Genre-based heuristics (placeholder)
    if genre == CoverGenre.THRILLER:
        return LayoutPattern(
            centered_title_percentage=45.0,
            top_title_percentage=40.0,
            bottom_title_percentage=15.0,
            image_placement={"full": 60.0, "top": 15.0, "center": 20.0, "bottom": 5.0},
        )
    if genre == CoverGenre.ROMANCE:
        return LayoutPattern(
            centered_title_percentage=55.0,
            top_title_percentage=25.0,
            bottom_title_percentage=20.0,
            image_placement={"full": 50.0, "center": 35.0, "top": 10.0, "bottom": 5.0},
        )
    return LayoutPattern(
        centered_title_percentage=50.0,
        top_title_percentage=30.0,
        bottom_title_percentage=20.0,
        image_placement={"full": 45.0, "center": 30.0, "top": 15.0, "bottom": 10.0},
    )


def _analyze_image_styles(covers: list[CoverData], genre: CoverGenre) -> ImageStyleBreakdown:
    """Analyze image style breakdown across covers.

    Note: This is a placeholder implementation. In production, this would use
    a vision model to classify image styles.
    """
    # Genre-based heuristics (placeholder)
    if genre == CoverGenre.ROMANCE:
        return ImageStyleBreakdown(
            photography_percentage=65.0,
            illustration_percentage=25.0,
            abstract_percentage=5.0,
            typography_only_percentage=5.0,
        )
    if genre == CoverGenre.FANTASY:
        return ImageStyleBreakdown(
            photography_percentage=15.0,
            illustration_percentage=75.0,
            abstract_percentage=5.0,
            typography_only_percentage=5.0,
        )
    if genre == CoverGenre.NONFICTION:
        return ImageStyleBreakdown(
            photography_percentage=30.0,
            illustration_percentage=20.0,
            abstract_percentage=25.0,
            typography_only_percentage=25.0,
        )
    return ImageStyleBreakdown(
        photography_percentage=45.0,
        illustration_percentage=35.0,
        abstract_percentage=10.0,
        typography_only_percentage=10.0,
    )


def _generate_ai_recommendations(
    genre: CoverGenre,
    subcategory: str | None,
    analyzed_covers: list[CoverData],
    dominant_colors: list[dict[str, Any]],
    typography_patterns: TypographyPattern,
    layout_patterns: LayoutPattern,
    image_style_breakdown: ImageStyleBreakdown,
) -> list[str]:
    """Generate AI-powered recommendations customized to the genre and analysis data."""
    recommendations: list[str] = []

    # Genre-specific baseline
    genre_base = _GENRE_RECOMMENDATIONS.get(genre, [])
    recommendations.extend(genre_base)

    # Color-based recommendations
    if dominant_colors:
        top_color = dominant_colors[0]["name"]
        recommendations.append(
            f"Top competitors heavily use {top_color} ({dominant_colors[0]['percentage']}% prevalence). "
            "Consider using this as your primary or accent color to align with genre expectations."
        )

    # Typography recommendations
    if typography_patterns["script_percentage"] > 40:
        recommendations.append(
            f"Script fonts are prevalent ({typography_patterns['script_percentage']}%) in this genre. "
            "Consider elegant script for titles to signal the genre instantly."
        )
    elif typography_patterns["sans_serif_percentage"] > 60:
        recommendations.append(
            f"Sans-serif fonts dominate ({typography_patterns['sans_serif_percentage']}%) in this genre. "
            "Use bold, clean sans-serif typography for maximum impact."
        )

    if typography_patterns["bold_percentage"] > 70:
        recommendations.append(
            "Bold typography is the norm (70%+). Ensure your title font has strong weight for thumbnail visibility."
        )

    # Layout recommendations
    max_placement = max(layout_patterns["image_placement"].items(), key=lambda x: x[1])
    recommendations.append(
        f"Image placement trend: {max_placement[1]}% use '{max_placement[0]}' placement. "
        "Match this pattern for genre consistency."
    )

    # Image style recommendations
    if image_style_breakdown["photography_percentage"] > 50:
        recommendations.append(
            f"Photography dominates ({image_style_breakdown['photography_percentage']}%). "
            "Use high-quality photographic elements for authenticity."
        )
    elif image_style_breakdown["illustration_percentage"] > 50:
        recommendations.append(
            f"Illustration is the preferred style ({image_style_breakdown['illustration_percentage']}%). "
            "Commission or generate illustrated artwork for genre alignment."
        )

    # Mood-based recommendations from analyzed covers
    if analyzed_covers:
        moods = [c.get("mood", "") for c in analyzed_covers if c.get("mood")]
        if moods:
            dark_count = sum(1 for m in moods if "Dark" in m)
            if dark_count > len(moods) * 0.6:
                recommendations.append(
                    "Majority of top covers use dark, moody aesthetics. Consider a darker color palette for impact."
                )

    # Subcategory-specific recommendation
    if subcategory:
        recommendations.append(
            f"Subcategory '{subcategory}' may have unique conventions. "
            "Review top-10 covers closely to identify niche-specific patterns."
        )

    return recommendations


# ---------------------------------------------------------------------------
# Cover Generator Preset Builder
# ---------------------------------------------------------------------------


def generate_cover_from_insights(
    genre: CoverGenre,
    analysis: GenreAnalysisResult,
) -> CoverGeneratorPresets:
    """Pre-fill cover generator form with competitive insights from analysis.

    Takes the structured analysis result and converts it into actionable
    form presets that can be used to initialize the cover generator.

    Parameters
    ----------
    genre:
        The target genre.
    analysis:
        The result from analyze_genre_covers.

    Returns
    -------
    CoverGeneratorPresets:
        Pre-filled form data including color palette, style keywords, mood,
        typography and layout recommendations, and additional instructions.
    """
    # Extract top colors as hex codes
    color_palette: list[str] = []
    for color_data in analysis["dominant_colors"][:5]:
        # Try to find hex code from analyzed covers
        color_name = color_data["name"]
        # Look up hex from named colors (reverse lookup)
        hex_code = next(
            (hex_val for hex_val, name in _NAMED_COLOURS.items() if name == color_name),
            "#000000",
        )
        color_palette.append(hex_code)

    # Build style keywords based on image style breakdown
    style_keywords: list[str] = []
    styles = analysis["image_style_breakdown"]
    if styles["photography_percentage"] > 40:
        style_keywords.extend(["photographic", "realistic", "professional photography"])
    if styles["illustration_percentage"] > 40:
        style_keywords.extend(["illustrated", "artistic", "hand-drawn"])
    if styles["abstract_percentage"] > 20:
        style_keywords.extend(["abstract", "geometric", "modern"])
    if styles["typography_only_percentage"] > 20:
        style_keywords.append("typography-focused")

    # Add genre-specific keywords
    if genre == CoverGenre.THRILLER:
        style_keywords.extend(["dramatic", "suspenseful", "cinematic"])
    elif genre == CoverGenre.ROMANCE:
        style_keywords.extend(["romantic", "elegant", "dreamy"])
    elif genre == CoverGenre.FANTASY:
        style_keywords.extend(["epic", "magical", "ornate"])
    elif genre == CoverGenre.SCI_FI:
        style_keywords.extend(["futuristic", "technological", "cosmic"])

    # Determine mood from analyzed covers
    mood_descriptors: list[str] = []
    if analysis["top_covers"]:
        moods = [c.get("mood", "") for c in analysis["top_covers"] if c.get("mood")]
        if moods:
            # Count mood patterns
            dark_count = sum(1 for m in moods if "Dark" in m)
            bright_count = sum(1 for m in moods if "Bright" in m)
            contrast_count = sum(1 for m in moods if "high-contrast" in m)

            if dark_count > len(moods) * 0.5:
                mood_descriptors.append("dark")
            if bright_count > len(moods) * 0.5:
                mood_descriptors.append("bright")
            if contrast_count > len(moods) * 0.5:
                mood_descriptors.append("high-contrast")

    mood = ", ".join(mood_descriptors) if mood_descriptors else "balanced"

    # Typography recommendation
    typo = analysis["typography_patterns"]
    typo_rec_parts: list[str] = []
    if typo["script_percentage"] > 40:
        typo_rec_parts.append("Use elegant script font for title")
    elif typo["sans_serif_percentage"] > 60:
        typo_rec_parts.append("Use bold sans-serif font for title")
    elif typo["serif_percentage"] > 50:
        typo_rec_parts.append("Use classic serif font for title")

    if typo["bold_percentage"] > 70:
        typo_rec_parts.append("Heavy font weight recommended")

    typography_recommendation = "; ".join(typo_rec_parts)

    # Layout recommendation
    layout = analysis["layout_patterns"]
    max_title_pos = max(
        [
            ("centered", layout["centered_title_percentage"]),
            ("top", layout["top_title_percentage"]),
            ("bottom", layout["bottom_title_percentage"]),
        ],
        key=lambda x: x[1],
    )
    max_image_pos = max(layout["image_placement"].items(), key=lambda x: x[1])

    layout_recommendation = (
        f"Title placement: {max_title_pos[0]} ({max_title_pos[1]}%); "
        f"Image: {max_image_pos[0]} ({max_image_pos[1]}%)"
    )

    # Additional instructions from AI recommendations
    top_recommendations = analysis["ai_recommendations"][:3]
    additional_instructions = "\n".join(f"- {rec}" for rec in top_recommendations)

    return CoverGeneratorPresets(
        color_palette=color_palette,
        style_keywords=style_keywords[:10],  # Limit to 10
        mood=mood,
        typography_recommendation=typography_recommendation,
        layout_recommendation=layout_recommendation,
        additional_instructions=additional_instructions,
    )
