"""Launch Planner Agent Template.

Creates comprehensive book launch plans, coordinates marketing activities,
generates promotional timelines, and provides day-by-day launch checklists.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Launch Planner Agent",
    "slug": "launch-planner",
    "description": (
        "Creates comprehensive, customized book launch plans with detailed timelines, "
        "marketing activity coordination, promotional sequences, and day-by-day checklists. "
        "Considers your marketing budget, author platform size, and genre-specific strategies."
    ),
    "category": "marketing",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 4.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 8192,
        "temperature": 0.5,
        "launch_window_days": 30,
    },
    "steps": [
        {
            "title": "Assess launch parameters",
            "description": "Gather book details, marketing budget, platform size, and launch goals",
            "agent_type": "research",
            "input_schema": {
                "book_details": "object",
                "marketing_budget": "number",
                "author_platform": "object",
                "launch_goals": "object",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Research genre launch strategies",
            "description": "Analyze successful launches in the same genre",
            "agent_type": "research",
            "input_schema": {
                "genre": "string",
                "comparable_books": "array",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Create launch timeline",
            "description": "Generate detailed pre-launch, launch day, and post-launch timelines",
            "agent_type": "marketing_copy",
            "input_schema": {
                "launch_date": "string",
                "activities": "array",
                "milestones": "array",
            },
            "estimated_tokens": 3000,
        },
        {
            "title": "Generate marketing copy",
            "description": "Create promotional emails, social posts, and ad copy for the launch",
            "agent_type": "marketing_copy",
            "input_schema": {
                "book_description": "string",
                "target_audience": "string",
                "key_themes": "array",
            },
            "estimated_tokens": 3000,
        },
        {
            "title": "Compile launch checklist",
            "description": "Create comprehensive day-by-day checklist with all tasks and deadlines",
            "agent_type": "marketing_copy",
            "input_schema": {
                "timeline": "object",
                "marketing_copy": "object",
            },
            "estimated_tokens": 2000,
        },
    ],
    "triggers": [
        {
            "type": "manual",
            "description": "User requests launch plan",
        },
        {
            "type": "event",
            "description": "Book manuscript finalized",
            "event": "manuscript.finalized",
        },
    ],
    "outputs": [
        {
            "name": "launch_plan",
            "description": "Comprehensive launch plan with strategy, timeline, and tactics",
            "format": "pdf",
        },
        {
            "name": "timeline",
            "description": "Detailed timeline with all pre-launch, launch, and post-launch activities",
            "format": "json",
        },
        {
            "name": "checklist",
            "description": "Day-by-day launch checklist with tasks and deadlines",
            "format": "markdown",
        },
        {
            "name": "marketing_copy",
            "description": "All promotional emails, social posts, and ad copy ready to use",
            "format": "markdown",
        },
        {
            "name": "budget_allocation",
            "description": "Recommended marketing spend allocation across channels",
            "format": "json",
        },
    ],
}
