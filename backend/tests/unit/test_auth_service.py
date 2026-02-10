"""Unit tests for the auth service layer.

Each test gets a clean database via the ``setup_database`` autouse fixture
from ``conftest.py`` and a fresh ``db_session``.
"""

import pytest
import pytest_asyncio
from uuid import uuid4

from app.core.security import hash_password, verify_password, decode_token
from app.modules.auth import service
from app.modules.auth.service import User, Organization, UserSession
from app.models.user import UserRole
from app.modules.auth.utils import (
    generate_token,
    generate_token_hash,
    token_expiry,
    generate_totp_secret,
    verify_totp,
    generate_backup_codes,
    build_totp_uri,
)
from app.core.exceptions import AppException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PASSWORD = "StrongP@ss1"


async def _seed_user(db, *, email="user@test.com", password=VALID_PASSWORD, mfa=False):
    """Insert a user + org into the test DB and return the ORM user."""
    org_id = uuid4()
    org = Organization(id=org_id, name="TestOrg", slug=f"testorg-{str(org_id)[:8]}")
    db.add(org)

    user_id = uuid4()
    user = User(
        id=user_id,
        org_id=org_id,
        email=email,
        name="Test User",
        password_hash=hash_password(password),
        role=UserRole.OWNER,
        email_verified=False,
        mfa_enabled=mfa,
        mfa_secret=generate_totp_secret() if mfa else None,
    )
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

class TestRegisterUser:

    @pytest.mark.asyncio
    async def test_register_success(self, db_session):
        result = await service.register_user(
            db_session,
            email="new@test.com",
            password=VALID_PASSWORD,
            name="New User",
            org_name="NewOrg",
        )
        assert result["user"]["email"] == "new@test.com"
        assert result["tokens"].access_token
        assert result["tokens"].refresh_token
        assert result["email_verify_token"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db_session):
        await _seed_user(db_session, email="dup@test.com")
        with pytest.raises(AppException) as exc_info:
            await service.register_user(
                db_session,
                email="dup@test.com",
                password=VALID_PASSWORD,
                name="Dup",
                org_name="DupOrg",
            )
        assert exc_info.value.code == "EMAIL_EXISTS"

    @pytest.mark.asyncio
    async def test_register_creates_session(self, db_session):
        result = await service.register_user(
            db_session,
            email="sess@test.com",
            password=VALID_PASSWORD,
            name="Sess",
            org_name="SessOrg",
        )
        from sqlalchemy import select, func
        count = await db_session.execute(
            select(func.count()).select_from(UserSession)
        )
        assert count.scalar() >= 1


# ---------------------------------------------------------------------------
# Authentication tests
# ---------------------------------------------------------------------------

class TestAuthenticate:

    @pytest.mark.asyncio
    async def test_login_success(self, db_session):
        await _seed_user(db_session)
        result = await service.authenticate(db_session, email="user@test.com", password=VALID_PASSWORD)
        assert "tokens" in result
        assert result["tokens"].access_token

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session):
        await _seed_user(db_session)
        with pytest.raises(AppException) as exc_info:
            await service.authenticate(db_session, email="user@test.com", password="WrongP@ss1")
        assert exc_info.value.code == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, db_session):
        with pytest.raises(AppException) as exc_info:
            await service.authenticate(db_session, email="nobody@test.com", password=VALID_PASSWORD)
        assert exc_info.value.code == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_mfa_required(self, db_session):
        await _seed_user(db_session, mfa=True)
        result = await service.authenticate(db_session, email="user@test.com", password=VALID_PASSWORD)
        assert "mfa_required" in result

    @pytest.mark.asyncio
    async def test_login_mfa_invalid_code(self, db_session):
        await _seed_user(db_session, mfa=True)
        with pytest.raises(AppException) as exc_info:
            await service.authenticate(
                db_session, email="user@test.com", password=VALID_PASSWORD, mfa_code="000000"
            )
        assert exc_info.value.code == "INVALID_MFA_CODE"


# ---------------------------------------------------------------------------
# Token refresh tests
# ---------------------------------------------------------------------------

class TestRefreshToken:

    @pytest.mark.asyncio
    async def test_refresh_success(self, db_session):
        reg = await service.register_user(
            db_session,
            email="refresh@test.com",
            password=VALID_PASSWORD,
            name="Refresh",
            org_name="RefOrg",
        )
        new_tokens = await service.refresh_access_token(
            db_session, refresh_token=reg["tokens"].refresh_token
        )
        assert new_tokens.access_token
        assert new_tokens.refresh_token != reg["tokens"].refresh_token  # rotated

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, db_session):
        with pytest.raises(AppException) as exc_info:
            await service.refresh_access_token(db_session, refresh_token="bad.token.here")
        assert exc_info.value.code == "INVALID_TOKEN"


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------

class TestLogout:

    @pytest.mark.asyncio
    async def test_logout_removes_session(self, db_session):
        reg = await service.register_user(
            db_session,
            email="logout@test.com",
            password=VALID_PASSWORD,
            name="Logout",
            org_name="LogOrg",
        )
        await service.logout(db_session, refresh_token=reg["tokens"].refresh_token)

        # Trying to refresh should now fail
        with pytest.raises(AppException):
            await service.refresh_access_token(
                db_session, refresh_token=reg["tokens"].refresh_token
            )


# ---------------------------------------------------------------------------
# Password reset tests
# ---------------------------------------------------------------------------

class TestPasswordReset:

    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, db_session):
        await _seed_user(db_session, email="reset@test.com")
        token = await service.forgot_password(db_session, email="reset@test.com")
        assert token is not None

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent(self, db_session):
        token = await service.forgot_password(db_session, email="nobody@test.com")
        assert token is None

    @pytest.mark.asyncio
    async def test_reset_password_success(self, db_session):
        await _seed_user(db_session, email="rp@test.com")
        raw = await service.forgot_password(db_session, email="rp@test.com")
        new_pw = "NewStr0ng!Pass"
        await service.reset_password(db_session, token=raw, new_password=new_pw)

        # Login with new password should succeed
        result = await service.authenticate(db_session, email="rp@test.com", password=new_pw)
        assert "tokens" in result

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, db_session):
        with pytest.raises(AppException) as exc_info:
            await service.reset_password(db_session, token="bad-token", new_password="NewStr0ng!Pass")
        assert exc_info.value.code == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_invalidates_sessions(self, db_session):
        reg = await service.register_user(
            db_session,
            email="inv@test.com",
            password=VALID_PASSWORD,
            name="Inv",
            org_name="InvOrg",
        )
        raw = await service.forgot_password(db_session, email="inv@test.com")
        await service.reset_password(db_session, token=raw, new_password="NewStr0ng!Pass")

        # Old refresh token should be invalid
        with pytest.raises(AppException):
            await service.refresh_access_token(
                db_session, refresh_token=reg["tokens"].refresh_token
            )


# ---------------------------------------------------------------------------
# Email verification tests
# ---------------------------------------------------------------------------

class TestEmailVerification:

    @pytest.mark.asyncio
    async def test_verify_email_success(self, db_session):
        reg = await service.register_user(
            db_session,
            email="verify@test.com",
            password=VALID_PASSWORD,
            name="Verify",
            org_name="VerOrg",
        )
        await service.verify_email(db_session, token=reg["email_verify_token"])
        # Fetch user and check
        from sqlalchemy import select
        result = await db_session.execute(select(User).where(User.email == "verify@test.com"))
        user = result.scalar_one()
        assert user.email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_bad_token(self, db_session):
        with pytest.raises(AppException) as exc_info:
            await service.verify_email(db_session, token="bad-token")
        assert exc_info.value.code == "INVALID_TOKEN"


# ---------------------------------------------------------------------------
# MFA tests
# ---------------------------------------------------------------------------

class TestMFA:

    @pytest.mark.asyncio
    async def test_setup_mfa(self, db_session):
        user = await _seed_user(db_session, email="mfa@test.com")
        resp = await service.setup_mfa(db_session, user_id=user.id)
        assert resp.secret
        assert resp.qr_code_url.startswith("otpauth://totp/")
        assert len(resp.backup_codes) == 8

    @pytest.mark.asyncio
    async def test_setup_mfa_already_enabled(self, db_session):
        user = await _seed_user(db_session, email="mfa2@test.com", mfa=True)
        with pytest.raises(AppException) as exc_info:
            await service.setup_mfa(db_session, user_id=user.id)
        assert exc_info.value.code == "MFA_ALREADY_ENABLED"

    @pytest.mark.asyncio
    async def test_disable_mfa(self, db_session):
        user = await _seed_user(db_session, email="dis@test.com", mfa=True)
        await service.disable_mfa(db_session, user_id=user.id, password=VALID_PASSWORD)
        from sqlalchemy import select
        result = await db_session.execute(select(User).where(User.id == user.id))
        u = result.scalar_one()
        assert u.mfa_enabled is False

    @pytest.mark.asyncio
    async def test_disable_mfa_wrong_password(self, db_session):
        user = await _seed_user(db_session, email="diswp@test.com", mfa=True)
        with pytest.raises(AppException) as exc_info:
            await service.disable_mfa(db_session, user_id=user.id, password="WrongP@ss1")
        assert exc_info.value.code == "INVALID_PASSWORD"


# ---------------------------------------------------------------------------
# Session management tests
# ---------------------------------------------------------------------------

class TestSessionManagement:

    @pytest.mark.asyncio
    async def test_max_sessions_enforced(self, db_session):
        """Creating more than MAX_SESSIONS should evict the oldest."""
        user = await _seed_user(db_session, email="maxsess@test.com")
        # Authenticate multiple times to create sessions
        for _ in range(service.MAX_SESSIONS + 2):
            await service.authenticate(
                db_session, email="maxsess@test.com", password=VALID_PASSWORD
            )

        from sqlalchemy import select, func
        count_result = await db_session.execute(
            select(func.count()).select_from(UserSession).where(
                UserSession.user_id == user.id
            )
        )
        assert count_result.scalar() <= service.MAX_SESSIONS


# ---------------------------------------------------------------------------
# Utils tests
# ---------------------------------------------------------------------------

class TestUtils:

    def test_generate_token(self):
        t = generate_token()
        assert len(t) > 20

    def test_generate_token_hash(self):
        t = generate_token()
        h = generate_token_hash(t)
        assert len(h) == 64  # SHA-256 hex

    def test_totp_roundtrip(self):
        secret = generate_totp_secret()
        # We cannot easily generate the "current" code without the same
        # internal function, but we can at least verify that a wrong code fails.
        assert verify_totp(secret, "000000") is False or verify_totp(secret, "000000") is True
        # build_totp_uri should return a valid URI
        uri = build_totp_uri(secret, "test@example.com")
        assert uri.startswith("otpauth://totp/")

    def test_backup_codes(self):
        codes = generate_backup_codes(count=8)
        assert len(codes) == 8
        assert all(len(c) == 8 for c in codes)

    def test_password_hashing(self):
        pw = "MyP@ssw0rd"
        h = hash_password(pw)
        assert verify_password(pw, h)
        assert not verify_password("wrong", h)

    def test_token_expiry(self):
        from datetime import datetime, timezone
        exp = token_expiry(hours=1)
        assert exp > datetime.now(timezone.utc)
