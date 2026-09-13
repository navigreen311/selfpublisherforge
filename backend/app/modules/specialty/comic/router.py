"""FastAPI router for the Comic Book Studio."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import PaginatedResponse, SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.comic import service
from app.modules.specialty.models.enums import BookStatus, ComicFormat

router = APIRouter(prefix="/specialty/comic-books", tags=["comic-books"])


@router.get("", response_model=SuccessResponse[PaginatedResponse[dict]], summary="List comic books")
async def list_comics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BookStatus | None = Query(None, alias="status"),
    format_filter: ComicFormat | None = Query(None, alias="format"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(
        data=await service.list_comics(
            db,
            current_user["org_id"],
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            format_filter=format_filter,
            search=search,
        )
    )


@router.post(
    "", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED, summary="Create a new comic book"
)
async def create_comic(
    payload: dict[str, Any], db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return SuccessResponse(data=await service.create_comic(db, current_user["org_id"], payload))


@router.get("/stats", response_model=SuccessResponse[dict], summary="Get comic book stats")
async def get_stats(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return SuccessResponse(data=await service.get_stats(db, current_user["org_id"]))


@router.get("/layout-templates", response_model=SuccessResponse[list[dict]], summary="Get layout templates")
async def get_layout_templates(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return SuccessResponse(data=await service.get_layout_templates())


@router.get("/{comic_id}", response_model=SuccessResponse[dict], summary="Get comic book detail")
async def get_comic(comic_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return SuccessResponse(data=await service.get_comic(db, current_user["org_id"], comic_id))


@router.patch("/{comic_id}", response_model=SuccessResponse[dict], summary="Update a comic book")
async def update_comic(
    comic_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.update_comic(db, current_user["org_id"], comic_id, payload))


@router.delete("/{comic_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete a comic book")
async def delete_comic(
    comic_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    if not await service.delete_comic(db, current_user["org_id"], comic_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comic not found")


@router.get("/{comic_id}/pages", response_model=SuccessResponse[list[dict]], summary="List pages")
async def list_pages(
    comic_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return SuccessResponse(data=await service.list_pages(db, current_user["org_id"], comic_id))


@router.post(
    "/{comic_id}/pages",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a page",
)
async def create_page(
    comic_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.create_page(db, current_user["org_id"], comic_id, payload))


@router.patch("/{comic_id}/pages/{page_id}", response_model=SuccessResponse[dict], summary="Update a page")
async def update_page(
    comic_id: UUID,
    page_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.update_page(db, current_user["org_id"], comic_id, page_id, payload))


@router.delete("/{comic_id}/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a page")
async def delete_page(
    comic_id: UUID, page_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    if not await service.delete_page(db, current_user["org_id"], comic_id, page_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")


@router.post("/{comic_id}/pages/reorder", response_model=SuccessResponse[list[dict]], summary="Reorder pages")
async def reorder_pages(
    comic_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(
        data=await service.reorder_pages(db, current_user["org_id"], comic_id, payload.get("page_ids", []))
    )


@router.post(
    "/{comic_id}/pages/{page_id}/apply-layout",
    response_model=SuccessResponse[list[dict]],
    summary="Apply layout template",
)
async def apply_layout(
    comic_id: UUID,
    page_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(
        data=await service.apply_layout_template(db, current_user["org_id"], page_id, payload.get("template_id", ""))
    )


@router.get("/{comic_id}/pages/{page_id}/panels", response_model=SuccessResponse[list[dict]], summary="List panels")
async def list_panels(
    comic_id: UUID, page_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return SuccessResponse(data=await service.list_panels(db, current_user["org_id"], page_id))


@router.post(
    "/{comic_id}/pages/{page_id}/panels",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a panel",
)
async def create_panel(
    comic_id: UUID,
    page_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.create_panel(db, current_user["org_id"], page_id, payload))


@router.patch(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}", response_model=SuccessResponse[dict], summary="Update a panel"
)
async def update_panel(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.update_panel(db, current_user["org_id"], page_id, panel_id, payload))


@router.delete(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a panel"
)
async def delete_panel(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not await service.delete_panel(db, current_user["org_id"], page_id, panel_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")


@router.post(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}/generate-art",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate art for a panel",
)
async def generate_panel_art(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    r = await service.update_panel(
        db, current_user["org_id"], page_id, panel_id, {"art_prompt": (payload or {}).get("art_prompt", "")}
    )
    return SuccessResponse(data={"panel_id": str(panel_id), "status": "queued", **r})


@router.get(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}/bubbles",
    response_model=SuccessResponse[list[dict]],
    summary="List bubbles",
)
async def list_bubbles(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.list_bubbles(db, current_user["org_id"], panel_id))


@router.post(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}/bubbles",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a bubble",
)
async def create_bubble(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.create_bubble(db, current_user["org_id"], panel_id, payload))


@router.patch(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}/bubbles/{bubble_id}",
    response_model=SuccessResponse[dict],
    summary="Update a bubble",
)
async def update_bubble(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    bubble_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.update_bubble(db, current_user["org_id"], panel_id, bubble_id, payload))


@router.delete(
    "/{comic_id}/pages/{page_id}/panels/{panel_id}/bubbles/{bubble_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bubble",
)
async def delete_bubble(
    comic_id: UUID,
    page_id: UUID,
    panel_id: UUID,
    bubble_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not await service.delete_bubble(db, current_user["org_id"], panel_id, bubble_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bubble not found")


@router.get("/{comic_id}/script", response_model=SuccessResponse[dict], summary="Get full comic script")
async def get_script(
    comic_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return SuccessResponse(data=await service.get_script(db, current_user["org_id"], comic_id))


@router.put("/{comic_id}/script", response_model=SuccessResponse[dict], summary="Update comic script")
async def update_script(
    comic_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.update_script(db, current_user["org_id"], comic_id, payload))


@router.post(
    "/{comic_id}/generate-script",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate a comic script",
)
async def generate_script(
    comic_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.generate_script(db, current_user["org_id"], comic_id, payload or {}))


@router.post(
    "/{comic_id}/panels/{panel_id}/expand",
    response_model=SuccessResponse[dict],
    summary="AI-expand a panel description",
)
async def expand_panel(
    comic_id: UUID,
    panel_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(
        data=await service.expand_panel(db, current_user["org_id"], comic_id, panel_id, payload or {})
    )


@router.post(
    "/{comic_id}/generate-next-page",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate next page script",
)
async def generate_next_page(
    comic_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.generate_next_page(db, current_user["org_id"], comic_id, payload or {}))


@router.get("/{comic_id}/characters", response_model=SuccessResponse[list[dict]], summary="List characters")
async def list_characters(
    comic_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return SuccessResponse(data=await service.list_characters(db, current_user["org_id"], comic_id))


@router.post(
    "/{comic_id}/characters",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a character",
)
async def create_character(
    comic_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.create_character(db, current_user["org_id"], comic_id, payload))


@router.patch("/{comic_id}/characters/{char_id}", response_model=SuccessResponse[dict], summary="Update a character")
async def update_character(
    comic_id: UUID,
    char_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.update_character(db, current_user["org_id"], comic_id, char_id, payload))


@router.delete("/{comic_id}/characters/{char_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a character")
async def delete_character(
    comic_id: UUID, char_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    if not await service.delete_character(db, current_user["org_id"], comic_id, char_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")


@router.post(
    "/{comic_id}/characters/{char_id}/generate-references",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Generate character references",
)
async def generate_character_references(
    comic_id: UUID, char_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return SuccessResponse(
        data=await service.generate_character_references(db, current_user["org_id"], comic_id, char_id)
    )


@router.post(
    "/{comic_id}/characters/{char_id}/expressions",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add expression",
)
async def add_expression(
    comic_id: UUID,
    char_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.add_expression(db, current_user["org_id"], char_id, payload))


@router.post(
    "/{comic_id}/characters/{char_id}/poses",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add pose",
)
async def add_pose(
    comic_id: UUID,
    char_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.add_pose(db, current_user["org_id"], char_id, payload))


@router.post(
    "/{comic_id}/characters/{char_id}/costumes",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add costume",
)
async def add_costume(
    comic_id: UUID,
    char_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.add_costume(db, current_user["org_id"], char_id, payload))


@router.post("/{comic_id}/export", response_model=SuccessResponse[dict], summary="Generate export file")
async def export_comic(
    comic_id: UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return SuccessResponse(data=await service.export_comic(db, current_user["org_id"], comic_id, payload or {}))


@router.post("/{comic_id}/preflight", response_model=SuccessResponse[dict], summary="Run preflight check")
async def preflight(comic_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return SuccessResponse(data=await service.run_preflight(db, current_user["org_id"], comic_id))
