"""Integration tests for the Advertising Intelligence API endpoints."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event

from app.database import Base, get_db
from app.main import create_app
from app.modules.advertising.models import (
    Campaign,
    CampaignPerformance,
    KeywordBid,
    AdCreative,
)
from app.modules.advertising.schemas import (
    AdPlatform,
    CampaignStatus,
    CampaignType,
    BidStrategy,
    MatchType,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create a test database and session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def mock_user(user_id, org_id):
    return {"user_id": user_id, "org_id": org_id, "role": "admin"}


@pytest_asyncio.fixture
async def client(test_db, mock_user):
    """Create a test HTTP client with auth mocked."""
    app = create_app()

    async def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db

    from app.core.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_campaign(test_db, org_id):
    """Create a sample campaign in the database."""
    campaign = Campaign(
        org_id=org_id,
        name="Test Campaign",
        platform=AdPlatform.AMAZON.value,
        campaign_type=CampaignType.SPONSORED_PRODUCTS.value,
        status=CampaignStatus.ACTIVE.value,
        daily_budget=50.0,
        total_budget=1500.0,
        bid_strategy=BidStrategy.MANUAL.value,
        target_acos=30.0,
        targeting_keywords=["fantasy books", "epic fantasy"],
        negative_keywords=["free"],
    )
    test_db.add(campaign)
    await test_db.flush()
    await test_db.refresh(campaign)
    return campaign


@pytest_asyncio.fixture
async def sample_performance(test_db, sample_campaign):
    """Create sample performance records for a campaign."""
    records = []
    base_date = datetime.now(timezone.utc) - timedelta(days=7)
    for i in range(7):
        perf = CampaignPerformance(
            campaign_id=sample_campaign.id,
            date=base_date + timedelta(days=i),
            impressions=1000 + i * 100,
            clicks=50 + i * 5,
            spend=25.0 + i * 2,
            sales=75.0 + i * 5,
            orders=5 + i,
            acos=33.3 - i,
            roas=3.0 + i * 0.1,
            ctr=5.0 + i * 0.2,
            cpc=0.50 - i * 0.01,
            conversion_rate=10.0 + i * 0.5,
        )
        test_db.add(perf)
        records.append(perf)
    await test_db.flush()
    return records


@pytest_asyncio.fixture
async def sample_keywords(test_db, sample_campaign):
    """Create sample keyword bids for a campaign."""
    keywords = []
    kw_data = [
        ("fantasy books", 1.50, False, 500, 25, 37.5, 100.0, 37.5),
        ("epic fantasy", 1.00, False, 300, 15, 15.0, 80.0, 18.75),
        ("dragon books", 0.75, False, 200, 10, 7.5, 30.0, 25.0),
        ("free", 0.0, True, 0, 0, 0.0, 0.0, 0.0),
    ]
    for keyword, bid, is_neg, imps, clicks, spend, sales, acos in kw_data:
        kw = KeywordBid(
            campaign_id=sample_campaign.id,
            keyword=keyword,
            match_type=MatchType.BROAD.value,
            bid_amount=bid,
            is_negative=is_neg,
            impressions=imps,
            clicks=clicks,
            spend=spend,
            sales=sales,
            acos=acos,
        )
        test_db.add(kw)
        keywords.append(kw)
    await test_db.flush()
    for kw in keywords:
        await test_db.refresh(kw)
    return keywords


@pytest_asyncio.fixture
async def sample_creative(test_db, org_id, sample_campaign):
    """Create a sample ad creative."""
    creative = AdCreative(
        org_id=org_id,
        campaign_id=sample_campaign.id,
        headline="Discover Epic Fantasy Adventures",
        body_text="Dive into a world of dragons and magic. Your next adventure awaits.",
        call_to_action="Buy Now",
        status="active",
        impressions=1000,
        clicks=50,
        ctr=5.0,
        conversions=10,
    )
    test_db.add(creative)
    await test_db.flush()
    await test_db.refresh(creative)
    return creative


# ─── Campaign API Tests ──────────────────────────────────────────────────────

class TestCampaignEndpoints:
    """Test campaign CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_campaign(self, client):
        """POST /api/v1/ads/campaigns should create a new campaign."""
        response = await client.post(
            "/api/v1/ads/campaigns",
            json={
                "name": "New Campaign",
                "platform": "amazon",
                "campaign_type": "sponsored_products",
                "daily_budget": 25.0,
                "bid_strategy": "manual",
                "target_acos": 30.0,
                "targeting_keywords": ["test keyword"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Campaign"
        assert data["platform"] == "amazon"
        assert data["status"] == "draft"
        assert data["daily_budget"] == 25.0
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_campaign_validation(self, client):
        """POST /api/v1/ads/campaigns should validate required fields."""
        response = await client.post(
            "/api/v1/ads/campaigns",
            json={
                "name": "",  # empty name
                "platform": "amazon",
                "campaign_type": "sponsored_products",
                "daily_budget": -5.0,  # negative budget
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_campaigns(self, client, sample_campaign):
        """GET /api/v1/ads/campaigns should list campaigns."""
        response = await client.get("/api/v1/ads/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_list_campaigns_filter_platform(self, client, sample_campaign):
        """GET /api/v1/ads/campaigns?platform=amazon should filter by platform."""
        response = await client.get("/api/v1/ads/campaigns?platform=amazon")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["platform"] == "amazon"

    @pytest.mark.asyncio
    async def test_list_campaigns_filter_status(self, client, sample_campaign):
        """GET /api/v1/ads/campaigns?status=active should filter by status."""
        response = await client.get("/api/v1/ads/campaigns?status=active")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_campaign(self, client, sample_campaign):
        """GET /api/v1/ads/campaigns/{id} should return campaign details."""
        response = await client.get(f"/api/v1/ads/campaigns/{sample_campaign.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_campaign.id)
        assert data["name"] == "Test Campaign"
        assert "performance_summary" in data

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, client):
        """GET /api/v1/ads/campaigns/{id} should return 404 for non-existent."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/ads/campaigns/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_campaign(self, client, sample_campaign):
        """PATCH /api/v1/ads/campaigns/{id} should update campaign."""
        response = await client.patch(
            f"/api/v1/ads/campaigns/{sample_campaign.id}",
            json={
                "name": "Updated Campaign",
                "daily_budget": 75.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign"
        assert data["daily_budget"] == 75.0

    @pytest.mark.asyncio
    async def test_update_campaign_status(self, client, sample_campaign):
        """PATCH /api/v1/ads/campaigns/{id} should update campaign status."""
        response = await client.patch(
            f"/api/v1/ads/campaigns/{sample_campaign.id}",
            json={"status": "paused"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"

    @pytest.mark.asyncio
    async def test_update_campaign_not_found(self, client):
        """PATCH /api/v1/ads/campaigns/{id} should return 404."""
        fake_id = uuid4()
        response = await client.patch(
            f"/api/v1/ads/campaigns/{fake_id}",
            json={"name": "Ghost"},
        )
        assert response.status_code == 404


# ─── Performance API Tests ───────────────────────────────────────────────────

class TestPerformanceEndpoints:
    """Test performance data endpoints."""

    @pytest.mark.asyncio
    async def test_get_performance(self, client, sample_campaign, sample_performance):
        """GET /api/v1/ads/campaigns/{id}/performance should return data."""
        response = await client.get(
            f"/api/v1/ads/campaigns/{sample_campaign.id}/performance"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7
        for record in data:
            assert "impressions" in record
            assert "clicks" in record
            assert "spend" in record
            assert "sales" in record
            assert "acos" in record

    @pytest.mark.asyncio
    async def test_get_performance_date_filter(
        self, client, sample_campaign, sample_performance
    ):
        """GET /api/v1/ads/campaigns/{id}/performance with date range."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        response = await client.get(
            f"/api/v1/ads/campaigns/{sample_campaign.id}/performance",
            params={"date_from": yesterday},
        )
        assert response.status_code == 200


# ─── Optimization API Tests ─────────────────────────────────────────────────

class TestOptimizationEndpoints:
    """Test campaign optimization endpoints."""

    @pytest.mark.asyncio
    async def test_optimize_campaign(
        self, client, sample_campaign, sample_keywords
    ):
        """POST /api/v1/ads/campaigns/{id}/optimize should return suggestions."""
        response = await client.post(
            f"/api/v1/ads/campaigns/{sample_campaign.id}/optimize",
            json={
                "target_acos": 25.0,
                "max_bid_increase_pct": 20.0,
                "max_bid_decrease_pct": 30.0,
                "min_data_points": 1,  # low threshold for test data
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == str(sample_campaign.id)
        assert data["target_acos"] == 25.0
        assert "bid_adjustments" in data
        assert "keywords_to_negate" in data
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_optimize_campaign_default_params(
        self, client, sample_campaign, sample_keywords
    ):
        """POST /api/v1/ads/campaigns/{id}/optimize with no body."""
        response = await client.post(
            f"/api/v1/ads/campaigns/{sample_campaign.id}/optimize",
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_optimize_campaign_not_found(self, client):
        """POST /api/v1/ads/campaigns/{id}/optimize for non-existent campaign."""
        fake_id = uuid4()
        response = await client.post(
            f"/api/v1/ads/campaigns/{fake_id}/optimize",
        )
        assert response.status_code == 404


# ─── Keyword Bid API Tests ──────────────────────────────────────────────────

class TestKeywordBidEndpoints:
    """Test keyword bid management endpoints."""

    @pytest.mark.asyncio
    async def test_list_keyword_bids(self, client, sample_campaign, sample_keywords):
        """GET /api/v1/ads/keyword-bids should return keyword bids."""
        response = await client.get(
            f"/api/v1/ads/keyword-bids?campaign_id={sample_campaign.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # including negative keyword

    @pytest.mark.asyncio
    async def test_update_keyword_bids(self, client, sample_campaign, sample_keywords):
        """PATCH /api/v1/ads/keyword-bids should update bids."""
        kw = sample_keywords[0]  # "fantasy books"
        response = await client.patch(
            "/api/v1/ads/keyword-bids",
            json={
                "updates": [
                    {"id": str(kw.id), "bid_amount": 2.00},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]["bid_amount"] == 2.00


# ─── Creative API Tests ─────────────────────────────────────────────────────

class TestCreativeEndpoints:
    """Test ad creative management endpoints."""

    @pytest.mark.asyncio
    async def test_list_creatives(self, client, sample_creative):
        """GET /api/v1/ads/creatives should return creatives."""
        response = await client.get("/api/v1/ads/creatives")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["headline"] == "Discover Epic Fantasy Adventures"

    @pytest.mark.asyncio
    async def test_generate_creatives(self, client):
        """POST /api/v1/ads/creatives/generate should generate AI creatives."""
        response = await client.post(
            "/api/v1/ads/creatives/generate",
            json={
                "book_title": "The Dragon's Prophecy",
                "book_description": "A young wizard discovers an ancient prophecy that will change the fate of the kingdom.",
                "genre": "Fantasy",
                "target_audience": "Fantasy readers 18-45",
                "tone": "exciting",
                "num_variations": 3,
                "platform": "amazon",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["variations"]) == 3
        assert data["platform"] == "amazon"
        assert data["book_title"] == "The Dragon's Prophecy"
        for v in data["variations"]:
            assert "headline" in v
            assert "body_text" in v
            assert "call_to_action" in v

    @pytest.mark.asyncio
    async def test_generate_creatives_facebook(self, client):
        """POST /api/v1/ads/creatives/generate for Facebook platform."""
        response = await client.post(
            "/api/v1/ads/creatives/generate",
            json={
                "book_title": "Summer Romance",
                "book_description": "A heartwarming love story set on the Italian coast.",
                "genre": "Romance",
                "num_variations": 2,
                "platform": "facebook",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["variations"]) == 2
        assert data["platform"] == "facebook"


# ─── Dashboard API Tests ─────────────────────────────────────────────────────

class TestDashboardEndpoint:
    """Test the aggregate dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard(
        self, client, sample_campaign, sample_performance
    ):
        """GET /api/v1/ads/dashboard should return aggregate data."""
        response = await client.get("/api/v1/ads/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_active_campaigns" in data
        assert "total_spend_today" in data
        assert "total_spend_month" in data
        assert "total_sales_month" in data
        assert "overall_acos" in data
        assert "overall_roas" in data
        assert "top_campaigns" in data
        assert "platform_breakdown" in data
        assert data["total_active_campaigns"] >= 1

    @pytest.mark.asyncio
    async def test_get_dashboard_empty(self, client):
        """GET /api/v1/ads/dashboard with no campaigns."""
        response = await client.get("/api/v1/ads/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_active_campaigns"] == 0
        assert data["total_spend_today"] == 0.0
