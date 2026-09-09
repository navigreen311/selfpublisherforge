"""KDP Spam Risk Detector.

Analyses a book for characteristics that may trigger KDP's anti-spam
systems: near-duplicate interiors, keyword-stuffed metadata, minor-edit
clones, and low unique-content ratios.

Blueprint refs: 7.2, 7.4
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.shared import (
    ContentFingerprint,
)
from app.modules.specialty.shared.fingerprinting import (
    cross_book_comparison,
)

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class SpamRiskReport:
    """Full spam risk analysis for a single book."""

    spam_risk_score: float  # 0-100
    risk_factors: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    safe_to_publish: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "spam_risk_score": self.spam_risk_score,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "safe_to_publish": self.safe_to_publish,
        }


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# If a book is >60% similar to any existing book, flag as high-risk
_INTERIOR_SIMILARITY_THRESHOLD = 0.60

# If a book is <15% different from another, flag as minor-edit clone
_MINOR_EDIT_THRESHOLD = 0.85  # similarity > 85% means < 15% different

# Minimum unique content thresholds
_COLORING_UNIQUE_PAGE_THRESHOLD = 0.85
_PUZZLE_UNIQUE_GRID_THRESHOLD = 1.0

# Metadata quality
_MAX_KEYWORDS_IN_TITLE = 4  # More than this suggests keyword stuffing
_MIN_DESCRIPTION_LENGTH = 50  # Characters
_KEYWORD_STUFF_PATTERN = re.compile(
    r"(\b\w+\b)(?:\s*[,|/]\s*\1){2,}", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Internal checks
# ---------------------------------------------------------------------------

async def _check_interior_originality(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_id: uuid.UUID,
) -> tuple[float, list[dict[str, Any]], list[str]]:
    """Compare book interior against all org books.

    Returns (penalty_points, risk_factors, recommendations).
    """
    comparisons = await cross_book_comparison(db, org_id, book_id)

    penalty = 0.0
    factors: list[dict[str, Any]] = []
    recs: list[str] = []

    for other_id, similarity in comparisons:
        if similarity > _INTERIOR_SIMILARITY_THRESHOLD:
            penalty += 30.0
            factors.append(
                {
                    "check": "interior_originality",
                    "severity": "high",
                    "detail": (
                        f"Book is {similarity:.0%} similar to book "
                        f"{other_id} (threshold: {_INTERIOR_SIMILARITY_THRESHOLD:.0%})"
                    ),
                    "other_book_id": str(other_id),
                    "similarity": round(similarity, 3),
                }
            )
            recs.append(
                f"Book is too similar to an existing book ({other_id}). "
                "Add significantly more unique content before publishing."
            )

        if similarity > _MINOR_EDIT_THRESHOLD:
            penalty += 25.0
            factors.append(
                {
                    "check": "minor_edit_detection",
                    "severity": "critical",
                    "detail": (
                        f"Book appears to be a minor edit of book "
                        f"{other_id} ({similarity:.0%} similar, "
                        f"<{1 - _MINOR_EDIT_THRESHOLD:.0%} different)"
                    ),
                    "other_book_id": str(other_id),
                    "similarity": round(similarity, 3),
                }
            )
            recs.append(
                "This book may be flagged as a minor-edit clone. "
                "KDP requires substantially different content between publications."
            )

    return min(penalty, 55.0), factors, recs


def _check_metadata_quality(
    title: str = "",
    keywords: list[str] | None = None,
    description: str = "",
) -> tuple[float, list[dict[str, Any]], list[str]]:
    """Assess metadata for spam signals.

    Returns (penalty_points, risk_factors, recommendations).
    """
    penalty = 0.0
    factors: list[dict[str, Any]] = []
    recs: list[str] = []

    # Title keyword stuffing: count comma/pipe-separated words
    title_words = re.split(r"[,|/\-–—]", title)
    if len(title_words) > _MAX_KEYWORDS_IN_TITLE:
        penalty += 15.0
        factors.append(
            {
                "check": "metadata_keyword_stuffing",
                "severity": "medium",
                "detail": (
                    f"Title contains {len(title_words)} keyword segments "
                    f"(max recommended: {_MAX_KEYWORDS_IN_TITLE})"
                ),
            }
        )
        recs.append(
            "Simplify the title. Keyword-stuffed titles are a common "
            "spam signal for KDP."
        )

    # Repeated keyword pattern
    if _KEYWORD_STUFF_PATTERN.search(title):
        penalty += 10.0
        factors.append(
            {
                "check": "metadata_repeated_keywords",
                "severity": "medium",
                "detail": "Title contains repeated keyword patterns.",
            }
        )
        recs.append("Remove repeated keywords from the title.")

    # Description too short
    if description and len(description.strip()) < _MIN_DESCRIPTION_LENGTH:
        penalty += 5.0
        factors.append(
            {
                "check": "metadata_thin_description",
                "severity": "low",
                "detail": (
                    f"Description is only {len(description.strip())} characters "
                    f"(minimum recommended: {_MIN_DESCRIPTION_LENGTH})"
                ),
            }
        )
        recs.append(
            "Write a more detailed description (at least 50 characters)."
        )
    elif not description:
        penalty += 5.0
        factors.append(
            {
                "check": "metadata_missing_description",
                "severity": "low",
                "detail": "No description provided.",
            }
        )
        recs.append("Add a book description before publishing.")

    # Title uniqueness (basic: flag extremely short generic titles)
    stripped_title = title.strip()
    if stripped_title and len(stripped_title) < 5:
        penalty += 5.0
        factors.append(
            {
                "check": "metadata_generic_title",
                "severity": "low",
                "detail": "Title is very short and may lack uniqueness.",
            }
        )
        recs.append("Use a more specific and descriptive title.")

    return min(penalty, 25.0), factors, recs


async def _check_content_substance(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    org_id: uuid.UUID,
) -> tuple[float, list[dict[str, Any]], list[str]]:
    """Check minimum unique content thresholds by book type.

    Returns (penalty_points, risk_factors, recommendations).
    """
    penalty = 0.0
    factors: list[dict[str, Any]] = []
    recs: list[str] = []

    # Count fingerprints for this book
    total_stmt = (
        select(func.count())
        .select_from(ContentFingerprint)
        .where(
            ContentFingerprint.org_id == org_id,
            ContentFingerprint.book_id == book_id,
        )
    )
    total_result = await db.execute(total_stmt)
    total_count = total_result.scalar() or 0

    if total_count == 0:
        # No fingerprints yet -- cannot assess
        return 0.0, factors, recs

    # Count distinct fingerprints (unique content)
    if book_type == "coloring":
        unique_stmt = (
            select(func.count(func.distinct(ContentFingerprint.phash)))
            .select_from(ContentFingerprint)
            .where(
                ContentFingerprint.org_id == org_id,
                ContentFingerprint.book_id == book_id,
                ContentFingerprint.content_type == "images",
            )
        )
        unique_result = await db.execute(unique_stmt)
        unique_count = unique_result.scalar() or 0
        unique_ratio = unique_count / total_count if total_count else 1.0

        if unique_ratio < _COLORING_UNIQUE_PAGE_THRESHOLD:
            penalty += 20.0
            factors.append(
                {
                    "check": "content_substance_coloring",
                    "severity": "high",
                    "detail": (
                        f"Only {unique_ratio:.0%} of pages are unique "
                        f"(minimum {_COLORING_UNIQUE_PAGE_THRESHOLD:.0%} required)"
                    ),
                    "unique_ratio": round(unique_ratio, 3),
                }
            )
            recs.append(
                f"Coloring books must have at least "
                f"{_COLORING_UNIQUE_PAGE_THRESHOLD:.0%} unique pages. "
                f"Replace duplicate pages with new designs."
            )

    elif book_type == "puzzle":
        unique_stmt = (
            select(func.count(func.distinct(ContentFingerprint.data_hash)))
            .select_from(ContentFingerprint)
            .where(
                ContentFingerprint.org_id == org_id,
                ContentFingerprint.book_id == book_id,
                ContentFingerprint.content_type == "puzzle_grids",
            )
        )
        unique_result = await db.execute(unique_stmt)
        unique_count = unique_result.scalar() or 0
        unique_ratio = unique_count / total_count if total_count else 1.0

        if unique_ratio < _PUZZLE_UNIQUE_GRID_THRESHOLD:
            penalty += 20.0
            factors.append(
                {
                    "check": "content_substance_puzzle",
                    "severity": "critical",
                    "detail": (
                        f"Only {unique_ratio:.0%} of puzzle grids are unique "
                        f"(100% unique grids required)"
                    ),
                    "unique_ratio": round(unique_ratio, 3),
                }
            )
            recs.append(
                "Puzzle books must have 100% unique grids. "
                "Regenerate any duplicate puzzles."
            )

    return min(penalty, 20.0), factors, recs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def calculate_spam_risk(
    db: AsyncSession,
    book_type: str,
    book_id: uuid.UUID,
    *,
    org_id: uuid.UUID | None = None,
    title: str = "",
    keywords: list[str] | None = None,
    description: str = "",
) -> SpamRiskReport:
    """Run full KDP spam risk analysis on a book.

    Parameters
    ----------
    db:
        Async database session.
    book_type:
        One of ``"childrens"``, ``"coloring"``, ``"puzzle"``.
    book_id:
        The book to analyse.
    org_id:
        Organisation / tenant ID.  If not provided, interior originality
        and content substance checks are skipped.
    title:
        Book title for metadata quality checks.
    keywords:
        KDP keywords for metadata quality checks.
    description:
        Book description for metadata quality checks.

    Returns
    -------
    SpamRiskReport
        Contains ``spam_risk_score`` (0-100), ``risk_factors``,
        ``recommendations``, and ``safe_to_publish`` (True if score < 50).
    """
    total_penalty = 0.0
    all_factors: list[dict[str, Any]] = []
    all_recs: list[str] = []

    # 1. Metadata quality (always available)
    meta_penalty, meta_factors, meta_recs = _check_metadata_quality(
        title=title, keywords=keywords, description=description
    )
    total_penalty += meta_penalty
    all_factors.extend(meta_factors)
    all_recs.extend(meta_recs)

    # 2. Interior originality (requires org_id)
    if org_id is not None:
        orig_penalty, orig_factors, orig_recs = await _check_interior_originality(
            db, org_id, book_id
        )
        total_penalty += orig_penalty
        all_factors.extend(orig_factors)
        all_recs.extend(orig_recs)

    # 3. Content substance (requires org_id)
    if org_id is not None:
        subst_penalty, subst_factors, subst_recs = await _check_content_substance(
            db, book_type, book_id, org_id
        )
        total_penalty += subst_penalty
        all_factors.extend(subst_factors)
        all_recs.extend(subst_recs)

    # Clamp to 0-100
    spam_score = min(max(total_penalty, 0.0), 100.0)

    return SpamRiskReport(
        spam_risk_score=round(spam_score, 1),
        risk_factors=all_factors,
        recommendations=all_recs,
        safe_to_publish=spam_score < 50.0,
    )
