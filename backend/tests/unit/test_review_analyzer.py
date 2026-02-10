"""Unit tests for the review analyzer module."""
import uuid

import pytest

from app.modules.competitor_finder.review_analyzer import (
    AnalysisResult,
    ReviewData,
    _compute_confidence,
    _extract_snippet,
    _generate_suggestion,
    analyze_reviews,
    compute_sentiment_score,
    count_strengths,
    extract_weakness_signals_heuristic,
    generate_review_summary,
)
from app.modules.competitor_finder.schemas import (
    Severity,
    WeaknessCategory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_review(
    rating: int = 3,
    title: str = "",
    body: str = "",
    helpful_votes: int = 0,
    verified: bool = True,
) -> ReviewData:
    return ReviewData(
        review_id=uuid.uuid4(),
        rating=rating,
        title=title,
        body=body,
        helpful_votes=helpful_votes,
        verified_purchase=verified,
    )


# ---------------------------------------------------------------------------
# compute_sentiment_score
# ---------------------------------------------------------------------------

class TestComputeSentimentScore:
    def test_empty_reviews_returns_neutral(self):
        assert compute_sentiment_score([]) == 0.5

    def test_all_five_star_returns_high(self):
        reviews = [_make_review(rating=5) for _ in range(10)]
        score = compute_sentiment_score(reviews)
        assert score == 1.0

    def test_all_one_star_returns_low(self):
        reviews = [_make_review(rating=1) for _ in range(10)]
        score = compute_sentiment_score(reviews)
        assert score == 0.0

    def test_mixed_ratings_returns_mid(self):
        reviews = [
            _make_review(rating=1),
            _make_review(rating=2),
            _make_review(rating=3),
            _make_review(rating=4),
            _make_review(rating=5),
        ]
        score = compute_sentiment_score(reviews)
        assert 0.3 < score < 0.7

    def test_verified_purchase_weighted_higher(self):
        # All same rating but different verification status
        verified = [_make_review(rating=5, verified=True) for _ in range(5)]
        unverified = [_make_review(rating=1, verified=False) for _ in range(5)]
        # Verified 5-star reviews should pull score up more
        score = compute_sentiment_score(verified + unverified)
        assert score > 0.5

    def test_helpful_votes_increase_weight(self):
        # Helpful high-rating reviews should pull the score up
        helpful_good = [_make_review(rating=5, helpful_votes=50) for _ in range(2)]
        unhelpful_bad = [_make_review(rating=1, helpful_votes=0) for _ in range(2)]
        score = compute_sentiment_score(helpful_good + unhelpful_bad)
        assert score > 0.5

    def test_returns_between_0_and_1(self):
        reviews = [_make_review(rating=r) for r in [1, 2, 3, 4, 5, 1, 5]]
        score = compute_sentiment_score(reviews)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# extract_weakness_signals_heuristic
# ---------------------------------------------------------------------------

class TestExtractWeaknessSignals:
    def test_empty_reviews_returns_empty(self):
        signals = extract_weakness_signals_heuristic([])
        assert signals == []

    def test_detects_content_quality_issues(self):
        reviews = [
            _make_review(rating=2, body="This book is very shallow and has nothing new."),
            _make_review(rating=1, body="Extremely shallow content, just rehashed stuff."),
            _make_review(rating=2, body="Shallow and outdated information."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        categories = [s.category for s in signals]
        assert WeaknessCategory.CONTENT_QUALITY in categories

    def test_detects_format_layout_issues(self):
        reviews = [
            _make_review(rating=2, body="The formatting is terrible, no table of contents."),
            _make_review(rating=1, body="Poor formatting and hard to read on Kindle."),
            _make_review(rating=2, body="Bad formatting throughout the book."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        categories = [s.category for s in signals]
        assert WeaknessCategory.FORMAT_LAYOUT in categories

    def test_detects_missing_features(self):
        reviews = [
            _make_review(rating=3, body="No workbook included. Very disappointing."),
            _make_review(rating=2, body="No workbook or companion materials at all."),
            _make_review(rating=3, body="I expected a no workbook disclaimer but there literally is no workbook."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        categories = [s.category for s in signals]
        assert WeaknessCategory.MISSING_FEATURES in categories

    def test_detects_pricing_complaints(self):
        reviews = [
            _make_review(rating=1, body="This book is way overpriced for the content."),
            _make_review(rating=2, body="Way too overpriced, not worth it."),
            _make_review(rating=1, body="Overpriced for what you get."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        categories = [s.category for s in signals]
        assert WeaknessCategory.PRICING in categories

    def test_detects_coverage_gaps(self):
        reviews = [
            _make_review(rating=3, body="The book is incomplete. It doesn't cover advanced topics."),
            _make_review(rating=2, body="Feels really incomplete, left out important parts."),
            _make_review(rating=3, body="Incomplete coverage of the subject."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        categories = [s.category for s in signals]
        assert WeaknessCategory.COVERAGE_GAPS in categories

    def test_ignores_infrequent_signals(self):
        # Only one review with the keyword - should be ignored (threshold is 2 or high helpful)
        reviews = [
            _make_review(rating=3, body="The book is a bit shallow."),
            _make_review(rating=4, body="Great book, learned a lot!"),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        # Shallow appears only once and no high helpful votes
        shallow_signals = [s for s in signals if "shallow" in s.signal_text.lower()]
        assert len(shallow_signals) == 0

    def test_multiple_categories_detected(self):
        reviews = [
            _make_review(rating=1, body="Shallow content with poor formatting throughout."),
            _make_review(rating=2, body="Shallow and poor formatting. Hard to read."),
            _make_review(rating=1, body="Very shallow book, poor formatting makes it worse."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        categories = set(s.category for s in signals)
        assert len(categories) >= 2

    def test_signals_sorted_by_confidence_descending(self):
        reviews = [
            _make_review(rating=1, body="Shallow content everywhere.", helpful_votes=20),
            _make_review(rating=2, body="Very shallow.", helpful_votes=15),
            _make_review(rating=1, body="Overpriced!"),
            _make_review(rating=2, body="Overpriced for what you get."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        if len(signals) >= 2:
            for i in range(len(signals) - 1):
                assert signals[i].confidence >= signals[i + 1].confidence

    def test_signal_has_evidence(self):
        reviews = [
            _make_review(rating=2, body="This is very shallow content."),
            _make_review(rating=1, body="Shallow and not worth buying."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        for signal in signals:
            if signal.evidence:
                assert len(signal.evidence) > 0
                assert "excerpt" in signal.evidence[0]

    def test_signal_has_suggestion(self):
        reviews = [
            _make_review(rating=2, body="Content is shallow and generic."),
            _make_review(rating=1, body="Too shallow for the topic."),
        ]
        signals = extract_weakness_signals_heuristic(reviews)
        for signal in signals:
            assert signal.suggestion is not None
            assert len(signal.suggestion) > 0


# ---------------------------------------------------------------------------
# count_strengths
# ---------------------------------------------------------------------------

class TestCountStrengths:
    def test_counts_4_and_5_star_reviews(self):
        reviews = [
            _make_review(rating=1),
            _make_review(rating=2),
            _make_review(rating=3),
            _make_review(rating=4),
            _make_review(rating=5),
        ]
        assert count_strengths(reviews) == 2

    def test_all_low_ratings_returns_zero(self):
        reviews = [_make_review(rating=r) for r in [1, 2, 3]]
        assert count_strengths(reviews) == 0

    def test_empty_returns_zero(self):
        assert count_strengths([]) == 0


# ---------------------------------------------------------------------------
# generate_review_summary
# ---------------------------------------------------------------------------

class TestGenerateReviewSummary:
    def test_empty_reviews(self):
        summary = generate_review_summary([])
        assert "No reviews" in summary

    def test_contains_count_and_average(self):
        reviews = [_make_review(rating=4), _make_review(rating=3)]
        summary = generate_review_summary(reviews)
        assert "2 reviews" in summary
        assert "3.5" in summary

    def test_flags_high_negative_ratio(self):
        reviews = [_make_review(rating=1) for _ in range(4)] + [_make_review(rating=5)]
        summary = generate_review_summary(reviews)
        assert "ALERT" in summary or "negative" in summary.lower()

    def test_includes_verified_count(self):
        reviews = [_make_review(rating=4, verified=True) for _ in range(3)]
        summary = generate_review_summary(reviews)
        assert "verified" in summary.lower()


# ---------------------------------------------------------------------------
# analyze_reviews (async)
# ---------------------------------------------------------------------------

class TestAnalyzeReviews:
    @pytest.mark.asyncio
    async def test_returns_analysis_result(self):
        reviews = [
            _make_review(rating=2, body="Shallow content, very disappointing."),
            _make_review(rating=1, body="Extremely shallow. Waste of money."),
            _make_review(rating=4, body="Pretty good book overall."),
        ]
        result = await analyze_reviews(reviews)
        assert isinstance(result, AnalysisResult)
        assert result.total_reviews_analyzed == 3
        assert result.sentiment_score > 0
        assert isinstance(result.review_summary, str)

    @pytest.mark.asyncio
    async def test_empty_reviews(self):
        result = await analyze_reviews([])
        assert result.total_reviews_analyzed == 0
        assert result.sentiment_score == 0.5


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestExtractSnippet:
    def test_keyword_in_middle(self):
        text = "This is a test where the shallow keyword appears in the middle of text."
        snippet = _extract_snippet(text, "shallow")
        assert "shallow" in snippet

    def test_keyword_not_found_returns_text(self):
        text = "A normal review without the target keyword."
        snippet = _extract_snippet(text, "nonexistent")
        assert snippet == text

    def test_empty_text_returns_keyword(self):
        assert _extract_snippet("", "test") == "test"

    def test_long_text_truncated_with_ellipsis(self):
        text = "x" * 50 + " shallow " + "y" * 200
        snippet = _extract_snippet(text, "shallow", context_chars=20)
        assert "..." in snippet


class TestComputeConfidence:
    def test_zero_reviews_returns_zero(self):
        assert _compute_confidence(0, 0, 0) == 0.0

    def test_high_frequency_high_helpful(self):
        score = _compute_confidence(10, 20, 100)
        assert score > 0.5

    def test_low_frequency_low_helpful(self):
        score = _compute_confidence(1, 100, 0)
        assert score < 0.5

    def test_bounded_between_0_and_1(self):
        score = _compute_confidence(1000, 10, 1000)
        assert 0.0 <= score <= 1.0


class TestGenerateSuggestion:
    def test_content_quality_suggestion(self):
        suggestion = _generate_suggestion(WeaknessCategory.CONTENT_QUALITY, "shallow")
        assert "shallow" in suggestion
        assert len(suggestion) > 20

    def test_format_layout_suggestion(self):
        suggestion = _generate_suggestion(WeaknessCategory.FORMAT_LAYOUT, "formatting")
        assert "formatting" in suggestion

    def test_pricing_suggestion(self):
        suggestion = _generate_suggestion(WeaknessCategory.PRICING, "overpriced")
        assert "overpriced" in suggestion
