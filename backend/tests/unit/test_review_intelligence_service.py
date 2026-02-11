"""Unit tests for the Review Intelligence service layer.

Covers review listing, sentiment analysis, alerts, reputation scoring,
and review acquisition tips.

All tests use mocked AsyncSession -- no real DB.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.review_intelligence import service
from app.modules.review_intelligence.schemas import (
    AcquisitionTipsRequest,
    AlertListParams,
    BatchAnalysisRequest,
    ReviewListParams,
    SentimentLabel,
    VelocityPeriod,
    VelocityTrend,
)


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
def user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


def _make_review(**overrides):
    """Factory helper to create a BookReview mock."""
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
        "book_id": uuid.uuid4(),
        "source": "amazon",
        "star_rating": 4,
        "body": "Great book!",
        "sentiment": "positive",
        "sentiment_score": 0.8,
        "review_date": datetime(2025, 1, 1, tzinfo=UTC),
        "deleted_at": None,
    }
    defaults.update(overrides)
    review = MagicMock()
    for k, v in defaults.items():
        setattr(review, k, v)
    return review


# ===========================================================================
# Tests: list_reviews
# ===========================================================================

class TestListReviews:
    """Tests for service.list_reviews."""

    @pytest.mark.asyncio
    async def test_returns_reviews_with_pagination(
        self,
        mock_db,
        org_id,
    ):
        """list_reviews should return reviews with cursor pagination."""
        review1 = _make_review(id=uuid.uuid4())
        review2 = _make_review(id=uuid.uuid4())

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [review1, review2]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        mock_db.execute.side_effect = [mock_result, mock_count]

        params = ReviewListParams(limit=20, sort_by="review_date")

        reviews, next_cursor, total = await service.list_reviews(mock_db, org_id, params)

        assert len(reviews) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_filters_by_sentiment(
        self,
        mock_db,
        org_id,
    ):
        """list_reviews should filter by sentiment when provided."""
        review1 = _make_review(sentiment="positive")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [review1]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count]

        params = ReviewListParams(
            sentiment=SentimentLabel.POSITIVE,
            limit=20,
        )

        reviews, _, total = await service.list_reviews(mock_db, org_id, params)

        assert len(reviews) == 1
        assert reviews[0].sentiment == "positive"


# ===========================================================================
# Tests: get_sentiment_breakdown
# ===========================================================================

class TestGetSentimentBreakdown:
    """Tests for service.get_sentiment_breakdown."""

    @pytest.mark.asyncio
    async def test_returns_sentiment_counts(
        self,
        mock_db,
        org_id,
        book_id,
    ):
        """get_sentiment_breakdown should return sentiment distribution."""
        mock_row = MagicMock(
            total=100,
            positive=70,
            neutral=20,
            negative=8,
            mixed=2,
            avg_score=0.75,
        )

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row

        mock_themes = MagicMock()
        mock_themes.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_result, mock_themes]

        result = await service.get_sentiment_breakdown(mock_db, org_id, book_id)

        assert result.total_count == 100
        assert result.positive_count == 70
        assert result.positive_pct == 70.0


# ===========================================================================
# Tests: analyze_reviews_batch
# ===========================================================================

class TestAnalyzeReviewsBatch:
    """Tests for service.analyze_reviews_batch."""

    @pytest.mark.asyncio
    @patch("app.modules.review_intelligence.service.analyze_sentiment_batch")
    @patch("app.modules.review_intelligence.service.extract_themes_from_results")
    async def test_analyzes_and_updates_reviews(
        self,
        mock_extract_themes,
        mock_analyze_sentiment_batch,
        mock_db,
        org_id,
    ):
        """analyze_reviews_batch should analyze reviews and update DB."""
        review1 = _make_review()
        review2 = _make_review()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [review1, review2]
        mock_db.execute.return_value = mock_result

        mock_analyze_sentiment_batch.return_value = [
            MagicMock(
                sentiment=SentimentLabel.POSITIVE,
                score=0.85,
                themes=["great", "helpful"],
                key_phrases=["very good"],
                complaints=[],
                praise=["excellent writing"],
            ),
            MagicMock(
                sentiment=SentimentLabel.NEUTRAL,
                score=0.5,
                themes=["okay"],
                key_phrases=["not bad"],
                complaints=["slow pacing"],
                praise=[],
            ),
        ]

        mock_extract_themes.return_value = []

        request = BatchAnalysisRequest(
            book_id=uuid.uuid4(),
            limit=100,
        )

        result = await service.analyze_reviews_batch(mock_db, org_id, request)

        assert result.total_analyzed == 2
        assert result.sentiment_breakdown.positive_count == 1
        mock_db.flush.assert_awaited_once()


# ===========================================================================
# Tests: list_alerts
# ===========================================================================

class TestListAlerts:
    """Tests for service.list_alerts."""

    @pytest.mark.asyncio
    async def test_returns_alerts_with_pagination(
        self,
        mock_db,
        org_id,
    ):
        """list_alerts should return paginated alerts."""
        alert1 = MagicMock(id=uuid.uuid4())
        alert2 = MagicMock(id=uuid.uuid4())

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [alert1, alert2]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        mock_db.execute.side_effect = [mock_result, mock_count]

        params = AlertListParams(limit=20)

        alerts, next_cursor, total = await service.list_alerts(mock_db, org_id, params)

        assert len(alerts) == 2
        assert total == 2


# ===========================================================================
# Tests: acknowledge_alert
# ===========================================================================

class TestAcknowledgeAlert:
    """Tests for service.acknowledge_alert."""

    @pytest.mark.asyncio
    async def test_marks_alert_as_acknowledged(
        self,
        mock_db,
        org_id,
        user_id,
    ):
        """acknowledge_alert should mark alert as acknowledged."""
        alert_id = uuid.uuid4()
        alert = MagicMock(id=alert_id, is_acknowledged=False)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result

        result = await service.acknowledge_alert(mock_db, org_id, alert_id, user_id)

        assert result is not None
        assert result.is_acknowledged is True
        assert result.acknowledged_by == user_id


# ===========================================================================
# Tests: compute_reputation_score
# ===========================================================================

class TestComputeReputationScore:
    """Tests for service.compute_reputation_score."""

    @pytest.mark.asyncio
    @patch("app.modules.review_intelligence.service.compute_velocity_from_snapshots")
    async def test_computes_reputation_score(
        self,
        mock_compute_velocity,
        mock_db,
        org_id,
        book_id,
    ):
        """compute_reputation_score should calculate comprehensive metrics."""
        # Mock stats
        mock_stats_row = MagicMock(
            total=100,
            avg_rating=4.2,
            positive=80,
            negative=10,
        )
        mock_stats_result = MagicMock()
        mock_stats_result.one.return_value = mock_stats_row

        # Mock rating distribution
        mock_dist_result = MagicMock()
        mock_dist_result.all.return_value = [(5, 50), (4, 30), (3, 10), (2, 5), (1, 5)]

        # Mock velocity
        mock_compute_velocity.return_value = MagicMock(
            trend=VelocityTrend.RISING,
        )

        # Mock existing reputation score lookup
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [
            mock_stats_result,
            mock_dist_result,
            mock_existing_result,
        ]

        result = await service.compute_reputation_score(mock_db, org_id, book_id)

        assert result.overall_score > 0
        assert result.avg_rating == 4.2
        assert result.total_reviews == 100
        assert result.velocity_trend == VelocityTrend.RISING


# ===========================================================================
# Tests: generate_acquisition_tips
# ===========================================================================

class TestGenerateAcquisitionTips:
    """Tests for service.generate_acquisition_tips."""

    @pytest.mark.asyncio
    async def test_returns_acquisition_tips(self):
        """generate_acquisition_tips should return tips (fallback or AI)."""
        request = AcquisitionTipsRequest(
            book_id=uuid.uuid4(),
            current_review_count=5,
            genre="thriller",
            target_audience="adult readers",
            budget="medium",
        )

        result = await service.generate_acquisition_tips(request)

        assert result.book_id == request.book_id
        assert len(result.tips) > 0
        assert result.estimated_review_potential > 0


# ===========================================================================
# Tests: Helper functions
# ===========================================================================

class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_calculate_overall_score(self):
        """_calculate_overall_score should compute score from components."""
        score = service._calculate_overall_score(
            avg_rating=4.5,
            total_reviews=100,
            sentiment_ratio=0.8,
            velocity_trend=VelocityTrend.RISING,
        )

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_score_to_grade(self):
        """_score_to_grade should convert numeric score to letter grade."""
        assert service._score_to_grade(96) == "A+"
        assert service._score_to_grade(92) == "A"
        assert service._score_to_grade(87) == "B+"
        assert service._score_to_grade(82) == "B"
        assert service._score_to_grade(77) == "C+"
        assert service._score_to_grade(72) == "C"
        assert service._score_to_grade(65) == "D"
        assert service._score_to_grade(50) == "F"

    def test_generate_reputation_recommendations(self):
        """_generate_reputation_recommendations should return actionable tips."""
        recommendations = service._generate_reputation_recommendations(
            avg_rating=3.8,
            total_reviews=5,
            sentiment_ratio=0.4,
            velocity_trend=VelocityTrend.DECLINING,
            negative_count=3,
            total_count=5,
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
