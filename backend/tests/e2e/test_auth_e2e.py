"""End-to-end tests for authentication flows.

Each test exercises a complete user journey through the HTTP API,
combining multiple auth endpoints in sequence.  Tests use the async
HTTPX client and in-memory SQLite fixtures from ``conftest.py``.
"""

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.modules.auth import service as auth_service

settings = get_settings()
AUTH_PREFIX = f"{settings.API_V1_PREFIX}/auth"
USERS_PREFIX = f"{settings.API_V1_PREFIX}/users"

VALID_PASSWORD = "StrongP@ss1"
NEW_PASSWORD = "NewStr0ng!Pass2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register(
    client: AsyncClient,
    email: str = "e2e@test.com",
    password: str = VALID_PASSWORD,
    name: str = "E2E Tester",
    org_name: str = "E2E Org",
) -> dict:
    """Register a user and return the full response JSON."""
    resp = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": email,
            "password": password,
            "name": name,
            "org_name": org_name,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(
    client: AsyncClient,
    email: str = "e2e@test.com",
    password: str = VALID_PASSWORD,
) -> tuple[dict, int]:
    """Login and return ``(response_json, status_code)``."""
    resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": email, "password": password},
    )
    return resp.json(), resp.status_code


def _auth_header(access_token: str) -> dict[str, str]:
    """Build an ``Authorization: Bearer <token>`` header dict."""
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# E2E: Full registration -> login -> access -> logout flow
# ---------------------------------------------------------------------------

class TestFullAuthLifecycle:
    """Register, login, access a protected resource, then logout."""

    @pytest.mark.asyncio
    async def test_register_login_access_logout(self, client: AsyncClient):
        email = "lifecycle@test.com"

        # 1. Register -------------------------------------------------------
        reg_data = await _register(client, email=email)
        assert reg_data["user"]["email"] == email
        assert "access_token" in reg_data["tokens"]
        assert "refresh_token" in reg_data["tokens"]

        # 2. Login with the registered credentials --------------------------
        login_data, login_status = await _login(client, email=email)
        assert login_status == 200
        access_token = login_data["tokens"]["access_token"]
        refresh_token = login_data["tokens"]["refresh_token"]

        # 3. Access protected endpoint with token --------------------------
        me_resp = await client.get(
            f"{USERS_PREFIX}/me",
            headers=_auth_header(access_token),
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == email

        # 4. Logout (invalidates the refresh token) -------------------------
        logout_resp = await client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_resp.status_code == 200

        # 5. Refresh with the invalidated refresh token should fail ---------
        refresh_resp = await client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_register_returns_usable_token(self, client: AsyncClient):
        """The token returned by registration should immediately grant
        access to protected resources (no separate login needed)."""
        email = "reg-token@test.com"
        reg_data = await _register(client, email=email)
        access_token = reg_data["tokens"]["access_token"]

        me_resp = await client.get(
            f"{USERS_PREFIX}/me",
            headers=_auth_header(access_token),
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email


# ---------------------------------------------------------------------------
# E2E: Token refresh flow
# ---------------------------------------------------------------------------

class TestTokenRefreshFlow:
    """Verify the full token rotation lifecycle."""

    @pytest.mark.asyncio
    async def test_refresh_provides_new_working_token(self, client: AsyncClient):
        email = "refresh-e2e@test.com"

        # 1. Register + login to get access & refresh tokens ----------------
        await _register(client, email=email)
        login_data, status = await _login(client, email=email)
        assert status == 200

        original_access = login_data["tokens"]["access_token"]
        original_refresh = login_data["tokens"]["refresh_token"]

        # 2. Refresh to get a new access token ------------------------------
        refresh_resp = await client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": original_refresh},
        )
        assert refresh_resp.status_code == 200
        refresh_data = refresh_resp.json()

        new_access = refresh_data["access_token"]
        new_refresh = refresh_data["refresh_token"]

        # Refresh token must be rotated (each has a unique jti)
        assert new_refresh != original_refresh
        # Access token is present and valid
        assert new_access

        # 3. Use the new access token to access a protected endpoint --------
        me_resp = await client.get(
            f"{USERS_PREFIX}/me",
            headers=_auth_header(new_access),
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email

    @pytest.mark.asyncio
    async def test_old_refresh_token_rejected_after_rotation(self, client: AsyncClient):
        """After refreshing, the old refresh token should be invalid
        (rotation means only the latest token works)."""
        email = "refresh-rot@test.com"

        await _register(client, email=email)
        login_data, _ = await _login(client, email=email)
        original_refresh = login_data["tokens"]["refresh_token"]

        # Rotate once
        resp = await client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": original_refresh},
        )
        assert resp.status_code == 200

        # Attempt reuse of the old refresh token
        resp2 = await client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": original_refresh},
        )
        assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# E2E: Password reset flow (forgot-password -> reset-password -> login)
# ---------------------------------------------------------------------------

class TestPasswordResetFlow:
    """Exercise the forgot-password / reset-password cycle.

    Since the ``POST /auth/forgot-password`` endpoint deliberately hides
    the reset token (anti-enumeration), we call the service layer to
    obtain the raw token.  Everything else goes through HTTP.
    """

    @pytest.mark.asyncio
    async def test_reset_password_then_login(self, client: AsyncClient, db_session):
        email = "pwreset@test.com"

        # 1. Register + login with original password -----------------------
        await _register(client, email=email)
        login_data, status = await _login(client, email=email)
        assert status == 200

        # 2. Obtain a reset token via the service layer --------------------
        raw_token = await auth_service.forgot_password(db_session, email=email)
        assert raw_token is not None

        # 3. Reset the password via the HTTP endpoint ----------------------
        reset_resp = await client.post(
            f"{AUTH_PREFIX}/reset-password",
            json={"token": raw_token, "new_password": NEW_PASSWORD},
        )
        assert reset_resp.status_code == 200

        # 4. Login with the OLD password should fail -----------------------
        _, old_status = await _login(client, email=email, password=VALID_PASSWORD)
        assert old_status == 401

        # 5. Login with the NEW password should succeed --------------------
        new_data, new_status = await _login(client, email=email, password=NEW_PASSWORD)
        assert new_status == 200
        assert "access_token" in new_data["tokens"]


# ---------------------------------------------------------------------------
# E2E: Invalid credentials rejected
# ---------------------------------------------------------------------------

class TestInvalidCredentialsRejected:
    """Verify that bad credentials are properly rejected."""

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        email = "badpw@test.com"
        await _register(client, email=email)

        _, status = await _login(client, email=email, password="WrongP@ss9")
        assert status == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        _, status = await _login(client, email="nobody@test.com")
        assert status == 401

    @pytest.mark.asyncio
    async def test_access_protected_route_without_token(self, client: AsyncClient):
        """Accessing /users/me with no Authorization header should be rejected."""
        resp = await client.get(f"{USERS_PREFIX}/me")
        assert resp.status_code == 403  # HTTPBearer returns 403 when header is missing

    @pytest.mark.asyncio
    async def test_access_protected_route_with_bogus_token(self, client: AsyncClient):
        """A completely invalid JWT should be rejected."""
        resp = await client.get(
            f"{USERS_PREFIX}/me",
            headers=_auth_header("not.a.valid.jwt.token"),
        )
        assert resp.status_code == 401
