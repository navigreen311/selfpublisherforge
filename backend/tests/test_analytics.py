"""Tests for the Analytics & BI module router endpoints.

Covers: dashboard, revenue, royalties, portfolio, reports, events, and trends.
Uses mocked service layer and authentication to isolate endpoint logic.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.analytics.schemas import (
    AggregationPeriod,
    AnalyticsEventResponse,
    DashboardData,
    KPICard,
    OutputFormat,
    Platform,
    PortfolioMetrics,
    ReportResponse,
    ReportStatus,
    ReportType,
    RevenueDataPoint,
    RevenueResponse,
    RoyaltyImportResponse,
    TrendData,
    TrendDataPoint,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_user(org_id, user_id):
    return {"user_id": user_id, "org_id": org_id, "role": "owner"}


@pytest_asyncio.fixture
async def client(mock_user):
    """Yield an HTTP test client with auth and DB dependencies overridden."""
    app = create_app()

    from app.database import get_db
    from app.core.dependencies import get_current_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Dashboard endpoint
# ---------------------------------------------------------------------------

class TestDashboard:
    @pytest.mark.asyncio
    async def test_get_dashboard_returns_200(self, client, org_id):
        """GET /api/v1/analytics/dashboard should return 200 with dashboard data."""
        now = datetime.now(timezone.utc)
        dashboard = DashboardData(
            kpis=[
                KPICard(label="Revenue", value="$1,000.00", change_percent=5.0, change_direction="up"),
            ],
            revenue_chart=[
                RevenueDataPoint(period="2024-01", revenue=Decimal("500.00"), units=20),
            ],
            top_books=[{"title": "My Book", "revenue": "500.00", "units": 20}],
            platform_breakdown={"kdp": Decimal("1000.00")},
            recent_royalties=[],
            period_start=now - timedelta(days=30),
            period_end=now,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_dashboard = AsyncMock(return_value=dashboard)

            response = await client.get("/api/v1/analytics/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert "kpis" in data
            assert "revenue_chart" in data
            assert "top_books" in data
            assert len(data["kpis"]) == 1
            assert data["kpis"][0]["label"] == "Revenue"


# ---------------------------------------------------------------------------
# 2. Revenue endpoint
# ---------------------------------------------------------------------------

class TestRevenue:
    @pytest.mark.asyncio
    async def test_get_revenue_returns_200(self, client, org_id):
        """GET /api/v1/analytics/revenue should return 200 with revenue data."""
        now = datetime.now(timezone.utc)
        revenue = RevenueResponse(
            total_revenue=Decimal("2500.00"),
            total_units=100,
            data_points=[
                RevenueDataPoint(period="2024-01", revenue=Decimal("1200.00"), units=50),
                RevenueDataPoint(period="2024-02", revenue=Decimal("1300.00"), units=50),
            ],
            period_start=now - timedelta(days=365),
            period_end=now,
            aggregation=AggregationPeriod.MONTHLY,
            by_platform={"kdp": Decimal("2000.00"), "ingram_spark": Decimal("500.00")},
            by_book=[],
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_revenue = AsyncMock(return_value=revenue)

            response = await client.get("/api/v1/analytics/revenue")

            assert response.status_code == 200
            data = response.json()
            assert data["total_units"] == 100
            assert len(data["data_points"]) == 2
            mock_service.get_revenue.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_revenue_with_filters(self, client, org_id):
        """GET /api/v1/analytics/revenue with platform and date filters."""
        now = datetime.now(timezone.utc)
        revenue = RevenueResponse(
            total_revenue=Decimal("800.00"),
            total_units=30,
            data_points=[],
            period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2024, 6, 30, 23, 59, 59, 999999, tzinfo=timezone.utc),
            aggregation=AggregationPeriod.WEEKLY,
            by_platform={},
            by_book=[],
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_revenue = AsyncMock(return_value=revenue)

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
            data = response.json()
            assert data["aggregation"] == "weekly"


# ---------------------------------------------------------------------------
# 3. Portfolio endpoint
# ---------------------------------------------------------------------------

class TestPortfolio:
    @pytest.mark.asyncio
    async def test_get_portfolio_returns_200(self, client, org_id):
        """GET /api/v1/analytics/portfolio should return portfolio metrics."""
        now = datetime.now(timezone.utc)
        portfolio = PortfolioMetrics(
            total_books=15,
            total_revenue=Decimal("12000.00"),
            total_units_sold=600,
            total_expenses=Decimal("2000.00"),
            net_profit=Decimal("10000.00"),
            avg_roi=Decimal("5.00"),
            platform_breakdown={"kdp": {"revenue": "10000.00"}},
            format_breakdown={"ebook": {"revenue": "8000.00"}},
            top_books=[{"title": "Best Seller", "revenue": "5000.00"}],
            snapshot_date=now,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_portfolio_metrics = AsyncMock(return_value=portfolio)

            response = await client.get("/api/v1/analytics/portfolio")

            assert response.status_code == 200
            data = response.json()
            assert data["total_books"] == 15
            assert data["total_units_sold"] == 600
            mock_service.get_portfolio_metrics.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Events endpoint
# ---------------------------------------------------------------------------

class TestEvents:
    @pytest.mark.asyncio
    async def test_record_event_returns_201(self, client, org_id):
        """POST /api/v1/analytics/events should record an event and return 201."""
        event_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        event_response = AnalyticsEventResponse(
            id=event_id,
            org_id=org_id,
            event_type="book_published",
            event_source="system",
            actor_id=None,
            actor_type="user",
            entity_type="book",
            entity_id=uuid.uuid4(),
            data={"book_title": "My New Book"},
            occurred_at=now,
            created_at=now,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.record_event = AsyncMock(return_value=event_response)

            response = await client.post(
                "/api/v1/analytics/events",
                json={
                    "event_type": "book_published",
                    "event_source": "system",
                    "entity_type": "book",
                    "data": {"book_title": "My New Book"},
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["event_type"] == "book_published"
            assert data["event_source"] == "system"
            assert data["data"]["book_title"] == "My New Book"
            mock_service.record_event.assert_called_once()


# ---------------------------------------------------------------------------
# 5. Reports endpoints
# ---------------------------------------------------------------------------

class TestReports:
    @pytest.mark.asyncio
    async def test_generate_report_returns_201(self, client, org_id, user_id):
        """POST /api/v1/analytics/reports/generate should create a report."""
        report_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        report_response = ReportResponse(
            id=report_id,
            org_id=org_id,
            title="Q1 Revenue Summary",
            report_type="revenue_summary",
            status="completed",
            output_format="pdf",
            parameters={},
            file_path="/tmp/reports/test.pdf",
            file_size=2048,
            generated_by=user_id,
            generated_at=now,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.create_report = AsyncMock(return_value=report_response)

            response = await client.post(
                "/api/v1/analytics/reports/generate",
                json={
                    "title": "Q1 Revenue Summary",
                    "report_type": "revenue_summary",
                    "output_format": "pdf",
                    "parameters": {},
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Q1 Revenue Summary"
            assert data["report_type"] == "revenue_summary"
            assert data["status"] == "completed"
            mock_service.create_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reports_returns_200(self, client, org_id):
        """GET /api/v1/analytics/reports should return paginated reports."""
        from app.core.pagination import PaginatedResponse

        paginated = PaginatedResponse[ReportResponse](
            items=[],
            next_cursor=None,
            has_more=False,
            total_count=0,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.list_reports = AsyncMock(return_value=paginated)

            response = await client.get("/api/v1/analytics/reports")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_download_report_not_found_returns_404(self, client, org_id):
        """GET /api/v1/analytics/reports/{id}/download returns 404 when report missing."""
        report_id = uuid.uuid4()

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_report_by_id = AsyncMock(return_value=None)

            response = await client.get(
                f"/api/v1/analytics/reports/{report_id}/download"
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "Report not found"


# ---------------------------------------------------------------------------
# 6. Trends endpoint
# ---------------------------------------------------------------------------

class TestTrends:
    @pytest.mark.asyncio
    async def test_get_trends_returns_200(self, client, org_id):
        """GET /api/v1/analytics/trends should return trend data."""
        now = datetime.now(timezone.utc)
        trends = TrendData(
            metric="revenue",
            data_points=[
                TrendDataPoint(period="2024-01", value=Decimal("500.00")),
                TrendDataPoint(period="2024-02", value=Decimal("700.00")),
            ],
            aggregation=AggregationPeriod.MONTHLY,
            period_start=now - timedelta(days=365),
            period_end=now,
            total=Decimal("1200.00"),
            average=Decimal("600.00"),
            change_percent=40.0,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_trends = AsyncMock(return_value=trends)

            response = await client.get("/api/v1/analytics/trends")

            assert response.status_code == 200
            data = response.json()
            assert data["metric"] == "revenue"
            assert len(data["data_points"]) == 2
            assert data["change_percent"] == 40.0
            mock_service.get_trends.assert_called_once()


# ---------------------------------------------------------------------------
# 7. Royalties endpoints
# ---------------------------------------------------------------------------

class TestRoyalties:
    @pytest.mark.asyncio
    async def test_get_royalties_returns_200(self, client, org_id):
        """GET /api/v1/analytics/royalties should return paginated royalties."""
        from app.core.pagination import PaginatedResponse
        from app.modules.analytics.schemas import RoyaltyRecordResponse

        paginated = PaginatedResponse[RoyaltyRecordResponse](
            items=[],
            next_cursor=None,
            has_more=False,
            total_count=0,
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.get_royalties = AsyncMock(return_value=paginated)

            response = await client.get("/api/v1/analytics/royalties")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total_count"] == 0
            mock_service.get_royalties.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_royalties_returns_200(self, client, org_id):
        """POST /api/v1/analytics/royalties/import should accept CSV data."""
        csv_content = base64.b64encode(
            b"Title,ASIN,Units Sold,Royalty\nMy Book,B001,10,29.99"
        ).decode()

        import_response = RoyaltyImportResponse(
            import_batch_id=uuid.uuid4(),
            records_imported=1,
            records_skipped=0,
            errors=[],
            platform="kdp",
        )

        with patch("app.modules.analytics.router.service") as mock_service:
            mock_service.import_royalty_data = AsyncMock(return_value=import_response)

            response = await client.post(
                "/api/v1/analytics/royalties/import",
                json={
                    "platform": "kdp",
                    "file_content": csv_content,
                    "file_name": "royalties.csv",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["records_imported"] == 1
            assert data["records_skipped"] == 0
            assert data["platform"] == "kdp"
            mock_service.import_royalty_data.assert_called_once()
