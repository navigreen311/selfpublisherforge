"""Rhythm Analyzer — Analyze sentence rhythm and cadence patterns."""

from __future__ import annotations

import re
import statistics
from typing import TypedDict


class RhythmMetrics(TypedDict):
    """Rhythm analysis results."""
    avg_syllables_per_sentence: float
    syllable_variance: float
    sentence_length_variety_score: float
    paragraph_rhythm_score: float
    opening_pattern_consistency: float
    short_sentence_ratio: float
    long_sentence_ratio: float


# Vowel sounds for syllable counting
_VOWELS = frozenset("aeiouy")


class RhythmAnalyzer:
    """Analyzes rhythm and cadence patterns in text."""

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Count syllables in a word using vowel-based heuristic."""
        word = word.lower().strip(".,!?;:'\"-")
        if not word:
            return 1

        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in _VOWELS
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith("e") and count > 1:
            count -= 1

        return max(1, count)

    @staticmethod
    def _count_sentence_syllables(sentence: str) -> int:
        """Count total syllables in a sentence."""
        words = re.findall(r"[a-zA-Z']+", sentence)
        return sum(RhythmAnalyzer._count_syllables(w) for w in words)

    @staticmethod
    def _get_opening_pattern(sentence: str) -> str:
        """Extract opening pattern (first 2-3 words structure)."""
        words = sentence.strip().split()[:3]
        # Simple pattern: just the count of words in the opening
        return str(len(words))

    def analyze(self, text: str) -> RhythmMetrics:
        """Analyze rhythm and cadence in the given text.

        Args:
            text: The text to analyze

        Returns:
            RhythmMetrics containing rhythm analysis
        """
        # Split into sentences
        sentences = [
            s.strip()
            for s in re.split(r'[.!?]+', text)
            if s.strip() and len(s.split()) >= 2
        ]

        if not sentences:
            return RhythmMetrics(
                avg_syllables_per_sentence=0.0,
                syllable_variance=0.0,
                sentence_length_variety_score=0.0,
                paragraph_rhythm_score=0.0,
                opening_pattern_consistency=0.0,
                short_sentence_ratio=0.0,
                long_sentence_ratio=0.0,
            )

        # Syllable analysis
        syllable_counts = [self._count_sentence_syllables(s) for s in sentences]
        avg_syllables = statistics.mean(syllable_counts)
        syllable_variance = statistics.variance(syllable_counts) if len(syllable_counts) > 1 else 0.0

        # Sentence length variety (coefficient of variation)
        word_counts = [len(s.split()) for s in sentences]
        avg_words = statistics.mean(word_counts)
        std_words = statistics.stdev(word_counts) if len(word_counts) > 1 else 0.0
        variety_score = (std_words / avg_words) if avg_words > 0 else 0.0

        # Paragraph rhythm (split by double newlines)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            para_sentence_counts = []
            for para in paragraphs:
                para_sentences = [
                    s.strip()
                    for s in re.split(r'[.!?]+', para)
                    if s.strip() and len(s.split()) >= 2
                ]
                para_sentence_counts.append(len(para_sentences))

            # Paragraph rhythm: consistency in paragraph length
            if len(para_sentence_counts) > 1:
                para_avg = statistics.mean(para_sentence_counts)
                para_std = statistics.stdev(para_sentence_counts)
                # Lower variance = more consistent rhythm
                paragraph_rhythm_score = 1.0 - min(1.0, para_std / max(para_avg, 1))
            else:
                paragraph_rhythm_score = 1.0
        else:
            paragraph_rhythm_score = 0.0

        # Opening pattern consistency
        opening_patterns = [self._get_opening_pattern(s) for s in sentences]
        if opening_patterns:
            most_common_pattern = max(set(opening_patterns), key=opening_patterns.count)
            consistency = opening_patterns.count(most_common_pattern) / len(opening_patterns)
        else:
            consistency = 0.0

        # Short vs long sentence ratios
        total = len(sentences)
        short_count = sum(1 for wc in word_counts if wc <= 10)
        long_count = sum(1 for wc in word_counts if wc >= 25)

        return RhythmMetrics(
            avg_syllables_per_sentence=avg_syllables,
            syllable_variance=syllable_variance,
            sentence_length_variety_score=variety_score,
            paragraph_rhythm_score=paragraph_rhythm_score,
            opening_pattern_consistency=consistency,
            short_sentence_ratio=short_count / total,
            long_sentence_ratio=long_count / total,
        )
