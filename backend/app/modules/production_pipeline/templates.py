"""Pre-built pipeline templates for common book publishing workflows."""

from __future__ import annotations

NONFICTION_TEMPLATE = {
    "name": "Nonfiction Book",
    "description": "8-stage pipeline for nonfiction books",
    "stages": [
        {
            "name": "Research & Outline",
            "color": "#6366f1",
            "tasks": [
                {"title": "Define target audience and reader avatar", "priority": "high"},
                {"title": "Create detailed chapter outline", "priority": "high"},
                {"title": "Research competing titles", "priority": "medium"},
                {"title": "Gather source materials and references", "priority": "medium"},
            ],
        },
        {
            "name": "Writing",
            "color": "#8b5cf6",
            "tasks": [
                {"title": "Write first draft - chapters 1-3", "priority": "high"},
                {"title": "Write first draft - chapters 4-6", "priority": "high"},
                {"title": "Write first draft - remaining chapters", "priority": "high"},
                {"title": "Write introduction and conclusion", "priority": "medium"},
                {"title": "Add case studies and examples", "priority": "medium"},
            ],
        },
        {
            "name": "Editing",
            "color": "#a78bfa",
            "tasks": [
                {"title": "Self-edit full manuscript", "priority": "high"},
                {"title": "Send to developmental editor", "priority": "high"},
                {"title": "Implement editor feedback", "priority": "high"},
                {"title": "Copy editing pass", "priority": "medium"},
            ],
        },
        {
            "name": "Cover Design",
            "color": "#c084fc",
            "tasks": [
                {"title": "Brief cover designer with comp titles", "priority": "high"},
                {"title": "Review cover concepts", "priority": "medium"},
                {"title": "Approve final cover design", "priority": "high"},
            ],
        },
        {
            "name": "Formatting",
            "color": "#e879f9",
            "tasks": [
                {"title": "Format ebook (EPUB/MOBI)", "priority": "high"},
                {"title": "Format paperback interior", "priority": "high"},
                {"title": "Create front/back matter", "priority": "medium"},
                {"title": "Final proofread of formatted files", "priority": "high"},
            ],
        },
        {
            "name": "Pre-Launch",
            "color": "#f472b6",
            "tasks": [
                {"title": "Set up Amazon listing (title, blurb, keywords)", "priority": "high"},
                {"title": "Create ARC campaign", "priority": "high"},
                {"title": "Build email launch sequence", "priority": "medium"},
                {"title": "Schedule social media announcements", "priority": "medium"},
                {"title": "Set up pre-order (if applicable)", "priority": "low"},
            ],
        },
        {
            "name": "Launch",
            "color": "#fb923c",
            "tasks": [
                {"title": "Publish on KDP", "priority": "high"},
                {"title": "Send launch emails", "priority": "high"},
                {"title": "Post launch announcements on social", "priority": "high"},
                {"title": "Monitor sales rank and reviews", "priority": "medium"},
            ],
        },
        {
            "name": "Post-Launch",
            "color": "#fbbf24",
            "tasks": [
                {"title": "Request reviews from readers", "priority": "high"},
                {"title": "Analyze first-week sales data", "priority": "medium"},
                {"title": "Set up Amazon Ads campaign", "priority": "medium"},
                {"title": "Plan next book or edition", "priority": "low"},
            ],
        },
    ],
}

FICTION_TEMPLATE = {
    "name": "Fiction Novel",
    "description": "8-stage pipeline for fiction novels",
    "stages": [
        {
            "name": "Planning & Outline",
            "color": "#6366f1",
            "tasks": [
                {"title": "Develop protagonist and character profiles", "priority": "high"},
                {"title": "Create plot outline (3-act structure)", "priority": "high"},
                {"title": "Build world/setting details", "priority": "medium"},
                {"title": "Write chapter-by-chapter synopsis", "priority": "medium"},
            ],
        },
        {
            "name": "First Draft",
            "color": "#8b5cf6",
            "tasks": [
                {"title": "Write Act 1 (chapters 1-8)", "priority": "high"},
                {"title": "Write Act 2 (chapters 9-20)", "priority": "high"},
                {"title": "Write Act 3 (chapters 21-end)", "priority": "high"},
                {"title": "Complete first draft review", "priority": "medium"},
            ],
        },
        {
            "name": "Revision",
            "color": "#a78bfa",
            "tasks": [
                {"title": "Structural revision pass", "priority": "high"},
                {"title": "Character arc consistency check", "priority": "high"},
                {"title": "Dialogue polish pass", "priority": "medium"},
                {"title": "Pacing and tension review", "priority": "medium"},
            ],
        },
        {
            "name": "Beta Readers",
            "color": "#c084fc",
            "tasks": [
                {"title": "Send to 3-5 beta readers", "priority": "high"},
                {"title": "Collect and organize feedback", "priority": "high"},
                {"title": "Implement beta reader changes", "priority": "high"},
            ],
        },
        {
            "name": "Professional Edit",
            "color": "#e879f9",
            "tasks": [
                {"title": "Developmental edit", "priority": "high"},
                {"title": "Implement dev edit feedback", "priority": "high"},
                {"title": "Line editing pass", "priority": "medium"},
                {"title": "Final proofread", "priority": "high"},
            ],
        },
        {
            "name": "Cover & Formatting",
            "color": "#f472b6",
            "tasks": [
                {"title": "Commission cover design", "priority": "high"},
                {"title": "Format ebook and print editions", "priority": "high"},
                {"title": "Create front and back matter", "priority": "medium"},
            ],
        },
        {
            "name": "Pre-Launch",
            "color": "#fb923c",
            "tasks": [
                {"title": "Optimize Amazon listing", "priority": "high"},
                {"title": "Send ARCs to reviewers", "priority": "high"},
                {"title": "Build email launch sequence", "priority": "medium"},
                {"title": "Plan social media campaign", "priority": "medium"},
            ],
        },
        {
            "name": "Launch",
            "color": "#fbbf24",
            "tasks": [
                {"title": "Hit publish on all platforms", "priority": "high"},
                {"title": "Execute launch day marketing", "priority": "high"},
                {"title": "Engage readers and respond to reviews", "priority": "medium"},
                {"title": "Track and optimize ad campaigns", "priority": "medium"},
            ],
        },
    ],
}

SHORT_STORY_TEMPLATE = {
    "name": "Short Story / Novella",
    "description": "5-stage pipeline for shorter works",
    "stages": [
        {
            "name": "Planning",
            "color": "#6366f1",
            "tasks": [
                {"title": "Outline story arc", "priority": "high"},
                {"title": "Define characters and setting", "priority": "medium"},
            ],
        },
        {
            "name": "Writing",
            "color": "#8b5cf6",
            "tasks": [
                {"title": "Write complete first draft", "priority": "high"},
                {"title": "Self-edit and revise", "priority": "high"},
            ],
        },
        {
            "name": "Editing",
            "color": "#a78bfa",
            "tasks": [
                {"title": "Professional edit/proofread", "priority": "high"},
                {"title": "Final revision pass", "priority": "medium"},
            ],
        },
        {
            "name": "Production",
            "color": "#e879f9",
            "tasks": [
                {"title": "Cover design", "priority": "high"},
                {"title": "Format ebook", "priority": "high"},
            ],
        },
        {
            "name": "Publish",
            "color": "#fbbf24",
            "tasks": [
                {"title": "Create listing and publish", "priority": "high"},
                {"title": "Announce to mailing list", "priority": "medium"},
            ],
        },
    ],
}

SERIES_LAUNCH_TEMPLATE = {
    "name": "Series Launch",
    "description": "9-stage pipeline for launching a book series",
    "stages": [
        {
            "name": "Series Planning",
            "color": "#6366f1",
            "tasks": [
                {"title": "Plan series arc across all books", "priority": "high"},
                {"title": "Create series bible (characters, world, timeline)", "priority": "high"},
                {"title": "Design series branding (covers, typography)", "priority": "medium"},
            ],
        },
        {
            "name": "Book 1 Draft",
            "color": "#8b5cf6",
            "tasks": [
                {"title": "Outline Book 1", "priority": "high"},
                {"title": "Write Book 1 first draft", "priority": "high"},
            ],
        },
        {
            "name": "Book 1 Edit",
            "color": "#a78bfa",
            "tasks": [
                {"title": "Revise and edit Book 1", "priority": "high"},
                {"title": "Beta readers for Book 1", "priority": "high"},
                {"title": "Professional edit Book 1", "priority": "high"},
            ],
        },
        {
            "name": "Book 1 Production",
            "color": "#c084fc",
            "tasks": [
                {"title": "Cover design Book 1", "priority": "high"},
                {"title": "Format and proofread Book 1", "priority": "high"},
            ],
        },
        {
            "name": "Book 2 Draft",
            "color": "#e879f9",
            "tasks": [
                {"title": "Outline Book 2", "priority": "high"},
                {"title": "Write Book 2 first draft", "priority": "high"},
            ],
        },
        {
            "name": "Book 2 Edit & Production",
            "color": "#f472b6",
            "tasks": [
                {"title": "Edit and format Book 2", "priority": "high"},
                {"title": "Cover design Book 2", "priority": "high"},
            ],
        },
        {
            "name": "Series Pre-Launch",
            "color": "#fb923c",
            "tasks": [
                {"title": "Set up series page on Amazon", "priority": "high"},
                {"title": "Create series landing page", "priority": "medium"},
                {"title": "Build anticipation email sequence", "priority": "medium"},
                {"title": "ARC campaign for Book 1", "priority": "high"},
            ],
        },
        {
            "name": "Rapid Release Launch",
            "color": "#fbbf24",
            "tasks": [
                {"title": "Publish Book 1", "priority": "high"},
                {"title": "Publish Book 2 (2-4 weeks later)", "priority": "high"},
                {"title": "Cross-promote between books", "priority": "medium"},
            ],
        },
        {
            "name": "Series Growth",
            "color": "#34d399",
            "tasks": [
                {"title": "Monitor read-through rates", "priority": "high"},
                {"title": "Optimize Book 1 listing for sell-through", "priority": "medium"},
                {"title": "Plan Books 3+ based on reader feedback", "priority": "medium"},
            ],
        },
    ],
}

BLANK_TEMPLATE = {
    "name": "Blank Pipeline",
    "description": "Empty pipeline - add your own stages and tasks",
    "stages": [],
}

TEMPLATES: dict[str, dict] = {
    "nonfiction": NONFICTION_TEMPLATE,
    "fiction": FICTION_TEMPLATE,
    "short_story": SHORT_STORY_TEMPLATE,
    "series_launch": SERIES_LAUNCH_TEMPLATE,
    "blank": BLANK_TEMPLATE,
}


def get_template(template_name: str) -> dict | None:
    """Get a pipeline template by name."""
    return TEMPLATES.get(template_name)


def list_template_names() -> list[str]:
    """List all available template names."""
    return list(TEMPLATES.keys())
