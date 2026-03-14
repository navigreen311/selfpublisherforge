"""FastAPI router for the Coloring Book Creator.

Endpoints (16 total):
    GET/POST   /api/v1/specialty/coloring-books               -- List / Create books
    GET        /api/v1/specialty/coloring-books/{id}           -- Read book
    PATCH      /api/v1/specialty/coloring-books/{id}           -- Update book
    DELETE     /api/v1/specialty/coloring-books/{id}           -- Delete book
    GET        .../{id}/pages                                  -- List pages
    POST       .../{id}/pages/{page_id}/generate               -- Generate line art
    POST       .../{id}/pages/{page_id}/upload                 -- Upload own art
    POST       .../{id}/pages/{page_id}/clean-lines            -- Run cleanup pipeline
    POST       .../{id}/pages/{page_id}/vectorize              -- Convert to SVG
    POST       .../{id}/pages/{page_id}/quality-check          -- Per-page QA
    POST       .../{id}/pages/{page_id}/coloring-simulation    -- Preview colored-in
    POST       .../{id}/batch-generate                         -- Batch generate (async)
    GET        .../{id}/batch-generate/{job_id}/status          -- Poll batch progress
    POST       .../{id}/quality-check                          -- Book-level QA dashboard
    POST       .../{id}/plan-series                            -- Create volume series plan
    POST       .../{id}/generate-next-volume                   -- Auto-generate next volume
    POST       .../{id}/export                                 -- Generate export file
    POST       .../{id}/preflight                              -- Run full preflight
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty.coloring import service

router = APIRouter(prefix="/specialty/coloring-books", tags=["coloring-books"])


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessResponse[list],
    summary="List coloring books",
    description="List all coloring books for the current organization.",
)
async def list_coloring_books(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    books = await service.list_coloring_books(db, current_user["org_id"])
    return SuccessResponse(data=books)


@router.post(
    "",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a coloring book",
    description="Create a new coloring book with wizard settings.",
)
async def create_coloring_book(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.create_coloring_book(db, current_user["org_id"], body)
    return SuccessResponse(data=book)


@router.get(
    "/{book_id}",
    response_model=SuccessResponse[dict],
    summary="Get a coloring book",
    description="Retrieve a single coloring book by ID.",
)
async def get_coloring_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.get_coloring_book(db, current_user["org_id"], book_id)
    return SuccessResponse(data=book)


@router.patch(
    "/{book_id}",
    response_model=SuccessResponse[dict],
    summary="Update a coloring book",
    description="Partially update coloring book metadata. Single-sided is always enforced.",
)
async def update_coloring_book(
    book_id: UUID,
    updates: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    book = await service.update_coloring_book(db, current_user["org_id"], book_id, updates)
    return SuccessResponse(data=book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a coloring book",
    description="Soft-delete a coloring book.",
)
async def delete_coloring_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await service.delete_coloring_book(db, current_user["org_id"], book_id)
    return


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@router.get(
    "/{book_id}/pages",
    response_model=SuccessResponse[list],
    summary="List coloring book pages",
    description="List all pages for a coloring book, ordered by page number.",
)
async def list_pages(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pages = await service.list_pages(db, current_user["org_id"], book_id)
    return SuccessResponse(data=pages)


# ---------------------------------------------------------------------------
# Page-Level Operations
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/pages/{page_id}/generate",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Generate line art",
    description=(
        "Generate coloring-book-specific line art for a page. "
        "Enforces pure line art, no shading, no color, single stroke weight."
    ),
)
async def generate_line_art(
    book_id: UUID,
    page_id: UUID,
    body: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    body = body or {}
    result = await service.generate_line_art(
        db,
        current_user["org_id"],
        book_id,
        page_id,
        prompt=body.get("prompt"),
        style=body.get("style"),
        complexity=body.get("complexity"),
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/pages/{page_id}/upload",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Upload own art",
    description="Upload user-provided line art for a coloring page. Runs quality pipeline automatically.",
)
async def upload_page_art(
    book_id: UUID,
    page_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    image_data = await file.read()
    result = await service.upload_page_art(
        db,
        current_user["org_id"],
        book_id,
        page_id,
        image_data=image_data,
        filename=file.filename or f"{page_id}.png",
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/pages/{page_id}/clean-lines",
    response_model=SuccessResponse[dict],
    summary="Run line art cleanup pipeline",
    description="Run the 7-step quality pipeline on an existing page image to clean lines.",
)
async def clean_lines(
    book_id: UUID,
    page_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.clean_lines(db, current_user["org_id"], book_id, page_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/pages/{page_id}/vectorize",
    response_model=SuccessResponse[dict],
    summary="Convert to SVG vectors",
    description="Convert raster line art to SVG vector format for ultra-crisp print quality.",
)
async def vectorize_page(
    book_id: UUID,
    page_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.vectorize_page(db, current_user["org_id"], book_id, page_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/pages/{page_id}/quality-check",
    response_model=SuccessResponse[dict],
    summary="Per-page quality check",
    description="Run quality verification on a single page and return detailed report.",
)
async def quality_check_page(
    book_id: UUID,
    page_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.quality_check_page(db, current_user["org_id"], book_id, page_id)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/pages/{page_id}/coloring-simulation",
    response_model=SuccessResponse[dict],
    summary="Preview colored-in versions",
    description="Generate a coloring simulation preview with marker, crayon, or colored pencil textures.",
)
async def coloring_simulation(
    book_id: UUID,
    page_id: UUID,
    body: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    body = body or {}
    result = await service.coloring_simulation(
        db,
        current_user["org_id"],
        book_id,
        page_id,
        medium=body.get("medium", "marker"),
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Batch Generation
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/batch-generate",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch generate all pages (async)",
    description=(
        "Queue batch generation of multiple pages with auto-QA per page. "
        "Variation mode prevents similar compositions. Returns a job ID to poll."
    ),
)
async def batch_generate(
    book_id: UUID,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.batch_generate(
        db,
        current_user["org_id"],
        book_id,
        descriptions=body.get("descriptions", []),
        variation_mode=body.get("variation_mode", True),
    )
    return SuccessResponse(data=result)


@router.get(
    "/{book_id}/batch-generate/{job_id}/status",
    response_model=SuccessResponse[dict],
    summary="Poll batch progress",
    description="Check the status and progress of a batch generation job.",
)
async def get_batch_status(
    book_id: UUID,
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    result = await service.get_batch_status(current_user["org_id"], book_id, job_id)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Book-Level Quality
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/quality-check",
    response_model=SuccessResponse[dict],
    summary="Book-level quality dashboard data",
    description=(
        "Aggregate quality scores, complexity distribution, theme cohesion, "
        "and print quality summary across all pages."
    ),
)
async def quality_check_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.run_quality_dashboard(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Series & Volume Factory
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/plan-series",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create volume series plan",
    description=(
        "Plan a multi-volume series with consistent branding. "
        "Locks title font, author position, volume badge, and spine layout."
    ),
)
async def plan_series(
    book_id: UUID,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.plan_series(db, current_user["org_id"], book_id, body)
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/generate-next-volume",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Auto-generate next volume",
    description="Clone style settings from this book and create the next volume in the series.",
)
async def generate_next_volume(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.generate_next_volume(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Export & Preflight
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/export",
    response_model=SuccessResponse[dict],
    summary="Generate export file",
    description=(
        "Export the coloring book as PDF, PNG, SVG, or Digital format. "
        "Enforces single-sided printing with blank backs and coloring-safe margins."
    ),
)
async def export_book(
    book_id: UUID,
    body: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    body = body or {}
    result = await service.export_book(
        db,
        current_user["org_id"],
        book_id,
        format=body.get("format", "pdf"),
    )
    return SuccessResponse(data=result)


@router.post(
    "/{book_id}/preflight",
    response_model=SuccessResponse[dict],
    summary="Run full preflight",
    description=(
        "Run comprehensive preflight checks: pure B&W, 300 DPI, stroke uniformity, "
        "closed shapes, no specks, ink density, no duplicates, grayscale, font licensing."
    ),
)
async def run_preflight(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.run_preflight(db, current_user["org_id"], book_id)
    return SuccessResponse(data=result)
