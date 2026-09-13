"""Bilingual Support service for Children's Book Studio.

Handles AI-powered translation with cultural adaptation, reading-level
validation in both languages, change-sync for modified pages, and
bilingual layout arrangement (side-by-side, alternating, back-section).
"""

from __future__ import annotations

from typing import Any

from app.modules.specialty.childrens.text_analysis import (
    AGE_BAND_RULES,
    _resolve_age_range,
    _word_count,
    calculate_readability_score,
)

# ---------------------------------------------------------------------------
# Supported Languages
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: list[str] = [
    "es",  # Spanish
    "fr",  # French
    "de",  # German
    "pt",  # Portuguese
    "it",  # Italian
    "zh",  # Chinese (Simplified)
    "ja",  # Japanese
    "ko",  # Korean
]

_LANGUAGE_NAMES: dict[str, str] = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_language(lang: str) -> None:
    """Raise ValueError if *lang* is not in SUPPORTED_LANGUAGES."""
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language '{lang}'. " f"Supported: {SUPPORTED_LANGUAGES}")


def _age_constraints_prompt(age_range: str) -> str:
    """Build an age-appropriate language constraint block for the LLM prompt."""
    key = _resolve_age_range(age_range)
    rules = AGE_BAND_RULES[key]

    constraints: list[str] = []
    if rules["max_sentence_words"] is not None:
        constraints.append(f"- Maximum {rules['max_sentence_words']} words per sentence")
    if rules["max_word_length"] is not None:
        constraints.append(f"- Maximum {rules['max_word_length']} letters per word")
    if rules["vocab_level"] is not None:
        constraints.append(f"- Use only top-{rules['vocab_level']} most common words in the target language")
    min_w, max_w = rules["total_words"]
    constraints.append(f"- Total book word count should stay between {min_w} and {max_w} words")
    return "\n".join(constraints)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def translate_book(
    pages: list[dict[str, Any]],
    target_language: str,
    age_range: str,
) -> dict[str, Any]:
    """Build LLM translation prompts and return translated page placeholders.

    Parameters
    ----------
    pages:
        List of page dicts, each with at minimum ``page_number`` (int) and
        ``text_content`` (str).
    target_language:
        ISO-639-1 language code (must be in SUPPORTED_LANGUAGES).
    age_range:
        Age-range key (e.g. ``"board"``, ``"picture_3_5"``).

    Returns
    -------
    dict with keys:
        - ``target_language``: str
        - ``language_name``: str
        - ``age_range``: str (resolved)
        - ``pages``: list[dict] – each page dict extended with
          ``translation_prompt`` (the LLM prompt) and
          ``translated_text`` (``None`` until the LLM responds).
        - ``system_prompt``: str – reusable system prompt for the LLM.
    """
    _validate_language(target_language)
    resolved_age = _resolve_age_range(age_range)
    lang_name = _LANGUAGE_NAMES.get(target_language, target_language)

    system_prompt = (
        f"You are a professional children's book translator specializing in "
        f"English to {lang_name} translation.\n\n"
        f"CRITICAL RULES:\n"
        f"1. Culturally adapt — do not transliterate. Replace idioms, cultural "
        f"references, and humor with equivalents natural in {lang_name}.\n"
        f"2. Maintain the emotional tone, rhythm, and pacing of the original.\n"
        f"3. If the original rhymes, attempt to preserve the rhyme scheme in "
        f"{lang_name} even if it means rephrasing.\n"
        f"4. Follow these age-appropriate language constraints:\n"
        f"{_age_constraints_prompt(age_range)}\n"
        f"5. Preserve page breaks exactly — each page must be translated "
        f"independently so illustrations stay aligned.\n\n"
        f"OUTPUT FORMAT: Respond with valid JSON only. No markdown, no code "
        f"fences, no extra commentary. Use this exact structure:\n"
        f'{{"translated_text": "<your translation here>", '
        f'"back_translation": "<literal English back-translation for QA>", '
        f'"notes": "<any cultural adaptation notes, or empty string>"}}\n\n'
        f"If the input text is empty or whitespace-only, return:\n"
        f'{{"translated_text": "", "back_translation": "", "notes": ""}}'
    )

    translated_pages: list[dict[str, Any]] = []
    for page in pages:
        text = page.get("text_content", "") or ""
        page_num = page.get("page_number", 0)

        if not text.strip():
            translated_pages.append(
                {
                    **page,
                    "translated_text": None,
                    "translation_prompt": None,
                }
            )
            continue

        user_prompt = (
            f"Translate the following children's book page (page {page_num}) "
            f"from English to {lang_name}.\n\n"
            f"Original text:\n{text}"
        )

        translated_pages.append(
            {
                **page,
                "translated_text": None,  # filled by LLM caller
                "translation_prompt": f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}",
            }
        )

    return {
        "target_language": target_language,
        "language_name": lang_name,
        "age_range": resolved_age,
        "pages": translated_pages,
        "system_prompt": system_prompt,
    }


# ---------------------------------------------------------------------------
# Translation Validation
# ---------------------------------------------------------------------------


# Expected word-count ratio bounds per target language relative to English.
# Values are (lower_bound, upper_bound) representing the typical range of
# translated_word_count / english_word_count.
_LANGUAGE_RATIO_BOUNDS: dict[str, tuple[float, float]] = {
    "es": (1.1, 1.35),  # Spanish: ~20% longer
    "fr": (1.15, 1.4),  # French: ~25% longer
    "de": (0.9, 1.2),  # German: roughly similar (compounds reduce word count)
    "pt": (1.1, 1.35),  # Portuguese: similar to Spanish
    "it": (1.1, 1.35),  # Italian: similar to Spanish
    "zh": (0.4, 0.8),  # Chinese: much fewer "words" (character-based)
    "ja": (0.4, 0.85),  # Japanese: fewer segmented words
    "ko": (0.6, 1.0),  # Korean: somewhat fewer words
}


def validate_translation(
    original: list[dict[str, Any]],
    translated: list[dict[str, Any]],
    age_range: str,
    target_language: str | None = None,
) -> dict[str, Any]:
    """Validate translated pages against the original.

    Parameters
    ----------
    original:
        Original page dicts with ``text_content``.
    translated:
        Translated page dicts with ``translated_text``.
    age_range:
        Age-range key.

    Returns
    -------
    dict with keys:
        - ``valid``: bool
        - ``original_readability``: float (0-100)
        - ``translated_readability``: float (0-100)
        - ``page_count_match``: bool
        - ``issues``: list[dict] – per-page issues
    """
    resolved_age = _resolve_age_range(age_range)
    issues: list[dict[str, Any]] = []

    page_count_match = len(original) == len(translated)
    if not page_count_match:
        issues.append(
            {
                "type": "page_count_mismatch",
                "message": (f"Original has {len(original)} pages but " f"translation has {len(translated)} pages."),
            }
        )

    # Collect full text for readability scoring
    original_full_text = "\n".join(p.get("text_content", "") or "" for p in original)
    translated_full_text = "\n".join(p.get("translated_text", "") or "" for p in translated)

    original_readability = calculate_readability_score(original_full_text, resolved_age)
    translated_readability = calculate_readability_score(translated_full_text, resolved_age)

    # Per-page validation
    pairs = min(len(original), len(translated))
    for i in range(pairs):
        orig_text = (original[i].get("text_content") or "").strip()
        trans_text = (translated[i].get("translated_text") or "").strip()
        page_num = original[i].get("page_number", i + 1)

        if orig_text and not trans_text:
            issues.append(
                {
                    "type": "missing_translation",
                    "page": page_num,
                    "message": f"Page {page_num} has original text but no translation.",
                }
            )
            continue

        if not orig_text:
            continue

        # Word-count ratio check using language-specific bounds
        orig_wc = _word_count(orig_text)
        trans_wc = _word_count(trans_text)
        if orig_wc > 0 and trans_wc > 0:
            ratio = trans_wc / orig_wc
            lo, hi = _LANGUAGE_RATIO_BOUNDS.get(target_language or "", (0.3, 2.0))
            # Apply tolerance: allow 30% beyond expected bounds for short pages
            tolerance = 0.3 if orig_wc < 20 else 0.15
            effective_lo = lo - tolerance
            effective_hi = hi + tolerance
            if ratio < effective_lo or ratio > effective_hi:
                expected_range = f"{lo:.2f}–{hi:.2f}"
                issues.append(
                    {
                        "type": "word_count_ratio",
                        "page": page_num,
                        "target_language": target_language,
                        "expected_ratio_range": expected_range,
                        "actual_ratio": round(ratio, 2),
                        "message": (
                            f"Page {page_num}: translation word count ({trans_wc}) "
                            f"vs original ({orig_wc}) gives ratio={ratio:.2f}, "
                            f"outside expected range {expected_range} "
                            f"for {_LANGUAGE_NAMES.get(target_language or '', 'unknown')}"
                        ),
                    }
                )

    return {
        "valid": len(issues) == 0,
        "original_readability": original_readability,
        "translated_readability": translated_readability,
        "page_count_match": page_count_match,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Sync Translations
# ---------------------------------------------------------------------------


def sync_translations(
    original_pages: list[dict[str, Any]],
    translated_pages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect changed originals and mark only those for re-translation.

    Compares ``text_content`` between original and the snapshot stored
    when the translation was created (``original_snapshot`` key on the
    translated page).  Pages whose original text changed are flagged
    for re-translation.

    Parameters
    ----------
    original_pages:
        Current original pages with ``page_number`` and ``text_content``.
    translated_pages:
        Previously translated pages with ``page_number``,
        ``translated_text``, and ``original_snapshot`` (the text_content
        at the time of translation).

    Returns
    -------
    dict with keys:
        - ``changed_pages``: list[int] – page numbers that need re-translation
        - ``unchanged_pages``: list[int]
        - ``pages``: list[dict] – updated translated page dicts with
          ``needs_retranslation`` bool flag added
        - ``total_changed``: int
    """
    # Build lookup by page_number
    orig_by_num: dict[int, str] = {
        p.get("page_number", 0): (p.get("text_content") or "").strip() for p in original_pages
    }

    changed: list[int] = []
    unchanged: list[int] = []
    updated_pages: list[dict[str, Any]] = []

    for tp in translated_pages:
        page_num = tp.get("page_number", 0)
        snapshot = (tp.get("original_snapshot") or "").strip()
        current_original = orig_by_num.get(page_num, "")

        needs_retranslation = snapshot != current_original and current_original != ""

        if needs_retranslation:
            changed.append(page_num)
        else:
            unchanged.append(page_num)

        updated_pages.append(
            {
                **tp,
                "needs_retranslation": needs_retranslation,
            }
        )

    return {
        "changed_pages": changed,
        "unchanged_pages": unchanged,
        "pages": updated_pages,
        "total_changed": len(changed),
    }


# ---------------------------------------------------------------------------
# Bilingual Layout
# ---------------------------------------------------------------------------


def get_bilingual_layout(
    pages: list[dict[str, Any]],
    translated_pages: list[dict[str, Any]],
    layout_mode: str,
) -> list[dict[str, Any]]:
    """Arrange original and translated pages according to *layout_mode*.

    Parameters
    ----------
    pages:
        Original pages with ``page_number`` and ``text_content``.
    translated_pages:
        Translated pages with ``page_number`` and ``translated_text``.
    layout_mode:
        One of ``"side_by_side"`` | ``"alternating"`` | ``"back_section"``.

    Returns
    -------
    list[dict] – combined pages arranged by mode.  Each dict includes:
        - ``page_number``: int (final layout page number)
        - ``original_text``: str | None
        - ``translated_text``: str | None
        - ``layout_type``: str (the mode)
        - ``source_page``: int (original page number)
    """
    valid_modes = {"side_by_side", "alternating", "back_section"}
    if layout_mode not in valid_modes:
        raise ValueError(f"Invalid layout_mode '{layout_mode}'. Must be one of {valid_modes}")

    # Build lookup
    trans_by_num: dict[int, str] = {p.get("page_number", 0): (p.get("translated_text") or "") for p in translated_pages}

    combined: list[dict[str, Any]] = []

    if layout_mode == "side_by_side":
        # Both languages on the same page
        for page in pages:
            pn = page.get("page_number", 0)
            combined.append(
                {
                    "page_number": pn,
                    "original_text": page.get("text_content") or "",
                    "translated_text": trans_by_num.get(pn, ""),
                    "layout_type": "side_by_side",
                    "source_page": pn,
                }
            )

    elif layout_mode == "alternating":
        # L1 page then L2 page, interleaved
        output_num = 1
        for page in pages:
            pn = page.get("page_number", 0)
            combined.append(
                {
                    "page_number": output_num,
                    "original_text": page.get("text_content") or "",
                    "translated_text": None,
                    "layout_type": "alternating_original",
                    "source_page": pn,
                }
            )
            output_num += 1
            combined.append(
                {
                    "page_number": output_num,
                    "original_text": None,
                    "translated_text": trans_by_num.get(pn, ""),
                    "layout_type": "alternating_translated",
                    "source_page": pn,
                }
            )
            output_num += 1

    elif layout_mode == "back_section":
        # Full story in L1, then full story in L2
        output_num = 1
        for page in pages:
            pn = page.get("page_number", 0)
            combined.append(
                {
                    "page_number": output_num,
                    "original_text": page.get("text_content") or "",
                    "translated_text": None,
                    "layout_type": "back_section_original",
                    "source_page": pn,
                }
            )
            output_num += 1

        for page in pages:
            pn = page.get("page_number", 0)
            combined.append(
                {
                    "page_number": output_num,
                    "original_text": None,
                    "translated_text": trans_by_num.get(pn, ""),
                    "layout_type": "back_section_translated",
                    "source_page": pn,
                }
            )
            output_num += 1

    return combined
