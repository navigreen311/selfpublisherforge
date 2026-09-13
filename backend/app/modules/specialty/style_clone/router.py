"""FastAPI router for Art Style Cloning."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import PaginatedResponse, SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.style_clone import service

router = APIRouter(prefix="/specialty/style-clones", tags=["style-clones"])


@router.get(
    "",
    response_model=SuccessResponse[PaginatedResponse[dict]],
    summary="List style clone profiles",
)
async def list_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    book_type: str | None = Query(None),
    search: str | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.list_profiles(
        db,
        current_user["org_id"],
        page=page,
        page_size=page_size,
        book_type=book_type,
        search=search,
        active_only=active_only,
    )
    return SuccessResponse(data=result)


@router.post(
    "",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create style clone profile",
)
async def create_profile(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile = await service.create_profile(db, current_user["org_id"], payload)
    return SuccessResponse(data=profile)


@router.get(
    "/{profile_id}",
    response_model=SuccessResponse[dict],
    summary="Get style clone profile",
)
async def get_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile = await service.get_profile(db, current_user["org_id"], profile_id)
    return SuccessResponse(data=profile)


@router.patch(
    "/{profile_id}",
    response_model=SuccessResponse[dict],
    summary="Update style clone profile",
)
async def update_profile(
    profile_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile = await service.update_profile(db, current_user["org_id"], profile_id, payload)
    return SuccessResponse(data=profile)


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete style clone profile",
)
async def delete_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_profile(db, current_user["org_id"], profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return


@router.post(
    "/{profile_id}/analyze",
    response_model=SuccessResponse[dict],
    summary="Analyze reference images and extract style",
)
async def analyze_style(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.analyze_style(db, current_user["org_id"], profile_id)
    return SuccessResponse(data=result)


@router.post(
    "/{profile_id}/test-generate",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Generate test images using style",
)
async def test_generate(
    profile_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.test_generate(db, current_user["org_id"], profile_id, payload)
    return SuccessResponse(data=result)


@router.post(
    "/{profile_id}/check-drift",
    response_model=SuccessResponse[dict],
    summary="Check for style drift",
)
async def check_drift(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.check_drift(db, current_user["org_id"], profile_id)
    return SuccessResponse(data=result)


@router.post(
    "/{profile_id}/set-default",
    response_model=SuccessResponse[dict],
    summary="Set as default style profile",
)
async def set_default(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.set_default(db, current_user["org_id"], profile_id)
    return SuccessResponse(data=result)
