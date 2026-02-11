"""Tone Analyzer — Analyze formality and tone characteristics."""

from __future__ import annotations

import re
from typing import TypedDict


class ToneMetrics(TypedDict):
    """Tone analysis results."""
    formality_score: float
    emotional_valence: float
    contraction_usage_rate: float
    first_person_ratio: float
    second_person_ratio: float
    third_person_ratio: float
    hedging_language_frequency: float


# Contraction patterns
_CONTRACTIONS = re.compile(
    r"\b(?:can't|won't|don't|doesn't|didn't|isn't|aren't|wasn't|weren't|"
    r"haven't|hasn't|hadn't|wouldn't|shouldn't|couldn't|mightn't|mustn't|"
    r"I'm|I've|I'll|I'd|you're|you've|you'll|you'd|he's|he'll|he'd|"
    r"she's|she'll|she'd|it's|it'll|we're|we've|we'll|we'd|they're|"
    r"they've|they'll|they'd|that's|there's|who's|what's|where's|"
    r"when's|why's|how's)\b",
    re.IGNORECASE,
)

# Person pronouns
_FIRST_PERSON = re.compile(
    r"\b(?:I|me|my|mine|myself|we|us|our|ours|ourselves)\b",
    re.IGNORECASE,
)
_SECOND_PERSON = re.compile(
    r"\b(?:you|your|yours|yourself|yourselves)\b",
    re.IGNORECASE,
)
_THIRD_PERSON = re.compile(
    r"\b(?:he|him|his|himself|she|her|hers|herself|it|its|itself|"
    r"they|them|their|theirs|themselves)\b",
    re.IGNORECASE,
)

# Hedging language (uncertainty markers)
_HEDGING = re.compile(
    r"\b(?:maybe|perhaps|possibly|probably|might|may|could|seems?|"
    r"appear|likely|unlikely|somewhat|relatively|fairly|rather|"
    r"kind of|sort of|tend to|generally|usually|often|sometimes|"
    r"occasionally|presumably|apparently|evidently|allegedly|"
    r"supposedly|arguably|in my opinion|I think|I believe|I feel|"
    r"suggest|indicate|imply)\b",
    re.IGNORECASE,
)

# Emotional valence indicators
_POSITIVE_WORDS = frozenset((
    "love happy joy wonderful great excellent amazing fantastic beautiful "
    "brilliant delightful pleased excited thrilled ecstatic glad cheerful "
    "pleasant satisfied content grateful blessed fortunate lucky successful "
    "perfect marvelous magnificent superb splendid terrific awesome fabulous "
    "good better best nice fine well"
).split())

_NEGATIVE_WORDS = frozenset((
    "hate sad anger fear terrible awful horrible dreadful bad worse worst "
    "poor terrible miserable unhappy depressed disappointed frustrated "
    "angry furious upset annoyed irritated disturbed worried anxious "
    "concerned troubled distressed painful hurt suffering difficult hard "
    "wrong failed failure problem issue mistake error"
).split())

# Formal vs informal indicators
_FORMAL_INDICATORS = re.compile(
    r"\b(?:furthermore|moreover|nevertheless|nonetheless|consequently|"
    r"therefore|thus|hence|accordingly|subsequently|henceforth|heretofore|"
    r"notwithstanding|whilst|upon|amongst|regarding|concerning|pertaining)\b",
    re.IGNORECASE,
)

_INFORMAL_INDICATORS = re.compile(
    r"\b(?:yeah|yep|nope|gonna|wanna|gotta|kinda|sorta|ok|okay|cool|"
    r"stuff|things|lots|tons|super|really|pretty|very|so|just|like)\b",
    re.IGNORECASE,
)


class ToneAnalyzer:
    """Analyzes tone and formality characteristics."""

    def analyze(self, text: str) -> ToneMetrics:
        """Analyze tone and formality in the given text.

        Args:
            text: The text to analyze

        Returns:
            ToneMetrics containing tone analysis
        """
        if not text.strip():
            return ToneMetrics(
                formality_score=0.5,
                emotional_valence=0.0,
                contraction_usage_rate=0.0,
                first_person_ratio=0.0,
                second_person_ratio=0.0,
                third_person_ratio=0.0,
                hedging_language_frequency=0.0,
            )

        words = re.findall(r"[a-zA-Z']+", text)
        total_words = len(words)

        if total_words == 0:
            return ToneMetrics(
                formality_score=0.5,
                emotional_valence=0.0,
                contraction_usage_rate=0.0,
                first_person_ratio=0.0,
                second_person_ratio=0.0,
                third_person_ratio=0.0,
                hedging_language_frequency=0.0,
            )

        # Contraction usage (informal indicator)
        contraction_count = len(_CONTRACTIONS.findall(text))
        contraction_rate = contraction_count / total_words

        # Person ratios
        first_person_count = len(_FIRST_PERSON.findall(text))
        second_person_count = len(_SECOND_PERSON.findall(text))
        third_person_count = len(_THIRD_PERSON.findall(text))

        first_person_ratio = first_person_count / total_words
        second_person_ratio = second_person_count / total_words
        third_person_ratio = third_person_count / total_words

        # Hedging language
        hedging_count = len(_HEDGING.findall(text))
        hedging_frequency = hedging_count / total_words

        # Formality score (0.0 = informal, 1.0 = formal)
        formal_count = len(_FORMAL_INDICATORS.findall(text))
        informal_count = len(_INFORMAL_INDICATORS.findall(text))

        # Calculate formality based on multiple factors
        formality_signals = 0.0

        # Formal indicators add to formality
        formality_signals += formal_count / max(total_words, 1) * 100

        # Informal indicators and contractions reduce formality
        formality_signals -= informal_count / max(total_words, 1) * 100
        formality_signals -= contraction_rate * 50

        # Third person is more formal, first/second person less formal
        formality_signals += third_person_ratio * 20
        formality_signals -= (first_person_ratio + second_person_ratio) * 10

        # Normalize to 0-1 range (sigmoid-like)
        formality_score = max(0.0, min(1.0, 0.5 + formality_signals / 20))

        # Emotional valence (-1.0 = negative, 0.0 = neutral, 1.0 = positive)
        words_lower = [w.lower() for w in words]
        positive_count = sum(1 for w in words_lower if w in _POSITIVE_WORDS)
        negative_count = sum(1 for w in words_lower if w in _NEGATIVE_WORDS)

        emotional_count = positive_count + negative_count
        if emotional_count > 0:
            emotional_valence = (positive_count - negative_count) / emotional_count
        else:
            emotional_valence = 0.0

        return ToneMetrics(
            formality_score=formality_score,
            emotional_valence=emotional_valence,
            contraction_usage_rate=contraction_rate,
            first_person_ratio=first_person_ratio,
            second_person_ratio=second_person_ratio,
            third_person_ratio=third_person_ratio,
            hedging_language_frequency=hedging_frequency,
        )
