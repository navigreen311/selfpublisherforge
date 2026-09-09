"""Unit tests for the Competitor Finder service layer.

Covers competitor analysis, weakness signals, batch analysis,
opportunity blueprints, gap analysis, and alerts.

All tests use mocked AsyncSession -- no real DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.competitor_finder.schemas import (
    AlertSeverity,
    AlertType,
    AnalysisStatus,
    BatchAnalyzeRequest,
    CompetitorAnalyzeRequest,
    GapAnalysisRequest,
)
from app.modules.competitor_finder.service import CompetitorFinderService

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def book_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Return a CompetitorFinderService instance with mocked DB."""
    return CompetitorFinderService(mock_db)


def _make_competitor_book(**overrides):
    """Factory helper to create a CompetitorBook mock."""
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
        "asin": "B000000001",
        "title": "Competitor Book",
        "author": "Author Name",
        "category": "Self-Help",
        "price": 9.99,
        "rating": 4.3,
        "review_count": 150,
        "bsr": 5000,
        "cover_url": "https://example.com/cover.jpg",
    }
    defaults.update(overrides)
    book = MagicMock()
    for k, v in defaults.items():
        setattr(book, k, v)
    return book


def _make_competitor_review(**overrides):
    """Factory helper to create a CompetitorReview mock."""
    defaults = {
        "id": uuid.uuid4(),
        "competitor_book_id": uuid.uuid4(),
        "rating": 3,
        "title": "Good book",
        "review_text": "I liked this book.",
        "helpful_votes": 5,
        "verified_purchase": True,
    }
    defaults.update(overrides)
    review = MagicMock()
    for k, v in defaults.items():
        setattr(review, k, v)
    return review


# ===========================================================================
# Tests: analyze_competitor
# ===========================================================================


class TestAnalyzeCompetitor:
    """Tests for CompetitorFinderService.analyze_competitor."""

    @pytest.mark.asyncio
    @patch("app.modules.competitor_finder.service.analyze_reviews_with_ai")
    @patch("app.modules.competitor_finder.service.generate_opportunity_blueprint")
    async def test_creates_analysis_record(
        self,
        mock_generate_opportunity,
        mock_analyze_reviews,
        service,
        org_id,
        book_id,
    ):
        """analyze_competitor should create a CompetitorAnalysis record."""
        book = _make_competitor_book(id=book_id)

        # Mock get_book
        book_result = MagicMock()
        book_result.scalar_one_or_none.return_value = book

        # Mock get_reviews
        reviews_result = MagicMock()
        reviews_result.scalars.return_value.all.return_value = [
            _make_competitor_review(),
        ]

        service.db.execute.side_effect = [book_result, reviews_result]

        # Mock analysis result
        mock_analyze_reviews.return_value = MagicMock(
            sentiment_score=0.7,
            review_summary="Overall positive",
            weakness_count=2,
            strength_count=5,
            total_reviews_analyzed=10,
            weakness_signals=[],
        )

        request = CompetitorAnalyzeRequest(
            book_id=book_id,
            max_reviews=100,
            include_opportunity=False,
        )

        result = await service.analyze_competitor(request, org_id)

        assert result.status == AnalysisStatus.COMPLETED.value
        assert result.sentiment_score == 0.7
        service.db.add.assert_called()
        service.db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_raises_error_when_book_not_found(
        self,
        service,
        org_id,
        book_id,
    ):
        """analyze_competitor should raise ValueError when book doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute.return_value = mock_result

        request = CompetitorAnalyzeRequest(
            book_id=book_id,
            max_reviews=100,
        )

        with pytest.raises(ValueError, match="not found"):
            await service.analyze_competitor(request, org_id)

    @pytest.mark.asyncio
    @patch("app.modules.competitor_finder.service.analyze_reviews_with_ai")
    @patch("app.modules.competitor_finder.service.generate_opportunity_blueprint")
    async def test_generates_opportunity_blueprint_when_requested(
        self,
        mock_generate_opportunity,
        mock_analyze_reviews,
        service,
        org_id,
        book_id,
    ):
        """analyze_competitor should generate opportunity blueprint if requested."""
        book = _make_competitor_book(id=book_id)

        book_result = MagicMock()
        book_result.scalar_one_or_none.return_value = book

        reviews_result = MagicMock()
        reviews_result.scalars.return_value.all.return_value = [
            _make_competitor_review(),
        ]

        service.db.execute.side_effect = [book_result, reviews_result]

        weakness_signal = MagicMock(
            category=MagicMock(value="content"),
            severity=MagicMock(value="high"),
            signal_text="Weak plot",
            evidence=["Review 1", "Review 2"],
            frequency=10,
            confidence=0.85,
            actionable=True,
            suggestion="Strengthen plot development",
        )

        mock_analyze_reviews.return_value = MagicMock(
            sentiment_score=0.6,
            review_summary="Mixed reviews",
            weakness_count=3,
            strength_count=2,
            total_reviews_analyzed=15,
            weakness_signals=[weakness_signal],
        )

        mock_generate_opportunity.return_value = MagicMock(
            title_suggestions=["Better Title"],
            content_strategy=["Focus on plot"],
            format_recommendations=["Ebook", "Paperback"],
            pricing_strategy="Price at $4.99",
            differentiators=["Unique angle"],
            target_audience="Self-help readers",
            estimated_opportunity_score=75,
            full_blueprint={"key": "value"},
        )

        request = CompetitorAnalyzeRequest(
            book_id=book_id,
            max_reviews=100,
            include_opportunity=True,
        )

        result = await service.analyze_competitor(request, org_id)

        assert result.status == AnalysisStatus.COMPLETED.value
        mock_generate_opportunity.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handles_analysis_failure(
        self,
        service,
        org_id,
        book_id,
    ):
        """analyze_competitor should mark status as FAILED on exception."""
        book = _make_competitor_book(id=book_id)

        book_result = MagicMock()
        book_result.scalar_one_or_none.return_value = book

        # Simulate error during review fetch
        service.db.execute.side_effect = [book_result, RuntimeError("DB error")]

        request = CompetitorAnalyzeRequest(
            book_id=book_id,
            max_reviews=100,
        )

        result = await service.analyze_competitor(request, org_id)

        assert result.status == AnalysisStatus.FAILED.value
        assert "DB error" in result.error_message


# ===========================================================================
# Tests: get_weaknesses
# ===========================================================================


class TestGetWeaknesses:
    """Tests for CompetitorFinderService.get_weaknesses."""

    @pytest.mark.asyncio
    async def test_returns_weakness_signals(
        self,
        service,
        org_id,
    ):
        """get_weaknesses should return weakness signals for an analysis."""
        analysis_id = uuid.uuid4()

        # Mock analysis lookup
        analysis_result = MagicMock()
        analysis_result.scalar_one_or_none.return_value = MagicMock(id=analysis_id)

        # Mock weaknesses lookup
        weakness1 = MagicMock(confidence=0.9)
        weakness2 = MagicMock(confidence=0.8)
        weaknesses_result = MagicMock()
        weaknesses_result.scalars.return_value.all.return_value = [weakness1, weakness2]

        service.db.execute.side_effect = [analysis_result, weaknesses_result]

        result = await service.get_weaknesses(analysis_id, org_id)

        assert len(result) == 2
        assert result[0].confidence == 0.9


# ===========================================================================
# Tests: batch_analyze
# ===========================================================================


class TestBatchAnalyze:
    """Tests for CompetitorFinderService.batch_analyze."""

    @pytest.mark.asyncio
    async def test_creates_analysis_records_for_top_books(
        self,
        service,
        org_id,
    ):
        """batch_analyze should create analysis records for top N books in category."""
        book1 = _make_competitor_book(id=uuid.uuid4(), bsr=1000)
        book2 = _make_competitor_book(id=uuid.uuid4(), bsr=2000)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [book1, book2]
        service.db.execute.return_value = mock_result

        request = BatchAnalyzeRequest(
            category="Self-Help",
            top_n=2,
        )

        result = await service.batch_analyze(request, org_id)

        assert len(result) == 2
        assert all(a.status == AnalysisStatus.PENDING.value for a in result)
        service.db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_error_when_no_books_found(
        self,
        service,
        org_id,
    ):
        """batch_analyze should raise ValueError when no books found in category."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.db.execute.return_value = mock_result

        request = BatchAnalyzeRequest(
            category="NonExistentCategory",
            top_n=5,
        )

        with pytest.raises(ValueError, match="No competitor books found"):
            await service.batch_analyze(request, org_id)


# ===========================================================================
# Tests: get_opportunity
# ===========================================================================


class TestGetOpportunity:
    """Tests for CompetitorFinderService.get_opportunity."""

    @pytest.mark.asyncio
    async def test_returns_opportunity_blueprint(
        self,
        service,
        org_id,
    ):
        """get_opportunity should return OpportunityBlueprint for an analysis."""
        analysis_id = uuid.uuid4()

        analysis_result = MagicMock()
        analysis_result.scalar_one_or_none.return_value = MagicMock(id=analysis_id)

        blueprint = MagicMock(analysis_id=analysis_id)
        blueprint_result = MagicMock()
        blueprint_result.scalar_one_or_none.return_value = blueprint

        service.db.execute.side_effect = [analysis_result, blueprint_result]

        result = await service.get_opportunity(analysis_id, org_id)

        assert result is not None
        assert result.analysis_id == analysis_id


# ===========================================================================
# Tests: run_gap_analysis
# ===========================================================================


class TestRunGapAnalysis:
    """Tests for CompetitorFinderService.run_gap_analysis."""

    @pytest.mark.asyncio
    @patch("app.modules.competitor_finder.service.run_gap_analysis")
    async def test_creates_gap_analysis_result(
        self,
        mock_run_gap_analysis,
        service,
        org_id,
    ):
        """run_gap_analysis should create a GapAnalysisResult record."""
        book1 = _make_competitor_book()
        book2 = _make_competitor_book()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [book1, book2]
        service.db.execute.return_value = mock_result

        mock_run_gap_analysis.return_value = MagicMock(
            books_analyzed=2,
            cover_gaps=[],
            title_gaps=[],
            content_gaps=[],
            summary="Gap analysis summary",
            recommendations=["Recommendation 1"],
        )

        request = GapAnalysisRequest(
            niche="Self-Help",
            category="Personal Growth",
            max_books=10,
        )

        result = await service.run_gap_analysis(request, org_id)

        assert result.status == "completed"
        assert result.books_analyzed == 2
        service.db.add.assert_called_once()
        service.db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_error_when_no_books_for_gap_analysis(
        self,
        service,
        org_id,
    ):
        """run_gap_analysis should raise ValueError when no books found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.db.execute.return_value = mock_result

        request = GapAnalysisRequest(
            niche="NonExistent",
            max_books=10,
        )

        with pytest.raises(ValueError, match="No competitor books found"):
            await service.run_gap_analysis(request, org_id)


# ===========================================================================
# Tests: Alerts
# ===========================================================================


class TestAlerts:
    """Tests for alert management methods."""

    @pytest.mark.asyncio
    async def test_get_alerts_returns_list(
        self,
        service,
        org_id,
    ):
        """get_alerts should return list of alerts for an org."""
        alert1 = MagicMock(id=uuid.uuid4(), dismissed=False)
        alert2 = MagicMock(id=uuid.uuid4(), dismissed=False)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [alert1, alert2]
        service.db.execute.return_value = mock_result

        result = await service.get_alerts(org_id, limit=50)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_create_alert(
        self,
        service,
        org_id,
    ):
        """create_alert should create a new CompetitorAlert."""
        result = await service.create_alert(
            org_id=org_id,
            alert_type=AlertType.NEW_COMPETITOR,
            title="New competitor detected",
            severity=AlertSeverity.INFO,
        )

        service.db.add.assert_called_once()
        service.db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dismiss_alert(
        self,
        service,
        org_id,
    ):
        """dismiss_alert should mark alert as dismissed."""
        alert_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        service.db.execute.return_value = mock_result

        result = await service.dismiss_alert(alert_id, org_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_alert_read(
        self,
        service,
        org_id,
    ):
        """mark_alert_read should mark alert as read."""
        alert_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        service.db.execute.return_value = mock_result

        result = await service.mark_alert_read(alert_id, org_id)

        assert result is True


# ===========================================================================
# Tests: _compute_overall_score
# ===========================================================================


class TestComputeOverallScore:
    """Tests for the static _compute_overall_score method."""

    def test_calculates_score_correctly(self):
        """_compute_overall_score should compute a 0-100 score."""
        result_mock = MagicMock(
            sentiment_score=0.8,
            weakness_count=5,
            strength_count=10,
        )

        score = CompetitorFinderService._compute_overall_score(result_mock)

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_high_sentiment_yields_high_score(self):
        """High sentiment with low weaknesses should yield high score."""
        result_mock = MagicMock(
            sentiment_score=0.9,
            weakness_count=1,
            strength_count=15,
        )

        score = CompetitorFinderService._compute_overall_score(result_mock)

        assert score > 50

    def test_low_sentiment_yields_low_score(self):
        """Low sentiment with many weaknesses should yield low score."""
        result_mock = MagicMock(
            sentiment_score=0.3,
            weakness_count=20,
            strength_count=2,
        )

        score = CompetitorFinderService._compute_overall_score(result_mock)

        assert score < 50
