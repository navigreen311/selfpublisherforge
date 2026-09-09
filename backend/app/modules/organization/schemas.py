"""Pydantic request/response schemas for the organization module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PlanTier

# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class OrganizationUpdateRequest(BaseModel):
    """Request to update organization details."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class InvitationCreateRequest(BaseModel):
    """Request to invite a user to the organization."""

    email: str
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class OrganizationResponse(BaseModel):
    """Organization details."""

    id: UUID
    name: str
    description: str | None
    tier: PlanTier
    created_at: datetime
    updated_at: datetime


class MemberResponse(BaseModel):
    """Organization member details."""

    id: UUID
    user_id: UUID
    email: str
    name: str
    role: str
    joined_at: datetime


class MemberListResponse(BaseModel):
    """Response containing list of organization members."""

    members: list[MemberResponse]
    total: int


class InvitationResponse(BaseModel):
    """Organization invitation details."""

    id: UUID
    email: str
    role: str
    status: str
    invited_at: datetime
    expires_at: datetime


class InvitationListResponse(BaseModel):
    """Response containing list of pending invitations."""

    invitations: list[InvitationResponse]
    total: int
