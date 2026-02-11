"""Price Optimization Agent Template.

Analyzes pricing strategies, monitors competitor pricing, recommends optimal
price points, and suggests promotional pricing schedules for maximum revenue.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Price Optimizer Agent",
    "slug": "price-optimizer",
    "description": (
        "Analyzes pricing data across your genre, monitors competitor pricing strategies, "
        "calculates optimal price points based on page count and positioning, and recommends "
        "promotional pricing schedules to maximize revenue and visibility."
    ),
    "category": "marketing",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 3.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "temperature": 0.2,
        "optimization_goal": "revenue",  # revenue, visibility, balanced
    },
    "steps": [
        {
            "title": "Analyze competitor pricing",
            "description": "Collect and analyze pricing data from similar books in the genre",
            "agent_type": "research",
            "input_schema": {
                "genre": "string",
                "page_count": "number",
                "format": "string",
                "competitor_list": "array",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Calculate optimal base price",
            "description": "Determine optimal regular price based on market data and book characteristics",
            "agent_type": "research",
            "input_schema": {
                "market_data": "object",
                "page_count": "number",
                "author_platform": "string",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Design promotional schedule",
            "description": "Create strategic pricing schedule for launch and ongoing promotions",
            "agent_type": "marketing_copy",
            "input_schema": {
                "base_price": "number",
                "launch_date": "string",
                "marketing_goals": "object",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Monitor price performance",
            "description": "Track sales performance at different price points and recommend adjustments",
            "agent_type": "research",
            "input_schema": {
                "current_price": "number",
                "sales_data": "object",
                "rank_data": "object",
            },
            "estimated_tokens": 2000,
        },
    ],
    "triggers": [
        {
            "type": "manual",
            "description": "User requests pricing analysis",
        },
        {
            "type": "event",
            "description": "New book ready for pricing",
            "event": "book.ready_for_launch",
        },
        {
            "type": "scheduled",
            "description": "Monthly pricing review",
            "schedule": "0 0 1 * *",  # First day of each month
        },
    ],
    "outputs": [
        {
            "name": "pricing_strategy",
            "description": "Comprehensive pricing strategy with base price and promotional schedule",
            "format": "pdf",
        },
        {
            "name": "competitor_pricing_data",
            "description": "Structured data on competitor pricing in the genre",
            "format": "json",
        },
        {
            "name": "revenue_projections",
            "description": "Projected revenue at different price points",
            "format": "json",
        },
        {
            "name": "promotional_calendar",
            "description": "Recommended pricing changes over time",
            "format": "json",
        },
    ],
}
