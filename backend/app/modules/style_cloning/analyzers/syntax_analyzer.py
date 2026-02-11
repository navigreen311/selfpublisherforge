"""Syntax Analyzer — Analyze sentence structures using basic NLP."""

from __future__ import annotations

import re
import statistics
from typing import TypedDict


class SyntaxMetrics(TypedDict):
    """Syntax analysis results."""
    avg_sentence_length: float
    sentence_length_std: float
    simple_sentence_ratio: float
    compound_sentence_ratio: float
    complex_sentence_ratio: float
    avg_clause_depth: float
    clause_depth_distribution: dict[int, float]
    passive_voice_ratio: float
    active_voice_ratio: float


# Clause markers for complexity detection
_COORDINATING_CONJUNCTIONS = re.compile(
    r'\b(?:and|but|or|nor|yet|so)\b',
    re.IGNORECASE,
)

_SUBORDINATING_CONJUNCTIONS = re.compile(
    r'\b(?:because|although|though|while|when|where|if|unless|until|'
    r'after|before|since|that|which|who|whom|whose|whenever|wherever|'
    r'whether|as|even though|in order that|provided that|assuming that)\b',
    re.IGNORECASE,
)

# Passive voice detection patterns
_PASSIVE_VOICE = re.compile(
    r'\b(?:am|is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?'
    r'(?:[\w]+ed|[\w]+en|shown|known|written|taken|given|made|done|seen|'
    r'told|found|felt|kept|left|lost|heard|held|met|read|said|brought|'
    r'thought|bought|caught|taught|fought|sought)\b',
    re.IGNORECASE,
)


class SyntaxAnalyzer:
    """Analyzes sentence structures and syntax patterns."""

    @staticmethod
    def _count_clauses(sentence: str) -> int:
        """Count the number of clauses in a sentence."""
        coord_count = len(_COORDINATING_CONJUNCTIONS.findall(sentence))
        sub_count = len(_SUBORDINATING_CONJUNCTIONS.findall(sentence))
        # Base clause + additional clauses from conjunctions
        return 1 + coord_count + sub_count

    @staticmethod
    def _classify_sentence(sentence: str) -> str:
        """Classify sentence as simple, compound, or complex."""
        coord_count = len(_COORDINATING_CONJUNCTIONS.findall(sentence))
        sub_count = len(_SUBORDINATING_CONJUNCTIONS.findall(sentence))

        if coord_count == 0 and sub_count == 0:
            return "simple"
        elif sub_count > 0:
            return "complex"
        else:
            return "compound"

    @staticmethod
    def _is_passive_voice(sentence: str) -> bool:
        """Detect if a sentence uses passive voice."""
        return bool(_PASSIVE_VOICE.search(sentence))

    def analyze(self, text: str) -> SyntaxMetrics:
        """Analyze syntax patterns in the given text.

        Args:
            text: The text to analyze

        Returns:
            SyntaxMetrics containing detailed syntax analysis
        """
        # Split into sentences (simple split for now)
        sentences = [
            s.strip()
            for s in re.split(r'[.!?]+', text)
            if s.strip() and len(s.split()) >= 2
        ]

        if not sentences:
            return SyntaxMetrics(
                avg_sentence_length=0.0,
                sentence_length_std=0.0,
                simple_sentence_ratio=0.0,
                compound_sentence_ratio=0.0,
                complex_sentence_ratio=0.0,
                avg_clause_depth=0.0,
                clause_depth_distribution={},
                passive_voice_ratio=0.0,
                active_voice_ratio=0.0,
            )

        # Calculate sentence lengths
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_length = statistics.mean(sentence_lengths)
        std_length = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0.0

        # Classify sentences
        classifications = [self._classify_sentence(s) for s in sentences]
        total = len(sentences)
        simple_count = classifications.count("simple")
        compound_count = classifications.count("compound")
        complex_count = classifications.count("complex")

        # Clause depth analysis
        clause_counts = [self._count_clauses(s) for s in sentences]
        avg_clause_depth = statistics.mean(clause_counts)

        # Build clause depth distribution
        clause_depth_dist: dict[int, int] = {}
        for count in clause_counts:
            clause_depth_dist[count] = clause_depth_dist.get(count, 0) + 1

        # Normalize distribution to percentages
        clause_depth_distribution = {
            depth: count / total
            for depth, count in clause_depth_dist.items()
        }

        # Passive vs active voice
        passive_count = sum(1 for s in sentences if self._is_passive_voice(s))
        passive_ratio = passive_count / total
        active_ratio = 1.0 - passive_ratio

        return SyntaxMetrics(
            avg_sentence_length=avg_length,
            sentence_length_std=std_length,
            simple_sentence_ratio=simple_count / total,
            compound_sentence_ratio=compound_count / total,
            complex_sentence_ratio=complex_count / total,
            avg_clause_depth=avg_clause_depth,
            clause_depth_distribution=clause_depth_distribution,
            passive_voice_ratio=passive_ratio,
            active_voice_ratio=active_ratio,
        )
