"""Pydantic request/response schemas for the admin module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.types.enums import PlanTier


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class UserListRequest(BaseModel):
    """Request parameters for listing users."""
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    search: str | None = None
    tier: PlanTier | None = None


class FeatureFlagUpdateRequest(BaseModel):
    """Request to update a feature flag."""
    enabled: bool
    description: str | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserListItem(BaseModel):
    """User summary for admin list view."""
    id: UUID
    email: str
    name: str
    created_at: datetime
    tier: PlanTier
    is_active: bool


class UserListResponse(BaseModel):
    """Response containing list of users."""
    users: list[UserListItem]
    total: int


class FeatureFlag(BaseModel):
    """Feature flag details."""
    key: str
    enabled: bool
    description: str | None = None


class FeatureFlagsResponse(BaseModel):
    """Response containing all feature flags."""
    flags: list[FeatureFlag]
