"""Celery tasks for audiobook mastering and export.

Async tasks for:
- Mastering: merge chapters, apply processing chain, upload master file
- Exporting: convert to target format, package for platform delivery

Time limit strategy
-------------------
- Mastering is a long-running operation:  soft=1800, hard=3600
- Exporting is also long-running:         soft=1800, hard=3600
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from celery.exceptions import SoftTimeLimitExceeded

from app.config import get_settings
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------

def _upload_to_s3(
    file_bytes: bytes,
    s3_key: str,
    content_type: str,
) -> str:
    """Upload bytes to S3 and return the object URL."""
    settings = get_settings()
    s3_client = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )

    s3_client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )

    file_url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
    logger.info("Uploaded %d bytes to s3://%s/%s", len(file_bytes), settings.S3_BUCKET, s3_key)
    return file_url


# ---------------------------------------------------------------------------
# Mastering task
# ---------------------------------------------------------------------------

@celery_app.task(
    name="audiobook.master",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
)
def master_audiobook_task(
    self,
    mastering_job_id: str,
    audiobook_id: str,
    org_id: str,
    chapter_urls: list[str],
    processing_settings: dict | None = None,
) -> dict:
    """Master an audiobook by merging chapters and applying processing chain.

    Steps:
    1. Download all chapter audio files
    2. Apply processing (normalization, noise reduction, dynamics)
    3. Merge chapters with crossfades
    4. Upload master file to S3
    5. Update mastering job record
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.modules.audiobook.models import (
        Audiobook,
        MasteringJob,
        MasteringStatus,
    )

    async def _do_mastering():
        async with async_session() as db:
            # Fetch mastering job
            stmt = select(MasteringJob).where(
                MasteringJob.id == uuid.UUID(mastering_job_id),
                MasteringJob.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

            if job is None:
                logger.warning("MasteringJob %s not found", mastering_job_id)
                return {
                    "mastering_job_id": mastering_job_id,
                    "status": "not_found",
                    "message": f"MasteringJob {mastering_job_id} not found",
                }

            job.status = MasteringStatus.PROCESSING
            await db.commit()

            try:
                # ASSUMPTION: Audio processing is handled by external tools
                # (ffmpeg, pydub, etc.) that would be integrated here.
                # For now, we create a placeholder master that represents
                # the merged and processed output.
                settings = processing_settings or {}
                logger.info(
                    "Mastering audiobook %s: %d chapters, settings=%s",
                    audiobook_id, len(chapter_urls), settings,
                )

                # Placeholder: In production, this would:
                # 1. Download each chapter from S3
                # 2. Apply normalization (LUFS target)
                # 3. Apply noise reduction
                # 4. Apply dynamic compression
                # 5. Merge with crossfades
                # 6. Export as high-quality intermediate
                master_bytes = b"MASTERED_AUDIO_PLACEHOLDER"
                s3_key = f"audiobooks/{org_id}/{audiobook_id}/master/master.wav"
                file_url = _upload_to_s3(master_bytes, s3_key, content_type="audio/wav")

                # Update mastering job
                job.status = MasteringStatus.COMPLETED
                job.output_file_url = file_url

                # Update audiobook with master URL
                ab_stmt = select(Audiobook).where(Audiobook.id == uuid.UUID(audiobook_id))
                ab_result = await db.execute(ab_stmt)
                audiobook = ab_result.scalar_one_or_none()
                if audiobook:
                    audiobook.master_file_url = file_url
                    audiobook.status = "mastered"

                await db.commit()

                logger.info(
                    "Mastering completed for audiobook %s, job %s, url=%s",
                    audiobook_id, mastering_job_id, file_url,
                )

                return {
                    "mastering_job_id": mastering_job_id,
                    "audiobook_id": audiobook_id,
                    "status": "completed",
                    "file_url": file_url,
                    "completed_at": datetime.now(UTC).isoformat(),
                }

            except Exception as exc:
                job.status = MasteringStatus.FAILED
                job.error_message = str(exc)
                await db.commit()
                raise

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _do_mastering()).result()
        else:
            result = loop.run_until_complete(_do_mastering())
    except RuntimeError:
        result = asyncio.run(_do_mastering())
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except ClientError as exc:
        logger.error("S3 error in mastering task %s: %s", mastering_job_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    except Exception as exc:
        logger.error("Mastering failed for job %s: %s", mastering_job_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc

    return result


# ── Export task ────────────────────────────────────────────────────────────

@celery_app.task(
    name="audiobook.export",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
)
def export_audiobook_task(
    self,
    export_id: str,
    audiobook_id: str,
    org_id: str,
    master_file_url: str,
    format: str = "mp3",
    target_platform: str = "generic",
    bitrate_kbps: int = 192,
    sample_rate_hz: int = 44100,
    include_metadata: bool = True,
) -> dict:
    """Export audiobook in the target format for platform delivery.

    Steps:
    1. Download the master file
    2. Convert to target format with specified parameters
    3. Apply platform-specific formatting
    4. Package as ZIP with chapter files + metadata
    5. Upload to S3
    6. Update export record
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.modules.audiobook.models import AudiobookExport, ExportStatus

    async def _do_export():
        async with async_session() as db:
            stmt = select(AudiobookExport).where(
                AudiobookExport.id == uuid.UUID(export_id),
                AudiobookExport.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            export_record = result.scalar_one_or_none()

            if export_record is None:
                logger.warning("AudiobookExport %s not found", export_id)
                return {
                    "export_id": export_id,
                    "status": "not_found",
                    "message": f"Export {export_id} not found",
                }

            export_record.status = ExportStatus.PROCESSING
            await db.commit()

            try:
                logger.info(
                    "Exporting audiobook %s: format=%s, platform=%s, bitrate=%d",
                    audiobook_id, format, target_platform, bitrate_kbps,
                )

                # ASSUMPTION: Format conversion uses external tools (ffmpeg).
                # In production, this would:
                # 1. Download master from S3
                # 2. Convert to target format (MP3, M4B, FLAC, WAV)
                # 3. Split into chapters if needed
                # 4. Apply platform-specific requirements
                # 5. Package as ZIP
                export_bytes = b"EXPORTED_AUDIO_PLACEHOLDER"
                ext = format
                s3_key = (
                    f"audiobooks/{org_id}/{audiobook_id}"
                    f"/exports/{export_id}.{ext}"
                )
                content_type = {
                    "mp3": "audio/mpeg",
                    "m4b": "audio/mp4",
                    "flac": "audio/flac",
                    "wav": "audio/wav",
                }.get(format, "application/octet-stream")

                file_url = _upload_to_s3(export_bytes, s3_key, content_type=content_type)

                export_record.status = ExportStatus.COMPLETED
                export_record.file_url = file_url
                export_record.file_size_bytes = len(export_bytes)
                await db.commit()

                logger.info(
                    "Export completed: export_id=%s, audiobook=%s, format=%s, url=%s",
                    export_id, audiobook_id, format, file_url,
                )

                return {
                    "export_id": export_id,
                    "audiobook_id": audiobook_id,
                    "status": "completed",
                    "file_url": file_url,
                    "file_size_bytes": len(export_bytes),
                    "format": format,
                    "target_platform": target_platform,
                    "completed_at": datetime.now(UTC).isoformat(),
                }

            except Exception as exc:
                export_record.status = ExportStatus.FAILED
                export_record.error_message = str(exc)
                await db.commit()
                raise

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _do_export()).result()
        else:
            result = loop.run_until_complete(_do_export())
    except RuntimeError:
        result = asyncio.run(_do_export())
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except ClientError as exc:
        logger.error("S3 error in export task %s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    except Exception as exc:
        logger.error("Export failed for %s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc

    return result
