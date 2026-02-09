"""Unit tests for readability scoring algorithms."""

import pytest

from app.modules.ai_writing.readability import (
    analyze_readability,
    count_syllables,
    flesch_kincaid_grade,
    flesch_reading_ease,
    gunning_fog,
    smog_index,
    ReadabilityMetrics,
)


# ---------------------------------------------------------------------------
# Syllable counting
# ---------------------------------------------------------------------------

class TestCountSyllables:
    def test_single_syllable_words(self):
        assert count_syllables("the") == 1
        assert count_syllables("cat") == 1
        assert count_syllables("dog") == 1

    def test_two_syllable_words(self):
        assert count_syllables("water") == 2
        assert count_syllables("happy") == 2
        assert count_syllables("table") == 2

    def test_three_syllable_words(self):
        assert count_syllables("beautiful") == 3
        assert count_syllables("important") == 3

    def test_empty_string(self):
        assert count_syllables("") == 0

    def test_short_words(self):
        assert count_syllables("I") == 1
        assert count_syllables("an") == 1
        assert count_syllables("go") == 1

    def test_silent_e(self):
        """Words ending in silent-e should not get an extra syllable."""
        assert count_syllables("make") == 1
        assert count_syllables("name") == 1


# ---------------------------------------------------------------------------
# Flesch-Kincaid Grade Level
# ---------------------------------------------------------------------------

class TestFleschKincaidGrade:
    def test_zero_words(self):
        assert flesch_kincaid_grade(0, 1, 0) == 0.0

    def test_zero_sentences(self):
        assert flesch_kincaid_grade(10, 0, 15) == 0.0

    def test_simple_text(self):
        """Simple text should produce a low grade level."""
        # 10 words, 2 sentences, 12 syllables
        grade = flesch_kincaid_grade(10, 2, 12)
        assert grade >= 0.0
        assert grade < 10.0

    def test_complex_text(self):
        """Complex text should produce a higher grade level."""
        # 50 words, 2 sentences, 100 syllables
        grade = flesch_kincaid_grade(50, 2, 100)
        assert grade > 5.0

    def test_result_non_negative(self):
        """Grade level should never be negative."""
        grade = flesch_kincaid_grade(5, 5, 5)
        assert grade >= 0.0


# ---------------------------------------------------------------------------
# Flesch Reading Ease
# ---------------------------------------------------------------------------

class TestFleschReadingEase:
    def test_zero_words(self):
        assert flesch_reading_ease(0, 1, 0) == 0.0

    def test_zero_sentences(self):
        assert flesch_reading_ease(10, 0, 15) == 0.0

    def test_simple_text_high_score(self):
        """Simple text should have a higher reading ease score."""
        # Short sentences, few syllables
        score = flesch_reading_ease(20, 4, 24)
        assert score > 60.0

    def test_complex_text_low_score(self):
        """Complex text should have a lower reading ease score."""
        # Long sentences, many syllables
        score = flesch_reading_ease(100, 2, 250)
        assert score < 30.0


# ---------------------------------------------------------------------------
# Gunning Fog
# ---------------------------------------------------------------------------

class TestGunningFog:
    def test_empty_word_list(self):
        assert gunning_fog([], 1) == 0.0

    def test_zero_sentences(self):
        assert gunning_fog(["hello", "world"], 0) == 0.0

    def test_simple_words(self):
        """Simple one-syllable words should yield a low fog index."""
        words = ["the", "cat", "sat", "on", "the", "mat"]
        fog = gunning_fog(words, 1)
        assert fog < 10.0

    def test_complex_words_increase_score(self):
        """Adding multi-syllable words should increase the fog index."""
        simple = ["the", "cat", "ran"]
        complex_words = ["the", "cat", "metamorphosis", "philosophical", "transcendental"]
        fog_simple = gunning_fog(simple, 1)
        fog_complex = gunning_fog(complex_words, 1)
        assert fog_complex > fog_simple


# ---------------------------------------------------------------------------
# SMOG Index
# ---------------------------------------------------------------------------

class TestSmogIndex:
    def test_zero_sentences(self):
        assert smog_index(0, 0) == 0.0

    def test_no_polysyllabic_words(self):
        """Even with 0 polysyllabic words, SMOG formula adds ~3.13."""
        result = smog_index(0, 10)
        assert abs(result - 3.13) < 0.1

    def test_increases_with_polysyllabic_count(self):
        """More polysyllabic words should increase the SMOG index."""
        s1 = smog_index(5, 30)
        s2 = smog_index(20, 30)
        assert s2 > s1


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

class TestAnalyzeReadability:
    SIMPLE_TEXT = (
        "The cat sat on the mat. The dog ran in the park. "
        "Birds fly in the sky. Fish swim in the sea."
    )
    COMPLEX_TEXT = (
        "The multifaceted philosophical underpinnings of contemporary "
        "epistemological discourse necessitate a comprehensive understanding "
        "of interdisciplinary methodological frameworks. Furthermore, the "
        "juxtaposition of theoretical paradigms illuminates the fundamental "
        "characteristics of postmodern intellectual inquiry."
    )

    def test_returns_metrics_dataclass(self):
        result = analyze_readability(self.SIMPLE_TEXT)
        assert isinstance(result, ReadabilityMetrics)

    def test_word_count(self):
        result = analyze_readability(self.SIMPLE_TEXT)
        assert result.word_count > 0

    def test_sentence_count(self):
        result = analyze_readability(self.SIMPLE_TEXT)
        assert result.sentence_count == 4

    def test_simple_text_reading_level(self):
        result = analyze_readability(self.SIMPLE_TEXT)
        assert result.reading_level in ("Kindergarten", "Elementary", "Middle School")

    def test_complex_text_higher_grade(self):
        simple = analyze_readability(self.SIMPLE_TEXT)
        complex_ = analyze_readability(self.COMPLEX_TEXT)
        assert complex_.flesch_kincaid_grade > simple.flesch_kincaid_grade

    def test_complex_text_lower_reading_ease(self):
        simple = analyze_readability(self.SIMPLE_TEXT)
        complex_ = analyze_readability(self.COMPLEX_TEXT)
        assert complex_.flesch_reading_ease < simple.flesch_reading_ease

    def test_all_fields_populated(self):
        result = analyze_readability(self.SIMPLE_TEXT)
        assert result.flesch_kincaid_grade >= 0
        assert result.gunning_fog >= 0
        assert result.smog_index >= 0
        assert result.syllable_count > 0
        assert result.avg_words_per_sentence > 0
        assert result.avg_syllables_per_word > 0
        assert result.reading_level != ""

    def test_empty_text(self):
        result = analyze_readability("")
        assert result.word_count == 0
        assert result.reading_level == "Kindergarten"
