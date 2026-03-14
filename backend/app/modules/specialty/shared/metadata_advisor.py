"""KDP Category & Metadata Advisor for Specialty Books.

Provides LLM-powered BISAC category recommendations, KDP keyword
generation, subtitle optimisation, and metadata compliance checking.

All LLM-dependent functions return structured prompts ready to be
sent to the LLM orchestration service (they do not call the LLM
directly, keeping this module free of async/IO dependencies).

Usage::

    prompt = recommend_categories("My Animal Coloring Book", ...)
    result = check_metadata_compliance(title, subtitle, description, keywords)
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# BISAC Category Reference
# ---------------------------------------------------------------------------

KDP_CATEGORIES: dict[str, list[dict[str, str]]] = {
    "childrens": [
        {"code": "JUV001000", "path": "Juvenile Fiction > Animals > General"},
        {"code": "JUV002000", "path": "Juvenile Fiction > Bedtime & Dreams"},
        {"code": "JUV013000", "path": "Juvenile Fiction > Family > General"},
        {"code": "JUV017000", "path": "Juvenile Fiction > Humorous Stories"},
        {"code": "JUV019000", "path": "Juvenile Fiction > Imagination & Play"},
        {"code": "JUV029000", "path": "Juvenile Fiction > Rhyming"},
        {"code": "JUV039000", "path": "Juvenile Fiction > Social Themes > General"},
        {"code": "JUV039060", "path": "Juvenile Fiction > Social Themes > Self-Esteem & Self-Reliance"},
        {"code": "JNF013000", "path": "Juvenile Nonfiction > Concepts > General"},
        {"code": "JNF003000", "path": "Juvenile Nonfiction > Animals > General"},
        {"code": "JUV012000", "path": "Juvenile Fiction > Fairy Tales & Folklore"},
        {"code": "JUV048000", "path": "Juvenile Fiction > Readers > Beginner"},
        {"code": "JUV000000", "path": "Juvenile Fiction > General"},
    ],
    "coloring": [
        {"code": "GAM019000", "path": "Games & Activities > Coloring Books"},
        {"code": "JUV054000", "path": "Juvenile Nonfiction > Activity Books > Coloring"},
        {"code": "ART028000", "path": "Art > Color Theory"},
        {"code": "GAM000000", "path": "Games & Activities > General"},
        {"code": "SEL000000", "path": "Self-Help > General"},
        {"code": "OCC010000", "path": "Body, Mind & Spirit > Mindfulness & Meditation"},
        {"code": "ART000000", "path": "Art > General"},
    ],
    "puzzle": [
        {"code": "GAM007000", "path": "Games & Activities > Puzzles"},
        {"code": "GAM007010", "path": "Games & Activities > Word & Word Search"},
        {"code": "GAM007020", "path": "Games & Activities > Crosswords > General"},
        {"code": "GAM007030", "path": "Games & Activities > Sudoku"},
        {"code": "GAM014000", "path": "Games & Activities > Mazes"},
        {"code": "GAM007040", "path": "Games & Activities > Puzzles > Logic"},
        {"code": "JUV054000", "path": "Juvenile Nonfiction > Activity Books > General"},
        {"code": "GAM000000", "path": "Games & Activities > General"},
        {"code": "GAM012000", "path": "Games & Activities > Brain Teasers"},
    ],
}

# Maximum lengths for KDP metadata fields
_MAX_TITLE_LEN = 200
_MAX_SUBTITLE_LEN = 200
_MAX_DESCRIPTION_LEN = 4000
_MAX_KEYWORD_LEN = 50
_KDP_MAX_KEYWORDS = 7

# Trademarked terms (subset for metadata)
_TRADEMARK_TERMS: list[str] = [
    "disney", "pixar", "marvel", "pokemon", "hello kitty",
    "sesame street", "paw patrol", "barbie", "lego", "harry potter",
    "peppa pig", "cocomelon", "bluey",
]

# KDP restricted phrases in titles/subtitles
_KDP_RESTRICTED_PHRASES: list[str] = [
    "best seller", "bestseller", "#1", "number one",
    "award winning", "award-winning", "as seen on",
    "free", "bonus", "limited edition",
]


# ---------------------------------------------------------------------------
# LLM Prompt Builders
# ---------------------------------------------------------------------------

def recommend_categories(
    title: str,
    description: str | None = None,
    book_type: str = "childrens",
    audience: str | None = None,
) -> dict[str, Any]:
    """Build an LLM prompt to recommend BISAC categories.

    Returns
    -------
    dict with ``system_prompt``, ``user_prompt``, ``reference_categories``
    (the relevant subset of ``KDP_CATEGORIES``).
    """
    ref_cats = KDP_CATEGORIES.get(book_type, KDP_CATEGORIES["childrens"])

    categories_text = "\n".join(
        f"  - {cat['code']}: {cat['path']}" for cat in ref_cats
    )

    system_prompt = (
        "You are a KDP metadata expert. Given a book title, description, "
        "type, and audience, recommend the 3-5 most relevant BISAC categories. "
        "Rank by relevance. For each, provide the BISAC code, full path, a "
        "relevance score (0.0-1.0), and a one-sentence rationale. "
        "Return valid JSON only."
    )

    user_prompt = (
        f"Book Title: {title}\n"
        f"Book Type: {book_type}\n"
        f"Description: {description or 'N/A'}\n"
        f"Audience: {audience or 'General'}\n\n"
        f"Available BISAC categories:\n{categories_text}\n\n"
        "Recommend the best 3-5 categories as a JSON array of objects with "
        "keys: code, path, relevance_score, rationale."
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "reference_categories": ref_cats,
    }


def generate_keywords(
    title: str,
    description: str | None = None,
    themes: list[str] | None = None,
    book_type: str = "childrens",
) -> dict[str, Any]:
    """Build an LLM prompt to generate 7 KDP backend keywords.

    Returns
    -------
    dict with ``system_prompt``, ``user_prompt``.
    """
    themes_str = ", ".join(themes) if themes else "N/A"

    system_prompt = (
        "You are a KDP keyword optimisation expert. Generate exactly 7 "
        "high-value backend keywords for a KDP listing. Keywords should "
        "be 1-3 words each, under 50 characters, and help the book rank "
        "in Amazon search. Do NOT repeat words from the title. "
        "Do NOT use trademarked terms. Return a JSON array of 7 strings."
    )

    user_prompt = (
        f"Book Title: {title}\n"
        f"Book Type: {book_type}\n"
        f"Description: {description or 'N/A'}\n"
        f"Themes: {themes_str}\n\n"
        "Generate 7 KDP keywords as a JSON array of strings."
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def optimize_subtitle(
    title: str,
    book_type: str = "childrens",
    audience: str | None = None,
) -> dict[str, Any]:
    """Build an LLM prompt to suggest optimised subtitles.

    Returns
    -------
    dict with ``system_prompt``, ``user_prompt``.
    """
    system_prompt = (
        "You are a KDP listing optimisation expert. Generate 3-5 subtitle "
        "suggestions that include relevant keywords for Amazon search while "
        "remaining natural and appealing to shoppers. Each subtitle should be "
        "under 200 characters. Do NOT use trademarked terms or restricted "
        "phrases like 'best seller' or 'award winning'. "
        "Return a JSON array of strings."
    )

    user_prompt = (
        f"Book Title: {title}\n"
        f"Book Type: {book_type}\n"
        f"Audience: {audience or 'General'}\n\n"
        "Generate 3-5 subtitle suggestions as a JSON array of strings."
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


# ---------------------------------------------------------------------------
# Metadata Compliance Checking (deterministic, no LLM)
# ---------------------------------------------------------------------------

def check_metadata_compliance(
    title: str,
    subtitle: str | None = None,
    description: str | None = None,
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Check KDP metadata fields for compliance issues.

    Parameters
    ----------
    title:
        Book title.
    subtitle:
        Book subtitle (optional).
    description:
        Book description (optional).
    keywords:
        List of KDP backend keywords (max 7).

    Returns
    -------
    dict with ``issues`` (list of problem descriptions) and
    ``suggestions`` (list of improvement tips).
    """
    issues: list[str] = []
    suggestions: list[str] = []

    # --- Title checks ---
    if not title or not title.strip():
        issues.append("Title is empty or blank.")
    elif len(title) > _MAX_TITLE_LEN:
        issues.append(
            f"Title exceeds {_MAX_TITLE_LEN} characters "
            f"({len(title)} characters)."
        )

    # Trademark check in title
    title_lower = (title or "").lower()
    for term in _TRADEMARK_TERMS:
        if term in title_lower:
            issues.append(f"Title contains trademarked term: '{term}'.")

    # Restricted phrases
    for phrase in _KDP_RESTRICTED_PHRASES:
        if phrase in title_lower:
            issues.append(
                f"Title contains KDP-restricted phrase: '{phrase}'."
            )

    # ALL-CAPS title
    if title and title == title.upper() and len(title) > 3:
        suggestions.append(
            "Avoid ALL-CAPS titles — use title case for better readability."
        )

    # --- Subtitle checks ---
    if subtitle:
        if len(subtitle) > _MAX_SUBTITLE_LEN:
            issues.append(
                f"Subtitle exceeds {_MAX_SUBTITLE_LEN} characters "
                f"({len(subtitle)} characters)."
            )
        sub_lower = subtitle.lower()
        for term in _TRADEMARK_TERMS:
            if term in sub_lower:
                issues.append(
                    f"Subtitle contains trademarked term: '{term}'."
                )
        for phrase in _KDP_RESTRICTED_PHRASES:
            if phrase in sub_lower:
                issues.append(
                    f"Subtitle contains KDP-restricted phrase: '{phrase}'."
                )

    # --- Description checks ---
    if description:
        if len(description) > _MAX_DESCRIPTION_LEN:
            issues.append(
                f"Description exceeds {_MAX_DESCRIPTION_LEN} characters "
                f"({len(description)} characters)."
            )
        if len(description) < 50:
            suggestions.append(
                "Description is very short. Aim for at least 150 characters "
                "for better discoverability."
            )
    else:
        suggestions.append(
            "No description provided. A compelling description improves "
            "conversion on Amazon."
        )

    # --- Keyword checks ---
    if keywords:
        if len(keywords) > _KDP_MAX_KEYWORDS:
            issues.append(
                f"Too many keywords ({len(keywords)}). KDP allows "
                f"a maximum of {_KDP_MAX_KEYWORDS}."
            )
        for kw in keywords:
            if len(kw) > _MAX_KEYWORD_LEN:
                issues.append(
                    f"Keyword '{kw}' exceeds {_MAX_KEYWORD_LEN} characters."
                )
            kw_lower = kw.lower()
            for term in _TRADEMARK_TERMS:
                if term in kw_lower:
                    issues.append(
                        f"Keyword '{kw}' contains trademarked term: '{term}'."
                    )
            # Check if keyword duplicates title words
            if title and kw.lower() in title.lower():
                suggestions.append(
                    f"Keyword '{kw}' duplicates words in the title. "
                    "Use unique keywords for broader reach."
                )
        # Fewer than 7 keywords
        if len(keywords) < _KDP_MAX_KEYWORDS:
            suggestions.append(
                f"Only {len(keywords)} keyword(s) provided. "
                f"Use all {_KDP_MAX_KEYWORDS} slots for maximum visibility."
            )
    else:
        suggestions.append(
            "No keywords provided. KDP allows up to 7 backend keywords — "
            "use them all for maximum discoverability."
        )

    return {
        "issues": issues,
        "suggestions": suggestions,
    }
