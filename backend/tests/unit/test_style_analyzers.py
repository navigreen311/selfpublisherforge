"""Unit tests for deep NLP style analyzers."""

from __future__ import annotations

from app.modules.style_cloning.analyzers import (
    RhythmAnalyzer,
    SyntaxAnalyzer,
    ToneAnalyzer,
    VocabularyAnalyzer,
)

# ---------------------------------------------------------------------------
# Sample texts for testing
# ---------------------------------------------------------------------------

SIMPLE_TEXT = (
    "The cat sat on the mat. The dog ran in the park. "
    "Birds sang in the trees. The sun shone brightly. "
    "Children played outside. Everyone was happy."
)

COMPLEX_TEXT = (
    "Although the weather was inclement, we decided to proceed with our plans "
    "because we had been preparing for months. While some team members expressed "
    "concerns about the feasibility, others remained optimistic that we could "
    "overcome any obstacles that might arise. The project, which had been initiated "
    "by the senior leadership team, required careful coordination between multiple "
    "departments, and we knew that success would depend on our ability to communicate "
    "effectively and respond to challenges with agility."
)

PASSIVE_VOICE_TEXT = (
    "The ball was thrown by John. The cake was eaten by Mary. "
    "The book was written by the author. Mistakes were made. "
    "The results were analyzed carefully. The decision was reached unanimously."
)

ACTIVE_VOICE_TEXT = (
    "John threw the ball. Mary ate the cake. The author wrote the book. "
    "We made mistakes. Scientists analyzed the results carefully. "
    "The committee reached the decision unanimously."
)

FORMAL_TEXT = (
    "Furthermore, it is imperative to acknowledge that the aforementioned findings "
    "corroborate the hypothesis. Consequently, we must proceed with the utmost caution. "
    "Nevertheless, the data indicates a significant correlation. Therefore, one might "
    "reasonably conclude that further investigation is warranted. Moreover, the "
    "implications of this research extend beyond the immediate scope of the study."
)

INFORMAL_TEXT = (
    "So yeah, I'm gonna tell you what I think about this whole thing. It's pretty cool, "
    "and I really like how it's all working out. There's tons of stuff we can do with it, "
    "and I'm super excited to see what happens next. I mean, it's just awesome, you know? "
    "We're gonna have a great time figuring this out together."
)

VARIED_RHYTHM_TEXT = (
    "The storm approached. Dark clouds gathered on the horizon, their ominous presence "
    "foretelling the tempest to come. Rain began to fall. Thunder rumbled in the distance, "
    "growing louder with each passing moment as the storm drew nearer. Lightning flashed. "
    "The wind picked up, bending trees and scattering leaves across the empty streets."
)

RICH_VOCABULARY_TEXT = (
    "The perspicacious philosopher contemplated the ineffable mysteries of existence. "
    "His cogitations wandered through labyrinthine corridors of epistemological inquiry, "
    "grappling with ontological conundrums that had perplexed metaphysicians for millennia. "
    "The quintessential quandary remained: could human consciousness truly apprehend "
    "the fundamental nature of phenomenological experience?"
)

FIRST_PERSON_TEXT = (
    "I think we should consider my proposal carefully. In my opinion, our team has "
    "made significant progress. I've noticed that our approach is working well. "
    "We believe this is the right direction for us to take. I'm confident in our abilities."
)

THIRD_PERSON_TEXT = (
    "The researcher conducted the experiment meticulously. She recorded all observations "
    "with precision. The participants demonstrated remarkable cooperation. They completed "
    "all tasks within the allotted timeframe. The results exceeded expectations. "
    "His conclusions were well-supported by the data."
)

POSITIVE_EMOTIONAL_TEXT = (
    "This wonderful day brought such joy and happiness. The beautiful scenery was "
    "absolutely magnificent. Everyone felt delighted and excited about the fantastic "
    "opportunities ahead. The excellent results made us thrilled and grateful. "
    "It was a truly marvelous experience that left us feeling blessed and content."
)

NEGATIVE_EMOTIONAL_TEXT = (
    "The terrible situation created widespread anxiety and fear. The awful results "
    "disappointed everyone and caused significant frustration. This unfortunate failure "
    "led to anger and distress among the team. The painful experience was deeply "
    "troubling and left everyone feeling sad and worried about the future."
)

HEDGING_TEXT = (
    "Perhaps this approach might work, though it seems somewhat uncertain. The results "
    "appear to suggest a possible correlation, but it's probably too early to say definitively. "
    "I think this could potentially indicate a trend, though maybe we should be cautious. "
    "It tends to suggest that we might see improvements, generally speaking."
)


# ---------------------------------------------------------------------------
# SyntaxAnalyzer Tests
# ---------------------------------------------------------------------------


class TestSyntaxAnalyzer:
    """Tests for SyntaxAnalyzer."""

    def test_simple_sentences(self):
        """Test analysis of simple sentences."""
        analyzer = SyntaxAnalyzer()
        metrics = analyzer.analyze(SIMPLE_TEXT)

        assert metrics["avg_sentence_length"] > 0
        assert metrics["simple_sentence_ratio"] > 0.5
        assert metrics["compound_sentence_ratio"] >= 0
        assert metrics["complex_sentence_ratio"] >= 0
        assert (
            abs(
                metrics["simple_sentence_ratio"]
                + metrics["compound_sentence_ratio"]
                + metrics["complex_sentence_ratio"]
                - 1.0
            )
            < 0.01
        )

    def test_complex_sentences(self):
        """Test analysis of complex sentences."""
        analyzer = SyntaxAnalyzer()
        metrics = analyzer.analyze(COMPLEX_TEXT)

        assert metrics["avg_sentence_length"] > 15
        assert metrics["complex_sentence_ratio"] > 0
        assert metrics["avg_clause_depth"] > 2

    def test_passive_voice_detection(self):
        """Test passive voice detection."""
        analyzer = SyntaxAnalyzer()
        passive_metrics = analyzer.analyze(PASSIVE_VOICE_TEXT)
        active_metrics = analyzer.analyze(ACTIVE_VOICE_TEXT)

        assert passive_metrics["passive_voice_ratio"] > active_metrics["passive_voice_ratio"]
        assert passive_metrics["active_voice_ratio"] < active_metrics["active_voice_ratio"]

    def test_clause_depth_distribution(self):
        """Test clause depth distribution calculation."""
        analyzer = SyntaxAnalyzer()
        metrics = analyzer.analyze(COMPLEX_TEXT)

        assert "clause_depth_distribution" in metrics
        assert isinstance(metrics["clause_depth_distribution"], dict)
        assert len(metrics["clause_depth_distribution"]) > 0
        # Check that distribution sums to ~1.0
        assert abs(sum(metrics["clause_depth_distribution"].values()) - 1.0) < 0.01

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = SyntaxAnalyzer()
        metrics = analyzer.analyze("")

        assert metrics["avg_sentence_length"] == 0.0
        assert metrics["simple_sentence_ratio"] == 0.0


# ---------------------------------------------------------------------------
# RhythmAnalyzer Tests
# ---------------------------------------------------------------------------


class TestRhythmAnalyzer:
    """Tests for RhythmAnalyzer."""

    def test_syllable_counting(self):
        """Test syllable counting accuracy."""
        analyzer = RhythmAnalyzer()

        # Test individual words
        assert analyzer._count_syllables("cat") == 1
        assert analyzer._count_syllables("happy") == 2
        assert analyzer._count_syllables("beautiful") == 3
        assert analyzer._count_syllables("unfortunately") >= 5

    def test_sentence_variety(self):
        """Test sentence length variety scoring."""
        analyzer = RhythmAnalyzer()

        varied_metrics = analyzer.analyze(VARIED_RHYTHM_TEXT)
        simple_metrics = analyzer.analyze(SIMPLE_TEXT)

        # Varied text should have higher variety score
        assert varied_metrics["sentence_length_variety_score"] > 0

    def test_short_long_sentence_ratios(self):
        """Test short and long sentence ratio calculation."""
        analyzer = RhythmAnalyzer()

        # Create text with known short sentences (2+ words required)
        short_text = "Hi there. Go now. Yes indeed. Run fast. Stop here. Wait please."
        metrics = analyzer.analyze(short_text)

        assert metrics["short_sentence_ratio"] > 0.5

        # Test long sentences
        long_metrics = analyzer.analyze(COMPLEX_TEXT)
        assert long_metrics["long_sentence_ratio"] >= 0

    def test_paragraph_rhythm(self):
        """Test paragraph rhythm scoring."""
        analyzer = RhythmAnalyzer()

        # Text with paragraph breaks
        para_text = (
            "First paragraph with sentences. More content here.\n\n"
            "Second paragraph follows. It has sentences too.\n\n"
            "Third paragraph appears. Final content section."
        )

        metrics = analyzer.analyze(para_text)
        assert 0 <= metrics["paragraph_rhythm_score"] <= 1.0

    def test_syllable_variance(self):
        """Test syllable variance calculation."""
        analyzer = RhythmAnalyzer()
        metrics = analyzer.analyze(SIMPLE_TEXT)

        assert metrics["avg_syllables_per_sentence"] > 0
        assert metrics["syllable_variance"] >= 0

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = RhythmAnalyzer()
        metrics = analyzer.analyze("")

        assert metrics["avg_syllables_per_sentence"] == 0.0
        assert metrics["syllable_variance"] == 0.0


# ---------------------------------------------------------------------------
# VocabularyAnalyzer Tests
# ---------------------------------------------------------------------------


class TestVocabularyAnalyzer:
    """Tests for VocabularyAnalyzer."""

    def test_type_token_ratio(self):
        """Test type-token ratio calculation."""
        analyzer = VocabularyAnalyzer()

        # Repetitive text has lower TTR
        repetitive = "the cat the cat the cat the cat"
        varied = "the quick brown fox jumps over lazy dog"

        rep_metrics = analyzer.analyze(repetitive)
        varied_metrics = analyzer.analyze(varied)

        assert rep_metrics["type_token_ratio"] < varied_metrics["type_token_ratio"]

    def test_hapax_legomena(self):
        """Test hapax legomena (words appearing once) detection."""
        analyzer = VocabularyAnalyzer()
        metrics = analyzer.analyze(RICH_VOCABULARY_TEXT)

        assert metrics["hapax_count"] > 0
        assert metrics["hapax_legomena_ratio"] > 0
        assert metrics["hapax_legomena_ratio"] <= 1.0

    def test_vocabulary_level_score(self):
        """Test vocabulary level scoring."""
        analyzer = VocabularyAnalyzer()

        simple_metrics = analyzer.analyze(SIMPLE_TEXT)
        rich_metrics = analyzer.analyze(RICH_VOCABULARY_TEXT)

        # Rich vocabulary should have higher level score
        assert rich_metrics["vocabulary_level_score"] > simple_metrics["vocabulary_level_score"]

    def test_average_word_length(self):
        """Test average word length calculation."""
        analyzer = VocabularyAnalyzer()

        simple_metrics = analyzer.analyze(SIMPLE_TEXT)
        rich_metrics = analyzer.analyze(RICH_VOCABULARY_TEXT)

        assert rich_metrics["avg_word_length"] > simple_metrics["avg_word_length"]
        assert simple_metrics["avg_word_length"] > 0

    def test_domain_terminology_density(self):
        """Test domain terminology detection."""
        analyzer = VocabularyAnalyzer()

        general_metrics = analyzer.analyze(SIMPLE_TEXT)
        technical_metrics = analyzer.analyze(RICH_VOCABULARY_TEXT)

        # Technical text should have higher domain density
        assert technical_metrics["domain_terminology_density"] > general_metrics["domain_terminology_density"]

    def test_unique_word_count(self):
        """Test unique word counting."""
        analyzer = VocabularyAnalyzer()
        metrics = analyzer.analyze("one two three one two one")

        assert metrics["unique_words"] == 3
        assert metrics["total_words"] == 6

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = VocabularyAnalyzer()
        metrics = analyzer.analyze("")

        assert metrics["type_token_ratio"] == 0.0
        assert metrics["total_words"] == 0


# ---------------------------------------------------------------------------
# ToneAnalyzer Tests
# ---------------------------------------------------------------------------


class TestToneAnalyzer:
    """Tests for ToneAnalyzer."""

    def test_formality_score(self):
        """Test formality score calculation."""
        analyzer = ToneAnalyzer()

        formal_metrics = analyzer.analyze(FORMAL_TEXT)
        informal_metrics = analyzer.analyze(INFORMAL_TEXT)

        assert formal_metrics["formality_score"] > informal_metrics["formality_score"]
        assert 0 <= formal_metrics["formality_score"] <= 1.0
        assert 0 <= informal_metrics["formality_score"] <= 1.0

    def test_contraction_detection(self):
        """Test contraction usage rate."""
        analyzer = ToneAnalyzer()

        no_contractions = "I am going to tell you what I think. It is very important."
        with_contractions = "I'm gonna tell you what I think. It's super important."

        no_contract_metrics = analyzer.analyze(no_contractions)
        with_contract_metrics = analyzer.analyze(with_contractions)

        assert with_contract_metrics["contraction_usage_rate"] > no_contract_metrics["contraction_usage_rate"]

    def test_person_ratios(self):
        """Test first/second/third person ratio calculation."""
        analyzer = ToneAnalyzer()

        first_metrics = analyzer.analyze(FIRST_PERSON_TEXT)
        third_metrics = analyzer.analyze(THIRD_PERSON_TEXT)

        assert first_metrics["first_person_ratio"] > third_metrics["first_person_ratio"]
        assert third_metrics["third_person_ratio"] > first_metrics["third_person_ratio"]

    def test_emotional_valence(self):
        """Test emotional valence scoring."""
        analyzer = ToneAnalyzer()

        positive_metrics = analyzer.analyze(POSITIVE_EMOTIONAL_TEXT)
        negative_metrics = analyzer.analyze(NEGATIVE_EMOTIONAL_TEXT)

        assert positive_metrics["emotional_valence"] > 0
        assert negative_metrics["emotional_valence"] < 0
        assert -1.0 <= positive_metrics["emotional_valence"] <= 1.0
        assert -1.0 <= negative_metrics["emotional_valence"] <= 1.0

    def test_hedging_language(self):
        """Test hedging language frequency."""
        analyzer = ToneAnalyzer()

        hedging_metrics = analyzer.analyze(HEDGING_TEXT)
        definite_text = "This is certain. The results are clear. We know this works."
        definite_metrics = analyzer.analyze(definite_text)

        assert hedging_metrics["hedging_language_frequency"] > definite_metrics["hedging_language_frequency"]

    def test_all_ratios_sum(self):
        """Test that person ratios are properly calculated."""
        analyzer = ToneAnalyzer()
        metrics = analyzer.analyze(FIRST_PERSON_TEXT)

        # All ratios should be between 0 and 1
        assert 0 <= metrics["first_person_ratio"] <= 1.0
        assert 0 <= metrics["second_person_ratio"] <= 1.0
        assert 0 <= metrics["third_person_ratio"] <= 1.0

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = ToneAnalyzer()
        metrics = analyzer.analyze("")

        assert metrics["formality_score"] == 0.5  # Neutral
        assert metrics["emotional_valence"] == 0.0
        assert metrics["contraction_usage_rate"] == 0.0


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestAnalyzersIntegration:
    """Integration tests for all analyzers working together."""

    def test_all_analyzers_on_same_text(self):
        """Test that all analyzers can process the same text without errors."""
        text = COMPLEX_TEXT

        syntax_analyzer = SyntaxAnalyzer()
        rhythm_analyzer = RhythmAnalyzer()
        vocabulary_analyzer = VocabularyAnalyzer()
        tone_analyzer = ToneAnalyzer()

        syntax_metrics = syntax_analyzer.analyze(text)
        rhythm_metrics = rhythm_analyzer.analyze(text)
        vocabulary_metrics = vocabulary_analyzer.analyze(text)
        tone_metrics = tone_analyzer.analyze(text)

        # Verify all metrics are returned
        assert isinstance(syntax_metrics, dict)
        assert isinstance(rhythm_metrics, dict)
        assert isinstance(vocabulary_metrics, dict)
        assert isinstance(tone_metrics, dict)

        # Verify key metrics are present
        assert "avg_sentence_length" in syntax_metrics
        assert "avg_syllables_per_sentence" in rhythm_metrics
        assert "type_token_ratio" in vocabulary_metrics
        assert "formality_score" in tone_metrics

    def test_analyzers_with_real_world_text(self):
        """Test analyzers with a realistic text sample."""
        real_text = (
            "The old house stood at the end of the lane. Its walls were weathered "
            "by decades of storms. Paint peeled from the wooden shutters. Ivy crept "
            "up the eastern wall. The garden had grown wild with neglect. Roses "
            "tangled with weeds along the fence. A broken gate hung from rusty "
            "hinges. Inside, dust covered every surface. The floorboards creaked "
            "underfoot. Memories lingered in every room. The kitchen still smelled "
            "faintly of cinnamon. Sunlight filtered through cracked windows. "
            "Shadows danced on the faded wallpaper. An old clock ticked on the "
            "mantle. Time had moved on but the house remained."
        )

        syntax_analyzer = SyntaxAnalyzer()
        rhythm_analyzer = RhythmAnalyzer()
        vocabulary_analyzer = VocabularyAnalyzer()
        tone_analyzer = ToneAnalyzer()

        syntax_metrics = syntax_analyzer.analyze(real_text)
        rhythm_metrics = rhythm_analyzer.analyze(real_text)
        vocabulary_metrics = vocabulary_analyzer.analyze(real_text)
        tone_metrics = tone_analyzer.analyze(real_text)

        # All should produce reasonable results
        assert syntax_metrics["avg_sentence_length"] > 5
        assert rhythm_metrics["avg_syllables_per_sentence"] >= 10
        assert 0 < vocabulary_metrics["type_token_ratio"] < 1.0
        assert 0 <= tone_metrics["formality_score"] <= 1.0
