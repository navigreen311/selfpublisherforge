"""AI-powered social media content generator.

Generates platform-specific social media posts for book marketing:
- Twitter (280 chars, hashtags)
- Facebook (longer posts, engagement-focused)
- Instagram (visual captions, hashtags)
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from app.config import get_settings
from app.models.marketing import SocialPlatform
from app.modules.marketing.schemas import (
    GenerateSocialContentRequest,
    SocialPostCreate,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Platform-specific templates
# ---------------------------------------------------------------------------

TWITTER_TEMPLATES = [
    "Excited to announce my new {genre} book '{book_title}'! {short_desc} #BookLaunch #IndieAuthor #{genre_hashtag}",
    "What if {hook}? Find out in '{book_title}' - available now! {buy_link} #{genre_hashtag} #NewRelease",
    "'{book_title}' is here! Perfect for fans of {comp_authors}. Grab your copy today! #{genre_hashtag} #BookRecommendation",
]

FACEBOOK_TEMPLATES = [
    (
        "I am thrilled to share that my new {genre} book, '{book_title}', is now available!\n\n"
        "{book_description}\n\n"
        "This book has been a labor of love, and I cannot wait for you to read it. "
        "If this sounds like your kind of story, I would be so grateful if you checked it out.\n\n"
        "Link in comments!"
    ),
    (
        "BIG NEWS! '{book_title}' is officially live!\n\n"
        "What it is about:\n{book_description}\n\n"
        "Who it is for: Anyone who loves {genre} stories that {appeal}.\n\n"
        "Thank you to everyone who has supported me on this journey. "
        "Your encouragement means everything!"
    ),
    (
        "Do you ever wonder {hook}?\n\n"
        "That is the question at the heart of my new book '{book_title}'. "
        "I wrote this story because {motivation}.\n\n"
        "If you are looking for a {genre} read that will {promise}, "
        "I think you will love this one.\n\n"
        "Available now - link in comments!"
    ),
]

INSTAGRAM_TEMPLATES = [
    (
        "NEW BOOK ALERT!\n\n"
        "'{book_title}' is here, and I could not be more excited to share it with you.\n\n"
        "{book_description}\n\n"
        "Swipe to see a sneak peek inside!\n\n"
        "#{genre_hashtag} #BookLaunch #NewRelease #IndieAuthor #BookStagram "
        "#ReadersOfInstagram #BookLovers #{genre_hashtag}Books"
    ),
    (
        "The wait is over! '{book_title}' drops TODAY.\n\n"
        "{short_desc}\n\n"
        "Who is ready to dive in? Tag a friend who would love this!\n\n"
        "#{genre_hashtag} #NewBook #MustRead #BookRecommendation "
        "#BookStagram #ReadingCommunity"
    ),
    (
        "Behind every book is a story of its own.\n\n"
        "'{book_title}' took {writing_time} to write, and every word was worth it. "
        "This is a story about {theme}.\n\n"
        "Available now - link in bio!\n\n"
        "#{genre_hashtag} #AuthorLife #WritingCommunity #IndiePublishing "
        "#BookStagram #NewRelease"
    ),
]


def _genre_to_hashtag(genre: str) -> str:
    """Convert a genre string to a hashtag-friendly format."""
    return genre.replace(" ", "").replace("-", "").replace("'", "")


class SocialContentGenerator:
    """Generates social media content for book marketing."""

    async def generate_content(
        self,
        request: GenerateSocialContentRequest,
    ) -> list[SocialPostCreate]:
        """Generate social media posts for specified platforms.

        Uses template-based generation with smart defaults.
        Can be extended with LLM for fully custom content.
        """
        posts: list[SocialPostCreate] = []
        genre_hashtag = _genre_to_hashtag(request.genre)

        context = {
            "book_title": request.book_title,
            "genre": request.genre,
            "genre_hashtag": genre_hashtag,
            "target_audience": request.target_audience,
            "book_description": request.book_description,
            "short_desc": request.book_description[:100] + "..." if len(request.book_description) > 100 else request.book_description,
            "hook": f"you could {request.book_description[:50].lower().strip()}...",
            "comp_authors": "similar authors",
            "appeal": "keep you turning pages",
            "motivation": "the story demanded to be told",
            "promise": "keep you engaged from start to finish",
            "writing_time": "months",
            "theme": request.genre.lower(),
            "buy_link": "",
            "tone": request.tone,
        }

        for platform in request.platforms:
            platform_posts = self._generate_for_platform(
                platform=platform,
                context=context,
                num_posts=request.num_posts_per_platform,
                launch_plan_id=request.launch_plan_id,
            )
            posts.extend(platform_posts)

        return posts

    async def generate_content_with_ai(
        self,
        request: GenerateSocialContentRequest,
    ) -> list[SocialPostCreate]:
        """Generate social media content using an LLM.

        Falls back to template generation on failure.
        """
        try:
            return await self._call_llm_for_content(request)
        except (OSError, ValueError, KeyError, RuntimeError, TypeError) as exc:
            logger.warning(
                "LLM social content generation failed (%s: %s), using templates",
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            return await self.generate_content(request)

    def _generate_for_platform(
        self,
        platform: SocialPlatform,
        context: dict[str, Any],
        num_posts: int,
        launch_plan_id: UUID | None = None,
    ) -> list[SocialPostCreate]:
        """Generate posts for a specific platform."""
        templates_map = {
            SocialPlatform.TWITTER: TWITTER_TEMPLATES,
            SocialPlatform.FACEBOOK: FACEBOOK_TEMPLATES,
            SocialPlatform.INSTAGRAM: INSTAGRAM_TEMPLATES,
        }

        templates = templates_map.get(platform, TWITTER_TEMPLATES)
        posts = []
        genre_hashtag = context.get("genre_hashtag", "Books")

        hashtags_map = {
            SocialPlatform.TWITTER: [f"#{genre_hashtag}", "#BookLaunch", "#IndieAuthor"],
            SocialPlatform.FACEBOOK: [f"#{genre_hashtag}", "#NewBook"],
            SocialPlatform.INSTAGRAM: [
                f"#{genre_hashtag}", "#BookStagram", "#NewRelease",
                "#IndieAuthor", "#BookLovers", "#ReadersOfInstagram",
            ],
        }

        for i in range(min(num_posts, len(templates))):
            template = templates[i % len(templates)]
            try:
                content = template.format(**context)
            except (KeyError, IndexError):
                content = template

            # Enforce Twitter character limit
            if platform == SocialPlatform.TWITTER and len(content) > 280:
                content = content[:277] + "..."

            posts.append(
                SocialPostCreate(
                    platform=platform,
                    content=content,
                    hashtags=hashtags_map.get(platform, []),
                    launch_plan_id=launch_plan_id,
                )
            )

        return posts

    async def _call_llm_for_content(
        self,
        request: GenerateSocialContentRequest,
    ) -> list[SocialPostCreate]:
        """Call the LLM to generate custom social media content."""
        prompt = self._build_social_prompt(request)

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = await client.messages.create(
                model=settings.DEFAULT_LLM_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            content = message.content[0].text
            posts_data = json.loads(content)
            return self._parse_llm_social_response(request, posts_data)

        except ImportError:
            logger.warning("anthropic package not available")
            return await self.generate_content(request)
        except (json.JSONDecodeError, KeyError, IndexError):
            logger.warning("Failed to parse LLM social response")
            return await self.generate_content(request)

    def _build_social_prompt(self, request: GenerateSocialContentRequest) -> str:
        """Build a prompt for social media content generation."""
        platform_names = ", ".join(p.value for p in request.platforms)
        return f"""You are a social media marketing expert for book authors.
Generate {request.num_posts_per_platform} posts per platform for the following platforms: {platform_names}

Book Title: {request.book_title}
Genre: {request.genre}
Target Audience: {request.target_audience}
Book Description: {request.book_description}
Tone: {request.tone}

Platform-specific guidelines:
- Twitter: Max 280 characters. Include 2-3 relevant hashtags.
- Facebook: 100-300 words. Engaging, conversational. Include call to action.
- Instagram: Visual-focused caption. Include 5-10 relevant hashtags.

Respond ONLY with valid JSON:
{{
  "posts": [
    {{
      "platform": "twitter|facebook|instagram",
      "content": "The post content...",
      "hashtags": ["#tag1", "#tag2"]
    }}
  ]
}}"""

    def _parse_llm_social_response(
        self,
        request: GenerateSocialContentRequest,
        data: dict[str, Any],
    ) -> list[SocialPostCreate]:
        """Parse LLM response into social post creates."""
        posts = []
        for post_data in data.get("posts", []):
            platform_str = post_data.get("platform", "twitter")
            try:
                platform = SocialPlatform(platform_str)
            except ValueError:
                continue

            posts.append(
                SocialPostCreate(
                    platform=platform,
                    content=post_data.get("content", ""),
                    hashtags=post_data.get("hashtags", []),
                    launch_plan_id=request.launch_plan_id,
                )
            )

        return posts
