"""FastAPI router for Kindle Fixed-Layout Export & Device Preview.

Endpoints:
  POST /api/v1/specialty/{type}/{id}/export-kindle   - Generate KPF or EPUB
  POST /api/v1/specialty/{type}/{id}/device-preview   - Device preview
  POST /api/v1/specialty/{type}/{id}/read-aloud-sync  - Generate read-aloud data
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty_books.service_kindle_export import (
    ExportFormat,
    FixedLayoutEPUBResponse,
    HighlightMode,
    KindleDevice,
    KindleValidationResponse,
    KPFExportResponse,
    MultiDevicePreviewResponse,
    ReadAloudSyncResponse,
    generate_device_preview,
    generate_fixed_epub,
    generate_kpf,
    generate_read_aloud_sync,
    validate_kindle_export,
)

router = APIRouter()

VALID_BOOK_TYPES = {"childrens", "coloring", "puzzle"}


# ── Request Schemas ──────────────────────────────────────────────────────


class KindleExportRequest(BaseModel):
    """Request body for Kindle export."""

    format: ExportFormat = Field(ExportFormat.KPF, description="Export format: kpf or epub")
    validate_before_export: bool = Field(True, description="Run validation before export")


class DevicePreviewRequest(BaseModel):
    """Request body for device preview generation."""

    device: KindleDevice | None = Field(
        None, description="Specific device, or null for all 6 devices"
    )


class ReadAloudSyncRequest(BaseModel):
    """Request body for read-aloud sync generation."""

    highlight_mode: HighlightMode = Field(
        HighlightMode.SENTENCE, description="word or sentence highlighting"
    )


# ── Response Wrappers ────────────────────────────────────────────────────


class KindleExportResponse(BaseModel):
    """Wrapper for export response that includes optional validation."""

    export: KPFExportResponse | FixedLayoutEPUBResponse
    validation: KindleValidationResponse | None = None


# ── Helpers ──────────────────────────────────────────────────────────────


def _validate_book_type(book_type: str) -> None:
    if book_type not in VALID_BOOK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid book type '{book_type}'. Must be one of: {', '.join(sorted(VALID_BOOK_TYPES))}",
        )


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/{book_type}/{book_id}/export-kindle",
    response_model=KindleExportResponse,
    summary="Export book as Kindle KPF or fixed-layout EPUB",
    description="Generate a Kindle Package Format or fixed-layout EPUB 3 export for the specified book.",
)
async def export_kindle(
    book_type: str,
    book_id: UUID,
    body: KindleExportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KindleExportResponse:
    _validate_book_type(book_type)
    org_id = current_user["org_id"]

    validation = None
    if body.validate_before_export:
        validation = await validate_kindle_export(db, book_type, book_id, org_id)
        if not validation.valid:
            return KindleExportResponse(
                export=await _generate_export(db, body.format, book_type, book_id, org_id),
                validation=validation,
            )

    export = await _generate_export(db, body.format, book_type, book_id, org_id)
    return KindleExportResponse(export=export, validation=validation)


async def _generate_export(
    db: AsyncSession,
    fmt: ExportFormat,
    book_type: str,
    book_id: UUID,
    org_id: UUID,
) -> KPFExportResponse | FixedLayoutEPUBResponse:
    if fmt == ExportFormat.KPF:
        return await generate_kpf(db, book_type, book_id, org_id)
    return await generate_fixed_epub(db, book_type, book_id, org_id)


@router.post(
    "/{book_type}/{book_id}/device-preview",
    response_model=MultiDevicePreviewResponse,
    summary="Generate device preview images",
    description="Render book pages at device resolution for up to 6 devices.",
)
async def device_preview(
    book_type: str,
    book_id: UUID,
    body: DevicePreviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MultiDevicePreviewResponse:
    _validate_book_type(book_type)
    org_id = current_user["org_id"]
    return await generate_device_preview(db, book_type, book_id, org_id, body.device)


@router.post(
    "/{book_type}/{book_id}/read-aloud-sync",
    response_model=ReadAloudSyncResponse,
    summary="Generate read-aloud highlight sync data",
    description="Generate SMIL-like timing data for text-audio synchronization with word or sentence highlighting.",
)
async def read_aloud_sync(
    book_type: str,
    book_id: UUID,
    body: ReadAloudSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadAloudSyncResponse:
    _validate_book_type(book_type)
    org_id = current_user["org_id"]
    return await generate_read_aloud_sync(
        db, book_type, book_id, org_id, body.highlight_mode
    )
