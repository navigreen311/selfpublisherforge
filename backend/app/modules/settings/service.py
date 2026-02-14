"""Settings service layer."""
import secrets
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.organization import Organization
from app.models.user import ApiKey, User


async def get_org_settings(db: AsyncSession, org_id: UUID) -> dict:
    """Get organization settings."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Get team members (users in the organization)
    users_result = await db.execute(
        select(User).where(User.org_id == org_id, User.deleted_at.is_(None))
    )
    users = users_result.scalars().all()

    team_members = [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "avatar_url": user.avatar_url,
        }
        for user in users
    ]

    settings = org.settings or {}

    return {
        "name": org.name,
        "website": settings.get("website"),
        "industry": settings.get("industry"),
        "imprint_name": settings.get("imprint_name"),
        "publisher_id": settings.get("publisher_id"),
        "default_genre": settings.get("default_genre"),
        "default_marketplace": settings.get("default_marketplace"),
        "default_currency": settings.get("default_currency", "USD"),
        "team_members": team_members,
    }


async def update_org_settings(db: AsyncSession, org_id: UUID, data: dict) -> dict:
    """Update organization settings."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update name if provided
    if data.get("name") is not None:
        org.name = data["name"]

    # Update settings JSONB field
    current_settings = org.settings or {}

    if data.get("website") is not None:
        current_settings["website"] = data["website"]
    if data.get("industry") is not None:
        current_settings["industry"] = data["industry"]
    if data.get("imprint_name") is not None:
        current_settings["imprint_name"] = data["imprint_name"]
    if data.get("default_genre") is not None:
        current_settings["default_genre"] = data["default_genre"]
    if data.get("default_marketplace") is not None:
        current_settings["default_marketplace"] = data["default_marketplace"]
    if data.get("default_currency") is not None:
        current_settings["default_currency"] = data["default_currency"]

    org.settings = current_settings
    await db.commit()
    await db.refresh(org)

    return await get_org_settings(db, org_id)


async def change_password(db: AsyncSession, user_id: UUID, current_pw: str, new_pw: str) -> dict:
    """Change user password."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(current_pw, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update to new password
    user.password_hash = hash_password(new_pw)
    await db.commit()

    return {"message": "Password changed successfully"}


async def enable_2fa(db: AsyncSession, user_id: UUID) -> dict:
    """Enable 2FA for user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate a mock secret (in production, use pyotp)
    secret = secrets.token_urlsafe(32)
    qr_code_url = f"otpauth://totp/SelfPublisherForge:{user.email}?secret={secret}&issuer=SelfPublisherForge"

    # Store secret (in production, encrypt this)
    user.mfa_secret = secret
    user.mfa_enabled = True
    await db.commit()

    return {
        "secret": secret,
        "qr_code_url": qr_code_url,
    }


async def disable_2fa(db: AsyncSession, user_id: UUID) -> dict:
    """Disable 2FA for user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.mfa_enabled = False
    user.mfa_secret = None
    await db.commit()

    return {"message": "2FA disabled successfully"}


async def get_sessions(db: AsyncSession, user_id: UUID) -> list[dict]:
    """Get all active sessions for user."""
    # Mock data - in production, query UserSession model
    return [
        {
            "id": uuid4(),
            "device": "Desktop",
            "browser": "Chrome 120",
            "os": "Windows 11",
            "ip_address": "192.168.1.1",
            "location": "San Francisco, CA",
            "is_current": True,
            "last_active_at": datetime.now(UTC),
        },
        {
            "id": uuid4(),
            "device": "Mobile",
            "browser": "Safari 17",
            "os": "iOS 17",
            "ip_address": "192.168.1.2",
            "location": "San Francisco, CA",
            "is_current": False,
            "last_active_at": datetime.now(UTC),
        },
    ]


async def revoke_session(db: AsyncSession, user_id: UUID, session_id: UUID) -> dict:
    """Revoke a specific session."""
    # Mock implementation - in production, update UserSession
    return {"message": "Session revoked successfully"}


async def revoke_all_sessions(db: AsyncSession, user_id: UUID) -> dict:
    """Revoke all sessions except current."""
    # Mock implementation - in production, update all UserSession records
    return {"message": "All sessions revoked successfully"}


async def get_login_history(db: AsyncSession, user_id: UUID) -> list[dict]:
    """Get login history for user."""
    # Mock data - in production, query login audit log
    return [
        {
            "id": uuid4(),
            "device": "Desktop",
            "browser": "Chrome 120",
            "ip_address": "192.168.1.1",
            "location": "San Francisco, CA",
            "success": True,
            "created_at": datetime.now(UTC),
        },
        {
            "id": uuid4(),
            "device": "Mobile",
            "browser": "Safari 17",
            "ip_address": "192.168.1.2",
            "location": "San Francisco, CA",
            "success": True,
            "created_at": datetime.now(UTC),
        },
    ]


async def list_api_keys(db: AsyncSession, user_id: UUID, org_id: UUID) -> list[dict]:
    """List all API keys for organization."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.org_id == org_id,
            ApiKey.deleted_at.is_(None)
        )
    )
    keys = result.scalars().all()

    return [
        {
            "id": key.id,
            "name": key.name,
            "key_prefix": key.prefix,
            "permissions": key.scopes or ["read"],
            "last_used_at": key.last_used_at,
            "created_at": key.created_at,
        }
        for key in keys
    ]


async def create_api_key(db: AsyncSession, user_id: UUID, org_id: UUID, data: dict) -> dict:
    """Create a new API key."""
    # Generate random API key
    raw_key = f"spf_{secrets.token_urlsafe(32)}"
    key_hash = hash_password(raw_key)
    prefix = raw_key[:12]

    api_key = ApiKey(
        org_id=org_id,
        created_by=user_id,
        key_hash=key_hash,
        prefix=prefix,
        name=data["name"],
        scopes=data.get("permissions", ["read"]),
        is_active=True,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": raw_key,  # Only shown once
        "permissions": api_key.scopes or ["read"],
    }


async def delete_api_key(db: AsyncSession, user_id: UUID, key_id: UUID) -> dict:
    """Delete (soft delete) an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.deleted_at.is_(None)
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    api_key.deleted_at = datetime.now(UTC)
    await db.commit()

    return {"message": "API key deleted successfully"}


async def regenerate_api_key(db: AsyncSession, user_id: UUID, key_id: UUID) -> dict:
    """Regenerate an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.deleted_at.is_(None)
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Generate new key
    raw_key = f"spf_{secrets.token_urlsafe(32)}"
    key_hash = hash_password(raw_key)
    prefix = raw_key[:12]

    api_key.key_hash = key_hash
    api_key.prefix = prefix
    await db.commit()
    await db.refresh(api_key)

    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": raw_key,  # Only shown once
        "permissions": api_key.scopes or ["read"],
    }


async def list_webhooks(db: AsyncSession, org_id: UUID) -> list[dict]:
    """List all webhooks for organization."""
    # Mock data - in production, query Webhook model
    return [
        {
            "id": uuid4(),
            "url": "https://example.com/webhook",
            "events": ["book.published", "book.updated"],
            "status": "active",
            "last_delivery_at": datetime.now(UTC),
            "last_response_code": 200,
            "created_at": datetime.now(UTC),
        },
    ]


async def create_webhook(db: AsyncSession, org_id: UUID, data: dict) -> dict:
    """Create a new webhook."""
    # Mock implementation - in production, create Webhook record
    webhook_id = uuid4()
    return {
        "id": webhook_id,
        "url": data["url"],
        "events": data["events"],
        "status": "active",
        "last_delivery_at": None,
        "last_response_code": None,
        "created_at": datetime.now(UTC),
    }


async def update_webhook(db: AsyncSession, org_id: UUID, webhook_id: UUID, data: dict) -> dict:
    """Update a webhook."""
    # Mock implementation - in production, update Webhook record
    return {
        "id": webhook_id,
        "url": data.get("url", "https://example.com/webhook"),
        "events": data.get("events", ["book.published"]),
        "status": data.get("status", "active"),
        "last_delivery_at": datetime.now(UTC),
        "last_response_code": 200,
        "created_at": datetime.now(UTC),
    }


async def delete_webhook(db: AsyncSession, org_id: UUID, webhook_id: UUID) -> dict:
    """Delete a webhook."""
    # Mock implementation - in production, soft delete Webhook record
    return {"message": "Webhook deleted successfully"}


async def test_webhook(db: AsyncSession, org_id: UUID, webhook_id: UUID) -> dict:
    """Test a webhook by sending a test payload."""
    # Mock implementation - in production, send actual HTTP request
    return {
        "success": True,
        "status_code": 200,
        "response_time_ms": 123,
    }


async def get_notification_prefs(db: AsyncSession, user_id: UUID) -> dict:
    """Get notification preferences for user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    prefs = user.preferences or {}
    notification_prefs = prefs.get("notifications", {
        "email": {
            "book_published": True,
            "production_complete": True,
            "marketing_updates": False,
        },
        "push": {
            "book_published": True,
            "production_complete": False,
            "marketing_updates": False,
        },
    })

    return {
        "preferences": notification_prefs,
        "quiet_hours_start": prefs.get("quiet_hours_start"),
        "quiet_hours_end": prefs.get("quiet_hours_end"),
    }


async def update_notification_prefs(db: AsyncSession, user_id: UUID, data: dict) -> dict:
    """Update notification preferences for user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    current_prefs = user.preferences or {}

    if data.get("preferences") is not None:
        current_prefs["notifications"] = data["preferences"]
    if data.get("quiet_hours_start") is not None:
        current_prefs["quiet_hours_start"] = data["quiet_hours_start"]
    if data.get("quiet_hours_end") is not None:
        current_prefs["quiet_hours_end"] = data["quiet_hours_end"]

    user.preferences = current_prefs
    await db.commit()

    return await get_notification_prefs(db, user_id)
