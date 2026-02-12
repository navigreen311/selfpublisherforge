"""FastAPI router for audiobook mastering & export endpoints (/api/v1/audiobooks/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import schemas, service

router = APIRouter()


# ── Master ────────────────────────────────────────────────────────────────


@router.post(
    "/{audiobook_id}/master",
    response_model=schemas.MasteringJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Master audiobook",
    description="Merge all chapters, apply mastering processing chain, and produce a master file.",
)
async def master_audiobook(
    audiobook_id: UUID,
    body: schemas.MasterAudiobookRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue a mastering job for the audiobook. All chapters must be approved."""
    org_id = current_user["org_id"]
    return await service.master_audiobook(db, audiobook_id, org_id, body)


# ── Export ────────────────────────────────────────────────────────────────


@router.post(
    "/{audiobook_id}/export",
    response_model=schemas.ExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Export audiobook",
    description="Export the mastered audiobook in a target format for a specific platform.",
)
async def export_audiobook(
    audiobook_id: UUID,
    body: schemas.ExportAudiobookRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export audiobook in target format for a specific platform."""
    org_id = current_user["org_id"]
    return await service.export_audiobook(db, audiobook_id, org_id, body)


# ── Download ──────────────────────────────────────────────────────────────


@router.get(
    "/{audiobook_id}/export/{export_id}/download",
    response_model=schemas.DownloadResponse,
    summary="Download exported audiobook",
    description="Get a pre-signed download URL for a completed export. Link expires in 1 hour.",
)
async def download_export(
    audiobook_id: UUID,
    export_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get download URL for an exported audiobook file."""
    org_id = current_user["org_id"]
    return await service.download_export(db, audiobook_id, export_id, org_id)


# ── Validate ──────────────────────────────────────────────────────────────


@router.post(
    "/{audiobook_id}/validate",
    response_model=schemas.ValidationResponse,
    summary="Validate audiobook",
    description="Validate all chapter audio files against platform specifications (ACX).",
)
async def validate_audiobook(
    audiobook_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run platform validation on all chapter audio files."""
    org_id = current_user["org_id"]
    return await service.validate_audiobook(db, audiobook_id, org_id)


# ── Cost breakdown ────────────────────────────────────────────────────────


@router.get(
    "/{audiobook_id}/cost",
    response_model=schemas.CostBreakdownResponse,
    summary="Get cost breakdown",
    description="Get detailed cost breakdown for the audiobook project by chapter and provider.",
)
async def get_cost_breakdown(
    audiobook_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed cost breakdown for the audiobook project."""
    org_id = current_user["org_id"]
    return await service.get_cost_breakdown(db, audiobook_id, org_id)
