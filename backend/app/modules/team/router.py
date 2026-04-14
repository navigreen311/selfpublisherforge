"""Team management API (roles, members, invitations)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.team.permissions import require_permission
from app.modules.team.schemas import (
    InvitationResponse,
    InviteCreate,
    RoleAssign,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    TeamMember,
)
from app.modules.team.service import TeamService
from app.schemas.common import MessageResponse

router = APIRouter(tags=["team"])


# ─── Roles ────────────────────────────────────────────────────────────────────

@router.get("/roles", response_model=list[RoleResponse], summary="List roles")
async def list_roles(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.list_roles(db, current_user["org_id"])


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=201,
    summary="Create custom role",
    dependencies=[Depends(require_permission("team", "create"))],
)
async def create_role(
    body: RoleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.create_role(
        db, current_user["org_id"], body.model_dump()
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.get_role(db, current_user["org_id"], role_id)


@router.patch(
    "/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permission("team", "edit"))],
)
async def update_role(
    role_id: UUID,
    body: RoleUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.update_role(
        db, current_user["org_id"], role_id,
        body.model_dump(exclude_unset=True),
    )


@router.delete(
    "/roles/{role_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("team", "delete"))],
)
async def delete_role(
    role_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TeamService.delete_role(db, current_user["org_id"], role_id)
    return MessageResponse(message="Role deleted")


# ─── Team members ────────────────────────────────────────────────────────────

@router.get("/team", response_model=list[TeamMember], summary="List team members")
async def list_team(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.list_team(db, current_user["org_id"])


@router.patch(
    "/team/{user_id}/role",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("team", "edit"))],
)
async def assign_role(
    user_id: UUID,
    body: RoleAssign,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TeamService.assign_role(
        db, current_user["org_id"], user_id, body.role_id
    )
    return MessageResponse(message="Role assigned")


@router.delete(
    "/team/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("team", "delete"))],
)
async def remove_member(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TeamService.remove_member(db, current_user["org_id"], user_id)
    return MessageResponse(message="Member removed")


# ─── Invitations ─────────────────────────────────────────────────────────────

@router.get("/team/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.list_invitations(db, current_user["org_id"])


@router.post(
    "/team/invite",
    response_model=InvitationResponse,
    status_code=201,
    dependencies=[Depends(require_permission("team", "create"))],
)
async def invite_member(
    body: InviteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.invite(
        db,
        current_user["org_id"],
        current_user["user_id"],
        body.model_dump(),
    )


@router.post(
    "/team/invite/{invite_id}/resend",
    response_model=InvitationResponse,
    dependencies=[Depends(require_permission("team", "create"))],
)
async def resend_invitation(
    invite_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TeamService.resend_invitation(
        db, current_user["org_id"], invite_id
    )
