"""Unit tests for the Advertising service layer.

Covers campaign CRUD, performance tracking, keyword bids, ad creatives,
optimization, and Facebook Ads integration.

All tests use mocked AsyncSession -- no real DB.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.modules.advertising.schemas import (
    AdPlatform,
    BidStrategy,
    CampaignCreate,
    CampaignFilter,
    CampaignStatus,
    CampaignType,
    CampaignUpdate,
    CreativeGenerateRequest,
    FacebookCampaignCreate,
    FacebookObjective,
    FacebookCampaignStatus,
    FacebookCampaignUpdate,
    KeywordBidBulkUpdate,
    OptimizationRequest,
    PerformanceQuery,
)
from app.modules.advertising.service import AdvertisingService


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
def campaign_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Return an AdvertisingService instance with mocked DB."""
    return AdvertisingService(mock_db)


def _make_campaign(**overrides):
    """Factory helper to create a Campaign mock."""
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
        "name": "Test Campaign",
        "platform": AdPlatform.AMAZON.value,
        "campaign_type": CampaignType.SPONSORED_PRODUCTS.value,
        "status": CampaignStatus.DRAFT.value,
        "book_id": uuid.uuid4(),
        "daily_budget": Decimal("20.00"),
        "total_budget": Decimal("500.00"),
        "bid_strategy": BidStrategy.MANUAL.value,
        "target_acos": Decimal("25.00"),
        "created_at": datetime.now(UTC),
        "deleted_at": None,
    }
    defaults.update(overrides)
    campaign = MagicMock()
    for k, v in defaults.items():
        setattr(campaign, k, v)
    return campaign


# ===========================================================================
# Tests: list_campaigns
# ===========================================================================

class TestListCampaigns:
    """Tests for AdvertisingService.list_campaigns."""

    @pytest.mark.asyncio
    async def test_returns_campaigns_with_performance(
        self,
        service,
        org_id,
    ):
        """list_campaigns should return campaigns with performance summaries."""
        campaign1 = _make_campaign()
        campaign2 = _make_campaign()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [campaign1, campaign2]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        # Mock performance summary
        mock_perf_result = MagicMock()
        mock_perf_result.one_or_none.return_value = None

        service.db.execute.side_effect = [mock_count, mock_result, mock_perf_result, mock_perf_result]

        campaigns, next_cursor, total = await service.list_campaigns(org_id, limit=20)

        assert len(campaigns) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_filters_by_platform(
        self,
        service,
        org_id,
    ):
        """list_campaigns should filter by platform when provided."""
        campaign1 = _make_campaign(platform=AdPlatform.AMAZON.value)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [campaign1]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        mock_perf_result = MagicMock()
        mock_perf_result.one_or_none.return_value = None

        service.db.execute.side_effect = [mock_count, mock_result, mock_perf_result]

        filters = CampaignFilter(platform=AdPlatform.AMAZON)
        campaigns, _, total = await service.list_campaigns(org_id, filters=filters)

        assert len(campaigns) == 1


# ===========================================================================
# Tests: get_campaign
# ===========================================================================

class TestGetCampaign:
    """Tests for AdvertisingService.get_campaign."""

    @pytest.mark.asyncio
    async def test_returns_campaign_with_performance(
        self,
        service,
        org_id,
        campaign_id,
    ):
        """get_campaign should return campaign with performance summary."""
        campaign = _make_campaign(id=campaign_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = campaign

        mock_perf_result = MagicMock()
        mock_perf_result.one_or_none.return_value = None

        service.db.execute.side_effect = [mock_result, mock_perf_result]

        result = await service.get_campaign(org_id, campaign_id)

        assert result.id == campaign_id

    @pytest.mark.asyncio
    async def test_raises_not_found_when_campaign_missing(
        self,
        service,
        org_id,
        campaign_id,
    ):
        """get_campaign should raise AppException when campaign not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute.return_value = mock_result

        with pytest.raises(AppException) as exc_info:
            await service.get_campaign(org_id, campaign_id)

        assert exc_info.value.status_code == 404


# ===========================================================================
# Tests: create_campaign
# ===========================================================================

class TestCreateCampaign:
    """Tests for AdvertisingService.create_campaign."""

    @pytest.mark.asyncio
    async def test_creates_campaign_and_keyword_bids(
        self,
        service,
        org_id,
        book_id,
    ):
        """create_campaign should create campaign and keyword bids."""
        data = CampaignCreate(
            name="New Campaign",
            platform=AdPlatform.AMAZON,
            campaign_type=CampaignType.SPONSORED_PRODUCTS,
            book_id=book_id,
            daily_budget=Decimal("25.00"),
            bid_strategy=BidStrategy.MANUAL,
            targeting_keywords=["thriller", "suspense"],
            negative_keywords=["horror"],
        )

        result = await service.create_campaign(org_id, data)

        assert service.db.add.call_count >= 4  # campaign + 3 keywords
        service.db.flush.assert_awaited()


# ===========================================================================
# Tests: update_campaign
# ===========================================================================

class TestUpdateCampaign:
    """Tests for AdvertisingService.update_campaign."""

    @pytest.mark.asyncio
    async def test_updates_campaign_fields(
        self,
        service,
        org_id,
        campaign_id,
    ):
        """update_campaign should update campaign fields."""
        campaign = _make_campaign(id=campaign_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = campaign
        service.db.execute.return_value = mock_result

        update_data = CampaignUpdate(
            name="Updated Campaign Name",
            daily_budget=Decimal("30.00"),
        )

        result = await service.update_campaign(org_id, campaign_id, update_data)

        assert campaign.name == "Updated Campaign Name"
        assert campaign.daily_budget == Decimal("30.00")


# ===========================================================================
# Tests: get_campaign_performance
# ===========================================================================

class TestGetCampaignPerformance:
    """Tests for AdvertisingService.get_campaign_performance."""

    @pytest.mark.asyncio
    async def test_returns_performance_records(
        self,
        service,
        org_id,
        campaign_id,
    ):
        """get_campaign_performance should return performance records."""
        # Mock campaign exists
        campaign_result = MagicMock()
        campaign_result.scalar_one_or_none.return_value = campaign_id

        # Mock performance records
        perf1 = MagicMock(date=datetime(2025, 1, 1).date(), impressions=1000, clicks=50)
        perf2 = MagicMock(date=datetime(2025, 1, 2).date(), impressions=1200, clicks=60)

        perf_result = MagicMock()
        perf_result.scalars.return_value.all.return_value = [perf1, perf2]

        service.db.execute.side_effect = [campaign_result, perf_result]

        query = PerformanceQuery(
            date_from=datetime(2025, 1, 1).date(),
            date_to=datetime(2025, 1, 31).date(),
        )

        result = await service.get_campaign_performance(org_id, campaign_id, query)

        assert len(result) == 2


# ===========================================================================
# Tests: Keyword Bids
# ===========================================================================

class TestKeywordBids:
    """Tests for keyword bid management."""

    @pytest.mark.asyncio
    async def test_list_keyword_bids(
        self,
        service,
        org_id,
        campaign_id,
    ):
        """list_keyword_bids should return keyword bids for a campaign."""
        # Mock campaign exists
        campaign_result = MagicMock()
        campaign_result.scalar_one_or_none.return_value = campaign_id

        # Mock keyword bids
        bid1 = MagicMock(keyword="thriller", bid_amount=Decimal("0.75"))
        bid2 = MagicMock(keyword="suspense", bid_amount=Decimal("0.85"))

        bids_result = MagicMock()
        bids_result.scalars.return_value.all.return_value = [bid1, bid2]

        service.db.execute.side_effect = [campaign_result, bids_result]

        result = await service.list_keyword_bids(org_id, campaign_id)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_keyword_bids_bulk(
        self,
        service,
        org_id,
    ):
        """update_keyword_bids should bulk update keyword bid amounts."""
        bid_id = uuid.uuid4()
        bid = MagicMock(id=bid_id, bid_amount=Decimal("0.75"))

        bid_result = MagicMock()
        bid_result.scalar_one_or_none.return_value = bid
        service.db.execute.return_value = bid_result

        bulk_update = KeywordBidBulkUpdate(
            updates=[
                {"id": str(bid_id), "bid_amount": Decimal("1.00")},
            ]
        )

        result = await service.update_keyword_bids(org_id, bulk_update)

        assert len(result) == 1
        assert bid.bid_amount == Decimal("1.00")


# ===========================================================================
# Tests: Ad Creatives
# ===========================================================================

class TestAdCreatives:
    """Tests for ad creative generation and listing."""

    @pytest.mark.asyncio
    async def test_list_creatives(
        self,
        service,
        org_id,
    ):
        """list_creatives should return ad creatives for an org."""
        creative1 = MagicMock(id=uuid.uuid4(), headline="Creative 1")
        creative2 = MagicMock(id=uuid.uuid4(), headline="Creative 2")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [creative1, creative2]
        service.db.execute.return_value = mock_result

        result = await service.list_creatives(org_id)

        assert len(result) == 2

    @pytest.mark.asyncio
    @patch.object(AdvertisingService, "creative_generator")
    async def test_generate_creatives(
        self,
        mock_creative_generator,
        service,
        org_id,
        book_id,
    ):
        """generate_creatives should generate and save ad creatives."""
        mock_creative_generator.generate_creatives = AsyncMock(
            return_value=MagicMock(
                variations=[
                    MagicMock(
                        headline="Great Thriller",
                        body_text="A page-turner you won't put down",
                        call_to_action="Buy Now",
                    ),
                ]
            )
        )

        request = CreativeGenerateRequest(
            book_id=book_id,
            platform=AdPlatform.AMAZON,
            num_variations=1,
        )

        result = await service.generate_creatives(org_id, request)

        assert len(result.variations) == 1
        service.db.add.assert_called()


# ===========================================================================
# Tests: Optimization
# ===========================================================================

class TestOptimization:
    """Tests for campaign optimization."""

    @pytest.mark.asyncio
    @patch.object(AdvertisingService, "optimizer")
    async def test_optimize_campaign(
        self,
        mock_optimizer,
        service,
        org_id,
        campaign_id,
    ):
        """optimize_campaign should generate optimization suggestions."""
        campaign = _make_campaign(id=campaign_id)

        campaign_result = MagicMock()
        campaign_result.scalar_one_or_none.return_value = campaign

        # Mock keywords
        kw_result = MagicMock()
        kw_result.scalars.return_value.all.return_value = []

        # Mock performance summary
        perf_result = MagicMock()
        perf_result.one_or_none.return_value = None

        service.db.execute.side_effect = [campaign_result, kw_result, perf_result]

        mock_optimizer.optimize_campaign.return_value = MagicMock(
            recommendations=["Increase bids on high-performing keywords"],
            estimated_improvement=Decimal("15.00"),
        )

        request = OptimizationRequest(
            target_acos=Decimal("20.00"),
            min_data_points=30,
        )

        result = await service.optimize_campaign(org_id, campaign_id, request)

        assert len(result.recommendations) > 0


# ===========================================================================
# Tests: Dashboard
# ===========================================================================

class TestGetDashboard:
    """Tests for AdvertisingService.get_dashboard."""

    @pytest.mark.asyncio
    async def test_returns_dashboard_metrics(
        self,
        service,
        org_id,
    ):
        """get_dashboard should return aggregated advertising metrics."""
        # Mock active campaigns count
        active_count_result = MagicMock()
        active_count_result.scalar.return_value = 5

        # Mock today's spend
        today_spend_result = MagicMock()
        today_spend_result.scalar.return_value = Decimal("50.00")

        # Mock month stats
        month_result = MagicMock()
        month_result.one_or_none.return_value = MagicMock(
            spend=Decimal("800.00"),
            sales=Decimal("3200.00"),
        )

        # Mock top campaigns
        top_campaigns_result = MagicMock()
        top_campaigns_result.scalars.return_value.all.return_value = []

        # Mock platform breakdown queries
        platform_campaigns_result = MagicMock()
        platform_campaigns_result.scalars.return_value.all.return_value = []

        service.db.execute.side_effect = [
            active_count_result,
            today_spend_result,
            month_result,
            top_campaigns_result,
            platform_campaigns_result,
            platform_campaigns_result,
        ]

        result = await service.get_dashboard(org_id)

        assert result.total_active_campaigns == 5
        assert result.total_spend_today == Decimal("50.00")


# ===========================================================================
# Tests: Facebook Ads
# ===========================================================================

class TestFacebookAds:
    """Tests for Facebook Ads integration."""

    @pytest.mark.asyncio
    @patch.object(AdvertisingService, "facebook_client")
    async def test_facebook_create_campaign(
        self,
        mock_facebook_client,
        service,
        org_id,
    ):
        """facebook_create_campaign should create Facebook campaign via API."""
        mock_facebook_client.create_campaign = AsyncMock(
            return_value={
                "external_campaign_id": "fb123",
                "created": True,
                "status": FacebookCampaignStatus.ACTIVE.value,
            }
        )

        data = FacebookCampaignCreate(
            name="FB Campaign",
            objective=FacebookObjective.OUTCOME_SALES,
            daily_budget=Decimal("50.00"),
            status=FacebookCampaignStatus.ACTIVE,
        )

        result = await service.facebook_create_campaign(org_id, data)

        assert result.external_campaign_id == "fb123"
        assert result.created is True
