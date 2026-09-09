"""Integration tests for auth API endpoints.

These tests hit the FastAPI ASGI app through HTTPX, using the overridden
test database from ``conftest.py``.
"""

import pytest
from httpx import AsyncClient

from app.config import get_settings

settings = get_settings()
PREFIX = f"{settings.API_V1_PREFIX}/auth"

VALID_PASSWORD = "StrongP@ss1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register(client: AsyncClient, email: str = "api@test.com") -> dict:
    """Register a user and return the full response JSON."""
    resp = await client.post(
        f"{PREFIX}/register",
        json={
            "email": email,
            "password": VALID_PASSWORD,
            "name": "API Tester",
            "org_name": "API Org",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client: AsyncClient, email: str = "api@test.com", password: str = VALID_PASSWORD) -> dict:
    resp = await client.post(
        f"{PREFIX}/login",
        json={"email": email, "password": password},
    )
    return resp.json(), resp.status_code


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegisterEndpoint:

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        data = await _register(client, email="reg1@test.com")
        assert data["user"]["email"] == "reg1@test.com"
        assert "access_token" in data["tokens"]

    @pytest.mark.asyncio
    async def test_register_duplicate(self, client: AsyncClient):
        await _register(client, email="dup@test.com")
        resp = await client.post(
            f"{PREFIX}/register",
            json={
                "email": "dup@test.com",
                "password": VALID_PASSWORD,
                "name": "Dup",
                "org_name": "DupOrg",
            },
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post(
            f"{PREFIX}/register",
            json={
                "email": "weak@test.com",
                "password": "short",
                "name": "Weak",
                "org_name": "WeakOrg",
            },
        )
        assert resp.status_code == 422  # validation error


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLoginEndpoint:

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        await _register(client, email="login1@test.com")
        data, status = await _login(client, email="login1@test.com")
        assert status == 200
        assert "access_token" in data["tokens"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await _register(client, email="login2@test.com")
        data, status = await _login(client, email="login2@test.com", password="WrongP@ss1")
        assert status == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        data, status = await _login(client, email="nope@test.com")
        assert status == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

class TestRefreshEndpoint:

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient):
        reg = await _register(client, email="ref@test.com")
        refresh_token = reg["tokens"]["refresh_token"]
        resp = await client.post(
            f"{PREFIX}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        # Token should be rotated
        assert data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_invalid(self, client: AsyncClient):
        resp = await client.post(
            f"{PREFIX}/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogoutEndpoint:

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        reg = await _register(client, email="lo@test.com")
        refresh_token = reg["tokens"]["refresh_token"]
        resp = await client.post(
            f"{PREFIX}/logout",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200

        # Refresh should now fail
        resp2 = await client.post(
            f"{PREFIX}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# Forgot / Reset Password
# ---------------------------------------------------------------------------

class TestPasswordResetEndpoints:

    @pytest.mark.asyncio
    async def test_forgot_password_always_200(self, client: AsyncClient):
        # Should return 200 even for non-existent email
        resp = await client.post(
            f"{PREFIX}/forgot-password",
            json={"email": "ghost@test.com"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            f"{PREFIX}/reset-password",
            json={"token": "bad-token", "new_password": "NewStr0ng!Pass"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

class TestEmailVerificationEndpoint:

    @pytest.mark.asyncio
    async def test_verify_email_bad_token(self, client: AsyncClient):
        resp = await client.post(
            f"{PREFIX}/verify-email",
            json={"token": "bad-token"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# MFA endpoints (require auth)
# ---------------------------------------------------------------------------

class TestMFAEndpoints:

    async def _auth_headers(self, client: AsyncClient, email: str = "mfa-api@test.com") -> dict:
        reg = await _register(client, email=email)
        token = reg["tokens"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_mfa_setup(self, client: AsyncClient):
        headers = await self._auth_headers(client, email="mfa1@test.com")
        resp = await client.post(f"{PREFIX}/mfa/setup", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "secret" in data
        assert "qr_code_url" in data
        assert len(data["backup_codes"]) == 8

    @pytest.mark.asyncio
    async def test_mfa_verify_bad_code(self, client: AsyncClient):
        headers = await self._auth_headers(client, email="mfa2@test.com")
        # Setup first
        await client.post(f"{PREFIX}/mfa/setup", headers=headers)
        resp = await client.post(
            f"{PREFIX}/mfa/verify",
            json={"code": "000000"},
            headers=headers,
        )
        # Should fail because 000000 is (almost certainly) wrong
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_mfa_disable_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            f"{PREFIX}/mfa/disable",
            json={"password": VALID_PASSWORD},
        )
        assert resp.status_code == 403  # no auth header

    @pytest.mark.asyncio
    async def test_mfa_disable_not_enabled(self, client: AsyncClient):
        headers = await self._auth_headers(client, email="mfa3@test.com")
        resp = await client.post(
            f"{PREFIX}/mfa/disable",
            json={"password": VALID_PASSWORD},
            headers=headers,
        )
        assert resp.status_code == 400
