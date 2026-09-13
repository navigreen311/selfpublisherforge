"""Integration tests for Market Intelligence org_id scoping.

Verifies that all DB-backed market intelligence endpoints enforce
org_id-based tenant isolation:
  - Competitors (list, track) are scoped by org_id via the router
  - Unauthenticated requests are rejected with 401
  - Category, keyword, and niche endpoints require auth context
  - Different orgs see only their own data
  - Null org_id falls back to unscoped queries

Known router gaps documented in tests:
  - GET /competitors/{id} does not pass org_id (cross-tenant read by ID)
  - GET /snapshots does not pass org_id (all snapshots visible to any org)
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.models.market import CompetitorBook, MarketCategory
from app.models.market import MarketSnapshot as MarketSnapshotDB

BASE = "/api/v1/market"

ORG_A = uuid.UUID("00000000-0000-0000-0000-00000000000a")
ORG_B = uuid.UUID("00000000-0000-0000-0000-00000000000b")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Mock user factories
# ---------------------------------------------------------------------------


def _mock_user_org_a() -> dict:
    return {"user_id": USER_ID, "org_id": ORG_A, "role": "owner"}


def _mock_user_org_b() -> dict:
    return {"user_id": USER_ID, "org_id": ORG_B, "role": "owner"}


def _mock_user_no_org() -> dict:
    return {"user_id": USER_ID, "org_id": None, "role": "viewer"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_app_with_user(db_session: AsyncSession, user_fn):
    """Create an app with both get_db and get_current_user overridden."""
    app = create_app()

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = user_fn
    return app


@pytest_asyncio.fixture
async def client_org_a(db_session: AsyncSession) -> AsyncClient:
    """Authenticated client for org A."""
    app = _make_app_with_user(db_session, _mock_user_org_a)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_org_b(db_session: AsyncSession) -> AsyncClient:
    """Authenticated client for org B."""
    app = _make_app_with_user(db_session, _mock_user_org_b)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_no_org(db_session: AsyncSession) -> AsyncClient:
    """Authenticated client with no org_id (None)."""
    app = _make_app_with_user(db_session, _mock_user_no_org)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauthenticated_client(db_session: AsyncSession) -> AsyncClient:
    """Client without auth -- no get_current_user override."""
    app = create_app()

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


async def _seed_competitor(
    db_session: AsyncSession, asin: str, org_id: uuid.UUID | None, title: str = "Test Book"
) -> CompetitorBook:
    """Insert a CompetitorBook row and return it."""
    book = CompetitorBook(
        org_id=org_id,
        asin=asin,
        title=title,
        author="Test Author",
        bsr_current=5000,
        bsr_history=[{"date": "2025-01-01T00:00:00Z", "bsr": 5000, "price": 9.99}],
        price=9.99,
        reviews_count=100,
        rating=4.5,
        metadata_json={"marketplace": "US"},
    )
    db_session.add(book)
    await db_session.flush()
    await db_session.refresh(book)
    return book


async def _seed_snapshot(
    db_session: AsyncSession, category: MarketCategory, org_id: uuid.UUID | None, day: int = 1
) -> MarketSnapshotDB:
    """Insert a MarketSnapshot row and return it."""
    snap = MarketSnapshotDB(
        org_id=org_id,
        category_id=category.id,
        snapshot_date=date(2025, 1, day),
        metrics={
            "avg_bsr": 50000.0,
            "avg_price": 9.99,
            "book_count": 5000,
            "avg_reviews": 200.0,
            "competition_score": 55.0,
        },
    )
    db_session.add(snap)
    await db_session.flush()
    await db_session.refresh(snap)
    return snap


async def _seed_category(
    db_session: AsyncSession, org_id: uuid.UUID | None, amazon_node_id: str, name: str
) -> MarketCategory:
    """Insert a MarketCategory and return it."""
    cat = MarketCategory(
        org_id=org_id,
        amazon_node_id=amazon_node_id,
        name=name,
    )
    db_session.add(cat)
    await db_session.flush()
    await db_session.refresh(cat)
    return cat


# ===========================================================================
# Test class: Unauthenticated access (401)
# ===========================================================================


class TestUnauthenticatedRejection:
    """All market endpoints must reject requests without valid auth."""

    @pytest.mark.asyncio
    async def test_categories_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.get(f"{BASE}/categories")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_category_analysis_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.get(f"{BASE}/categories/154606011/analysis")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_keyword_research_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.post(f"{BASE}/keywords/research", json={"keywords": ["test"]})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_keyword_suggestions_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.get(f"{BASE}/keywords/suggestions", params={"genre": "romance"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_niche_analysis_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.post(f"{BASE}/analyze-niche", json={"niche": "self-help tips"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_competitors_list_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.get(f"{BASE}/competitors")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_competitor_track_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.post(f"{BASE}/competitors/track", json={"asin": "B000000001"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_snapshots_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.get(f"{BASE}/snapshots")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_trends_requires_auth(self, unauthenticated_client: AsyncClient):
        resp = await unauthenticated_client.get(f"{BASE}/trends", params={"keyword": "self help", "days": 30})
        assert resp.status_code in (401, 403)


# ===========================================================================
# Test class: Competitor list org_id scoping
# ===========================================================================


class TestCompetitorListOrgScoping:
    """GET /competitors passes org_id from current_user to the service,
    so the list is scoped to the caller's org."""

    @pytest.mark.asyncio
    async def test_list_competitors_scoped_to_org_a(self, db_session: AsyncSession, client_org_a: AsyncClient):
        """Org A sees only its own competitors, not org B's."""
        await _seed_competitor(db_session, "B000000001", ORG_A, title="Org A Book")
        await _seed_competitor(db_session, "B000000002", ORG_B, title="Org B Book")

        resp = await client_org_a.get(f"{BASE}/competitors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["asin"] == "B000000001"
        assert data[0]["title"] == "Org A Book"

    @pytest.mark.asyncio
    async def test_list_competitors_scoped_to_org_b(self, db_session: AsyncSession, client_org_b: AsyncClient):
        """Org B sees only its own competitors, not org A's."""
        await _seed_competitor(db_session, "B000000003", ORG_A, title="Org A Book 2")
        await _seed_competitor(db_session, "B000000004", ORG_B, title="Org B Book 2")

        resp = await client_org_b.get(f"{BASE}/competitors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["asin"] == "B000000004"

    @pytest.mark.asyncio
    async def test_list_competitors_empty_for_new_org(self, db_session: AsyncSession, client_org_b: AsyncClient):
        """An org with no tracked competitors should get an empty list."""
        await _seed_competitor(db_session, "B000000008", ORG_A)

        resp = await client_org_b.get(f"{BASE}/competitors")
        assert resp.status_code == 200
        assert resp.json() == []


# ===========================================================================
# Test class: Competitor tracking org_id scoping
# ===========================================================================


class TestCompetitorTrackOrgScoping:
    """POST /competitors/track passes org_id from current_user, so tracked
    books are stamped with the caller's org and only visible to that org."""

    @pytest.mark.asyncio
    async def test_track_competitor_assigns_org_id(self, db_session: AsyncSession, client_org_a: AsyncClient):
        """Tracking a competitor stamps it with the caller's org_id."""
        resp = await client_org_a.post(f"{BASE}/competitors/track", json={"asin": "B000000005"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["asin"] == "B000000005"

        # Verify the tracked book appears in org A's list
        list_resp = await client_org_a.get(f"{BASE}/competitors")
        assert list_resp.status_code == 200
        asins = [c["asin"] for c in list_resp.json()]
        assert "B000000005" in asins

    @pytest.mark.asyncio
    async def test_track_competitor_not_visible_to_other_org(
        self, db_session: AsyncSession, client_org_a: AsyncClient, client_org_b: AsyncClient
    ):
        """A competitor tracked by org A should not appear in org B's list."""
        track_resp = await client_org_a.post(f"{BASE}/competitors/track", json={"asin": "B000000006"})
        assert track_resp.status_code == 201

        list_resp = await client_org_b.get(f"{BASE}/competitors")
        assert list_resp.status_code == 200
        asins = [c["asin"] for c in list_resp.json()]
        assert "B000000006" not in asins

    @pytest.mark.asyncio
    async def test_track_duplicate_asin_same_org_returns_existing(
        self, db_session: AsyncSession, client_org_a: AsyncClient
    ):
        """Tracking the same ASIN twice within one org returns the existing record."""
        resp1 = await client_org_a.post(f"{BASE}/competitors/track", json={"asin": "B000000009"})
        assert resp1.status_code == 201
        id1 = resp1.json()["id"]

        resp2 = await client_org_a.post(f"{BASE}/competitors/track", json={"asin": "B000000009"})
        # Should return the existing record (201 or 200 depending on implementation)
        assert resp2.status_code in (200, 201)
        id2 = resp2.json()["id"]
        assert id1 == id2


# ===========================================================================
# Test class: Competitor get-by-ID (current gap: no org scoping)
# ===========================================================================


class TestCompetitorGetByIdScoping:
    """GET /competitors/{id} currently does NOT pass org_id to the service.
    These tests document the current behavior."""

    @pytest.mark.asyncio
    async def test_owner_can_get_own_competitor_by_id(self, db_session: AsyncSession, client_org_a: AsyncClient):
        """Org A can retrieve its own competitor by ID."""
        book = await _seed_competitor(db_session, "B000000007", ORG_A, title="My Book")
        comp_id = str(book.id)

        resp = await client_org_a.get(f"{BASE}/competitors/{comp_id}")
        assert resp.status_code == 200
        assert resp.json()["asin"] == "B000000007"

    @pytest.mark.asyncio
    async def test_cross_org_get_by_id_currently_not_scoped(
        self, db_session: AsyncSession, client_org_a: AsyncClient, client_org_b: AsyncClient
    ):
        """KNOWN GAP: GET /competitors/{id} does not filter by org_id.

        Org B can currently read org A's competitor by ID because the router
        does not pass org_id to svc.get_competitor(). This test documents
        the current (unscoped) behavior. When the router is updated to pass
        org_id, change the assertion to expect 404.
        """
        book = await _seed_competitor(db_session, "B000000013", ORG_A, title="Secret A Book")
        comp_id = str(book.id)

        resp = await client_org_b.get(f"{BASE}/competitors/{comp_id}")
        # Current behavior: 200 (not scoped)
        # Expected after fix: 404
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_nonexistent_competitor_returns_404(self, client_org_a: AsyncClient):
        """Getting a competitor with a random UUID should 404."""
        fake_id = str(uuid.uuid4())
        resp = await client_org_a.get(f"{BASE}/competitors/{fake_id}")
        assert resp.status_code == 404


# ===========================================================================
# Test class: Snapshot endpoint (current gap: no org scoping in router)
# ===========================================================================


class TestSnapshotOrgScoping:
    """GET /snapshots currently does NOT pass org_id to svc.get_snapshots().
    These tests document the actual behavior."""

    @pytest.mark.asyncio
    async def test_snapshots_currently_unscoped(self, db_session: AsyncSession, client_org_a: AsyncClient):
        """KNOWN GAP: The snapshots endpoint does not pass org_id.

        All snapshots are visible regardless of the caller's org.  When the
        router is updated to pass org_id=current_user['org_id'], update this
        test to assert only org A's snapshot is returned.
        """
        cat_a = await _seed_category(db_session, ORG_A, "999001", "Org A Category")
        cat_b = await _seed_category(db_session, ORG_B, "999002", "Org B Category")
        await _seed_snapshot(db_session, cat_a, ORG_A, day=1)
        await _seed_snapshot(db_session, cat_b, ORG_B, day=2)

        resp = await client_org_a.get(f"{BASE}/snapshots")
        assert resp.status_code == 200
        data = resp.json()
        # Currently unscoped: both org's snapshots are returned
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_snapshots_empty_when_no_data(self, client_org_a: AsyncClient):
        """With no seeded snapshots, the endpoint returns an empty list."""
        resp = await client_org_a.get(f"{BASE}/snapshots")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_snapshots_limit_parameter(self, db_session: AsyncSession, client_org_a: AsyncClient):
        """Limit parameter restricts the number of snapshots returned."""
        cat = await _seed_category(db_session, ORG_A, "999003", "Test Category")
        for i in range(1, 6):
            await _seed_snapshot(db_session, cat, ORG_A, day=i)

        resp = await client_org_a.get(f"{BASE}/snapshots", params={"limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3


# ===========================================================================
# Test class: Category listing with auth context
# ===========================================================================


class TestCategoryAuthContext:
    """Category endpoints require auth but return shared (client-side) data.
    The service accepts org_id for forward compatibility but currently
    the router does not pass it."""

    @pytest.mark.asyncio
    async def test_categories_accessible_with_auth(self, client_org_a: AsyncClient):
        """Authenticated users can browse categories."""
        resp = await client_org_a.get(f"{BASE}/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_category_analysis_with_auth(self, client_org_a: AsyncClient):
        """Category analysis is accessible with valid auth."""
        resp = await client_org_a.get(f"{BASE}/categories/154606011/analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["category_id"] == "154606011"
        assert "competition_score" in data


# ===========================================================================
# Test class: Keyword research with org context
# ===========================================================================


class TestKeywordResearchOrgScope:
    """Keyword endpoints require auth and accept the org context.
    Currently client-only, so org_id does not change results."""

    @pytest.mark.asyncio
    async def test_keyword_research_with_org_a(self, client_org_a: AsyncClient):
        """Keyword research succeeds with org A auth context."""
        resp = await client_org_a.post(
            f"{BASE}/keywords/research",
            json={"keywords": ["self help", "productivity"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data
        assert len(data["keywords"]) == 2

    @pytest.mark.asyncio
    async def test_keyword_suggestions_with_org_b(self, client_org_b: AsyncClient):
        """Keyword suggestions succeed with org B auth context."""
        resp = await client_org_b.get(f"{BASE}/keywords/suggestions", params={"genre": "romance", "limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 3


# ===========================================================================
# Test class: Niche analysis with org context
# ===========================================================================


class TestNicheAnalysisOrgScope:
    """Niche analysis endpoints require auth and carry org context.
    Currently client-only, so org_id does not change results."""

    @pytest.mark.asyncio
    async def test_niche_analysis_with_org_a(self, client_org_a: AsyncClient):
        """Niche analysis succeeds with org A auth context."""
        resp = await client_org_a.post(
            f"{BASE}/analyze-niche",
            json={"niche": "self-help for millennials"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["niche"] == "self-help for millennials"
        assert 0 <= data["demand_score"] <= 100
        assert 0 <= data["opportunity_score"] <= 100

    @pytest.mark.asyncio
    async def test_niche_analysis_with_org_b(self, client_org_b: AsyncClient):
        """Niche analysis succeeds with org B auth context."""
        resp = await client_org_b.post(
            f"{BASE}/analyze-niche",
            json={"niche": "romance novels"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["niche"] == "romance novels"


# ===========================================================================
# Test class: Null org_id handling
# ===========================================================================


class TestNullOrgIdHandling:
    """Users without an org_id should still be able to use client-only endpoints.
    DB-scoped queries skip the org_id filter when it is None."""

    @pytest.mark.asyncio
    async def test_categories_work_without_org_id(self, client_no_org: AsyncClient):
        """Categories are client-only, so no org_id is fine."""
        resp = await client_no_org.get(f"{BASE}/categories")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_competitors_list_with_null_org_returns_unscoped(
        self, db_session: AsyncSession, client_no_org: AsyncClient
    ):
        """When org_id is None, list_competitors returns all non-deleted competitors
        because the service skips the org_id filter clause."""
        await _seed_competitor(db_session, "B000000010", ORG_A, title="Book A")
        await _seed_competitor(db_session, "B000000011", ORG_B, title="Book B")
        await _seed_competitor(db_session, "B000000012", None, title="Book No Org")

        resp = await client_no_org.get(f"{BASE}/competitors")
        assert resp.status_code == 200
        data = resp.json()
        # With org_id=None the service does not add an org filter
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_niche_analysis_works_without_org_id(self, client_no_org: AsyncClient):
        """Niche analysis is client-only, so null org_id is handled fine."""
        resp = await client_no_org.post(
            f"{BASE}/analyze-niche",
            json={"niche": "cooking for beginners"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["niche"] == "cooking for beginners"

    @pytest.mark.asyncio
    async def test_keyword_research_works_without_org_id(self, client_no_org: AsyncClient):
        """Keyword research is client-only, so null org_id is handled fine."""
        resp = await client_no_org.post(
            f"{BASE}/keywords/research",
            json={"keywords": ["gardening"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["keywords"]) == 1
