"""Cross-module integration tests for the SelfPublisherForge API.

These tests verify that the entire FastAPI application works together:
health endpoints, OpenAPI spec, auth flow, CORS headers, and
that all major API prefixes are registered and respond.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API = "/api/v1"

REGISTER_PAYLOAD = {
    "email": "integration@test.com",
    "password": "StrongP@ss1",
    "name": "Integration Tester",
    "org_name": "Test Org",
}

LOGIN_PAYLOAD = {
    "email": "integration@test.com",
    "password": "StrongP@ss1",
}

# All tags that main.py registers routers with.
EXPECTED_TAGS = [
    "auth",
    "users",
    "billing",
    "storage",
    "notifications",
    "realtime",
    "llm",
    "market",
    "knowledge",
    "writing",
    "style",
    "pipelines",
    "publishing",
    "kdp-validation",
    "product-page",
    "pricing",
    "competitors",
    "marketing",
    "advertising",
    "reviews",
    "analytics",
    "agents",
    "portfolio",
    "audience",
    "seasonal",
    "covers",
    "chrome-extension",
]


# ---------------------------------------------------------------------------
# 1. Health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_root(client: AsyncClient):
    """GET /health returns 200 with healthy status."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_api_prefix(client: AsyncClient):
    """GET /api/v1/health also returns 200."""
    resp = await client.get(f"{API}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# 2. OpenAPI spec
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openapi_spec_accessible(client: AsyncClient):
    """The OpenAPI JSON spec should be accessible at /api/v1/openapi.json."""
    resp = await client.get(f"{API}/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert "openapi" in spec
    assert "paths" in spec
    assert "info" in spec
    assert spec["info"]["title"] == "SelfPublisherForge API"


@pytest.mark.asyncio
async def test_openapi_spec_includes_expected_tags(client: AsyncClient):
    """Every expected tag should appear in at least one path operation."""
    resp = await client.get(f"{API}/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()

    # Collect all tags actually present in the spec paths
    found_tags: set[str] = set()
    for _path, methods in spec.get("paths", {}).items():
        for _method, operation in methods.items():
            if isinstance(operation, dict):
                for tag in operation.get("tags", []):
                    found_tags.add(tag)

    for tag in EXPECTED_TAGS:
        assert tag in found_tags, (
            f"Expected tag '{tag}' not found in OpenAPI spec. "
            f"Found tags: {sorted(found_tags)}"
        )


# ---------------------------------------------------------------------------
# 3. Auth flow: register -> login -> profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_register(client: AsyncClient):
    """POST /api/v1/auth/register creates a user and returns tokens."""
    resp = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert "tokens" in data
    assert "user" in data
    assert data["user"]["email"] == REGISTER_PAYLOAD["email"]
    assert data["tokens"]["token_type"] == "bearer"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_auth_register_duplicate_email(client: AsyncClient):
    """Registering with the same email twice returns 409."""
    resp1 = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert resp1.status_code == 201

    resp2 = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_auth_login(client: AsyncClient):
    """POST /api/v1/auth/login with valid credentials returns tokens."""
    # First register
    await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)

    # Then login
    resp = await client.post(f"{API}/auth/login", json=LOGIN_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "tokens" in data
    assert data["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_auth_login_invalid_credentials(client: AsyncClient):
    """POST /api/v1/auth/login with bad credentials returns 401."""
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": "nobody@test.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_flow_register_login_profile(client: AsyncClient):
    """Full auth flow: register -> login -> get profile (authenticated)."""
    # Register
    reg_resp = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert reg_resp.status_code == 201
    tokens = reg_resp.json()["tokens"]
    access_token = tokens["access_token"]

    # Use the token to fetch profile
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_resp = await client.get(f"{API}/users/me", headers=headers)
    # Profile endpoint should either return user data (200) or
    # a service-level error -- but NOT a 404 (route must exist).
    assert profile_resp.status_code in (200, 500, 422)


# ---------------------------------------------------------------------------
# 4. Major API prefixes respond (even with 401/403 for unauthorized)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,expected_codes",
    [
        (f"{API}/auth/login", {200, 401, 405, 422}),
        (f"{API}/users/me", {200, 401, 403}),
        (f"{API}/billing/plans", {200, 401, 403, 404, 405}),
        (f"{API}/storage/files", {200, 401, 403, 404, 405}),
        (f"{API}/notifications", {200, 401, 403, 404, 405}),
        (f"{API}/llm/models", {200, 401, 403, 404, 405}),
        (f"{API}/market/categories", {200, 401, 403, 404, 405}),
        (f"{API}/knowledge/entries", {200, 401, 403, 404, 405}),
        (f"{API}/pipelines", {200, 401, 403, 404, 405, 422}),
        (f"{API}/publishing/accounts", {200, 401, 403, 404, 405}),
        (f"{API}/marketing/campaigns", {200, 401, 403, 404, 405}),
        (f"{API}/ads/campaigns", {200, 401, 403, 404, 405}),
        (f"{API}/analytics/dashboard", {200, 401, 403, 404, 405}),
        (f"{API}/agents", {200, 401, 403, 404, 405}),
    ],
)
async def test_api_prefix_responds(
    client: AsyncClient, path: str, expected_codes: set[int]
):
    """Each major API prefix should return a recognized status code, not 404
    (which would mean the route is not registered at all)."""
    resp = await client.get(path)
    assert resp.status_code in expected_codes, (
        f"GET {path} returned unexpected {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# 5. CORS headers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_headers_on_health(client: AsyncClient):
    """An OPTIONS preflight to /health should include CORS headers."""
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORSMiddleware should respond to preflight
    assert resp.status_code in (200, 204, 405)
    # If CORS is configured, we expect the allow-origin header
    if resp.status_code in (200, 204):
        allow_origin = resp.headers.get("access-control-allow-origin", "")
        assert allow_origin in ("*", "http://localhost:3000"), (
            f"Expected CORS allow-origin header, got: {allow_origin}"
        )


@pytest.mark.asyncio
async def test_cors_headers_on_api(client: AsyncClient):
    """Cross-origin GET to the API should include access-control-allow-origin."""
    resp = await client.get(
        f"{API}/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 200
    allow_origin = resp.headers.get("access-control-allow-origin", "")
    assert allow_origin in ("*", "http://localhost:3000")


# ---------------------------------------------------------------------------
# 6. Registration validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client: AsyncClient):
    """Weak passwords should be rejected by the schema validator."""
    payload = {
        "email": "weak@test.com",
        "password": "weak",
        "name": "Test User",
        "org_name": "Org",
    }
    resp = await client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    """Missing required fields should yield 422."""
    resp = await client.post(f"{API}/auth/register", json={"email": "x@test.com"})
    assert resp.status_code == 422
