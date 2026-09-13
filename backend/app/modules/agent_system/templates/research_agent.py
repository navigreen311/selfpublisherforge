"""Market Research Agent Template.

Analyzes market trends, identifies profitable niches, evaluates competition,
and discovers keyword opportunities for self-publishers.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Market Research Agent",
    "slug": "market-research",
    "description": (
        "Analyzes market trends, niches, and competition to identify profitable "
        "opportunities. Researches bestseller lists, competitor strategies, reader "
        "preferences, and emerging trends in your genre."
    ),
    "category": "research",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 5.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 8192,
        "temperature": 0.3,
        "auto_refresh_interval_hours": 24,
    },
    "steps": [
        {
            "title": "Analyze bestseller lists",
            "description": (
                "Scrape and analyze current bestseller rankings across major platforms " "(Amazon, Apple Books, etc.)"
            ),
            "agent_type": "research",
            "input_schema": {
                "genre": "string",
                "subgenres": "array",
                "platforms": "array",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Identify trending topics and themes",
            "description": "Analyze trending topics, tropes, and themes within the target genre",
            "agent_type": "research",
            "input_schema": {
                "genre": "string",
                "time_period": "string",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Evaluate competition density",
            "description": "Assess competition levels for identified niches and sub-genres",
            "agent_type": "research",
            "input_schema": {
                "niches": "array",
                "competition_threshold": "number",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Generate opportunity report",
            "description": "Compile findings into actionable market opportunity report with recommendations",
            "agent_type": "research",
            "input_schema": {
                "analysis_data": "object",
            },
            "estimated_tokens": 3000,
        },
    ],
    "triggers": [
        {
            "type": "manual",
            "description": "User initiates market research",
        },
        {
            "type": "scheduled",
            "description": "Weekly market trend updates",
            "schedule": "0 0 * * 1",  # Every Monday at midnight
        },
        {
            "type": "event",
            "description": "New book project created",
            "event": "project.created",
        },
    ],
    "outputs": [
        {
            "name": "market_analysis_report",
            "description": "Comprehensive PDF report with market trends, niche opportunities, and competition analysis",
            "format": "pdf",
        },
        {
            "name": "bestseller_data",
            "description": "Structured data of current bestsellers in target genres",
            "format": "json",
        },
        {
            "name": "opportunity_scores",
            "description": "Ranked list of market opportunities with profitability scores",
            "format": "json",
        },
    ],
}
