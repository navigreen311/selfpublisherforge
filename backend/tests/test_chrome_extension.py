"""Unit tests for the Chrome Extension module.

Covers schemas, service helpers, and router configuration.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.modules.chrome_extension.schemas import (
    AmazonMarketplace,
    ClipSaveRequest,
    ClipSaveResponse,
    ClipType,
    ExtractDataRequest,
    ExtractedAmazonData,
    ExtractedDataResponse,
    QuickResearchResponse,
    ReviewSummary,
)
from app.modules.chrome_extension.service import (
    _estimate_daily_sales,
    save_clip,
    save_extracted_data,
)

# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestExtractedAmazonDataSchema:
    """Validate Pydantic v2 schema for Amazon data extraction."""

    def test_valid_minimal_data(self):
        data = ExtractedAmazonData(asin="B0CTEST001", title="Test Book")
        assert data.asin == "B0CTEST001"
        assert data.marketplace == AmazonMarketplace.US
        assert data.currency == "USD"

    def test_asin_too_short_rejected(self):
        with pytest.raises(ValidationError):
            ExtractedAmazonData(asin="SHORT", title="Bad")

    def test_asin_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ExtractedAmazonData(asin="B0CTOOLONG1", title="Bad")

    def test_full_data_round_trip(self):
        data = ExtractedAmazonData(
            asin="B0CTEST001",
            title="Full Book",
            subtitle="A Subtitle",
            author="Author Name",
            price=9.99,
            currency="GBP",
            bsr=500,
            bsr_categories={"Romance": 100},
            categories=["Romance"],
            keywords=["love"],
            reviews=ReviewSummary(total_reviews=10, average_rating=4.5),
            page_url="https://amazon.com/dp/B0CTEST001",
            marketplace=AmazonMarketplace.UK,
        )
        dumped = data.model_dump()
        assert dumped["bsr"] == 500
        assert dumped["reviews"]["total_reviews"] == 10


class TestResponseSchemas:
    """Ensure response schemas use Pydantic v2 from_attributes."""

    def test_extracted_data_response_from_attributes(self):
        assert ExtractedDataResponse.model_config.get("from_attributes") is True

    def test_clip_save_response_from_attributes(self):
        assert ClipSaveResponse.model_config.get("from_attributes") is True

    def test_quick_research_response_from_attributes(self):
        assert QuickResearchResponse.model_config.get("from_attributes") is True

    def test_extracted_data_response_construction(self):
        resp = ExtractedDataResponse(
            id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            asin="B0CTEST001",
            title="Test",
            bsr=100,
            saved_at=datetime.now(UTC),
        )
        assert resp.asin == "B0CTEST001"

    def test_clip_save_response_construction(self):
        resp = ClipSaveResponse(
            id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            clip_type=ClipType.TEXT,
            title="Clip",
            saved_at=datetime.now(UTC),
        )
        assert resp.clip_type == ClipType.TEXT


class TestClipSaveRequestSchema:
    """Validate clip save request schema."""

    def test_minimal_clip(self):
        req = ClipSaveRequest(content="Some content")
        assert req.clip_type == ClipType.TEXT
        assert req.tags == []

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            ClipSaveRequest(content="")

    def test_invalid_clip_type_rejected(self):
        with pytest.raises(ValidationError):
            ClipSaveRequest(clip_type="invalid", content="test")


# ---------------------------------------------------------------------------
# Service helper tests
# ---------------------------------------------------------------------------


class TestEstimateDailySales:
    """Test the BSR-to-sales estimation helper."""

    def test_zero_bsr_returns_zero(self):
        assert _estimate_daily_sales(0) == 0

    def test_negative_bsr_returns_zero(self):
        assert _estimate_daily_sales(-1) == 0

    def test_low_bsr_high_sales(self):
        sales = _estimate_daily_sales(10)
        assert sales > 0
        assert sales >= _estimate_daily_sales(100)

    def test_high_bsr_low_sales(self):
        sales = _estimate_daily_sales(200_000)
        assert sales == 1

    def test_monotonic_decrease(self):
        """Sales estimates should generally decrease as BSR increases."""
        bsr_values = [50, 500, 5000, 50000, 500000]
        sales = [_estimate_daily_sales(b) for b in bsr_values]
        for i in range(len(sales) - 1):
            assert sales[i] >= sales[i + 1]


# ---------------------------------------------------------------------------
# Service layer tests with mocked DB
# ---------------------------------------------------------------------------


class TestSaveExtractedDataService:
    """Test service.save_extracted_data with mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_save_creates_product_and_returns_response(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        product_id = uuid.uuid4()
        org_id = uuid.uuid4()
        now = datetime.now(UTC)

        async def fake_refresh(obj):
            obj.id = product_id
            obj.org_id = org_id
            obj.created_at = now

        mock_db.refresh = AsyncMock(side_effect=fake_refresh)

        request = ExtractDataRequest(
            data=ExtractedAmazonData(asin="B0CTEST001", title="Test Book", bsr=1000),
            notes="A note",
            tags=["tag1"],
        )

        result = await save_extracted_data(mock_db, org_id, request)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()
        assert result.asin == "B0CTEST001"
        assert result.title == "Test Book"
        assert result.bsr == 1000
        assert result.id == product_id


class TestSaveClipService:
    """Test service.save_clip with mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_save_clip_creates_and_returns_response(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        clip_id = uuid.uuid4()
        org_id = uuid.uuid4()
        now = datetime.now(UTC)

        async def fake_refresh(obj):
            obj.id = clip_id
            obj.org_id = org_id
            obj.created_at = now

        mock_db.refresh = AsyncMock(side_effect=fake_refresh)

        request = ClipSaveRequest(
            clip_type=ClipType.LINK,
            content="https://example.com",
            source_url="https://example.com",
            title="Example",
            tags=["web"],
        )

        result = await save_clip(mock_db, org_id, request)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        assert result.clip_type == ClipType.LINK
        assert result.title == "Example"
        assert result.id == clip_id


# ---------------------------------------------------------------------------
# Router configuration tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify the router is properly configured."""

    def test_router_exists_and_is_api_router(self):
        from fastapi import APIRouter

        from app.modules.chrome_extension.router import router

        assert isinstance(router, APIRouter)

    def test_router_has_extension_prefix(self):
        from app.modules.chrome_extension.router import router

        assert router.prefix == "/extension"

    def test_router_has_correct_tags(self):
        from app.modules.chrome_extension.router import router

        assert "chrome-extension" in router.tags
