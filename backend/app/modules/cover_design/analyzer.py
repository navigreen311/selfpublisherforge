"""Competitor cover analysis module.

Analyses competitor covers to extract dominant colours, text placement,
imagery style, and provides recommendations for a given niche.
"""
from __future__ import annotations

import logging
from typing import Any

from app.modules.cover_design.schemas import (
    ColorAnalysis,
    CompetitorCoverAnalysis,
    CompetitorAnalysisResponse,
    CoverGenre,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Named colour lookup (simplified)
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
    """Return the closest named colour (very simplified lookup)."""
    return _NAMED_COLOURS.get(hex_code.upper())


# ---------------------------------------------------------------------------
# Single-cover analysis
# ---------------------------------------------------------------------------


async def analyze_single_cover(
    image_url: str,
) -> CompetitorCoverAnalysis:
    """Analyse a single competitor cover image.

    In production this would:
    1. Download the image
    2. Use Pillow/OpenCV for colour extraction
    3. Optionally call a vision LLM (GPT-4V / Claude) for text placement
       and imagery-style analysis

    For now we return a structured placeholder that demonstrates the schema.
    """
    # Placeholder colour analysis
    dominant_colors = [
        ColorAnalysis(hex_code="#1B1B3A", percentage=40.0, name="Dark Navy"),
        ColorAnalysis(hex_code="#FFD700", percentage=25.0, name="Gold"),
        ColorAnalysis(hex_code="#FFFFFF", percentage=20.0, name="White"),
        ColorAnalysis(hex_code="#2C3E50", percentage=15.0, name="Charcoal"),
    ]

    return CompetitorCoverAnalysis(
        image_url=image_url,
        dominant_colors=dominant_colors,
        text_placement="Title centred upper third, author name bottom centre",
        imagery_style="Photographic with overlay filter",
        overall_mood="Dark, dramatic, professional",
        font_style="Bold sans-serif title, light serif author name",
        effectiveness_score=7.5,
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
        # Placeholder: in production we would search for covers in this niche
        logger.info(
            "No image URLs provided; generating placeholder analysis for %s / %s",
            genre,
            niche_keywords,
        )
        analyses.append(
            CompetitorCoverAnalysis(
                image_url=None,
                dominant_colors=[
                    ColorAnalysis(hex_code="#1B1B3A", percentage=35.0, name="Dark Navy"),
                    ColorAnalysis(hex_code="#E74C3C", percentage=30.0, name="Crimson"),
                    ColorAnalysis(hex_code="#FFFFFF", percentage=20.0, name="White"),
                    ColorAnalysis(hex_code="#000000", percentage=15.0, name="Black"),
                ],
                text_placement="Title upper third, centred",
                imagery_style="Mixed photographic and illustrated",
                overall_mood="Dramatic",
                font_style="Bold display fonts",
                effectiveness_score=7.0,
            )
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
