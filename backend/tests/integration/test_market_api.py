"""Integration tests for the Market Intelligence API endpoints.

Uses FastAPI's TestClient (via httpx) to exercise every endpoint
defined in the market intelligence router.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app

BASE = "/api/v1/market"


# ---------------------------------------------------------------------------
# Auth override — all market endpoints now require get_current_user
# ---------------------------------------------------------------------------


def _mock_current_user():
    return {
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "org_id": uuid.UUID("00000000-0000-0000-0000-000000000099"),
        "role": "owner",
    }


@pytest_asyncio.fixture
async def client(db_session):
    """Authenticated HTTP test client with get_current_user overridden."""
    import logging

    logger = logging.getLogger(__name__)

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _mock_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ------------------------------------------------------------------
# GET /categories
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_browse_categories(client: AsyncClient):
    resp = await client.get(f"{BASE}/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    cat = data[0]
    assert "id" in cat
    assert "name" in cat
    assert "children" in cat


@pytest.mark.asyncio
async def test_browse_categories_with_root_id(client: AsyncClient):
    resp = await client.get(f"{BASE}/categories", params={"root_id": "154606011"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["id"] == "154606011"


# ------------------------------------------------------------------
# GET /categories/{id}/analysis
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_category_analysis(client: AsyncClient):
    resp = await client.get(f"{BASE}/categories/154606011/analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category_id"] == "154606011"
    assert "avg_bsr" in data
    assert "competition_score" in data
    assert "bsr_distribution" in data
    assert 0 <= data["competition_score"] <= 100


# ------------------------------------------------------------------
# POST /keywords/research
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_keyword_research(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/keywords/research",
        json={"keywords": ["self help", "productivity"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "keywords" in data
    assert len(data["keywords"]) == 2
    kw = data["keywords"][0]
    assert "search_volume" in kw
    assert "competition" in kw
    assert "cpc" in kw
    assert "trend" in kw
    assert kw["trend"] in ("up", "down", "stable")


@pytest.mark.asyncio
async def test_keyword_research_validation(client: AsyncClient):
    # Empty keywords list should fail validation
    resp = await client.post(
        f"{BASE}/keywords/research",
        json={"keywords": []},
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------
# GET /keywords/suggestions
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_keyword_suggestions(client: AsyncClient):
    resp = await client.get(
        f"{BASE}/keywords/suggestions",
        params={"genre": "romance", "limit": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    assert "keyword" in data[0]
    assert "search_volume" in data[0]


@pytest.mark.asyncio
async def test_keyword_suggestions_missing_genre(client: AsyncClient):
    resp = await client.get(f"{BASE}/keywords/suggestions")
    assert resp.status_code == 422


# ------------------------------------------------------------------
# POST /analyze-niche
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_niche(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/analyze-niche",
        json={"niche": "self-help for millennials"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["niche"] == "self-help for millennials"
    assert 0 <= data["demand_score"] <= 100
    assert 0 <= data["supply_score"] <= 100
    assert 0 <= data["opportunity_score"] <= 100
    assert isinstance(data["top_competitors"], list)
    assert isinstance(data["gap_analysis"], list)
    assert len(data["recommendation"]) > 0


@pytest.mark.asyncio
async def test_analyze_niche_with_category(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/analyze-niche",
        json={"niche": "productivity", "category_id": "154606011"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["niche"] == "productivity"


@pytest.mark.asyncio
async def test_analyze_niche_validation(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/analyze-niche",
        json={"niche": "x"},  # too short (min_length=2)
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------
# GET /competitors + POST /competitors/track
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_competitors_empty_initially(client: AsyncClient):
    resp = await client.get(f"{BASE}/competitors")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_track_competitor(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/competitors/track",
        json={"asin": "B000000001"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["asin"] == "B000000001"
    assert "id" in data
    assert "bsr_history" in data
    assert isinstance(data["bsr_history"], list)


@pytest.mark.asyncio
async def test_track_competitor_invalid_asin(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/competitors/track",
        json={"asin": "INVALIDASIN"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_competitor_not_found(client: AsyncClient):
    import uuid

    fake_id = str(uuid.uuid4())
    resp = await client.get(f"{BASE}/competitors/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_track_and_get_competitor(client: AsyncClient):
    # Track
    track_resp = await client.post(
        f"{BASE}/competitors/track",
        json={"asin": "B000000002"},
    )
    assert track_resp.status_code == 201
    comp_id = track_resp.json()["id"]

    # Get
    get_resp = await client.get(f"{BASE}/competitors/{comp_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == comp_id
    assert data["asin"] == "B000000002"


# ------------------------------------------------------------------
# GET /trends
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_market_trends_with_keyword(client: AsyncClient):
    resp = await client.get(
        f"{BASE}/trends",
        params={"keyword": "self help", "days": 30},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "trends" in data
    assert "period_start" in data
    assert "period_end" in data


@pytest.mark.asyncio
async def test_market_trends_with_category(client: AsyncClient):
    resp = await client.get(
        f"{BASE}/trends",
        params={"category_id": "154606011"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["trends"], list)


# ------------------------------------------------------------------
# GET /snapshots
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_market_snapshots_empty_when_no_data(client: AsyncClient):
    """Snapshots now come from DB; with no rows inserted the list is empty."""
    resp = await client.get(f"{BASE}/snapshots")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_market_snapshots_with_seeded_data(client: AsyncClient, db_session):
    """Insert snapshot rows via DB and verify the endpoint returns them."""
    from datetime import date

    from app.models.market import MarketCategory
    from app.models.market import MarketSnapshot as MarketSnapshotDB

    # Create a MarketCategory first (snapshot FK target)
    cat = MarketCategory(
        amazon_node_id="154606011",
        name="Self-Help",
    )
    db_session.add(cat)
    await db_session.flush()
    await db_session.refresh(cat)

    # Seed 5 snapshots
    for i in range(5):
        snap = MarketSnapshotDB(
            category_id=cat.id,
            snapshot_date=date(2025, 1, 1 + i),
            metrics={
                "avg_bsr": 50000.0 + i * 1000,
                "avg_price": 9.99,
                "book_count": 5000 + i * 100,
                "avg_reviews": 200.0,
                "competition_score": 55.0 + i,
            },
        )
        db_session.add(snap)
    await db_session.flush()

    resp = await client.get(f"{BASE}/snapshots", params={"limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 5
    snap = data[0]
    assert "category_id" in snap
    assert "avg_bsr" in snap
    assert "competition_score" in snap
    assert snap["category_name"] == "Self-Help"


@pytest.mark.asyncio
async def test_market_snapshots_with_limit(client: AsyncClient):
    """With no seeded data the endpoint returns an empty list."""
    resp = await client.get(f"{BASE}/snapshots", params={"limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0
