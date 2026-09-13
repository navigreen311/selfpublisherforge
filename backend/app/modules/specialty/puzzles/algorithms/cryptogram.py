"""
Cryptogram puzzle generator using substitution cipher.

Algorithm:
  1. Generate a random A-Z mapping where no letter maps to itself (a derangement).
  2. Apply the cipher to the input phrase.
  3. Provide the encoded text with blanks for answers.
  4. Generate a frequency hint (most common encoded letter likely maps to E).
  5. Optionally reveal 1-2 starter letters.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

from .utils import (
    generate_content_hash,
    svg_footer,
    svg_header,
    svg_rect,
    svg_text,
)

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ---------------------------------------------------------------------------
# Derangement generation (no letter maps to itself)
# ---------------------------------------------------------------------------


def _generate_derangement() -> dict[str, str]:
    """
    Generate a random derangement of A-Z (no fixed points).

    Uses the rejection method: shuffle until no letter maps to itself.
    This converges quickly (~63% acceptance rate per attempt).
    """
    letters = list(ALPHABET)
    while True:
        shuffled = letters[:]
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(letters, shuffled, strict=False)):
            return dict(zip(letters, shuffled, strict=False))


def _apply_cipher(text: str, cipher_map: dict[str, str]) -> str:
    """Apply the substitution cipher, preserving non-alpha characters."""
    result: list[str] = []
    for ch in text:
        if ch.upper() in cipher_map:
            mapped = cipher_map[ch.upper()]
            result.append(mapped if ch.isupper() else mapped.lower())
        else:
            result.append(ch)
    return "".join(result)


def _frequency_hints(encoded: str, cipher_map: dict[str, str]) -> list[str]:
    """
    Generate frequency-analysis hints.

    Returns a list of human-readable hint strings, e.g.:
      "The most frequent letter 'X' likely represents 'E'"
    """
    # Reverse map: encoded letter → original letter
    reverse_map = {v: k for k, v in cipher_map.items()}

    # Count only alpha characters in the encoded text
    counts = Counter(ch.upper() for ch in encoded if ch.isalpha())
    if not counts:
        return []

    hints: list[str] = []
    most_common = counts.most_common(1)[0]
    enc_letter = most_common[0]
    orig_letter = reverse_map.get(enc_letter, "?")
    hints.append(f"The most frequent letter '{enc_letter}' represents '{orig_letter}'")
    return hints


def _starter_hints(cipher_map: dict[str, str], unique_letters: set[str], count: int = 2) -> list[dict[str, str]]:
    """
    Reveal *count* letter mappings as starter hints.

    Chooses common letters (E, T, A, O, …) if present in the phrase.
    """
    priority = "ETAOINSHRDLCUMWFGYPBVKJXQZ"
    selected: list[dict[str, str]] = []
    for letter in priority:
        if letter in unique_letters and len(selected) < count:
            selected.append(
                {
                    "encoded": cipher_map[letter],
                    "decoded": letter,
                }
            )
    return selected


# ---------------------------------------------------------------------------
# Difficulty calculation
# ---------------------------------------------------------------------------


def calculate_difficulty(phrase_length: int, unique_letters: int, letter_frequency_distribution: float) -> float:
    """
    Calculate a difficulty score from 0 to 100.

    Parameters
    ----------
    phrase_length : int
        Total number of alpha characters in the original phrase.
    unique_letters : int
        Count of distinct letters used.
    letter_frequency_distribution : float
        Standard deviation of letter frequencies (lower = more uniform = harder).
    """
    # Longer phrases → slightly easier (more data for frequency analysis),
    # but we reward length up to a point for puzzle richness.
    length_score = min(phrase_length / 200.0, 1.0) * 30.0

    # More unique letters → harder (more unknowns)
    unique_score = (unique_letters / 26.0) * 40.0

    # Lower frequency std-dev → harder (uniform distribution defeats frequency analysis)
    # Typical std-dev ranges from ~0.01 (uniform) to ~0.08 (skewed English).
    freq_score = max(0.0, 1.0 - letter_frequency_distribution / 0.08) * 30.0

    return round(length_score + unique_score + freq_score, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_cryptogram(phrase: str, reveal_count: int = 2) -> dict[str, Any]:
    """
    Generate a cryptogram puzzle.

    Parameters
    ----------
    phrase : str
        The original quote or sentence to encode.
    reveal_count : int
        Number of starter letter mappings to reveal (0 to disable).

    Returns
    -------
    dict with keys:
        encoded      – the encoded string
        cipher_map   – dict mapping original → encoded letters
        original     – the original phrase (answer key)
        hints        – list of hint strings / dicts
        content_hash – SHA-256 hex string
        difficulty_score – float 0-100
        svg          – rendered SVG string
    """
    if not phrase or not any(ch.isalpha() for ch in phrase):
        raise ValueError("Phrase must contain at least one alphabetic character.")

    # Step 1: Generate derangement cipher
    cipher_map = _generate_derangement()

    # Step 2: Apply cipher
    encoded = _apply_cipher(phrase, cipher_map)

    # Step 3-4: Hints
    unique_letters_in_phrase = {ch.upper() for ch in phrase if ch.isalpha()}
    freq_hints = _frequency_hints(encoded, cipher_map)

    starter = []
    if reveal_count > 0:
        starter = _starter_hints(cipher_map, unique_letters_in_phrase, reveal_count)

    hints: list[Any] = freq_hints + starter

    # Difficulty calculation
    alpha_chars = [ch for ch in phrase if ch.isalpha()]
    phrase_length = len(alpha_chars)
    unique_count = len(unique_letters_in_phrase)
    freq_counter = Counter(ch.upper() for ch in alpha_chars)
    total = sum(freq_counter.values())
    freqs = [v / total for v in freq_counter.values()] if total else []
    mean_freq = sum(freqs) / len(freqs) if freqs else 0
    std_dev = (sum((f - mean_freq) ** 2 for f in freqs) / len(freqs)) ** 0.5 if freqs else 0

    difficulty_score = calculate_difficulty(phrase_length, unique_count, std_dev)

    content_hash = generate_content_hash(
        {
            "encoded": encoded,
            "original": phrase,
            "cipher_map": cipher_map,
        }
    )

    svg = render_cryptogram_svg(encoded, phrase, cipher_map, starter)

    return {
        "encoded": encoded,
        "cipher_map": cipher_map,
        "original": phrase,
        "hints": hints,
        "content_hash": content_hash,
        "difficulty_score": difficulty_score,
        "svg": svg,
    }


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


def render_cryptogram_svg(
    encoded: str, original: str, cipher_map: dict[str, str], starters: list[dict[str, str]], chars_per_line: int = 30
) -> str:
    """
    Render the cryptogram as SVG with encoded letters on top and
    small answer boxes below each letter.
    """
    # Reverse map for starter reveals
    revealed: dict[str, str] = {}
    for s in starters:
        revealed[s["encoded"].upper()] = s["decoded"].upper()

    # Break into lines
    words = encoded.split(" ")
    lines: list[str] = []
    current_line = ""
    for word in words:
        test = (current_line + " " + word).strip()
        if len(test) > chars_per_line and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    cell_w = 28
    cell_h = 50
    padding = 30
    line_spacing = cell_h + 20
    max_chars = max(len(line) for line in lines) if lines else 1
    width = padding * 2 + max_chars * cell_w
    height = padding * 2 + len(lines) * line_spacing + 40

    parts: list[str] = [svg_header(width, height)]
    parts.append(svg_rect(0, 0, width, height, fill="white", stroke="none"))

    # Title
    parts.append(
        svg_text(width // 2, padding, "Cryptogram", font_size=22, font_weight="bold", font_family="sans-serif")
    )

    y = padding + 40
    for line in lines:
        x = padding
        for ch in line:
            if ch.isalpha():
                # Encoded letter on top
                parts.append(
                    svg_text(x + cell_w // 2, y, ch.upper(), font_size=16, font_family="monospace", font_weight="bold")
                )
                # Answer box below
                box_y = y + 8
                parts.append(svg_rect(x + 2, box_y, cell_w - 4, 22, fill="white", stroke="black"))
                # If this is a revealed starter letter, show it
                upper_ch = ch.upper()
                if upper_ch in revealed:
                    parts.append(
                        svg_text(
                            x + cell_w // 2,
                            box_y + 11,
                            revealed[upper_ch],
                            font_size=14,
                            font_family="monospace",
                            fill="blue",
                        )
                    )
            else:
                # Non-alpha (space, punctuation) — just render the character
                parts.append(svg_text(x + cell_w // 2, y, ch, font_size=16, font_family="monospace"))
            x += cell_w
        y += line_spacing

    # Hint area
    parts.append(
        svg_text(
            padding,
            y + 10,
            "Hint: Each letter stands for a different letter.",
            font_size=12,
            anchor="start",
            font_family="sans-serif",
            fill="gray",
        )
    )

    parts.append(svg_footer())
    return "".join(parts)
