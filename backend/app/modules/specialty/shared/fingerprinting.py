"""Originality Fingerprinting System.

Generates content-type-specific fingerprints and compares them to detect
duplicate or near-duplicate content across books.  Supports four content
types:

* **images** -- perceptual hash (simplified average hash)
* **puzzle_grids** -- SHA-256 of normalised grid JSON
* **word_lists** -- Jaccard similarity coefficient
* **text** -- 3-gram frequency vector fingerprint

Blueprint refs: 7.1, 7.3, 7.4
"""
from __future__ import annotations

import hashlib
import json
import math
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.shared import ContentFingerprint


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class FingerprintResult:
    """Container returned by :func:`generate_fingerprint`."""

    content_type: str
    fingerprint: str
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicateGuardrailResult:
    """Result of anti-duplicate guardrail checks."""

    passed: bool
    unique_ratio: float
    threshold: float
    violations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal fingerprint generators
# ---------------------------------------------------------------------------

def _average_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """Compute a simplified average-hash (aHash) for an image.

    This is a *pure-Python* approximation that works on raw pixel bytes
    (grayscale, row-major).  For production use, callers should convert
    their image to an 8x8 grayscale before passing the 64 pixel values
    here.  The function also accepts arbitrary-length bytes and will
    down-sample by averaging blocks.

    Returns a hex string of length ``hash_size ** 2 // 4``.
    """
    total_pixels = hash_size * hash_size
    pixels = list(image_bytes)

    # Down-sample to hash_size x hash_size by block averaging
    if len(pixels) >= total_pixels:
        block = max(len(pixels) // total_pixels, 1)
        sampled: list[float] = []
        for i in range(total_pixels):
            start = i * block
            end = min(start + block, len(pixels))
            chunk = pixels[start:end]
            sampled.append(sum(chunk) / len(chunk) if chunk else 0)
    else:
        # Pad short input with zeros
        sampled = [float(p) for p in pixels] + [0.0] * (total_pixels - len(pixels))

    mean_val = sum(sampled) / total_pixels if total_pixels else 0

    # Build bit string: 1 if pixel >= mean, else 0
    bits = "".join("1" if px >= mean_val else "0" for px in sampled)

    # Convert to hex
    hex_str = format(int(bits, 2), f"0{total_pixels // 4}x")
    return hex_str


def _grid_data_hash(grid_data: Any) -> str:
    """SHA-256 of the normalised JSON representation of *grid_data*."""
    normalised = json.dumps(grid_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _jaccard_vector(word_list: list[str]) -> dict[str, Any]:
    """Store the word set for later Jaccard comparison.

    Returns a dict with the canonical sorted word set so it can be
    persisted as JSON in ``jaccard_vector``.
    """
    normalised = sorted({w.strip().lower() for w in word_list if w.strip()})
    return {"words": normalised}


def _ngram_fingerprint(text: str, n: int = 3) -> str:
    """Build a 3-gram frequency-vector fingerprint.

    Returns a JSON string of the top-128 n-grams (by frequency) which
    serves as the fingerprint for similarity comparison.
    """
    text_lower = text.lower()
    if len(text_lower) < n:
        return json.dumps({})
    grams: Counter[str] = Counter()
    for i in range(len(text_lower) - n + 1):
        grams[text_lower[i : i + n]] += 1
    # Keep top 128 grams for compact storage
    top = dict(grams.most_common(128))
    return json.dumps(top, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _hamming_distance(hex_a: str, hex_b: str) -> float:
    """Normalised Hamming distance between two hex hash strings (0.0-1.0).

    0.0 = identical, 1.0 = completely different.
    """
    if len(hex_a) != len(hex_b):
        max_len = max(len(hex_a), len(hex_b))
        hex_a = hex_a.ljust(max_len, "0")
        hex_b = hex_b.ljust(max_len, "0")
    int_a = int(hex_a, 16)
    int_b = int(hex_b, 16)
    xor = int_a ^ int_b
    total_bits = len(hex_a) * 4
    diff_bits = bin(xor).count("1")
    return diff_bits / total_bits if total_bits else 0.0


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard similarity coefficient between two sets (0.0-1.0)."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _cosine_similarity(vec_a: dict[str, int], vec_b: dict[str, int]) -> float:
    """Cosine similarity between two sparse frequency vectors (0.0-1.0)."""
    all_keys = set(vec_a) | set(vec_b)
    if not all_keys:
        return 1.0
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in all_keys)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_fingerprint(
    content_type: str,
    content_data: Any,
) -> FingerprintResult:
    """Generate a fingerprint for the given content.

    Parameters
    ----------
    content_type:
        One of ``"images"``, ``"puzzle_grids"``, ``"word_lists"``, ``"text"``.
    content_data:
        The raw content.  Expected types:
        - images: ``bytes`` (raw pixel data or image bytes)
        - puzzle_grids: any JSON-serialisable grid structure
        - word_lists: ``list[str]``
        - text: ``str``

    Returns
    -------
    FingerprintResult
        Includes the fingerprint value, method name, and optional metadata.
    """
    if content_type == "images":
        fp = _average_hash(content_data)
        return FingerprintResult(
            content_type=content_type,
            fingerprint=fp,
            method="average_hash",
            metadata={"hash_size": 8},
        )
    elif content_type == "puzzle_grids":
        fp = _grid_data_hash(content_data)
        return FingerprintResult(
            content_type=content_type,
            fingerprint=fp,
            method="sha256_grid",
        )
    elif content_type == "word_lists":
        vec = _jaccard_vector(content_data)
        # Use a hash of the sorted word list as the canonical fingerprint
        fp = hashlib.sha256(
            json.dumps(vec, sort_keys=True).encode()
        ).hexdigest()
        return FingerprintResult(
            content_type=content_type,
            fingerprint=fp,
            method="jaccard",
            metadata={"word_count": len(vec["words"]), "words": vec["words"]},
        )
    elif content_type == "text":
        fp = _ngram_fingerprint(content_data)
        return FingerprintResult(
            content_type=content_type,
            fingerprint=fp,
            method="ngram_3",
        )
    else:
        raise ValueError(f"Unsupported content_type: {content_type!r}")


def compare_fingerprints(
    fp1: FingerprintResult,
    fp2: FingerprintResult,
) -> float:
    """Compare two fingerprints and return a similarity score (0.0-1.0).

    Higher values indicate more similar content.  The comparison method
    is chosen based on the content type of *fp1*.
    """
    if fp1.content_type != fp2.content_type:
        raise ValueError(
            f"Cannot compare different content types: "
            f"{fp1.content_type!r} vs {fp2.content_type!r}"
        )

    if fp1.content_type == "images":
        # Hamming distance gives dissimilarity; invert for similarity
        return 1.0 - _hamming_distance(fp1.fingerprint, fp2.fingerprint)

    elif fp1.content_type == "puzzle_grids":
        # SHA-256: either identical or not
        return 1.0 if fp1.fingerprint == fp2.fingerprint else 0.0

    elif fp1.content_type == "word_lists":
        words_a = set(fp1.metadata.get("words", []))
        words_b = set(fp2.metadata.get("words", []))
        return _jaccard_similarity(words_a, words_b)

    elif fp1.content_type == "text":
        vec_a: dict[str, int] = json.loads(fp1.fingerprint) if fp1.fingerprint else {}
        vec_b: dict[str, int] = json.loads(fp2.fingerprint) if fp2.fingerprint else {}
        return _cosine_similarity(vec_a, vec_b)

    else:
        raise ValueError(f"Unsupported content_type: {fp1.content_type!r}")


async def cross_book_comparison(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_id: uuid.UUID,
) -> list[tuple[uuid.UUID, float]]:
    """Compare a book's fingerprints against all other books in the org.

    Returns a list of ``(other_book_id, similarity_score)`` pairs sorted
    by descending similarity.
    """
    # Fetch fingerprints for the target book
    target_stmt = select(ContentFingerprint).where(
        ContentFingerprint.org_id == org_id,
        ContentFingerprint.book_id == book_id,
    )
    target_result = await db.execute(target_stmt)
    target_rows = target_result.scalars().all()

    if not target_rows:
        return []

    # Fetch all other fingerprints in the org
    others_stmt = select(ContentFingerprint).where(
        ContentFingerprint.org_id == org_id,
        ContentFingerprint.book_id != book_id,
    )
    others_result = await db.execute(others_stmt)
    others_rows = others_result.scalars().all()

    if not others_rows:
        return []

    # Group other fingerprints by book_id
    other_books: dict[uuid.UUID, list[ContentFingerprint]] = {}
    for row in others_rows:
        other_books.setdefault(row.book_id, []).append(row)

    # Compare each target fingerprint against each other book's fingerprints
    book_scores: dict[uuid.UUID, list[float]] = {}

    for target_row in target_rows:
        target_fp = _row_to_fingerprint_result(target_row)
        if target_fp is None:
            continue

        for other_book_id, other_rows_list in other_books.items():
            for other_row in other_rows_list:
                if other_row.content_type != target_row.content_type:
                    continue
                other_fp = _row_to_fingerprint_result(other_row)
                if other_fp is None:
                    continue
                try:
                    score = compare_fingerprints(target_fp, other_fp)
                except ValueError:
                    continue
                book_scores.setdefault(other_book_id, []).append(score)

    # Average scores per book
    results: list[tuple[uuid.UUID, float]] = []
    for bid, scores in book_scores.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        results.append((bid, avg))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def check_anti_duplicate_guardrails(
    book_type: str,
    unique_ratio: float,
    word_overlap_ratio: float = 0.0,
) -> DuplicateGuardrailResult:
    """Check anti-duplicate guardrails per book type.

    Thresholds (from blueprint 7.4):
    - Coloring books: 85% unique pages per volume
    - Puzzle books: 100% unique grids
    - Max 30% word overlap between volumes
    """
    violations: list[str] = []

    if book_type == "coloring":
        threshold = 0.85
        if unique_ratio < threshold:
            violations.append(
                f"Coloring book has {unique_ratio:.0%} unique pages "
                f"(minimum {threshold:.0%} required)"
            )
    elif book_type == "puzzle":
        threshold = 1.0
        if unique_ratio < threshold:
            violations.append(
                f"Puzzle book has {unique_ratio:.0%} unique grids "
                f"(100% unique grids required)"
            )
    else:
        # Children's books -- no specific page uniqueness threshold
        threshold = 0.0

    # Word overlap check (applies to all types with word-based content)
    if word_overlap_ratio > 0.30:
        violations.append(
            f"Word overlap between volumes is {word_overlap_ratio:.0%} "
            f"(maximum 30% allowed)"
        )

    passed = len(violations) == 0
    return DuplicateGuardrailResult(
        passed=passed,
        unique_ratio=unique_ratio,
        threshold=threshold,
        violations=violations,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_fingerprint_result(row: ContentFingerprint) -> FingerprintResult | None:
    """Convert a DB row back into a FingerprintResult for comparison."""
    ct = row.content_type

    if ct == "images":
        if not row.phash:
            return None
        return FingerprintResult(
            content_type=ct,
            fingerprint=row.phash,
            method="average_hash",
        )
    elif ct == "puzzle_grids":
        if not row.data_hash:
            return None
        return FingerprintResult(
            content_type=ct,
            fingerprint=row.data_hash,
            method="sha256_grid",
        )
    elif ct == "word_lists":
        if not row.jaccard_vector:
            return None
        words = row.jaccard_vector.get("words", [])
        fp = hashlib.sha256(
            json.dumps(row.jaccard_vector, sort_keys=True).encode()
        ).hexdigest()
        return FingerprintResult(
            content_type=ct,
            fingerprint=fp,
            method="jaccard",
            metadata={"word_count": len(words), "words": words},
        )
    elif ct == "text":
        if not row.ngram_fingerprint:
            return None
        return FingerprintResult(
            content_type=ct,
            fingerprint=row.ngram_fingerprint,
            method="ngram_3",
        )
    return None
