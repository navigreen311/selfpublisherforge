"""Competitor Tracker Agent Template.

Monitors competitor book performance, tracks pricing changes, analyzes marketing
strategies, and provides competitive intelligence for strategic decision-making.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Competitor Tracker Agent",
    "slug": "competitor-tracker",
    "description": (
        "Continuously monitors your key competitors' book performance, tracks sales rank "
        "changes, pricing adjustments, new releases, review activity, and marketing strategies. "
        "Provides actionable competitive intelligence to inform your publishing decisions."
    ),
    "category": "research",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 3.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "temperature": 0.2,
        "check_interval_hours": 12,
        "max_competitors": 10,
    },
    "steps": [
        {
            "title": "Monitor competitor book data",
            "description": "Track sales ranks, prices, reviews, and other key metrics for competitor books",
            "agent_type": "research",
            "input_schema": {
                "competitor_books": "array",
                "platforms": "array",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Detect significant changes",
            "description": "Identify noteworthy changes in pricing, rankings, or review activity",
            "agent_type": "research",
            "input_schema": {
                "current_data": "object",
                "historical_data": "object",
                "change_thresholds": "object",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Analyze marketing strategies",
            "description": "Examine competitor marketing tactics, ad copy, promotional timing",
            "agent_type": "research",
            "input_schema": {
                "competitor_activities": "array",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Generate competitive insights",
            "description": "Compile actionable insights and strategic recommendations",
            "agent_type": "research",
            "input_schema": {
                "analysis_results": "object",
            },
            "estimated_tokens": 2000,
        },
    ],
    "triggers": [
        {
            "type": "scheduled",
            "description": "Regular competitor monitoring",
            "schedule": "0 */12 * * *",  # Every 12 hours
        },
        {
            "type": "event",
            "description": "Competitor launches new book",
            "event": "competitor.book_launch",
        },
        {
            "type": "manual",
            "description": "User requests competitor analysis",
        },
    ],
    "outputs": [
        {
            "name": "competitor_dashboard",
            "description": "Visual dashboard showing competitor metrics and trends",
            "format": "json",
        },
        {
            "name": "change_alerts",
            "description": "Notifications of significant competitor changes",
            "format": "json",
        },
        {
            "name": "strategy_analysis",
            "description": "Analysis of competitor marketing strategies and tactics",
            "format": "markdown",
        },
        {
            "name": "competitive_insights",
            "description": "Actionable recommendations based on competitive intelligence",
            "format": "pdf",
        },
        {
            "name": "performance_comparison",
            "description": "Comparative analysis of your books vs. competitors",
            "format": "json",
        },
    ],
}
