"""Organization service -- org/team management, invitations, roles."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.organization import Organization
from app.models.user import User
from app.modules.organization.schemas import (
    InvitationListResponse,
    InvitationResponse,
    MemberListResponse,
    MemberResponse,
    OrganizationResponse,
)

logger = logging.getLogger(__name__)


async def get_organization(db: AsyncSession, org_id: UUID) -> OrganizationResponse:
    """Get organization by ID.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        OrganizationResponse with org details

    Raises:
        AppException: If organization not found
    """
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise AppException(
            status_code=404,
            code="ORGANIZATION_NOT_FOUND",
            message="Organization not found",
        )

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        description=org.description,
        tier=org.plan_tier,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


async def update_organization(
    db: AsyncSession,
    org_id: UUID,
    name: str | None = None,
    description: str | None = None,
) -> OrganizationResponse:
    """Update organization details.

    Args:
        db: Database session
        org_id: Organization ID
        name: New organization name (optional)
        description: New description (optional)

    Returns:
        Updated OrganizationResponse

    Raises:
        AppException: If organization not found
    """
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise AppException(
            status_code=404,
            code="ORGANIZATION_NOT_FOUND",
            message="Organization not found",
        )

    if name is not None:
        org.name = name
    if description is not None:
        org.description = description

    org.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        description=org.description,
        tier=org.plan_tier,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


async def list_members(db: AsyncSession, org_id: UUID) -> MemberListResponse:
    """List all members of an organization.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        MemberListResponse containing members and total count

    Note:
        This is a basic implementation. A full implementation would include
        a separate OrganizationMember table to track roles and permissions.
    """
    query = select(User).where(User.org_id == org_id).order_by(User.created_at)
    result = await db.execute(query)
    users = result.scalars().all()

    members = [
        MemberResponse(
            id=user.id,
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,  # Use actual role from User model
            joined_at=user.created_at,
        )
        for user in users
    ]

    return MemberListResponse(members=members, total=len(members))


async def create_invitation(
    db: AsyncSession,
    org_id: UUID,
    email: str,
    role: str,
) -> InvitationResponse:
    """Create an invitation to join the organization.

    Args:
        db: Database session
        org_id: Organization ID
        email: Invitee email
        role: Role to assign (admin, member, viewer)

    Returns:
        InvitationResponse with invitation details

    Note:
        This is a stub implementation. A full implementation would create
        an invitation record in the database and send an email.
    """
    # Placeholder: generate a mock invitation
    from uuid import uuid4

    invitation_id = uuid4()
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=7)

    logger.info(f"Created invitation {invitation_id} for {email} to org {org_id} as {role}")

    return InvitationResponse(
        id=invitation_id,
        email=email,
        role=role,
        status="pending",
        invited_at=now,
        expires_at=expires_at,
    )


async def list_invitations(db: AsyncSession, org_id: UUID) -> InvitationListResponse:
    """List all pending invitations for an organization.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        InvitationListResponse containing invitations and total count

    Note:
        This is a stub implementation. A full implementation would query
        an invitations table.
    """
    # Placeholder: return empty list
    return InvitationListResponse(invitations=[], total=0)


async def remove_member(db: AsyncSession, org_id: UUID, user_id: UUID) -> None:
    """Remove a member from the organization.

    Args:
        db: Database session
        org_id: Organization ID
        user_id: User ID to remove

    Raises:
        AppException: If user not found or not a member

    Note:
        This is a stub implementation. A full implementation would handle
        member removal properly, including permission checks.
    """
    query = select(User).where(User.id == user_id, User.org_id == org_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(
            status_code=404,
            code="MEMBER_NOT_FOUND",
            message="Member not found in this organization",
        )

    # In a real implementation, we would move the user to a "removed" state
    # or disassociate them from the organization
    logger.info(f"Removed user {user_id} from organization {org_id}")
