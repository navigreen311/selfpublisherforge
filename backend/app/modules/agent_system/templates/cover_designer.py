"""Cover Design Automation Agent Template.

Analyzes genre conventions, generates cover concepts, provides design
specifications, and recommends visual elements for book covers.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Cover Design Assistant",
    "slug": "cover-design-assistant",
    "description": (
        "Analyzes successful covers in your genre, identifies visual trends, "
        "generates detailed design briefs, and provides specific recommendations "
        "for colors, fonts, imagery, and layout that will help your book stand out."
    ),
    "category": "marketing",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 4.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 8192,
        "temperature": 0.7,
        "creativity_level": "high",
    },
    "steps": [
        {
            "title": "Analyze genre cover conventions",
            "description": "Research bestselling covers in the target genre to identify visual patterns",
            "agent_type": "research",
            "input_schema": {
                "genre": "string",
                "subgenre": "string",
                "target_audience": "string",
            },
            "estimated_tokens": 2500,
        },
        {
            "title": "Identify trending design elements",
            "description": "Catalog current trends in typography, color palettes, imagery styles, and layouts",
            "agent_type": "research",
            "input_schema": {
                "genre_covers": "array",
                "time_period": "string",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Generate design concepts",
            "description": "Create multiple cover concepts with detailed specifications",
            "agent_type": "marketing_copy",
            "input_schema": {
                "book_title": "string",
                "genre_conventions": "object",
                "book_description": "string",
            },
            "estimated_tokens": 3000,
        },
        {
            "title": "Provide design specifications",
            "description": "Generate detailed design brief with fonts, colors, imagery, and layout guidelines",
            "agent_type": "marketing_copy",
            "input_schema": {
                "selected_concept": "object",
            },
            "estimated_tokens": 2000,
        },
    ],
    "triggers": [
        {
            "type": "manual",
            "description": "User requests cover design analysis",
        },
        {
            "type": "event",
            "description": "Book manuscript completed",
            "event": "manuscript.completed",
        },
    ],
    "outputs": [
        {
            "name": "cover_concepts",
            "description": "3-5 detailed cover design concepts with visual descriptions",
            "format": "pdf",
        },
        {
            "name": "design_brief",
            "description": "Comprehensive design specifications for selected concept",
            "format": "markdown",
        },
        {
            "name": "genre_analysis",
            "description": "Visual trends analysis for the target genre",
            "format": "json",
        },
        {
            "name": "color_palette",
            "description": "Recommended color schemes with hex codes",
            "format": "json",
        },
        {
            "name": "font_recommendations",
            "description": "Specific font pairings for title and author name",
            "format": "json",
        },
    ],
}
