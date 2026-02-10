"""
Quality Assurance Module

Post-generation quality checks including readability scoring,
plagiarism detection (placeholder), and hallucination detection (placeholder).
Supports progressive enhancement: if Haiku output quality is below threshold
the orchestrator can re-route to Sonnet.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Discrete quality rating."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class QualityReport:
    """Aggregated quality assessment of an LLM response."""

    overall_level: QualityLevel = QualityLevel.GOOD
    overall_score: float = 0.0  # 0-100

    readability_score: float = 0.0
    readability_grade_level: float = 0.0
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0

    plagiarism_flag: bool = False
    plagiarism_confidence: float = 0.0

    hallucination_flag: bool = False
    hallucination_confidence: float = 0.0

    issues: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def passes_threshold(self) -> bool:
        """True if quality is at least acceptable (score >= 40)."""
        return self.overall_score >= 40.0


# Default thresholds for progressive enhancement
QUALITY_THRESHOLDS = {
    QualityLevel.EXCELLENT: 80.0,
    QualityLevel.GOOD: 60.0,
    QualityLevel.ACCEPTABLE: 40.0,
    QualityLevel.POOR: 20.0,
    QualityLevel.FAILED: 0.0,
}

# Minimum quality score to accept without escalation
PROGRESSIVE_ENHANCEMENT_THRESHOLD = 40.0


class QualityAssurance:
    """Runs post-generation quality checks."""

    def __init__(
        self,
        enhancement_threshold: float = PROGRESSIVE_ENHANCEMENT_THRESHOLD,
    ) -> None:
        self._threshold = enhancement_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(
        self,
        content: str,
        task_type: Optional[str] = None,
    ) -> QualityReport:
        """Run all quality checks and return a unified report."""
        if not content or not content.strip():
            return QualityReport(
                overall_level=QualityLevel.FAILED,
                overall_score=0.0,
                issues=["Empty response content"],
            )

        report = QualityReport()

        # Readability
        self._assess_readability(content, report)

        # Plagiarism (placeholder)
        self._assess_plagiarism(content, report)

        # Hallucination (placeholder)
        self._assess_hallucination(content, report)

        # Compute overall score
        report.overall_score = self._compute_overall_score(report)
        report.overall_level = self._score_to_level(report.overall_score)

        logger.debug(
            "Quality assessment: score=%.1f level=%s issues=%s",
            report.overall_score,
            report.overall_level.value,
            report.issues,
        )
        return report

    def needs_enhancement(self, report: QualityReport) -> bool:
        """Return True if the response quality is below threshold and
        should be re-generated with a more capable model."""
        return report.overall_score < self._threshold

    # ------------------------------------------------------------------
    # Readability
    # ------------------------------------------------------------------

    def _assess_readability(self, content: str, report: QualityReport) -> None:
        """Compute basic readability metrics using Flesch-Kincaid."""
        words = self._tokenize_words(content)
        sentences = self._split_sentences(content)
        syllables = sum(self._count_syllables(w) for w in words)

        report.word_count = len(words)
        report.sentence_count = len(sentences)
        report.avg_sentence_length = (
            len(words) / len(sentences) if sentences else 0.0
        )

        # Flesch Reading Ease (0-100, higher = easier)
        if words and sentences:
            asl = len(words) / len(sentences)
            asw = syllables / len(words) if words else 0
            flesch = 206.835 - (1.015 * asl) - (84.6 * asw)
            report.readability_score = max(0.0, min(100.0, flesch))

            # Flesch-Kincaid Grade Level
            fk_grade = (0.39 * asl) + (11.8 * asw) - 15.59
            report.readability_grade_level = max(0.0, fk_grade)
        else:
            report.readability_score = 0.0
            report.readability_grade_level = 0.0

        # Flag potential issues
        if report.word_count < 10:
            report.issues.append("Response is very short (< 10 words)")
        if report.avg_sentence_length > 40:
            report.issues.append("Average sentence length is very high (> 40 words)")

    # ------------------------------------------------------------------
    # Plagiarism detection (placeholder)
    # ------------------------------------------------------------------

    def _assess_plagiarism(self, content: str, report: QualityReport) -> None:
        """Placeholder: In production, compare against corpus or use API."""
        # Placeholder — always returns clean
        report.plagiarism_flag = False
        report.plagiarism_confidence = 0.0

    # ------------------------------------------------------------------
    # Hallucination detection (placeholder)
    # ------------------------------------------------------------------

    def _assess_hallucination(self, content: str, report: QualityReport) -> None:
        """Placeholder: In production, cross-reference claims with knowledge base."""
        # Placeholder — always returns clean
        report.hallucination_flag = False
        report.hallucination_confidence = 0.0

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_overall_score(report: QualityReport) -> float:
        """Weighted combination of quality signals."""
        # Readability contributes 60%, plagiarism/hallucination 20% each
        readability_component = report.readability_score * 0.60

        # Plagiarism: 100 = clean, 0 = confirmed plagiarism
        plagiarism_component = (
            (1.0 - report.plagiarism_confidence) * 100.0
        ) * 0.20

        # Hallucination: 100 = clean, 0 = confirmed hallucination
        hallucination_component = (
            (1.0 - report.hallucination_confidence) * 100.0
        ) * 0.20

        total = readability_component + plagiarism_component + hallucination_component

        # Penalize for issues
        penalty = len(report.issues) * 5.0
        return max(0.0, min(100.0, total - penalty))

    @staticmethod
    def _score_to_level(score: float) -> QualityLevel:
        """Convert numeric score to discrete quality level."""
        if score >= 80.0:
            return QualityLevel.EXCELLENT
        if score >= 60.0:
            return QualityLevel.GOOD
        if score >= 40.0:
            return QualityLevel.ACCEPTABLE
        if score >= 20.0:
            return QualityLevel.POOR
        return QualityLevel.FAILED

    # ------------------------------------------------------------------
    # Text analysis utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize_words(text: str) -> list[str]:
        """Split text into word tokens."""
        return re.findall(r"[a-zA-Z']+", text)

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Approximate syllable count for English words."""
        word = word.lower().rstrip("e")
        vowels = re.findall(r'[aeiouy]+', word)
        count = len(vowels)
        return max(1, count)
