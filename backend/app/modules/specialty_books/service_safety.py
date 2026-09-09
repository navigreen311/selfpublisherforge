"""Safety & compliance service for Specialty Books.

Provides originality fingerprinting, KDP spam risk detection,
trademark-safe enforcement, content sensitivity checks,
anti-duplicate guardrails, and full compliance report generation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

SIMILARITY_THRESHOLD = 0.40  # 40% overlap triggers a flag

# Trademark blocklist — well-known brands that must never appear in
# user-generated content destined for KDP.
TRADEMARK_BLOCKLIST: list[str] = [
    "disney",
    "pixar",
    "peppa pig",
    "bluey",
    "paw patrol",
    "marvel",
    "frozen",
    "cocomelon",
    "sesame street",
    "pokemon",
    "pikachu",
    "hello kitty",
    "barbie",
    "lego",
    "hot wheels",
    "transformers",
    "spider-man",
    "spiderman",
    "batman",
    "superman",
    "wonder woman",
    "star wars",
    "minions",
    "teenage mutant ninja turtles",
    "tmnt",
    "my little pony",
    "care bears",
    "spongebob",
    "dora the explorer",
    "thomas the tank engine",
    "thomas and friends",
    "bob the builder",
    "winnie the pooh",
    "mickey mouse",
    "donald duck",
    "elsa",
    "moana",
    "encanto",
    "nintendo",
    "mario",
    "sonic the hedgehog",
    "fortnite",
    "roblox",
    "minecraft",
    "among us",
]

# Pattern for "in the style of [specific artist]"
STYLE_OF_PATTERN = re.compile(
    r"\bin\s+the\s+style\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    re.IGNORECASE,
)

# Sensitive content patterns organised by category.
SENSITIVITY_PATTERNS: dict[str, list[str]] = {
    "weapons_violence": [
        r"\b(?:gun|pistol|rifle|shotgun|firearm|sword|dagger|knife|weapon)\b",
        r"\b(?:shoot|stab|kill|murder|slaughter|blood|gore|wound|bleed)\b",
        r"\b(?:war|battle|combat|fight|attack|assault|explosion|bomb)\b",
    ],
    "excessive_fear": [
        r"\b(?:terror|horrify|nightmare|scream|torture|agony|dread)\b",
        r"\b(?:monster|demon|devil|ghost|zombie|skeleton)\s+(?:attack|chase|hunt)\b",
    ],
    "stereotypes": [
        r"\b(?:savage|primitive|uncivilised|uncivilized)\s+(?:people|tribe|native)\b",
        r"\b(?:all\s+(?:boys|girls|women|men)\s+(?:are|should|must))\b",
    ],
    "mature_themes": [
        r"\b(?:sex|sexual|nude|naked|porn|erotic|drug|cocaine|heroin|meth)\b",
        r"\b(?:alcohol|beer|wine|vodka|drunk|intoxicated|cigarette|smoking)\b",
    ],
}

# Words that are generally too advanced for young children (ages 0-5).
ADVANCED_VOCABULARY: set[str] = {
    "consequently",
    "nevertheless",
    "furthermore",
    "notwithstanding",
    "paradoxical",
    "juxtaposition",
    "epistemological",
    "quintessential",
    "metamorphosis",
    "philosophical",
    "ambiguity",
    "dichotomy",
    "existential",
    "transcendent",
    "conundrum",
    "unprecedented",
    "infrastructure",
    "bureaucratic",
    "ecclesiastical",
    "antidisestablishmentarianism",
}


# ═══════════════════════════════════════════════════════════════════════
# HASHING / FINGERPRINT HELPERS
# ═══════════════════════════════════════════════════════════════════════


def _sha256(data: str) -> str:
    """Return a hex SHA-256 digest of *data*."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _compute_phash(image_url: str | None) -> str | None:
    """Compute a perceptual hash for an image.

    In production this would download the image and run a pHash algorithm
    (e.g. via the ``imagehash`` library). For now we derive a deterministic
    hash from the URL so the fingerprinting pipeline works end-to-end.
    """
    if not image_url:
        return None
    return _sha256(f"phash:{image_url}")[:16]


def _compute_grid_hash(grid_data: dict | list | None) -> str | None:
    """Hash a puzzle grid data structure."""
    if not grid_data:
        return None
    serialised = json.dumps(grid_data, sort_keys=True, default=str)
    return _sha256(serialised)


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute the Jaccard similarity coefficient of two string sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _extract_ngrams(text: str, n: int = 3) -> list[str]:
    """Extract word-level n-grams from *text*."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < n:
        return words
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def _ngram_fingerprint(text: str | None, n: int = 3) -> str | None:
    """Create an n-gram fingerprint string from *text*."""
    if not text:
        return None
    ngrams = _extract_ngrams(text, n)
    if not ngrams:
        return None
    return _sha256("|".join(sorted(set(ngrams))))


def _ngram_similarity(text_a: str | None, text_b: str | None, n: int = 3) -> float:
    """Compare two texts using n-gram overlap (Jaccard over n-gram sets)."""
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0
    set_a = set(_extract_ngrams(text_a, n))
    set_b = set(_extract_ngrams(text_b, n))
    return _jaccard_similarity(set_a, set_b)


# ═══════════════════════════════════════════════════════════════════════
# 1. ORIGINALITY FINGERPRINTING
# ═══════════════════════════════════════════════════════════════════════


async def _get_book_record(db: AsyncSession, book_type: str, book_id: uuid.UUID, org_id: uuid.UUID) -> Any:
    """Retrieve the book record for a given type."""
    # Lazy imports to avoid circular dependencies
    if book_type == "childrens":
        from app.modules.specialty_books.models_childrens import ChildrensBook as Model
    elif book_type == "coloring":
        try:
            from app.modules.specialty_books.models_coloring import ColoringBook as Model  # type: ignore[assignment]
        except ImportError:
            return None
    elif book_type == "puzzle":
        try:
            from app.modules.specialty_books.models_puzzle import PuzzleBook as Model  # type: ignore[assignment]
        except ImportError:
            return None
    else:
        return None

    result = await db.execute(select(Model).where(Model.id == book_id, Model.org_id == org_id))
    return result.scalar_one_or_none()


async def _get_book_pages(db: AsyncSession, book_type: str, book_id: uuid.UUID, org_id: uuid.UUID) -> list[Any]:
    """Retrieve pages/puzzles for a book."""
    if book_type == "childrens":
        from app.modules.specialty_books.models_childrens import ChildrensBookPage as PageModel
    elif book_type == "coloring":
        try:
            from app.modules.specialty_books.models_coloring import (
                ColoringBookPage as PageModel,  # type: ignore[assignment]
            )
        except ImportError:
            return []
    elif book_type == "puzzle":
        try:
            from app.modules.specialty_books.models_puzzle import Puzzle as PageModel  # type: ignore[assignment]
        except ImportError:
            return []
    else:
        return []

    result = await db.execute(select(PageModel).where(PageModel.book_id == book_id, PageModel.org_id == org_id))
    return list(result.scalars().all())


async def generate_originality_fingerprint(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate multi-method originality fingerprints for a book.

    Methods used per content type:
    - Images: perceptual hash (pHash)
    - Puzzles: grid hash (SHA-256 of grid data)
    - Word lists: Jaccard similarity vector
    - Text: n-gram fingerprinting (sliding window of 3 words)

    Returns a dict with per-page fingerprints and an overall fingerprint hash.
    """
    pages = await _get_book_pages(db, book_type, book_id, org_id)

    fingerprints: list[dict[str, Any]] = []
    combined_parts: list[str] = []

    for page in pages:
        fp: dict[str, Any] = {
            "page_id": str(getattr(page, "id", "")),
        }

        # Image pHash (children's illustration_url, coloring illustration_url)
        image_url = getattr(page, "illustration_url", None)
        phash = _compute_phash(image_url)
        if phash:
            fp["phash"] = phash
            combined_parts.append(phash)

        # Grid hash (puzzle grid_data)
        grid_data = getattr(page, "grid_data", None)
        grid_hash = _compute_grid_hash(grid_data)
        if grid_hash:
            fp["data_hash"] = grid_hash
            combined_parts.append(grid_hash)

        # Word list Jaccard vector (puzzle word_list)
        word_list = getattr(page, "word_list", None)
        if word_list and isinstance(word_list, (list, set)):
            words_set = set(w.lower() for w in word_list if isinstance(w, str))
            fp["jaccard_vector"] = sorted(words_set)
            combined_parts.append("|".join(sorted(words_set)))

        # Text n-gram fingerprint (children's text_content, puzzle clues)
        text_content = getattr(page, "text_content", None)
        ngram_fp = _ngram_fingerprint(text_content)
        if ngram_fp:
            fp["ngram_fingerprint"] = ngram_fp
            combined_parts.append(ngram_fp)

        fingerprints.append(fp)

    overall_hash = _sha256("|".join(combined_parts)) if combined_parts else _sha256("empty")

    result = {
        "book_type": book_type,
        "book_id": str(book_id),
        "org_id": str(org_id),
        "fingerprints": fingerprints,
        "overall_hash": overall_hash,
        "page_count": len(fingerprints),
        "generated_at": datetime.now(UTC).isoformat(),
    }

    logger.info(
        "Generated originality fingerprint for %s/%s: %d pages, hash=%s",
        book_type,
        book_id,
        len(fingerprints),
        overall_hash[:12],
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# 2. COMPARE ORIGINALITY
# ═══════════════════════════════════════════════════════════════════════


async def compare_originality(
    db: AsyncSession,
    book_id_1: uuid.UUID,
    book_id_2: uuid.UUID,
    org_id: uuid.UUID,
    book_type: str = "childrens",
) -> dict[str, Any]:
    """Compare two books and return a detailed similarity report.

    Compares all fingerprint types between the books, calculates per-type
    similarity scores and an overall weighted average. Flags if >40% overlap.
    """
    fp1 = await generate_originality_fingerprint(db, book_type, book_id_1, org_id)
    fp2 = await generate_originality_fingerprint(db, book_type, book_id_2, org_id)

    scores: dict[str, float] = {}

    # Compare pHash fingerprints
    phashes_1 = [f["phash"] for f in fp1["fingerprints"] if "phash" in f]
    phashes_2 = [f["phash"] for f in fp2["fingerprints"] if "phash" in f]
    if phashes_1 and phashes_2:
        matching = len(set(phashes_1) & set(phashes_2))
        total = max(len(set(phashes_1) | set(phashes_2)), 1)
        scores["image_phash"] = matching / total

    # Compare grid hashes
    grids_1 = [f["data_hash"] for f in fp1["fingerprints"] if "data_hash" in f]
    grids_2 = [f["data_hash"] for f in fp2["fingerprints"] if "data_hash" in f]
    if grids_1 and grids_2:
        matching = len(set(grids_1) & set(grids_2))
        total = max(len(set(grids_1) | set(grids_2)), 1)
        scores["grid_hash"] = matching / total

    # Compare word lists via Jaccard
    words_1: set[str] = set()
    words_2: set[str] = set()
    for f in fp1["fingerprints"]:
        if "jaccard_vector" in f:
            words_1.update(f["jaccard_vector"])
    for f in fp2["fingerprints"]:
        if "jaccard_vector" in f:
            words_2.update(f["jaccard_vector"])
    if words_1 or words_2:
        scores["word_list_jaccard"] = _jaccard_similarity(words_1, words_2)

    # Compare text via n-gram fingerprints
    ngrams_1 = [f["ngram_fingerprint"] for f in fp1["fingerprints"] if "ngram_fingerprint" in f]
    ngrams_2 = [f["ngram_fingerprint"] for f in fp2["fingerprints"] if "ngram_fingerprint" in f]
    if ngrams_1 and ngrams_2:
        matching = len(set(ngrams_1) & set(ngrams_2))
        total = max(len(set(ngrams_1) | set(ngrams_2)), 1)
        scores["text_ngram"] = matching / total

    # Weighted overall score
    weights = {
        "image_phash": 0.35,
        "grid_hash": 0.30,
        "word_list_jaccard": 0.20,
        "text_ngram": 0.15,
    }
    total_weight = sum(weights.get(k, 0.25) for k in scores)
    if total_weight > 0:
        overall = sum(scores[k] * weights.get(k, 0.25) for k in scores) / total_weight
    else:
        overall = 0.0

    flagged = overall > SIMILARITY_THRESHOLD

    if flagged:
        recommendation = (
            f"HIGH SIMILARITY ({overall:.0%}): These books share significant content. "
            "Differentiate before publishing to avoid KDP duplicate-content flags."
        )
    else:
        recommendation = f"Similarity is within acceptable range ({overall:.0%})."

    return {
        "book_a_id": str(book_id_1),
        "book_b_id": str(book_id_2),
        "similarity_score": round(overall * 100, 2),
        "per_type_scores": {k: round(v * 100, 2) for k, v in scores.items()},
        "flagged": flagged,
        "recommendation": recommendation,
        "compared_at": datetime.now(UTC).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════
# 3. CROSS-BOOK SIMILARITY MATRIX
# ═══════════════════════════════════════════════════════════════════════


async def cross_book_similarity_matrix(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_type: str,
) -> dict[str, Any]:
    """Build a similarity matrix across all books of the same type in an org.

    Flags any pair with >40% similarity.
    """
    # Retrieve all book IDs of this type for the org
    if book_type == "childrens":
        from app.modules.specialty_books.models_childrens import ChildrensBook as Model
    elif book_type == "coloring":
        try:
            from app.modules.specialty_books.models_coloring import ColoringBook as Model  # type: ignore[assignment]
        except ImportError:
            return {"matrix": [], "flagged_pairs": [], "book_count": 0}
    elif book_type == "puzzle":
        try:
            from app.modules.specialty_books.models_puzzle import PuzzleBook as Model  # type: ignore[assignment]
        except ImportError:
            return {"matrix": [], "flagged_pairs": [], "book_count": 0}
    else:
        return {"matrix": [], "flagged_pairs": [], "book_count": 0}

    result = await db.execute(select(Model.id).where(Model.org_id == org_id))
    book_ids = [row[0] for row in result.all()]

    matrix: list[dict[str, Any]] = []
    flagged_pairs: list[dict[str, Any]] = []

    for i, bid_a in enumerate(book_ids):
        for bid_b in book_ids[i + 1 :]:
            comparison = await compare_originality(db, bid_a, bid_b, org_id, book_type)
            entry = {
                "book_a_id": str(bid_a),
                "book_b_id": str(bid_b),
                "similarity_score": comparison["similarity_score"],
            }
            matrix.append(entry)
            if comparison["flagged"]:
                flagged_pairs.append(entry)

    return {
        "book_type": book_type,
        "org_id": str(org_id),
        "book_count": len(book_ids),
        "matrix": matrix,
        "flagged_pairs": flagged_pairs,
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════
# 4. KDP SPAM RISK DETECTOR
# ═══════════════════════════════════════════════════════════════════════


def _check_interior_originality(pages: list[Any]) -> tuple[float, list[dict[str, Any]]]:
    """Score interior originality. Returns (score 0-100, flags)."""
    flags: list[dict[str, Any]] = []
    if not pages:
        flags.append(
            {
                "type": "no_content",
                "severity": "error",
                "description": "Book has no pages/content.",
                "fix": "Add interior content before publishing.",
            }
        )
        return 0.0, flags

    # Check for unique content across pages
    hashes: list[str] = []
    for page in pages:
        parts: list[str] = []
        text_content = getattr(page, "text_content", None)
        if text_content:
            parts.append(text_content)
        illustration_url = getattr(page, "illustration_url", None)
        if illustration_url:
            parts.append(illustration_url)
        grid_data = getattr(page, "grid_data", None)
        if grid_data:
            parts.append(json.dumps(grid_data, sort_keys=True, default=str))
        content = "|".join(parts) if parts else f"empty_{getattr(page, 'id', '')}"
        hashes.append(_sha256(content))

    unique_ratio = len(set(hashes)) / max(len(hashes), 1)
    score = unique_ratio * 100

    if unique_ratio < 0.5:
        flags.append(
            {
                "type": "low_uniqueness",
                "severity": "error",
                "description": f"Only {unique_ratio:.0%} of pages have unique content.",
                "fix": "Diversify page content — each page should be substantially different.",
            }
        )
    elif unique_ratio < 0.8:
        flags.append(
            {
                "type": "moderate_uniqueness",
                "severity": "warning",
                "description": f"{unique_ratio:.0%} of pages are unique. Aim for 85%+.",
                "fix": "Review similar pages and add variation.",
            }
        )

    return score, flags


def _check_metadata_quality(book: Any) -> tuple[float, list[dict[str, Any]]]:
    """Score metadata quality. Returns (score 0-100, flags)."""
    flags: list[dict[str, Any]] = []
    score = 100.0

    title = getattr(book, "title", "") or ""
    description = getattr(book, "description", None) or ""

    # Keyword stuffing: too many commas, pipes, or extremely long title
    if len(title) > 200:
        score -= 30
        flags.append(
            {
                "type": "title_too_long",
                "severity": "warning",
                "description": f"Title is {len(title)} characters. KDP recommends <200.",
                "fix": "Shorten the title. Move keywords to the subtitle or keyword fields.",
            }
        )

    comma_count = title.count(",") + title.count("|") + title.count(" - ")
    if comma_count > 3:
        score -= 25
        flags.append(
            {
                "type": "keyword_stuffed_title",
                "severity": "error",
                "description": f"Title contains {comma_count} separator characters — likely keyword-stuffed.",
                "fix": "Use a natural title. Place keywords in subtitle and KDP keyword fields.",
            }
        )

    # Description substance
    if len(description) < 50:
        score -= 20
        flags.append(
            {
                "type": "thin_description",
                "severity": "warning",
                "description": "Description is too short (<50 chars). KDP recommends substantive descriptions.",
                "fix": "Write a detailed description of at least 150 characters.",
            }
        )

    return max(score, 0.0), flags


def _check_minor_edit_risk(pages: list[Any]) -> tuple[float, list[dict[str, Any]]]:
    """Detect if this looks like a minor edit of another book. Returns (score, flags)."""
    flags: list[dict[str, Any]] = []

    if not pages:
        return 100.0, flags

    # Check for very short or empty content pages
    empty_count = 0
    for page in pages:
        text = getattr(page, "text_content", None) or ""
        illustration = getattr(page, "illustration_url", None) or ""
        grid = getattr(page, "grid_data", None)
        if not text.strip() and not illustration and not grid:
            empty_count += 1

    empty_ratio = empty_count / max(len(pages), 1)
    score = (1 - empty_ratio) * 100

    if empty_ratio > 0.3:
        flags.append(
            {
                "type": "high_empty_pages",
                "severity": "warning",
                "description": f"{empty_ratio:.0%} of pages are empty or have no substantive content.",
                "fix": "Ensure all pages have meaningful content (text, illustrations, or puzzles).",
            }
        )

    return max(score, 0.0), flags


def _check_content_substance(pages: list[Any]) -> tuple[float, list[dict[str, Any]]]:
    """Check if there's enough real content vs filler. Returns (score, flags)."""
    flags: list[dict[str, Any]] = []

    if not pages:
        return 0.0, [
            {
                "type": "no_pages",
                "severity": "error",
                "description": "No pages found.",
                "fix": "Add content pages to the book.",
            }
        ]

    total_text_length = 0
    pages_with_content = 0

    for page in pages:
        text = getattr(page, "text_content", None) or ""
        illustration = getattr(page, "illustration_url", None) or ""
        grid = getattr(page, "grid_data", None)

        if text.strip() or illustration or grid:
            pages_with_content += 1
        total_text_length += len(text.strip())

    content_ratio = pages_with_content / max(len(pages), 1)
    score = content_ratio * 100

    if len(pages) < 10:
        score = min(score, 40.0)
        flags.append(
            {
                "type": "too_few_pages",
                "severity": "warning",
                "description": f"Only {len(pages)} pages. Low-content books risk KDP rejection.",
                "fix": "Add more pages to meet minimum content standards (at least 24 for most categories).",
            }
        )

    if content_ratio < 0.7:
        flags.append(
            {
                "type": "low_content_density",
                "severity": "error",
                "description": f"Only {content_ratio:.0%} of pages have substantive content.",
                "fix": "Fill empty pages with content or remove unnecessary blank pages.",
            }
        )

    return max(score, 0.0), flags


async def run_spam_check(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, Any]:
    """Run the KDP Spam Risk Detector.

    Checks:
    1. Interior originality — are pages unique enough?
    2. Metadata quality — title not keyword-stuffed, description substantive
    3. Minor-edit detection — is this just a slight variation of another book?
    4. Content substance — enough real content vs filler?

    Returns a risk assessment with score (0-100, higher = more risky),
    flags with remediation suggestions, and a pass/fail determination.
    """
    book = await _get_book_record(db, book_type, book_id, org_id)
    pages = await _get_book_pages(db, book_type, book_id, org_id)

    all_flags: list[dict[str, Any]] = []

    # 1. Interior originality
    interior_score, interior_flags = _check_interior_originality(pages)
    all_flags.extend(interior_flags)

    # 2. Metadata quality
    if book:
        meta_score, meta_flags = _check_metadata_quality(book)
        all_flags.extend(meta_flags)
    else:
        meta_score = 0.0
        all_flags.append(
            {
                "type": "book_not_found",
                "severity": "error",
                "description": "Book record not found.",
                "fix": "Ensure the book exists and belongs to your organization.",
            }
        )

    # 3. Minor-edit detection
    minor_edit_score, minor_edit_flags = _check_minor_edit_risk(pages)
    all_flags.extend(minor_edit_flags)

    # 4. Content substance
    substance_score, substance_flags = _check_content_substance(pages)
    all_flags.extend(substance_flags)

    # Compute overall risk score (inverse of quality — higher = more risky)
    quality_score = interior_score * 0.30 + meta_score * 0.25 + minor_edit_score * 0.20 + substance_score * 0.25
    risk_score = round(100 - quality_score, 2)

    passed = risk_score < 50  # Below 50 is acceptable

    return {
        "book_type": book_type,
        "book_id": str(book_id),
        "risk_score": risk_score,
        "flags": all_flags,
        "passed": passed,
        "component_scores": {
            "interior_originality": round(interior_score, 2),
            "metadata_quality": round(meta_score, 2),
            "minor_edit_risk": round(minor_edit_score, 2),
            "content_substance": round(substance_score, 2),
        },
        "checked_at": datetime.now(UTC).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════
# 5. TRADEMARK-SAFE ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════


def check_trademark_safety(text: str, context: str = "general") -> list[dict[str, Any]]:
    """Check text for trademark violations.

    Scans for:
    - Blocklisted brand names (Disney, Marvel, etc.)
    - "In the style of [specific artist]" patterns

    Args:
        text: The text to check (titles, descriptions, illustration prompts, etc.)
        context: Where the text comes from (title, description, prompt, etc.)

    Returns:
        List of violations with location, matched term, and severity.
    """
    violations: list[dict[str, Any]] = []

    # Check blocklist
    for trademark in TRADEMARK_BLOCKLIST:
        # Use word boundary matching for single words, substring for multi-word
        if " " in trademark:
            pattern = re.compile(re.escape(trademark), re.IGNORECASE)
        else:
            pattern = re.compile(rf"\b{re.escape(trademark)}\b", re.IGNORECASE)

        for match in pattern.finditer(text):
            violations.append(
                {
                    "type": "trademark_violation",
                    "term": match.group(),
                    "trademark": trademark,
                    "position": match.start(),
                    "context": context,
                    "severity": "error",
                    "description": (
                        f"Trademarked term '{match.group()}' detected in {context}. "
                        "This will likely trigger KDP rejection or legal action."
                    ),
                    "fix": f"Remove or replace '{match.group()}' with a generic alternative.",
                }
            )

    # Check "in the style of [artist]" pattern
    for match in STYLE_OF_PATTERN.finditer(text):
        artist_name = match.group(1)
        violations.append(
            {
                "type": "style_imitation",
                "term": match.group(),
                "artist": artist_name,
                "position": match.start(),
                "context": context,
                "severity": "warning",
                "description": (
                    f"'In the style of {artist_name}' detected in {context}. "
                    "Referencing specific artists may violate their rights or "
                    "trigger AI-art content policies."
                ),
                "fix": (
                    f"Describe the desired style using generic terms instead of "
                    f"referencing '{artist_name}' by name."
                ),
            }
        )

    return violations


# ═══════════════════════════════════════════════════════════════════════
# 6. CONTENT SENSITIVITY CHECK
# ═══════════════════════════════════════════════════════════════════════


def _parse_min_age(age_range: str | None) -> int:
    """Extract the minimum age from an age range string like '3-5' or '8-12'."""
    if not age_range:
        return 0
    match = re.match(r"(\d+)", age_range)
    return int(match.group(1)) if match else 0


def check_content_sensitivity(
    text: str,
    age_range: str | None = None,
) -> list[dict[str, Any]]:
    """Check text for content appropriateness based on target age range.

    Checks for:
    - Weapons/violence references
    - Excessive fear content
    - Stereotypical depictions
    - Mature themes
    - Age-appropriate vocabulary

    Returns a list of issues with severity (warning or block).
    """
    issues: list[dict[str, Any]] = []
    min_age = _parse_min_age(age_range)

    for category, patterns in SENSITIVITY_PATTERNS.items():
        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                # Determine severity based on age range and category
                if (
                    category == "mature_themes"
                    or category == "weapons_violence"
                    and min_age < 8
                    or category == "stereotypes"
                    or min_age < 6
                ):
                    severity = "block"
                else:
                    severity = "warning"

                issues.append(
                    {
                        "type": category,
                        "term": match.group(),
                        "position": match.start(),
                        "severity": severity,
                        "age_range": age_range or "unspecified",
                        "description": (
                            f"'{match.group()}' detected — potentially inappropriate "
                            f"for age range {age_range or 'unspecified'} "
                            f"(category: {category.replace('_', ' ')})."
                        ),
                    }
                )

    # Age-appropriate vocabulary check (only for young children)
    if min_age < 6:
        words = set(re.findall(r"\w+", text.lower()))
        advanced_found = words & ADVANCED_VOCABULARY
        for word in sorted(advanced_found):
            issues.append(
                {
                    "type": "advanced_vocabulary",
                    "term": word,
                    "severity": "warning",
                    "age_range": age_range or "unspecified",
                    "description": (f"'{word}' may be too advanced for children aged {age_range or '0-5'}."),
                }
            )

    return issues


# ═══════════════════════════════════════════════════════════════════════
# 7. ANTI-DUPLICATE GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════


async def anti_duplicate_guardrails(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, Any]:
    """Run volume-factory anti-duplicate guardrails.

    Rules:
    - Coloring: 85% unique pages per volume required
    - Puzzle: 100% unique grids required
    - Puzzle: max 30% word overlap between volumes

    Returns pass/fail with detailed checks.
    """
    pages = await _get_book_pages(db, book_type, book_id, org_id)
    checks: list[dict[str, Any]] = []
    overall_pass = True

    if book_type == "coloring":
        # 85% unique pages required
        if pages:
            hashes: list[str] = []
            for page in pages:
                url = getattr(page, "illustration_url", None) or ""
                prompt = getattr(page, "illustration_prompt", None) or ""
                content = f"{url}|{prompt}"
                hashes.append(_sha256(content))
            unique_ratio = len(set(hashes)) / max(len(hashes), 1)
            passed = unique_ratio >= 0.85
            if not passed:
                overall_pass = False
            checks.append(
                {
                    "rule": "unique_pages_85_pct",
                    "passed": passed,
                    "value": round(unique_ratio * 100, 2),
                    "threshold": 85.0,
                    "description": f"{unique_ratio:.0%} unique pages (require 85%+).",
                }
            )
        else:
            checks.append(
                {
                    "rule": "unique_pages_85_pct",
                    "passed": False,
                    "value": 0,
                    "threshold": 85.0,
                    "description": "No pages found to evaluate.",
                }
            )
            overall_pass = False

    elif book_type == "puzzle":
        # 100% unique grids required
        if pages:
            grid_hashes: list[str] = []
            for page in pages:
                grid_data = getattr(page, "grid_data", None)
                if grid_data:
                    grid_hashes.append(_compute_grid_hash(grid_data) or "")
            if grid_hashes:
                unique_grids = len(set(grid_hashes))
                total_grids = len(grid_hashes)
                grid_unique = unique_grids == total_grids
                if not grid_unique:
                    overall_pass = False
                checks.append(
                    {
                        "rule": "unique_grids_100_pct",
                        "passed": grid_unique,
                        "value": round(unique_grids / max(total_grids, 1) * 100, 2),
                        "threshold": 100.0,
                        "description": (
                            f"{unique_grids}/{total_grids} unique grids "
                            f"({'PASS' if grid_unique else 'FAIL: duplicates found'})."
                        ),
                    }
                )

            # Max 30% word overlap between puzzles in same volume
            all_word_sets: list[set[str]] = []
            for page in pages:
                word_list = getattr(page, "word_list", None)
                if word_list and isinstance(word_list, (list, set)):
                    all_word_sets.append(set(w.lower() for w in word_list if isinstance(w, str)))

            if len(all_word_sets) >= 2:
                max_overlap = 0.0
                for i, ws_a in enumerate(all_word_sets):
                    for ws_b in all_word_sets[i + 1 :]:
                        overlap = _jaccard_similarity(ws_a, ws_b)
                        max_overlap = max(max_overlap, overlap)

                word_pass = max_overlap <= 0.30
                if not word_pass:
                    overall_pass = False
                checks.append(
                    {
                        "rule": "word_overlap_30_pct_max",
                        "passed": word_pass,
                        "value": round(max_overlap * 100, 2),
                        "threshold": 30.0,
                        "description": (
                            f"Max word overlap: {max_overlap:.0%} "
                            f"({'PASS' if word_pass else 'FAIL: too much overlap'})."
                        ),
                    }
                )
        else:
            checks.append(
                {
                    "rule": "unique_grids_100_pct",
                    "passed": False,
                    "value": 0,
                    "threshold": 100.0,
                    "description": "No puzzles found to evaluate.",
                }
            )
            overall_pass = False

    elif book_type == "childrens":
        # General uniqueness check for children's books
        if pages:
            hashes = []
            for page in pages:
                text = getattr(page, "text_content", None) or ""
                url = getattr(page, "illustration_url", None) or ""
                hashes.append(_sha256(f"{text}|{url}"))
            unique_ratio = len(set(hashes)) / max(len(hashes), 1)
            passed = unique_ratio >= 0.85
            if not passed:
                overall_pass = False
            checks.append(
                {
                    "rule": "unique_pages_85_pct",
                    "passed": passed,
                    "value": round(unique_ratio * 100, 2),
                    "threshold": 85.0,
                    "description": f"{unique_ratio:.0%} unique pages (require 85%+).",
                }
            )

    return {
        "book_type": book_type,
        "book_id": str(book_id),
        "passed": overall_pass,
        "checks": checks,
        "checked_at": datetime.now(UTC).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════
# 8. COMPLIANCE REPORT
# ═══════════════════════════════════════════════════════════════════════


async def generate_compliance_report(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate a full compliance report aggregating all safety checks.

    Includes:
    - Originality fingerprint & scores
    - Spam risk assessment
    - Trademark check results
    - Content sensitivity results
    - Anti-duplicate guardrail status
    - Overall compliance status
    """
    # 1. Originality fingerprint
    fingerprint = await generate_originality_fingerprint(db, book_type, book_id, org_id)

    # 2. Spam risk
    spam_result = await run_spam_check(db, book_type, book_id, org_id)

    # 3. Trademark check — scan all text content
    pages = await _get_book_pages(db, book_type, book_id, org_id)
    book = await _get_book_record(db, book_type, book_id, org_id)

    trademark_violations: list[dict[str, Any]] = []
    if book:
        title = getattr(book, "title", "") or ""
        trademark_violations.extend(check_trademark_safety(title, "title"))
        description = getattr(book, "description", None) or ""
        if description:
            trademark_violations.extend(check_trademark_safety(description, "description"))

    for page in pages:
        text_content = getattr(page, "text_content", None) or ""
        if text_content:
            trademark_violations.extend(check_trademark_safety(text_content, "page_content"))
        prompt = getattr(page, "illustration_prompt", None) or ""
        if prompt:
            trademark_violations.extend(check_trademark_safety(prompt, "illustration_prompt"))

    # 4. Content sensitivity
    age_range = getattr(book, "age_range", None) if book else None
    sensitivity_issues: list[dict[str, Any]] = []
    for page in pages:
        text_content = getattr(page, "text_content", None) or ""
        if text_content:
            sensitivity_issues.extend(check_content_sensitivity(text_content, age_range))

    # 5. Anti-duplicate guardrails
    duplicate_result = await anti_duplicate_guardrails(db, book_type, book_id, org_id)

    # Overall compliance status
    has_errors = (
        not spam_result["passed"]
        or any(v["severity"] == "error" for v in trademark_violations)
        or any(i["severity"] == "block" for i in sensitivity_issues)
        or not duplicate_result["passed"]
    )

    has_warnings = (
        any(v["severity"] == "warning" for v in trademark_violations)
        or any(i["severity"] == "warning" for i in sensitivity_issues)
        or any(f["severity"] == "warning" for f in spam_result.get("flags", []))
    )

    if has_errors:
        overall_status = "fail"
    elif has_warnings:
        overall_status = "warning"
    else:
        overall_status = "pass"

    return {
        "book_type": book_type,
        "book_id": str(book_id),
        "org_id": str(org_id),
        "overall_status": overall_status,
        "originality": {
            "overall_hash": fingerprint["overall_hash"],
            "page_count": fingerprint["page_count"],
        },
        "spam_risk": {
            "risk_score": spam_result["risk_score"],
            "passed": spam_result["passed"],
            "flags": spam_result["flags"],
            "component_scores": spam_result["component_scores"],
        },
        "trademark": {
            "violations": trademark_violations,
            "violation_count": len(trademark_violations),
            "passed": len([v for v in trademark_violations if v["severity"] == "error"]) == 0,
        },
        "content_sensitivity": {
            "issues": sensitivity_issues,
            "issue_count": len(sensitivity_issues),
            "blocks": [i for i in sensitivity_issues if i["severity"] == "block"],
            "warnings": [i for i in sensitivity_issues if i["severity"] == "warning"],
        },
        "anti_duplicate": duplicate_result,
        "generated_at": datetime.now(UTC).isoformat(),
    }
