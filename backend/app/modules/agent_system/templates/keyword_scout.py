"""Keyword Scout Agent Template.

Discovers high-value keywords, analyzes search volume and competition,
recommends keyword strategies for book metadata, and optimizes for discoverability.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Keyword Scout Agent",
    "slug": "keyword-scout",
    "description": (
        "Discovers high-value keywords with strong search volume and low competition, "
        "analyzes keyword trends in your genre, recommends optimal keyword combinations "
        "for your book metadata, and helps maximize discoverability on retail platforms."
    ),
    "category": "research",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 3.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "temperature": 0.3,
        "keyword_count": 50,
        "min_search_volume": 100,
    },
    "steps": [
        {
            "title": "Generate keyword candidates",
            "description": "Create comprehensive list of potential keywords based on book content and genre",
            "agent_type": "research",
            "input_schema": {
                "book_description": "string",
                "genre": "string",
                "themes": "array",
                "tropes": "array",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Analyze keyword metrics",
            "description": "Research search volume, competition, and ranking difficulty for each keyword",
            "agent_type": "research",
            "input_schema": {
                "keyword_candidates": "array",
                "platform": "string",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Identify keyword opportunities",
            "description": "Score and rank keywords based on opportunity (high volume, low competition)",
            "agent_type": "research",
            "input_schema": {
                "keyword_metrics": "object",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Generate keyword strategy",
            "description": "Create optimized keyword combinations for different metadata fields",
            "agent_type": "marketing_copy",
            "input_schema": {
                "top_keywords": "array",
                "metadata_limits": "object",
            },
            "estimated_tokens": 1500,
        },
    ],
    "triggers": [
        {
            "type": "manual",
            "description": "User requests keyword research",
        },
        {
            "type": "event",
            "description": "Book ready for metadata optimization",
            "event": "book.metadata_stage",
        },
        {
            "type": "scheduled",
            "description": "Monthly keyword trend update",
            "schedule": "0 0 15 * *",  # 15th of each month
        },
    ],
    "outputs": [
        {
            "name": "keyword_report",
            "description": "Comprehensive keyword research report with recommendations",
            "format": "pdf",
        },
        {
            "name": "keyword_scores",
            "description": "Ranked list of keywords with opportunity scores",
            "format": "json",
        },
        {
            "name": "metadata_recommendations",
            "description": "Optimized keyword combinations for title, subtitle, description, and backend keywords",
            "format": "json",
        },
        {
            "name": "competitor_keywords",
            "description": "Keywords used by successful competitors",
            "format": "json",
        },
    ],
}
