"""FastAPI router for the Pen Names module."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.pen_names import schemas, service

router = APIRouter()


@router.get(
    "",
    response_model=list[schemas.PenNameResponse],
    summary="List pen names",
    description="List all pen names for the current organization (default first).",
)
async def list_pen_names(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pens = await service.list_pen_names(db, current_user["org_id"])
    return [service.to_response(p) for p in pens]


@router.post(
    "",
    response_model=schemas.PenNameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create pen name",
)
async def create_pen_name(
    body: schemas.PenNameCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pen = await service.create_pen_name(
        db,
        org_id=current_user["org_id"],
        user_id=current_user.get("user_id"),
        display_name=body.display_name,
        amazon_url=body.amazon_url,
        bio=body.bio,
        photo_url=body.photo_url,
        genres=body.genres,
        is_default=body.is_default,
    )
    return service.to_response(pen)


@router.get(
    "/{pen_id}",
    response_model=schemas.PenNameResponse,
    summary="Get pen name",
)
async def get_pen_name(
    pen_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pen = await service.get_pen_name(db, current_user["org_id"], pen_id)
    return service.to_response(pen)


@router.patch(
    "/{pen_id}",
    response_model=schemas.PenNameResponse,
    summary="Update pen name",
)
async def update_pen_name(
    pen_id: UUID,
    body: schemas.PenNameUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pen = await service.update_pen_name(
        db,
        org_id=current_user["org_id"],
        pen_id=pen_id,
        display_name=body.display_name,
        amazon_url=body.amazon_url,
        bio=body.bio,
        photo_url=body.photo_url,
        genres=body.genres,
        is_default=body.is_default,
    )
    return service.to_response(pen)


@router.delete(
    "/{pen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pen name",
)
async def delete_pen_name(
    pen_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_pen_name(db, current_user["org_id"], pen_id)
    return None


@router.post(
    "/{pen_id}/set-default",
    response_model=schemas.PenNameResponse,
    summary="Set pen name as default",
)
async def set_default(
    pen_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pen = await service.set_default(db, current_user["org_id"], pen_id)
    return service.to_response(pen)


@router.get(
    "/{pen_id}/books",
    response_model=schemas.PenNameBooksResponse,
    summary="List books attributed to a pen name",
)
async def list_pen_books(
    pen_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    books = await service.list_books_for_pen(db, current_user["org_id"], pen_id)
    return {"books": books}


@router.get(
    "/{pen_id}/analytics",
    response_model=schemas.PenNameAnalyticsResponse,
    summary="Pen name analytics summary",
)
async def pen_analytics(
    pen_id: UUID,
    period: str = Query("30d", pattern="^(7d|30d|90d|365d|all)$"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.pen_analytics(db, current_user["org_id"], pen_id, period)
