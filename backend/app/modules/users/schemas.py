"""Pydantic schemas for User & Organization management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import PlanTier, TimestampMixin, UserRole

# ─── User Profile ────────────────────────────────────────────────────────────


class UserProfile(TimestampMixin):
    """Full user profile returned by GET /users/me."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    avatar_url: str | None = None
    role: UserRole
    org_id: UUID
    preferences: dict[str, Any] | None = Field(default_factory=dict)
    is_active: bool = True
    mfa_enabled: bool = False


class UpdateUserRequest(BaseModel):
    """Fields that a user can update on their own profile."""

    name: str | None = Field(None, min_length=1, max_length=120)
    avatar_url: str | None = None


class UpdatePreferencesRequest(BaseModel):
    """Partial JSONB merge for user preferences."""

    preferences: dict[str, Any]


# ─── Sessions ────────────────────────────────────────────────────────────────


class SessionResponse(BaseModel):
    """Representation of an active user session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
    last_active_at: datetime | None = None


# ─── Organization ────────────────────────────────────────────────────────────


class OrgDetails(TimestampMixin):
    """Organization details returned by GET /orgs/{id}."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan_tier: PlanTier
    logo_url: str | None = None
    max_members: int = 5


class UpdateOrgRequest(BaseModel):
    """Fields that an owner or admin can update on the org."""

    name: str | None = Field(None, min_length=1, max_length=200)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    logo_url: str | None = None


class OrgMember(BaseModel):
    """A single member entry in the organization member list."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    name: str
    role: UserRole
    joined_at: datetime


class InviteRequest(BaseModel):
    """Payload to invite a user to the organization."""

    email: EmailStr
    role: UserRole = UserRole.VIEWER


class InviteResponse(BaseModel):
    """Response after creating an invitation."""

    id: UUID
    email: str
    role: UserRole
    invited_at: datetime
    expires_at: datetime


class ChangeRoleRequest(BaseModel):
    """Payload to change a member's role (owner only)."""

    role: UserRole


# ─── API Keys ────────────────────────────────────────────────────────────────


class ApiKeyCreate(BaseModel):
    """Payload to create a new API key."""

    name: str = Field(..., min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    expires_in_days: int | None = Field(None, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    """API key metadata (never returns the raw secret after creation)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    prefix: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_active: bool = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only at creation time — includes the full key."""

    key: str
