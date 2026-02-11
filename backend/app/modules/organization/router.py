"""FastAPI router for organization endpoints (/api/v1/orgs/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.notifications.email import send_transactional_email
from app.modules.organization import schemas, service
from app.schemas.common import MessageResponse
from app.config import get_settings

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
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details.

    Requires user to be a member of the organization.
    """
    # Check user belongs to org
    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

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
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update organization details.

    Requires owner or admin role.
    """
    # Check user belongs to org
    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

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
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organization members.

    Requires user to be a member of the organization.
    """
    # Check user belongs to org
    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

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
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create an organization invitation.

    Requires owner or admin role.
    Sends an invitation email to the invitee.
    """
    # Check user belongs to org
    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Create invitation
    invitation = await service.create_invitation(
        db,
        org_id=org_id,
        email=body.email,
        role=body.role,
    )

    # Get organization details for email
    org = await service.get_organization(db, org_id)

    # Send invitation email
    settings = get_settings()
    invite_url = f"{settings.FRONTEND_URL}/invitations/{invitation.id}"
    send_transactional_email(
        to_email=body.email,
        template_name="team_invite",
        context={
            "name": body.email.split("@")[0],  # Use email prefix as name placeholder
            "org_name": org.name,
            "invite_url": invite_url,
        },
    )

    return invitation


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
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pending invitations.

    Requires user to be a member of the organization.
    """
    # Check user belongs to org
    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

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
    current_user: dict = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization.

    Requires owner or admin role.
    Prevents removing yourself or the last admin.
    """
    # Check user belongs to org
    if current_user["org_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Prevent removing yourself
    if current_user["user_id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the organization"
        )

    # Check if removing the last admin/owner
    members = await service.list_members(db, org_id)
    admin_count = sum(
        1 for m in members.members
        if m.role in ["owner", "admin"] and m.user_id != user_id
    )

    if admin_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last admin from the organization"
        )

    await service.remove_member(db, org_id, user_id)
    return MessageResponse(message=f"Member {user_id} removed successfully")
