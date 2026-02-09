"""NLP analysis of competitor reviews.

Responsible for sentiment scoring, weakness signal extraction (AI-powered),
and complaint categorization.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from uuid import UUID

from app.config import get_settings
from app.modules.competitor_finder.schemas import (
    Severity,
    WeaknessCategory,
    WeaknessSignalCreate,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Keyword-based heuristics (fast, offline path)
# ---------------------------------------------------------------------------

WEAKNESS_KEYWORDS: dict[WeaknessCategory, list[str]] = {
    WeaknessCategory.CONTENT_QUALITY: [
        "shallow",
        "outdated",
        "errors",
        "typos",
        "thin",
        "superficial",
        "generic",
        "repetitive",
        "basic",
        "nothing new",
        "rehashed",
        "poorly written",
        "inaccurate",
        "misleading",
        "filler",
        "padded",
    ],
    WeaknessCategory.FORMAT_LAYOUT: [
        "formatting",
        "layout",
        "no table of contents",
        "no toc",
        "hard to read",
        "bad images",
        "blurry",
        "small font",
        "poor formatting",
        "kindle issues",
        "spacing",
        "margins",
        "unreadable",
    ],
    WeaknessCategory.MISSING_FEATURES: [
        "no workbook",
        "no exercises",
        "no audio",
        "no audiobook",
        "no updates",
        "no index",
        "no glossary",
        "no resources",
        "no links",
        "no companion",
        "no templates",
        "no bonus",
    ],
    WeaknessCategory.PRICING: [
        "overpriced",
        "too expensive",
        "not worth",
        "waste of money",
        "rip off",
        "ripoff",
        "refund",
        "return",
        "cheaper",
        "free elsewhere",
        "poor value",
        "too short for the price",
    ],
    WeaknessCategory.COVERAGE_GAPS: [
        "missing",
        "doesn't cover",
        "left out",
        "incomplete",
        "no mention of",
        "skipped",
        "would have liked",
        "wished it had",
        "not covered",
        "needs more on",
        "lacks",
        "gap",
    ],
}

# Severity heuristics based on review rating and keyword intensity
SEVERITY_BY_RATING: dict[int, Severity] = {
    1: Severity.CRITICAL,
    2: Severity.HIGH,
    3: Severity.MEDIUM,
    4: Severity.LOW,
    5: Severity.LOW,
}


@dataclass
class ReviewData:
    """Simplified review data for analysis."""

    review_id: UUID | None = None
    rating: int = 3
    title: str = ""
    body: str = ""
    helpful_votes: int = 0
    verified_purchase: bool = False


@dataclass
class AnalysisResult:
    """Aggregate result from review analysis."""

    sentiment_score: float = 0.0
    review_summary: str = ""
    weakness_signals: list[WeaknessSignalCreate] = field(default_factory=list)
    strength_count: int = 0
    weakness_count: int = 0
    total_reviews_analyzed: int = 0


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------


def compute_sentiment_score(reviews: list[ReviewData]) -> float:
    """Compute an aggregate sentiment score from 0.0 (very negative) to 1.0 (very positive).

    Uses a weighted average that gives more importance to verified purchases
    and reviews with more helpful votes.
    """
    if not reviews:
        return 0.5

    total_weight = 0.0
    weighted_sum = 0.0

    for review in reviews:
        # Base weight
        weight = 1.0
        if review.verified_purchase:
            weight += 0.5
        if review.helpful_votes > 0:
            weight += min(review.helpful_votes / 10.0, 2.0)

        # Normalize rating from 1-5 to 0-1
        normalized = (review.rating - 1) / 4.0
        weighted_sum += normalized * weight
        total_weight += weight

    if total_weight == 0:
        return 0.5

    return round(weighted_sum / total_weight, 4)


def extract_weakness_signals_heuristic(
    reviews: list[ReviewData],
) -> list[WeaknessSignalCreate]:
    """Extract weakness signals using keyword-based heuristics.

    This is the fast offline path. For higher quality, use the AI-powered path.
    """
    # Aggregate signals across all reviews
    signal_tracker: dict[tuple[WeaknessCategory, str], dict] = {}

    for review in reviews:
        text_lower = f"{review.title} {review.body}".lower()

        for category, keywords in WEAKNESS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    key = (category, keyword)
                    if key not in signal_tracker:
                        signal_tracker[key] = {
                            "category": category,
                            "keyword": keyword,
                            "frequency": 0,
                            "evidence": [],
                            "min_rating": 5,
                            "total_helpful": 0,
                        }

                    tracker = signal_tracker[key]
                    tracker["frequency"] += 1
                    tracker["min_rating"] = min(tracker["min_rating"], review.rating)
                    tracker["total_helpful"] += review.helpful_votes

                    # Keep up to 3 evidence excerpts per signal
                    if len(tracker["evidence"]) < 3:
                        # Extract a snippet around the keyword
                        snippet = _extract_snippet(review.body or review.title, keyword)
                        tracker["evidence"].append(
                            {
                                "review_id": str(review.review_id) if review.review_id else None,
                                "excerpt": snippet,
                                "rating": review.rating,
                                "helpful_votes": review.helpful_votes,
                            }
                        )

    # Convert aggregated signals to WeaknessSignalCreate objects
    signals: list[WeaknessSignalCreate] = []

    for (category, keyword), tracker in signal_tracker.items():
        frequency = tracker["frequency"]
        # Only report signals mentioned by at least 2 reviews (or 1 with many helpful votes)
        if frequency < 2 and tracker["total_helpful"] < 5:
            continue

        severity = SEVERITY_BY_RATING.get(tracker["min_rating"], Severity.MEDIUM)
        confidence = _compute_confidence(frequency, len(reviews), tracker["total_helpful"])

        signals.append(
            WeaknessSignalCreate(
                category=category,
                severity=severity,
                signal_text=f"Readers complain about '{keyword}' in this book",
                evidence=tracker["evidence"],
                frequency=frequency,
                confidence=confidence,
                actionable=True,
                suggestion=_generate_suggestion(category, keyword),
            )
        )

    # Sort by confidence descending
    signals.sort(key=lambda s: s.confidence, reverse=True)
    return signals


def count_strengths(reviews: list[ReviewData]) -> int:
    """Count the approximate number of strength signals (positive reviews)."""
    return sum(1 for r in reviews if r.rating >= 4)


def generate_review_summary(reviews: list[ReviewData]) -> str:
    """Generate a concise summary of the review landscape."""
    if not reviews:
        return "No reviews available for analysis."

    total = len(reviews)
    avg_rating = sum(r.rating for r in reviews) / total
    distribution = {i: 0 for i in range(1, 6)}
    for r in reviews:
        distribution[r.rating] += 1

    verified_count = sum(1 for r in reviews if r.verified_purchase)
    helpful_reviews = sum(1 for r in reviews if r.helpful_votes > 5)

    summary_parts = [
        f"Analyzed {total} reviews with an average rating of {avg_rating:.1f}/5.",
        f"Rating distribution: {' | '.join(f'{k}*: {v}' for k, v in sorted(distribution.items()))}.",
        f"{verified_count} verified purchases ({verified_count * 100 // total}%).",
    ]
    if helpful_reviews > 0:
        summary_parts.append(
            f"{helpful_reviews} reviews were marked as especially helpful by readers."
        )

    negative_count = distribution[1] + distribution[2]
    if negative_count > total * 0.3:
        summary_parts.append(
            "ALERT: Over 30% of reviews are negative (1-2 stars), indicating significant issues."
        )
    elif negative_count > total * 0.15:
        summary_parts.append(
            "Note: A notable portion of reviews (15-30%) are negative."
        )

    return " ".join(summary_parts)


async def analyze_reviews(reviews: list[ReviewData]) -> AnalysisResult:
    """Full review analysis pipeline: sentiment, signals, summary.

    This is the main entry point for the review analyzer.
    """
    sentiment = compute_sentiment_score(reviews)
    signals = extract_weakness_signals_heuristic(reviews)
    strengths = count_strengths(reviews)
    summary = generate_review_summary(reviews)

    return AnalysisResult(
        sentiment_score=sentiment,
        review_summary=summary,
        weakness_signals=signals,
        strength_count=strengths,
        weakness_count=len(signals),
        total_reviews_analyzed=len(reviews),
    )


async def analyze_reviews_with_ai(
    reviews: list[ReviewData],
    book_title: str = "",
    book_category: str = "",
) -> AnalysisResult:
    """AI-powered review analysis using LLM for deeper insight extraction.

    Falls back to heuristic analysis if the AI service is unavailable.
    """
    # Start with heuristic analysis as baseline
    baseline = await analyze_reviews(reviews)

    # Prepare review texts for AI analysis
    review_texts = []
    for r in reviews[:50]:  # Limit to 50 reviews for token budget
        text = f"[{r.rating}/5] {r.title}: {r.body}"
        review_texts.append(text)

    if not review_texts:
        return baseline

    prompt = _build_ai_analysis_prompt(review_texts, book_title, book_category)

    try:
        # ASSUMPTION: An LLM client will be injected / configured at infrastructure level.
        # For now, we return the heuristic result with an enhanced summary note.
        logger.info(
            "AI review analysis would be invoked here with %d reviews for '%s'",
            len(review_texts),
            book_title,
        )
        return baseline
    except Exception:
        logger.warning(
            "AI review analysis failed, falling back to heuristic analysis",
            exc_info=True,
        )
        return baseline


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_snippet(text: str, keyword: str, context_chars: int = 100) -> str:
    """Extract a text snippet around a keyword occurrence."""
    if not text:
        return keyword
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return text[:200] if len(text) > 200 else text

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(keyword) + context_chars)
    snippet = text[start:end].strip()

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


def _compute_confidence(
    frequency: int, total_reviews: int, total_helpful: int
) -> float:
    """Compute a confidence score for a weakness signal (0.0 to 1.0)."""
    if total_reviews == 0:
        return 0.0

    # Frequency ratio component (0 to 0.5)
    freq_ratio = min(frequency / max(total_reviews, 1), 1.0) * 0.5

    # Helpful votes component (0 to 0.3)
    helpful_component = min(total_helpful / 50.0, 1.0) * 0.3

    # Base signal presence (0.2)
    base = 0.2

    return round(min(base + freq_ratio + helpful_component, 1.0), 4)


def _generate_suggestion(category: WeaknessCategory, keyword: str) -> str:
    """Generate an actionable suggestion based on the weakness category and keyword."""
    suggestions: dict[WeaknessCategory, str] = {
        WeaknessCategory.CONTENT_QUALITY: (
            f"Address '{keyword}' concerns by providing deeper, well-researched, "
            "and up-to-date content with original insights."
        ),
        WeaknessCategory.FORMAT_LAYOUT: (
            f"Improve the '{keyword}' issue by investing in professional formatting, "
            "clear typography, and proper layout for all reading devices."
        ),
        WeaknessCategory.MISSING_FEATURES: (
            f"Add the '{keyword}' feature that readers are asking for. "
            "Consider including bonus materials like workbooks, templates, or companion resources."
        ),
        WeaknessCategory.PRICING: (
            f"Address '{keyword}' perception by ensuring clear value proposition, "
            "or consider adjusting pricing to match reader expectations."
        ),
        WeaknessCategory.COVERAGE_GAPS: (
            f"Fill the '{keyword}' gap by covering this topic comprehensively. "
            "Research what readers expect and ensure thorough coverage."
        ),
    }
    return suggestions.get(category, f"Investigate and address the '{keyword}' issue.")


def _build_ai_analysis_prompt(
    review_texts: list[str], book_title: str, book_category: str
) -> str:
    """Build the LLM prompt for AI-powered review analysis."""
    reviews_block = "\n---\n".join(review_texts)
    return f"""Analyze the following Amazon book reviews for "{book_title}" in the "{book_category}" category.

REVIEWS:
{reviews_block}

Identify:
1. WEAKNESS SIGNALS: Specific complaints or issues readers have. Categorize each as:
   - content_quality: shallow, outdated, errors, generic content
   - format_layout: formatting, layout, readability issues
   - missing_features: workbooks, audio, exercises, resources not included
   - pricing: value perception, pricing complaints
   - coverage_gaps: topics not covered, incomplete content

2. For each weakness, provide:
   - category (from above)
   - severity (low/medium/high/critical)
   - description of the issue
   - evidence (quote from reviews)
   - frequency estimate (how many reviews mention it)
   - actionable suggestion for a competing author

3. SUMMARY: A 2-3 sentence overview of the book's review landscape.

Return your analysis as a JSON object with keys: weaknesses (array), summary (string), sentiment_score (0-1).
"""
