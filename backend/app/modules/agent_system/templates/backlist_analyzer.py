"""Backlist Optimization Agent Template.

Analyzes backlist performance, identifies underperforming titles with potential,
recommends optimization strategies, and creates action plans to revive older books.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Backlist Analyzer Agent",
    "slug": "backlist-analyzer",
    "description": (
        "Analyzes your backlist catalog to identify hidden opportunities, underperforming "
        "titles with revenue potential, and optimization strategies. Recommends cover updates, "
        "pricing changes, metadata improvements, and cross-promotion tactics to revive older books."
    ),
    "category": "automation",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 4.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 8192,
        "temperature": 0.4,
        "min_book_age_months": 6,
    },
    "steps": [
        {
            "title": "Collect backlist performance data",
            "description": "Gather sales, rank, review, and engagement data for all backlist titles",
            "agent_type": "research",
            "input_schema": {
                "book_catalog": "array",
                "platforms": "array",
                "date_range": "object",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Identify optimization opportunities",
            "description": "Analyze which books have untapped potential based on genre trends and performance",
            "agent_type": "research",
            "input_schema": {
                "performance_data": "object",
                "genre_trends": "object",
            },
            "estimated_tokens": 2500,
        },
        {
            "title": "Evaluate current metadata and positioning",
            "description": "Assess covers, descriptions, keywords, and pricing against current genre conventions",
            "agent_type": "research",
            "input_schema": {
                "book_metadata": "array",
                "genre_standards": "object",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Generate optimization recommendations",
            "description": "Create specific, prioritized recommendations for each backlist title",
            "agent_type": "marketing_copy",
            "input_schema": {
                "opportunities": "array",
                "metadata_gaps": "object",
            },
            "estimated_tokens": 3000,
        },
        {
            "title": "Create action plan",
            "description": "Develop prioritized action plan with estimated impact and effort for each optimization",
            "agent_type": "marketing_copy",
            "input_schema": {
                "recommendations": "array",
                "available_budget": "number",
            },
            "estimated_tokens": 2500,
        },
    ],
    "triggers": [
        {
            "type": "scheduled",
            "description": "Quarterly backlist review",
            "schedule": "0 0 1 */3 *",  # First day of every quarter
        },
        {
            "type": "manual",
            "description": "User requests backlist analysis",
        },
        {
            "type": "event",
            "description": "Book reaches 6 months old",
            "event": "book.age_milestone",
        },
    ],
    "outputs": [
        {
            "name": "backlist_analysis",
            "description": "Comprehensive analysis of backlist performance and opportunities",
            "format": "pdf",
        },
        {
            "name": "opportunity_scores",
            "description": "Ranked list of books with optimization potential and expected impact",
            "format": "json",
        },
        {
            "name": "optimization_recommendations",
            "description": "Specific recommendations for covers, pricing, metadata, and marketing",
            "format": "markdown",
        },
        {
            "name": "action_plan",
            "description": "Prioritized action plan with timeline and resource requirements",
            "format": "json",
        },
        {
            "name": "revenue_projections",
            "description": "Estimated revenue impact of recommended optimizations",
            "format": "json",
        },
    ],
}
