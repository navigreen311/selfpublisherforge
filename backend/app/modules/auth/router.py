"""FastAPI router for authentication endpoints (/api/v1/auth/...)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import MessageResponse
from app.modules.auth import schemas, service

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
    # In production, send verification email with result["email_verify_token"]
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
    tokens = await service.refresh_access_token(db, refresh_token=body.refresh_token)
    return tokens


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
    # In production, send email with _token
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
