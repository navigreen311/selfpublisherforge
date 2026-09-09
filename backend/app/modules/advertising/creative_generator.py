"""AI-powered ad creative generation for book advertising.

Generates ad headlines, body copy, and CTAs from book data and market research.
Uses LLM to produce compelling ad variations optimized for each platform.
"""

import json
import logging

from app.config import get_settings
from app.modules.advertising.schemas import (
    AdPlatform,
    CreativeGenerateRequest,
    CreativeGenerateResponse,
    GeneratedCreative,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# Platform-specific constraints
PLATFORM_CONSTRAINTS = {
    AdPlatform.AMAZON: {
        "headline_max_length": 150,
        "body_max_length": 500,
        "cta_options": ["Buy Now", "Learn More", "Read Sample", "Add to Cart"],
        "guidelines": (
            "Amazon Sponsored Products ads appear in search results. "
            "Headlines should be keyword-rich and directly address the reader's need. "
            "Focus on the book's unique value proposition. "
            "Avoid superlatives like 'best' or 'number one' unless substantiated."
        ),
    },
    AdPlatform.FACEBOOK: {
        "headline_max_length": 40,
        "body_max_length": 125,
        "cta_options": ["Shop Now", "Learn More", "Sign Up", "Download"],
        "guidelines": (
            "Facebook ads should be visually engaging and emotionally compelling. "
            "Use short, punchy headlines. Body text should create curiosity or urgency. "
            "Address the target audience directly. Use conversational tone."
        ),
    },
}


class AdCreativeGenerator:
    """Generates ad creatives using AI/LLM for book advertising campaigns."""

    def __init__(self, llm_client=None):
        """Initialize the creative generator.

        Args:
            llm_client: Optional LLM client. If not provided, uses built-in
                        template-based generation as fallback.
        """
        self.llm_client = llm_client

    async def generate_creatives(
        self,
        request: CreativeGenerateRequest,
    ) -> CreativeGenerateResponse:
        """Generate ad creative variations for a book.

        Uses LLM if available, otherwise falls back to template-based generation.

        Args:
            request: Creative generation parameters including book info and platform.

        Returns:
            CreativeGenerateResponse with multiple creative variations.
        """
        platform = request.platform
        constraints = PLATFORM_CONSTRAINTS.get(platform, PLATFORM_CONSTRAINTS[AdPlatform.AMAZON])

        if self.llm_client:
            try:
                variations = await self._generate_with_llm(request, constraints)
            except (ConnectionError, TimeoutError, ValueError, KeyError, IndexError, RuntimeError) as e:
                logger.warning("LLM generation failed, falling back to templates: %s", e)
                variations = self._generate_with_templates(request, constraints)
        else:
            variations = self._generate_with_templates(request, constraints)

        return CreativeGenerateResponse(
            variations=variations[: request.num_variations],
            platform=platform,
            book_title=request.book_title,
        )

    async def _generate_with_llm(
        self,
        request: CreativeGenerateRequest,
        constraints: dict,
    ) -> list[GeneratedCreative]:
        """Generate creatives using LLM.

        Constructs a prompt that includes book details, platform constraints,
        and target audience information.
        """
        prompt = self._build_prompt(request, constraints)

        try:
            # Use Anthropic API
            response = await self.llm_client.messages.create(
                model=settings.DEFAULT_LLM_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse the LLM response
            content = response.content[0].text
            return self._parse_llm_response(content, constraints)
        except (ConnectionError, TimeoutError, ValueError, KeyError, IndexError, RuntimeError) as e:
            logger.error("LLM creative generation error: %s", e)
            raise

    def _build_prompt(
        self,
        request: CreativeGenerateRequest,
        constraints: dict,
    ) -> str:
        """Build the LLM prompt for creative generation."""
        cta_options = ", ".join(constraints["cta_options"])

        return f"""You are an expert advertising copywriter specializing in book marketing.
Generate {request.num_variations} ad creative variations for the following book.

BOOK DETAILS:
- Title: {request.book_title}
- Description: {request.book_description}
- Genre: {request.genre or "Not specified"}
- Target Audience: {request.target_audience or "General readers"}
- Desired Tone: {request.tone}

PLATFORM: {request.platform.value}
CONSTRAINTS:
- Headline max length: {constraints["headline_max_length"]} characters
- Body text max length: {constraints["body_max_length"]} characters
- Available CTAs: {cta_options}
- {constraints["guidelines"]}

OUTPUT FORMAT (JSON array):
[
  {{
    "headline": "...",
    "body_text": "...",
    "call_to_action": "...",
    "reasoning": "Brief explanation of the creative approach"
  }}
]

Generate exactly {request.num_variations} variations with different angles/approaches.
Respond ONLY with the JSON array, no other text."""

    def _parse_llm_response(
        self,
        content: str,
        constraints: dict,
    ) -> list[GeneratedCreative]:
        """Parse LLM response into GeneratedCreative objects."""
        try:
            # Try to extract JSON from the response
            # Handle cases where LLM wraps in markdown code blocks
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()

            data = json.loads(cleaned)
            if not isinstance(data, list):
                data = [data]

            creatives = []
            for item in data:
                headline = item.get("headline", "")[: constraints["headline_max_length"]]
                body_text = item.get("body_text", "")[: constraints["body_max_length"]]
                cta = item.get("call_to_action", constraints["cta_options"][0])
                if cta not in constraints["cta_options"]:
                    cta = constraints["cta_options"][0]

                creatives.append(
                    GeneratedCreative(
                        headline=headline,
                        body_text=body_text,
                        call_to_action=cta,
                        reasoning=item.get("reasoning", ""),
                    )
                )

            return creatives
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    def _generate_with_templates(
        self,
        request: CreativeGenerateRequest,
        constraints: dict,
    ) -> list[GeneratedCreative]:
        """Generate creatives using templates as fallback when LLM is unavailable."""
        title = request.book_title
        genre = request.genre or "book"
        audience = request.target_audience or "readers"
        cta_options = constraints["cta_options"]

        templates = [
            GeneratedCreative(
                headline=_truncate(f"Discover {title}", constraints["headline_max_length"]),
                body_text=_truncate(
                    f"Looking for your next great {genre} read? "
                    f"{title} delivers exactly what {audience} are searching for. "
                    f"Start reading today.",
                    constraints["body_max_length"],
                ),
                call_to_action=cta_options[0],
                reasoning="Discovery angle - appeals to reader curiosity",
            ),
            GeneratedCreative(
                headline=_truncate(f"{title} - A Must-Read", constraints["headline_max_length"]),
                body_text=_truncate(
                    f"Join thousands of {audience} who have already discovered {title}. "
                    f"This {genre} masterpiece will keep you turning pages.",
                    constraints["body_max_length"],
                ),
                call_to_action=cta_options[1] if len(cta_options) > 1 else cta_options[0],
                reasoning="Social proof angle - emphasizes popularity",
            ),
            GeneratedCreative(
                headline=_truncate(f"New Release: {title}", constraints["headline_max_length"]),
                body_text=_truncate(
                    f"Fresh off the press! {title} is the {genre} experience "
                    f"that {audience} have been waiting for. Don't miss out.",
                    constraints["body_max_length"],
                ),
                call_to_action=cta_options[0],
                reasoning="Urgency/newness angle - creates FOMO",
            ),
            GeneratedCreative(
                headline=_truncate(f"Your Next Favorite {genre.title()}", constraints["headline_max_length"]),
                body_text=_truncate(
                    f"{title} has everything {audience} love: compelling characters, "
                    f"gripping story, and unforgettable moments.",
                    constraints["body_max_length"],
                ),
                call_to_action=cta_options[1] if len(cta_options) > 1 else cta_options[0],
                reasoning="Benefits angle - focuses on reader experience",
            ),
            GeneratedCreative(
                headline=_truncate(f"Can't Put It Down: {title}", constraints["headline_max_length"]),
                body_text=_truncate(
                    f"Readers are calling {title} impossible to put down. "
                    f"The perfect {genre} for {audience} who demand quality.",
                    constraints["body_max_length"],
                ),
                call_to_action=cta_options[0],
                reasoning="Endorsement angle - uses reader testimonial framing",
            ),
        ]

        return templates[: request.num_variations]


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
