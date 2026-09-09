"""
Word Scramble puzzle generator.

Algorithm: Shuffle + Verify
  1. Sanitize word list.
  2. For each word: randomly shuffle letters.
  3. Verify the shuffled version differs from the original.
  4. Verify the shuffled version is not another valid common word.
  5. Optional hint: first letter or word length.
"""

from __future__ import annotations

import random
from typing import Any

from .utils import (
    COMMON_WORDS,
    generate_content_hash,
    svg_footer,
    svg_header,
    svg_rect,
    svg_text,
)

# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def _sanitize_word(word: str) -> str:
    """Strip and upper-case a word, keeping only alpha characters."""
    return "".join(ch for ch in word.strip().upper() if ch.isalpha())


def _shuffle_word(word: str, max_attempts: int = 100) -> str:
    """
    Shuffle the letters of *word* such that:
      - The result differs from the original.
      - The result is NOT a common English word.

    Returns the shuffled string (upper-case).
    """
    letters = list(word.upper())
    for _ in range(max_attempts):
        shuffled = letters[:]
        random.shuffle(shuffled)
        candidate = "".join(shuffled)
        if candidate == word.upper():
            continue
        if candidate.lower() in COMMON_WORDS:
            continue
        return candidate
    # Fallback: reverse (guaranteed different for len > 1)
    reversed_word = word.upper()[::-1]
    if reversed_word == word.upper():
        # Palindrome edge-case: swap first two characters
        lst = list(word.upper())
        lst[0], lst[1] = lst[1], lst[0]
        return "".join(lst)
    return reversed_word


def _calculate_letter_pattern_complexity(word: str) -> float:
    """
    Estimate how hard it is to unscramble a word based on letter-pattern features.

    Factors:
      - Number of unique letters (more unique = harder).
      - Ratio of vowels to consonants.
      - Repeated-letter count (repeated letters make it easier).
    Returns a value between 0 and 1.
    """
    upper = word.upper()
    length = len(upper)
    if length == 0:
        return 0.0

    unique = len(set(upper))
    vowels = sum(1 for ch in upper if ch in "AEIOU")
    consonants = length - vowels

    # Uniqueness ratio (all unique → harder)
    uniqueness = unique / length

    # Balance ratio: perfectly balanced vowels/consonants → harder to decode
    if length > 0:
        balance = 1.0 - abs(vowels - consonants) / length
    else:
        balance = 0.0

    # Repetition penalty: many repeats → easier
    repeat_penalty = 1.0 - (length - unique) / max(length, 1)

    return round((uniqueness * 0.4 + balance * 0.3 + repeat_penalty * 0.3), 4)


def calculate_difficulty(avg_word_length: float, letter_pattern_complexity: float) -> float:
    """
    Calculate a difficulty score from 0 to 100.

    Parameters
    ----------
    avg_word_length : float
        Average number of letters across all scrambled words.
    letter_pattern_complexity : float
        Average complexity score (0-1) from ``_calculate_letter_pattern_complexity``.
    """
    # Longer words are harder (cap contribution at ~15 letters)
    length_score = min(avg_word_length / 15.0, 1.0) * 100.0
    pattern_score = letter_pattern_complexity * 100.0
    return round(length_score * 0.5 + pattern_score * 0.5, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_word_scramble(words: list[str], hint_mode: str = "first_letter") -> dict[str, Any]:
    """
    Generate a word scramble puzzle.

    Parameters
    ----------
    words : list[str]
        List of words to scramble.
    hint_mode : str
        ``"first_letter"``, ``"word_length"``, ``"both"``, or ``"none"``.

    Returns
    -------
    dict with keys:
        scrambles    – list of {original, scrambled, hint}
        content_hash – SHA-256 hex string
        difficulty_score – float 0-100
        svg          – rendered SVG string
    """
    if not words:
        raise ValueError("Word list must not be empty.")

    scrambles: list[dict[str, str]] = []
    complexities: list[float] = []

    for raw_word in words:
        clean = _sanitize_word(raw_word)
        if len(clean) < 2:
            continue  # Cannot meaningfully scramble single-letter words

        scrambled = _shuffle_word(clean)
        complexity = _calculate_letter_pattern_complexity(clean)
        complexities.append(complexity)

        # Build hint
        hint = ""
        if hint_mode in ("first_letter", "both"):
            hint += f"Starts with '{clean[0]}'"
        if hint_mode in ("word_length", "both"):
            sep = ". " if hint else ""
            hint += f"{sep}{len(clean)} letters"
        if hint_mode == "none":
            hint = ""

        scrambles.append(
            {
                "original": clean,
                "scrambled": scrambled,
                "hint": hint,
            }
        )

    if not scrambles:
        raise ValueError("No valid words to scramble (all too short).")

    avg_len = sum(len(s["original"]) for s in scrambles) / len(scrambles)
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0
    difficulty_score = calculate_difficulty(avg_len, avg_complexity)

    content_hash = generate_content_hash({"scrambles": scrambles})
    svg = render_word_scramble_svg(scrambles)

    return {
        "scrambles": scrambles,
        "content_hash": content_hash,
        "difficulty_score": difficulty_score,
        "svg": svg,
    }


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


def render_word_scramble_svg(scrambles: list[dict[str, str]], line_height: int = 60, padding: int = 30) -> str:
    """Render scrambled words with blank answer lines to SVG."""
    width = 500
    height = padding * 2 + len(scrambles) * line_height + 20
    parts: list[str] = [svg_header(width, height)]
    parts.append(svg_rect(0, 0, width, height, fill="white", stroke="none"))

    # Title
    parts.append(
        svg_text(width // 2, padding, "Word Scramble", font_size=22, font_weight="bold", font_family="sans-serif")
    )

    y = padding + 40
    for idx, entry in enumerate(scrambles, 1):
        scrambled = entry["scrambled"]
        hint = entry.get("hint", "")

        # Number + scrambled word
        label = f"{idx}. {scrambled}"
        parts.append(
            svg_text(padding, y, label, font_size=18, anchor="start", font_family="monospace", font_weight="bold")
        )

        # Answer blank line
        blank_x = padding + 30
        blank_y = y + 22
        line_len = len(entry["original"]) * 18
        parts.append(
            f'  <line x1="{blank_x}" y1="{blank_y}" '
            f'x2="{blank_x + line_len}" y2="{blank_y}" '
            f'stroke="gray" stroke-width="1" stroke-dasharray="4,2"/>\n'
        )

        # Hint (small text)
        if hint:
            parts.append(
                svg_text(
                    blank_x + line_len + 10,
                    blank_y - 4,
                    f"({hint})",
                    font_size=11,
                    anchor="start",
                    font_family="sans-serif",
                    fill="gray",
                )
            )

        y += line_height

    parts.append(svg_footer())
    return "".join(parts)
