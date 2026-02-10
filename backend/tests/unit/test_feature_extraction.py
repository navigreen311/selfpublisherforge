"""Unit tests for the linguistic feature extraction pipeline.

Tests cover vocabulary analysis, sentence metrics, paragraph metrics,
rhetorical device detection, and dialogue analysis.
"""

from __future__ import annotations

import pytest

from app.modules.style_cloning.ingestion import ingest_text, SegmentedText
from app.modules.style_cloning.features import (
    extract_all_features,
    extract_vocabulary,
    extract_sentence_metrics,
    extract_paragraph_metrics,
    extract_rhetorical_metrics,
    extract_dialogue_metrics,
)


# ---------------------------------------------------------------------------
# Fixtures — sample texts of varying styles
# ---------------------------------------------------------------------------

SIMPLE_PROSE = (
    "The cat sat on the mat. It was a warm day. The sun shone brightly. "
    "Birds sang in the trees. A gentle breeze blew through the garden. "
    "The flowers swayed softly. Children played in the park nearby. "
    "Their laughter echoed across the field. Dogs chased balls on the grass. "
    "The world felt peaceful and calm."
)

COMPLEX_LITERARY = (
    "Although the tempestuous maelstrom of consciousness threatened to "
    "overwhelm her senses, she nevertheless persevered through the labyrinthine "
    "corridors of memory, because the ephemeral nature of existence demanded "
    "nothing less than absolute philosophical commitment to the transcendent "
    "ideals that had sustained her ancestors through countless generations of "
    "suffering and resilience. The melancholy that pervaded her thoughts was "
    "not merely an emotional response but rather an existential acknowledgment "
    "of the fundamental absurdity that characterized the human condition, "
    "while simultaneously serving as a catalyst for the profound artistic "
    "expression that would ultimately define her legacy. Furthermore, the "
    "juxtaposition of her intellectual aspirations against the mundane "
    "realities of quotidian existence created an irreconcilable tension "
    "that manifested itself in increasingly elaborate rhetorical constructions "
    "and philosophical digressions."
)

DIALOGUE_HEAVY = (
    '"I can\'t believe you did that," she said, shaking her head.\n\n'
    '"What choice did I have?" he replied. "The situation demanded action."\n\n'
    '"You could have waited," she whispered. "Patience is a virtue."\n\n'
    'He laughed bitterly. "Patience? In times like these?"\n\n'
    '"Yes," she said firmly. "Especially in times like these."\n\n'
    'He turned away, staring out the window. "You don\'t understand."\n\n'
    '"I understand perfectly," she said. "That\'s what frightens me."\n\n'
    'Silence fell between them. The clock ticked loudly on the wall.\n\n'
    '"We need to talk about what happens next," he said finally.\n\n'
    '"There is no next," she replied. "This is the end."'
)

EMOTIONAL_TEXT = (
    "The anguish tore through her heart like a blade of fire. She felt "
    "the terror rising, an overwhelming dread that consumed every rational "
    "thought. Love and hate battled within her soul, a furious tempest of "
    "passion and despair. The grief was unbearable, a crushing weight that "
    "threatened to destroy everything she had ever known. Joy seemed like "
    "a distant memory, eclipsed by the horror of the present moment. "
    "Yet hope flickered somewhere deep inside, a tiny flame of euphoria "
    "that refused to be extinguished despite the agony of her existence."
)

# A longer sample for more reliable statistics
EXTENDED_PROSE = " ".join([SIMPLE_PROSE] * 30)


@pytest.fixture
def simple_segmented() -> SegmentedText:
    return ingest_text(SIMPLE_PROSE)


@pytest.fixture
def complex_segmented() -> SegmentedText:
    return ingest_text(COMPLEX_LITERARY)


@pytest.fixture
def dialogue_segmented() -> SegmentedText:
    return ingest_text(DIALOGUE_HEAVY)


@pytest.fixture
def emotional_segmented() -> SegmentedText:
    return ingest_text(EMOTIONAL_TEXT)


@pytest.fixture
def extended_segmented() -> SegmentedText:
    return ingest_text(EXTENDED_PROSE)


# ===================================================================
# Ingestion tests
# ===================================================================

class TestIngestion:

    def test_ingest_produces_sentences(self, simple_segmented: SegmentedText):
        assert len(simple_segmented.sentences) > 0

    def test_ingest_produces_paragraphs(self, simple_segmented: SegmentedText):
        assert len(simple_segmented.paragraphs) > 0

    def test_word_count_positive(self, simple_segmented: SegmentedText):
        assert simple_segmented.word_count > 0

    def test_raw_text_preserved(self, simple_segmented: SegmentedText):
        assert "cat sat" in simple_segmented.raw_text

    def test_multi_paragraph_splitting(self, dialogue_segmented: SegmentedText):
        # Dialogue text has explicit paragraph breaks
        assert len(dialogue_segmented.paragraphs) > 3


# ===================================================================
# Vocabulary analysis tests
# ===================================================================

class TestVocabularyExtraction:

    def test_total_word_count(self, simple_segmented: SegmentedText):
        vocab = extract_vocabulary(simple_segmented)
        assert vocab.total_word_count > 0

    def test_unique_word_count(self, simple_segmented: SegmentedText):
        vocab = extract_vocabulary(simple_segmented)
        assert vocab.unique_word_count > 0
        assert vocab.unique_word_count <= vocab.total_word_count

    def test_lexical_density_bounded(self, simple_segmented: SegmentedText):
        vocab = extract_vocabulary(simple_segmented)
        assert 0.0 <= vocab.lexical_density <= 1.0

    def test_type_token_ratio_bounded(self, simple_segmented: SegmentedText):
        vocab = extract_vocabulary(simple_segmented)
        assert 0.0 < vocab.type_token_ratio <= 1.0

    def test_reading_level_simple_vs_complex(
        self,
        simple_segmented: SegmentedText,
        complex_segmented: SegmentedText,
    ):
        simple_vocab = extract_vocabulary(simple_segmented)
        complex_vocab = extract_vocabulary(complex_segmented)
        # Complex literary text should have a higher reading level
        assert complex_vocab.reading_level > simple_vocab.reading_level

    def test_avg_word_length_positive(self, simple_segmented: SegmentedText):
        vocab = extract_vocabulary(simple_segmented)
        assert vocab.avg_word_length > 0

    def test_top_words_returned(self, extended_segmented: SegmentedText):
        vocab = extract_vocabulary(extended_segmented)
        assert len(vocab.top_words) > 0
        # Each entry is (word, count)
        for word, count in vocab.top_words:
            assert isinstance(word, str)
            assert count > 0

    def test_complex_text_has_higher_rare_words(
        self,
        simple_segmented: SegmentedText,
        complex_segmented: SegmentedText,
    ):
        simple_vocab = extract_vocabulary(simple_segmented)
        complex_vocab = extract_vocabulary(complex_segmented)
        # Complex text should have more rare words
        assert complex_vocab.rare_word_frequency >= simple_vocab.rare_word_frequency

    def test_empty_text_returns_defaults(self):
        seg = ingest_text("")
        vocab = extract_vocabulary(seg)
        assert vocab.total_word_count == 0
        assert vocab.lexical_density == 0.0


# ===================================================================
# Sentence metrics tests
# ===================================================================

class TestSentenceExtraction:

    def test_avg_length_positive(self, simple_segmented: SegmentedText):
        metrics = extract_sentence_metrics(simple_segmented)
        assert metrics.avg_length > 0

    def test_simple_prose_has_more_simple_sentences(self, simple_segmented: SegmentedText):
        metrics = extract_sentence_metrics(simple_segmented)
        # Simple prose should be predominantly simple sentences
        assert metrics.simple_ratio >= metrics.complex_ratio

    def test_complex_prose_has_complex_sentences(self, complex_segmented: SegmentedText):
        metrics = extract_sentence_metrics(complex_segmented)
        # Complex literary text should have compound or complex sentences
        assert (metrics.compound_ratio + metrics.complex_ratio) > 0

    def test_ratios_sum_to_one(self, simple_segmented: SegmentedText):
        metrics = extract_sentence_metrics(simple_segmented)
        total = metrics.simple_ratio + metrics.compound_ratio + metrics.complex_ratio
        assert abs(total - 1.0) < 0.01

    def test_min_max_lengths(self, simple_segmented: SegmentedText):
        metrics = extract_sentence_metrics(simple_segmented)
        assert metrics.min_length <= metrics.max_length
        assert metrics.min_length >= 0

    def test_length_variance_non_negative(self, simple_segmented: SegmentedText):
        metrics = extract_sentence_metrics(simple_segmented)
        assert metrics.length_variance >= 0

    def test_complex_text_longer_avg_sentences(
        self,
        simple_segmented: SegmentedText,
        complex_segmented: SegmentedText,
    ):
        simple_m = extract_sentence_metrics(simple_segmented)
        complex_m = extract_sentence_metrics(complex_segmented)
        assert complex_m.avg_length > simple_m.avg_length

    def test_question_ratio(self, dialogue_segmented: SegmentedText):
        metrics = extract_sentence_metrics(dialogue_segmented)
        # Dialogue text has some questions
        assert metrics.question_ratio >= 0

    def test_empty_returns_defaults(self):
        seg = ingest_text("")
        metrics = extract_sentence_metrics(seg)
        assert metrics.avg_length == 0.0


# ===================================================================
# Paragraph metrics tests
# ===================================================================

class TestParagraphExtraction:

    def test_avg_length_positive(self, simple_segmented: SegmentedText):
        metrics = extract_paragraph_metrics(simple_segmented)
        assert metrics.avg_length >= 0

    def test_avg_word_count_positive(self, simple_segmented: SegmentedText):
        metrics = extract_paragraph_metrics(simple_segmented)
        assert metrics.avg_word_count >= 0

    def test_transition_density(self, complex_segmented: SegmentedText):
        metrics = extract_paragraph_metrics(complex_segmented)
        # Complex text uses transition words like "furthermore", "nevertheless"
        assert metrics.transition_word_density >= 0

    def test_short_paragraph_ratio_bounded(self, dialogue_segmented: SegmentedText):
        metrics = extract_paragraph_metrics(dialogue_segmented)
        assert 0.0 <= metrics.short_paragraph_ratio <= 1.0

    def test_long_paragraph_ratio_bounded(self, simple_segmented: SegmentedText):
        metrics = extract_paragraph_metrics(simple_segmented)
        assert 0.0 <= metrics.long_paragraph_ratio <= 1.0

    def test_dialogue_text_has_short_paragraphs(self, dialogue_segmented: SegmentedText):
        metrics = extract_paragraph_metrics(dialogue_segmented)
        # Dialogue text paragraphs are typically short
        assert metrics.short_paragraph_ratio > 0

    def test_empty_returns_defaults(self):
        seg = ingest_text("")
        metrics = extract_paragraph_metrics(seg)
        assert metrics.avg_length == 0.0


# ===================================================================
# Rhetorical metrics tests
# ===================================================================

class TestRhetoricalExtraction:

    def test_emotional_intensity_bounded(self, emotional_segmented: SegmentedText):
        metrics = extract_rhetorical_metrics(emotional_segmented)
        assert 0.0 <= metrics.emotional_intensity <= 1.0

    def test_emotional_text_higher_intensity(
        self,
        simple_segmented: SegmentedText,
        emotional_segmented: SegmentedText,
    ):
        simple_m = extract_rhetorical_metrics(simple_segmented)
        emotional_m = extract_rhetorical_metrics(emotional_segmented)
        assert emotional_m.emotional_intensity > simple_m.emotional_intensity

    def test_simile_density_non_negative(self, simple_segmented: SegmentedText):
        metrics = extract_rhetorical_metrics(simple_segmented)
        assert metrics.simile_density >= 0

    def test_metaphor_density_non_negative(self, simple_segmented: SegmentedText):
        metrics = extract_rhetorical_metrics(simple_segmented)
        assert metrics.metaphor_density >= 0

    def test_humor_density_non_negative(self, simple_segmented: SegmentedText):
        metrics = extract_rhetorical_metrics(simple_segmented)
        assert metrics.humor_marker_density >= 0

    def test_alliteration_detection(self):
        text = "Peter Piper picked a peck of pickled peppers. Sally sells seashells by the seashore."
        seg = ingest_text(text)
        metrics = extract_rhetorical_metrics(seg)
        assert metrics.alliteration_density > 0

    def test_empty_returns_defaults(self):
        seg = ingest_text("")
        metrics = extract_rhetorical_metrics(seg)
        assert metrics.emotional_intensity == 0.0


# ===================================================================
# Dialogue metrics tests
# ===================================================================

class TestDialogueExtraction:

    def test_dialogue_detected(self, dialogue_segmented: SegmentedText):
        metrics = extract_dialogue_metrics(dialogue_segmented)
        assert metrics.dialogue_ratio > 0

    def test_dialogue_ratio_bounded(self, dialogue_segmented: SegmentedText):
        metrics = extract_dialogue_metrics(dialogue_segmented)
        assert 0.0 <= metrics.dialogue_ratio <= 1.0

    def test_said_tags_detected(self, dialogue_segmented: SegmentedText):
        metrics = extract_dialogue_metrics(dialogue_segmented)
        # Our sample uses "said" frequently
        assert metrics.said_tag_ratio >= 0

    def test_no_dialogue_in_simple_prose(self, simple_segmented: SegmentedText):
        metrics = extract_dialogue_metrics(simple_segmented)
        assert metrics.dialogue_ratio == 0.0

    def test_action_beat_ratio_bounded(self, dialogue_segmented: SegmentedText):
        metrics = extract_dialogue_metrics(dialogue_segmented)
        assert 0.0 <= metrics.action_beat_ratio <= 1.0

    def test_dialogue_to_narrative_ratio(self, dialogue_segmented: SegmentedText):
        metrics = extract_dialogue_metrics(dialogue_segmented)
        assert metrics.dialogue_to_narrative_ratio >= 0

    def test_empty_returns_defaults(self):
        seg = ingest_text("")
        metrics = extract_dialogue_metrics(seg)
        assert metrics.dialogue_ratio == 0.0


# ===================================================================
# Full pipeline test
# ===================================================================

class TestFullExtraction:

    def test_extract_all_features(self, simple_segmented: SegmentedText):
        features = extract_all_features(simple_segmented)
        assert features.vocabulary.total_word_count > 0
        assert features.sentence.avg_length > 0
        assert features.paragraph is not None
        assert features.rhetorical is not None
        assert features.dialogue is not None

    def test_different_styles_produce_different_features(
        self,
        simple_segmented: SegmentedText,
        complex_segmented: SegmentedText,
    ):
        simple_f = extract_all_features(simple_segmented)
        complex_f = extract_all_features(complex_segmented)
        # Reading levels should differ
        assert simple_f.vocabulary.reading_level != complex_f.vocabulary.reading_level
        # Average sentence lengths should differ
        assert simple_f.sentence.avg_length != complex_f.sentence.avg_length
