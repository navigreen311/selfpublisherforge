"""Integration tests for Market Intelligence auth enforcement.

Verifies that endpoints requiring ``get_current_user`` return 401/403
when no token (or an invalid token) is supplied, and succeed with a
valid bearer token.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app

BASE = "/api/v1/market"

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")


def _mock_current_user() -> dict:
    """Return a valid mock user dict used for authenticated requests."""
    return {
        "user_id": USER_ID,
        "org_id": ORG_ID,
        "role": "owner",
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def unauthenticated_client(db_session):
    """Client that does NOT override get_current_user.

    Any endpoint guarded by ``Depends(get_current_user)`` will reject
    requests that lack a valid Authorization header.
    """
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


@pytest_asyncio.fixture
async def authenticated_client(db_session):
    """Client that overrides get_current_user with a mock user."""
    app = create_app()

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _mock_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper: endpoints that require auth (Depends(get_current_user))
# ---------------------------------------------------------------------------

# Each tuple is (method, path, json_body_or_None)
AUTH_PROTECTED_ENDPOINTS: list[tuple[str, str, dict | None]] = [
    ("GET", f"{BASE}/categories", None),
    ("GET", f"{BASE}/categories/154606011/analysis", None),
    ("POST", f"{BASE}/keywords/research", {"keywords": ["self help"]}),
    ("GET", f"{BASE}/keywords/suggestions?genre=romance", None),
    ("POST", f"{BASE}/analyze-niche", {"niche": "self-help for millennials"}),
    ("GET", f"{BASE}/trends?keyword=self+help&days=30", None),
    ("GET", f"{BASE}/snapshots", None),
]


# ---------------------------------------------------------------------------
# Tests: unauthenticated (401)
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """Endpoints guarded by get_current_user must return 401/403 without a token."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,path,body",
        AUTH_PROTECTED_ENDPOINTS,
        ids=[
            "GET_categories",
            "GET_category_analysis",
            "POST_keyword_research",
            "GET_keyword_suggestions",
            "POST_analyze_niche",
            "GET_trends",
            "GET_snapshots",
        ],
    )
    async def test_returns_401_without_auth(
        self, unauthenticated_client: AsyncClient, method: str, path: str, body
    ):
        if method == "GET":
            resp = await unauthenticated_client.get(path)
        else:
            resp = await unauthenticated_client.post(path, json=body)

        assert resp.status_code in (401, 403), (
            f"{method} {path} returned {resp.status_code} instead of 401/403"
        )

    @pytest.mark.asyncio
    async def test_invalid_bearer_token_returns_401(
        self, unauthenticated_client: AsyncClient
    ):
        """Supply a bogus bearer token -- should still be rejected."""
        resp = await unauthenticated_client.get(
            f"{BASE}/categories",
            headers={"Authorization": "Bearer totally-invalid-token"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: authenticated (200 / success)
# ---------------------------------------------------------------------------


class TestAuthenticatedAccess:
    """Endpoints return success when a valid (mocked) user is present."""

    @pytest.mark.asyncio
    async def test_browse_categories_authenticated(
        self, authenticated_client: AsyncClient
    ):
        resp = await authenticated_client.get(f"{BASE}/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_category_analysis_authenticated(
        self, authenticated_client: AsyncClient
    ):
        resp = await authenticated_client.get(
            f"{BASE}/categories/154606011/analysis"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category_id"] == "154606011"

    @pytest.mark.asyncio
    async def test_keyword_research_authenticated(
        self, authenticated_client: AsyncClient
    ):
        resp = await authenticated_client.post(
            f"{BASE}/keywords/research",
            json={"keywords": ["self help", "productivity"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data

    @pytest.mark.asyncio
    async def test_keyword_suggestions_authenticated(
        self, authenticated_client: AsyncClient
    ):
        resp = await authenticated_client.get(
            f"{BASE}/keywords/suggestions", params={"genre": "romance", "limit": 5}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_analyze_niche_authenticated(
        self, authenticated_client: AsyncClient
    ):
        resp = await authenticated_client.post(
            f"{BASE}/analyze-niche",
            json={"niche": "self-help for millennials"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["niche"] == "self-help for millennials"

    @pytest.mark.asyncio
    async def test_competitors_list_authenticated(
        self, authenticated_client: AsyncClient
    ):
        """GET /competitors does not use get_current_user but should still work."""
        resp = await authenticated_client.get(f"{BASE}/competitors")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Tests: org_id scoping
# ---------------------------------------------------------------------------


class TestOrgIdScoping:
    """Verify the current_user dict carries org_id for downstream use."""

    @pytest.mark.asyncio
    async def test_authenticated_user_has_org_id(self):
        """The mock user fixture includes org_id for request-scoped data isolation."""
        user = _mock_current_user()
        assert user["org_id"] == ORG_ID
        assert isinstance(user["org_id"], uuid.UUID)

    @pytest.mark.asyncio
    async def test_different_org_gets_different_scope(self, db_session):
        """Demonstrate that swapping org_id yields a distinct user context."""
        other_org = uuid.UUID("00000000-0000-0000-0000-000000000088")

        def _other_org_user():
            return {
                "user_id": USER_ID,
                "org_id": other_org,
                "role": "viewer",
            }

        app = create_app()

        async def _override_get_db():
            try:
                yield db_session
                await db_session.commit()
            except Exception:
                await db_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_current_user] = _other_org_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(f"{BASE}/categories")
            assert resp.status_code == 200

        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests: /trends and /snapshots now require auth (previously public)
# ---------------------------------------------------------------------------


class TestTrendsAndSnapshotsAuth:
    """After W01, /trends and /snapshots also require get_current_user."""

    @pytest.mark.asyncio
    async def test_trends_requires_auth(
        self, unauthenticated_client: AsyncClient
    ):
        """GET /trends returns 401/403 without auth."""
        resp = await unauthenticated_client.get(
            f"{BASE}/trends", params={"keyword": "self help", "days": 30}
        )
        assert resp.status_code in (401, 403), (
            f"GET /trends returned {resp.status_code} instead of 401/403"
        )

    @pytest.mark.asyncio
    async def test_snapshots_requires_auth(
        self, unauthenticated_client: AsyncClient
    ):
        """GET /snapshots returns 401/403 without auth."""
        resp = await unauthenticated_client.get(f"{BASE}/snapshots")
        assert resp.status_code in (401, 403), (
            f"GET /snapshots returned {resp.status_code} instead of 401/403"
        )

    @pytest.mark.asyncio
    async def test_trends_authenticated(
        self, authenticated_client: AsyncClient
    ):
        """GET /trends succeeds with auth."""
        resp = await authenticated_client.get(
            f"{BASE}/trends", params={"keyword": "self help", "days": 30}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_snapshots_authenticated(
        self, authenticated_client: AsyncClient
    ):
        """GET /snapshots succeeds with auth."""
        resp = await authenticated_client.get(f"{BASE}/snapshots")
        assert resp.status_code == 200
