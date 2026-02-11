"""FastAPI router for organization endpoints (/api/v1/orgs/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.organization import schemas, service
from app.schemas.common import MessageResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /orgs/{org_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{org_id}",
    response_model=schemas.OrganizationResponse,
    summary="Get organization",
    description="Retrieve organization details by ID.",
)
async def get_organization(
    org_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details.

    TODO: Add permission check to ensure user belongs to this org.
    """
    return await service.get_organization(db, org_id)


# ---------------------------------------------------------------------------
# PUT /orgs/{org_id}
# ---------------------------------------------------------------------------
@router.put(
    "/{org_id}",
    response_model=schemas.OrganizationResponse,
    summary="Update organization",
    description="Update organization name and description.",
)
async def update_organization(
    org_id: UUID,
    body: schemas.OrganizationUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organization details.

    TODO: Add admin-only permission check.
    """
    return await service.update_organization(
        db,
        org_id=org_id,
        name=body.name,
        description=body.description,
    )


# ---------------------------------------------------------------------------
# GET /orgs/{org_id}/members
# ---------------------------------------------------------------------------
@router.get(
    "/{org_id}/members",
    response_model=schemas.MemberListResponse,
    summary="List organization members",
    description="Get all members of the organization.",
)
async def list_members(
    org_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organization members.

    TODO: Add permission check.
    """
    return await service.list_members(db, org_id)


# ---------------------------------------------------------------------------
# POST /orgs/{org_id}/invitations
# ---------------------------------------------------------------------------
@router.post(
    "/{org_id}/invitations",
    response_model=schemas.InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invitation",
    description="Invite a user to join the organization.",
)
async def create_invitation(
    org_id: UUID,
    body: schemas.InvitationCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an organization invitation.

    TODO: Add admin-only permission check.
    TODO: Send invitation email.
    """
    return await service.create_invitation(
        db,
        org_id=org_id,
        email=body.email,
        role=body.role,
    )


# ---------------------------------------------------------------------------
# GET /orgs/{org_id}/invitations
# ---------------------------------------------------------------------------
@router.get(
    "/{org_id}/invitations",
    response_model=schemas.InvitationListResponse,
    summary="List invitations",
    description="Get all pending invitations for the organization.",
)
async def list_invitations(
    org_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pending invitations.

    TODO: Add permission check.
    """
    return await service.list_invitations(db, org_id)


# ---------------------------------------------------------------------------
# DELETE /orgs/{org_id}/members/{user_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{org_id}/members/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove member",
    description="Remove a member from the organization.",
)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization.

    TODO: Add admin-only permission check.
    TODO: Prevent removing the last admin.
    """
    await service.remove_member(db, org_id, user_id)
    return MessageResponse(message=f"Member {user_id} removed successfully")
