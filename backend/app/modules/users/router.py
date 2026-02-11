"""API router for User & Organization management.

Prefix: /api/v1/users  and  /api/v1/orgs
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.users.schemas import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    ChangeRoleRequest,
    InviteRequest,
    InviteResponse,
    OrgDetails,
    OrgMember,
    SessionResponse,
    UpdateOrgRequest,
    UpdatePreferencesRequest,
    UpdateUserRequest,
    UserProfile,
)
from app.modules.users.service import UserService
from app.schemas.common import MessageResponse

router = APIRouter(tags=["users"])


# ─── User Profile ────────────────────────────────────────────────────────────

@router.get(
    "/users/me",
    response_model=UserProfile,
    summary="Get current user profile",
    description="Get the authenticated user's profile including preferences.",
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's profile."""
    return await UserService.get_user_profile(db, current_user["user_id"])


@router.patch(
    "/users/me",
    response_model=UserProfile,
    summary="Update user profile",
    description="Update the authenticated user's profile fields.",
)
async def update_current_user_profile(
    body: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    return await UserService.update_user_profile(
        db, current_user["user_id"], body.model_dump(exclude_unset=True)
    )


@router.patch(
    "/users/me/preferences",
    response_model=UserProfile,
    summary="Update user preferences",
    description="Merge-update user preferences stored as JSONB.",
)
async def update_user_preferences(
    body: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Merge-update user preferences (JSONB)."""
    return await UserService.update_preferences(
        db, current_user["user_id"], body.preferences
    )


# ─── Sessions ────────────────────────────────────────────────────────────────

@router.get(
    "/users/me/sessions",
    response_model=list[SessionResponse],
    summary="List active sessions",
    description="List the current user's active login sessions.",
)
async def list_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's active sessions."""
    return await UserService.list_sessions(db, current_user["user_id"])


@router.delete(
    "/users/me/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Revoke session",
    description="Revoke a specific login session by ID.",
)
async def revoke_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific session."""
    await UserService.revoke_session(db, current_user["user_id"], session_id)
    return MessageResponse(message="Session revoked successfully")


# ─── Organization ────────────────────────────────────────────────────────────

@router.get(
    "/orgs/{org_id}",
    response_model=OrgDetails,
    summary="Get organization details",
    description="Get organization details including plan and settings.",
)
async def get_org_details(
    org_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details."""
    _assert_org_access(current_user, org_id)
    return await UserService.get_org(db, org_id)


@router.patch(
    "/orgs/{org_id}",
    response_model=OrgDetails,
    summary="Update organization",
    description="Update organization settings. Requires owner or admin role.",
)
async def update_org(
    org_id: UUID,
    body: UpdateOrgRequest,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update organization settings (owner/admin only)."""
    _assert_org_access(current_user, org_id)
    return await UserService.update_org(
        db, org_id, body.model_dump(exclude_unset=True), current_user
    )


@router.get(
    "/orgs/{org_id}/members",
    response_model=list[OrgMember],
    summary="List organization members",
    description="List all members in the organization.",
)
async def list_org_members(
    org_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members in the organization."""
    _assert_org_access(current_user, org_id)
    return await UserService.list_members(db, org_id)


@router.post(
    "/orgs/{org_id}/invite",
    response_model=InviteResponse,
    status_code=201,
    summary="Invite member",
    description="Invite a new user to the organization. Requires owner or admin role.",
)
async def invite_member(
    org_id: UUID,
    body: InviteRequest,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new user to the organization."""
    _assert_org_access(current_user, org_id)
    return await UserService.invite_member(
        db, org_id, body.email, body.role.value, current_user
    )


@router.patch(
    "/orgs/{org_id}/members/{user_id}/role",
    response_model=MessageResponse,
    summary="Change member role",
    description="Change a member's role within the organization. Requires owner role.",
)
async def change_member_role(
    org_id: UUID,
    user_id: UUID,
    body: ChangeRoleRequest,
    current_user: dict = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Change a member's role (owner only)."""
    _assert_org_access(current_user, org_id)
    await UserService.change_member_role(
        db, org_id, user_id, body.role.value, current_user
    )
    return MessageResponse(message="Role updated successfully")


@router.delete(
    "/orgs/{org_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Remove member",
    description="Remove a member from the organization. Requires owner or admin role.",
)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization."""
    _assert_org_access(current_user, org_id)
    await UserService.remove_member(db, org_id, user_id, current_user)
    return MessageResponse(message="Member removed successfully")


# ─── API Keys ────────────────────────────────────────────────────────────────

@router.post(
    "/orgs/{org_id}/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=201,
    summary="Create API key",
    description="Create a new API key for the organization. Requires owner or admin role.",
)
async def create_api_key(
    org_id: UUID,
    body: ApiKeyCreate,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for the organization."""
    _assert_org_access(current_user, org_id)
    return await UserService.create_api_key(
        db, org_id, body.model_dump(), current_user
    )


@router.get(
    "/orgs/{org_id}/api-keys",
    response_model=list[ApiKeyResponse],
    summary="List API keys",
    description="List all active API keys for the organization.",
)
async def list_api_keys(
    org_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active API keys for the organization."""
    _assert_org_access(current_user, org_id)
    return await UserService.list_api_keys(db, org_id)


@router.delete(
    "/orgs/{org_id}/api-keys/{key_id}",
    response_model=MessageResponse,
    summary="Revoke API key",
    description="Revoke an API key. Requires owner or admin role.",
)
async def revoke_api_key(
    org_id: UUID,
    key_id: UUID,
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    _assert_org_access(current_user, org_id)
    await UserService.revoke_api_key(db, org_id, key_id, current_user)
    return MessageResponse(message="API key revoked successfully")


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _assert_org_access(current_user: dict, org_id: UUID) -> None:
    """Ensure the current user belongs to the requested organization."""
    from fastapi import HTTPException, status

    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization",
        )
