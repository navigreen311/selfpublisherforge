"""Pen Name Management API router.

Prefix: /api/v1/pen-names
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.pen_names.schemas import (
    PenNameAnalyticsResponse,
    PenNameBooksResponse,
    PenNameCreate,
    PenNameResponse,
    PenNameUpdate,
)
from app.modules.pen_names.service import PenNameService
from app.modules.team.permissions import require_permission
from app.schemas.common import MessageResponse

router = APIRouter(tags=["pen-names"])


@router.get(
    "",
    response_model=list[PenNameResponse],
    summary="List pen names",
)
async def list_pen_names(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PenNameService.list_pen_names(db, current_user["org_id"])


@router.post(
    "",
    response_model=PenNameResponse,
    status_code=201,
    summary="Create pen name",
    dependencies=[Depends(require_permission("pen_names", "create"))],
)
async def create_pen_name(
    body: PenNameCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PenNameService.create(
        db,
        current_user["org_id"],
        current_user["user_id"],
        body.model_dump(),
    )


@router.get("/{pen_name_id}", response_model=PenNameResponse)
async def get_pen_name(
    pen_name_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PenNameService.get(db, current_user["org_id"], pen_name_id)


@router.patch(
    "/{pen_name_id}",
    response_model=PenNameResponse,
    dependencies=[Depends(require_permission("pen_names", "edit"))],
)
async def update_pen_name(
    pen_name_id: UUID,
    body: PenNameUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PenNameService.update(
        db, current_user["org_id"], pen_name_id,
        body.model_dump(exclude_unset=True),
    )


@router.delete(
    "/{pen_name_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("pen_names", "delete"))],
)
async def delete_pen_name(
    pen_name_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await PenNameService.delete(db, current_user["org_id"], pen_name_id)
    return MessageResponse(message="Pen name deleted")


@router.get("/{pen_name_id}/books", response_model=PenNameBooksResponse)
async def list_books(
    pen_name_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    books = await PenNameService.list_books(
        db, current_user["org_id"], pen_name_id
    )
    return {"books": books}


@router.get("/{pen_name_id}/analytics", response_model=PenNameAnalyticsResponse)
async def get_analytics(
    pen_name_id: UUID,
    period: str = Query("30d", pattern="^(7d|30d|90d|1y|all)$"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PenNameService.get_analytics(
        db, current_user["org_id"], pen_name_id, period
    )
