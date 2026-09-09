"""FastAPI router for Photo Integration."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import PaginatedResponse, SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.models.enums import PhotoUsageType
from app.modules.specialty.photo import service

router = APIRouter(prefix="/specialty/photo-references", tags=["photo-references"])


@router.get(
    "",
    response_model=SuccessResponse[PaginatedResponse[dict]],
    summary="List photo references",
)
async def list_photos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    book_type: str | None = Query(None),
    book_id: UUID | None = Query(None),
    usage_type: PhotoUsageType | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.list_photos(
        db,
        current_user["org_id"],
        page=page,
        page_size=page_size,
        book_type=book_type,
        book_id=book_id,
        usage_type=usage_type,
        search=search,
    )
    return SuccessResponse(data=result)


@router.post(
    "",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a photo reference",
)
async def upload_photo(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    usage_type: str = Form("style_reference"),
    book_type: str | None = Form(None),
    book_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    payload = {
        "name": name,
        "description": description,
        "usage_type": usage_type,
        "book_type": book_type,
        "book_id": book_id,
    }
    photo = await service.upload_photo(db, current_user["org_id"], file, payload)
    return SuccessResponse(data=photo)


@router.get(
    "/{photo_id}",
    response_model=SuccessResponse[dict],
    summary="Get photo reference detail",
)
async def get_photo(
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    photo = await service.get_photo(db, current_user["org_id"], photo_id)
    return SuccessResponse(data=photo)


@router.patch(
    "/{photo_id}",
    response_model=SuccessResponse[dict],
    summary="Update photo reference",
)
async def update_photo(
    photo_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    photo = await service.update_photo(db, current_user["org_id"], photo_id, payload)
    return SuccessResponse(data=photo)


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete photo reference",
)
async def delete_photo(
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_photo(db, current_user["org_id"], photo_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return


@router.post(
    "/generate-with-refs",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Generate image using photo references",
)
async def generate_with_references(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_with_references(db, current_user["org_id"], payload)
    return SuccessResponse(data=result)
