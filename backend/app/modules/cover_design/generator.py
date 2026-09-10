"""AI cover generation module.

Builds prompts from genre/mood/elements, calls the OpenAI DALL-E 3
image-generation API, and post-processes the result (resize, thumbnail,
upload to S3).

Enhanced with support for multiple formats (ebook, paperback, audiobook),
variable variations, art style presets, reference images, and spine calculation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, cast

import openai

from app.config import get_settings
from app.modules.cover_design.schemas import (
    CoverDimensions,
    CoverGenre,
    CoverPlatform,
)
from app.modules.cover_design.templates import (
    FORMAT_DIMENSIONS,
    get_dimensions_for_platform,
    get_template_by_id,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Enums for enhanced functionality
# ---------------------------------------------------------------------------


class CoverFormat:
    """Cover format types."""

    EBOOK = "ebook"
    PAPERBACK = "paperback"
    AUDIOBOOK = "audiobook"


class ArtStyle:
    """Art style presets for cover generation."""

    MINIMAL = "minimal"
    PHOTOGRAPHIC = "photographic"
    ILLUSTRATED = "illustrated"
    TYPOGRAPHIC = "typographic"
    VINTAGE = "vintage"
    THREE_D_RENDER = "3d_render"


# Format-specific dimensions
# Art style prompt guidance
ART_STYLE_PROMPTS: dict[str, str] = {
    ArtStyle.MINIMAL: (
        "Minimalist design with clean lines, ample negative space, limited colour palette (2-3 colours max), "
        "simple geometric shapes, and restrained typography. Focus on essential elements only."
    ),
    ArtStyle.PHOTOGRAPHIC: (
        "High-quality photographic imagery with realistic lighting, depth of field effects, "
        "professional photo composition, natural textures, and authentic atmospheric elements. "
        "Style should resemble professional photography or photo manipulation."
    ),
    ArtStyle.ILLUSTRATED: (
        "Hand-drawn or digital illustration style with artistic interpretation, visible brush strokes or pen work, "
        "illustrative techniques (watercolour, ink, digital painting, vector art), creative interpretation, "
        "and stylized rather than photorealistic rendering."
    ),
    ArtStyle.TYPOGRAPHIC: (
        "Typography-focused design where text is the primary visual element. Bold, expressive letterforms, "
        "creative text treatments, hierarchy through font variation, minimal imagery, "
        "text as both content and decoration. Typography should dominate the composition."
    ),
    ArtStyle.VINTAGE: (
        "Vintage or retro aesthetic with aged textures, weathered effects, classic design patterns, "
        "period-appropriate colour palettes (sepia, faded colours, muted tones), distressed elements, "
        "nostalgic feel reminiscent of classic book covers from the 1950s-1980s."
    ),
    ArtStyle.THREE_D_RENDER: (
        "3D rendered design with dimensional depth, realistic lighting and shadows, "
        "computer-generated imagery (CGI) aesthetic, volumetric elements, modern rendering techniques, "
        "polished surfaces, and photorealistic 3D objects or environments."
    ),
}


# ---------------------------------------------------------------------------
# Spine calculation for paperback
# ---------------------------------------------------------------------------


def calculate_spine_width(
    page_count: int,
    paper_type: str = "white",
    dpi: int = 300,
) -> float:
    """Calculate spine width in inches for paperback covers.

    Args:
        page_count: Total number of pages in the book
        paper_type: Either "white" (0.002252" per page) or "cream" (0.0025" per page)
        dpi: Dots per inch for conversion to pixels

    Returns:
        Spine width in inches
    """
    thickness_per_page = 0.0025 if paper_type.lower() == "cream" else 0.002252
    return page_count * thickness_per_page


def get_paperback_dimensions(
    page_count: int,
    trim_width: float = 6.0,
    trim_height: float = 9.0,
    paper_type: str = "white",
    bleed: float = 0.125,
    dpi: int = 300,
) -> CoverDimensions:
    """Calculate full wrap dimensions for paperback cover with spine.

    Args:
        page_count: Total number of pages
        trim_width: Book width in inches (default 6x9)
        trim_height: Book height in inches (default 6x9)
        paper_type: "white" or "cream"
        bleed: Bleed in inches (typically 0.125")
        dpi: Resolution (typically 300)

    Returns:
        CoverDimensions with full wrap width including spine
    """
    spine_width = calculate_spine_width(page_count, paper_type, dpi)

    # Total width = front cover + spine + back cover + bleed on both sides
    total_width_inches = (trim_width * 2) + spine_width + (bleed * 2)
    total_height_inches = trim_height + (bleed * 2)

    width_px = int(total_width_inches * dpi)
    height_px = int(total_height_inches * dpi)
    bleed_px = int(bleed * dpi)

    return CoverDimensions(
        width_px=width_px,
        height_px=height_px,
        dpi=dpi,
        bleed_px=bleed_px,
    )


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
    art_style: str | None = None,
    book_description: str | None = None,
    cover_format: str = CoverFormat.EBOOK,
    reference_image_context: str | None = None,
) -> str:
    """Build an image-generation prompt for a book cover.

    The prompt is designed to work well with DALL-E 3 and similar
    text-to-image models.

    Args:
        title: Book title
        subtitle: Book subtitle (optional)
        author_name: Author name
        genre: Book genre
        mood: Mood/tone keywords
        style_keywords: Visual style keywords
        color_palette: Colour preferences
        additional_instructions: Custom instructions
        template_id: Template identifier
        art_style: Art style preset (minimal, photographic, illustrated, etc.)
        book_description: Book blurb/description for context
        cover_format: Format type (ebook, paperback, audiobook)
        reference_image_context: Context about reference image style
    """
    parts: list[str] = []

    # Base instruction - format-specific
    if cover_format == CoverFormat.AUDIOBOOK:
        parts.append(
            "Create a professional audiobook cover design optimized for square format. "
            "The cover must work at small thumbnail sizes and be visually striking when viewed as a square. "
            "Design should be bold, clear, and instantly recognizable even at 200x200px."
        )
    elif cover_format == CoverFormat.PAPERBACK:
        parts.append(
            "Create a professional paperback book cover design for the FRONT COVER ONLY. "
            "This will be part of a full wrap, so ensure the design works as a standalone front cover. "
            "The cover should look like a real, commercially available paperback book suitable for retail."
        )
    else:  # EBOOK
        parts.append(
            "Create a professional ebook cover design optimized for digital retail platforms. "
            "The cover should look like a real, commercially available ebook cover "
            "suitable for Amazon, Apple Books, and other online retailers. "
            "Design must be clear and readable at thumbnail sizes (typically 200-300px tall)."
        )

    # Art style guidance
    if art_style and art_style in ART_STYLE_PROMPTS:
        parts.append(f"Art style: {ART_STYLE_PROMPTS[art_style]}")

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

    # Reference image context
    if reference_image_context:
        parts.append(f"Style reference notes: {reference_image_context}")

    # Additional instructions
    if additional_instructions:
        parts.append(f"Additional instructions: {additional_instructions}")

    # Quality instruction - format-specific
    if cover_format == CoverFormat.AUDIOBOOK:
        parts.append(
            "The design must be high-resolution, commercially polished, with very bold and readable typography "
            "that works in a perfect square format. Ensure visual elements are centred and balanced for square composition."
        )
    else:
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
        "Tension-evoking imagery â€” cityscapes, silhouettes, shadowy scenes."
    ),
    CoverGenre.MYSTERY: (
        "Intriguing, atmospheric. Muted or noir colour palette. "
        "Mysterious imagery â€” fog, keyholes, magnifying glasses, dimly lit scenes."
    ),
    CoverGenre.SCI_FI: (
        "Futuristic, technologically advanced. Cool blues, neon accents. "
        "Space vistas, technology, futuristic cityscapes."
    ),
    CoverGenre.FANTASY: (
        "Epic, magical. Rich jewel tones. Ornate typography. " "Landscapes, mythical creatures, magical elements."
    ),
    CoverGenre.HORROR: (
        "Dark, unsettling. Very limited palette â€” blacks, reds, greys. " "Distressed fonts. Creepy imagery."
    ),
    CoverGenre.LITERARY_FICTION: (
        "Artistic, understated. Sophisticated design with thoughtful typography. " "Abstract or metaphorical imagery."
    ),
    CoverGenre.NONFICTION: (
        "Professional, authoritative. Clean layout, strong typography. " "Solid backgrounds or subtle patterns."
    ),
    CoverGenre.SELF_HELP: (
        "Uplifting, accessible. Warm, bright colours. Clear, friendly fonts. "
        "Nature imagery or abstract positive symbols."
    ),
    CoverGenre.BUSINESS: (
        "Corporate, polished. Navy, charcoal, gold accents. " "Authoritative serif or clean sans-serif fonts."
    ),
    CoverGenre.CHILDRENS: (
        "Bright, playful, illustrated. Bold primary colours. "
        "Fun rounded fonts. Cartoon or watercolour illustration style."
    ),
    CoverGenre.YOUNG_ADULT: (
        "Trendy, bold. Eye-catching colours and modern typography. " "Stylish imagery that appeals to teens."
    ),
    CoverGenre.MEMOIR: (
        "Personal, textured. Warm or muted tones. Handwritten or serif fonts. "
        "Personal photography or intimate illustration."
    ),
    CoverGenre.COOKBOOK: ("Appetising, clean. Warm colours. Space for food photography. " "Clean, readable fonts."),
    CoverGenre.OTHER: ("Clean, professional book cover with balanced composition."),
}


# ---------------------------------------------------------------------------
# Image generation (DALL-E 3)
# ---------------------------------------------------------------------------


def _get_openai_api_key() -> str | None:
    """Return the OpenAI API key if it is configured, else ``None``."""
    key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if key and key not in ("", "YOUR_OPENAI_API_KEY_HERE"):
        return key
    return None


async def generate_cover_image(
    prompt: str,
    dimensions: CoverDimensions | None = None,
    platform: CoverPlatform = CoverPlatform.AMAZON_KDP,
    cover_format: str = CoverFormat.EBOOK,
) -> dict[str, Any]:
    """Call the OpenAI DALL-E 3 API and return image metadata.

    Returns a dict with keys:
        - image_url: str â€” URL of the generated image
        - thumbnail_url: str | None â€” URL of a smaller preview
        - prompt_used: str â€” the prompt actually sent (or DALL-E revised prompt)
        - width_px, height_px, dpi: int â€” final dimensions
        - status: str â€” "success" or "error"
        - error: str | None â€” error message when status is "error"
    """
    if dimensions is None:
        if cover_format in FORMAT_DIMENSIONS:
            dimensions = FORMAT_DIMENSIONS[cover_format]
        else:
            dimensions = get_dimensions_for_platform(platform)

    # Map our desired dimensions to a DALL-E 3 supported size string
    dalle_size = _pick_dalle_size(dimensions.width_px, dimensions.height_px)

    # Verify the API key is available
    api_key = _get_openai_api_key()
    if api_key is None:
        logger.warning(
            "OPENAI_API_KEY is not configured â€” cannot generate cover image. "
            "Set the key in your .env file or environment variables."
        )
        return {
            "image_url": None,
            "thumbnail_url": None,
            "prompt_used": prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "error",
            "error": "OPENAI_API_KEY is not configured.",
        }

    try:
        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=cast(Any, dalle_size),  # dalle_size is validated to be one of the correct sizes
            quality="hd",
            n=1,
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt or prompt

        # Use the same URL for the thumbnail for now; downstream
        # post-processing (S3 upload / resize) can produce a real thumbnail.
        thumbnail_url = image_url

        logger.info("Generated DALL-E 3 cover image successfully.")

        return {
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "prompt_used": revised_prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "success",
            "error": None,
        }

    except openai.AuthenticationError:
        logger.warning("OpenAI authentication failed â€” check your OPENAI_API_KEY.")
        return {
            "image_url": None,
            "thumbnail_url": None,
            "prompt_used": prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "error",
            "error": "OpenAI authentication failed. Please verify your API key.",
        }
    except openai.RateLimitError:
        logger.warning("OpenAI rate limit reached while generating cover image.")
        return {
            "image_url": None,
            "thumbnail_url": None,
            "prompt_used": prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "error",
            "error": "Rate limit reached. Please try again later.",
        }
    except openai.BadRequestError as exc:
        logger.warning("OpenAI rejected the cover prompt: %s", exc)
        return {
            "image_url": None,
            "thumbnail_url": None,
            "prompt_used": prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "error",
            "error": f"Image generation request was rejected: {exc}",
        }
    except openai.APIError as exc:
        logger.exception("OpenAI API error during cover generation: %s", exc)
        return {
            "image_url": None,
            "thumbnail_url": None,
            "prompt_used": prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "error",
            "error": f"OpenAI API error: {exc}",
        }
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        logger.exception("Unexpected error during cover image generation: %s", exc)
        return {
            "image_url": None,
            "thumbnail_url": None,
            "prompt_used": prompt,
            "width_px": dimensions.width_px,
            "height_px": dimensions.height_px,
            "dpi": dimensions.dpi,
            "status": "error",
            "error": f"Unexpected error: {exc}",
        }


def _pick_dalle_size(width: int, height: int) -> str:
    """Map arbitrary dimensions to the closest DALL-E 3 supported size."""
    ratio = width / height if height else 1.0
    if ratio < 0.8:
        return "1024x1792"  # portrait
    if ratio > 1.2:
        return "1792x1024"  # landscape
    return "1024x1024"  # square


# ---------------------------------------------------------------------------
# Variation generation
# ---------------------------------------------------------------------------


async def generate_variations(
    original_prompt: str,
    variation_type: str,
    count: int = 3,
    instructions: str | None = None,
    dimensions: CoverDimensions | None = None,
    cover_format: str = CoverFormat.EBOOK,
) -> list[dict[str, Any]]:
    """Generate variations of an existing cover concept.

    ``variation_type`` can be 'style', 'color', 'layout', or 'typography'.
    ``count`` can be 2, 4, 6, or 8 (or any reasonable number).
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

        result = await generate_cover_image(
            variation_prompt,
            dimensions=dimensions,
            cover_format=cover_format,
        )
        result["variation_index"] = i
        result["variation_type"] = variation_type
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Multi-format generation with art styles
# ---------------------------------------------------------------------------


async def generate_multi_format_covers(
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
    art_style: str | None = None,
    book_description: str | None = None,
    reference_image_urls: list[str] | None = None,
    reference_image_context: str | None = None,
    formats: list[str] | None = None,
    variations_per_format: int = 2,
    paperback_page_count: int | None = None,
    paperback_paper_type: str = "white",
) -> dict[str, list[dict[str, Any]]]:
    """Generate covers for multiple formats with variations.

    Args:
        title: Book title
        subtitle: Book subtitle
        author_name: Author name
        genre: Book genre
        mood: Mood keywords
        style_keywords: Visual style keywords
        color_palette: Colour preferences
        additional_instructions: Custom instructions
        template_id: Template identifier
        art_style: Art style preset
        book_description: Book blurb for context
        reference_image_urls: URLs of reference images (for future enhancement)
        reference_image_context: Description of reference image style
        formats: List of formats to generate (ebook, paperback, audiobook)
        variations_per_format: Number of variations per format (2, 4, 6, 8)
        paperback_page_count: Page count for spine calculation
        paperback_paper_type: "white" or "cream"

    Returns:
        Dict mapping format names to lists of generated cover results
    """
    if formats is None:
        formats = [CoverFormat.EBOOK]

    # Validate variations count
    if variations_per_format not in [2, 4, 6, 8]:
        logger.warning(f"Unusual variation count {variations_per_format}, proceeding anyway")

    results: dict[str, list[dict[str, Any]]] = {}

    for cover_format in formats:
        # Determine dimensions for this format
        if cover_format == CoverFormat.PAPERBACK:
            if paperback_page_count is None:
                logger.warning("Paperback format requires page_count for spine calculation, using default 200 pages")
                paperback_page_count = 200
            dimensions = get_paperback_dimensions(
                page_count=paperback_page_count,
                paper_type=paperback_paper_type,
            )
        elif cover_format in FORMAT_DIMENSIONS:
            dimensions = FORMAT_DIMENSIONS[cover_format]
        else:
            dimensions = get_dimensions_for_platform(CoverPlatform.AMAZON_KDP)

        # Build base prompt for this format
        base_prompt = build_cover_prompt(
            title=title,
            subtitle=subtitle,
            author_name=author_name,
            genre=genre,
            mood=mood,
            style_keywords=style_keywords,
            color_palette=color_palette,
            additional_instructions=additional_instructions,
            template_id=template_id,
            art_style=art_style,
            book_description=book_description,
            cover_format=cover_format,
            reference_image_context=reference_image_context,
        )

        # Generate variations for this format
        format_results = []
        for i in range(variations_per_format):
            # Add variation-specific guidance
            variation_prompt = base_prompt
            if i > 0:
                variation_prompt += f" Create a distinct variation (version {i + 1} of {variations_per_format})."

            result = await generate_cover_image(
                prompt=variation_prompt,
                dimensions=dimensions,
                cover_format=cover_format,
            )
            result["variation_index"] = i
            result["format"] = cover_format
            if cover_format == CoverFormat.PAPERBACK and paperback_page_count:
                result["spine_width_inches"] = calculate_spine_width(
                    paperback_page_count,
                    paperback_paper_type,
                )

            format_results.append(result)

        results[cover_format] = format_results

    return results
