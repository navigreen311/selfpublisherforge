"""Vocabulary Analyzer — Analyze vocabulary richness and word usage patterns."""

from __future__ import annotations

import re
from collections import Counter
from typing import TypedDict


class VocabularyRichnessMetrics(TypedDict):
    """Vocabulary richness analysis results."""
    type_token_ratio: float
    hapax_legomena_ratio: float
    avg_word_length: float
    vocabulary_level_score: float
    domain_terminology_density: float
    total_words: int
    unique_words: int
    hapax_count: int


# Common stop words (top ~300)
_STOP_WORDS = frozenset((
    "the be to of and a in that have i it for not on with he as you do at "
    "this but his by from they we say her she or an will my one all would "
    "there their what so up out if about who get which go me when make can "
    "like time no just him know take people into year your good some could "
    "them see other than then now look only come its over think also back "
    "after use two how our work first well way even new want because any "
    "these give day most us is was are been has had were did does doing "
    "am being have has having do does doing shall should would may might "
    "must need dare ought used will can could very said each tell three "
    "still find long down day made part"
).split())

# Common/frequent words (simplified top 5000 proxy - using word length heuristic)
# Words 1-4 chars long are considered common, 5-7 intermediate, 8+ advanced
_COMMON_WORD_LENGTH_THRESHOLD = 4
_INTERMEDIATE_WORD_LENGTH = 7


class VocabularyAnalyzer:
    """Analyzes vocabulary richness and complexity."""

    @staticmethod
    def _is_domain_term(word: str) -> bool:
        """Heuristic to identify potential domain-specific terminology.

        Domain terms are typically:
        - Longer than 8 characters
        - Not common stop words
        - May contain technical patterns (capitalized, hyphenated, etc.)
        """
        if word.lower() in _STOP_WORDS:
            return False

        # Long words are more likely to be domain-specific
        if len(word) >= 10:
            return True

        # Capitalized words in middle of text (proper nouns, technical terms)
        if word[0].isupper() and len(word) > 5:
            return True

        # Hyphenated technical terms
        if '-' in word and len(word) > 6:
            return True

        return False

    def analyze(self, text: str) -> VocabularyRichnessMetrics:
        """Analyze vocabulary richness in the given text.

        Args:
            text: The text to analyze

        Returns:
            VocabularyRichnessMetrics containing vocabulary analysis
        """
        # Extract words (preserve case for proper noun detection)
        words = re.findall(r"[a-zA-Z']+(?:-[a-zA-Z']+)*", text)

        if not words:
            return VocabularyRichnessMetrics(
                type_token_ratio=0.0,
                hapax_legomena_ratio=0.0,
                avg_word_length=0.0,
                vocabulary_level_score=0.0,
                domain_terminology_density=0.0,
                total_words=0,
                unique_words=0,
                hapax_count=0,
            )

        total_words = len(words)
        words_lower = [w.lower() for w in words]

        # Count word frequencies
        word_counts = Counter(words_lower)
        unique_words = len(word_counts)

        # Type-Token Ratio (TTR)
        type_token_ratio = unique_words / total_words

        # Hapax Legomena (words appearing exactly once)
        hapax_count = sum(1 for count in word_counts.values() if count == 1)
        hapax_ratio = hapax_count / total_words

        # Average word length
        avg_word_length = sum(len(w) for w in words_lower) / total_words

        # Vocabulary level score (based on word length distribution)
        # 0.0 = very simple (short words), 1.0 = advanced (long words)
        length_counts = Counter(len(w) for w in words_lower)
        common_count = sum(
            count for length, count in length_counts.items()
            if length <= _COMMON_WORD_LENGTH_THRESHOLD
        )
        advanced_count = sum(
            count for length, count in length_counts.items()
            if length > _INTERMEDIATE_WORD_LENGTH
        )

        # Normalize to 0-1 scale
        vocab_level_score = min(1.0, advanced_count / max(total_words, 1) * 3)

        # Domain terminology density
        domain_terms = [w for w in words if self._is_domain_term(w)]
        domain_density = len(domain_terms) / total_words

        return VocabularyRichnessMetrics(
            type_token_ratio=type_token_ratio,
            hapax_legomena_ratio=hapax_ratio,
            avg_word_length=avg_word_length,
            vocabulary_level_score=vocab_level_score,
            domain_terminology_density=domain_density,
            total_words=total_words,
            unique_words=unique_words,
            hapax_count=hapax_count,
        )
