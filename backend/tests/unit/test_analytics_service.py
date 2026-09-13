"""Unit tests for the analytics service layer."""

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.analytics import service
from app.modules.analytics.schemas import (
    AnalyticsEventCreate,
    OutputFormat,
    Platform,
    ReportRequest,
    ReportType,
    RoyaltyImportRequest,
)
from tests.conftest import populate_server_defaults


@pytest.mark.asyncio
async def test_get_dashboard_default_period():
    """Test get_dashboard with default 30-day period."""
    mock_db = AsyncMock()
    org_id = uuid4()

    with (
        patch("app.modules.analytics.service.compute_kpis") as mock_kpis,
        patch("app.modules.analytics.service.aggregate_revenue") as mock_rev,
        patch("app.modules.analytics.service.aggregate_revenue_by_book") as mock_books,
        patch("app.modules.analytics.service.aggregate_revenue_by_platform") as mock_platforms,
    ):
        mock_kpis.return_value = []
        mock_rev.return_value = []
        mock_books.return_value = []
        mock_platforms.return_value = {"kdp": Decimal("100.00")}
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        )

        result = await service.get_dashboard(mock_db, org_id)

        assert result.kpis == []
        assert result.platform_breakdown == {"kdp": Decimal("100.00")}
        assert isinstance(result.period_start, datetime)
        assert isinstance(result.period_end, datetime)


@pytest.mark.asyncio
async def test_import_royalty_data_no_content():
    """Test import_royalty_data with no file content."""
    mock_db = AsyncMock()
    org_id = uuid4()
    request = RoyaltyImportRequest(
        platform=Platform.KDP,
        file_content=None,
    )

    result = await service.import_royalty_data(mock_db, org_id, request)

    assert result.records_imported == 0
    assert result.records_skipped == 0
    assert "No file content provided" in result.errors


@pytest.mark.asyncio
async def test_create_report_celery_failure():
    """Test report creation when Celery is unavailable."""
    mock_db = AsyncMock()
    mock_db.begin = MagicMock(return_value=AsyncMock())
    org_id = uuid4()
    user_id = uuid4()
    request = ReportRequest(
        title="Test Report",
        report_type=ReportType.PORTFOLIO_OVERVIEW,
        output_format=OutputFormat.XLSX,
    )

    with (
        patch("app.modules.analytics.service.scheduled_report_generation") as mock_task,
        patch("app.modules.analytics.service.generate_report") as mock_gen,
    ):
        mock_task.delay.side_effect = ConnectionError("Broker unreachable")
        now = datetime.now(UTC)
        mock_gen.return_value = SimpleNamespace(
            id=uuid4(),
            org_id=org_id,
            title="Test Report",
            report_type=ReportType.PORTFOLIO_OVERVIEW,
            status="completed",
            output_format=OutputFormat.XLSX,
            parameters={},
            file_path=None,
            file_size=None,
            generated_by=user_id,
            generated_at=now,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        result = await service.create_report(mock_db, org_id, user_id, request)

        assert result.title == "Test Report"
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_record_event():
    """Test recording an analytics event."""
    added: list = []
    mock_db = AsyncMock()
    mock_db.add = MagicMock(side_effect=added.append)

    async def _flush(*_a, **_kw):
        for obj in added:
            await populate_server_defaults(obj)

    mock_db.flush = AsyncMock(side_effect=_flush)
    org_id = uuid4()
    event_data = AnalyticsEventCreate(
        event_type="page_view",
        event_source="web",
        actor_id=uuid4(),
        actor_type="user",
        entity_type="book",
        entity_id=uuid4(),
        data={"page": "/dashboard"},
    )

    result = await service.record_event(mock_db, org_id, event_data)

    assert result.event_type == "page_view"
    assert result.event_source == "web"
    assert isinstance(result.occurred_at, datetime)
