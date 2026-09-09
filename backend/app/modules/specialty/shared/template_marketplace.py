"""Template & Pack Marketplace.

Provides built-in page layouts, theme packs, and style packs for
specialty book creation.  All templates use non-trademarked names
and themes.

Blueprint refs: 6.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Template:
    """A marketplace template or pack."""

    id: str
    name: str
    category: str  # page_layout | theme_pack | style_pack
    book_type: str | None  # childrens | coloring | puzzle | None (universal)
    description: str
    preview_url: str | None
    config: dict[str, Any]
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

BUILT_IN_TEMPLATES: list[dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Page Layouts
    # -----------------------------------------------------------------------
    {
        "id": "layout-full-bleed",
        "name": "Full Bleed Illustration",
        "category": "page_layout",
        "book_type": "childrens",
        "description": "Full-page illustration with optional text overlay. "
        "Ideal for dramatic moments and wordless spreads.",
        "preview_url": None,
        "config": {
            "layout": "full_bleed",
            "text_overlay": True,
            "bleed": 0.125,
        },
        "tags": ["childrens", "illustration", "dramatic"],
    },
    {
        "id": "layout-top-image-bottom-text",
        "name": "Image Top / Text Bottom",
        "category": "page_layout",
        "book_type": "childrens",
        "description": "Classic picture book layout with illustration on top "
        "and text below. Most commonly used format.",
        "preview_url": None,
        "config": {
            "layout": "image_top_text_bottom",
            "image_ratio": 0.6,
            "text_ratio": 0.4,
        },
        "tags": ["childrens", "classic", "standard"],
    },
    {
        "id": "layout-side-by-side",
        "name": "Side by Side",
        "category": "page_layout",
        "book_type": "childrens",
        "description": "Image on one side, text on the other. Works well "
        "for landscape spreads and dialogue-heavy pages.",
        "preview_url": None,
        "config": {
            "layout": "side_by_side",
            "image_side": "left",
        },
        "tags": ["childrens", "landscape", "dialogue"],
    },
    {
        "id": "layout-single-sided-coloring",
        "name": "Single-Sided Coloring Page",
        "category": "page_layout",
        "book_type": "coloring",
        "description": "Standard coloring book page with blank back. "
        "Ensures markers and paints don't bleed through.",
        "preview_url": None,
        "config": {
            "layout": "single_sided",
            "blank_back": True,
            "extra_inner_margin": 0.25,
        },
        "tags": ["coloring", "standard"],
    },
    {
        "id": "layout-bordered-coloring",
        "name": "Bordered Coloring Page",
        "category": "page_layout",
        "book_type": "coloring",
        "description": "Coloring page with decorative border frame. " "Adds a finished look to each page.",
        "preview_url": None,
        "config": {
            "layout": "bordered",
            "border_width": 0.5,
            "border_style": "decorative",
        },
        "tags": ["coloring", "bordered", "decorative"],
    },
    {
        "id": "layout-puzzle-single",
        "name": "One Puzzle Per Page",
        "category": "page_layout",
        "book_type": "puzzle",
        "description": "Standard layout with one puzzle per page. "
        "Title, instructions, and puzzle grid with ample writing space.",
        "preview_url": None,
        "config": {
            "layout": "single_puzzle",
            "header_height": 0.8,
            "grid_padding": 0.5,
        },
        "tags": ["puzzle", "standard", "single"],
    },
    {
        "id": "layout-puzzle-double",
        "name": "Two Puzzles Per Page",
        "category": "page_layout",
        "book_type": "puzzle",
        "description": "Compact layout with two puzzles per page. " "Good for smaller puzzle types or travel editions.",
        "preview_url": None,
        "config": {
            "layout": "double_puzzle",
            "split": "horizontal",
            "grid_padding": 0.3,
        },
        "tags": ["puzzle", "compact", "double"],
    },
    # -----------------------------------------------------------------------
    # Theme Packs
    # -----------------------------------------------------------------------
    {
        "id": "theme-animals-wildlife",
        "name": "Animals & Wildlife",
        "category": "theme_pack",
        "book_type": None,
        "description": "Safari animals, ocean creatures, forest animals, "
        "farm animals, and birds. 50+ themed word lists included.",
        "preview_url": None,
        "config": {
            "themes": ["safari", "ocean", "forest", "farm", "birds", "insects"],
            "word_lists": True,
            "illustration_prompts": True,
        },
        "tags": ["animals", "nature", "kids", "universal"],
    },
    {
        "id": "theme-fantasy-worlds",
        "name": "Fantasy Worlds",
        "category": "theme_pack",
        "book_type": None,
        "description": "Dragons, castles, wizards, fairies, and enchanted forests. "
        "Non-trademarked fantasy themes suitable for all ages.",
        "preview_url": None,
        "config": {
            "themes": ["dragons", "castles", "wizards", "fairies", "enchanted_forest"],
            "word_lists": True,
            "illustration_prompts": True,
        },
        "tags": ["fantasy", "magic", "adventure"],
    },
    {
        "id": "theme-nature-seasons",
        "name": "Nature & Seasons",
        "category": "theme_pack",
        "book_type": None,
        "description": "Spring flowers, summer beach, autumn leaves, winter snow. "
        "Seasonal illustrations and themed vocabulary.",
        "preview_url": None,
        "config": {
            "themes": ["spring", "summer", "autumn", "winter", "garden", "mountains"],
            "word_lists": True,
            "seasonal": True,
        },
        "tags": ["nature", "seasons", "outdoor"],
    },
    {
        "id": "theme-space-scifi",
        "name": "Space & Science Fiction",
        "category": "theme_pack",
        "book_type": None,
        "description": "Planets, rockets, astronauts, aliens, and galaxies. "
        "Science-themed vocabulary for educational puzzle books.",
        "preview_url": None,
        "config": {
            "themes": ["planets", "rockets", "astronauts", "aliens", "galaxies", "robots"],
            "word_lists": True,
            "educational": True,
        },
        "tags": ["space", "science", "educational"],
    },
    {
        "id": "theme-food-desserts",
        "name": "Food & Desserts",
        "category": "theme_pack",
        "book_type": None,
        "description": "Cupcakes, fruits, vegetables, baking, and kitchen items. "
        "Popular coloring book theme with broad appeal.",
        "preview_url": None,
        "config": {
            "themes": ["cupcakes", "fruits", "vegetables", "baking", "kitchen"],
            "word_lists": True,
        },
        "tags": ["food", "desserts", "baking"],
    },
    {
        "id": "theme-holidays",
        "name": "Holidays & Celebrations",
        "category": "theme_pack",
        "book_type": None,
        "description": "Christmas, Halloween, Easter, Valentine's Day, Thanksgiving. "
        "Seasonal auto-theming for timely releases.",
        "preview_url": None,
        "config": {
            "themes": ["christmas", "halloween", "easter", "valentines", "thanksgiving"],
            "word_lists": True,
            "seasonal": True,
        },
        "tags": ["holidays", "seasonal", "celebrations"],
    },
    {
        "id": "theme-mandalas-patterns",
        "name": "Mandalas & Patterns",
        "category": "theme_pack",
        "book_type": "coloring",
        "description": "Geometric mandalas, repeating patterns, and zentangle designs. "
        "Top-selling adult coloring book category.",
        "preview_url": None,
        "config": {
            "themes": ["mandala", "geometric", "zentangle", "repeating_pattern"],
            "complexity_range": [3, 9],
        },
        "tags": ["mandalas", "patterns", "adult", "coloring"],
    },
    {
        "id": "theme-geometric-abstract",
        "name": "Geometric Abstract",
        "category": "theme_pack",
        "book_type": "coloring",
        "description": "Abstract geometric shapes, tessellations, and optical illusions. "
        "Modern aesthetic for teen and adult audiences.",
        "preview_url": None,
        "config": {
            "themes": ["geometric", "tessellation", "optical_illusion", "abstract"],
            "complexity_range": [5, 10],
        },
        "tags": ["geometric", "abstract", "modern", "coloring"],
    },
    # -----------------------------------------------------------------------
    # Style Packs
    # -----------------------------------------------------------------------
    {
        "id": "style-whimsical-watercolor",
        "name": "Whimsical Watercolor",
        "category": "style_pack",
        "book_type": "childrens",
        "description": "Soft watercolor illustration style with gentle edges and "
        "dreamy color palettes. Perfect for bedtime stories.",
        "preview_url": None,
        "config": {
            "illustration_style": "watercolor",
            "color_palette": "pastel",
            "line_weight": "none",
            "texture": "paper_grain",
        },
        "tags": ["watercolor", "soft", "dreamy", "childrens"],
    },
    {
        "id": "style-bold-cartoon",
        "name": "Bold Cartoon",
        "category": "style_pack",
        "book_type": "childrens",
        "description": "Bright, bold cartoon style with thick outlines and "
        "vivid colors. Great for action-oriented stories.",
        "preview_url": None,
        "config": {
            "illustration_style": "cartoon",
            "color_palette": "bright",
            "line_weight": "bold",
            "texture": "smooth",
        },
        "tags": ["cartoon", "bold", "bright", "childrens"],
    },
    {
        "id": "style-clean-outlines",
        "name": "Clean Outlines",
        "category": "style_pack",
        "book_type": "coloring",
        "description": "Crisp, uniform line weight with closed shapes for easy coloring. "
        "Best for younger audiences.",
        "preview_url": None,
        "config": {
            "line_style": "clean",
            "line_weight": 2.0,
            "stroke_uniformity": True,
            "closed_shapes_enforced": True,
        },
        "tags": ["clean", "simple", "kids", "coloring"],
    },
    {
        "id": "style-detailed-realistic",
        "name": "Detailed Realistic",
        "category": "style_pack",
        "book_type": "coloring",
        "description": "Highly detailed realistic illustrations with fine line work. "
        "Designed for advanced adult colorists.",
        "preview_url": None,
        "config": {
            "line_style": "fine",
            "line_weight": 0.8,
            "detail_level": "high",
            "complexity": 8,
        },
        "tags": ["detailed", "realistic", "adult", "coloring"],
    },
    {
        "id": "style-large-print",
        "name": "Large Print",
        "category": "style_pack",
        "book_type": "puzzle",
        "description": "Enlarged grids, larger fonts, and increased spacing for "
        "readers who need larger print. APH-compliant.",
        "preview_url": None,
        "config": {
            "scale": 1.5,
            "min_font_size": 18,
            "grid_line_weight": 2.0,
            "letter_spacing": 1.15,
            "contrast_ratio": 7.0,
        },
        "tags": ["large_print", "accessible", "seniors", "puzzle"],
    },
    {
        "id": "style-kid-friendly-puzzles",
        "name": "Kid-Friendly Puzzles",
        "category": "style_pack",
        "book_type": "puzzle",
        "description": "Playful fonts, colorful headers, and illustrated decorations "
        "around puzzle grids. Fun and engaging for ages 5-10.",
        "preview_url": None,
        "config": {
            "font_family": "rounded_sans",
            "header_style": "playful",
            "decorations": True,
            "difficulty_badges": True,
            "grid_style": "rounded_corners",
        },
        "tags": ["kids", "fun", "playful", "puzzle"],
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_templates(
    book_type: str | None = None,
    category: str | None = None,
) -> list[Template]:
    """Return filtered list of available templates.

    Parameters
    ----------
    book_type:
        Filter by book type (``childrens``, ``coloring``, ``puzzle``).
        Templates with ``book_type=None`` (universal) are always included.
    category:
        Filter by category (``page_layout``, ``theme_pack``, ``style_pack``).
    """
    results: list[Template] = []

    for t in BUILT_IN_TEMPLATES:
        # Filter by book type (include universal templates).
        if book_type and t["book_type"] is not None and t["book_type"] != book_type:
            continue

        # Filter by category.
        if category and t["category"] != category:
            continue

        results.append(
            Template(
                id=t["id"],
                name=t["name"],
                category=t["category"],
                book_type=t["book_type"],
                description=t["description"],
                preview_url=t.get("preview_url"),
                config=t["config"],
                tags=t.get("tags", []),
            )
        )

    return results
