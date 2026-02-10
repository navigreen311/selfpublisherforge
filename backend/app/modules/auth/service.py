"""Authentication service — business logic for registration, login, tokens,
password reset, email verification, MFA, and session management."""

import re
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.modules.auth.utils import (
    generate_token,
    generate_token_hash,
    token_expiry,
    generate_totp_secret,
    verify_totp,
    build_totp_uri,
    generate_backup_codes,
)
from app.modules.auth.schemas import (
    TokenResponse,
    MFASetupResponse,
    MFARequiredResponse,
    UserResponse,
)

# Import canonical ORM models from the shared models package
from app.models.organization import Organization
from app.models.user import User, UserRole, UserSession

settings = get_settings()

# Max concurrent sessions per user
MAX_SESSIONS = 5


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: str,
    org_name: str,
) -> dict:
    """Create an organization + user, hash the password, generate an email-
    verification token, and return the user info + token pair.

    Raises AppException if the email is already taken.
    """
    # Check for existing user
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise AppException(
            status_code=409,
            code="EMAIL_EXISTS",
            message="A user with this email already exists.",
        )

    # Create organization
    org_id = uuid4()
    slug = _make_slug(org_name, str(org_id))
    org = Organization(id=org_id, name=org_name, slug=slug)
    db.add(org)

    # Email verification token
    raw_verify_token = generate_token()
    verify_hash = generate_token_hash(raw_verify_token)

    # Create user
    user_id = uuid4()
    user = User(
        id=user_id,
        org_id=org_id,
        email=email,
        name=name,
        password_hash=hash_password(password),
        role=UserRole.OWNER,
        email_verified=False,
        email_verify_token=verify_hash,
        email_verify_expires=token_expiry(hours=48),
    )
    db.add(user)
    await db.flush()

    # Build tokens
    token_data = {"sub": str(user_id), "org_id": str(org_id), "role": "owner"}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)

    # Create session
    await _create_session(db, user_id=user_id, refresh_token=refresh)

    return {
        "user": _user_dict(user),
        "tokens": TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        "email_verify_token": raw_verify_token,
    }


async def authenticate(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    mfa_code: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
    """Verify credentials, optionally verify MFA, and return tokens.

    Returns either a TokenResponse dict or an MFARequiredResponse when the
    user has MFA enabled but no code was supplied.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise AppException(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )

    # MFA check
    if user.mfa_enabled:
        if not mfa_code:
            # Issue a short-lived MFA token so the client can retry with code
            mfa_token = create_access_token(
                {"sub": str(user.id), "purpose": "mfa"},
                expires_delta=timedelta(minutes=5),
            )
            return {
                "mfa_required": MFARequiredResponse(mfa_required=True, mfa_token=mfa_token),
            }
        if not _verify_mfa(user, mfa_code):
            raise AppException(
                status_code=401,
                code="INVALID_MFA_CODE",
                message="Invalid MFA code.",
            )

    role_value = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    token_data = {"sub": str(user.id), "org_id": str(user.org_id), "role": role_value}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)

    await _create_session(
        db,
        user_id=user.id,
        refresh_token=refresh,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    return {
        "user": _user_dict(user),
        "tokens": TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    }


async def refresh_access_token(db: AsyncSession, *, refresh_token: str) -> TokenResponse:
    """Validate a refresh token, ensure the session exists, and issue a new
    access token (rotating the refresh token as well)."""
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise AppException(status_code=401, code="INVALID_TOKEN", message="Invalid refresh token.")

    if payload.get("type") != "refresh":
        raise AppException(status_code=401, code="INVALID_TOKEN", message="Token is not a refresh token.")

    token_hash = generate_token_hash(refresh_token)
    result = await db.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise AppException(status_code=401, code="SESSION_EXPIRED", message="Session expired or invalid.")

    user_id = payload["sub"]
    org_id = payload.get("org_id", "")
    role = payload.get("role", "viewer")

    token_data = {"sub": user_id, "org_id": org_id, "role": role}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    # Rotate refresh token in session
    session.refresh_token_hash = generate_token_hash(new_refresh)
    session.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await db.flush()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout(db: AsyncSession, *, refresh_token: str) -> None:
    """Delete the session associated with the given refresh token."""
    token_hash = generate_token_hash(refresh_token)
    await db.execute(
        delete(UserSession).where(UserSession.refresh_token_hash == token_hash)
    )
    await db.flush()


async def forgot_password(db: AsyncSession, *, email: str) -> str | None:
    """Generate a password-reset token and store its hash on the user.

    Returns the raw token so the caller (router) can send it via email.
    Returns *None* if the email is not found (to prevent enumeration the
    router should still return 200).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    raw_token = generate_token()
    user.password_reset_token = generate_token_hash(raw_token)
    user.password_reset_expires = token_expiry(hours=1)
    await db.flush()
    return raw_token


async def reset_password(db: AsyncSession, *, token: str, new_password: str) -> None:
    """Reset the user's password given a valid reset token.

    Also invalidates all existing sessions (security best practice).
    """
    token_hash = generate_token_hash(token)
    result = await db.execute(
        select(User).where(
            User.password_reset_token == token_hash,
            User.password_reset_expires > datetime.now(timezone.utc),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise AppException(status_code=400, code="INVALID_TOKEN", message="Invalid or expired reset token.")

    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.flush()

    # Invalidate all sessions on password change
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    await db.flush()


async def verify_email(db: AsyncSession, *, token: str) -> None:
    """Mark a user's email as verified."""
    token_hash = generate_token_hash(token)
    result = await db.execute(
        select(User).where(
            User.email_verify_token == token_hash,
            User.email_verify_expires > datetime.now(timezone.utc),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise AppException(status_code=400, code="INVALID_TOKEN", message="Invalid or expired verification token.")

    user.email_verified = True
    user.email_verify_token = None
    user.email_verify_expires = None
    await db.flush()


async def setup_mfa(db: AsyncSession, *, user_id: UUID) -> MFASetupResponse:
    """Generate a TOTP secret and backup codes for the user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found.")
    if user.mfa_enabled:
        raise AppException(status_code=400, code="MFA_ALREADY_ENABLED", message="MFA is already enabled.")

    secret = generate_totp_secret()
    backup_codes = generate_backup_codes()

    # Store hashes of backup codes so raw codes are never persisted
    user.mfa_secret = secret
    user.mfa_backup_codes = ",".join(generate_token_hash(c) for c in backup_codes)
    # MFA is *not* enabled until the user verifies with a code via /mfa/verify
    await db.flush()

    qr_url = build_totp_uri(secret, user.email)

    return MFASetupResponse(secret=secret, qr_code_url=qr_url, backup_codes=backup_codes)


async def verify_mfa_setup(db: AsyncSession, *, user_id: UUID, code: str) -> None:
    """Verify a TOTP code to finalize MFA setup (enable MFA on the account)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found.")
    if user.mfa_enabled:
        raise AppException(status_code=400, code="MFA_ALREADY_ENABLED", message="MFA is already enabled.")
    if not user.mfa_secret:
        raise AppException(status_code=400, code="MFA_NOT_SETUP", message="MFA has not been set up. Call /mfa/setup first.")

    if not verify_totp(user.mfa_secret, code):
        raise AppException(status_code=400, code="INVALID_MFA_CODE", message="Invalid TOTP code.")

    user.mfa_enabled = True
    await db.flush()


async def disable_mfa(db: AsyncSession, *, user_id: UUID, password: str) -> None:
    """Disable MFA after verifying the user's password."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found.")
    if not user.mfa_enabled:
        raise AppException(status_code=400, code="MFA_NOT_ENABLED", message="MFA is not enabled.")
    if not verify_password(password, user.password_hash):
        raise AppException(status_code=401, code="INVALID_PASSWORD", message="Incorrect password.")

    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = None
    await db.flush()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _create_session(
    db: AsyncSession,
    *,
    user_id: UUID,
    refresh_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> UserSession:
    """Create a new session row, enforcing the max-sessions cap."""
    # Count existing sessions
    count_result = await db.execute(
        select(func.count()).select_from(UserSession).where(UserSession.user_id == user_id)
    )
    count = count_result.scalar() or 0

    if count >= MAX_SESSIONS:
        # Evict the oldest session(s)
        oldest = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.asc())
            .limit(count - MAX_SESSIONS + 1)
        )
        for old_session in oldest.scalars().all():
            await db.delete(old_session)
        await db.flush()

    session = UserSession(
        id=uuid4(),
        user_id=user_id,
        refresh_token_hash=generate_token_hash(refresh_token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    await db.flush()
    return session


def _user_dict(user: User) -> dict:
    """Serialize a User ORM instance to a plain dict."""
    role_value = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "org_id": str(user.org_id),
        "role": role_value,
        "email_verified": user.email_verified,
        "mfa_enabled": user.mfa_enabled,
    }


def _make_slug(org_name: str, org_id: str) -> str:
    """Generate a URL-safe slug from an organization name, appending a short
    UUID suffix to avoid collisions."""
    base = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-")
    suffix = org_id[:8]
    return f"{base}-{suffix}" if base else suffix


def _verify_mfa(user: User, code: str) -> bool:
    """Check a TOTP code or a backup code for the user."""
    # Try TOTP first
    if verify_totp(user.mfa_secret, code):
        return True

    # Try backup codes
    if user.mfa_backup_codes:
        code_hash = generate_token_hash(code)
        hashes = user.mfa_backup_codes.split(",")
        if code_hash in hashes:
            # Consume the backup code
            hashes.remove(code_hash)
            user.mfa_backup_codes = ",".join(hashes) if hashes else None
            return True

    return False
