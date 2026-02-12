"""Service layer for audiobook export & download operations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audiobook.models import (
    Audiobook,
    AudiobookExport,
    ExportFormat,
    ExportStatus,
    TargetPlatform,
)


async def _get_audiobook_for_org(
    db: AsyncSession,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
) -> Audiobook | None:
    """Fetch an audiobook by project_id, scoped to org."""
    stmt = select(Audiobook).where(
        Audiobook.project_id == project_id,
        Audiobook.org_id == org_id,
        Audiobook.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_export(
    db: AsyncSession,
    audiobook_id: uuid.UUID,
    format_: str,
    platform: str,
) -> AudiobookExport:
    """Create a new export job (queued status)."""
    export = AudiobookExport(
        audiobook_id=audiobook_id,
        format=ExportFormat(format_),
        target_platform=TargetPlatform(platform),
        status=ExportStatus.QUEUED,
    )
    db.add(export)
    await db.flush()
    return export


async def list_exports(
    db: AsyncSession,
    audiobook_id: uuid.UUID,
) -> list[AudiobookExport]:
    """List all non-deleted exports for an audiobook."""
    stmt = (
        select(AudiobookExport)
        .where(
            AudiobookExport.audiobook_id == audiobook_id,
            AudiobookExport.deleted_at.is_(None),
        )
        .order_by(AudiobookExport.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_export(
    db: AsyncSession,
    export_id: uuid.UUID,
    audiobook_id: uuid.UUID,
) -> AudiobookExport | None:
    """Get a single export by ID, scoped to its audiobook."""
    stmt = select(AudiobookExport).where(
        AudiobookExport.id == export_id,
        AudiobookExport.audiobook_id == audiobook_id,
        AudiobookExport.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def generate_download_url(
    export: AudiobookExport,
) -> dict:
    """Generate a pre-signed download URL for a completed export.

    In production this would call S3/GCS to create a signed URL.
    For now, returns the stored file_url with an expiry window.
    """
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    filename = f"export_{export.id}.{export.format.value}"
    return {
        "download_url": export.file_url or "",
        "expires_at": expires_at,
        "filename": filename,
        "file_size_bytes": export.file_size_bytes or 0,
    }
