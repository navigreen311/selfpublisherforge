"""Integration tests for Facebook Ads router endpoints."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event

from app.database import Base, get_db
from app.main import create_app
from app.modules.advertising.facebook_ads import FacebookAdsClient, FacebookAdsError


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
async def unauthed_client(test_db):
    """Create a test HTTP client WITHOUT auth override (no token)."""
    app = create_app()

    async def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    # Deliberately do NOT override get_current_user so auth is enforced

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_fb_client():
    """Return a fully-mocked FacebookAdsClient with sensible defaults."""
    mock = AsyncMock(spec=FacebookAdsClient)

    # create_campaign
    mock.create_campaign.return_value = {
        "external_campaign_id": "fb_camp_123",
        "status": "paused",
        "objective": "OUTCOME_SALES",
        "daily_budget": 50.0,
        "created": True,
    }

    # list_campaigns
    mock.list_campaigns.return_value = {
        "campaigns": [
            {
                "external_campaign_id": "fb_camp_123",
                "name": "Test FB Campaign",
                "objective": "OUTCOME_SALES",
                "status": "active",
                "daily_budget": 50.0,
            },
            {
                "external_campaign_id": "fb_camp_456",
                "name": "Second FB Campaign",
                "objective": "OUTCOME_TRAFFIC",
                "status": "paused",
                "daily_budget": 25.0,
            },
        ],
        "total_count": 2,
    }

    # get_campaign
    mock.get_campaign.return_value = {
        "external_campaign_id": "fb_camp_123",
        "name": "Test FB Campaign",
        "objective": "OUTCOME_SALES",
        "status": "active",
        "daily_budget": 50.0,
        "created_time": "2025-01-01T00:00:00+0000",
        "updated_time": "2025-01-02T00:00:00+0000",
    }

    # update_campaign
    mock.update_campaign.return_value = {
        "external_campaign_id": "fb_camp_123",
        "updated": True,
        "changes": {"name": "Updated Campaign"},
    }

    # pause_campaign
    mock.pause_campaign.return_value = {
        "external_campaign_id": "fb_camp_123",
        "updated": True,
        "changes": {"status": "PAUSED"},
    }

    # get_campaign_insights
    mock.get_campaign_insights.return_value = {
        "external_campaign_id": "fb_camp_123",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "metrics": {
            "impressions": 10000.0,
            "clicks": 500.0,
            "spend": 250.0,
            "ctr": 5.0,
            "cpc": 0.50,
            "cpm": 25.0,
            "reach": 8000.0,
        },
        "report_status": "completed",
    }

    # create_custom_audience
    mock.create_custom_audience.return_value = {
        "audience_id": "aud_789",
        "name": "Book Readers",
        "source_type": "CUSTOM",
        "created": True,
    }

    return mock


# ─── Create Facebook Campaign Tests ─────────────────────────────────────────


class TestCreateFacebookCampaign:
    """Test POST /api/v1/ads/facebook/campaigns."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_create_campaign_success(self, mock_fb_cls, client, mock_fb_client):
        """POST /api/v1/ads/facebook/campaigns with valid data should return 201."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "name": "My Facebook Campaign",
                "objective": "OUTCOME_SALES",
                "daily_budget": 50.0,
                "status": "PAUSED",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert data["name"] == "My Facebook Campaign"
        assert data["objective"] == "OUTCOME_SALES"
        assert data["daily_budget"] == 50.0
        assert data["created"] is True

    @pytest.mark.asyncio
    async def test_create_campaign_missing_name(self, client):
        """POST /api/v1/ads/facebook/campaigns with missing name should return 422."""
        response = await client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "objective": "OUTCOME_SALES",
                "daily_budget": 50.0,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_campaign_empty_name(self, client):
        """POST /api/v1/ads/facebook/campaigns with empty name should return 422."""
        response = await client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "name": "",
                "objective": "OUTCOME_SALES",
                "daily_budget": 50.0,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_campaign_invalid_objective(self, client):
        """POST /api/v1/ads/facebook/campaigns with invalid objective should return 422."""
        response = await client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "name": "Bad Objective Campaign",
                "objective": "INVALID_OBJECTIVE",
                "daily_budget": 50.0,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_campaign_negative_budget(self, client):
        """POST /api/v1/ads/facebook/campaigns with negative budget should return 422."""
        response = await client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "name": "Negative Budget Campaign",
                "objective": "OUTCOME_SALES",
                "daily_budget": -10.0,
            },
        )
        assert response.status_code == 422


# ─── List Facebook Campaigns Tests ──────────────────────────────────────────


class TestListFacebookCampaigns:
    """Test GET /api/v1/ads/facebook/campaigns."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_list_campaigns_success(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns should return 200 with list."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert "total_count" in data
        assert data["total_count"] == 2
        assert len(data["campaigns"]) == 2
        assert data["campaigns"][0]["external_campaign_id"] == "fb_camp_123"
        assert data["campaigns"][1]["external_campaign_id"] == "fb_camp_456"

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_list_campaigns_with_status_filter(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns?status=ACTIVE should pass filter."""
        mock_fb_client.list_campaigns.return_value = {
            "campaigns": [
                {
                    "external_campaign_id": "fb_camp_123",
                    "name": "Active Campaign",
                    "objective": "OUTCOME_SALES",
                    "status": "active",
                    "daily_budget": 50.0,
                },
            ],
            "total_count": 1,
        }
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns?status=ACTIVE")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_list_campaigns_empty(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns with no campaigns should return empty list."""
        mock_fb_client.list_campaigns.return_value = {
            "campaigns": [],
            "total_count": 0,
        }
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["campaigns"] == []


# ─── Get Facebook Campaign by ID Tests ──────────────────────────────────────


class TestGetFacebookCampaign:
    """Test GET /api/v1/ads/facebook/campaigns/{campaign_id}."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_campaign_success(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id} should return 200."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns/fb_camp_123")
        assert response.status_code == 200
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert data["name"] == "Test FB Campaign"
        assert data["objective"] == "OUTCOME_SALES"
        assert data["status"] == "active"
        assert data["daily_budget"] == 50.0

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_campaign_not_found(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/nonexistent should return 404."""
        mock_fb_client.get_campaign.side_effect = FacebookAdsError(
            "Campaign not found",
            status_code=404,
            fb_error={"code": 100, "message": "Unsupported get request."},
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns/nonexistent_id")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]["message"].lower()


# ─── Update Facebook Campaign Tests ─────────────────────────────────────────


class TestUpdateFacebookCampaign:
    """Test PATCH and PUT /api/v1/ads/facebook/campaigns/{campaign_id}."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_patch_campaign_success(self, mock_fb_cls, client, mock_fb_client):
        """PATCH /api/v1/ads/facebook/campaigns/{id} with valid data should return 200."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.patch(
            "/api/v1/ads/facebook/campaigns/fb_camp_123",
            json={"name": "Updated Campaign"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert data["updated"] is True

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_put_campaign_success(self, mock_fb_cls, client, mock_fb_client):
        """PUT /api/v1/ads/facebook/campaigns/{id} with valid data should return 200."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.put(
            "/api/v1/ads/facebook/campaigns/fb_camp_123",
            json={"name": "Updated Campaign", "daily_budget": 75.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert data["updated"] is True

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_update_campaign_status(self, mock_fb_cls, client, mock_fb_client):
        """PATCH /api/v1/ads/facebook/campaigns/{id} should update status."""
        mock_fb_client.update_campaign.return_value = {
            "external_campaign_id": "fb_camp_123",
            "updated": True,
            "changes": {"status": "ACTIVE"},
        }
        mock_fb_cls.return_value = mock_fb_client

        response = await client.patch(
            "/api/v1/ads/facebook/campaigns/fb_camp_123",
            json={"status": "ACTIVE"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] is True

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_update_campaign_not_found(self, mock_fb_cls, client, mock_fb_client):
        """PATCH /api/v1/ads/facebook/campaigns/{id} on nonexistent should return 404."""
        mock_fb_client.update_campaign.side_effect = FacebookAdsError(
            "Campaign not found",
            status_code=404,
            fb_error={"code": 100, "message": "Unsupported post request."},
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.patch(
            "/api/v1/ads/facebook/campaigns/nonexistent_id",
            json={"name": "Ghost"},
        )
        assert response.status_code == 404


# ─── Pause Facebook Campaign Tests ──────────────────────────────────────────


class TestPauseFacebookCampaign:
    """Test POST /api/v1/ads/facebook/campaigns/{campaign_id}/pause."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_pause_campaign_success(self, mock_fb_cls, client, mock_fb_client):
        """POST /api/v1/ads/facebook/campaigns/{id}/pause should return 200."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.post("/api/v1/ads/facebook/campaigns/fb_camp_123/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert data["status"] == "paused"
        assert data["updated"] is True

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_pause_campaign_not_found(self, mock_fb_cls, client, mock_fb_client):
        """POST /api/v1/ads/facebook/campaigns/{id}/pause on nonexistent should return 404."""
        mock_fb_client.pause_campaign.side_effect = FacebookAdsError(
            "Campaign not found",
            status_code=404,
            fb_error={"code": 100},
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.post("/api/v1/ads/facebook/campaigns/nonexistent_id/pause")
        assert response.status_code == 404


# ─── Campaign Insights / Metrics Tests ──────────────────────────────────────


class TestFacebookCampaignInsights:
    """Test GET /api/v1/ads/facebook/campaigns/{campaign_id}/insights."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_insights_success(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/insights should return 200."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/insights",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert data["start_date"] == "2025-01-01"
        assert data["end_date"] == "2025-01-31"
        assert "metrics" in data
        assert data["metrics"]["impressions"] == 10000.0
        assert data["metrics"]["clicks"] == 500.0
        assert data["metrics"]["spend"] == 250.0
        assert data["report_status"] == "completed"

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_insights_invalid_date_format(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/insights with bad date should return 400."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/insights",
            params={"start_date": "not-a-date", "end_date": "2025-01-31"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid" in data["detail"]

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_insights_missing_dates(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/insights without dates should return 422."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns/fb_camp_123/insights")
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_insights_campaign_not_found(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/insights on nonexistent should return 404."""
        mock_fb_client.get_campaign_insights.side_effect = FacebookAdsError(
            "Campaign not found",
            status_code=404,
            fb_error={"code": 100},
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get(
            "/api/v1/ads/facebook/campaigns/nonexistent_id/insights",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )
        assert response.status_code == 404


class TestFacebookCampaignMetrics:
    """Test GET /api/v1/ads/facebook/campaigns/{campaign_id}/metrics."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_metrics_success(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/metrics should return 200."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/metrics",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["external_campaign_id"] == "fb_camp_123"
        assert "metrics" in data
        assert data["report_status"] == "completed"

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_metrics_invalid_start_date(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/metrics with bad start_date should return 400."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/metrics",
            params={"start_date": "2025/01/01", "end_date": "2025-01-31"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_metrics_invalid_end_date(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/metrics with bad end_date should return 400."""
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/metrics",
            params={"start_date": "2025-01-01", "end_date": "Jan 31 2025"},
        )
        assert response.status_code == 400


# ─── Create Facebook Audience Tests ──────────────────────────────────────────


class TestCreateFacebookAudience:
    """Test POST /api/v1/ads/facebook/audiences."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.router._facebook_client")
    async def test_create_audience_success(self, mock_client, client):
        """POST /api/v1/ads/facebook/audiences with valid data should return 201."""
        mock_client.create_custom_audience = AsyncMock(return_value={
            "audience_id": "aud_789",
            "name": "Book Readers",
            "source_type": "CUSTOM",
            "created": True,
        })

        response = await client.post(
            "/api/v1/ads/facebook/audiences",
            json={
                "name": "Book Readers",
                "description": "People who love reading books",
                "source_type": "CUSTOM",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["audience_id"] == "aud_789"
        assert data["name"] == "Book Readers"
        assert data["created"] is True

    @pytest.mark.asyncio
    async def test_create_audience_missing_name(self, client):
        """POST /api/v1/ads/facebook/audiences without name should return 422."""
        response = await client.post(
            "/api/v1/ads/facebook/audiences",
            params={
                "description": "Missing name",
                "source_type": "CUSTOM",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.modules.advertising.router._facebook_client", new=None)
    async def test_create_audience_client_unavailable(self, client):
        """POST /api/v1/ads/facebook/audiences when client is None should return 503."""
        response = await client.post(
            "/api/v1/ads/facebook/audiences",
            json={
                "name": "Test Audience",
                "source_type": "CUSTOM",
            },
        )
        assert response.status_code == 503
        data = response.json()
        assert "not available" in data["detail"].lower()


# ─── Auth Required Tests ────────────────────────────────────────────────────


class TestFacebookAdsAuthRequired:
    """All Facebook Ads endpoints should return 401/403 without auth token."""

    @pytest.mark.asyncio
    async def test_create_campaign_requires_auth(self, unauthed_client):
        """POST /api/v1/ads/facebook/campaigns without token should return 401/403."""
        response = await unauthed_client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "name": "Unauthorized Campaign",
                "objective": "OUTCOME_SALES",
                "daily_budget": 50.0,
            },
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_campaigns_requires_auth(self, unauthed_client):
        """GET /api/v1/ads/facebook/campaigns without token should return 401/403."""
        response = await unauthed_client.get("/api/v1/ads/facebook/campaigns")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_campaign_requires_auth(self, unauthed_client):
        """GET /api/v1/ads/facebook/campaigns/{id} without token should return 401/403."""
        response = await unauthed_client.get("/api/v1/ads/facebook/campaigns/fb_camp_123")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_patch_campaign_requires_auth(self, unauthed_client):
        """PATCH /api/v1/ads/facebook/campaigns/{id} without token should return 401/403."""
        response = await unauthed_client.patch(
            "/api/v1/ads/facebook/campaigns/fb_camp_123",
            json={"name": "No Auth"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_put_campaign_requires_auth(self, unauthed_client):
        """PUT /api/v1/ads/facebook/campaigns/{id} without token should return 401/403."""
        response = await unauthed_client.put(
            "/api/v1/ads/facebook/campaigns/fb_camp_123",
            json={"name": "No Auth"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_pause_campaign_requires_auth(self, unauthed_client):
        """POST /api/v1/ads/facebook/campaigns/{id}/pause without token should return 401/403."""
        response = await unauthed_client.post(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/pause"
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_insights_requires_auth(self, unauthed_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/insights without token should return 401/403."""
        response = await unauthed_client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/insights",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_metrics_requires_auth(self, unauthed_client):
        """GET /api/v1/ads/facebook/campaigns/{id}/metrics without token should return 401/403."""
        response = await unauthed_client.get(
            "/api/v1/ads/facebook/campaigns/fb_camp_123/metrics",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_audience_requires_auth(self, unauthed_client):
        """POST /api/v1/ads/facebook/audiences without token should return 401/403."""
        response = await unauthed_client.post(
            "/api/v1/ads/facebook/audiences",
            params={"name": "No Auth Audience"},
        )
        assert response.status_code in (401, 403)


# ─── Facebook Ads Error Handling Tests ──────────────────────────────────────


class TestFacebookAdsErrorHandling:
    """Test that FacebookAdsError from the client is properly mapped to HTTP errors."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_create_campaign_fb_api_error(self, mock_fb_cls, client, mock_fb_client):
        """POST /api/v1/ads/facebook/campaigns should return 502 on Facebook API error."""
        mock_fb_client.create_campaign.side_effect = FacebookAdsError(
            "Facebook API error (400): Invalid parameter",
            status_code=400,
            fb_error={"code": 100, "message": "Invalid parameter"},
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.post(
            "/api/v1/ads/facebook/campaigns",
            json={
                "name": "Error Campaign",
                "objective": "OUTCOME_SALES",
                "daily_budget": 50.0,
            },
        )
        # Router maps FacebookAdsError status_code to the HTTP response
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_list_campaigns_fb_api_error(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns should return 502 on generic FB error."""
        mock_fb_client.list_campaigns.side_effect = FacebookAdsError(
            "Network error calling Facebook API",
            status_code=None,
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns")
        assert response.status_code == 502

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.FacebookAdsClient")
    async def test_get_campaign_fb_error_code_100(self, mock_fb_cls, client, mock_fb_client):
        """GET /api/v1/ads/facebook/campaigns/{id} with fb_error code 100 should return 404."""
        mock_fb_client.get_campaign.side_effect = FacebookAdsError(
            "Unsupported get request",
            status_code=400,
            fb_error={"code": 100, "message": "Unsupported get request."},
        )
        mock_fb_cls.return_value = mock_fb_client

        response = await client.get("/api/v1/ads/facebook/campaigns/bad_id")
        assert response.status_code == 404
