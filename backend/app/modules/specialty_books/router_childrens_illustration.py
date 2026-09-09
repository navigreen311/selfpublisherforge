"""FastAPI router for Children's Books illustration, safety, preview, and export.

Endpoints cover illustration generation, character reference images,
safety/preflight checks, preview modes, and multi-format export.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty_books import service_childrens_illustration as svc

router = APIRouter(
    prefix="/specialty-books/childrens",
    tags=["childrens-books-illustration"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class VariationsRequest(BaseModel):
    count: int = Field(default=4, ge=1, le=8, description="Number of variations to generate")


class PreviewRequest(BaseModel):
    mode: str = Field(
        ...,
        description="Preview mode: spread_view, single_page, or look_inside",
    )


class ExportRequest(BaseModel):
    format: str = Field(
        ...,
        description="Export format: print_pdf, kpf, fixed_epub, or png",
    )


class ReflowRequest(BaseModel):
    target_trim_size: str = Field(
        ...,
        description="Target trim size in WxH format (e.g., '8x10')",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{id}/pages/{page_id}/generate-illustration",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI illustration for a page",
    description=(
        "Build prompt from page illustration_prompt + character descriptions, "
        "add style directives, run trademark safety check, and generate illustration."
    ),
)
async def generate_illustration(
    id: UUID,
    page_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.generate_illustration(db, book_id=id, page_id=page_id, org_id=current_user["org_id"])
    return SuccessResponse(data=result)


@router.post(
    "/{id}/pages/{page_id}/generate-variations",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate illustration variations for a page",
    description="Generate multiple illustration variations for comparison.",
)
async def generate_variations(
    id: UUID,
    page_id: UUID,
    request: VariationsRequest = VariationsRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.generate_variations(
        db,
        book_id=id,
        page_id=page_id,
        org_id=current_user["org_id"],
        count=request.count,
    )
    return SuccessResponse(data=result)


@router.post(
    "/{id}/characters/{char_id}/generate-references",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate character reference images",
    description=("Generate 4 reference images for a character: front view, side view, " "happy face, scared face."),
)
async def generate_character_references(
    id: UUID,
    char_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.generate_character_references(db, book_id=id, char_id=char_id, org_id=current_user["org_id"])
    return SuccessResponse(data=result)


@router.post(
    "/{id}/safety-check",
    response_model=SuccessResponse,
    summary="Run trademark and content safety check",
    description=(
        "Scan all illustration prompts and text content for trademark violations " "and content sensitivity issues."
    ),
)
async def safety_check(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.safety_check(db, book_id=id, org_id=current_user["org_id"])
    return SuccessResponse(data=result)


@router.post(
    "/{id}/preflight",
    response_model=SuccessResponse,
    summary="Run enhanced preflight check",
    description=(
        "Comprehensive preflight validation: illustrations, margins, DPI, "
        "gutter, page count, fonts, trademarks, content, language level."
    ),
)
async def run_preflight(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.run_preflight(db, book_id=id, org_id=current_user["org_id"])
    return SuccessResponse(data=result)


@router.post(
    "/{id}/export",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Export book as Print PDF, EPUB, or PNG",
    description=(
        "Export in print_pdf (KDP interior with bleed/trim/300 DPI), "
        "fixed_epub (EPUB 3), or png (individual pages). "
        "Includes provenance report and font license summary."
    ),
)
async def export_book(
    id: UUID,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.export_book(
        db,
        book_id=id,
        org_id=current_user["org_id"],
        format=request.format,
    )
    return SuccessResponse(data=result)


@router.post(
    "/{id}/export-kindle",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Export book as Kindle Package Format (KPF)",
    description=("Export the book as a Kindle Package Format file " "for Kindle Fire and iPad."),
)
async def export_kindle(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.export_book(db, book_id=id, org_id=current_user["org_id"], format="kpf")
    return SuccessResponse(data=result)


@router.post(
    "/{id}/device-preview",
    response_model=SuccessResponse,
    summary="Generate device preview",
    description=(
        "Preview the book in spread_view, single_page, or look_inside mode. "
        "Includes guide overlays for bleed, trim, safe zone, and gutter."
    ),
)
async def device_preview(
    id: UUID,
    request: PreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.generate_preview(db, book_id=id, org_id=current_user["org_id"], mode=request.mode)
    return SuccessResponse(data=result)


@router.post(
    "/{id}/gutter-check",
    response_model=SuccessResponse,
    summary="Check for gutter collisions",
    description="Detect faces and text elements near the fold/spine.",
)
async def gutter_check(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.check_gutter_collisions(db, book_id=id, org_id=current_user["org_id"])
    return SuccessResponse(data=result)


@router.post(
    "/{id}/reflow",
    response_model=SuccessResponse,
    summary="Reflow book to a different trim size",
    description=("Generate a reflow plan for converting the book between trim sizes."),
)
async def reflow(
    id: UUID,
    request: ReflowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.generate_reflow(
        db,
        book_id=id,
        org_id=current_user["org_id"],
        target_trim_size=request.target_trim_size,
    )
    return SuccessResponse(data=result)
