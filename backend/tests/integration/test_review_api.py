"""Integration tests for Review Intelligence API endpoints."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import create_app


# We need to override auth for integration tests
def mock_current_user():
    return {
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "org_id": uuid.UUID("00000000-0000-0000-0000-000000000099"),
        "role": "owner",
    }


ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")
BOOK_ID = uuid.UUID("00000000-0000-0000-0000-000000000042")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
async def app_with_db(db_engine, db):
    """Create FastAPI app with test database and register review router."""
    from app.core.dependencies import get_current_user

    app = create_app()

    # Override dependencies
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = mock_current_user

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app_with_db):
    """Create an async test client."""
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def seeded_db(db):
    """Seed the test database with sample reviews."""
    from tests.conftest import make_review

    reviews = []
    now = datetime.now(UTC)

    # Positive reviews
    for i in range(5):
        r = make_review(
            org_id=ORG_ID,
            book_id=BOOK_ID,
            star_rating=4.5,
            body="Loved this book, amazing writing!",
            sentiment="positive",
            sentiment_score=0.8,
            review_date=now - timedelta(days=i),
        )
        reviews.append(r)

    # Negative reviews
    for i in range(3):
        r = make_review(
            org_id=ORG_ID,
            book_id=BOOK_ID,
            star_rating=2.0,
            body="Terrible, very boring and slow",
            sentiment="negative",
            sentiment_score=-0.7,
            review_date=now - timedelta(days=i + 5),
        )
        reviews.append(r)

    # Neutral review
    r = make_review(
        org_id=ORG_ID,
        book_id=BOOK_ID,
        star_rating=3.0,
        body="It was okay, nothing special",
        sentiment="neutral",
        sentiment_score=0.0,
        review_date=now - timedelta(days=10),
    )
    reviews.append(r)

    # Competitor review
    r = make_review(
        org_id=ORG_ID,
        book_id=BOOK_ID,
        star_rating=4.0,
        body="Competitor book review",
        sentiment="positive",
        sentiment_score=0.6,
        is_competitor=True,
        review_date=now - timedelta(days=2),
    )
    reviews.append(r)

    for review in reviews:
        db.add(review)
    await db.flush()

    return reviews


# --- List reviews tests ---


class TestListReviewsEndpoint:
    @pytest.mark.asyncio
    async def test_list_reviews_empty(self, client):
        response = await client.get("/api/v1/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_list_reviews_with_data(self, client, seeded_db):
        response = await client.get("/api/v1/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10
        assert len(data["items"]) <= 20

    @pytest.mark.asyncio
    async def test_list_reviews_pagination(self, client, seeded_db):
        response = await client.get("/api/v1/reviews?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    @pytest.mark.asyncio
    async def test_list_reviews_filter_sentiment(self, client, seeded_db):
        response = await client.get("/api/v1/reviews?sentiment=positive")
        assert response.status_code == 200
        data = response.json()
        assert all(
            item["sentiment"] == "positive" for item in data["items"]
        )

    @pytest.mark.asyncio
    async def test_list_reviews_filter_min_rating(self, client, seeded_db):
        response = await client.get("/api/v1/reviews?min_rating=4.0")
        assert response.status_code == 200
        data = response.json()
        assert all(item["star_rating"] >= 4.0 for item in data["items"])


# --- Book reviews tests ---


class TestBookReviewsEndpoint:
    @pytest.mark.asyncio
    async def test_get_book_reviews(self, client, seeded_db):
        response = await client.get(f"/api/v1/reviews/book/{BOOK_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_book_reviews_nonexistent_book(self, client):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/reviews/book/{fake_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0


# --- Sentiment endpoint tests ---


class TestSentimentEndpoint:
    @pytest.mark.asyncio
    async def test_get_sentiment_breakdown(self, client, seeded_db):
        response = await client.get(f"/api/v1/reviews/sentiment/{BOOK_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "positive_count" in data
        assert "negative_count" in data
        assert "neutral_count" in data
        assert "total_count" in data
        assert data["total_count"] > 0

    @pytest.mark.asyncio
    async def test_sentiment_percentages_sum(self, client, seeded_db):
        response = await client.get(f"/api/v1/reviews/sentiment/{BOOK_ID}")
        data = response.json()
        total_pct = (
            data["positive_pct"]
            + data["neutral_pct"]
            + data["negative_pct"]
            + data["mixed_pct"]
        )
        # Should sum to approximately 100% (allowing floating point variance)
        assert 99.0 <= total_pct <= 101.0

    @pytest.mark.asyncio
    async def test_sentiment_empty_book(self, client):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/reviews/sentiment/{fake_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0


# --- Velocity endpoint tests ---


class TestVelocityEndpoint:
    @pytest.mark.asyncio
    async def test_get_velocity(self, client, seeded_db):
        response = await client.get(
            f"/api/v1/reviews/velocity/{BOOK_ID}?period=daily&lookback=7"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == str(BOOK_ID)
        assert data["period"] == "daily"
        assert "data_points" in data
        assert "trend" in data
        assert data["trend"] in ["rising", "stable", "declining"]

    @pytest.mark.asyncio
    async def test_velocity_weekly(self, client, seeded_db):
        response = await client.get(
            f"/api/v1/reviews/velocity/{BOOK_ID}?period=weekly"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "weekly"


# --- Alerts endpoint tests ---


class TestAlertsEndpoint:
    @pytest.mark.asyncio
    async def test_list_alerts_empty(self, client):
        response = await client.get("/api/v1/reviews/alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self, client):
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/reviews/alerts/{fake_id}/acknowledge",
            json={"notes": "acknowledged"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, client, db, seeded_db):
        from app.modules.review_intelligence.models import ReviewAlert

        # Create an alert manually
        alert = ReviewAlert(
            org_id=ORG_ID,
            book_id=BOOK_ID,
            alert_type="negative_spike",
            severity="high",
            title="Test Alert",
            description="Test description",
        )
        db.add(alert)
        await db.flush()

        response = await client.patch(
            f"/api/v1/reviews/alerts/{alert.id}/acknowledge",
            json={"notes": "acknowledged"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_acknowledged"] is True
        assert data["acknowledged_by"] is not None


# --- Batch analysis endpoint tests ---


class TestAnalyzeEndpoint:
    @pytest.mark.asyncio
    async def test_analyze_empty(self, client):
        response = await client.post(
            "/api/v1/reviews/analyze",
            json={"book_id": str(uuid.uuid4()), "limit": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] == 0

    @pytest.mark.asyncio
    async def test_analyze_with_reviews(self, client, seeded_db):
        with patch(
            "app.modules.review_intelligence.sentiment.analyze_sentiment_llm",
            new_callable=AsyncMock,
        ) as mock_llm:
            from app.modules.review_intelligence.schemas import SentimentAnalysisResult
            from app.modules.review_intelligence.schemas import SentimentLabel as SL
            mock_llm.return_value = SentimentAnalysisResult(
                sentiment=SL.POSITIVE, score=0.8, themes=["writing_style"],
                key_phrases=[], complaints=[], praise=["amazing"],
            )
            response = await client.post(
                "/api/v1/reviews/analyze",
                json={"book_id": str(BOOK_ID), "limit": 5},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] > 0
        assert "sentiment_breakdown" in data
        assert "top_themes" in data
        assert "actionable_insights" in data


# --- Reputation endpoint tests ---


class TestReputationEndpoint:
    @pytest.mark.asyncio
    async def test_get_reputation(self, client, seeded_db):
        response = await client.get(f"/api/v1/reviews/reputation/{BOOK_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == str(BOOK_ID)
        assert "overall_score" in data
        assert "health_grade" in data
        assert "avg_rating" in data
        assert 0 <= data["overall_score"] <= 100
        assert data["health_grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

    @pytest.mark.asyncio
    async def test_reputation_empty_book(self, client):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/reviews/reputation/{fake_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_reviews"] == 0
        assert data["health_grade"] == "F"


# --- Acquisition tips endpoint tests ---


class TestAcquisitionTipsEndpoint:
    @pytest.mark.asyncio
    async def test_get_tips(self, client):
        with patch(
            "app.modules.review_intelligence.router.generate_acquisition_tips",
            new_callable=AsyncMock,
        ) as mock_tips:
            from app.modules.review_intelligence.schemas import AcquisitionTipsRequest
            from app.modules.review_intelligence.service import _default_acquisition_tips
            req = AcquisitionTipsRequest(
                book_id=BOOK_ID, current_review_count=5, genre="fantasy",
            )
            mock_tips.return_value = _default_acquisition_tips(req)
            response = await client.post(
                "/api/v1/reviews/acquisition/tips",
                json={
                    "book_id": str(BOOK_ID),
                    "current_review_count": 5,
                    "genre": "fantasy",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == str(BOOK_ID)
        assert len(data["tips"]) > 0
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_tips_have_required_fields(self, client):
        with patch(
            "app.modules.review_intelligence.router.generate_acquisition_tips",
            new_callable=AsyncMock,
        ) as mock_tips:
            from app.modules.review_intelligence.schemas import AcquisitionTipsRequest
            from app.modules.review_intelligence.service import _default_acquisition_tips
            req = AcquisitionTipsRequest(book_id=BOOK_ID)
            mock_tips.return_value = _default_acquisition_tips(req)
            response = await client.post(
                "/api/v1/reviews/acquisition/tips",
                json={"book_id": str(BOOK_ID)},
            )
        assert response.status_code == 200
        data = response.json()
        for tip in data["tips"]:
            assert "category" in tip
            assert "tip" in tip
            assert "effort_level" in tip
            assert "expected_impact" in tip
