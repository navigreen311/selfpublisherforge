"""Prompt templates for AI content generation.

Each template is a callable that accepts a context dict and returns a
fully-formed system/user prompt pair suitable for the LLM.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


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


# ===========================================================================
# Action-based prompts (6-action Writing Studio)
# ===========================================================================
# Each action prompt builder accepts a context dict populated from
# ActionGenerateRequest fields and returns a (system, user) message pair.
#
# Supported placeholders in context:
#   {style_profile}  - voice characteristics (e.g., "lyrical, sparse")
#   {tone}           - tone modifier (e.g., "suspenseful")
#   {length}         - target length: "short", "medium", "long"
#   {context}        - surrounding text / chapter outline
#   {instruction}    - user instruction text
#   {selected_text}  - user-selected passage
#   {context_before} - text before cursor (~500 words)
#   {genre}          - genre of the work
#   {chapter_outline} - current chapter outline/synopsis
#   {previous_content} - previous chapter content
# ---------------------------------------------------------------------------

_LENGTH_GUIDANCE = {
    "short": "approximately 100 words",
    "medium": "approximately 300 words",
    "long": "approximately 800 words",
}


def _action_system_base(
    *,
    style_profile: str = "",
    tone: str = "",
    genre: str = "",
) -> str:
    """Build the base system prompt for action-based generation.

    Incorporates style profile voice characteristics, tone, and genre
    to give the LLM a consistent authorial persona.
    """
    parts = [
        "You are a professional author and writing assistant. "
        "You produce high-quality, publication-ready prose. "
        "Output ONLY the requested content with no preamble, commentary, "
        "or meta-text. Do not wrap your response in quotes or markdown "
        "code blocks unless explicitly asked.",
    ]
    if genre:
        parts.append(f"Genre: {genre}.")
    if tone:
        parts.append(f"Write in a {tone} tone.")
    if style_profile:
        parts.append(f"Voice and style: {style_profile}.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Action: write — Generate new content
# ---------------------------------------------------------------------------

def action_write_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Build prompts for the 'write' action: generate new content.

    System prompt includes chapter outline context, previous content,
    and style profile voice. User instruction tells what to write.
    """
    style_profile = context.get("style_profile", "")
    tone = context.get("tone", "")
    genre = context.get("genre", "")
    length = context.get("length", "medium")
    instruction = context.get("instruction", "")
    chapter_outline = context.get("chapter_outline", "")
    previous_content = context.get("previous_content", "")
    context_before = context.get("context_before", "")

    system_parts = [_action_system_base(style_profile=style_profile, tone=tone, genre=genre)]
    if chapter_outline:
        system_parts.append(
            f"\n\nCHAPTER OUTLINE:\n{chapter_outline}"
        )
    if previous_content:
        # Truncate to last 1000 chars to stay within context limits
        prev_snippet = previous_content[-2000:] if len(previous_content) > 2000 else previous_content
        system_parts.append(
            f"\n\nPREVIOUS CONTENT (for continuity):\n{prev_snippet}"
        )
    system = "\n".join(system_parts)

    length_hint = _LENGTH_GUIDANCE.get(length, _LENGTH_GUIDANCE["medium"])
    user_parts = []
    if context_before:
        ctx_snippet = context_before[-1500:] if len(context_before) > 1500 else context_before
        user_parts.append(f"Current text so far:\n---\n{ctx_snippet}\n---\n")
    user_parts.append(f"Write new content ({length_hint}).")
    if instruction:
        user_parts.append(f"Instructions: {instruction}")

    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Action: rewrite — Improve selected text
# ---------------------------------------------------------------------------

def action_rewrite_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Build prompts for the 'rewrite' action: improve selected text.

    Rewrites the selection while maintaining its original meaning,
    improving clarity, flow, and prose quality.
    """
    style_profile = context.get("style_profile", "")
    tone = context.get("tone", "")
    genre = context.get("genre", "")
    selected_text = context.get("selected_text", "")
    instruction = context.get("instruction", "")

    system = _action_system_base(style_profile=style_profile, tone=tone, genre=genre)
    system += (
        " Rewrite the provided text to improve clarity, readability, and "
        "prose quality while maintaining the original meaning and intent. "
        "Preserve the narrative voice and any character-specific dialogue. "
        "Return ONLY the rewritten text."
    )

    user_parts = []
    if selected_text:
        user_parts.append(f"Rewrite the following text:\n\n---\n{selected_text}\n---")
    if instruction:
        user_parts.append(f"\nAdditional instructions: {instruction}")

    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Action: expand — Add detail to selection
# ---------------------------------------------------------------------------

def action_expand_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Build prompts for the 'expand' action: add detail and elaboration.

    Expands the selection with more detail, examples, sensory descriptions,
    and deeper exploration of the ideas.
    """
    style_profile = context.get("style_profile", "")
    tone = context.get("tone", "")
    genre = context.get("genre", "")
    length = context.get("length", "medium")
    selected_text = context.get("selected_text", "")
    context_before = context.get("context_before", "")
    instruction = context.get("instruction", "")

    system = _action_system_base(style_profile=style_profile, tone=tone, genre=genre)
    system += (
        " Expand the provided text with more detail, vivid descriptions, "
        "examples, and deeper elaboration. Add sensory details, character "
        "thoughts, and richer scene-setting where appropriate. "
        "The expanded version should feel natural and seamless, not padded. "
        "Return ONLY the expanded text."
    )

    length_hint = _LENGTH_GUIDANCE.get(length, _LENGTH_GUIDANCE["medium"])
    user_parts = []
    if context_before:
        ctx_snippet = context_before[-800:] if len(context_before) > 800 else context_before
        user_parts.append(f"Surrounding context:\n---\n{ctx_snippet}\n---\n")
    if selected_text:
        user_parts.append(
            f"Expand the following text (target {length_hint} for the expanded version):\n\n"
            f"---\n{selected_text}\n---"
        )
    if instruction:
        user_parts.append(f"\nAdditional instructions: {instruction}")

    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Action: shorten — Condense selection
# ---------------------------------------------------------------------------

def action_shorten_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Build prompts for the 'shorten' action: condense text.

    Condenses the selection to be more concise while preserving all
    key information, plot points, and emotional beats.
    """
    style_profile = context.get("style_profile", "")
    tone = context.get("tone", "")
    genre = context.get("genre", "")
    selected_text = context.get("selected_text", "")
    instruction = context.get("instruction", "")

    system = _action_system_base(style_profile=style_profile, tone=tone, genre=genre)
    system += (
        " Condense the provided text to be more concise while preserving "
        "all key information, important plot points, character development, "
        "and emotional beats. Remove redundancy, tighten sentences, and "
        "eliminate filler words. The result should be noticeably shorter "
        "but lose none of the essential content. "
        "Return ONLY the shortened text."
    )

    user_parts = []
    if selected_text:
        user_parts.append(
            f"Shorten the following text while preserving its key content:\n\n"
            f"---\n{selected_text}\n---"
        )
    if instruction:
        user_parts.append(f"\nAdditional instructions: {instruction}")

    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Action: continue — Generate from cursor position
# ---------------------------------------------------------------------------

def action_continue_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Build prompts for the 'continue' action: write from cursor position.

    Uses context_before (last ~500 words before cursor) to seamlessly
    continue the narrative. No explicit user instruction needed.
    """
    style_profile = context.get("style_profile", "")
    tone = context.get("tone", "")
    genre = context.get("genre", "")
    length = context.get("length", "medium")
    context_before = context.get("context_before", "")
    context_after = context.get("context_after", "")
    chapter_outline = context.get("chapter_outline", "")
    instruction = context.get("instruction", "")

    system = _action_system_base(style_profile=style_profile, tone=tone, genre=genre)
    system += (
        " Continue writing naturally from where the text left off. "
        "Maintain the same narrative voice, pacing, tense, point of view, "
        "and stylistic choices. The continuation should read as if written "
        "by the same author in the same sitting — seamless and natural."
    )
    if chapter_outline:
        system += f"\n\nCHAPTER OUTLINE (for direction):\n{chapter_outline}"

    length_hint = _LENGTH_GUIDANCE.get(length, _LENGTH_GUIDANCE["medium"])
    user_parts = []
    if context_before:
        user_parts.append(f"Text so far:\n---\n{context_before}\n---\n")
    user_parts.append(f"Continue writing from where the text ends ({length_hint}).")
    if context_after:
        ctx_after_snippet = context_after[:500] if len(context_after) > 500 else context_after
        user_parts.append(
            f"\nNote: the text that follows the cursor is:\n---\n{ctx_after_snippet}\n---\n"
            "Ensure your continuation transitions smoothly into this subsequent text."
        )
    if instruction:
        user_parts.append(f"\nAdditional instructions: {instruction}")

    return system, "\n".join(user_parts)


# ---------------------------------------------------------------------------
# Action: ideas — Brainstorm bullet points
# ---------------------------------------------------------------------------

def action_ideas_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Build prompts for the 'ideas' action: brainstorm directions.

    Returns a structured list of 5 different directions for the next
    section, NOT prose. Each idea includes a brief title and description.
    """
    style_profile = context.get("style_profile", "")
    tone = context.get("tone", "")
    genre = context.get("genre", "")
    context_before = context.get("context_before", "")
    chapter_outline = context.get("chapter_outline", "")
    instruction = context.get("instruction", "")

    system = _action_system_base(style_profile=style_profile, tone=tone, genre=genre)
    system += (
        " You are brainstorming creative directions for the next section "
        "of this manuscript. Suggest exactly 5 different, distinct directions "
        "the writing could take. Each suggestion should be a concise bullet "
        "point with a bold title and 1-2 sentence description.\n\n"
        "Format your response EXACTLY as a numbered list:\n"
        "1. **Title** - Description of this direction\n"
        "2. **Title** - Description of this direction\n"
        "... and so on for all 5 ideas.\n\n"
        "Do NOT write prose. Do NOT include any preamble or closing remarks. "
        "Output ONLY the 5 numbered items."
    )
    if chapter_outline:
        system += f"\n\nCHAPTER OUTLINE:\n{chapter_outline}"

    user_parts = []
    if context_before:
        ctx_snippet = context_before[-1500:] if len(context_before) > 1500 else context_before
        user_parts.append(f"Current text:\n---\n{ctx_snippet}\n---\n")
    user_parts.append("Suggest 5 different directions for the next section.")
    if instruction:
        user_parts.append(f"Focus area: {instruction}")

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

# Action-based prompt registry for the 6 Writing Studio actions
ACTION_PROMPT_REGISTRY: dict[str, Callable[..., tuple[str, str]]] = {
    "write": action_write_prompt,
    "rewrite": action_rewrite_prompt,
    "expand": action_expand_prompt,
    "shorten": action_shorten_prompt,
    "continue": action_continue_prompt,
    "ideas": action_ideas_prompt,
}


def get_prompt(generation_type: str, context: dict[str, Any]) -> tuple[str, str]:
    """Look up the prompt builder and return (system, user) messages."""
    builder = PROMPT_REGISTRY.get(generation_type)
    if builder is None:
        raise ValueError(f"Unknown generation type: {generation_type}")
    return builder(context)


def get_action_prompt(action: str, context: dict[str, Any]) -> tuple[str, str]:
    """Look up an action prompt builder and return (system, user) messages.

    Actions: write, rewrite, expand, shorten, continue, ideas
    """
    builder = ACTION_PROMPT_REGISTRY.get(action)
    if builder is None:
        raise ValueError(
            f"Unknown writing action: {action}. "
            f"Valid actions: {', '.join(ACTION_PROMPT_REGISTRY.keys())}"
        )
    return builder(context)
