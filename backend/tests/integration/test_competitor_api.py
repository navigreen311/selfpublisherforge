"""Integration tests for the Competitor Weakness Finder API endpoints.

Uses FastAPI's TestClient with mocked database and auth dependencies.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.competitor_finder.router import router
from app.modules.competitor_finder.models import (
    CompetitorAlert,
    CompetitorAnalysis,
    CompetitorBook,
    CompetitorReview,
    GapAnalysisResult,
    OpportunityBlueprint,
    WeaknessSignal,
)
from app.modules.competitor_finder.schemas import (
    AnalysisStatus,
    AlertSeverity,
    AlertType,
    WeaknessCategory,
    Severity,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_ORG_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()
TEST_BOOK_ID = uuid.uuid4()
TEST_ANALYSIS_ID = uuid.uuid4()

NOW = datetime.now(timezone.utc)


def _create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with the competitor router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/competitors", tags=["competitors"])
    return app


def _mock_current_user():
    """Return a mock current user dict."""
    return {
        "user_id": TEST_USER_ID,
        "org_id": TEST_ORG_ID,
        "role": "admin",
    }


def _mock_book() -> MagicMock:
    """Create a mock competitor book."""
    book = MagicMock(spec=CompetitorBook)
    book.id = TEST_BOOK_ID
    book.org_id = TEST_ORG_ID
    book.asin = "B0EXAMPLE01"
    book.title = "Test Competitor Book"
    book.author = "Test Author"
    book.bsr = 5000
    book.price = 14.99
    book.rating = 3.8
    book.review_count = 250
    book.category = "Self-Help"
    book.cover_url = "https://example.com/cover.jpg"
    book.metadata_json = None
    book.created_at = NOW
    book.updated_at = NOW
    return book


def _mock_analysis() -> MagicMock:
    """Create a mock competitor analysis."""
    analysis = MagicMock(spec=CompetitorAnalysis)
    analysis.id = TEST_ANALYSIS_ID
    analysis.org_id = TEST_ORG_ID
    analysis.book_id = TEST_BOOK_ID
    analysis.status = AnalysisStatus.COMPLETED.value
    analysis.overall_score = 45.5
    analysis.sentiment_score = 0.65
    analysis.weakness_count = 3
    analysis.strength_count = 10
    analysis.review_summary = "Test summary"
    analysis.positioning_analysis = {"category": "Self-Help"}
    analysis.metadata_json = None
    analysis.completed_at = NOW
    analysis.error_message = None
    analysis.created_at = NOW
    analysis.updated_at = NOW
    return analysis


def _mock_weakness() -> MagicMock:
    """Create a mock weakness signal."""
    ws = MagicMock(spec=WeaknessSignal)
    ws.id = uuid.uuid4()
    ws.analysis_id = TEST_ANALYSIS_ID
    ws.category = WeaknessCategory.CONTENT_QUALITY.value
    ws.severity = Severity.HIGH.value
    ws.signal_text = "Readers complain about 'shallow' content"
    ws.evidence = [{"excerpt": "Very shallow...", "rating": 2, "helpful_votes": 5}]
    ws.frequency = 5
    ws.confidence = 0.75
    ws.actionable = True
    ws.suggestion = "Provide deeper, well-researched content"
    ws.created_at = NOW
    ws.updated_at = NOW
    return ws


def _mock_opportunity() -> MagicMock:
    """Create a mock opportunity blueprint."""
    opp = MagicMock(spec=OpportunityBlueprint)
    opp.id = uuid.uuid4()
    opp.analysis_id = TEST_ANALYSIS_ID
    opp.title_suggestions = ["The Definitive Guide to Self-Help"]
    opp.content_strategy = {"key_topics": ["Deep research"], "depth_level": "advanced"}
    opp.format_recommendations = ["Professional formatting"]
    opp.pricing_strategy = {"recommended_price": 12.99}
    opp.differentiators = ["Deeper content"]
    opp.target_audience = "Intermediate readers"
    opp.estimated_opportunity_score = 0.72
    opp.full_blueprint = {"summary": "Great opportunity"}
    opp.created_at = NOW
    opp.updated_at = NOW
    return opp


def _mock_alert() -> MagicMock:
    """Create a mock competitor alert."""
    alert = MagicMock(spec=CompetitorAlert)
    alert.id = uuid.uuid4()
    alert.org_id = TEST_ORG_ID
    alert.book_id = TEST_BOOK_ID
    alert.alert_type = AlertType.PRICE_CHANGE.value
    alert.severity = AlertSeverity.WARNING.value
    alert.title = "Price dropped for Test Book"
    alert.description = "Price changed from $14.99 to $9.99"
    alert.data = {"old_price": 14.99, "new_price": 9.99}
    alert.read = False
    alert.dismissed = False
    alert.created_at = NOW
    alert.updated_at = NOW
    return alert


def _mock_gap_result() -> MagicMock:
    """Create a mock gap analysis result."""
    gap = MagicMock(spec=GapAnalysisResult)
    gap.id = uuid.uuid4()
    gap.org_id = TEST_ORG_ID
    gap.niche = "self-help"
    gap.category = "Self-Help"
    gap.books_analyzed = 10
    gap.cover_gaps = [{"gap_type": "missing_covers", "description": "2 books lack covers"}]
    gap.title_gaps = [{"gap_type": "missing_power_words", "description": "No 'ultimate' usage"}]
    gap.content_gaps = [{"topic": "exercises", "description": "Missing exercises"}]
    gap.summary = "Good opportunity in self-help niche"
    gap.recommendations = ["Add workbook", "Better formatting"]
    gap.status = "completed"
    gap.metadata_json = None
    gap.created_at = NOW
    gap.updated_at = NOW
    return gap


# ---------------------------------------------------------------------------
# Tests: POST /competitors/analyze
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    @patch("app.modules.competitor_finder.router.get_current_user")
    @patch("app.modules.competitor_finder.router.get_db")
    def test_analyze_returns_201(self, mock_db, mock_auth, mock_service_cls):
        mock_auth.return_value = _mock_current_user()
        mock_db.return_value = AsyncMock()

        mock_service = AsyncMock()
        mock_service.analyze_competitor.return_value = _mock_analysis()
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.post(
            "/api/v1/competitors/analyze",
            json={"book_id": str(TEST_BOOK_ID)},
        )
        assert response.status_code == 201

    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    @patch("app.modules.competitor_finder.router.get_current_user")
    @patch("app.modules.competitor_finder.router.get_db")
    def test_analyze_not_found_returns_404(self, mock_db, mock_auth, mock_service_cls):
        mock_auth.return_value = _mock_current_user()
        mock_db.return_value = AsyncMock()

        mock_service = AsyncMock()
        mock_service.analyze_competitor.side_effect = ValueError("Not found")
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.post(
            "/api/v1/competitors/analyze",
            json={"book_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: GET /competitors/{id}/weaknesses
# ---------------------------------------------------------------------------

class TestGetWeaknessesEndpoint:
    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_get_weaknesses_returns_list(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.get_weaknesses.return_value = [_mock_weakness()]
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.get(f"/api/v1/competitors/{TEST_ANALYSIS_ID}/weaknesses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_get_weaknesses_not_found(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.get_weaknesses.side_effect = ValueError("Not found")
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.get(f"/api/v1/competitors/{uuid.uuid4()}/weaknesses")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: GET /competitors/{id}/opportunity
# ---------------------------------------------------------------------------

class TestGetOpportunityEndpoint:
    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_get_opportunity_returns_data(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.get_opportunity.return_value = _mock_opportunity()
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.get(f"/api/v1/competitors/{TEST_ANALYSIS_ID}/opportunity")
        assert response.status_code == 200

    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_get_opportunity_not_found(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.get_opportunity.return_value = None
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.get(f"/api/v1/competitors/{uuid.uuid4()}/opportunity")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: GET /competitors/alerts
# ---------------------------------------------------------------------------

class TestGetAlertsEndpoint:
    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_get_alerts_returns_list(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.get_alerts.return_value = [_mock_alert()]
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.get("/api/v1/competitors/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_get_alerts_with_query_params(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.get_alerts.return_value = []
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.get(
            "/api/v1/competitors/alerts?include_dismissed=true&limit=10"
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests: POST /competitors/gap-analysis
# ---------------------------------------------------------------------------

class TestGapAnalysisEndpoint:
    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_gap_analysis_returns_201(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.run_gap_analysis.return_value = _mock_gap_result()
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.post(
            "/api/v1/competitors/gap-analysis",
            json={"niche": "self-help", "category": "Self-Help"},
        )
        assert response.status_code == 201

    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_gap_analysis_not_found(self, mock_service_cls):
        mock_service = AsyncMock()
        mock_service.run_gap_analysis.side_effect = ValueError("No books found")
        mock_service_cls.return_value = mock_service

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.post(
            "/api/v1/competitors/gap-analysis",
            json={"niche": "nonexistent"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: POST /competitors/batch-analyze
# ---------------------------------------------------------------------------

class TestBatchAnalyzeEndpoint:
    @patch("app.modules.competitor_finder.router.process_batch_analysis")
    @patch("app.modules.competitor_finder.router.CompetitorFinderService")
    def test_batch_analyze_returns_202(self, mock_service_cls, mock_task):
        analysis1 = _mock_analysis()
        analysis2 = _mock_analysis()
        analysis2.id = uuid.uuid4()
        analysis2.book_id = uuid.uuid4()

        mock_service = AsyncMock()
        mock_service.batch_analyze.return_value = [analysis1, analysis2]
        mock_service_cls.return_value = mock_service

        mock_task_result = MagicMock()
        mock_task_result.id = "task-123"
        mock_task.delay.return_value = mock_task_result

        from app.core.dependencies import get_current_user as gcu
        from app.database import get_db as gdb

        app = _create_test_app()
        app.dependency_overrides[gcu] = lambda: _mock_current_user()
        app.dependency_overrides[gdb] = lambda: AsyncMock()

        client = TestClient(app)
        response = client.post(
            "/api/v1/competitors/batch-analyze?marketplace=US",
            json={"category": "Self-Help", "top_n": 5},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["analyses_created"] == 2
        assert data["task_id"] == "task-123"
