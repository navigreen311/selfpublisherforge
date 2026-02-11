"""Social Media Content Agent Template.

Generates engaging social media content, creates platform-specific posts,
schedules content calendars, and maintains consistent author brand voice.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Social Content Agent",
    "slug": "social-content-agent",
    "description": (
        "Generates engaging, on-brand social media content tailored to each platform "
        "(Twitter, Instagram, Facebook, TikTok). Creates content calendars, writes "
        "captions, suggests hashtags, and maintains consistent author voice across all channels."
    ),
    "category": "marketing",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 3.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "temperature": 0.8,
        "content_days": 30,
        "posts_per_week": 5,
    },
    "steps": [
        {
            "title": "Analyze author brand voice",
            "description": "Establish consistent brand voice and content themes from existing content",
            "agent_type": "marketing_copy",
            "input_schema": {
                "author_bio": "string",
                "book_themes": "array",
                "sample_posts": "array",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Generate content ideas",
            "description": "Create diverse content ideas aligned with author brand and marketing goals",
            "agent_type": "marketing_copy",
            "input_schema": {
                "brand_voice": "object",
                "content_pillars": "array",
                "upcoming_releases": "array",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Create platform-specific posts",
            "description": "Write posts optimized for each social media platform's format and audience",
            "agent_type": "marketing_copy",
            "input_schema": {
                "content_ideas": "array",
                "platforms": "array",
                "character_limits": "object",
            },
            "estimated_tokens": 3000,
        },
        {
            "title": "Build content calendar",
            "description": "Organize posts into a scheduled content calendar with optimal posting times",
            "agent_type": "marketing_copy",
            "input_schema": {
                "posts": "array",
                "posting_frequency": "object",
                "time_zones": "string",
            },
            "estimated_tokens": 1500,
        },
    ],
    "triggers": [
        {
            "type": "scheduled",
            "description": "Weekly content generation",
            "schedule": "0 10 * * 0",  # Every Sunday at 10 AM
        },
        {
            "type": "event",
            "description": "New book announcement",
            "event": "book.announcement",
        },
        {
            "type": "manual",
            "description": "User requests social content",
        },
    ],
    "outputs": [
        {
            "name": "content_calendar",
            "description": "30-day content calendar with scheduled posts for all platforms",
            "format": "json",
        },
        {
            "name": "social_posts",
            "description": "Ready-to-publish posts with captions, hashtags, and image suggestions",
            "format": "markdown",
        },
        {
            "name": "hashtag_research",
            "description": "Recommended hashtags for each platform and content type",
            "format": "json",
        },
        {
            "name": "engagement_prompts",
            "description": "Questions and prompts designed to drive audience engagement",
            "format": "markdown",
        },
        {
            "name": "brand_voice_guide",
            "description": "Documentation of author brand voice and content guidelines",
            "format": "pdf",
        },
    ],
}
