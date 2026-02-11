"""Authentication service — business logic for registration, login, tokens,
password reset, email verification, MFA, session management, and OAuth."""

import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

# Import canonical ORM models from the shared models package
from app.models.organization import Organization
from app.models.user import OAuthAccount, User, UserRole, UserSession
from app.modules.auth.oauth_providers import get_oauth_provider
from app.modules.auth.schemas import (
    MFARequiredResponse,
    MFASetupResponse,
    OAuthAuthorizationURL,
    TokenResponse,
)
from app.modules.auth.utils import (
    build_totp_uri,
    generate_backup_codes,
    generate_token,
    generate_token_hash,
    generate_totp_secret,
    token_expiry,
    verify_totp,
)

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
            UserSession.expires_at > datetime.now(UTC),
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
    session.expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
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
            User.password_reset_expires > datetime.now(UTC),
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
            User.email_verify_expires > datetime.now(UTC),
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
# OAuth state management (CSRF protection)
# ---------------------------------------------------------------------------

# In-memory state store for CSRF protection
# In production, use Redis with expiration
_oauth_states: dict[str, dict] = {}


def _store_oauth_state(state: str, provider: str) -> None:
    """Store OAuth state for CSRF validation.

    Note: In production, this should use Redis with a TTL of ~10 minutes.
    """
    _oauth_states[state] = {
        "provider": provider,
        "created_at": datetime.now(UTC),
    }


def _validate_oauth_state(state: str | None, provider: str) -> None:
    """Validate OAuth state parameter for CSRF protection.

    Raises AppException if state is invalid or expired.
    """
    if not state:
        raise AppException(
            status_code=400,
            code="OAUTH_INVALID_STATE",
            message="Missing state parameter. CSRF validation failed.",
        )

    stored = _oauth_states.get(state)
    if not stored:
        raise AppException(
            status_code=400,
            code="OAUTH_INVALID_STATE",
            message="Invalid state parameter. CSRF validation failed.",
        )

    # Check if state is for the correct provider
    if stored["provider"] != provider:
        raise AppException(
            status_code=400,
            code="OAUTH_INVALID_STATE",
            message="State parameter provider mismatch.",
        )

    # Check if state is expired (10 minutes)
    age = (datetime.now(UTC) - stored["created_at"]).total_seconds()
    if age > 600:  # 10 minutes
        _oauth_states.pop(state, None)
        raise AppException(
            status_code=400,
            code="OAUTH_STATE_EXPIRED",
            message="OAuth state expired. Please try again.",
        )

    # State is valid, consume it (one-time use)
    _oauth_states.pop(state, None)


# ---------------------------------------------------------------------------
# OAuth — Generic provider handling
# ---------------------------------------------------------------------------


def generate_oauth_auth_url(provider_name: str) -> OAuthAuthorizationURL:
    """Build an OAuth authorization URL for the specified provider.

    Args:
        provider_name: The provider name ('google' or 'github')

    Returns:
        OAuthAuthorizationURL with the authorization URL and provider name

    Raises:
        AppException: If provider is not configured or invalid
    """
    provider = get_oauth_provider(provider_name)
    state = provider.generate_state()
    url = provider.get_authorization_url(state)

    # Store state for CSRF validation
    _store_oauth_state(state, provider_name)

    return OAuthAuthorizationURL(authorization_url=url, provider=provider_name)


def generate_google_auth_url() -> OAuthAuthorizationURL:
    """Build the Google OAuth2 authorization URL.

    Raises AppException(501) when Google OAuth is not configured.
    """
    return generate_oauth_auth_url("google")


async def handle_oauth_callback(
    db: AsyncSession,
    *,
    provider_name: str,
    code: str,
    state: str | None = None,
) -> dict:
    """Generic OAuth callback handler for any provider.

    Args:
        db: Database session
        provider_name: The provider name ('google' or 'github')
        code: Authorization code from the provider
        state: CSRF state parameter from the provider

    Returns:
        dict with 'user' and 'tokens' keys

    Raises:
        AppException: If authentication fails or state is invalid
    """
    # 1. Validate CSRF state
    _validate_oauth_state(state, provider_name)

    # 2. Get provider instance
    provider = get_oauth_provider(provider_name)

    # 3. Exchange code for tokens
    tokens = await provider.exchange_code(code)

    # 4. Get user info
    user_info = await provider.get_user_info(tokens.access_token)

    # 5. Find or create user + link OAuth account
    return await _find_or_create_oauth_user(
        db,
        provider=provider_name,
        provider_user_id=user_info.provider_user_id,
        email=user_info.email,
        name=user_info.name,
        avatar_url=user_info.avatar_url,
        oauth_access_token=tokens.access_token,
        oauth_refresh_token=tokens.refresh_token,
    )


async def handle_google_callback(
    db: AsyncSession,
    *,
    code: str,
    state: str | None = None,
) -> dict:
    """Exchange the Google authorization code for tokens, fetch the user
    profile, find-or-create the local user, link the OAuth account, and
    return JWT tokens.
    """
    return await handle_oauth_callback(
        db,
        provider_name="google",
        code=code,
        state=state,
    )


# ---------------------------------------------------------------------------
# OAuth — GitHub
# ---------------------------------------------------------------------------

def generate_github_auth_url() -> OAuthAuthorizationURL:
    """Build the GitHub OAuth authorization URL.

    Raises AppException(501) when GitHub OAuth is not configured.
    """
    return generate_oauth_auth_url("github")


async def handle_github_callback(
    db: AsyncSession,
    *,
    code: str,
    state: str | None = None,
) -> dict:
    """Exchange the GitHub authorization code for tokens, fetch the user
    profile, find-or-create the local user, link the OAuth account, and
    return JWT tokens.
    """
    return await handle_oauth_callback(
        db,
        provider_name="github",
        code=code,
        state=state,
    )


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
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    await db.flush()
    return session


async def _find_or_create_oauth_user(
    db: AsyncSession,
    *,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str,
    avatar_url: str | None = None,
    oauth_access_token: str | None = None,
    oauth_refresh_token: str | None = None,
) -> dict:
    """Shared logic for all OAuth providers.

    1. Check if an OAuthAccount already exists for (provider, provider_user_id).
       If so, load the linked user and issue tokens.
    2. Otherwise, check if a User with the same email exists.
       If so, link a new OAuthAccount to that user.
    3. Otherwise, create a brand-new Organization + User + OAuthAccount.

    Returns the same dict shape as ``register_user`` / ``authenticate``.
    """
    # --- Check for existing OAuth link ---
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account is not None:
        # Update stored tokens
        oauth_account.access_token = oauth_access_token
        if oauth_refresh_token:
            oauth_account.refresh_token = oauth_refresh_token
        oauth_account.provider_email = email
        if avatar_url:
            oauth_account.avatar_url = avatar_url
        await db.flush()

        # Load user
        user_result = await db.execute(select(User).where(User.id == oauth_account.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise AppException(
                status_code=404,
                code="USER_NOT_FOUND",
                message="Linked user account not found.",
            )
        return await _issue_oauth_tokens(db, user)

    # --- Check for existing user with same email ---
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()  # type: ignore[assignment]

    if user is not None:
        # Link new OAuth account to existing user
        oauth_account = OAuthAccount(
            id=uuid4(),
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            access_token=oauth_access_token,
            refresh_token=oauth_refresh_token,
            avatar_url=avatar_url,
        )
        db.add(oauth_account)
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        await db.flush()
        return await _issue_oauth_tokens(db, user)

    # --- Create new organization + user + OAuth account ---
    org_id = uuid4()
    slug = _make_slug(name, str(org_id))
    org = Organization(id=org_id, name=f"{name}'s Workspace", slug=slug)
    db.add(org)

    user_id = uuid4()
    user = User(
        id=user_id,
        org_id=org_id,
        email=email,
        name=name,
        password_hash=hash_password(secrets.token_urlsafe(32)),  # random password for OAuth-only users
        role=UserRole.OWNER,
        email_verified=True,  # OAuth emails are already verified by the provider
        avatar_url=avatar_url,
    )
    db.add(user)

    oauth_account = OAuthAccount(
        id=uuid4(),
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=email,
        access_token=oauth_access_token,
        refresh_token=oauth_refresh_token,
        avatar_url=avatar_url,
    )
    db.add(oauth_account)
    await db.flush()

    return await _issue_oauth_tokens(db, user)


async def _issue_oauth_tokens(db: AsyncSession, user: User) -> dict:
    """Issue JWT access and refresh tokens for an OAuth-authenticated user."""
    role_value = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    token_data = {"sub": str(user.id), "org_id": str(user.org_id), "role": role_value}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)

    await _create_session(db, user_id=user.id, refresh_token=refresh)

    return {
        "user": _user_dict(user),
        "tokens": TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    }


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
    if verify_totp(user.mfa_secret, code):  # type: ignore[arg-type]
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
