"""Audiobook mastering & export service -- business logic for mastering, exporting, validation, and cost."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

import boto3
from botocore.config import Config as BotoConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.modules.audiobook.models import (
    Audiobook,
    AudiobookChapter,
    AudiobookExport,
    ChapterStatus,
    ExportFormat,
    ExportStatus,
    MasteringJob,
    MasteringStatus,
    TargetPlatform,
)
from app.modules.audiobook.schemas import (
    ChapterCostItem,
    CostBreakdownResponse,
    DownloadResponse,
    ExportAudiobookRequest,
    ExportResponse,
    MasterAudiobookRequest,
    MasteringJobResponse,
    ValidationResponse,
    ValidationResultItem,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ACX platform audio specifications
# ---------------------------------------------------------------------------
ACX_SPECS = {
    "sample_rate_hz": 44100,
    "bit_depth": 16,
    "channels": 1,  # Mono
    "format": "mp3",
    "bitrate_kbps": 192,
    "peak_db_max": -3.0,
    "noise_floor_db_max": -60.0,
    "lufs_min": -23.0,
    "lufs_max": -18.0,
    "max_duration_seconds": 7200,  # 2 hours per chapter
    "min_duration_seconds": 1,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_audiobook(db: AsyncSession, audiobook_id: UUID, org_id: UUID) -> Audiobook:
    """Fetch an audiobook with org_id permission check."""
    query = select(Audiobook).where(
        Audiobook.id == audiobook_id,
        Audiobook.deleted_at.is_(None),
    )
    result = await db.execute(query)
    audiobook = result.scalar_one_or_none()

    if not audiobook:
        raise AppException(
            status_code=404,
            code="AUDIOBOOK_NOT_FOUND",
            message="Audiobook not found",
        )

    if audiobook.org_id != org_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    return audiobook


async def _get_chapters(db: AsyncSession, audiobook_id: UUID) -> list[AudiobookChapter]:
    """Fetch all non-deleted chapters for an audiobook, ordered by chapter number."""
    query = (
        select(AudiobookChapter)
        .where(
            AudiobookChapter.audiobook_id == audiobook_id,
            AudiobookChapter.deleted_at.is_(None),
        )
        .order_by(AudiobookChapter.chapter_number)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


def _generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a pre-signed S3 URL for downloading a file."""
    settings = get_settings()
    s3_client = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": s3_key},
        ExpiresIn=expires_in,
    )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

async def master_audiobook(
    db: AsyncSession,
    audiobook_id: UUID,
    org_id: UUID,
    request: MasterAudiobookRequest,
) -> MasteringJobResponse:
    """Queue mastering job: merge chapters, apply processing chain, export.

    Steps:
    1. Verify all chapters are approved
    2. Create mastering job record
    3. Dispatch Celery task
    """
    audiobook = await _get_audiobook(db, audiobook_id, org_id)
    chapters = await _get_chapters(db, audiobook_id)

    if not chapters:
        raise AppException(
            status_code=422,
            code="NO_CHAPTERS",
            message="Audiobook has no chapters to master",
        )

    unapproved = [ch for ch in chapters if ch.status != ChapterStatus.APPROVED]
    if unapproved:
        unapproved_nums = [str(ch.chapter_number) for ch in unapproved]
        raise AppException(
            status_code=422,
            code="CHAPTERS_NOT_APPROVED",
            message=f"All chapters must be approved before mastering. "
                    f"Unapproved chapters: {', '.join(unapproved_nums)}",
        )

    processing_settings = {
        "normalize_loudness": request.normalize_loudness,
        "target_lufs": request.target_lufs,
        "noise_reduction": request.noise_reduction,
        "compress_dynamics": request.compress_dynamics,
        "crossfade_ms": request.crossfade_ms,
    }

    mastering_job = MasteringJob(
        audiobook_id=audiobook_id,
        status=MasteringStatus.QUEUED,
        processing_settings=processing_settings,
    )
    db.add(mastering_job)
    await db.flush()

    audiobook.status = "mastering"
    audiobook.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(mastering_job)

    # Dispatch Celery task
    from app.tasks.mastering_tasks import master_audiobook_task

    task = master_audiobook_task.apply_async(
        kwargs={
            "mastering_job_id": str(mastering_job.id),
            "audiobook_id": str(audiobook_id),
            "org_id": str(org_id),
            "chapter_urls": [ch.audio_file_url for ch in chapters],
            "processing_settings": processing_settings,
        },
        queue="file_queue",
    )

    mastering_job.celery_task_id = task.id
    await db.commit()
    await db.refresh(mastering_job)

    logger.info(
        "Queued mastering job %s for audiobook %s (celery task: %s)",
        mastering_job.id, audiobook_id, task.id,
    )

    return MasteringJobResponse(
        id=mastering_job.id,
        audiobook_id=mastering_job.audiobook_id,
        status=mastering_job.status.value,
        celery_task_id=mastering_job.celery_task_id,
        output_file_url=mastering_job.output_file_url,
        processing_settings=mastering_job.processing_settings,
        error_message=mastering_job.error_message,
        duration_seconds=mastering_job.duration_seconds,
        created_at=mastering_job.created_at,
        updated_at=mastering_job.updated_at,
    )


async def export_audiobook(
    db: AsyncSession,
    audiobook_id: UUID,
    org_id: UUID,
    request: ExportAudiobookRequest,
) -> ExportResponse:
    """Export audiobook in target format for specific platform.

    Steps:
    1. Verify master exists
    2. Apply platform-specific formatting (ACX, Findaway, etc.)
    3. Create export record
    4. Queue format conversion if needed
    """
    audiobook = await _get_audiobook(db, audiobook_id, org_id)

    if not audiobook.master_file_url:
        raise AppException(
            status_code=422,
            code="NOT_MASTERED",
            message="Audiobook must be mastered before exporting. "
                    "Run the mastering endpoint first.",
        )

    export_record = AudiobookExport(
        audiobook_id=audiobook_id,
        format=ExportFormat(request.format),
        target_platform=TargetPlatform(request.target_platform),
        status=ExportStatus.QUEUED,
    )
    db.add(export_record)
    await db.flush()

    audiobook.status = "exporting"
    audiobook.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(export_record)

    # Dispatch Celery task for format conversion / packaging
    from app.tasks.mastering_tasks import export_audiobook_task

    task = export_audiobook_task.apply_async(
        kwargs={
            "export_id": str(export_record.id),
            "audiobook_id": str(audiobook_id),
            "org_id": str(org_id),
            "master_file_url": audiobook.master_file_url,
            "format": request.format,
            "target_platform": request.target_platform,
            "bitrate_kbps": request.bitrate_kbps,
            "sample_rate_hz": request.sample_rate_hz,
            "include_metadata": request.include_metadata,
        },
        queue="file_queue",
    )

    export_record.celery_task_id = task.id
    await db.commit()
    await db.refresh(export_record)

    logger.info(
        "Queued export %s for audiobook %s (format: %s, platform: %s, celery task: %s)",
        export_record.id, audiobook_id, request.format, request.target_platform, task.id,
    )

    return ExportResponse(
        id=export_record.id,
        audiobook_id=export_record.audiobook_id,
        format=export_record.format.value,
        target_platform=export_record.target_platform.value,
        status=export_record.status.value,
        file_url=export_record.file_url,
        file_size_bytes=export_record.file_size_bytes,
        celery_task_id=export_record.celery_task_id,
        error_message=export_record.error_message,
        created_at=export_record.created_at,
        updated_at=export_record.updated_at,
    )


async def download_export(
    db: AsyncSession,
    audiobook_id: UUID,
    export_id: UUID,
    org_id: UUID,
) -> DownloadResponse:
    """Get download URL for exported audiobook. Returns a pre-signed S3 URL (1-hour expiry)."""
    audiobook = await _get_audiobook(db, audiobook_id, org_id)

    query = select(AudiobookExport).where(
        AudiobookExport.id == export_id,
        AudiobookExport.audiobook_id == audiobook_id,
        AudiobookExport.deleted_at.is_(None),
    )
    result = await db.execute(query)
    export_record = result.scalar_one_or_none()

    if not export_record:
        raise AppException(
            status_code=404,
            code="EXPORT_NOT_FOUND",
            message="Export not found",
        )

    if export_record.status != ExportStatus.COMPLETED:
        raise AppException(
            status_code=422,
            code="EXPORT_NOT_READY",
            message=f"Export is not ready for download. Current status: {export_record.status.value}",
        )

    if not export_record.file_url:
        raise AppException(
            status_code=422,
            code="EXPORT_FILE_MISSING",
            message="Export file URL is missing",
        )

    # Extract S3 key from the full URL
    settings = get_settings()
    s3_prefix = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/"
    s3_key = export_record.file_url.removeprefix(s3_prefix)

    expires_in = 3600  # 1 hour
    download_url = _generate_presigned_url(s3_key, expires_in=expires_in)

    ext = export_record.format.value
    filename = f"{audiobook.title.replace(' ', '_')}.{ext}"

    logger.info("Generated download URL for export %s (audiobook %s)", export_id, audiobook_id)

    return DownloadResponse(
        export_id=export_record.id,
        download_url=download_url,
        expires_in_seconds=expires_in,
        file_size_bytes=export_record.file_size_bytes,
        format=export_record.format.value,
        filename=filename,
    )


async def validate_audiobook(
    db: AsyncSession,
    audiobook_id: UUID,
    org_id: UUID,
) -> ValidationResponse:
    """Run platform validation on all chapter audio files against ACX specs.

    Validates each chapter's audio parameters against ACX requirements:
    - Sample rate, bit depth, channels
    - Peak levels and noise floor
    - LUFS loudness range
    - Duration limits
    """
    await _get_audiobook(db, audiobook_id, org_id)
    chapters = await _get_chapters(db, audiobook_id)

    if not chapters:
        raise AppException(
            status_code=422,
            code="NO_CHAPTERS",
            message="Audiobook has no chapters to validate",
        )

    results: list[ValidationResultItem] = []
    chapters_passed = 0

    for chapter in chapters:
        errors: list[str] = []
        warnings: list[str] = []

        # Check that audio file exists
        if not chapter.audio_file_url:
            errors.append("No audio file uploaded for this chapter")
            results.append(ValidationResultItem(
                chapter_number=chapter.chapter_number,
                chapter_title=chapter.title,
                passed=False,
                errors=errors,
                warnings=warnings,
            ))
            continue

        # Validate against stored validation results if available
        vr = chapter.validation_results or {}

        sample_rate = vr.get("sample_rate_hz")
        if sample_rate and sample_rate != ACX_SPECS["sample_rate_hz"]:
            errors.append(
                f"Sample rate {sample_rate} Hz does not match required {ACX_SPECS['sample_rate_hz']} Hz"
            )

        bit_depth = vr.get("bit_depth")
        if bit_depth and bit_depth < ACX_SPECS["bit_depth"]:
            errors.append(
                f"Bit depth {bit_depth} is below minimum {ACX_SPECS['bit_depth']}"
            )

        channels = vr.get("channels")
        if channels and channels != ACX_SPECS["channels"]:
            warnings.append(
                f"Audio has {channels} channel(s), ACX requires mono ({ACX_SPECS['channels']} channel)"
            )

        peak_db = vr.get("peak_db")
        if peak_db is not None and peak_db > ACX_SPECS["peak_db_max"]:
            errors.append(
                f"Peak level {peak_db} dB exceeds maximum {ACX_SPECS['peak_db_max']} dB"
            )

        noise_floor_db = vr.get("noise_floor_db")
        if noise_floor_db is not None and noise_floor_db > ACX_SPECS["noise_floor_db_max"]:
            errors.append(
                f"Noise floor {noise_floor_db} dB exceeds maximum {ACX_SPECS['noise_floor_db_max']} dB"
            )

        lufs = vr.get("lufs")
        if lufs is not None:
            if lufs < ACX_SPECS["lufs_min"]:
                errors.append(
                    f"Loudness {lufs} LUFS is below minimum {ACX_SPECS['lufs_min']} LUFS"
                )
            elif lufs > ACX_SPECS["lufs_max"]:
                errors.append(
                    f"Loudness {lufs} LUFS exceeds maximum {ACX_SPECS['lufs_max']} LUFS"
                )

        duration = chapter.duration_seconds
        if duration is not None:
            if duration > ACX_SPECS["max_duration_seconds"]:
                errors.append(
                    f"Chapter duration {duration:.0f}s exceeds maximum {ACX_SPECS['max_duration_seconds']}s"
                )
            if duration < ACX_SPECS["min_duration_seconds"]:
                warnings.append(
                    f"Chapter duration {duration:.1f}s is very short"
                )

        passed = len(errors) == 0
        if passed:
            chapters_passed += 1

        results.append(ValidationResultItem(
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title,
            passed=passed,
            errors=errors,
            warnings=warnings,
            details=vr if vr else None,
        ))

    overall_passed = chapters_passed == len(chapters)

    logger.info(
        "Validation complete for audiobook %s: %d/%d chapters passed",
        audiobook_id, chapters_passed, len(chapters),
    )

    return ValidationResponse(
        audiobook_id=audiobook_id,
        overall_passed=overall_passed,
        total_chapters=len(chapters),
        chapters_passed=chapters_passed,
        chapters_failed=len(chapters) - chapters_passed,
        results=results,
        validated_at=datetime.now(UTC),
    )


async def get_cost_breakdown(
    db: AsyncSession,
    audiobook_id: UUID,
    org_id: UUID,
) -> CostBreakdownResponse:
    """Get detailed cost breakdown for the audiobook project.

    Sums costs from generation jobs, compares providers, and shows per-chapter costs.
    """
    audiobook = await _get_audiobook(db, audiobook_id, org_id)
    chapters = await _get_chapters(db, audiobook_id)

    total_cost = 0.0
    total_duration = 0.0
    cost_by_provider: dict[str, float] = defaultdict(float)
    chapter_items: list[ChapterCostItem] = []

    for chapter in chapters:
        cost = chapter.generation_cost_usd or 0.0
        duration = chapter.duration_seconds or 0.0
        provider = chapter.provider or "unknown"

        total_cost += cost
        total_duration += duration
        cost_by_provider[provider] += cost

        chapter_items.append(ChapterCostItem(
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title,
            provider=chapter.provider,
            duration_seconds=chapter.duration_seconds,
            generation_cost_usd=chapter.generation_cost_usd,
        ))

    return CostBreakdownResponse(
        audiobook_id=audiobook_id,
        title=audiobook.title,
        total_cost_usd=round(total_cost, 6),
        total_chapters=len(chapters),
        total_duration_seconds=round(total_duration, 2),
        chapters=chapter_items,
        cost_by_provider=dict(cost_by_provider),
    )
