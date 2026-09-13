"""Unit tests for the conformity checker — verifying style match scoring."""

from __future__ import annotations

import pytest

from app.modules.style_cloning.conformity import _bounded_similarity, _ratio_similarity, check_conformity
from app.modules.style_cloning.features import extract_all_features
from app.modules.style_cloning.ingestion import ingest_text
from app.modules.style_cloning.profile_generator import generate_voice_fingerprint
from app.modules.style_cloning.schemas import VoiceFingerprint

# ---------------------------------------------------------------------------
# Sample texts
# ---------------------------------------------------------------------------

REFERENCE_TEXT = (
    "The cat sat on the mat. It was a warm day. The sun shone brightly. "
    "Birds sang in the trees. A gentle breeze blew through the garden. "
    "The flowers swayed softly. Children played in the park nearby. "
    "Their laughter echoed across the field. Dogs chased balls on the grass. "
    "The world felt peaceful and calm. The river flowed quietly. "
    "Fish jumped in the still water. Leaves rustled in the wind. "
    "Clouds drifted across the sky. The afternoon passed slowly. "
    "Evening came with golden light. Stars began to appear. "
    "The moon rose over the hills. Night settled in gently. "
    "All was quiet and still."
)

SIMILAR_TEXT = (
    "The dog lay on the rug. It was a cool evening. The moon glowed softly. "
    "Owls hooted in the night. A light wind stirred the curtains. "
    "The garden slept peacefully. Parents read books inside. "
    "Their voices murmured softly. Cats curled on the sofa. "
    "The house felt warm and safe."
)

VERY_DIFFERENT_TEXT = (
    "Although the metaphysical implications of quantum entanglement suggest "
    "an irreconcilable paradox between deterministic causality and the "
    "probabilistic nature of subatomic phenomena, nevertheless the "
    "epistemological ramifications of such observations compel us to "
    "fundamentally reconsider the philosophical underpinnings upon which "
    "our understanding of consciousness, free will, and the teleological "
    "significance of human existence have been historically predicated, "
    "particularly when considering the phenomenological experiences of "
    "anguish and existential dread that characterize the human condition."
)


# ---------------------------------------------------------------------------
# Build a reference fingerprint
# ---------------------------------------------------------------------------


@pytest.fixture
def reference_fingerprint() -> VoiceFingerprint:
    seg = ingest_text(REFERENCE_TEXT)
    features = extract_all_features(seg)
    return generate_voice_fingerprint(features, seg)


# ===================================================================
# Similarity helper tests
# ===================================================================


class TestSimilarityHelpers:
    def test_ratio_similarity_identical(self):
        assert _ratio_similarity(0.5, 0.5) == 1.0

    def test_ratio_similarity_within_tolerance(self):
        score = _ratio_similarity(0.5, 0.55, tolerance=0.15)
        assert score == 1.0

    def test_ratio_similarity_beyond_tolerance(self):
        score = _ratio_similarity(0.5, 0.9, tolerance=0.1)
        assert score < 1.0

    def test_ratio_similarity_zeros(self):
        assert _ratio_similarity(0.0, 0.0) == 1.0

    def test_ratio_similarity_bounded(self):
        score = _ratio_similarity(0.0, 1.0)
        assert 0.0 <= score <= 1.0

    def test_bounded_similarity_identical(self):
        assert _bounded_similarity(5.0, 5.0, 10.0) == 1.0

    def test_bounded_similarity_max_diff(self):
        assert _bounded_similarity(0.0, 10.0, 10.0) == 0.0

    def test_bounded_similarity_partial(self):
        score = _bounded_similarity(5.0, 10.0, 10.0)
        assert score == pytest.approx(0.5)


# ===================================================================
# Conformity check tests
# ===================================================================


class TestConformityCheck:
    def test_identical_text_scores_high(self, reference_fingerprint: VoiceFingerprint):
        """Checking the reference text against its own fingerprint should score very high."""
        result = check_conformity(reference_fingerprint, REFERENCE_TEXT)
        assert result.overall_score >= 70.0

    def test_similar_text_scores_moderate_to_high(self, reference_fingerprint: VoiceFingerprint):
        """Similar simple prose should score reasonably well."""
        result = check_conformity(reference_fingerprint, SIMILAR_TEXT)
        assert result.overall_score >= 40.0

    def test_different_text_scores_lower(self, reference_fingerprint: VoiceFingerprint):
        """Very different prose should score lower than similar prose."""
        similar_result = check_conformity(reference_fingerprint, SIMILAR_TEXT)
        different_result = check_conformity(reference_fingerprint, VERY_DIFFERENT_TEXT)
        assert different_result.overall_score < similar_result.overall_score

    def test_overall_score_bounded(self, reference_fingerprint: VoiceFingerprint):
        result = check_conformity(reference_fingerprint, SIMILAR_TEXT)
        assert 0.0 <= result.overall_score <= 100.0

    def test_sub_scores_bounded(self, reference_fingerprint: VoiceFingerprint):
        result = check_conformity(reference_fingerprint, SIMILAR_TEXT)
        assert 0.0 <= result.vocabulary_score <= 100.0
        assert 0.0 <= result.sentence_score <= 100.0
        assert 0.0 <= result.paragraph_score <= 100.0
        assert 0.0 <= result.rhetorical_score <= 100.0
        assert 0.0 <= result.dialogue_score <= 100.0

    def test_feedback_is_list(self, reference_fingerprint: VoiceFingerprint):
        result = check_conformity(reference_fingerprint, VERY_DIFFERENT_TEXT)
        assert isinstance(result.feedback, list)

    def test_different_text_produces_feedback(self, reference_fingerprint: VoiceFingerprint):
        """Very different text should generate at least some feedback items."""
        result = check_conformity(reference_fingerprint, VERY_DIFFERENT_TEXT)
        assert len(result.feedback) > 0

    def test_vocabulary_score_drops_for_complex_text(self, reference_fingerprint: VoiceFingerprint):
        """Complex text against simple profile should have lower vocabulary score."""
        similar_result = check_conformity(reference_fingerprint, SIMILAR_TEXT)
        different_result = check_conformity(reference_fingerprint, VERY_DIFFERENT_TEXT)
        assert different_result.vocabulary_score <= similar_result.vocabulary_score

    def test_sentence_score_drops_for_complex_text(self, reference_fingerprint: VoiceFingerprint):
        """Complex text with long sentences should score lower on sentence metrics."""
        different_result = check_conformity(reference_fingerprint, VERY_DIFFERENT_TEXT)
        # The very different text has extremely long sentences
        assert different_result.sentence_score < 100.0


# ===================================================================
# Edge case tests
# ===================================================================


class TestConformityEdgeCases:
    def test_very_short_text(self, reference_fingerprint: VoiceFingerprint):
        """Even very short text should return a valid result."""
        result = check_conformity(reference_fingerprint, "Hello there my friend.")
        assert 0.0 <= result.overall_score <= 100.0

    def test_text_with_no_dialogue_against_no_dialogue_profile(self, reference_fingerprint: VoiceFingerprint):
        """Both reference and sample have no dialogue — dialogue score should be high."""
        result = check_conformity(reference_fingerprint, SIMILAR_TEXT)
        assert result.dialogue_score >= 80.0

    def test_text_with_dialogue_against_no_dialogue_profile(self, reference_fingerprint: VoiceFingerprint):
        """Dialogue text against non-dialogue profile."""
        dialogue_text = (
            '"Hello," she said. "How are you?" He replied, "I am fine." '
            '"That is good," she whispered. "Very good indeed."'
        )
        result = check_conformity(reference_fingerprint, dialogue_text)
        # Should still return valid scores
        assert 0.0 <= result.overall_score <= 100.0
