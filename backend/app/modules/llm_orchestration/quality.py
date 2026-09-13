"""
Quality Assurance Module

Post-generation quality checks including readability scoring,
plagiarism detection via text fingerprinting, and hallucination detection
via claim extraction and confidence scoring.
Supports progressive enhancement: if Haiku output quality is below threshold
the orchestrator can re-route to Sonnet.
"""

from __future__ import annotations

import hashlib
import logging
import re
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import cast

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants for plagiarism / hallucination detection
# ---------------------------------------------------------------------------

# Shingling parameters
_SHINGLE_SIZE = 4  # number of words per shingle (4-gram)
_PLAGIARISM_NGRAM_THRESHOLD = 0.30  # 30% 4-gram overlap triggers flag

# MinHash parameters
_NUM_MINHASH_PERM = 128  # number of hash permutations for MinHash
_MINHASH_SIMILARITY_THRESHOLD = 0.40  # Jaccard similarity threshold

# Large Mersenne prime used in MinHash universal hashing
_MERSENNE_PRIME = (1 << 61) - 1
_MAX_HASH = (1 << 32) - 1

# Hallucination detection parameters
_CLAIM_DENSITY_HIGH = 0.6  # ratio of claim-bearing sentences to trigger caution
_UNVERIFIABLE_THRESHOLD = 0.5  # ratio of unverifiable claims to flag


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
        plagiarism_ngram_threshold: float = _PLAGIARISM_NGRAM_THRESHOLD,
        minhash_similarity_threshold: float = _MINHASH_SIMILARITY_THRESHOLD,
    ) -> None:
        self._threshold = enhancement_threshold
        self._plagiarism_ngram_threshold = plagiarism_ngram_threshold
        self._minhash_similarity_threshold = minhash_similarity_threshold

        # Reference corpus: stores MinHash signatures and n-gram sets of
        # previously assessed content for cross-document plagiarism detection.
        self._reference_signatures: list[list[int]] = []
        self._reference_ngram_sets: list[set[tuple[str, ...]]] = []

        # Pre-generate hash function coefficients for MinHash
        self._hash_a, self._hash_b = self._generate_minhash_coefficients(_NUM_MINHASH_PERM)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(
        self,
        content: str,
        task_type: str | None = None,
        context: str | None = None,
    ) -> QualityReport:
        """Run all quality checks and return a unified report.

        Args:
            content: The generated text to evaluate.
            task_type: Optional task category (e.g. ``"summarization"``).
            context: Optional source/prompt context for cross-referencing
                claims during hallucination detection.
        """
        if not content or not content.strip():
            return QualityReport(
                overall_level=QualityLevel.FAILED,
                overall_score=0.0,
                issues=["Empty response content"],
            )

        report = QualityReport()

        # Readability
        self._assess_readability(content, report)

        # Plagiarism detection via shingling + MinHash
        self._assess_plagiarism(content, report)

        # Hallucination detection via claim extraction
        self._assess_hallucination(content, report, context=context)

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
        report.avg_sentence_length = len(words) / len(sentences) if sentences else 0.0

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
    # Plagiarism detection via shingling + MinHash
    # ------------------------------------------------------------------

    def _assess_plagiarism(self, content: str, report: QualityReport) -> None:
        """Detect potential plagiarism using text fingerprinting.

        Approach:
        1. Build a set of word-level n-grams (shingles) from *content*.
        2. Compute a MinHash signature over those shingles.
        3. Compare the signature and raw n-gram overlap against every
           previously seen document stored in the reference corpus.
        4. If either the estimated Jaccard similarity (MinHash) exceeds
           ``_MINHASH_SIMILARITY_THRESHOLD`` **or** the raw n-gram overlap
           exceeds ``_PLAGIARISM_NGRAM_THRESHOLD``, flag the content.

        After assessment the current document is added to the corpus so
        future content can be compared against it.
        """
        words = self._normalize_words(content)

        # Need enough words to form at least one shingle
        if len(words) < _SHINGLE_SIZE:
            report.plagiarism_flag = False
            report.plagiarism_confidence = 0.0
            return

        ngrams = self._build_ngrams(words, _SHINGLE_SIZE)
        signature = self._minhash_signature(ngrams)

        max_ngram_overlap: float = 0.0
        max_minhash_sim: float = 0.0

        for ref_sig, ref_ngrams in zip(self._reference_signatures, self._reference_ngram_sets, strict=False):
            # Raw n-gram overlap (Jaccard on the actual sets)
            if ngrams and ref_ngrams:
                intersection = len(ngrams & ref_ngrams)
                union = len(ngrams | ref_ngrams)
                overlap = intersection / union if union else 0.0
                max_ngram_overlap = max(max_ngram_overlap, overlap)

            # Estimated Jaccard via MinHash
            mh_sim = self._minhash_jaccard(signature, ref_sig)
            max_minhash_sim = max(max_minhash_sim, mh_sim)

        # Determine flag and confidence
        # Use the stronger of the two signals
        combined_score = max(max_ngram_overlap, max_minhash_sim)

        if max_ngram_overlap >= self._plagiarism_ngram_threshold:
            report.plagiarism_flag = True
            report.plagiarism_confidence = min(1.0, combined_score)
            report.issues.append(f"Potential plagiarism detected " f"({max_ngram_overlap:.0%} n-gram overlap)")
            report.metadata["plagiarism_ngram_overlap"] = round(max_ngram_overlap, 4)
            report.metadata["plagiarism_minhash_similarity"] = round(max_minhash_sim, 4)
        elif max_minhash_sim >= self._minhash_similarity_threshold:
            report.plagiarism_flag = True
            report.plagiarism_confidence = min(1.0, combined_score)
            report.issues.append(f"Potential plagiarism detected " f"({max_minhash_sim:.0%} MinHash similarity)")
            report.metadata["plagiarism_ngram_overlap"] = round(max_ngram_overlap, 4)
            report.metadata["plagiarism_minhash_similarity"] = round(max_minhash_sim, 4)
        else:
            report.plagiarism_flag = False
            report.plagiarism_confidence = combined_score
            report.metadata["plagiarism_ngram_overlap"] = round(max_ngram_overlap, 4)
            report.metadata["plagiarism_minhash_similarity"] = round(max_minhash_sim, 4)

        # Add current document to reference corpus for future comparisons
        self._reference_signatures.append(signature)
        self._reference_ngram_sets.append(ngrams)

    # ------------------------------------------------------------------
    # Hallucination detection via claim extraction
    # ------------------------------------------------------------------

    def _assess_hallucination(
        self,
        content: str,
        report: QualityReport,
        *,
        context: str | None = None,
    ) -> None:
        """Detect potential hallucinations via claim extraction and scoring.

        Approach:
        1. Split *content* into sentences.
        2. Classify each sentence as a *factual claim* if it contains
           numbers, dates, proper nouns, or other verifiable markers.
        3. If *context* (source/prompt) is provided, cross-reference each
           claim against the context using token overlap.  Claims whose
           key terms do not appear in the context are considered
           *unverifiable*.
        4. Compute a confidence score based on claim density and the ratio
           of unverifiable claims.
        """
        sentences = self._split_sentences(content)
        if not sentences:
            report.hallucination_flag = False
            report.hallucination_confidence = 0.0
            return

        claims: list[str] = []
        non_claims: list[str] = []

        for sentence in sentences:
            if self._is_factual_claim(sentence):
                claims.append(sentence)
            else:
                non_claims.append(sentence)

        total_sentences = len(sentences)
        claim_count = len(claims)
        claim_density = claim_count / total_sentences if total_sentences else 0.0

        # Cross-reference claims against context if available
        unverifiable_count = 0
        if context and claims:
            context_tokens = set(self._normalize_words(context))
            for claim in claims:
                if not self._claim_supported_by_context(claim, context_tokens):
                    unverifiable_count += 1

        unverifiable_ratio = unverifiable_count / claim_count if claim_count else 0.0

        # Confidence scoring
        # High claim density with many unverifiable claims = high confidence
        # of hallucination.  Without context we rely on claim density alone
        # as a weaker signal.
        if context:
            # With context we can be more precise
            confidence = self._compute_hallucination_confidence_with_context(claim_density, unverifiable_ratio)
        else:
            # Without context, use heuristic based on claim density and
            # the proportion of "strong" claims (specific numbers/dates)
            strong_claim_count = sum(1 for c in claims if self._is_strong_claim(c))
            strong_ratio = strong_claim_count / total_sentences if total_sentences else 0.0
            confidence = self._compute_hallucination_confidence_no_context(claim_density, strong_ratio)

        report.hallucination_confidence = round(min(1.0, max(0.0, confidence)), 4)
        report.hallucination_flag = report.hallucination_confidence >= 0.5

        if report.hallucination_flag:
            report.issues.append(
                f"Potential hallucination detected " f"(confidence {report.hallucination_confidence:.0%})"
            )

        report.metadata["hallucination_claim_count"] = claim_count
        report.metadata["hallucination_claim_density"] = round(claim_density, 4)
        report.metadata["hallucination_unverifiable_count"] = unverifiable_count
        report.metadata["hallucination_unverifiable_ratio"] = round(unverifiable_ratio, 4)

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_overall_score(report: QualityReport) -> float:
        """Weighted combination of quality signals."""
        # Readability contributes 60%, plagiarism/hallucination 20% each
        readability_component = report.readability_score * 0.60

        # Plagiarism: 100 = clean, 0 = confirmed plagiarism
        plagiarism_component = ((1.0 - report.plagiarism_confidence) * 100.0) * 0.20

        # Hallucination: 100 = clean, 0 = confirmed hallucination
        hallucination_component = ((1.0 - report.hallucination_confidence) * 100.0) * 0.20

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
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Approximate syllable count for English words."""
        word = word.lower().rstrip("e")
        vowels = re.findall(r"[aeiouy]+", word)
        count = len(vowels)
        return max(1, count)

    # ------------------------------------------------------------------
    # Plagiarism detection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_words(text: str) -> list[str]:
        """Lowercase and extract alphabetic tokens for fingerprinting."""
        return [w.lower() for w in re.findall(r"[a-zA-Z']+", text) if len(w) > 1]

    @staticmethod
    def _build_ngrams(words: list[str], n: int) -> set[tuple[str, ...]]:
        """Build a set of word-level n-grams (shingles)."""
        if len(words) < n:
            return set()
        return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}

    @staticmethod
    def _generate_minhash_coefficients(
        num_perm: int,
    ) -> tuple[list[int], list[int]]:
        """Pre-generate random coefficients for MinHash universal hashing.

        Uses deterministic seeding so results are reproducible across runs.
        Returns two lists (a, b) of length *num_perm*.
        """
        import random

        rng = random.Random(42)  # deterministic seed
        a_coeffs: list[int] = []
        b_coeffs: list[int] = []
        for _ in range(num_perm):
            a_coeffs.append(rng.randint(1, _MERSENNE_PRIME - 1))
            b_coeffs.append(rng.randint(0, _MERSENNE_PRIME - 1))
        return a_coeffs, b_coeffs

    def _minhash_signature(self, ngrams: set[tuple[str, ...]]) -> list[int]:
        """Compute a MinHash signature for a set of n-grams.

        Each n-gram is hashed to a 32-bit integer, then for each of
        ``_NUM_MINHASH_PERM`` universal hash functions we keep the minimum
        hash value.  The resulting list of minimums is the signature.
        """
        num_perm = _NUM_MINHASH_PERM
        signature = [_MAX_HASH] * num_perm

        for shingle in ngrams:
            # Hash the shingle to a 32-bit int via SHA-256 truncation
            h = self._hash_shingle(shingle)
            for i in range(num_perm):
                # Universal hash: h_i(x) = (a_i * x + b_i) mod p mod 2^32
                val = ((self._hash_a[i] * h + self._hash_b[i]) % _MERSENNE_PRIME) & _MAX_HASH
                if val < signature[i]:
                    signature[i] = val

        return signature

    @staticmethod
    def _hash_shingle(shingle: tuple[str, ...]) -> int:
        """Deterministically hash a word-tuple to a 32-bit unsigned int."""
        raw = " ".join(shingle).encode("utf-8")
        digest = hashlib.sha256(raw).digest()
        return cast("int", struct.unpack("<I", digest[:4])[0])

    @staticmethod
    def _minhash_jaccard(sig_a: list[int], sig_b: list[int]) -> float:
        """Estimate Jaccard similarity from two MinHash signatures."""
        if not sig_a or not sig_b or len(sig_a) != len(sig_b):
            return 0.0
        matches = sum(1 for a, b in zip(sig_a, sig_b, strict=False) if a == b)
        return matches / len(sig_a)

    # ------------------------------------------------------------------
    # Hallucination detection helpers
    # ------------------------------------------------------------------

    # Patterns for identifying factual claims
    _RE_NUMBERS = re.compile(r"\b\d[\d,.]*\b")
    _RE_DATES = re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}|\b(?:January|February|"
        r"March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:,?\s+\d{4})?)\b",
        re.IGNORECASE,
    )
    _RE_PROPER_NOUNS = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")
    _RE_PERCENTAGES = re.compile(r"\b\d+(?:\.\d+)?%")
    _RE_MEASUREMENTS = re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:kg|lb|km|mi|cm|mm|m|ft|in|oz|mg|g|ml|l|" r"mph|kph|hz|gb|mb|kb|tb)\b",
        re.IGNORECASE,
    )

    # Common English stop words to ignore during context matching
    _STOP_WORDS: frozenset[str] = frozenset(
        {
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "shall",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "out",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "because",
            "but",
            "and",
            "or",
            "if",
            "while",
            "about",
            "up",
            "it",
            "its",
            "this",
            "that",
            "these",
            "those",
            "i",
            "me",
            "my",
            "we",
            "our",
            "you",
            "your",
            "he",
            "him",
            "his",
            "she",
            "her",
            "they",
            "them",
            "their",
            "what",
            "which",
            "who",
            "whom",
        }
    )

    @classmethod
    def _is_factual_claim(cls, sentence: str) -> bool:
        """Return True if the sentence likely contains a verifiable factual claim.

        A sentence is considered a factual claim if it contains any of:
        - Numeric values (e.g., "42", "3.14")
        - Dates (e.g., "2024", "March 15, 2023")
        - Proper nouns (capitalized multi-word names)
        - Percentages ("15%")
        - Measurement units ("50 kg")
        """
        if cls._RE_NUMBERS.search(sentence):
            return True
        if cls._RE_DATES.search(sentence):
            return True
        if cls._RE_PERCENTAGES.search(sentence):
            return True
        if cls._RE_MEASUREMENTS.search(sentence):
            return True
        # Proper nouns: require at least two capitalized words to reduce
        # false positives from sentence-initial capitalization
        proper_nouns = cls._RE_PROPER_NOUNS.findall(sentence)
        multi_word_names = [pn for pn in proper_nouns if " " in pn]
        return bool(multi_word_names)

    @classmethod
    def _is_strong_claim(cls, sentence: str) -> bool:
        """Return True if the claim contains highly specific data.

        Strong claims are those with precise numbers, percentages, dates
        with full year, or measurement values -- the kind of data most
        likely to be hallucinated.
        """
        if cls._RE_PERCENTAGES.search(sentence):
            return True
        if cls._RE_MEASUREMENTS.search(sentence):
            return True
        if cls._RE_DATES.search(sentence):
            # Only count as strong if it includes a 4-digit year
            if re.search(r"\b\d{4}\b", sentence):
                return True
        # Precise multi-digit numbers
        return bool(re.search("\\b\\d{3,}\\b", sentence))

    @classmethod
    def _claim_supported_by_context(
        cls,
        claim: str,
        context_tokens: set[str],
    ) -> bool:
        """Check whether a claim's key terms appear in the context.

        Extracts non-stop-word tokens and specific data points (numbers,
        proper nouns) from the claim, then checks what fraction of them
        can be found in *context_tokens*.  If fewer than 50% of key terms
        are present, the claim is considered unverifiable.
        """
        claim_words = [
            w.lower() for w in re.findall(r"[a-zA-Z']+", claim) if len(w) > 1 and w.lower() not in cls._STOP_WORDS
        ]
        # Also extract raw numbers as "key terms"
        claim_numbers = cls._RE_NUMBERS.findall(claim)

        key_terms = claim_words + [n.lower() for n in claim_numbers]
        if not key_terms:
            # No key terms to verify -- treat as supported
            return True

        matched = sum(1 for term in key_terms if term in context_tokens)
        support_ratio = matched / len(key_terms)
        return support_ratio >= 0.5

    @staticmethod
    def _compute_hallucination_confidence_with_context(
        claim_density: float,
        unverifiable_ratio: float,
    ) -> float:
        """Compute hallucination confidence when source context is available.

        Heavily weights *unverifiable_ratio* since we have a concrete
        reference to compare against.  Claim density acts as a secondary
        amplifier -- dense factual content with many unsupported claims is
        a strong hallucination signal.
        """
        # Primary signal: unverifiable ratio (0-1)
        # Secondary signal: claim density amplifier
        base = unverifiable_ratio * 0.75
        density_boost = claim_density * unverifiable_ratio * 0.25
        return min(1.0, base + density_boost)

    @staticmethod
    def _compute_hallucination_confidence_no_context(
        claim_density: float,
        strong_claim_ratio: float,
    ) -> float:
        """Compute hallucination confidence without source context.

        Without context we cannot truly verify claims, so we apply a
        conservative heuristic: only flag when claim density is very high
        **and** many claims contain highly specific data (which LLMs are
        more likely to fabricate).

        The confidence tops out lower than the with-context variant since
        we are less certain.
        """
        # Only flag when density is notably high AND strong claims abound
        if claim_density < _CLAIM_DENSITY_HIGH:
            # Below the high-density threshold, confidence stays low
            return strong_claim_ratio * claim_density * 0.3
        # High density of strong claims
        base = strong_claim_ratio * 0.5
        density_amplifier = (claim_density - _CLAIM_DENSITY_HIGH) * 0.5
        return min(0.75, base + density_amplifier)  # cap at 0.75 without context
