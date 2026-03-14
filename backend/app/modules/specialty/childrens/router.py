"""FastAPI router for the Children's Book Studio.

Endpoints cover full CRUD for books, pages, and characters, plus AI story
generation, readability analysis, character-consistency checks, safety
scanning, bilingual translation, illustration generation, and export/preflight.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import PaginatedResponse, SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.childrens import service
from app.modules.specialty.models.enums import AgeRange, BookStatus

router = APIRouter(prefix="/specialty/childrens-books", tags=["childrens-books"])


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=SuccessResponse[dict],
    summary="Get children's book stats",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.get_stats(db, current_user["org_id"]))


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessResponse[PaginatedResponse[dict]],
    summary="List children's books (paginated)",
)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BookStatus | None = Query(None, alias="status"),
    age_range: AgeRange | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.list_books(
        db,
        current_user["org_id"],
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        age_range=age_range,
    )
    return SuccessResponse(data=result)


@router.post(
    "",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new children's book",
)
async def create_book(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.create_book(db, current_user["org_id"], payload)
    return SuccessResponse(data=book)


@router.get(
    "/{book_id}",
    response_model=SuccessResponse[dict],
    summary="Get children's book detail",
)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.get_book(db, current_user["org_id"], book_id)
    return SuccessResponse(data=book)


@router.patch(
    "/{book_id}",
    response_model=SuccessResponse[dict],
    summary="Update a children's book",
)
async def update_book(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.update_book(db, current_user["org_id"], book_id, payload)
    return SuccessResponse(data=book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a children's book",
)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_book(db, current_user["org_id"], book_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return


# ---------------------------------------------------------------------------
# Page CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/{book_id}/pages",
    response_model=SuccessResponse[list[dict]],
    summary="List pages for a book",
)
async def list_pages(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pages = await service.list_pages(db, current_user["org_id"], book_id)
    return SuccessResponse(data=pages)


@router.post(
    "/{book_id}/pages",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a page in a book",
)
async def create_page(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    page = await service.create_page(db, current_user["org_id"], book_id, payload)
    return SuccessResponse(data=page)


@router.patch(
    "/{book_id}/pages/{page_id}",
    response_model=SuccessResponse[dict],
    summary="Update a page",
)
async def update_page(
    book_id: UUID,
    page_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    page = await service.update_page(db, current_user["org_id"], book_id, page_id, payload)
    return SuccessResponse(data=page)


@router.delete(
    "/{book_id}/pages/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a page",
)
async def delete_page(
    book_id: UUID,
    page_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_page(db, current_user["org_id"], book_id, page_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return


@router.post(
    "/{book_id}/pages/reorder",
    response_model=SuccessResponse[list[dict]],
    summary="Reorder pages",
)
async def reorder_pages(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Expects ``{"page_ids": [uuid, uuid, ...]}`` in desired order."""
    page_ids = payload.get("page_ids", [])
    pages = await service.reorder_pages(db, current_user["org_id"], book_id, page_ids)
    return SuccessResponse(data=pages)


# ---------------------------------------------------------------------------
# Illustration endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/pages/{page_id}/generate-illustration",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate illustration for a page",
)
async def generate_illustration(
    book_id: UUID,
    page_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_illustration(
        db, current_user["org_id"], book_id, page_id, payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/pages/{page_id}/generate-variations",
    response_model=SuccessResponse[list[dict]],
    status_code=status.HTTP_201_CREATED,
    summary="Generate 4 illustration variations",
)
async def generate_variations(
    book_id: UUID,
    page_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    results = await service.generate_illustration_variations(
        db, current_user["org_id"], book_id, page_id, payload or {},
    )
    return SuccessResponse(data=results)


@router.post(
    "/{book_id}/pages/{page_id}/upload-image",
    response_model=SuccessResponse[dict],
    summary="Upload a custom image for a page",
)
async def upload_page_image(
    book_id: UUID,
    page_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.upload_page_image(
        db, current_user["org_id"], book_id, page_id, file,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Character CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/{book_id}/characters",
    response_model=SuccessResponse[list[dict]],
    summary="List characters for a book",
)
async def list_characters(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    chars = await service.list_characters(db, current_user["org_id"], book_id)
    return SuccessResponse(data=chars)


@router.post(
    "/{book_id}/characters",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a character",
)
async def create_character(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    char = await service.create_character(db, current_user["org_id"], book_id, payload)
    return SuccessResponse(data=char)


@router.patch(
    "/{book_id}/characters/{char_id}",
    response_model=SuccessResponse[dict],
    summary="Update a character",
)
async def update_character(
    book_id: UUID,
    char_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    char = await service.update_character(
        db, current_user["org_id"], book_id, char_id, payload,
    )
    return SuccessResponse(data=char)


@router.delete(
    "/{book_id}/characters/{char_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a character",
)
async def delete_character(
    book_id: UUID,
    char_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_character(
        db, current_user["org_id"], book_id, char_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return


@router.post(
    "/{book_id}/characters/{char_id}/generate-references",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Generate 4 reference images for a character",
)
async def generate_character_references(
    book_id: UUID,
    char_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_character_references(
        db, current_user["org_id"], book_id, char_id,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# AI / Analysis endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/generate-story",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate a full story with illustration prompts",
)
async def generate_story(
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_story(
        db, current_user["org_id"], book_id, payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/analyze-text",
    response_model=SuccessResponse[dict],
    summary="Readability, rhythm, and pacing analysis",
)
async def analyze_text(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.analyze_text(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/continuity-check",
    response_model=SuccessResponse[dict],
    summary="Check illustration prompt consistency against character sheets",
)
async def continuity_check(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.check_continuity(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/auto-fix-prompts",
    response_model=SuccessResponse[dict],
    summary="Batch-fix illustration prompts to include character descriptions",
)
async def auto_fix_prompts(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.auto_fix_prompts(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/safety-check",
    response_model=SuccessResponse[dict],
    summary="Trademark and content sensitivity check",
)
async def safety_check(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.check_safety(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/translate",
    response_model=SuccessResponse[dict],
    summary="Generate bilingual translation",
)
async def translate_book(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.translate_book(
        db, current_user["org_id"], book_id, payload,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Export / Preflight endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/export",
    response_model=SuccessResponse[dict],
    summary="Generate export file (PDF / PNG pages)",
)
async def export_book(
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.export_book(
        db, current_user["org_id"], book_id, payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/export-kindle",
    response_model=SuccessResponse[dict],
    summary="Fixed-layout KPF/EPUB export",
)
async def export_kindle(
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.export_kindle(
        db, current_user["org_id"], book_id, payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/device-preview",
    response_model=SuccessResponse[dict],
    summary="Device-accurate preview images",
)
async def device_preview(
    book_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.device_preview(
        db, current_user["org_id"], book_id, payload or {},
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/preflight",
    response_model=SuccessResponse[dict],
    summary="Run full preflight check",
)
async def preflight(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.run_preflight(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/gutter-check",
    response_model=SuccessResponse[dict],
    summary="Check for gutter collisions",
)
async def gutter_check(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.gutter_check(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/reflow",
    response_model=SuccessResponse[dict],
    summary="Generate alternate trim-size version",
)
async def reflow(
    book_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.reflow(
        db, current_user["org_id"], book_id, payload,
    )
    return SuccessResponse(data=result)
