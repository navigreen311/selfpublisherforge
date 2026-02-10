"""Prompt templates for AI content generation.

Each template is a callable that accepts a context dict and returns a
fully-formed system/user prompt pair suitable for the LLM.
"""

from __future__ import annotations

from typing import Any, Callable


def _base_system_prompt(genre: str = "", tone: str = "") -> str:
    parts = [
        "You are an expert fiction and non-fiction author who writes compelling, "
        "well-structured prose. Follow the user's instructions precisely."
    ]
    if genre:
        parts.append(f"Genre: {genre}.")
    if tone:
        parts.append(f"Tone: {tone}.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Outline
# ---------------------------------------------------------------------------

def outline_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for outline generation."""
    genre = context.get("genre", "")
    premise = context.get("premise", "")
    num_chapters = context.get("num_chapters", 12)
    tone = context.get("tone", "")
    target_audience = context.get("target_audience", "")
    additional = context.get("additional_instructions", "")

    system = _base_system_prompt(genre, tone)
    user_parts = [
        f"Generate a detailed book outline with {num_chapters} chapters.",
    ]
    if premise:
        user_parts.append(f"Premise: {premise}")
    if target_audience:
        user_parts.append(f"Target audience: {target_audience}")
    if additional:
        user_parts.append(f"Additional instructions: {additional}")
    user_parts.append(
        "\nFor each chapter provide:\n"
        "- title\n"
        "- synopsis (2-3 sentences)\n"
        "- key_points (list of 2-4 bullet points)\n\n"
        "Return ONLY valid JSON with the structure:\n"
        '{"chapters": [{"title": "...", "synopsis": "...", "key_points": ["..."]}], '
        '"summary": "brief overall summary"}'
    )
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Chapter writing
# ---------------------------------------------------------------------------

def chapter_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for chapter generation."""
    genre = context.get("genre", "")
    tone = context.get("tone", "")
    chapter_title = context.get("chapter_title", "Untitled Chapter")
    synopsis = context.get("synopsis", "")
    previous_summary = context.get("previous_summary", "")
    instructions = context.get("instructions", "")
    target_words = context.get("target_words", 2000)

    system = _base_system_prompt(genre, tone)
    user_parts = [
        f"Write a full chapter titled \"{chapter_title}\".",
        f"Target word count: approximately {target_words} words.",
    ]
    if synopsis:
        user_parts.append(f"Chapter synopsis: {synopsis}")
    if previous_summary:
        user_parts.append(f"Summary of previous chapters: {previous_summary}")
    if instructions:
        user_parts.append(f"Special instructions: {instructions}")
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Blurb
# ---------------------------------------------------------------------------

def blurb_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for blurb / book description."""
    genre = context.get("genre", "")
    title = context.get("title", "")
    synopsis = context.get("synopsis", "")
    tone = context.get("tone", "")
    instructions = context.get("instructions", "")

    system = _base_system_prompt(genre, tone)
    user_parts = ["Write a compelling book blurb / back-cover description."]
    if title:
        user_parts.append(f"Book title: {title}")
    if synopsis:
        user_parts.append(f"Synopsis: {synopsis}")
    if instructions:
        user_parts.append(f"Special instructions: {instructions}")
    user_parts.append(
        "The blurb should hook the reader, hint at conflict, and end with intrigue."
    )
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Title suggestions
# ---------------------------------------------------------------------------

def title_suggestions_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for title suggestions."""
    genre = context.get("genre", "")
    synopsis = context.get("synopsis", "")
    tone = context.get("tone", "")
    num_suggestions = context.get("num_suggestions", 10)
    instructions = context.get("instructions", "")

    system = _base_system_prompt(genre, tone)
    user_parts = [
        f"Suggest {num_suggestions} compelling book titles.",
    ]
    if synopsis:
        user_parts.append(f"Synopsis: {synopsis}")
    if instructions:
        user_parts.append(f"Special instructions: {instructions}")
    user_parts.append(
        "\nReturn ONLY a JSON array of strings: [\"Title 1\", \"Title 2\", ...]"
    )
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Continue writing
# ---------------------------------------------------------------------------

def continue_writing_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for continuing existing text."""
    genre = context.get("genre", "")
    tone = context.get("tone", "")
    existing_text = context.get("existing_text", "")
    instructions = context.get("instructions", "")
    target_words = context.get("target_words", 500)

    system = _base_system_prompt(genre, tone)
    user_parts = [
        "Continue writing from where the text left off. "
        "Maintain the same style, voice, and narrative thread.",
        f"Target approximately {target_words} additional words.",
    ]
    if existing_text:
        user_parts.append(f"\n--- EXISTING TEXT ---\n{existing_text}\n--- END ---\n")
    if instructions:
        user_parts.append(f"Special instructions: {instructions}")
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Edit selection
# ---------------------------------------------------------------------------

def edit_selection_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for editing a selected passage."""
    genre = context.get("genre", "")
    tone = context.get("tone", "")
    selected_text = context.get("selected_text", "")
    instructions = context.get("instructions", "")
    edit_type = context.get("edit_type", "improve")

    system = _base_system_prompt(genre, tone)
    user_parts = [
        f"Edit the following passage. Edit type: {edit_type}.",
    ]
    if selected_text:
        user_parts.append(f"\n--- SELECTED TEXT ---\n{selected_text}\n--- END ---\n")
    if instructions:
        user_parts.append(f"Special instructions: {instructions}")
    user_parts.append("Return ONLY the revised text, nothing else.")
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Tone adjustment
# ---------------------------------------------------------------------------

def tone_adjustment_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Return (system, user) prompt pair for adjusting the tone of text."""
    genre = context.get("genre", "")
    target_tone = context.get("target_tone", "professional")
    selected_text = context.get("selected_text", "")
    instructions = context.get("instructions", "")

    system = _base_system_prompt(genre, target_tone)
    user_parts = [
        f"Rewrite the following text to match a {target_tone} tone.",
    ]
    if selected_text:
        user_parts.append(f"\n--- TEXT ---\n{selected_text}\n--- END ---\n")
    if instructions:
        user_parts.append(f"Special instructions: {instructions}")
    user_parts.append("Return ONLY the revised text, nothing else.")
    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROMPT_REGISTRY: dict[str, Callable[..., tuple[str, str]]] = {
    "outline": outline_prompt,
    "chapter": chapter_prompt,
    "blurb": blurb_prompt,
    "title_suggestions": title_suggestions_prompt,
    "continue_writing": continue_writing_prompt,
    "edit_selection": edit_selection_prompt,
    "tone_adjustment": tone_adjustment_prompt,
}


def get_prompt(generation_type: str, context: dict[str, Any]) -> tuple[str, str]:
    """Look up the prompt builder and return (system, user) messages."""
    builder = PROMPT_REGISTRY.get(generation_type)
    if builder is None:
        raise ValueError(f"Unknown generation type: {generation_type}")
    return builder(context)
