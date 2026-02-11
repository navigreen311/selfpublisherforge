"""Readability scoring algorithms.

Implements Flesch-Kincaid Grade Level, Flesch Reading Ease,
Gunning Fog Index, SMOG Index, and reading-level classification.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# Common 3+ syllable words that should NOT count for Gunning Fog "complex" words
_EASY_WORD_SUFFIXES = {"ing", "ed", "es", "er", "est", "ly"}

# Vowel pattern for syllable estimation
_VOWEL_GROUP = re.compile(r"[aeiouy]+", re.IGNORECASE)
_SENTENCE_BOUNDARY = re.compile(r"[.!?]+")


@dataclass(frozen=True)
class ReadabilityMetrics:
    """Container for all readability metric results."""

    flesch_kincaid_grade: float
    flesch_reading_ease: float
    gunning_fog: float
    smog_index: float
    word_count: int
    sentence_count: int
    syllable_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float
    reading_level: str


def count_syllables(word: str) -> int:
    """Estimate the number of syllables in a single word.

    Uses vowel-group heuristic with adjustments for silent-e and
    common English patterns.
    """
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1

    # Handle consonant + "le" endings (e.g., "table", "simple") -- these
    # form their own syllable, so we should NOT strip the trailing 'e'.
    has_cle_ending = (
        len(word) >= 3
        and word.endswith("le")
        and word[-3] not in "aeiouy"
    )

    # Remove trailing silent e (but not consonant+le patterns)
    if word.endswith("e") and not has_cle_ending:
        word = word[:-1]

    matches = _VOWEL_GROUP.findall(word)
    count = len(matches)
    return max(count, 1)


def _tokenize_words(text: str) -> list[str]:
    """Extract word tokens from text."""
    return [w for w in re.findall(r"[a-zA-Z']+", text) if len(w) > 0]


def _count_sentences(text: str) -> int:
    """Count sentences in text using punctuation boundaries."""
    sentences = _SENTENCE_BOUNDARY.split(text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    return max(len(sentences), 1)


def _is_complex_word(word: str) -> bool:
    """Determine if a word is 'complex' for Gunning Fog calculation.

    A complex word has 3+ syllables and is not a proper noun,
    jargon, or compound word made of simple words.
    """
    syllables = count_syllables(word)
    if syllables < 3:
        return False
    # Exclude words that are only complex due to common suffixes
    lower = word.lower()
    for suffix in _EASY_WORD_SUFFIXES:
        if lower.endswith(suffix):
            base = lower[: -len(suffix)]
            if count_syllables(base) < 3:
                return False
    return True


def _count_polysyllabic_words(words: list[str]) -> int:
    """Count words with 3 or more syllables (for SMOG)."""
    return sum(1 for w in words if count_syllables(w) >= 3)


def flesch_kincaid_grade(
    word_count: int,
    sentence_count: int,
    syllable_count: int,
) -> float:
    """Calculate the Flesch-Kincaid Grade Level.

    Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    """
    if word_count == 0 or sentence_count == 0:
        return 0.0
    asl = word_count / sentence_count
    asw = syllable_count / word_count
    grade = 0.39 * asl + 11.8 * asw - 15.59
    return round(max(grade, 0.0), 2)


def flesch_reading_ease(
    word_count: int,
    sentence_count: int,
    syllable_count: int,
) -> float:
    """Calculate the Flesch Reading Ease score.

    Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    Higher scores indicate easier readability (0-100 typical range).
    """
    if word_count == 0 or sentence_count == 0:
        return 0.0
    asl = word_count / sentence_count
    asw = syllable_count / word_count
    score = 206.835 - 1.015 * asl - 84.6 * asw
    return round(score, 2)


def gunning_fog(words: list[str], sentence_count: int) -> float:
    """Calculate the Gunning Fog Index.

    Formula: 0.4 * ((words/sentences) + 100 * (complex_words/words))
    """
    word_count = len(words)
    if word_count == 0 or sentence_count == 0:
        return 0.0
    complex_count = sum(1 for w in words if _is_complex_word(w))
    fog = 0.4 * ((word_count / sentence_count) + 100 * (complex_count / word_count))
    return round(fog, 2)


def smog_index(polysyllabic_count: int, sentence_count: int) -> float:
    """Calculate the SMOG (Simple Measure of Gobbledygook) Index.

    Formula: 1.0430 * sqrt(polysyllabic_count * (30 / sentences)) + 3.1291
    Requires at least 30 sentences for statistical validity but we
    provide an estimate for shorter texts.
    """
    if sentence_count == 0:
        return 0.0
    smog = 1.0430 * math.sqrt(polysyllabic_count * (30 / sentence_count)) + 3.1291
    return round(smog, 2)


def _classify_reading_level(grade: float) -> str:
    """Map a grade level score to a human-readable reading level."""
    if grade < 1:
        return "Kindergarten"
    if grade < 6:
        return "Elementary"
    if grade < 9:
        return "Middle School"
    if grade < 13:
        return "High School"
    if grade < 17:
        return "College"
    return "Graduate"


def analyze_readability(text: str) -> ReadabilityMetrics:
    """Perform full readability analysis on the given text.

    Returns a ReadabilityMetrics dataclass with all scores and
    derived statistics.
    """
    words = _tokenize_words(text)
    word_count = len(words)
    sentence_count = _count_sentences(text)
    syllable_count = sum(count_syllables(w) for w in words)
    polysyllabic = _count_polysyllabic_words(words)

    fk_grade = flesch_kincaid_grade(word_count, sentence_count, syllable_count)
    fre = flesch_reading_ease(word_count, sentence_count, syllable_count)
    fog = gunning_fog(words, sentence_count)
    smog = smog_index(polysyllabic, sentence_count)

    avg_wps = round(word_count / sentence_count, 2) if sentence_count else 0.0
    avg_spw = round(syllable_count / word_count, 2) if word_count else 0.0

    return ReadabilityMetrics(
        flesch_kincaid_grade=fk_grade,
        flesch_reading_ease=fre,
        gunning_fog=fog,
        smog_index=smog,
        word_count=word_count,
        sentence_count=sentence_count,
        syllable_count=syllable_count,
        avg_words_per_sentence=avg_wps,
        avg_syllables_per_word=avg_spw,
        reading_level=_classify_reading_level(fk_grade),
    )
