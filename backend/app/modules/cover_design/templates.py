"""Built-in cover templates organised by genre.

Each template includes dimension specs, font recommendations, and layout guidance
for common self-publishing platforms.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.cover_design.schemas import CoverDimensions, CoverGenre, CoverPlatform

# ---------------------------------------------------------------------------
# Platform dimension presets
# ---------------------------------------------------------------------------

PLATFORM_DIMENSIONS: dict[CoverPlatform, CoverDimensions] = {
    CoverPlatform.AMAZON_KDP: CoverDimensions(width_px=1600, height_px=2560, dpi=300, bleed_px=38),
    CoverPlatform.INGRAM_SPARK: CoverDimensions(width_px=1800, height_px=2700, dpi=300, bleed_px=38),
    CoverPlatform.BARNES_NOBLE: CoverDimensions(width_px=1400, height_px=2100, dpi=300, bleed_px=0),
    CoverPlatform.APPLE_BOOKS: CoverDimensions(width_px=1400, height_px=2100, dpi=300, bleed_px=0),
    CoverPlatform.GOOGLE_PLAY: CoverDimensions(width_px=1280, height_px=1920, dpi=300, bleed_px=0),
    CoverPlatform.CUSTOM: CoverDimensions(width_px=1600, height_px=2560, dpi=300, bleed_px=0),
}


# ---------------------------------------------------------------------------
# Template dataclass
# ---------------------------------------------------------------------------


@dataclass
class CoverTemplate:
    id: str
    name: str
    genre: CoverGenre
    description: str
    thumbnail_url: str | None = None
    dimensions: CoverDimensions = field(
        default_factory=lambda: PLATFORM_DIMENSIONS[CoverPlatform.AMAZON_KDP]
    )
    font_recommendations: list[str] = field(default_factory=list)
    layout_guidance: str = ""
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Template library
# ---------------------------------------------------------------------------

TEMPLATES: list[CoverTemplate] = [
    # Romance
    CoverTemplate(
        id="romance-classic",
        name="Classic Romance",
        genre=CoverGenre.ROMANCE,
        description="Warm colour palette with elegant script fonts. Central couple silhouette or scenic background.",
        font_recommendations=["Playfair Display", "Great Vibes", "Cormorant Garamond"],
        layout_guidance="Title in decorative script at top third, author name at bottom. Warm overlay filter.",
        tags=["romance", "contemporary", "warm", "elegant"],
    ),
    CoverTemplate(
        id="romance-dark",
        name="Dark Romance",
        genre=CoverGenre.ROMANCE,
        description="Moody, dark background with bold contrasting title typography.",
        font_recommendations=["Didot", "Bodoni Moda", "Lora"],
        layout_guidance="Dark background, title in large serif centred vertically, subtle texture overlay.",
        tags=["romance", "dark", "moody", "bold"],
    ),
    # Thriller
    CoverTemplate(
        id="thriller-gritty",
        name="Gritty Thriller",
        genre=CoverGenre.THRILLER,
        description="High-contrast, desaturated imagery with bold sans-serif title.",
        font_recommendations=["Oswald", "Anton", "Impact"],
        layout_guidance="Full-bleed background image, large bold title upper third, tagline below. High contrast.",
        tags=["thriller", "gritty", "dark", "bold"],
    ),
    CoverTemplate(
        id="thriller-psychological",
        name="Psychological Thriller",
        genre=CoverGenre.THRILLER,
        description="Minimalist design with unsettling imagery and clean typography.",
        font_recommendations=["Montserrat", "Bebas Neue", "Raleway"],
        layout_guidance="Sparse, centred composition. Single focal element. Clean sans-serif title.",
        tags=["thriller", "psychological", "minimalist", "clean"],
    ),
    # Mystery
    CoverTemplate(
        id="mystery-cozy",
        name="Cozy Mystery",
        genre=CoverGenre.MYSTERY,
        description="Bright, illustrative style with playful fonts. Friendly and inviting.",
        font_recommendations=["Quicksand", "Fredoka One", "Poppins"],
        layout_guidance="Illustrated scene, bright palette, playful title font at top, author at bottom.",
        tags=["mystery", "cozy", "bright", "playful"],
    ),
    # Sci-Fi
    CoverTemplate(
        id="scifi-epic",
        name="Epic Sci-Fi",
        genre=CoverGenre.SCI_FI,
        description="Sweeping space vistas or futuristic cityscapes with modern fonts.",
        font_recommendations=["Orbitron", "Exo 2", "Rajdhani"],
        layout_guidance="Full-bleed sci-fi landscape, title in futuristic font at top, subtle glow effects.",
        tags=["sci-fi", "epic", "space", "futuristic"],
    ),
    CoverTemplate(
        id="scifi-cyberpunk",
        name="Cyberpunk",
        genre=CoverGenre.SCI_FI,
        description="Neon colours, dark backgrounds, glitch aesthetics.",
        font_recommendations=["Share Tech Mono", "Audiowide", "Press Start 2P"],
        layout_guidance="Dark background with neon accents. Glitch/distortion effects on title.",
        tags=["sci-fi", "cyberpunk", "neon", "glitch"],
    ),
    # Fantasy
    CoverTemplate(
        id="fantasy-epic",
        name="Epic Fantasy",
        genre=CoverGenre.FANTASY,
        description="Sweeping landscapes, ornate borders, medieval-inspired typography.",
        font_recommendations=["Cinzel", "Uncial Antiqua", "MedievalSharp"],
        layout_guidance="Full scene background, ornate border frame, title in medieval serif at top.",
        tags=["fantasy", "epic", "medieval", "ornate"],
    ),
    CoverTemplate(
        id="fantasy-urban",
        name="Urban Fantasy",
        genre=CoverGenre.FANTASY,
        description="Dark city backdrop with magical elements and bold modern fonts.",
        font_recommendations=["Cinzel Decorative", "Philosopher", "Spectral"],
        layout_guidance="City skyline with magical overlays, bold title centred.",
        tags=["fantasy", "urban", "dark", "magical"],
    ),
    # Horror
    CoverTemplate(
        id="horror-classic",
        name="Classic Horror",
        genre=CoverGenre.HORROR,
        description="Dark, atmospheric imagery with distressed or blood-style fonts.",
        font_recommendations=["Creepster", "Nosifer", "Eater"],
        layout_guidance="Very dark background, distressed title font, red accent colour. Minimal elements.",
        tags=["horror", "dark", "distressed", "atmospheric"],
    ),
    # Nonfiction
    CoverTemplate(
        id="nonfiction-professional",
        name="Professional Nonfiction",
        genre=CoverGenre.NONFICTION,
        description="Clean, authoritative design with strong typography. Bold title, subtle graphics.",
        font_recommendations=["Roboto Slab", "Merriweather", "Source Sans Pro"],
        layout_guidance="Solid or gradient background, large bold title centred, subtitle below, author at bottom.",
        tags=["nonfiction", "professional", "clean", "authoritative"],
    ),
    CoverTemplate(
        id="nonfiction-modern",
        name="Modern Nonfiction",
        genre=CoverGenre.NONFICTION,
        description="Bright colours, geometric shapes, contemporary sans-serif fonts.",
        font_recommendations=["Poppins", "Inter", "Work Sans"],
        layout_guidance="Bold colour blocks, geometric accents, sans-serif title, clean layout.",
        tags=["nonfiction", "modern", "bright", "geometric"],
    ),
    # Self-Help
    CoverTemplate(
        id="selfhelp-inspirational",
        name="Inspirational Self-Help",
        genre=CoverGenre.SELF_HELP,
        description="Uplifting colour palette, sunrise/nature imagery, motivational typography.",
        font_recommendations=["Lato", "Nunito", "Open Sans"],
        layout_guidance="Warm gradient or nature background, large inspirational title, clean layout.",
        tags=["self-help", "inspirational", "warm", "uplifting"],
    ),
    # Business
    CoverTemplate(
        id="business-executive",
        name="Executive Business",
        genre=CoverGenre.BUSINESS,
        description="Navy/charcoal palette, gold accents, authoritative serif fonts.",
        font_recommendations=["Libre Baskerville", "Playfair Display", "EB Garamond"],
        layout_guidance="Dark professional background, gold accent lines, serif title, clean grid layout.",
        tags=["business", "executive", "professional", "authoritative"],
    ),
    # Children's
    CoverTemplate(
        id="childrens-playful",
        name="Playful Children's",
        genre=CoverGenre.CHILDRENS,
        description="Bright, colourful illustration style with fun, rounded fonts.",
        font_recommendations=["Bubblegum Sans", "Comic Neue", "Baloo 2"],
        layout_guidance="Full illustration background, large playful title, bright primary colours.",
        tags=["childrens", "playful", "bright", "illustrated"],
    ),
    # Young Adult
    CoverTemplate(
        id="ya-contemporary",
        name="Contemporary YA",
        genre=CoverGenre.YOUNG_ADULT,
        description="Trendy, stylish design with bold colours and modern typography.",
        font_recommendations=["Josefin Sans", "Raleway", "Nunito Sans"],
        layout_guidance="Eye-catching composition, bold colours, modern sans-serif, centred layout.",
        tags=["young-adult", "contemporary", "trendy", "bold"],
    ),
    # Memoir
    CoverTemplate(
        id="memoir-personal",
        name="Personal Memoir",
        genre=CoverGenre.MEMOIR,
        description="Intimate, textured design with handwritten or personal-feeling fonts.",
        font_recommendations=["Caveat", "Dancing Script", "Sorts Mill Goudy"],
        layout_guidance="Textured paper background, handwritten-style title, personal photo or illustration.",
        tags=["memoir", "personal", "intimate", "textured"],
    ),
    # Cookbook
    CoverTemplate(
        id="cookbook-modern",
        name="Modern Cookbook",
        genre=CoverGenre.COOKBOOK,
        description="Clean layout with appetising food photography space and clean fonts.",
        font_recommendations=["Josefin Slab", "Amatic SC", "Sacramento"],
        layout_guidance="Large food photography area, clean title overlay, warm colour accents.",
        tags=["cookbook", "modern", "clean", "appetising"],
    ),
]

# Indexed for fast lookup
_TEMPLATES_BY_ID: dict[str, CoverTemplate] = {t.id: t for t in TEMPLATES}
_TEMPLATES_BY_GENRE: dict[CoverGenre, list[CoverTemplate]] = {}
for _t in TEMPLATES:
    _TEMPLATES_BY_GENRE.setdefault(_t.genre, []).append(_t)


def get_template_by_id(template_id: str) -> CoverTemplate | None:
    return _TEMPLATES_BY_ID.get(template_id)


def get_templates_by_genre(genre: CoverGenre) -> list[CoverTemplate]:
    return _TEMPLATES_BY_GENRE.get(genre, [])


def get_all_templates() -> list[CoverTemplate]:
    return list(TEMPLATES)


def get_dimensions_for_platform(platform: CoverPlatform) -> CoverDimensions:
    return PLATFORM_DIMENSIONS.get(platform, PLATFORM_DIMENSIONS[CoverPlatform.AMAZON_KDP])
