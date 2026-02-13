"""FastAPI router for audiobook mastering & ACX validation endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import schemas_extended as schemas
from app.modules.audiobook import service_mastering as service

router = APIRouter()


# ── Mastering endpoints ────────────────────────────────────────────────────


@router.post(
    "/{project_id}/master",
    response_model=schemas.MasteringJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start mastering pipeline",
    description=(
        "Start the mastering pipeline for the audiobook. " "Dispatches a Celery task and returns the job info."
    ),
)
async def master_audiobook(
    project_id: UUID,
    body: schemas.MasterRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start the mastering pipeline for the audiobook.

    Accepts mastering options (target_lufs, normalize, noise_gate,
    output_format, sample_rate, bit_rate), dispatches a Celery task,
    and returns the job info with a 202 Accepted status.
    """
    return await service.start_mastering(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
        options=body.model_dump(),
    )


@router.get(
    "/{project_id}/master/status",
    response_model=schemas.MasteringStatusResponse,
    summary="Get mastering status",
    description="Get the current mastering job status for a project.",
)
async def get_mastering_status(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current mastering job status for a project."""
    return await service.get_mastering_status(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
    )


# ── ACX Validation endpoint ───────────────────────────────────────────────


@router.post(
    "/{project_id}/validate",
    response_model=schemas.ACXValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run ACX validation",
    description=(
        "Run ACX compliance validation on the project's audio. "
        "Returns pass/fail for each chapter and an overall result. "
        "Checks: peak level <= -3 dB, RMS -23 to -18 dB, "
        "noise floor < -60 dB, sample rate 44100 Hz, "
        "MP3 CBR 192 kbps, mono channel."
    ),
)
async def validate_audiobook(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run ACX compliance validation on the project's audio."""
    return await service.validate_acx(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
    )
