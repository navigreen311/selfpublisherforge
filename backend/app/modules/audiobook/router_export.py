"""API router for audiobook export & download endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import service_export
from app.modules.audiobook.schemas_extended import (
    DownloadResponse,
    ExportJobResponse,
    ExportListResponse,
    ExportRequest,
)

router = APIRouter()


# ── Export endpoints ──────────────────────────────────────────────────────


@router.post(
    "/{project_id}/export",
    response_model=ExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start audiobook export",
    description=(
        "Start an audiobook export in the specified format and platform. "
        "Returns immediately with a job ID (HTTP 202). Poll the export "
        "status endpoint to track progress."
    ),
)
async def export_audiobook(
    project_id: UUID,
    body: ExportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audiobook = await service_export._get_audiobook_for_org(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
    )
    if not audiobook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audiobook not found for this project.",
        )

    export = await service_export.create_export(
        db,
        audiobook_id=audiobook.id,
        format_=body.format,
        platform=body.platform,
    )
    return export


@router.get(
    "/{project_id}/exports",
    response_model=ExportListResponse,
    summary="List exports for a project",
    description="List all export jobs for an audiobook project.",
)
async def list_exports(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audiobook = await service_export._get_audiobook_for_org(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
    )
    if not audiobook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audiobook not found for this project.",
        )

    exports = await service_export.list_exports(db, audiobook_id=audiobook.id)
    return ExportListResponse(items=exports, total=len(exports))


@router.get(
    "/{project_id}/exports/{export_id}",
    response_model=ExportJobResponse,
    summary="Get export status",
    description="Get a specific export job's status and download URL if complete.",
)
async def get_export(
    project_id: UUID,
    export_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audiobook = await service_export._get_audiobook_for_org(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
    )
    if not audiobook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audiobook not found for this project.",
        )

    export = await service_export.get_export(
        db,
        export_id=export_id,
        audiobook_id=audiobook.id,
    )
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found.",
        )
    return export


@router.get(
    "/{project_id}/exports/{export_id}/download",
    response_model=DownloadResponse,
    summary="Get download URL",
    description=("Get a pre-signed download URL for a completed export. " "The URL expires after one hour."),
)
async def download_export(
    project_id: UUID,
    export_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audiobook = await service_export._get_audiobook_for_org(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
    )
    if not audiobook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audiobook not found for this project.",
        )

    export = await service_export.get_export(
        db,
        export_id=export_id,
        audiobook_id=audiobook.id,
    )
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found.",
        )

    if export.status.value != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Export is not ready for download (status: {export.status.value}).",
        )

    if not export.file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not available.",
        )

    download_info = await service_export.generate_download_url(export)
    return download_info
