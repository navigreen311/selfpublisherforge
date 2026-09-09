"""Linguistic Feature Extraction — vocabulary, sentence patterns, paragraph
patterns, rhetorical devices, and dialogue analysis."""

from __future__ import annotations

import json
import logging
import re
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from app.modules.style_cloning.ingestion import SegmentedText
from app.modules.style_cloning.schemas import (
    DialogueMetrics,
    ParagraphMetrics,
    RhetoricalMetrics,
    SentenceMetrics,
    VocabularyMetrics,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load feature word lists from config (with hardcoded fallbacks)
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent / "feature_words.json"

_DEFAULT_STOP_WORDS = (
    "the be to of and a in that have i it for not on with he as you do at "
    "this but his by from they we say her she or an will my one all would "
    "there their what so up out if about who get which go me when make can "
    "like time no just him know take people into year your good some could "
    "them see other than then now look only come its over think also back "
    "after use two how our work first well way even new want because any "
    "these give day most us is was are been has had were did does doing "
    "am being have has having do does doing shall should would may might "
    "must need dare ought used will can could"
).split()

_DEFAULT_TRANSITION_WORDS = (
    "however moreover furthermore additionally nevertheless nonetheless "
    "therefore consequently meanwhile accordingly alternatively besides "
    "hence likewise otherwise similarly thus indeed finally instead "
    "subsequently certainly specifically particularly especially notably "
    "significantly incidentally admittedly conversely undoubtedly"
).split()

_DEFAULT_EMOTIONAL_WORDS = (
    "love hate fear anger joy sorrow grief ecstasy rage fury terror "
    "passion despair hope agony bliss torment dread euphoria misery "
    "delight horror anguish triumph heartbreak devastation elation "
    "anxious terrified furious overjoyed heartbroken desperate "
    "thrilled horrified enraged ecstatic melancholy"
).split()


def _load_feature_words() -> dict:
    """Load feature word lists from the JSON config file.

    Falls back to hardcoded defaults if the config file is missing or invalid.
    """
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("Loaded feature words from %s", _CONFIG_PATH)
        return cast("dict[Any, Any]", data)
    except FileNotFoundError:
        logger.warning(
            "Feature words config not found at %s; using hardcoded defaults",
            _CONFIG_PATH,
        )
        return {}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "Failed to read feature words config at %s (%s); using hardcoded defaults",
            _CONFIG_PATH,
            exc,
        )
        return {}


_feature_config = _load_feature_words()

# ---------------------------------------------------------------------------
# Common English stop words & top-5000 approximation
# ---------------------------------------------------------------------------

_STOP_WORDS: frozenset[str] = frozenset(_feature_config.get("stop_words", _DEFAULT_STOP_WORDS))

# A simplified set of common English words (top ~5000 proxy) — for rare-word
# detection we flag words NOT in this set.  We use a heuristic: words <= 5
# chars that appear often in the text are considered common.

# Empty by design: feature extraction uses heuristic analysis rather than POS prefix matching
_CONTENT_POS_PREFIXES: frozenset[str] = frozenset()


def _is_content_word(word: str) -> bool:
    return word.lower() not in _STOP_WORDS and len(word) > 1


# ---------------------------------------------------------------------------
# Transition / signal words
# ---------------------------------------------------------------------------

_TRANSITION_WORDS: frozenset[str] = frozenset(_feature_config.get("transition_words", _DEFAULT_TRANSITION_WORDS))

# ---------------------------------------------------------------------------
# Rhetorical device patterns
# ---------------------------------------------------------------------------

_SIMILE_RE = re.compile(r"\b(?:like|as)\s+(?:a|an|the)\s+\w+", re.IGNORECASE)
_METAPHOR_INDICATORS = re.compile(
    r"\b(?:is|was|are|were)\s+(?:a|an|the)\s+\w+",
    re.IGNORECASE,
)
_HUMOR_MARKERS = re.compile(
    r"(?:lol|haha|heh|\;[\-\)]|😂|ironic(?:ally)?|joke[ds]?|laugh(?:ed|ing)?|funny|hilarious)",
    re.IGNORECASE,
)
_ALLITERATION_RE = re.compile(r"\b([a-z])\w+\s+\1\w+(?:\s+\1\w+)?", re.IGNORECASE)
_EMOTIONAL_WORDS: frozenset[str] = frozenset(_feature_config.get("emotional_words", _DEFAULT_EMOTIONAL_WORDS))

# ---------------------------------------------------------------------------
# Dialogue detection
# ---------------------------------------------------------------------------

_DIALOGUE_RE = re.compile(
    r'[\u201C"]([^"\u201D]*?)[\u201D"]',
    re.DOTALL,
)
_SAID_TAGS = re.compile(
    r'[\u201D"]\s*(?:,\s*)?(?:he|she|they|I|we|\w+)\s+said\b',
    re.IGNORECASE,
)
_SPEECH_TAGS = re.compile(
    r'[\u201D"]\s*(?:,\s*)?(?:he|she|they|I|we|\w+)\s+'
    r"(?:said|asked|replied|whispered|shouted|exclaimed|muttered|murmured|"
    r"cried|yelled|stammered|sighed|gasped|snapped|growled|hissed|"
    r"bellowed|pleaded|demanded|called|screamed|answered|remarked)\b",
    re.IGNORECASE,
)
_ACTION_BEAT_RE = re.compile(
    r'[\u201D"]\s*[.!?]?\s*[A-Z][a-z]+\s+(?:\w+\s+){0,3}'
    r"(?:turned|walked|looked|nodded|shook|smiled|frowned|crossed|"
    r"leaned|sat|stood|stepped|moved|placed|picked|set|put|took|ran|"
    r"grabbed|reached|pulled|pushed|pointed|waved)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Clause counting (for sentence complexity)
# ---------------------------------------------------------------------------

_CLAUSE_MARKERS = re.compile(
    r"\b(?:and|but|or|nor|yet|so|because|although|though|while|when|"
    r"where|if|unless|until|after|before|since|that|which|who|whom|"
    r"whose|whenever|wherever|whether)\b",
    re.IGNORECASE,
)


def _count_clauses(sentence: str) -> int:
    markers = len(_CLAUSE_MARKERS.findall(sentence))
    return max(1, markers + 1)


def _classify_sentence(sentence: str) -> str:
    clauses = _count_clauses(sentence)
    subordinators = re.findall(
        r"\b(?:because|although|though|while|when|where|if|unless|until|"
        r"after|before|since|that|which|who|whom|whose|whenever|wherever|"
        r"whether)\b",
        sentence,
        re.IGNORECASE,
    )
    if clauses == 1:
        return "simple"
    if subordinators:
        return "complex"
    return "compound"


# ---------------------------------------------------------------------------
# Flesch-Kincaid helpers
# ---------------------------------------------------------------------------

_VOWELS = frozenset("aeiouy")


def _count_syllables(word: str) -> int:
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
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _flesch_kincaid_grade(total_words: int, total_sentences: int, total_syllables: int) -> float:
    if total_sentences == 0 or total_words == 0:
        return 0.0
    return 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59


# ---------------------------------------------------------------------------
# Public extraction functions
# ---------------------------------------------------------------------------


def extract_vocabulary(segmented: SegmentedText) -> VocabularyMetrics:
    """Analyze vocabulary characteristics of the text."""
    words = re.findall(r"[a-zA-Z']+", segmented.raw_text.lower())
    if not words:
        return VocabularyMetrics()  # type: ignore[call-arg]

    total = len(words)
    unique = set(words)
    content_words = [w for w in words if _is_content_word(w)]
    content_total = len(content_words)

    word_counts = Counter(words)
    # Rare words: longer than 7 chars and appear fewer than 3 times
    # In a production system we'd use a frequency corpus
    common_threshold = max(3, total // 5000)
    rare_count = sum(1 for w in words if len(w) > 7 and word_counts[w] <= common_threshold)

    total_syllables = sum(_count_syllables(w) for w in words)

    # Top content words
    content_counter = Counter(content_words)
    top_words = content_counter.most_common(30)

    avg_word_len = sum(len(w) for w in words) / total if total else 0.0

    return VocabularyMetrics(
        unique_word_count=len(unique),
        total_word_count=total,
        lexical_density=content_total / total if total else 0.0,
        type_token_ratio=len(unique) / total if total else 0.0,
        rare_word_frequency=rare_count / total if total else 0.0,
        reading_level=_flesch_kincaid_grade(total, max(len(segmented.sentences), 1), total_syllables),
        avg_word_length=avg_word_len,
        top_words=top_words,
    )


def extract_sentence_metrics(segmented: SegmentedText) -> SentenceMetrics:
    """Analyze sentence-level characteristics."""
    sentences = segmented.sentences
    if not sentences:
        return SentenceMetrics()  # type: ignore[call-arg]

    lengths = [len(s.split()) for s in sentences]
    classifications = [_classify_sentence(s) for s in sentences]

    total = len(sentences)
    simple_count = classifications.count("simple")
    compound_count = classifications.count("compound")
    complex_count = classifications.count("complex")
    question_count = sum(1 for s in sentences if s.rstrip().endswith("?"))
    exclamation_count = sum(1 for s in sentences if s.rstrip().endswith("!"))

    return SentenceMetrics(
        avg_length=statistics.mean(lengths) if lengths else 0.0,
        length_variance=statistics.variance(lengths) if len(lengths) > 1 else 0.0,
        min_length=min(lengths) if lengths else 0,
        max_length=max(lengths) if lengths else 0,
        simple_ratio=simple_count / total,
        compound_ratio=compound_count / total,
        complex_ratio=complex_count / total,
        question_ratio=question_count / total,
        exclamation_ratio=exclamation_count / total,
    )


def extract_paragraph_metrics(segmented: SegmentedText) -> ParagraphMetrics:
    """Analyze paragraph-level characteristics."""
    paragraphs = segmented.paragraphs
    if not paragraphs:
        return ParagraphMetrics()  # type: ignore[call-arg]

    para_sentence_counts: list[int] = []
    para_word_counts: list[int] = []
    transition_counts: list[int] = []

    for para in paragraphs:
        from app.modules.style_cloning.ingestion import _split_sentences

        sents = _split_sentences(para)
        para_sentence_counts.append(len(sents))
        para_word_counts.append(len(para.split()))
        words_lower = para.lower().split()
        t_count = sum(1 for w in words_lower if w.strip(".,;:") in _TRANSITION_WORDS)
        transition_counts.append(t_count)

    total = len(paragraphs)
    short = sum(1 for c in para_sentence_counts if c <= 2)
    long_ = sum(1 for c in para_sentence_counts if c >= 8)

    return ParagraphMetrics(
        avg_length=statistics.mean(para_sentence_counts) if para_sentence_counts else 0.0,
        avg_word_count=statistics.mean(para_word_counts) if para_word_counts else 0.0,
        transition_word_density=(statistics.mean(transition_counts) if transition_counts else 0.0),
        short_paragraph_ratio=short / total if total else 0.0,
        long_paragraph_ratio=long_ / total if total else 0.0,
    )


def extract_rhetorical_metrics(segmented: SegmentedText) -> RhetoricalMetrics:
    """Detect rhetorical devices in the text."""
    text = segmented.raw_text
    word_count = segmented.word_count
    if word_count == 0:
        return RhetoricalMetrics()  # type: ignore[call-arg]

    per_1000 = 1000 / word_count

    simile_count = len(_SIMILE_RE.findall(text))
    metaphor_count = len(_METAPHOR_INDICATORS.findall(text))
    humor_count = len(_HUMOR_MARKERS.findall(text))
    alliteration_count = len(_ALLITERATION_RE.findall(text))

    # Emotional intensity: fraction of words that are emotional
    words = re.findall(r"[a-zA-Z']+", text.lower())
    emotional_count = sum(1 for w in words if w in _EMOTIONAL_WORDS)
    emotional_intensity = min(1.0, emotional_count / max(len(words), 1) * 20)

    # Rhetorical questions
    sentences = segmented.sentences
    rhetorical_q = sum(
        1
        for s in sentences
        if s.rstrip().endswith("?")
        and not s.lstrip().startswith(
            (
                "Who ",
                "What ",
                "Where ",
                "When ",
                "How ",
                "Why ",
                "Did ",
                "Do ",
                "Does ",
                "Is ",
                "Are ",
                "Was ",
                "Were ",
                "Can ",
                "Could ",
                "Will ",
                "Would ",
                "Should ",
            )
        )
    )

    return RhetoricalMetrics(
        metaphor_density=metaphor_count * per_1000,
        simile_density=simile_count * per_1000,
        humor_marker_density=humor_count * per_1000,
        emotional_intensity=emotional_intensity,
        alliteration_density=alliteration_count * per_1000,
        rhetorical_question_density=rhetorical_q * per_1000,
    )


def extract_dialogue_metrics(segmented: SegmentedText) -> DialogueMetrics:
    """Analyze dialogue patterns in the text (primarily for fiction)."""
    text = segmented.raw_text
    word_count = segmented.word_count
    if word_count == 0:
        return DialogueMetrics()  # type: ignore[call-arg]

    dialogue_spans = _DIALOGUE_RE.findall(text)
    if not dialogue_spans:
        return DialogueMetrics()  # type: ignore[call-arg]

    dialogue_words = sum(len(span.split()) for span in dialogue_spans)
    narrative_words = word_count - dialogue_words

    said_tags = len(_SAID_TAGS.findall(text))
    all_speech_tags = len(_SPEECH_TAGS.findall(text))
    action_beats = len(_ACTION_BEAT_RE.findall(text))

    total_tags = all_speech_tags + action_beats
    avg_dialogue_length = dialogue_words / len(dialogue_spans) if dialogue_spans else 0.0

    return DialogueMetrics(
        dialogue_ratio=dialogue_words / word_count if word_count else 0.0,
        avg_dialogue_length=avg_dialogue_length,
        said_tag_ratio=said_tags / all_speech_tags if all_speech_tags else 0.0,
        action_beat_ratio=action_beats / total_tags if total_tags else 0.0,
        dialogue_to_narrative_ratio=(dialogue_words / narrative_words if narrative_words else 0.0),
    )


# ---------------------------------------------------------------------------
# Aggregate extractor
# ---------------------------------------------------------------------------


@dataclass
class AllFeatures:
    vocabulary: VocabularyMetrics
    sentence: SentenceMetrics
    paragraph: ParagraphMetrics
    rhetorical: RhetoricalMetrics
    dialogue: DialogueMetrics


def extract_all_features(segmented: SegmentedText) -> AllFeatures:
    """Run the full feature-extraction pipeline."""
    return AllFeatures(
        vocabulary=extract_vocabulary(segmented),
        sentence=extract_sentence_metrics(segmented),
        paragraph=extract_paragraph_metrics(segmented),
        rhetorical=extract_rhetorical_metrics(segmented),
        dialogue=extract_dialogue_metrics(segmented),
    )
