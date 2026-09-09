"""Unit tests for the analytics service layer."""

from datetime import datetime
from decimal import Decimal
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


@pytest.mark.asyncio
async def test_get_dashboard_default_period():
    """Test get_dashboard with default 30-day period."""
    mock_db = AsyncMock()
    org_id = uuid4()

    with patch("app.modules.analytics.service.compute_kpis") as mock_kpis,          patch("app.modules.analytics.service.aggregate_revenue") as mock_rev,          patch("app.modules.analytics.service.aggregate_revenue_by_book") as mock_books,          patch("app.modules.analytics.service.aggregate_revenue_by_platform") as mock_platforms:

        mock_kpis.return_value = {"total_revenue": Decimal("100.00")}
        mock_rev.return_value = []
        mock_books.return_value = []
        mock_platforms.return_value = []
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))

        result = await service.get_dashboard(mock_db, org_id)

        assert result.kpis == {"total_revenue": Decimal("100.00")}
        assert isinstance(result.period_start, datetime)
        assert isinstance(result.period_end, datetime)


@pytest.mark.asyncio
async def test_import_royalty_data_no_content():
    """Test import_royalty_data with no file content."""
    mock_db = AsyncMock()
    org_id = uuid4()
    request = RoyaltyImportRequest(
        platform=Platform.AMAZON_KDP,
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
    org_id = uuid4()
    user_id = uuid4()
    request = ReportRequest(
        title="Test Report",
        report_type=ReportType.PORTFOLIO,
        output_format=OutputFormat.CSV,
    )

    with patch("app.modules.analytics.service.scheduled_report_generation") as mock_task,          patch("app.modules.analytics.service.generate_report") as mock_gen:

        mock_task.delay.side_effect = ConnectionError("Broker unreachable")
        mock_gen.return_value = MagicMock(id=uuid4())

        result = await service.create_report(mock_db, org_id, user_id, request)

        assert result.title == "Test Report"
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_record_event():
    """Test recording an analytics event."""
    mock_db = AsyncMock()
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
