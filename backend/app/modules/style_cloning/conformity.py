"""Conformity Checker — compare generated text features against a stored voice
profile and return a 0-100 match score with actionable feedback."""

from __future__ import annotations

from app.modules.style_cloning.features import extract_all_features
from app.modules.style_cloning.ingestion import ingest_text
from app.modules.style_cloning.schemas import (
    ConformityCheckResult,
    DialogueMetrics,
    ParagraphMetrics,
    RhetoricalMetrics,
    SentenceMetrics,
    VocabularyMetrics,
    VoiceFingerprint,
)

# ---------------------------------------------------------------------------
# Per-dimension similarity helpers
# ---------------------------------------------------------------------------


def _ratio_similarity(a: float, b: float, tolerance: float = 0.15) -> float:
    """Compare two values on a 0-1 scale where values within *tolerance*
    of each other score 1.0 and divergence reduces the score."""
    if a == 0 and b == 0:
        return 1.0
    diff = abs(a - b)
    max_val = max(abs(a), abs(b), 1e-9)
    relative_diff = diff / max_val
    if relative_diff <= tolerance:
        return 1.0
    # Linear decay beyond tolerance
    return max(0.0, 1.0 - (relative_diff - tolerance) / (1.0 - tolerance))


def _bounded_similarity(a: float, b: float, max_diff: float) -> float:
    """Similarity where the max meaningful difference is *max_diff*."""
    diff = abs(a - b)
    return max(0.0, 1.0 - diff / max_diff)


# ---------------------------------------------------------------------------
# Sub-score calculators
# ---------------------------------------------------------------------------


def _vocabulary_score(profile: VocabularyMetrics, sample: VocabularyMetrics) -> tuple[float, list[str]]:
    feedback: list[str] = []
    scores: list[float] = []

    # Lexical density
    s = _ratio_similarity(profile.lexical_density, sample.lexical_density, 0.1)
    scores.append(s)
    if s < 0.7:
        if sample.lexical_density > profile.lexical_density:
            feedback.append("Text is denser than the target style; consider using more function words.")
        else:
            feedback.append("Text is less dense than the target style; consider more content words.")

    # Type-token ratio
    s = _ratio_similarity(profile.type_token_ratio, sample.type_token_ratio, 0.1)
    scores.append(s)
    if s < 0.7:
        if sample.type_token_ratio > profile.type_token_ratio:
            feedback.append("Vocabulary variety is too high; try repeating key terms more.")
        else:
            feedback.append("Vocabulary variety is too low; try using more diverse words.")

    # Reading level
    s = _bounded_similarity(profile.reading_level, sample.reading_level, 6.0)
    scores.append(s)
    if s < 0.7:
        if sample.reading_level > profile.reading_level:
            feedback.append(
                f"Reading level too high ({sample.reading_level:.1f} vs target {profile.reading_level:.1f}); simplify."
            )
        else:
            feedback.append(
                f"Reading level too low ({sample.reading_level:.1f} vs target {profile.reading_level:.1f}); use more complex vocabulary."
            )

    # Average word length
    s = _bounded_similarity(profile.avg_word_length, sample.avg_word_length, 3.0)
    scores.append(s)

    # Rare word frequency
    s = _ratio_similarity(profile.rare_word_frequency, sample.rare_word_frequency, 0.05)
    scores.append(s)

    return (sum(scores) / len(scores) * 100, feedback) if scores else (100.0, feedback)


def _sentence_score(profile: SentenceMetrics, sample: SentenceMetrics) -> tuple[float, list[str]]:
    feedback: list[str] = []
    scores: list[float] = []

    # Average length
    s = _bounded_similarity(profile.avg_length, sample.avg_length, 15.0)
    scores.append(s)
    if s < 0.7:
        if sample.avg_length > profile.avg_length:
            feedback.append(f"Sentences too long (avg {sample.avg_length:.1f} vs target {profile.avg_length:.1f}).")
        else:
            feedback.append(f"Sentences too short (avg {sample.avg_length:.1f} vs target {profile.avg_length:.1f}).")

    # Variance
    s = _ratio_similarity(profile.length_variance, sample.length_variance, 0.3)
    scores.append(s)

    # Structure ratios
    for label, prof_val, samp_val in [
        ("simple", profile.simple_ratio, sample.simple_ratio),
        ("compound", profile.compound_ratio, sample.compound_ratio),
        ("complex", profile.complex_ratio, sample.complex_ratio),
    ]:
        sim = _ratio_similarity(prof_val, samp_val, 0.15)
        scores.append(sim)
        if sim < 0.6:
            feedback.append(f"Proportion of {label} sentences differs significantly from target.")

    # Punctuation energy
    s = _ratio_similarity(
        profile.question_ratio + profile.exclamation_ratio,
        sample.question_ratio + sample.exclamation_ratio,
        0.1,
    )
    scores.append(s)

    return (sum(scores) / len(scores) * 100, feedback) if scores else (100.0, feedback)


def _paragraph_score(profile: ParagraphMetrics, sample: ParagraphMetrics) -> tuple[float, list[str]]:
    feedback: list[str] = []
    scores: list[float] = []

    s = _bounded_similarity(profile.avg_length, sample.avg_length, 5.0)
    scores.append(s)
    if s < 0.7:
        feedback.append("Paragraph lengths differ from the target profile.")

    s = _bounded_similarity(profile.avg_word_count, sample.avg_word_count, 80.0)
    scores.append(s)

    s = _ratio_similarity(profile.transition_word_density, sample.transition_word_density, 0.3)
    scores.append(s)
    if s < 0.7:
        feedback.append("Transition word usage differs from target; adjust connective phrases.")

    s = _ratio_similarity(profile.short_paragraph_ratio, sample.short_paragraph_ratio, 0.2)
    scores.append(s)

    return (sum(scores) / len(scores) * 100, feedback) if scores else (100.0, feedback)


def _rhetorical_score(profile: RhetoricalMetrics, sample: RhetoricalMetrics) -> tuple[float, list[str]]:
    feedback: list[str] = []
    scores: list[float] = []

    for label, prof_val, samp_val in [
        ("metaphor", profile.metaphor_density, sample.metaphor_density),
        ("simile", profile.simile_density, sample.simile_density),
        ("humor", profile.humor_marker_density, sample.humor_marker_density),
        ("emotional intensity", profile.emotional_intensity, sample.emotional_intensity),
    ]:
        s = _ratio_similarity(prof_val, samp_val, 0.3)
        scores.append(s)
        if s < 0.6:
            direction = "more" if samp_val < prof_val else "fewer"
            feedback.append(f"Use {direction} {label} elements to match the target style.")

    return (sum(scores) / len(scores) * 100, feedback) if scores else (100.0, feedback)


def _dialogue_score(profile: DialogueMetrics, sample: DialogueMetrics) -> tuple[float, list[str]]:
    feedback: list[str] = []
    scores: list[float] = []

    # If the profile has negligible dialogue, don't penalize
    if profile.dialogue_ratio < 0.02 and sample.dialogue_ratio < 0.02:
        return 100.0, feedback

    s = _ratio_similarity(profile.dialogue_ratio, sample.dialogue_ratio, 0.15)
    scores.append(s)
    if s < 0.7:
        if sample.dialogue_ratio > profile.dialogue_ratio:
            feedback.append("Too much dialogue relative to the target style.")
        else:
            feedback.append("Too little dialogue relative to the target style.")

    s = _ratio_similarity(profile.said_tag_ratio, sample.said_tag_ratio, 0.2)
    scores.append(s)

    s = _ratio_similarity(profile.action_beat_ratio, sample.action_beat_ratio, 0.2)
    scores.append(s)

    return (sum(scores) / len(scores) * 100, feedback) if scores else (100.0, feedback)


# ---------------------------------------------------------------------------
# Weights for overall score
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "vocabulary": 0.25,
    "sentence": 0.25,
    "paragraph": 0.15,
    "rhetorical": 0.20,
    "dialogue": 0.15,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_conformity(
    profile_fingerprint: VoiceFingerprint,
    text: str,
) -> ConformityCheckResult:
    """Compare *text* against *profile_fingerprint* and return a conformity score.

    Returns a ``ConformityCheckResult`` with an overall 0-100 score plus
    per-dimension sub-scores and actionable feedback.
    """
    segmented = ingest_text(text)
    features = extract_all_features(segmented)

    vocab_score, vocab_fb = _vocabulary_score(profile_fingerprint.vocabulary, features.vocabulary)
    sent_score, sent_fb = _sentence_score(profile_fingerprint.sentence, features.sentence)
    para_score, para_fb = _paragraph_score(profile_fingerprint.paragraph, features.paragraph)
    rhet_score, rhet_fb = _rhetorical_score(profile_fingerprint.rhetorical, features.rhetorical)
    dial_score, dial_fb = _dialogue_score(profile_fingerprint.dialogue, features.dialogue)

    overall = (
        _WEIGHTS["vocabulary"] * vocab_score
        + _WEIGHTS["sentence"] * sent_score
        + _WEIGHTS["paragraph"] * para_score
        + _WEIGHTS["rhetorical"] * rhet_score
        + _WEIGHTS["dialogue"] * dial_score
    )

    feedback = vocab_fb + sent_fb + para_fb + rhet_fb + dial_fb

    return ConformityCheckResult(
        overall_score=round(overall, 2),
        vocabulary_score=round(vocab_score, 2),
        sentence_score=round(sent_score, 2),
        paragraph_score=round(para_score, 2),
        rhetorical_score=round(rhet_score, 2),
        dialogue_score=round(dial_score, 2),
        feedback=feedback,
    )
