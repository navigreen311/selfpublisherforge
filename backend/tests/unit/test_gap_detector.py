"""Unit tests for the gap detector module."""

import pytest

from app.modules.competitor_finder.gap_detector import (
    BookData,
    GapAnalysisData,
    detect_content_gaps,
    detect_cover_gaps,
    detect_title_gaps,
    run_gap_analysis,
)
from app.modules.competitor_finder.schemas import ContentGap, CoverGap, TitleGap

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_book(
    title: str = "Test Book",
    author: str = "Test Author",
    price: float | None = 9.99,
    rating: float | None = 4.0,
    review_count: int = 100,
    cover_url: str | None = "https://example.com/cover.jpg",
    bsr: int | None = 5000,
    category: str = "Self-Help",
    review_topics: list[str] | None = None,
    review_complaints: list[str] | None = None,
) -> BookData:
    return BookData(
        title=title,
        author=author,
        price=price,
        rating=rating,
        review_count=review_count,
        cover_url=cover_url,
        bsr=bsr,
        category=category,
        review_topics=review_topics or [],
        review_complaints=review_complaints or [],
    )


# ---------------------------------------------------------------------------
# detect_cover_gaps
# ---------------------------------------------------------------------------


class TestDetectCoverGaps:
    def test_empty_books_returns_empty(self):
        gaps = detect_cover_gaps([])
        assert gaps == []

    def test_detects_missing_covers(self):
        books = [
            _make_book(cover_url=None),
            _make_book(cover_url=None),
            _make_book(cover_url="https://example.com/cover.jpg"),
        ]
        gaps = detect_cover_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "missing_covers" in gap_types

    def test_no_missing_cover_gap_when_all_have_covers(self):
        books = [_make_book() for _ in range(5)]
        gaps = detect_cover_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "missing_covers" not in gap_types

    def test_detects_visual_sameness(self):
        # Many books with overlapping title words suggest visual similarity
        books = [
            _make_book(title="Self-Discipline Mastery Guide"),
            _make_book(title="Self-Discipline Handbook"),
            _make_book(title="Self-Discipline for Success"),
            _make_book(title="Self-Discipline Made Easy"),
            _make_book(title="Self-Discipline Blueprint"),
            _make_book(title="Self-Discipline Secrets"),
        ]
        gaps = detect_cover_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "visual_sameness" in gap_types

    def test_detects_premium_positioning_opportunity(self):
        # Many cheap books = opportunity for premium positioning
        books = [
            _make_book(price=2.99),
            _make_book(price=3.99),
            _make_book(price=1.99),
            _make_book(price=2.49),
            _make_book(price=19.99),
        ]
        gaps = detect_cover_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "premium_positioning" in gap_types

    def test_returns_cover_gap_objects(self):
        books = [_make_book(cover_url=None), _make_book()]
        gaps = detect_cover_gaps(books)
        for gap in gaps:
            assert isinstance(gap, CoverGap)
            assert gap.gap_type
            assert gap.description


# ---------------------------------------------------------------------------
# detect_title_gaps
# ---------------------------------------------------------------------------


class TestDetectTitleGaps:
    def test_empty_books_returns_empty(self):
        gaps = detect_title_gaps([])
        assert gaps == []

    def test_detects_missing_power_words(self):
        books = [
            _make_book(title="My Book About Dogs"),
            _make_book(title="Another Dog Book"),
            _make_book(title="Dogs for Life"),
        ]
        gaps = detect_title_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "missing_power_words" in gap_types

    def test_missing_power_words_includes_keywords(self):
        books = [_make_book(title="Simple Dog Book")]
        gaps = detect_title_gaps(books)
        for gap in gaps:
            if gap.gap_type == "missing_power_words":
                assert len(gap.missing_keywords) > 0

    def test_detects_missing_title_patterns(self):
        # No "how to" pattern among titles
        books = [
            _make_book(title="The Dog Owner Manual"),
            _make_book(title="Dog Training Secrets"),
            _make_book(title="Dogs 101"),
        ]
        gaps = detect_title_gaps(books)
        pattern_gaps = [g for g in gaps if "missing_pattern" in g.gap_type]
        # Should detect at least some missing patterns
        assert len(pattern_gaps) > 0

    def test_detects_subtitle_opportunity(self):
        # No subtitles (no colons)
        books = [
            _make_book(title="Dog Training Guide"),
            _make_book(title="Puppy Training Manual"),
            _make_book(title="Dog Obedience Handbook"),
            _make_book(title="Training Your Dog"),
        ]
        gaps = detect_title_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "subtitle_opportunity" in gap_types

    def test_no_subtitle_gap_when_most_have_subtitles(self):
        books = [
            _make_book(title="Dog Training: The Complete Guide"),
            _make_book(title="Puppy Training: Step by Step"),
            _make_book(title="Dog Obedience: A Handbook"),
            _make_book(title="Training Your Dog: 101 Tips"),
        ]
        gaps = detect_title_gaps(books)
        gap_types = [g.gap_type for g in gaps]
        assert "subtitle_opportunity" not in gap_types

    def test_returns_title_gap_objects(self):
        books = [_make_book(title="Simple Book")]
        gaps = detect_title_gaps(books)
        for gap in gaps:
            assert isinstance(gap, TitleGap)
            assert gap.gap_type
            assert gap.description


# ---------------------------------------------------------------------------
# detect_content_gaps
# ---------------------------------------------------------------------------


class TestDetectContentGaps:
    def test_empty_books_returns_empty(self):
        gaps = detect_content_gaps([])
        assert gaps == []

    def test_detects_complaint_based_gaps(self):
        books = [
            _make_book(review_complaints=["advanced topics", "practical examples"]),
            _make_book(review_complaints=["advanced topics", "case studies"]),
            _make_book(review_complaints=["advanced topics"]),
        ]
        gaps = detect_content_gaps(books, niche="test")
        topics = [g.topic for g in gaps]
        assert "advanced topics" in topics

    def test_detects_low_average_rating_gap(self):
        books = [
            _make_book(rating=3.0),
            _make_book(rating=2.5),
            _make_book(rating=3.5),
        ]
        gaps = detect_content_gaps(books, niche="test")
        topics = [g.topic for g in gaps]
        assert "overall_quality" in topics

    def test_no_quality_gap_with_high_ratings(self):
        books = [
            _make_book(rating=4.5),
            _make_book(rating=4.8),
            _make_book(rating=4.2),
        ]
        gaps = detect_content_gaps(books, niche="test")
        topics = [g.topic for g in gaps]
        assert "overall_quality" not in topics

    def test_detects_value_gap(self):
        books = [
            _make_book(price=24.99, rating=3.0),
            _make_book(price=19.99, rating=3.5),
        ]
        gaps = detect_content_gaps(books, niche="test")
        topics = [g.topic for g in gaps]
        assert "value_gap" in topics

    def test_no_value_gap_with_cheap_books(self):
        books = [
            _make_book(price=4.99, rating=3.0),
            _make_book(price=5.99, rating=3.5),
        ]
        gaps = detect_content_gaps(books, niche="test")
        topics = [g.topic for g in gaps]
        assert "value_gap" not in topics

    def test_returns_content_gap_objects(self):
        books = [
            _make_book(review_complaints=["exercises", "exercises"]),
            _make_book(review_complaints=["exercises"]),
        ]
        gaps = detect_content_gaps(books, niche="test")
        for gap in gaps:
            assert isinstance(gap, ContentGap)
            assert gap.topic
            assert gap.description


# ---------------------------------------------------------------------------
# run_gap_analysis (async full pipeline)
# ---------------------------------------------------------------------------


class TestRunGapAnalysis:
    @pytest.mark.asyncio
    async def test_returns_gap_analysis_data(self):
        books = [
            _make_book(title="Dog Training Basics"),
            _make_book(title="Puppy Care", cover_url=None),
            _make_book(title="Dog Behavior"),
        ]
        result = await run_gap_analysis(books, niche="dog training", category="Pets")
        assert isinstance(result, GapAnalysisData)
        assert result.books_analyzed == 3
        assert isinstance(result.summary, str)
        assert isinstance(result.recommendations, list)

    @pytest.mark.asyncio
    async def test_empty_books(self):
        result = await run_gap_analysis([], niche="empty")
        assert result.books_analyzed == 0
        assert result.cover_gaps == []
        assert result.title_gaps == []
        assert result.content_gaps == []

    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self):
        books = [
            _make_book(
                title="Self Help Book",
                price=2.99,
                rating=3.0,
                cover_url=None,
                review_complaints=["exercises", "exercises"],
            ),
            _make_book(
                title="Self Help Guide",
                price=3.99,
                rating=3.5,
                cover_url=None,
                review_complaints=["exercises", "practical examples"],
            ),
            _make_book(
                title="Self Help Manual",
                price=2.49,
                rating=2.5,
                review_complaints=["exercises", "depth"],
            ),
            _make_book(
                title="Self Help Handbook",
                price=4.99,
                rating=3.0,
                review_complaints=["practical examples", "depth"],
            ),
            _make_book(
                title="Self Help Primer",
                price=1.99,
                rating=3.2,
                review_complaints=["depth"],
            ),
        ]
        result = await run_gap_analysis(books, niche="self-help", category="Self-Help")
        # Should find gaps in all three dimensions
        total_gaps = len(result.cover_gaps) + len(result.title_gaps) + len(result.content_gaps)
        assert total_gaps > 0
        assert result.summary
        assert len(result.recommendations) > 0
