"""Integration tests for the Analytics API endpoints.

Tests all /api/v1/analytics/* routes with mocked database and authentication.
"""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.analytics.schemas import (
    AggregationPeriod,
)

# ---------- Fixtures ----------


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_user(org_id, user_id):
    return {"user_id": user_id, "org_id": org_id, "role": "owner"}


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest_asyncio.fixture
async def client(mock_db, mock_user):
    app = create_app()

    from app.core.dependencies import get_current_user
    from app.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------- Dashboard ----------


class TestDashboardEndpoint:
    @pytest.mark.asyncio
    async def test_get_dashboard_calls_service(self, client, mock_db):
        """GET /api/v1/analytics/dashboard returns dashboard data."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_dashboard = AsyncMock(
                return_value=MagicMock(
                    kpis=[],
                    revenue_chart=[],
                    top_books=[],
                    platform_breakdown={},
                    recent_royalties=[],
                    period_start=datetime.now(UTC) - timedelta(days=30),
                    period_end=datetime.now(UTC),
                )
            )

            # Patch model_dump for pydantic serialization
            mock_result = mock_service.get_dashboard.return_value
            mock_result.model_dump = MagicMock(
                return_value={
                    "kpis": [],
                    "revenue_chart": [],
                    "top_books": [],
                    "platform_breakdown": {},
                    "recent_royalties": [],
                    "period_start": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
                    "period_end": datetime.now(UTC).isoformat(),
                }
            )

            response = await client.get("/api/v1/analytics/dashboard")

            assert response.status_code == 200
            mock_service.get_dashboard.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dashboard_with_date_params(self, client, mock_db):
        """GET /api/v1/analytics/dashboard with date parameters."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_dashboard = AsyncMock(
                return_value=MagicMock(
                    kpis=[],
                    revenue_chart=[],
                    top_books=[],
                    platform_breakdown={},
                    recent_royalties=[],
                    period_start=datetime(2024, 1, 1, tzinfo=UTC),
                    period_end=datetime(2024, 1, 31, tzinfo=UTC),
                )
            )
            mock_service.get_dashboard.return_value.model_dump = MagicMock(
                return_value={
                    "kpis": [],
                    "revenue_chart": [],
                    "top_books": [],
                    "platform_breakdown": {},
                    "recent_royalties": [],
                    "period_start": "2024-01-01T00:00:00+00:00",
                    "period_end": "2024-01-31T00:00:00+00:00",
                }
            )

            response = await client.get(
                "/api/v1/analytics/dashboard",
                params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            )

            assert response.status_code == 200


# ---------- Revenue ----------


class TestRevenueEndpoint:
    @pytest.mark.asyncio
    async def test_get_revenue(self, client, mock_db):
        """GET /api/v1/analytics/revenue returns revenue data."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_revenue = AsyncMock(
                return_value=MagicMock(
                    total_revenue=Decimal("1000.00"),
                    total_units=50,
                    data_points=[],
                    period_start=datetime.now(UTC) - timedelta(days=365),
                    period_end=datetime.now(UTC),
                    aggregation=AggregationPeriod.MONTHLY,
                    by_platform={},
                    by_book=[],
                )
            )
            mock_service.get_revenue.return_value.model_dump = MagicMock(
                return_value={
                    "total_revenue": "1000.00",
                    "total_units": 50,
                    "data_points": [],
                    "period_start": datetime.now(UTC).isoformat(),
                    "period_end": datetime.now(UTC).isoformat(),
                    "aggregation": "monthly",
                    "by_platform": {},
                    "by_book": [],
                }
            )

            response = await client.get("/api/v1/analytics/revenue")

            assert response.status_code == 200
            mock_service.get_revenue.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_revenue_with_filters(self, client, mock_db):
        """GET /api/v1/analytics/revenue with query parameters."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_revenue = AsyncMock(
                return_value=MagicMock(
                    total_revenue=Decimal("500.00"),
                    total_units=25,
                    data_points=[],
                    period_start=datetime(2024, 1, 1, tzinfo=UTC),
                    period_end=datetime(2024, 6, 30, tzinfo=UTC),
                    aggregation=AggregationPeriod.WEEKLY,
                    by_platform={},
                    by_book=[],
                )
            )
            mock_service.get_revenue.return_value.model_dump = MagicMock(
                return_value={
                    "total_revenue": "500.00",
                    "total_units": 25,
                    "data_points": [],
                    "period_start": "2024-01-01T00:00:00+00:00",
                    "period_end": "2024-06-30T00:00:00+00:00",
                    "aggregation": "weekly",
                    "by_platform": {},
                    "by_book": [],
                }
            )

            response = await client.get(
                "/api/v1/analytics/revenue",
                params={
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-30",
                    "platform": "kdp",
                    "aggregation": "weekly",
                },
            )

            assert response.status_code == 200


# ---------- Royalties ----------


class TestRoyaltiesEndpoint:
    @pytest.mark.asyncio
    async def test_get_royalties(self, client, mock_db):
        """GET /api/v1/analytics/royalties returns paginated results."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_royalties = AsyncMock(
                return_value=MagicMock(
                    items=[],
                    next_cursor=None,
                    has_more=False,
                    total_count=0,
                )
            )
            mock_service.get_royalties.return_value.model_dump = MagicMock(
                return_value={
                    "items": [],
                    "next_cursor": None,
                    "has_more": False,
                    "total_count": 0,
                }
            )

            response = await client.get("/api/v1/analytics/royalties")

            assert response.status_code == 200
            mock_service.get_royalties.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_royalties(self, client, mock_db):
        """POST /api/v1/analytics/royalties/import accepts CSV data."""
        csv_content = base64.b64encode(b"Title,ASIN\nBook,B123").decode()

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.import_royalty_data = AsyncMock(
                return_value=MagicMock(
                    import_batch_id=uuid.uuid4(),
                    records_imported=1,
                    records_skipped=0,
                    errors=[],
                    platform="kdp",
                )
            )
            mock_service.import_royalty_data.return_value.model_dump = MagicMock(
                return_value={
                    "import_batch_id": str(uuid.uuid4()),
                    "records_imported": 1,
                    "records_skipped": 0,
                    "errors": [],
                    "platform": "kdp",
                }
            )

            response = await client.post(
                "/api/v1/analytics/royalties/import",
                json={
                    "platform": "kdp",
                    "file_content": csv_content,
                    "file_name": "royalties.csv",
                },
            )

            assert response.status_code == 200
            mock_service.import_royalty_data.assert_called_once()


# ---------- Portfolio ----------


class TestPortfolioEndpoint:
    @pytest.mark.asyncio
    async def test_get_portfolio(self, client, mock_db):
        """GET /api/v1/analytics/portfolio returns portfolio metrics."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_portfolio_metrics = AsyncMock(
                return_value=MagicMock(
                    total_books=10,
                    total_revenue=Decimal("5000.00"),
                    total_units_sold=250,
                    total_expenses=Decimal("0.00"),
                    net_profit=Decimal("5000.00"),
                    avg_roi=Decimal("0.00"),
                    platform_breakdown={},
                    format_breakdown={},
                    top_books=[],
                    snapshot_date=datetime.now(UTC),
                )
            )
            mock_service.get_portfolio_metrics.return_value.model_dump = MagicMock(
                return_value={
                    "total_books": 10,
                    "total_revenue": "5000.00",
                    "total_units_sold": 250,
                    "total_expenses": "0.00",
                    "net_profit": "5000.00",
                    "avg_roi": "0.00",
                    "platform_breakdown": {},
                    "format_breakdown": {},
                    "top_books": [],
                    "snapshot_date": datetime.now(UTC).isoformat(),
                }
            )

            response = await client.get("/api/v1/analytics/portfolio")

            assert response.status_code == 200
            mock_service.get_portfolio_metrics.assert_called_once()


# ---------- Reports ----------


class TestReportsEndpoint:
    @pytest.mark.asyncio
    async def test_generate_report(self, client, mock_db, user_id):
        """POST /api/v1/analytics/reports/generate creates a report."""
        report_id = uuid.uuid4()

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.create_report = AsyncMock(
                return_value=MagicMock(
                    id=report_id,
                    org_id=uuid.uuid4(),
                    title="Revenue Summary Q1 2024",
                    report_type="revenue_summary",
                    status="completed",
                    output_format="pdf",
                    parameters={},
                    file_path="/tmp/reports/test.pdf",
                    file_size=1024,
                    generated_by=user_id,
                    generated_at=datetime.now(UTC),
                    error_message=None,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            mock_service.create_report.return_value.model_dump = MagicMock(
                return_value={
                    "id": str(report_id),
                    "org_id": str(uuid.uuid4()),
                    "title": "Revenue Summary Q1 2024",
                    "report_type": "revenue_summary",
                    "status": "completed",
                    "output_format": "pdf",
                    "parameters": {},
                    "file_path": "/tmp/reports/test.pdf",
                    "file_size": 1024,
                    "generated_by": str(user_id),
                    "generated_at": datetime.now(UTC).isoformat(),
                    "error_message": None,
                    "created_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            )

            response = await client.post(
                "/api/v1/analytics/reports/generate",
                json={
                    "title": "Revenue Summary Q1 2024",
                    "report_type": "revenue_summary",
                    "output_format": "pdf",
                    "parameters": {},
                },
            )

            assert response.status_code == 201
            mock_service.create_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reports(self, client, mock_db):
        """GET /api/v1/analytics/reports returns paginated reports."""
        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.list_reports = AsyncMock(
                return_value=MagicMock(
                    items=[],
                    next_cursor=None,
                    has_more=False,
                    total_count=0,
                )
            )
            mock_service.list_reports.return_value.model_dump = MagicMock(
                return_value={
                    "items": [],
                    "next_cursor": None,
                    "has_more": False,
                    "total_count": 0,
                }
            )

            response = await client.get("/api/v1/analytics/reports")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_report_not_found(self, client, mock_db):
        """GET /api/v1/analytics/reports/{id}/download returns 404 for missing report."""
        report_id = uuid.uuid4()

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_report_by_id = AsyncMock(return_value=None)

            response = await client.get(f"/api/v1/analytics/reports/{report_id}/download")

            assert response.status_code == 404


# ---------- Events ----------


class TestEventsEndpoint:
    @pytest.mark.asyncio
    async def test_record_event(self, client, mock_db):
        """POST /api/v1/analytics/events records an event."""
        event_id = uuid.uuid4()
        now = datetime.now(UTC)

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.record_event = AsyncMock(
                return_value=MagicMock(
                    id=event_id,
                    org_id=uuid.uuid4(),
                    event_type="page_view",
                    event_source="web",
                    actor_id=None,
                    actor_type="user",
                    entity_type=None,
                    entity_id=None,
                    data={},
                    occurred_at=now,
                    created_at=now,
                )
            )
            mock_service.record_event.return_value.model_dump = MagicMock(
                return_value={
                    "id": str(event_id),
                    "org_id": str(uuid.uuid4()),
                    "event_type": "page_view",
                    "event_source": "web",
                    "actor_id": None,
                    "actor_type": "user",
                    "entity_type": None,
                    "entity_id": None,
                    "data": {},
                    "occurred_at": now.isoformat(),
                    "created_at": now.isoformat(),
                }
            )

            response = await client.post(
                "/api/v1/analytics/events",
                json={
                    "event_type": "page_view",
                    "event_source": "web",
                    "data": {"page": "/books"},
                },
            )

            assert response.status_code == 201
            mock_service.record_event.assert_called_once()


# ---------- Trends ----------


class TestTrendsEndpoint:
    @pytest.mark.asyncio
    async def test_get_trends(self, client, mock_db):
        """GET /api/v1/analytics/trends returns trend data."""
        now = datetime.now(UTC)

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_trends = AsyncMock(
                return_value=MagicMock(
                    metric="revenue",
                    data_points=[],
                    aggregation=AggregationPeriod.MONTHLY,
                    period_start=now - timedelta(days=365),
                    period_end=now,
                    total=Decimal("0.00"),
                    average=Decimal("0.00"),
                    change_percent=None,
                )
            )
            mock_service.get_trends.return_value.model_dump = MagicMock(
                return_value={
                    "metric": "revenue",
                    "data_points": [],
                    "aggregation": "monthly",
                    "period_start": (now - timedelta(days=365)).isoformat(),
                    "period_end": now.isoformat(),
                    "total": "0.00",
                    "average": "0.00",
                    "change_percent": None,
                }
            )

            response = await client.get("/api/v1/analytics/trends")

            assert response.status_code == 200
            mock_service.get_trends.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trends_with_params(self, client, mock_db):
        """GET /api/v1/analytics/trends with query parameters."""
        now = datetime.now(UTC)

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_trends = AsyncMock(
                return_value=MagicMock(
                    metric="revenue",
                    data_points=[],
                    aggregation=AggregationPeriod.WEEKLY,
                    period_start=now - timedelta(days=90),
                    period_end=now,
                    total=Decimal("0.00"),
                    average=Decimal("0.00"),
                    change_percent=None,
                )
            )
            mock_service.get_trends.return_value.model_dump = MagicMock(
                return_value={
                    "metric": "revenue",
                    "data_points": [],
                    "aggregation": "weekly",
                    "period_start": (now - timedelta(days=90)).isoformat(),
                    "period_end": now.isoformat(),
                    "total": "0.00",
                    "average": "0.00",
                    "change_percent": None,
                }
            )

            response = await client.get(
                "/api/v1/analytics/trends",
                params={
                    "metric": "revenue",
                    "aggregation": "weekly",
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                },
            )

            assert response.status_code == 200
