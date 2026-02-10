"""Integration tests for auth password-reset and MFA flows.

Tests the full HTTP request/response cycle through FastAPI's TestClient,
mocking only the database session and authentication dependencies.
Follows the pattern from test_user_api.py.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.auth.router import router
from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.core.error_handler import app_exception_handler
from app.modules.auth.utils import generate_token_hash, generate_totp_secret, verify_totp
from app.models.user import UserRole


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

_USER_ID = uuid4()
_ORG_ID = uuid4()

VALID_PASSWORD = "StrongP@ss1"
STRONG_NEW_PASSWORD = "N3wSecure!Pass"


def _current_user():
    return {"user_id": _USER_ID, "org_id": _ORG_ID, "role": "owner"}


def _make_user_mock(
    *,
    user_id: UUID | None = None,
    email: str = "user@example.com",
    name: str = "Test User",
    org_id: UUID | None = None,
    password_hash: str = "hashed_pw",
    role: UserRole = UserRole.OWNER,
    email_verified: bool = False,
    email_verify_token: str | None = None,
    email_verify_expires: datetime | None = None,
    password_reset_token: str | None = None,
    password_reset_expires: datetime | None = None,
    mfa_enabled: bool = False,
    mfa_secret: str | None = None,
    mfa_backup_codes: str | None = None,
) -> MagicMock:
    """Create a mock User ORM object with the given attributes."""
    user = MagicMock()
    user.id = user_id or _USER_ID
    user.email = email
    user.name = name
    user.org_id = org_id or _ORG_ID
    user.password_hash = password_hash
    user.role = role
    user.email_verified = email_verified
    user.email_verify_token = email_verify_token
    user.email_verify_expires = email_verify_expires
    user.password_reset_token = password_reset_token
    user.password_reset_expires = password_reset_expires
    user.mfa_enabled = mfa_enabled
    user.mfa_secret = mfa_secret
    user.mfa_backup_codes = mfa_backup_codes
    return user


def _make_scalar_result(obj):
    """Wrap an object (or None) in a mock that exposes scalar_one_or_none."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    result.scalar.return_value = 0  # for count queries
    return result


def _create_app(user_factory=None) -> tuple[FastAPI, AsyncMock]:
    """Build a test app with mocked DB and auth dependencies."""
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(router, prefix="/api/v1/auth")

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.delete = AsyncMock()

    async def override_get_db():
        yield mock_db

    user = (user_factory or _current_user)()

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    return app, mock_db


def _create_app_no_auth() -> tuple[FastAPI, AsyncMock]:
    """Build a test app with mocked DB but NO auth override (endpoints that
    don't require auth)."""
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(router, prefix="/api/v1/auth")

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.delete = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    return app, mock_db


# ===========================================================================
# Forgot Password Tests
# ===========================================================================

class TestForgotPassword:
    """Tests for POST /api/v1/auth/forgot-password."""

    def test_forgot_password_existing_email_returns_200(self):
        """POST /forgot-password with an existing email should return 200
        and set a reset token on the user."""
        app, mock_db = _create_app_no_auth()
        user_mock = _make_user_mock(email="exists@example.com")
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "exists@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "If that email exists, a reset link has been sent."
        # Verify password_reset_token was set on user
        assert user_mock.password_reset_token is not None
        assert user_mock.password_reset_expires is not None

    def test_forgot_password_nonexistent_email_returns_200(self):
        """POST /forgot-password should return 200 even for unknown emails
        to prevent email enumeration."""
        app, mock_db = _create_app_no_auth()
        mock_db.execute.return_value = _make_scalar_result(None)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "ghost@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "If that email exists, a reset link has been sent."

    def test_forgot_password_invalid_email_returns_422(self):
        """Invalid email format should return 422 validation error."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert resp.status_code == 422

    def test_forgot_password_missing_email_returns_422(self):
        """Missing email field should return 422 validation error."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={},
        )
        assert resp.status_code == 422


# ===========================================================================
# Reset Password Tests
# ===========================================================================

class TestResetPassword:
    """Tests for POST /api/v1/auth/reset-password."""

    def test_reset_password_with_valid_token(self):
        """POST /reset-password with a valid token should reset the password
        and return 200."""
        app, mock_db = _create_app_no_auth()

        raw_token = "valid-reset-token-abc123"
        token_hash = generate_token_hash(raw_token)
        user_mock = _make_user_mock(
            password_reset_token=token_hash,
            password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        with patch("app.modules.auth.service.hash_password", return_value="new_hashed"):
            resp = client.post(
                "/api/v1/auth/reset-password",
                json={"token": raw_token, "new_password": STRONG_NEW_PASSWORD},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Password has been reset successfully."

    def test_reset_password_with_invalid_token(self):
        """POST /reset-password with an invalid/expired token should return 400."""
        app, mock_db = _create_app_no_auth()
        # No user found for the given token hash
        mock_db.execute.return_value = _make_scalar_result(None)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "bad-token-xyz", "new_password": STRONG_NEW_PASSWORD},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_reset_password_weak_password_returns_422(self):
        """A weak new_password (no uppercase, no digit, no special char) should
        be rejected with 422 by the Pydantic validator."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "some-token", "new_password": "weak"},
        )
        assert resp.status_code == 422

    def test_reset_password_no_uppercase_returns_422(self):
        """Password without uppercase should fail validation."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "some-token", "new_password": "nouppercase1!"},
        )
        assert resp.status_code == 422

    def test_reset_password_no_digit_returns_422(self):
        """Password without a digit should fail validation."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "some-token", "new_password": "NoDigitHere!"},
        )
        assert resp.status_code == 422

    def test_reset_password_no_special_char_returns_422(self):
        """Password without a special character should fail validation."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "some-token", "new_password": "NoSpecial1A"},
        )
        assert resp.status_code == 422

    def test_reset_password_invalidates_sessions(self):
        """After a successful password reset, all user sessions should be
        invalidated (the service calls delete on UserSession)."""
        app, mock_db = _create_app_no_auth()

        raw_token = "session-clear-token"
        token_hash = generate_token_hash(raw_token)
        user_mock = _make_user_mock(
            password_reset_token=token_hash,
            password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        # First call returns the user, second call is the session deletion
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        with patch("app.modules.auth.service.hash_password", return_value="new_hash"):
            resp = client.post(
                "/api/v1/auth/reset-password",
                json={"token": raw_token, "new_password": STRONG_NEW_PASSWORD},
            )
        assert resp.status_code == 200
        # The service calls db.execute at least twice: once for the SELECT,
        # once for the DELETE of sessions, and db.flush at least twice.
        assert mock_db.execute.call_count >= 2
        assert mock_db.flush.call_count >= 2


# ===========================================================================
# MFA Setup Tests
# ===========================================================================

class TestMFASetup:
    """Tests for POST /api/v1/auth/mfa/setup."""

    def test_mfa_setup_returns_secret_and_qr_and_backup_codes(self):
        """POST /mfa/setup should return secret, qr_code_url, and backup_codes
        for a user who has not yet enabled MFA."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(mfa_enabled=False, mfa_secret=None)
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post("/api/v1/auth/mfa/setup")
        assert resp.status_code == 200
        data = resp.json()
        assert "secret" in data
        assert len(data["secret"]) > 0
        assert "qr_code_url" in data
        assert data["qr_code_url"].startswith("otpauth://totp/")
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 8

    def test_mfa_setup_already_enabled_returns_400(self):
        """POST /mfa/setup when MFA is already enabled should return 400."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(mfa_enabled=True, mfa_secret="EXISTING_SECRET")
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post("/api/v1/auth/mfa/setup")
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "MFA_ALREADY_ENABLED"

    def test_mfa_setup_user_not_found_returns_404(self):
        """POST /mfa/setup when user is not found in DB should return 404."""
        app, mock_db = _create_app()
        mock_db.execute.return_value = _make_scalar_result(None)

        client = TestClient(app)
        resp = client.post("/api/v1/auth/mfa/setup")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    def test_mfa_setup_stores_secret_on_user(self):
        """POST /mfa/setup should persist the TOTP secret and backup code
        hashes on the user model."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(mfa_enabled=False, mfa_secret=None)
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post("/api/v1/auth/mfa/setup")
        assert resp.status_code == 200
        # Verify the secret was stored on the mock user
        assert user_mock.mfa_secret is not None
        assert len(user_mock.mfa_secret) > 0
        # Verify backup code hashes were stored
        assert user_mock.mfa_backup_codes is not None
        assert "," in user_mock.mfa_backup_codes  # comma-separated hashes


# ===========================================================================
# MFA Verify Tests
# ===========================================================================

class TestMFAVerify:
    """Tests for POST /api/v1/auth/mfa/verify."""

    def test_mfa_verify_correct_code_activates_mfa(self):
        """POST /mfa/verify with the correct TOTP code should enable MFA."""
        app, mock_db = _create_app()
        secret = generate_totp_secret()
        user_mock = _make_user_mock(
            mfa_enabled=False,
            mfa_secret=secret,
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        # Generate the correct TOTP code for the secret
        with patch("app.modules.auth.service.verify_totp", return_value=True):
            resp = client.post(
                "/api/v1/auth/mfa/verify",
                json={"code": "123456"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "MFA enabled successfully."
        # The service should have set mfa_enabled = True
        assert user_mock.mfa_enabled is True

    def test_mfa_verify_wrong_code_returns_400(self):
        """POST /mfa/verify with an incorrect TOTP code should return 400."""
        app, mock_db = _create_app()
        secret = generate_totp_secret()
        user_mock = _make_user_mock(
            mfa_enabled=False,
            mfa_secret=secret,
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        with patch("app.modules.auth.service.verify_totp", return_value=False):
            resp = client.post(
                "/api/v1/auth/mfa/verify",
                json={"code": "000000"},
            )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "INVALID_MFA_CODE"

    def test_mfa_verify_already_enabled_returns_400(self):
        """POST /mfa/verify when MFA is already enabled should return 400."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(
            mfa_enabled=True,
            mfa_secret="SOME_SECRET",
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "MFA_ALREADY_ENABLED"

    def test_mfa_verify_no_setup_first_returns_400(self):
        """POST /mfa/verify without calling /mfa/setup first should return 400."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(
            mfa_enabled=False,
            mfa_secret=None,  # No secret means setup wasn't called
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "MFA_NOT_SETUP"

    def test_mfa_verify_code_too_short_returns_422(self):
        """MFA code shorter than 6 characters should be rejected at schema level."""
        app, mock_db = _create_app()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "123"},
        )
        assert resp.status_code == 422

    def test_mfa_verify_code_too_long_returns_422(self):
        """MFA code longer than 6 characters should be rejected at schema level."""
        app, mock_db = _create_app()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "1234567890"},
        )
        assert resp.status_code == 422


# ===========================================================================
# MFA Disable Tests
# ===========================================================================

class TestMFADisable:
    """Tests for POST /api/v1/auth/mfa/disable."""

    def test_mfa_disable_with_correct_password(self):
        """POST /mfa/disable with the correct password should disable MFA."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(
            mfa_enabled=True,
            mfa_secret="TOTP_SECRET",
            mfa_backup_codes="hash1,hash2",
            password_hash="hashed_pw",
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        with patch("app.modules.auth.service.verify_password", return_value=True):
            resp = client.post(
                "/api/v1/auth/mfa/disable",
                json={"password": VALID_PASSWORD},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "MFA disabled successfully."
        # Verify MFA was cleared on the user
        assert user_mock.mfa_enabled is False
        assert user_mock.mfa_secret is None
        assert user_mock.mfa_backup_codes is None

    def test_mfa_disable_wrong_password_returns_401(self):
        """POST /mfa/disable with an incorrect password should return 401."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(
            mfa_enabled=True,
            mfa_secret="TOTP_SECRET",
            password_hash="hashed_pw",
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        with patch("app.modules.auth.service.verify_password", return_value=False):
            resp = client.post(
                "/api/v1/auth/mfa/disable",
                json={"password": "WrongP@ss99"},
            )
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "INVALID_PASSWORD"

    def test_mfa_disable_not_enabled_returns_400(self):
        """POST /mfa/disable when MFA is not enabled should return 400."""
        app, mock_db = _create_app()
        user_mock = _make_user_mock(mfa_enabled=False)
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            json={"password": VALID_PASSWORD},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "MFA_NOT_ENABLED"

    def test_mfa_disable_user_not_found_returns_404(self):
        """POST /mfa/disable when the user is not found should return 404."""
        app, mock_db = _create_app()
        mock_db.execute.return_value = _make_scalar_result(None)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            json={"password": VALID_PASSWORD},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    def test_mfa_disable_missing_password_returns_422(self):
        """POST /mfa/disable without a password field should return 422."""
        app, mock_db = _create_app()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            json={},
        )
        assert resp.status_code == 422


# ===========================================================================
# Verify Email Tests
# ===========================================================================

class TestVerifyEmail:
    """Tests for POST /api/v1/auth/verify-email."""

    def test_verify_email_valid_token(self):
        """POST /verify-email with a valid token should mark email as verified."""
        app, mock_db = _create_app_no_auth()

        raw_token = "valid-email-verify-token"
        token_hash = generate_token_hash(raw_token)
        user_mock = _make_user_mock(
            email_verified=False,
            email_verify_token=token_hash,
            email_verify_expires=datetime.now(timezone.utc) + timedelta(hours=48),
        )
        mock_db.execute.return_value = _make_scalar_result(user_mock)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/verify-email",
            json={"token": raw_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Email verified successfully."
        assert user_mock.email_verified is True
        assert user_mock.email_verify_token is None
        assert user_mock.email_verify_expires is None

    def test_verify_email_invalid_token_returns_400(self):
        """POST /verify-email with an invalid token should return 400."""
        app, mock_db = _create_app_no_auth()
        mock_db.execute.return_value = _make_scalar_result(None)

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/verify-email",
            json={"token": "bad-token"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_verify_email_missing_token_returns_422(self):
        """POST /verify-email without a token field should return 422."""
        app, mock_db = _create_app_no_auth()

        client = TestClient(app)
        resp = client.post(
            "/api/v1/auth/verify-email",
            json={},
        )
        assert resp.status_code == 422
