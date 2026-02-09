"""AI cover generation module.

Builds prompts from genre/mood/elements, calls the image-generation API
(OpenAI DALL-E 3 with a Midjourney-style placeholder), and post-processes
the result (resize, thumbnail, upload to S3).
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.config import get_settings
from app.modules.cover_design.schemas import (
    CoverDimensions,
    CoverGenre,
    CoverPlatform,
    CoverStatus,
)
from app.modules.cover_design.templates import (
    get_dimensions_for_platform,
    get_template_by_id,
    get_templates_by_genre,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def build_cover_prompt(
    *,
    title: str,
    subtitle: str | None = None,
    author_name: str,
    genre: CoverGenre,
    mood: str | None = None,
    style_keywords: list[str] | None = None,
    color_palette: list[str] | None = None,
    additional_instructions: str | None = None,
    template_id: str | None = None,
) -> str:
    """Build an image-generation prompt for a book cover.

    The prompt is designed to work well with DALL-E 3 and similar
    text-to-image models.
    """
    parts: list[str] = []

    # Base instruction
    parts.append(
        "Create a professional book cover design for a published book. "
        "The cover should look like a real, commercially available book cover "
        "suitable for online retail."
    )

    # Genre guidance
    genre_guidance = _GENRE_PROMPT_FRAGMENTS.get(genre, "")
    if genre_guidance:
        parts.append(f"Genre style: {genre_guidance}")

    # Template-specific guidance
    if template_id:
        template = get_template_by_id(template_id)
        if template and template.layout_guidance:
            parts.append(f"Layout: {template.layout_guidance}")

    # Title and author
    parts.append(f'Book title: "{title}".')
    if subtitle:
        parts.append(f'Subtitle: "{subtitle}".')
    parts.append(f'Author name: "{author_name}".')

    # Mood
    if mood:
        parts.append(f"The overall mood should be: {mood}.")

    # Style keywords
    if style_keywords:
        parts.append(f"Visual style keywords: {', '.join(style_keywords)}.")

    # Colour palette
    if color_palette:
        parts.append(f"Preferred colour palette: {', '.join(color_palette)}.")

    # Additional instructions
    if additional_instructions:
        parts.append(f"Additional instructions: {additional_instructions}")

    # Quality instruction
    parts.append(
        "The design should be high-resolution, commercially polished, "
        "with readable typography and balanced composition."
    )

    return " ".join(parts)


_GENRE_PROMPT_FRAGMENTS: dict[CoverGenre, str] = {
    CoverGenre.ROMANCE: (
        "Romantic, warm colour tones. Elegant script or serif fonts. "
        "Imagery can include couples, scenic vistas, or intimate settings."
    ),
    CoverGenre.THRILLER: (
        "High-contrast, dramatic. Dark backgrounds, bold sans-serif fonts. "
        "Tension-evoking imagery — cityscapes, silhouettes, shadowy scenes."
    ),
    CoverGenre.MYSTERY: (
        "Intriguing, atmospheric. Muted or noir colour palette. "
        "Mysterious imagery — fog, keyholes, magnifying glasses, dimly lit scenes."
    ),
    CoverGenre.SCI_FI: (
        "Futuristic, technologically advanced. Cool blues, neon accents. "
        "Space vistas, technology, futuristic cityscapes."
    ),
    CoverGenre.FANTASY: (
        "Epic, magical. Rich jewel tones. Ornate typography. "
        "Landscapes, mythical creatures, magical elements."
    ),
    CoverGenre.HORROR: (
        "Dark, unsettling. Very limited palette — blacks, reds, greys. "
        "Distressed fonts. Creepy imagery."
    ),
    CoverGenre.LITERARY_FICTION: (
        "Artistic, understated. Sophisticated design with thoughtful typography. "
        "Abstract or metaphorical imagery."
    ),
    CoverGenre.NONFICTION: (
        "Professional, authoritative. Clean layout, strong typography. "
        "Solid backgrounds or subtle patterns."
    ),
    CoverGenre.SELF_HELP: (
        "Uplifting, accessible. Warm, bright colours. Clear, friendly fonts. "
        "Nature imagery or abstract positive symbols."
    ),
    CoverGenre.BUSINESS: (
        "Corporate, polished. Navy, charcoal, gold accents. "
        "Authoritative serif or clean sans-serif fonts."
    ),
    CoverGenre.CHILDRENS: (
        "Bright, playful, illustrated. Bold primary colours. "
        "Fun rounded fonts. Cartoon or watercolour illustration style."
    ),
    CoverGenre.YOUNG_ADULT: (
        "Trendy, bold. Eye-catching colours and modern typography. "
        "Stylish imagery that appeals to teens."
    ),
    CoverGenre.MEMOIR: (
        "Personal, textured. Warm or muted tones. Handwritten or serif fonts. "
        "Personal photography or intimate illustration."
    ),
    CoverGenre.COOKBOOK: (
        "Appetising, clean. Warm colours. Space for food photography. "
        "Clean, readable fonts."
    ),
    CoverGenre.OTHER: (
        "Clean, professional book cover with balanced composition."
    ),
}


# ---------------------------------------------------------------------------
# Image generation (DALL-E 3 / placeholder)
# ---------------------------------------------------------------------------


async def generate_cover_image(
    prompt: str,
    dimensions: CoverDimensions | None = None,
    platform: CoverPlatform = CoverPlatform.AMAZON_KDP,
) -> dict[str, Any]:
    """Call the image generation API and return image metadata.

    Returns a dict with keys:
        - image_url: str — URL (or local path) of the generated image
        - thumbnail_url: str | None — URL of a smaller thumbnail
        - prompt_used: str — the prompt actually sent
        - width_px, height_px, dpi: int — final dimensions

    NOTE: In production this calls OpenAI DALL-E 3 (or a Midjourney proxy).
    The current implementation returns a *placeholder* so that the rest of the
    pipeline can be tested without burning API credits.
    """
    if dimensions is None:
        dimensions = get_dimensions_for_platform(platform)

    # Map our desired dimensions to DALL-E 3 supported sizes
    dalle_size = _pick_dalle_size(dimensions.width_px, dimensions.height_px)

    # ----- Placeholder implementation -----
    # In production, uncomment the openai call below:
    #
    # import openai
    # client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    # response = await client.images.generate(
    #     model="dall-e-3",
    #     prompt=prompt,
    #     size=dalle_size,
    #     quality="hd",
    #     n=1,
    # )
    # image_url = response.data[0].url
    # revised_prompt = response.data[0].revised_prompt

    image_id = uuid.uuid4().hex[:12]
    image_url = f"https://placeholder.selfpublisherforge.com/covers/{image_id}.png"
    thumbnail_url = f"https://placeholder.selfpublisherforge.com/covers/{image_id}_thumb.png"
    revised_prompt = prompt

    logger.info("Generated placeholder cover image: %s", image_url)

    return {
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "prompt_used": revised_prompt,
        "width_px": dimensions.width_px,
        "height_px": dimensions.height_px,
        "dpi": dimensions.dpi,
    }


def _pick_dalle_size(width: int, height: int) -> str:
    """Map arbitrary dimensions to the closest DALL-E 3 supported size."""
    ratio = width / height if height else 1.0
    if ratio < 0.8:
        return "1024x1792"  # portrait
    elif ratio > 1.2:
        return "1792x1024"  # landscape
    else:
        return "1024x1024"  # square


# ---------------------------------------------------------------------------
# Variation generation
# ---------------------------------------------------------------------------


async def generate_variations(
    original_prompt: str,
    variation_type: str,
    count: int = 3,
    instructions: str | None = None,
) -> list[dict[str, Any]]:
    """Generate variations of an existing cover concept.

    ``variation_type`` can be 'style', 'color', 'layout', or 'typography'.
    """
    modifier_map = {
        "style": "Create a variation with a different artistic style but the same content.",
        "color": "Create a variation with a different colour scheme.",
        "layout": "Create a variation with a different layout and composition.",
        "typography": "Create a variation with different font styles and text placement.",
    }
    modifier = modifier_map.get(variation_type, modifier_map["style"])

    results: list[dict[str, Any]] = []
    for i in range(count):
        variation_prompt = f"{original_prompt} {modifier}"
        if instructions:
            variation_prompt += f" {instructions}"
        variation_prompt += f" (variation {i + 1} of {count})"

        result = await generate_cover_image(variation_prompt)
        result["variation_index"] = i
        result["variation_type"] = variation_type
        results.append(result)

    return results
