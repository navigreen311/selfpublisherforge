"""Gap detection for cover styles, title patterns, and content coverage.

Analyzes a set of competitor books in a niche to find underserved areas
that a new author can exploit.
"""
from __future__ import annotations

import logging
import os
import re
from collections import Counter
from dataclasses import dataclass, field

from app.config import get_settings
from app.modules.competitor_finder.schemas import (
    ContentGap,
    CoverGap,
    TitleGap,
)

GAP_PRICE_THRESHOLD = float(os.environ.get("GAP_PRICE_THRESHOLD", "0.5"))
GAP_FREQUENCY_THRESHOLD = float(os.environ.get("GAP_FREQUENCY_THRESHOLD", "0.5"))

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class BookData:
    """Simplified book data for gap analysis."""

    title: str = ""
    author: str | None = None
    category: str | None = None
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None
    cover_url: str | None = None
    bsr: int | None = None
    metadata: dict | None = None

    # Review-derived data (optional, for content gap detection)
    review_topics: list[str] = field(default_factory=list)
    review_complaints: list[str] = field(default_factory=list)


@dataclass
class GapAnalysisData:
    """Results of a gap analysis for a niche."""

    cover_gaps: list[CoverGap] = field(default_factory=list)
    title_gaps: list[TitleGap] = field(default_factory=list)
    content_gaps: list[ContentGap] = field(default_factory=list)
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    books_analyzed: int = 0


# ---------------------------------------------------------------------------
# Cover gap detection
# ---------------------------------------------------------------------------

# Common cover style archetypes in self-publishing
COVER_STYLE_ARCHETYPES = [
    "minimalist",
    "photographic",
    "illustrated",
    "typography-focused",
    "dark/moody",
    "bright/colorful",
    "professional/corporate",
    "hand-drawn/artsy",
    "gradient/modern",
    "vintage/classic",
]


def detect_cover_gaps(books: list[BookData]) -> list[CoverGap]:
    """Detect gaps in cover design approaches across a niche.

    Since we work with metadata and URLs (not actual image analysis), this
    focuses on identifiable patterns and known archetypes.
    """
    if not books:
        logger.warning("detect_cover_gaps called with empty book list — no data to analyze")
        return []

    gaps: list[CoverGap] = []
    total = len(books)

    # Check if any books lack covers
    books_without_covers = [b for b in books if not b.cover_url]
    if books_without_covers:
        gaps.append(
            CoverGap(
                gap_type="missing_covers",
                description=(
                    f"{len(books_without_covers)} of {total} books have no cover image. "
                    "A professional cover immediately differentiates your book."
                ),
                prevalence=len(books_without_covers) / total,
                opportunity="Stand out by investing in a professional, eye-catching cover design.",
            )
        )

    # Analyze title keywords for cover style hints
    title_words = _collect_title_words(books)

    # Check for overused patterns (opportunity to stand out)
    if total >= 5:
        # If most titles are very similar, there's a differentiation opportunity
        common_words = Counter(title_words).most_common(5)
        overused = [w for w, c in common_words if c > total * GAP_FREQUENCY_THRESHOLD and len(w) > 3]
        if overused:
            gaps.append(
                CoverGap(
                    gap_type="visual_sameness",
                    description=(
                        f"Most books in this niche use similar themes around: {', '.join(overused)}. "
                        "Covers likely look very similar."
                    ),
                    prevalence=0.7,
                    opportunity=(
                        "Use a contrasting visual style to stand out in search results. "
                        "If most covers are dark, go bright. If photographic, try illustrated."
                    ),
                )
            )

    # Check price-cover correlation (cheap books often have bad covers)
    priced_books = [b for b in books if b.price is not None]
    if priced_books:
        avg_price = sum(b.price for b in priced_books) / len(priced_books)  # type: ignore[arg-type]
        cheap_books = [b for b in priced_books if (b.price or 0) < avg_price * GAP_PRICE_THRESHOLD]
        if len(cheap_books) > total * 0.3:
            gaps.append(
                CoverGap(
                    gap_type="premium_positioning",
                    description=(
                        f"Over 30% of books are priced below ${avg_price * GAP_PRICE_THRESHOLD:.2f}. "
                        "Many cheap books have low-quality covers."
                    ),
                    prevalence=len(cheap_books) / total,
                    opportunity=(
                        "Position with a premium cover design to signal quality and "
                        "justify a higher price point."
                    ),
                )
            )

    return gaps


# ---------------------------------------------------------------------------
# Title gap detection
# ---------------------------------------------------------------------------

TITLE_POWER_WORDS = [
    "complete",
    "ultimate",
    "definitive",
    "essential",
    "comprehensive",
    "practical",
    "step-by-step",
    "beginner",
    "advanced",
    "master",
    "secrets",
    "guide",
    "handbook",
    "blueprint",
    "framework",
    "system",
    "proven",
    "simple",
]

TITLE_PATTERNS = {
    "how_to": r"how\s+to",
    "number_list": r"\d+\s+(ways|tips|steps|secrets|strategies|lessons|rules|habits)",
    "question": r"^(why|what|how|when|where|who)\s",
    "the_x_of_y": r"the\s+\w+\s+of\s+\w+",
    "for_audience": r"for\s+(beginners|dummies|experts|entrepreneurs|women|men|kids|teens)",
    "year_edition": r"20\d{2}",
    "with_bonus": r"(bonus|free|included|companion|workbook)",
}


def detect_title_gaps(books: list[BookData]) -> list[TitleGap]:
    """Detect underused title patterns and missing keywords in a niche."""
    if not books:
        logger.warning("detect_title_gaps called with empty book list — no data to analyze")
        return []

    gaps: list[TitleGap] = []
    total = len(books)
    titles = [b.title.lower() for b in books]

    # Check which power words are underused
    word_usage: dict[str, int] = {}
    for word in TITLE_POWER_WORDS:
        count = sum(1 for t in titles if word in t)
        word_usage[word] = count

    underused = [w for w, c in word_usage.items() if c == 0]
    if underused:
        gaps.append(
            TitleGap(
                gap_type="missing_power_words",
                description=(
                    f"None of the {total} titles use these powerful keywords: "
                    f"{', '.join(underused[:8])}"
                ),
                missing_keywords=underused[:8],
                opportunity=(
                    "Incorporate underused power words in your title or subtitle "
                    "to capture different search intents."
                ),
            )
        )

    # Check which title patterns are underused
    for pattern_name, regex in TITLE_PATTERNS.items():
        matches = sum(1 for t in titles if re.search(regex, t, re.IGNORECASE))
        if matches == 0:
            gaps.append(
                TitleGap(
                    gap_type=f"missing_pattern_{pattern_name}",
                    description=(
                        f"No titles use the '{pattern_name.replace('_', ' ')}' pattern. "
                        "This could be an untapped angle."
                    ),
                    missing_keywords=[],
                    opportunity=(
                        f"Consider using the '{pattern_name.replace('_', ' ')}' title structure "
                        "to differentiate and capture unique search queries."
                    ),
                )
            )
        elif matches < total * 0.1 and total >= 5:
            gaps.append(
                TitleGap(
                    gap_type=f"rare_pattern_{pattern_name}",
                    description=(
                        f"Only {matches} of {total} titles use the "
                        f"'{pattern_name.replace('_', ' ')}' pattern."
                    ),
                    missing_keywords=[],
                    opportunity=(
                        f"The '{pattern_name.replace('_', ' ')}' pattern is underused, "
                        "presenting a differentiation opportunity."
                    ),
                )
            )

    # Check subtitle usage
    titles_with_colon = sum(1 for t in titles if ":" in t)
    if titles_with_colon < total * 0.3:
        gaps.append(
            TitleGap(
                gap_type="subtitle_opportunity",
                description=(
                    f"Only {titles_with_colon} of {total} books use subtitles (colon-separated). "
                    "Subtitles add keyword richness and clarify the value proposition."
                ),
                missing_keywords=[],
                opportunity=(
                    "Add a subtitle to improve search visibility and communicate "
                    "your book's unique value."
                ),
            )
        )

    return gaps


# ---------------------------------------------------------------------------
# Content gap detection
# ---------------------------------------------------------------------------


def detect_content_gaps(
    books: list[BookData],
    niche: str = "",
) -> list[ContentGap]:
    """Detect content coverage gaps across competitor books.

    Uses review-derived topics and complaints to identify underserved content areas.
    """
    if not books:
        logger.warning("detect_content_gaps called with empty book list — no data to analyze")
        return []

    gaps: list[ContentGap] = []
    total = len(books)

    # Aggregate all review topics and complaints
    all_topics: list[str] = []
    all_complaints: list[str] = []
    for book in books:
        all_topics.extend(book.review_topics)
        all_complaints.extend(book.review_complaints)

    # Find topics that appear in complaints but not well-covered
    complaint_counter = Counter(all_complaints)
    topic_counter = Counter(all_topics)

    for complaint, count in complaint_counter.most_common(10):
        if count >= 2:
            # Check if this topic is well-covered
            coverage = topic_counter.get(complaint, 0) / max(total, 1)
            if coverage < GAP_FREQUENCY_THRESHOLD:
                gaps.append(
                    ContentGap(
                        topic=complaint,
                        description=(
                            f"Readers frequently mention '{complaint}' as missing or insufficient "
                            f"({count} mentions across reviews)."
                        ),
                        demand_signal=f"Mentioned in {count} review complaints",
                        competitor_coverage=coverage,
                    )
                )

    # Check for rating-based content quality gaps
    rated_books = [b for b in books if b.rating is not None]
    if rated_books:
        avg_rating = sum(b.rating for b in rated_books) / len(rated_books)  # type: ignore[arg-type]
        if avg_rating < 4.0:
            gaps.append(
                ContentGap(
                    topic="overall_quality",
                    description=(
                        f"Average rating in this niche is {avg_rating:.1f}/5, indicating "
                        "general reader dissatisfaction with content quality."
                    ),
                    demand_signal="Low average niche rating",
                    competitor_coverage=0.0,
                )
            )

    # Check for price-content mismatch opportunities
    priced_books = [b for b in books if b.price is not None and b.rating is not None]
    if priced_books:
        high_price_low_rating = [
            b for b in priced_books
            if (b.price or 0) > 14.99 and (b.rating or 5) < 4.0
        ]
        if high_price_low_rating:
            gaps.append(
                ContentGap(
                    topic="value_gap",
                    description=(
                        f"{len(high_price_low_rating)} books are priced above $14.99 "
                        "but rated below 4.0 stars, indicating a value gap."
                    ),
                    demand_signal="High price + low rating = opportunity",
                    competitor_coverage=len(high_price_low_rating) / total,
                )
            )

    return gaps


# ---------------------------------------------------------------------------
# Full gap analysis
# ---------------------------------------------------------------------------


async def run_gap_analysis(
    books: list[BookData],
    niche: str = "",
    category: str | None = None,
) -> GapAnalysisData:
    """Run a complete gap analysis across cover, title, and content dimensions."""
    cover_gaps = detect_cover_gaps(books)
    title_gaps = detect_title_gaps(books)
    content_gaps = detect_content_gaps(books, niche=niche)

    recommendations = _build_recommendations(cover_gaps, title_gaps, content_gaps)
    summary = _build_summary(books, cover_gaps, title_gaps, content_gaps, niche)

    return GapAnalysisData(
        cover_gaps=cover_gaps,
        title_gaps=title_gaps,
        content_gaps=content_gaps,
        summary=summary,
        recommendations=recommendations,
        books_analyzed=len(books),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _collect_title_words(books: list[BookData]) -> list[str]:
    """Collect all meaningful words from book titles."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "that", "this", "your", "my",
        "how", "what", "why", "when", "where", "who", "which", "be", "are",
    }
    words = []
    for book in books:
        for word in re.findall(r"\b[a-zA-Z]+\b", book.title.lower()):
            if word not in stop_words and len(word) > 2:
                words.append(word)
    return words


def _build_recommendations(
    cover_gaps: list[CoverGap],
    title_gaps: list[TitleGap],
    content_gaps: list[ContentGap],
) -> list[str]:
    """Build prioritized recommendations from all gap types."""
    recs: list[str] = []

    # Content gaps are highest priority
    for gap in content_gaps[:3]:
        if gap.competitor_coverage < 0.3:
            recs.append(f"HIGH PRIORITY - Content: {gap.description}")

    # Cover gaps
    for cover_gap in cover_gaps[:2]:
        if cover_gap.opportunity:
            recs.append(f"Cover: {cover_gap.opportunity}")

    # Title gaps
    for title_gap in title_gaps[:2]:
        if title_gap.opportunity:
            recs.append(f"Title: {title_gap.opportunity}")

    if not recs:
        recs.append(
            "This niche appears well-served. Focus on execution quality "
            "and unique perspective to differentiate."
        )

    return recs


def _build_summary(
    books: list[BookData],
    cover_gaps: list[CoverGap],
    title_gaps: list[TitleGap],
    content_gaps: list[ContentGap],
    niche: str,
) -> str:
    """Build a concise summary of the gap analysis."""
    total_gaps = len(cover_gaps) + len(title_gaps) + len(content_gaps)
    total_books = len(books)

    if total_gaps == 0:
        return (
            f"Analysis of {total_books} books in '{niche}' reveals a competitive niche "
            "with few obvious gaps. Success will depend on superior execution."
        )

    parts = [
        f"Analysis of {total_books} books in '{niche}' identified {total_gaps} gaps:"
    ]
    if cover_gaps:
        parts.append(f"{len(cover_gaps)} cover design opportunities")
    if title_gaps:
        parts.append(f"{len(title_gaps)} title/keyword opportunities")
    if content_gaps:
        parts.append(f"{len(content_gaps)} content coverage gaps")

    return " | ".join(parts) + "."
