"""AI-powered blurb generation and A/B variant creation.

Uses genre-specific templates and AI prompts to generate optimized
blurb variations for Amazon book listings.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.modules.product_page_lab.schemas import (
    BlurbGenerateResponse,
    BlurbVariant,
    Genre,
)
from app.modules.product_page_lab.analyzer import analyze_blurb

# ---------------------------------------------------------------------------
# Genre-specific templates
# ---------------------------------------------------------------------------

GENRE_TEMPLATES: dict[str, dict[str, str]] = {
    Genre.ROMANCE: {
        "emotional_hook": (
            "<b>{hook}</b>\n\n"
            "{protagonist} never expected {inciting_incident}.\n\n"
            "But when {love_interest} enters their life, everything changes.\n\n"
            "{conflict}\n\n"
            "<i>{tagline}</i>\n\n"
            "{cta}"
        ),
        "question_hook": (
            "<b>What happens when {question}?</b>\n\n"
            "{setup}\n\n"
            "{tension}\n\n"
            "- {bullet1}\n"
            "- {bullet2}\n"
            "- {bullet3}\n\n"
            "<i>{tagline}</i>\n\n"
            "{cta}"
        ),
    },
    Genre.THRILLER: {
        "suspense_hook": (
            "<b>{hook}</b>\n\n"
            "{protagonist} thought {false_safety}.\n\n"
            "They were wrong.\n\n"
            "{stakes}\n\n"
            "{ticking_clock}\n\n"
            "<i>{tagline}</i>\n\n"
            "{cta}"
        ),
        "action_hook": (
            "<b>{hook}</b>\n\n"
            "{setup}\n\n"
            "Now, with {stakes}, {protagonist} must {mission}.\n\n"
            "- {bullet1}\n"
            "- {bullet2}\n"
            "- {bullet3}\n\n"
            "<i>{tagline}</i>\n\n"
            "{cta}"
        ),
    },
    Genre.NON_FICTION: {
        "problem_solution": (
            "<b>{hook}</b>\n\n"
            "Are you struggling with {problem}?\n\n"
            "In <i>{title}</i>, {author_credential} reveals:\n\n"
            "- {benefit1}\n"
            "- {benefit2}\n"
            "- {benefit3}\n"
            "- {benefit4}\n\n"
            "{social_proof}\n\n"
            "<b>{cta}</b>"
        ),
        "story_hook": (
            "<b>{hook}</b>\n\n"
            "{story}\n\n"
            "Inside, you'll discover:\n\n"
            "- {benefit1}\n"
            "- {benefit2}\n"
            "- {benefit3}\n\n"
            "{transformation_promise}\n\n"
            "<b>{cta}</b>"
        ),
    },
}

# Default template for genres without specific templates
DEFAULT_TEMPLATES: dict[str, str] = {
    "emotional_hook": (
        "<b>{hook}</b>\n\n"
        "{opening}\n\n"
        "{middle}\n\n"
        "{tension}\n\n"
        "<i>{tagline}</i>\n\n"
        "{cta}"
    ),
    "question_hook": (
        "<b>{question}</b>\n\n"
        "{setup}\n\n"
        "{conflict}\n\n"
        "- {bullet1}\n"
        "- {bullet2}\n"
        "- {bullet3}\n\n"
        "<i>{tagline}</i>\n\n"
        "{cta}"
    ),
    "list_hook": (
        "<b>{hook}</b>\n\n"
        "{intro}\n\n"
        "- {point1}\n"
        "- {point2}\n"
        "- {point3}\n"
        "- {point4}\n\n"
        "{closing}\n\n"
        "<b>{cta}</b>"
    ),
}

# Hook types by genre
HOOK_TYPES: dict[str, list[str]] = {
    Genre.ROMANCE: ["emotional_hook", "question_hook"],
    Genre.THRILLER: ["suspense_hook", "action_hook"],
    Genre.MYSTERY: ["suspense_hook", "question_hook"],
    Genre.FANTASY: ["emotional_hook", "question_hook"],
    Genre.SCIENCE_FICTION: ["question_hook", "emotional_hook"],
    Genre.NON_FICTION: ["problem_solution", "story_hook"],
    Genre.SELF_HELP: ["problem_solution", "story_hook"],
}

# Style labels
BLURB_STYLES = [
    "compelling_narrative",
    "benefit_driven",
    "emotional_appeal",
    "suspense_driven",
    "social_proof",
]


# ---------------------------------------------------------------------------
# AI prompt builders
# ---------------------------------------------------------------------------

def build_blurb_generation_prompt(
    current_blurb: str,
    genre: Genre,
    target_audience: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    tone: Optional[str] = None,
    variant_index: int = 0,
) -> str:
    """Build an AI prompt for generating an optimized blurb variant."""
    keywords = keywords or []
    style = BLURB_STYLES[variant_index % len(BLURB_STYLES)]

    prompt = f"""You are an expert Amazon book marketing copywriter specializing in {genre.value} books.

TASK: Rewrite and optimize the following book blurb for maximum conversion on Amazon.

CURRENT BLURB:
{current_blurb}

OPTIMIZATION STYLE: {style}

REQUIREMENTS:
1. Start with a powerful hook (first line must grab attention)
2. Use HTML formatting: <b> for bold, <i> for italic, <br> for line breaks
3. Include bullet points for key selling points where appropriate
4. End with a clear call-to-action
5. Keep between 150-250 words
6. Maintain genre conventions for {genre.value}
"""

    if target_audience:
        prompt += f"\nTARGET AUDIENCE: {target_audience}"

    if keywords:
        prompt += f"\nKEYWORDS TO INCLUDE: {', '.join(keywords)}"

    if tone:
        prompt += f"\nTONE: {tone}"

    hook_types = HOOK_TYPES.get(genre, list(DEFAULT_TEMPLATES.keys()))
    hook_type = hook_types[variant_index % len(hook_types)] if hook_types else "emotional_hook"
    prompt += f"\nHOOK STYLE: {hook_type}"

    prompt += """

OUTPUT FORMAT:
Return ONLY the optimized blurb text with HTML formatting. No explanations or commentary."""

    return prompt


# ---------------------------------------------------------------------------
# Local blurb generation (template-based fallback)
# ---------------------------------------------------------------------------

def generate_blurb_variants_local(
    current_blurb: str,
    genre: Genre,
    target_audience: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    tone: Optional[str] = None,
    num_variants: int = 3,
) -> BlurbGenerateResponse:
    """Generate blurb variants using local template-based approach.

    This is the fallback when AI generation is unavailable.
    It creates variations by rearranging and enhancing the existing blurb.
    """
    # Analyze the original blurb
    original_analysis = analyze_blurb(current_blurb)
    original_score = original_analysis.score

    variants: list[BlurbVariant] = []
    keywords = keywords or []

    for i in range(num_variants):
        style = BLURB_STYLES[i % len(BLURB_STYLES)]
        hook_types_list = HOOK_TYPES.get(genre, list(DEFAULT_TEMPLATES.keys()))
        hook_type = hook_types_list[i % len(hook_types_list)] if hook_types_list else "emotional_hook"

        # Create variant based on style
        variant_content = _create_template_variant(
            current_blurb, style, hook_type, keywords, i
        )

        # Score the variant
        variant_analysis = analyze_blurb(variant_content)

        highlights: list[str] = []
        if variant_analysis.has_hook and not original_analysis.has_hook:
            highlights.append("Added compelling hook")
        if variant_analysis.has_html_formatting and not original_analysis.has_html_formatting:
            highlights.append("Added HTML formatting")
        if variant_analysis.has_cta and not original_analysis.has_cta:
            highlights.append("Added call-to-action")
        if variant_analysis.has_bullet_points and not original_analysis.has_bullet_points:
            highlights.append("Added bullet points")

        variants.append(BlurbVariant(
            variant_id=str(uuid.uuid4()),
            content=variant_content,
            style=style,
            hook_type=hook_type,
            estimated_conversion_score=round(variant_analysis.score, 1),
            highlights=highlights,
        ))

    return BlurbGenerateResponse(
        original_score=round(original_score, 1),
        variants=variants,
        generation_metadata={
            "method": "template_based",
            "genre": genre.value,
            "num_variants": num_variants,
        },
    )


def _create_template_variant(
    blurb: str,
    style: str,
    hook_type: str,
    keywords: list[str],
    index: int,
) -> str:
    """Create a template-based variant of the blurb."""
    sentences = [s.strip() for s in blurb.replace("\n", " ").split(".") if s.strip()]

    # Build enhanced blurb with formatting
    parts: list[str] = []

    # Add a hook
    if sentences:
        if style == "benefit_driven" and len(sentences) > 1:
            parts.append(f"<b>{sentences[0]}.</b>")
        elif style == "emotional_appeal":
            parts.append(f"<b><i>{sentences[0]}.</i></b>")
        elif style == "suspense_driven":
            parts.append(f"<b>{sentences[0]}...</b>")
        else:
            parts.append(f"<b>{sentences[0]}.</b>")

    # Add body
    middle_sentences = sentences[1:-1] if len(sentences) > 2 else sentences[1:]
    if middle_sentences:
        body = ". ".join(middle_sentences) + "."
        parts.append(f"\n\n{body}")

    # Add bullet points if style suggests it
    if style in ("benefit_driven", "social_proof") and keywords:
        bullet_section = "\n\n"
        for kw in keywords[:3]:
            bullet_section += f"- {kw.title()}\n"
        parts.append(bullet_section)

    # Add closing with CTA
    if sentences:
        last = sentences[-1] if len(sentences) > 1 else ""
        if last:
            parts.append(f"\n\n<i>{last}.</i>")

    parts.append("\n\n<b>Scroll up and grab your copy today!</b>")

    return "".join(parts)


# ---------------------------------------------------------------------------
# AI blurb generation (requires LLM service)
# ---------------------------------------------------------------------------

async def generate_blurb_variants_ai(
    current_blurb: str,
    genre: Genre,
    target_audience: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    tone: Optional[str] = None,
    num_variants: int = 3,
    llm_client: Optional[object] = None,
) -> BlurbGenerateResponse:
    """Generate blurb variants using AI.

    Falls back to template-based generation if no LLM client is provided.
    """
    if llm_client is None:
        return generate_blurb_variants_local(
            current_blurb=current_blurb,
            genre=genre,
            target_audience=target_audience,
            keywords=keywords,
            tone=tone,
            num_variants=num_variants,
        )

    original_analysis = analyze_blurb(current_blurb)
    original_score = original_analysis.score

    variants: list[BlurbVariant] = []

    for i in range(num_variants):
        style = BLURB_STYLES[i % len(BLURB_STYLES)]
        hook_types_list = HOOK_TYPES.get(genre, list(DEFAULT_TEMPLATES.keys()))
        hook_type = hook_types_list[i % len(hook_types_list)] if hook_types_list else "emotional_hook"

        prompt = build_blurb_generation_prompt(
            current_blurb=current_blurb,
            genre=genre,
            target_audience=target_audience,
            keywords=keywords,
            tone=tone,
            variant_index=i,
        )

        try:
            # Call LLM -- interface depends on the orchestration module
            response = await llm_client.generate(prompt)  # type: ignore[attr-defined]
            variant_content = response.strip()
        except Exception:
            # Fallback to template
            variant_content = _create_template_variant(
                current_blurb, style, hook_type, keywords or [], i
            )

        variant_analysis = analyze_blurb(variant_content)

        highlights: list[str] = []
        if variant_analysis.has_hook:
            highlights.append("Strong hook detected")
        if variant_analysis.has_html_formatting:
            highlights.append("HTML formatting included")
        if variant_analysis.has_cta:
            highlights.append("Call-to-action present")

        variants.append(BlurbVariant(
            variant_id=str(uuid.uuid4()),
            content=variant_content,
            style=style,
            hook_type=hook_type,
            estimated_conversion_score=round(variant_analysis.score, 1),
            highlights=highlights,
        ))

    return BlurbGenerateResponse(
        original_score=round(original_score, 1),
        variants=variants,
        generation_metadata={
            "method": "ai_generated",
            "genre": genre.value,
            "num_variants": num_variants,
        },
    )
