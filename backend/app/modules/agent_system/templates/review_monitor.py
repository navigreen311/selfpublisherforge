"""Review Monitoring Agent Template.

Monitors book reviews across platforms, analyzes sentiment, identifies patterns,
generates response templates, and alerts on important review activity.
"""

from typing import Any

TEMPLATE: dict[str, Any] = {
    "name": "Review Monitor Agent",
    "slug": "review-monitor",
    "description": (
        "Continuously monitors reviews across all platforms, analyzes sentiment and themes, "
        "identifies common praise and complaints, generates suggested responses, and alerts "
        "you to critical reviews or significant review milestones."
    ),
    "category": "automation",
    "tier": "pro",
    "default_config": {
        "max_budget_usd": 2.0,
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "temperature": 0.3,
        "alert_threshold": 3.5,  # Alert on reviews below this rating
        "check_interval_hours": 6,
    },
    "steps": [
        {
            "title": "Collect new reviews",
            "description": "Gather new reviews from Amazon, Goodreads, Apple Books, and other platforms",
            "agent_type": "research",
            "input_schema": {
                "book_ids": "object",
                "platforms": "array",
                "last_check": "string",
            },
            "estimated_tokens": 1000,
        },
        {
            "title": "Analyze sentiment and themes",
            "description": "Perform sentiment analysis and identify common themes in reviews",
            "agent_type": "research",
            "input_schema": {
                "reviews": "array",
            },
            "estimated_tokens": 2000,
        },
        {
            "title": "Generate response templates",
            "description": "Create personalized response templates for different review types",
            "agent_type": "marketing_copy",
            "input_schema": {
                "review_categories": "object",
                "author_voice": "string",
            },
            "estimated_tokens": 1500,
        },
        {
            "title": "Create alert notifications",
            "description": "Generate notifications for critical reviews or important milestones",
            "agent_type": "marketing_copy",
            "input_schema": {
                "critical_reviews": "array",
                "milestones": "array",
            },
            "estimated_tokens": 1000,
        },
    ],
    "triggers": [
        {
            "type": "scheduled",
            "description": "Regular review monitoring",
            "schedule": "0 */6 * * *",  # Every 6 hours
        },
        {
            "type": "event",
            "description": "New book launched",
            "event": "book.launched",
        },
        {
            "type": "manual",
            "description": "User requests review analysis",
        },
    ],
    "outputs": [
        {
            "name": "review_summary",
            "description": "Summary of recent reviews with sentiment analysis",
            "format": "markdown",
        },
        {
            "name": "theme_analysis",
            "description": "Common themes, praise points, and complaint patterns",
            "format": "json",
        },
        {
            "name": "response_templates",
            "description": "Suggested responses for different review types",
            "format": "markdown",
        },
        {
            "name": "alerts",
            "description": "Critical review alerts and milestone notifications",
            "format": "json",
        },
        {
            "name": "sentiment_trends",
            "description": "Sentiment trends over time",
            "format": "json",
        },
    ],
}
