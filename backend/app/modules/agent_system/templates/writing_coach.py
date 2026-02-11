"""Writing Coach Agent Template.

Provides personalized writing feedback, identifies improvement areas,
tracks writing progress, and offers actionable suggestions for craft improvement.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Writing Coach Agent",
    "slug": "writing-coach",
    "description": (
        "Your personal writing mentor that analyzes your writing style, identifies "
        "areas for improvement, tracks your progress over time, and provides "
        "actionable feedback on pacing, character development, dialogue, and prose quality."
    ),
    "category": "writing",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 3.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 16384,
        "temperature": 0.5,
        "coaching_style": "constructive",  # constructive, detailed, encouraging
    },
    "steps": [
        {
            "title": "Analyze writing sample",
            "description": "Deep analysis of submitted text for style, voice, and technical elements",
            "agent_type": "editor",
            "input_schema": {
                "text": "string",
                "word_count": "number",
                "genre": "string",
            },
            "estimated_tokens": 4000,
        },
        {
            "title": "Identify strengths and weaknesses",
            "description": "Pinpoint specific areas of excellence and opportunities for improvement",
            "agent_type": "editor",
            "input_schema": {
                "analysis_results": "object",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Generate personalized exercises",
            "description": "Create targeted writing exercises to address identified weaknesses",
            "agent_type": "writing_assistant",
            "input_schema": {
                "weaknesses": "array",
                "skill_level": "string",
            },
            "estimated_tokens": 3000,
        },
        {
            "title": "Track progress over time",
            "description": "Compare current writing to previous samples to measure improvement",
            "agent_type": "research",
            "input_schema": {
                "current_analysis": "object",
                "historical_analyses": "array",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Provide coaching report",
            "description": "Compile comprehensive feedback with specific, actionable recommendations",
            "agent_type": "editor",
            "input_schema": {
                "all_analyses": "object",
            },
            "estimated_tokens": 3000,
        },
    ],
    "triggers": [
        {
            "type": "manual",
            "description": "User submits writing for feedback",
        },
        {
            "type": "event",
            "description": "Chapter completed",
            "event": "chapter.completed",
        },
        {
            "type": "scheduled",
            "description": "Weekly progress review",
            "schedule": "0 9 * * 5",  # Every Friday at 9 AM
        },
    ],
    "outputs": [
        {
            "name": "coaching_report",
            "description": "Detailed feedback report with strengths, weaknesses, and improvement plan",
            "format": "pdf",
        },
        {
            "name": "writing_exercises",
            "description": "Personalized exercises targeting specific skill gaps",
            "format": "markdown",
        },
        {
            "name": "progress_metrics",
            "description": "Quantitative metrics showing writing improvement over time",
            "format": "json",
        },
        {
            "name": "style_profile",
            "description": "Analysis of unique writing voice and style characteristics",
            "format": "json",
        },
    ],
}
