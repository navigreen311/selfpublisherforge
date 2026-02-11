"""Agent marketplace template registry.

This module provides pre-built agent templates for common self-publishing workflows.
Each template defines a complete agent configuration including workflow steps, triggers,
and expected outputs.
"""

from typing import Any

from .backlist_analyzer import TEMPLATE as BACKLIST_ANALYZER_TEMPLATE
from .competitor_tracker import TEMPLATE as COMPETITOR_TRACKER_TEMPLATE
from .cover_designer import TEMPLATE as COVER_DESIGNER_TEMPLATE
from .keyword_scout import TEMPLATE as KEYWORD_SCOUT_TEMPLATE
from .launch_planner import TEMPLATE as LAUNCH_PLANNER_TEMPLATE
from .price_optimizer import TEMPLATE as PRICE_OPTIMIZER_TEMPLATE
from .research_agent import TEMPLATE as RESEARCH_TEMPLATE
from .review_monitor import TEMPLATE as REVIEW_MONITOR_TEMPLATE
from .social_content import TEMPLATE as SOCIAL_CONTENT_TEMPLATE
from .writing_coach import TEMPLATE as WRITING_COACH_TEMPLATE

# Template registry
_TEMPLATES: list[dict[str, Any]] = [
    RESEARCH_TEMPLATE,
    WRITING_COACH_TEMPLATE,
    COVER_DESIGNER_TEMPLATE,
    PRICE_OPTIMIZER_TEMPLATE,
    REVIEW_MONITOR_TEMPLATE,
    KEYWORD_SCOUT_TEMPLATE,
    LAUNCH_PLANNER_TEMPLATE,
    COMPETITOR_TRACKER_TEMPLATE,
    SOCIAL_CONTENT_TEMPLATE,
    BACKLIST_ANALYZER_TEMPLATE,
]


def list_templates(category: str | None = None, tier: str | None = None) -> list[dict[str, Any]]:
    """List all available agent templates with optional filters.

    Args:
        category: Filter by category (research, marketing, writing, automation)
        tier: Filter by tier (free, pro, enterprise)

    Returns:
        List of template dictionaries
    """
    templates = _TEMPLATES

    if category:
        templates = [t for t in templates if t.get("category") == category]

    if tier:
        templates = [t for t in templates if t.get("tier") == tier]

    return templates


def get_template(slug: str) -> dict[str, Any] | None:
    """Get a specific template by slug.

    Args:
        slug: Template slug (e.g., "market-research")

    Returns:
        Template dictionary or None if not found
    """
    for template in _TEMPLATES:
        if template.get("slug") == slug:
            return template
    return None


def validate_template(template: dict[str, Any]) -> bool:
    """Validate that a template has all required fields.

    Args:
        template: Template dictionary to validate

    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = [
        "name", "slug", "description", "category", "tier",
        "default_config", "steps", "triggers", "outputs"
    ]

    for field in required_fields:
        if field not in template:
            raise ValueError(f"Template missing required field: {field}")

    # Validate steps structure
    if not isinstance(template["steps"], list) or len(template["steps"]) == 0:
        raise ValueError("Template must have at least one step")

    for step in template["steps"]:
        if not isinstance(step, dict):
            raise ValueError("Each step must be a dictionary")
        if "title" not in step or "description" not in step:
            raise ValueError("Each step must have 'title' and 'description'")

    # Validate triggers
    if not isinstance(template["triggers"], list):
        raise ValueError("Triggers must be a list")

    # Validate outputs
    if not isinstance(template["outputs"], list):
        raise ValueError("Outputs must be a list")

    return True


# Validate all templates on import
for tmpl in _TEMPLATES:
    validate_template(tmpl)
