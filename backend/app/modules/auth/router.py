"""FastAPI router for authentication endpoints (/api/v1/auth/...)."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.auth import schemas, service
from app.modules.notifications.email import send_transactional_email
from app.schemas.common import MessageResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=None,
    status_code=201,
    summary="Register new user",
    description="Create a new user and organization, returning JWT tokens.",
)
async def register(body: schemas.RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user and organization, returning JWT tokens."""
    result = await service.register_user(
        db,
        email=body.email,
        password=body.password,
        name=body.name,
        org_name=body.org_name,
    )
    settings = get_settings()
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={result['email_verify_token']}"
    send_transactional_email(
        to_email=body.email,
        template_name="verification",
        context={"name": body.name, "verification_url": verification_url},
    )
    return {
        "user": result["user"],
        "tokens": result["tokens"].model_dump(),
        "message": "Registration successful. Please verify your email.",
    }


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=None,
    summary="Login",
    description="Authenticate with email and password, with optional MFA code.",
)
async def login(body: schemas.LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password (+ optional MFA code)."""
    result = await service.authenticate(
        db,
        email=body.email,
        password=body.password,
        mfa_code=body.mfa_code,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    if "mfa_required" in result:
        return result["mfa_required"].model_dump()
    return {
        "user": result["user"],
        "tokens": result["tokens"].model_dump(),
    }


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=schemas.TokenResponse,
    summary="Refresh access token",
    description="Refresh an access token using a valid refresh token.",
)
async def refresh(body: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    return await service.refresh_access_token(db, refresh_token=body.refresh_token)


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Invalidate the session associated with the provided refresh token.",
)
async def logout(body: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Invalidate the session associated with the provided refresh token."""
    await service.logout(db, refresh_token=body.refresh_token)
    return MessageResponse(message="Logged out successfully.")


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------
@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Forgot password",
    description="Request a password-reset email. Always returns 200 to prevent email enumeration.",
)
async def forgot_password(body: schemas.ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password-reset email.  Always returns 200 to prevent email enumeration."""
    _token = await service.forgot_password(db, email=body.email)
    if _token:  # Only send if user exists (prevent enumeration)
        settings = get_settings()
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={_token}"
        send_transactional_email(
            to_email=body.email,
            template_name="password_reset",
            context={"name": "User", "reset_url": reset_url},
        )
    return MessageResponse(message="If that email exists, a reset link has been sent.")


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------
@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset a user's password using a valid reset token.",
)
async def reset_password(body: schemas.ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset a user's password with a valid reset token."""
    await service.reset_password(db, token=body.token, new_password=body.new_password)
    return MessageResponse(message="Password has been reset successfully.")


# ---------------------------------------------------------------------------
# POST /verify-email
# ---------------------------------------------------------------------------
@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email",
    description="Verify a user's email address with the token sent during registration.",
)
async def verify_email(body: schemas.VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify a user's email address with the token sent during registration."""
    await service.verify_email(db, token=body.token)
    return MessageResponse(message="Email verified successfully.")


# ---------------------------------------------------------------------------
# POST /mfa/setup
# ---------------------------------------------------------------------------
@router.post(
    "/mfa/setup",
    response_model=schemas.MFASetupResponse,
    summary="Setup MFA",
    description="Generate a TOTP secret and backup codes. MFA is activated after verification.",
)
async def mfa_setup(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a TOTP secret and backup codes.  MFA is not activated until
    the user verifies a code via POST /mfa/verify."""
    return await service.setup_mfa(db, user_id=current_user["user_id"])


# ---------------------------------------------------------------------------
# POST /mfa/verify
# ---------------------------------------------------------------------------
@router.post(
    "/mfa/verify",
    response_model=MessageResponse,
    summary="Verify MFA setup",
    description="Verify a TOTP code to finalize MFA activation.",
)
async def mfa_verify(
    body: schemas.MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a TOTP code to finalize MFA activation."""
    await service.verify_mfa_setup(db, user_id=current_user["user_id"], code=body.code)
    return MessageResponse(message="MFA enabled successfully.")


# ---------------------------------------------------------------------------
# POST /mfa/disable
# ---------------------------------------------------------------------------
@router.post(
    "/mfa/disable",
    response_model=MessageResponse,
    summary="Disable MFA",
    description="Disable MFA for the current user. Requires password confirmation.",
)
async def mfa_disable(
    body: schemas.MFADisableRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable MFA (requires current password for confirmation)."""
    await service.disable_mfa(db, user_id=current_user["user_id"], password=body.password)
    return MessageResponse(message="MFA disabled successfully.")


# ---------------------------------------------------------------------------
# OAuth — Google
# ---------------------------------------------------------------------------
@router.get(
    "/oauth/google",
    response_model=schemas.OAuthAuthorizationURL,
    summary="Google OAuth authorization URL",
    description="Returns the Google OAuth2 authorization URL to redirect the user to.",
)
async def oauth_google():
    """Return Google OAuth2 authorization URL."""
    return service.generate_google_auth_url()


@router.get(
    "/oauth/google/callback",
    response_model=None,
    summary="Google OAuth callback",
    description="Handle the Google OAuth2 callback, create or link user account, and return JWT tokens.",
)
async def oauth_google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str | None = Query(None, description="CSRF state parameter"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth2 callback."""
    result = await service.handle_google_callback(db, code=code, state=state)
    return {
        "user": result["user"],
        "tokens": result["tokens"].model_dump(),
    }


# ---------------------------------------------------------------------------
# OAuth — GitHub
# ---------------------------------------------------------------------------
@router.get(
    "/oauth/github",
    response_model=schemas.OAuthAuthorizationURL,
    summary="GitHub OAuth authorization URL",
    description="Returns the GitHub OAuth authorization URL to redirect the user to.",
)
async def oauth_github():
    """Return GitHub OAuth authorization URL."""
    return service.generate_github_auth_url()


@router.get(
    "/oauth/github/callback",
    response_model=None,
    summary="GitHub OAuth callback",
    description="Handle the GitHub OAuth callback, create or link user account, and return JWT tokens.",
)
async def oauth_github_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str | None = Query(None, description="CSRF state parameter"),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    result = await service.handle_github_callback(db, code=code, state=state)
    return {
        "user": result["user"],
        "tokens": result["tokens"].model_dump(),
    }
