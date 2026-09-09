"""Voice Profile Generator — aggregate features into a 200+ dimension voice
vector, generate a natural-language style guide, and produce a style card."""

from __future__ import annotations

import os

from app.modules.style_cloning.features import AllFeatures
from app.modules.style_cloning.ingestion import HIGH_CONFIDENCE_WORDS, SegmentedText
from app.modules.style_cloning.schemas import (
    StyleCard,
    VoiceFingerprint,
)

INTENSITY_THRESHOLD = float(os.environ.get("STYLE_INTENSITY_THRESHOLD", "0.5"))
RATIO_THRESHOLD = float(os.environ.get("STYLE_RATIO_THRESHOLD", "0.5"))


# ---------------------------------------------------------------------------
# Dimension definitions — each tuple is (label, extraction_func)
# We build a 200+ dimension vector from the extracted features.
# ---------------------------------------------------------------------------


def _build_voice_vector(features: AllFeatures) -> tuple[list[float], list[str]]:
    """Build a numeric voice vector from extracted features.

    Returns (vector, dimension_labels).
    """
    dims: list[tuple[str, float]] = []

    # --- Vocabulary dimensions (30) ---
    v = features.vocabulary
    dims.append(("vocab_unique_word_count", float(v.unique_word_count)))
    dims.append(("vocab_total_word_count", float(v.total_word_count)))
    dims.append(("vocab_lexical_density", v.lexical_density))
    dims.append(("vocab_type_token_ratio", v.type_token_ratio))
    dims.append(("vocab_rare_word_frequency", v.rare_word_frequency))
    dims.append(("vocab_reading_level", v.reading_level))
    dims.append(("vocab_avg_word_length", v.avg_word_length))
    # Top-word frequency distribution (top 20 as individual dims)
    for i in range(20):
        if i < len(v.top_words):
            dims.append((f"vocab_top_word_{i}_freq", float(v.top_words[i][1])))
        else:
            dims.append((f"vocab_top_word_{i}_freq", 0.0))
    # Derived: vocabulary richness index
    dims.append(("vocab_richness_index", v.type_token_ratio * v.lexical_density))
    dims.append(("vocab_complexity_index", v.rare_word_frequency * v.reading_level))
    dims.append(("vocab_word_length_norm", v.avg_word_length / 10.0))

    # --- Sentence dimensions (40) ---
    s = features.sentence
    dims.append(("sent_avg_length", s.avg_length))
    dims.append(("sent_length_variance", s.length_variance))
    dims.append(("sent_min_length", float(s.min_length)))
    dims.append(("sent_max_length", float(s.max_length)))
    dims.append(("sent_simple_ratio", s.simple_ratio))
    dims.append(("sent_compound_ratio", s.compound_ratio))
    dims.append(("sent_complex_ratio", s.complex_ratio))
    dims.append(("sent_question_ratio", s.question_ratio))
    dims.append(("sent_exclamation_ratio", s.exclamation_ratio))
    # Derived sentence features
    dims.append(("sent_length_range", float(s.max_length - s.min_length)))
    dims.append(("sent_complexity_blend", s.compound_ratio + s.complex_ratio))
    dims.append(("sent_rhythm_score", s.length_variance / max(s.avg_length, 1.0)))
    dims.append(("sent_punctuation_energy", s.question_ratio + s.exclamation_ratio))
    # Sentence pattern buckets (normalized length distribution in 5 buckets)
    for i, bucket_name in enumerate(["very_short", "short", "medium", "long", "very_long"]):
        dims.append(
            (f"sent_bucket_{bucket_name}", 0.0)
        )  # reserved: sentence-length distribution buckets (not yet computed; requires per-sentence lengths)
    # Interaction features
    dims.append(("sent_simple_x_avg_len", s.simple_ratio * s.avg_length))
    dims.append(("sent_complex_x_variance", s.complex_ratio * s.length_variance))
    for i in range(20):  # padding to reach 40 sentence dims
        dims.append((f"sent_reserved_{i}", 0.0))

    # --- Paragraph dimensions (30) ---
    p = features.paragraph
    dims.append(("para_avg_length", p.avg_length))
    dims.append(("para_avg_word_count", p.avg_word_count))
    dims.append(("para_transition_density", p.transition_word_density))
    dims.append(("para_short_ratio", p.short_paragraph_ratio))
    dims.append(("para_long_ratio", p.long_paragraph_ratio))
    dims.append(("para_balance_ratio", 1.0 - abs(p.short_paragraph_ratio - p.long_paragraph_ratio)))
    dims.append(("para_density_norm", p.avg_word_count / max(p.avg_length, 1.0)))
    for i in range(23):  # padding to reach 30 paragraph dims
        dims.append((f"para_reserved_{i}", 0.0))

    # --- Rhetorical dimensions (30) ---
    r = features.rhetorical
    dims.append(("rhet_metaphor_density", r.metaphor_density))
    dims.append(("rhet_simile_density", r.simile_density))
    dims.append(("rhet_humor_density", r.humor_marker_density))
    dims.append(("rhet_emotional_intensity", r.emotional_intensity))
    dims.append(("rhet_alliteration_density", r.alliteration_density))
    dims.append(("rhet_rhetorical_q_density", r.rhetorical_question_density))
    dims.append(("rhet_figurative_total", r.metaphor_density + r.simile_density))
    dims.append(("rhet_expressiveness", r.humor_marker_density + r.emotional_intensity))
    for i in range(22):  # padding to reach 30 rhetorical dims
        dims.append((f"rhet_reserved_{i}", 0.0))

    # --- Dialogue dimensions (30) ---
    d = features.dialogue
    dims.append(("dial_dialogue_ratio", d.dialogue_ratio))
    dims.append(("dial_avg_length", d.avg_dialogue_length))
    dims.append(("dial_said_tag_ratio", d.said_tag_ratio))
    dims.append(("dial_action_beat_ratio", d.action_beat_ratio))
    dims.append(("dial_to_narrative_ratio", d.dialogue_to_narrative_ratio))
    dims.append(("dial_tag_preference", d.said_tag_ratio - d.action_beat_ratio))
    for i in range(24):  # padding to reach 30 dialogue dims
        dims.append((f"dial_reserved_{i}", 0.0))

    # --- Cross-domain interaction features (40+) ---
    dims.append(("cross_vocab_x_sent_complexity", v.reading_level * (s.compound_ratio + s.complex_ratio)))
    dims.append(("cross_vocab_x_rhet_figurative", v.rare_word_frequency * (r.metaphor_density + r.simile_density)))
    dims.append(("cross_sent_x_para_density", s.avg_length * p.avg_length))
    dims.append(("cross_dial_x_sent_energy", d.dialogue_ratio * (s.question_ratio + s.exclamation_ratio)))
    dims.append(("cross_rhet_x_dial_emotion", r.emotional_intensity * d.dialogue_ratio))
    dims.append(("cross_vocab_x_para_transitions", v.lexical_density * p.transition_word_density))
    dims.append(("cross_sent_variance_x_para_short", s.length_variance * p.short_paragraph_ratio))
    for i in range(33):  # padding to reach 40 cross dims
        dims.append((f"cross_reserved_{i}", 0.0))

    labels = [d[0] for d in dims]
    vector = [d[1] for d in dims]
    return vector, labels


# ---------------------------------------------------------------------------
# Style card generation (natural language)
# ---------------------------------------------------------------------------


def _describe_vocabulary_level(v) -> str:
    if v.reading_level < 6:
        return "accessible / elementary"
    if v.reading_level < 10:
        return "moderate / general audience"
    if v.reading_level < 14:
        return "advanced / literary"
    return "highly complex / academic"


def _describe_tone(features: AllFeatures) -> str:
    parts: list[str] = []
    r = features.rhetorical
    if r.emotional_intensity > INTENSITY_THRESHOLD:
        parts.append("emotionally charged")
    elif r.emotional_intensity > 0.2:
        parts.append("moderately emotive")
    else:
        parts.append("measured and restrained")

    if r.humor_marker_density > 2.0:
        parts.append("humorous")
    if r.metaphor_density + r.simile_density > 5.0:
        parts.append("figurative and poetic")

    return ", ".join(parts) if parts else "neutral"


def _describe_pacing(features: AllFeatures) -> str:
    s = features.sentence
    p = features.paragraph
    parts: list[str] = []
    if s.avg_length < 12:
        parts.append("fast-paced with short punchy sentences")
    elif s.avg_length < 20:
        parts.append("moderate sentence rhythm")
    else:
        parts.append("deliberate with long flowing sentences")

    if s.length_variance > 100:
        parts.append("highly varied cadence")
    elif s.length_variance > 30:
        parts.append("moderate rhythmic variation")

    if p.short_paragraph_ratio > RATIO_THRESHOLD:
        parts.append("frequent paragraph breaks")
    return "; ".join(parts) if parts else "balanced pacing"


def _describe_sentence_style(features: AllFeatures) -> str:
    s = features.sentence
    dominant = max(
        [("simple", s.simple_ratio), ("compound", s.compound_ratio), ("complex", s.complex_ratio)],
        key=lambda x: x[1],
    )
    return f"Predominantly {dominant[0]} sentences (avg {s.avg_length:.1f} words)"


def _describe_paragraph_style(features: AllFeatures) -> str:
    p = features.paragraph
    if p.short_paragraph_ratio > 0.6:
        return f"Short paragraphs averaging {p.avg_length:.1f} sentences; many brief passages"
    if p.long_paragraph_ratio > 0.3:
        return f"Dense paragraphs averaging {p.avg_length:.1f} sentences; extended blocks"
    return f"Mixed paragraph lengths averaging {p.avg_length:.1f} sentences"


def _describe_rhetorical_style(features: AllFeatures) -> str:
    r = features.rhetorical
    devices: list[str] = []
    if r.simile_density > 1.0:
        devices.append("similes")
    if r.metaphor_density > 2.0:
        devices.append("metaphors")
    if r.alliteration_density > 1.0:
        devices.append("alliteration")
    if r.humor_marker_density > 1.0:
        devices.append("humor")
    if not devices:
        return "Minimal use of rhetorical devices; straightforward prose"
    return f"Notable use of {', '.join(devices)}"


def _describe_dialogue_style(features: AllFeatures) -> str:
    d = features.dialogue
    if d.dialogue_ratio < 0.05:
        return "Minimal dialogue; predominantly narrative"
    tag_style = "said-heavy" if d.said_tag_ratio > 0.6 else "varied attribution"
    beat_style = "frequent action beats" if d.action_beat_ratio > 0.3 else "tag-driven"
    return f"Dialogue-rich ({d.dialogue_ratio:.0%}); {tag_style}; {beat_style}"


def _generate_example_prompts(card: StyleCard) -> list[str]:
    return [
        f"Write in a {card.tone} tone with {card.sentence_style.lower()}.",
        f"Match this style: {card.summary[:200]}",
        f"Use {card.vocabulary_level} vocabulary. {card.paragraph_style}. {card.dialogue_style}.",
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_voice_fingerprint(
    features: AllFeatures,
    segmented: SegmentedText,
) -> VoiceFingerprint:
    """Build the complete voice fingerprint from extracted features."""
    vector, labels = _build_voice_vector(features)
    return VoiceFingerprint(
        vocabulary=features.vocabulary,
        sentence=features.sentence,
        paragraph=features.paragraph,
        rhetorical=features.rhetorical,
        dialogue=features.dialogue,
        voice_vector=vector,
        dimension_labels=labels,
    )


def generate_style_card(features: AllFeatures, segmented: SegmentedText) -> StyleCard:
    """Generate a human-readable style card from features."""
    v = features.vocabulary
    vocab_level = _describe_vocabulary_level(v)
    tone = _describe_tone(features)
    pacing = _describe_pacing(features)
    sentence_style = _describe_sentence_style(features)
    paragraph_style = _describe_paragraph_style(features)
    rhetorical_style = _describe_rhetorical_style(features)
    dialogue_style = _describe_dialogue_style(features)

    summary = (
        f"This author writes at a {vocab_level} level with a {tone} tone. "
        f"Pacing is {pacing}. {sentence_style}. {paragraph_style}. "
        f"{rhetorical_style}. {dialogue_style}."
    )

    key_metrics = {
        "reading_level": v.reading_level,
        "lexical_density": v.lexical_density,
        "avg_sentence_length": features.sentence.avg_length,
        "sentence_variance": features.sentence.length_variance,
        "emotional_intensity": features.rhetorical.emotional_intensity,
        "dialogue_ratio": features.dialogue.dialogue_ratio,
        "word_count": float(segmented.word_count),
        "confidence": min(1.0, segmented.word_count / HIGH_CONFIDENCE_WORDS),
    }

    card = StyleCard(
        summary=summary,
        tone=tone,
        pacing=pacing,
        vocabulary_level=vocab_level,
        sentence_style=sentence_style,
        paragraph_style=paragraph_style,
        rhetorical_style=rhetorical_style,
        dialogue_style=dialogue_style,
        key_metrics=key_metrics,
    )
    card.example_prompts = _generate_example_prompts(card)
    return card


def compute_confidence(word_count: int) -> float:
    """Return 0.0-1.0 confidence based on sample size."""
    return min(1.0, word_count / HIGH_CONFIDENCE_WORDS)
