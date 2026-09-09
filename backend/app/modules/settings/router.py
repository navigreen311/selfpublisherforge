"""Settings API router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.database import get_db
from app.modules.settings import service
from app.modules.settings.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    ChangePasswordRequest,
    Enable2FAResponse,
    LoginHistoryEntry,
    NotificationPrefsResponse,
    NotificationPrefsUpdateRequest,
    OrgSettingsResponse,
    OrgSettingsUpdateRequest,
    SessionInfo,
    WebhookCreateRequest,
    WebhookResponse,
    WebhookUpdateRequest,
)

router = APIRouter()


@router.get("/integrations/status")
async def get_integrations_status(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
):
    """Get configured/not-configured status for each integration."""
    from app.config import get_settings

    app_settings = get_settings()

    def _is_set(value: str | None) -> bool:
        if not value:
            return False
        v = str(value).strip()
        return bool(v) and not v.startswith("YOUR_")

    integrations = [
        {
            "id": "stripe",
            "name": "Stripe",
            "category": "payments",
            "description": "Process subscriptions and one-time payments.",
            "configured": _is_set(getattr(app_settings, "STRIPE_SECRET_KEY", None)),
            "docs_url": "https://stripe.com/docs",
        },
        {
            "id": "sendgrid",
            "name": "SendGrid",
            "category": "email",
            "description": "Transactional email delivery.",
            "configured": _is_set(getattr(app_settings, "SENDGRID_API_KEY", None)),
            "docs_url": "https://sendgrid.com/docs",
        },
        {
            "id": "s3",
            "name": "Amazon S3",
            "category": "storage",
            "description": "Object storage for assets and exports.",
            "configured": bool(getattr(app_settings, "S3_BUCKET", None)),
            "docs_url": "https://docs.aws.amazon.com/s3/",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "category": "ai",
            "description": "GPT-powered writing and generation.",
            "configured": _is_set(getattr(app_settings, "OPENAI_API_KEY", None)),
            "docs_url": "https://platform.openai.com/docs",
        },
        {
            "id": "anthropic",
            "name": "Anthropic Claude",
            "category": "ai",
            "description": "Claude-powered writing and generation.",
            "configured": _is_set(getattr(app_settings, "ANTHROPIC_API_KEY", None)),
            "docs_url": "https://docs.anthropic.com",
        },
    ]
    return {"integrations": integrations}


@router.get("/organization", response_model=OrgSettingsResponse)
async def get_org_settings(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Get organization settings."""
    return await service.get_org_settings(db, current_user["org_id"])


@router.patch("/organization", response_model=OrgSettingsResponse)
async def update_org_settings(
    data: OrgSettingsUpdateRequest,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Update organization settings (admin/owner only)."""
    return await service.update_org_settings(
        db, current_user["org_id"], data.model_dump(exclude_unset=True)
    )


@router.post("/security/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    return await service.change_password(
        db, current_user["user_id"], data.current_password, data.new_password
    )


@router.post("/security/enable-2fa", response_model=Enable2FAResponse)
async def enable_2fa(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Enable two-factor authentication."""
    return await service.enable_2fa(db, current_user["user_id"])


@router.post("/security/disable-2fa")
async def disable_2fa(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Disable two-factor authentication."""
    return await service.disable_2fa(db, current_user["user_id"])


@router.get("/security/sessions", response_model=list[SessionInfo])
async def get_sessions(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Get all active sessions."""
    return await service.get_sessions(db, current_user["user_id"])


@router.delete("/security/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific session."""
    return await service.revoke_session(db, current_user["user_id"], session_id)


@router.delete("/security/sessions")
async def revoke_all_sessions(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all sessions except current."""
    return await service.revoke_all_sessions(db, current_user["user_id"])


@router.get("/security/login-history", response_model=list[LoginHistoryEntry])
async def get_login_history(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Get login history."""
    return await service.get_login_history(db, current_user["user_id"])


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys (admin/owner only)."""
    return await service.list_api_keys(db, current_user["user_id"], current_user["org_id"])


@router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreateRequest,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key (admin/owner only)."""
    return await service.create_api_key(
        db, current_user["user_id"], current_user["org_id"], data.model_dump()
    )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: UUID,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key (admin/owner only)."""
    return await service.delete_api_key(db, current_user["user_id"], key_id)


@router.post("/api-keys/{key_id}/regenerate", response_model=ApiKeyCreatedResponse)
async def regenerate_api_key(
    key_id: UUID,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate an API key (admin/owner only)."""
    return await service.regenerate_api_key(db, current_user["user_id"], key_id)


@router.get("/webhooks", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """List all webhooks (admin/owner only)."""
    return await service.list_webhooks(db, current_user["org_id"])


@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreateRequest,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new webhook (admin/owner only)."""
    return await service.create_webhook(db, current_user["org_id"], data.model_dump())


@router.patch("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdateRequest,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Update a webhook (admin/owner only)."""
    return await service.update_webhook(
        db, current_user["org_id"], webhook_id, data.model_dump(exclude_unset=True)
    )


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook (admin/owner only)."""
    return await service.delete_webhook(db, current_user["org_id"], webhook_id)


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: UUID,
    current_user: dict = Depends(require_role("admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Test a webhook (admin/owner only)."""
    return await service.test_webhook(db, current_user["org_id"], webhook_id)


@router.get("/notifications", response_model=NotificationPrefsResponse)
async def get_notification_prefs(
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Get notification preferences."""
    return await service.get_notification_prefs(db, current_user["user_id"])


@router.patch("/notifications", response_model=NotificationPrefsResponse)
async def update_notification_prefs(
    data: NotificationPrefsUpdateRequest,
    current_user: dict = Depends(require_role("member", "editor", "admin", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Update notification preferences."""
    return await service.update_notification_prefs(
        db, current_user["user_id"], data.model_dump(exclude_unset=True)
    )
