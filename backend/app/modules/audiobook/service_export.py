"""Business logic for audiobook export and download operations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, ForbiddenError, NotFoundError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy model access (avoids circular imports & N806 lint violations)
# ---------------------------------------------------------------------------


def _project_model():
    from app.models.audiobook import AudiobookProject

    return AudiobookProject


def _job_model():
    from app.models.audiobook import AudiobookGenerationJob

    return AudiobookGenerationJob


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_project_or_404(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
):
    """Fetch an audiobook project, verifying it belongs to the org."""
    model = _project_model()
    query = select(model).where(
        model.id == project_id,
        model.deleted_at.is_(None),
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundError("Audiobook project")

    if project.org_id != org_id:
        raise ForbiddenError("Access denied to this audiobook project.")

    return project


async def _get_export_job_or_404(
    db: AsyncSession,
    project_id: UUID,
    export_id: UUID,
    org_id: UUID,
):
    """Fetch an export job, verifying the parent project belongs to the org."""
    await _get_project_or_404(db, project_id, org_id)

    model = _job_model()
    query = select(model).where(
        model.id == export_id,
        model.audiobook_project_id == project_id,
        model.job_type == "format_convert",
        model.deleted_at.is_(None),
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise NotFoundError("Export job")

    return job


# ---------------------------------------------------------------------------
# Start export
# ---------------------------------------------------------------------------


async def start_export(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
    options: dict,
) -> dict:
    """Start audiobook export.

    1. Verify project exists, belongs to org, and has completed mastering.
    2. Create AudiobookGenerationJob with job_type='format_convert'.
    3. Store export options in input_params (format, platform, etc.).
    4. TODO: Dispatch Celery task for conversion.
    5. Return {export_id, status, format, created_at}.
    """
    project = await _get_project_or_404(db, project_id, org_id)

    if project.status not in ("complete", "published"):
        raise AppException(
            status_code=422,
            code="PROJECT_NOT_READY",
            message="Project must have completed mastering before export. "
            f"Current status: '{project.status}'.",
        )

    export_format = options.get("format", project.output_format or "mp3")
    platform = options.get("platform", project.target_platform or "acx")

    input_params = {
        "format": export_format,
        "platform": platform,
        "sample_rate": options.get("sample_rate", project.sample_rate),
        "bit_rate": options.get("bit_rate", project.bit_rate),
        "channels": options.get("channels", project.channels),
    }

    job = _job_model()(
        audiobook_project_id=project_id,
        chapter_id=None,
        job_type="format_convert",
        status="queued",
        priority=5,
        input_params=input_params,
    )
    db.add(job)
    await db.flush()

    # TODO: dispatch Celery task for format conversion once task is implemented

    logger.info(
        "Queued audiobook export: project=%s format=%s platform=%s job=%s",
        project_id,
        export_format,
        platform,
        job.id,
    )

    return {
        "export_id": job.id,
        "status": job.status,
        "format": export_format,
        "created_at": job.created_at,
    }


# ---------------------------------------------------------------------------
# List exports
# ---------------------------------------------------------------------------


async def list_exports(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
) -> dict:
    """List all export jobs for a project.

    Queries AudiobookGenerationJob where job_type='format_convert'
    and project_id matches. Returns {items: [...], total: int}.
    """
    await _get_project_or_404(db, project_id, org_id)

    model = _job_model()

    # Count total
    count_query = select(func.count()).select_from(model).where(
        model.audiobook_project_id == project_id,
        model.job_type == "format_convert",
        model.deleted_at.is_(None),
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch items
    query = (
        select(model)
        .where(
            model.audiobook_project_id == project_id,
            model.job_type == "format_convert",
            model.deleted_at.is_(None),
        )
        .order_by(model.created_at.desc())
    )
    result = await db.execute(query)
    jobs = result.scalars().all()

    items = [
        {
            "export_id": job.id,
            "status": job.status,
            "format": (job.input_params or {}).get("format", "mp3"),
            "platform": (job.input_params or {}).get("platform"),
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
        }
        for job in jobs
    ]

    return {"items": items, "total": total}


# ---------------------------------------------------------------------------
# Get export
# ---------------------------------------------------------------------------


async def get_export(
    db: AsyncSession,
    project_id: UUID,
    export_id: UUID,
    org_id: UUID,
) -> dict | None:
    """Get a specific export job status."""
    job = await _get_export_job_or_404(db, project_id, export_id, org_id)

    return {
        "export_id": job.id,
        "status": job.status,
        "format": (job.input_params or {}).get("format", "mp3"),
        "platform": (job.input_params or {}).get("platform"),
        "input_params": job.input_params or {},
        "output": job.output or {},
        "error_message": job.error_message,
        "retry_count": job.retry_count,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
    }


# ---------------------------------------------------------------------------
# Get download URL
# ---------------------------------------------------------------------------


async def get_download_url(
    db: AsyncSession,
    project_id: UUID,
    export_id: UUID,
    org_id: UUID,
) -> dict | None:
    """Get download URL for a completed export.

    Verifies export is completed, then returns the output audio URL.
    For now, returns the output.audio_url from the job if available.
    In production, this would generate a pre-signed S3 URL.
    """
    job = await _get_export_job_or_404(db, project_id, export_id, org_id)

    if job.status != "completed":
        raise AppException(
            status_code=422,
            code="EXPORT_NOT_COMPLETED",
            message=f"Export is not yet completed. Current status: '{job.status}'.",
        )

    output = job.output or {}
    audio_url = output.get("audio_url")

    if not audio_url:
        raise AppException(
            status_code=404,
            code="DOWNLOAD_NOT_AVAILABLE",
            message="Export completed but no download file is available.",
        )

    # TODO: Generate pre-signed S3 URL instead of returning raw URL.
    # For now, return the stored URL directly.
    expires_at = datetime.now(UTC) + timedelta(hours=24)

    return {
        "download_url": audio_url,
        "expires_at": expires_at,
        "filename": output.get(
            "filename",
            f"export_{export_id}.{(job.input_params or {}).get('format', 'mp3')}",
        ),
        "file_size_bytes": output.get("file_size_bytes", 0),
    }
