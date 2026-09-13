"""Celery tasks for audiobook mastering, export, and voice cloning.

Handles:
- Full mastering chain (normalize, noise gate, compression, EQ, room tone)
- Chapter merging and retail sample generation
- ACX / platform validation
- Voice cloning requests

Time limit strategy
-------------------
Each task declares explicit ``soft_time_limit`` and ``time_limit`` values
(in seconds) based on expected workload:
  - Quick   (notifications, status updates):   soft=60,   hard=120
  - Medium  (API calls, data sync):            soft=300,  hard=600
  - Long    (bulk imports, report generation):  soft=1800, hard=3600
  - V. Long (full analytics aggregation):       soft=3300, hard=3600
Global defaults in config.py are 3300/3600 but per-task limits take precedence.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from celery.exceptions import SoftTimeLimitExceeded

from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _publish_event(project_id: str, event_type: str, data: dict) -> None:
    """Publish a real-time event via Redis pub/sub for WebSocket consumers."""
    import redis

    from app.config import get_settings

    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    channel = f"audiobook:{project_id}:events"
    message = json.dumps({"type": event_type, **data})
    r.publish(channel, message)
    r.close()


# ---------------------------------------------------------------------------
# Master audiobook
# ---------------------------------------------------------------------------


@celery_app.task(
    name="mastering.master_audiobook",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
)
def master_audiobook_task(self, job_id: str, project_id: str) -> dict:
    """Merge all approved chapters into a final audiobook and apply mastering chain.

    Parameters
    ----------
    job_id : str
        UUID of the ``AudiobookGenerationJob`` tracking this mastering run.
    project_id : str
        UUID of the ``AudiobookProject`` to master.

    Returns
    -------
    dict
        ``{"status": "completed", "master_url": ..., "duration": ...}`` on
        success, or ``{"status": "failed", "error": ...}`` on failure.
    """
    import asyncio

    from sqlalchemy import select

    from app.database import async_session
    from app.models.audiobook import (
        AudiobookChapter,
        AudiobookGenerationJob,
        AudiobookProject,
    )
    from app.services.voiceforge.audio_processor import AudioProcessor

    async def _process():
        async with async_session() as db:
            job = (
                await db.execute(select(AudiobookGenerationJob).where(AudiobookGenerationJob.id == job_id))
            ).scalar_one()
            project = (await db.execute(select(AudiobookProject).where(AudiobookProject.id == project_id))).scalar_one()
            chapters = (
                (
                    await db.execute(
                        select(AudiobookChapter)
                        .where(
                            AudiobookChapter.audiobook_project_id == project_id,
                            AudiobookChapter.status == "approved",
                        )
                        .order_by(AudiobookChapter.chapter_number)
                    )
                )
                .scalars()
                .all()
            )

            job.status = "processing"
            await db.commit()

            _publish_event(
                str(project_id),
                "mastering_progress",
                {"percent": 10, "stage": "loading_chapters"},
            )

            processor = AudioProcessor()
            chapter_paths = [
                Path(
                    ch.audio_url.replace(
                        "s3://",
                        "/tmp/",  # noqa: S108  # stub: pending real S3 download
                    )
                )
                for ch in chapters
            ]

            # Apply mastering chain to each chapter
            params = job.input_params or {}
            mastered_paths: list[Path] = []

            for i, path in enumerate(chapter_paths):
                percent = 10 + int(70 * (i / len(chapter_paths)))
                _publish_event(
                    str(project_id),
                    "mastering_progress",
                    {"percent": percent, "stage": f"mastering_chapter_{i + 1}"},
                )

                if params.get("normalize", True):
                    result = processor.normalize(path, target_rms=params.get("target_rms_db", -20.0))
                    path = result.audio_path
                if params.get("noise_gate", True):
                    result = processor.apply_noise_gate(path)
                    path = result.audio_path
                if params.get("compression", True):
                    result = processor.apply_compression(path)
                    path = result.audio_path
                if params.get("eq", True):
                    result = processor.apply_eq(path)
                    path = result.audio_path
                if params.get("room_tone", True):
                    result = processor.add_room_tone(path)
                    path = result.audio_path

                # Convert to target format
                result = processor.convert_format(path, target_format=project.output_format or "mp3")
                mastered_paths.append(result.audio_path)

            # Merge chapters
            _publish_event(
                str(project_id),
                "mastering_progress",
                {"percent": 85, "stage": "merging"},
            )
            merged = processor.merge_chapters(mastered_paths, output_format=project.output_format or "mp3")

            # Generate retail sample
            sample = processor.generate_retail_sample(merged.audio_path, duration_seconds=300)

            # Embed metadata
            metadata = project.metadata_ or {}
            metadata.update({"title": project.title, "genre": "Audiobook"})
            processor.embed_metadata(merged.audio_path, metadata)

            # Upload to S3
            _publish_event(
                str(project_id),
                "mastering_progress",
                {"percent": 95, "stage": "uploading"},
            )
            master_url = f"s3://{merged.audio_path}"  # TODO: actual S3 upload
            sample_url = f"s3://{sample.audio_path}"

            # Update records
            project.status = "complete"
            project.master_audio_url = master_url
            project.cover_audio_url = sample_url
            project.total_duration_seconds = int(merged.duration_seconds)

            job.status = "completed"
            job.output = {
                "master_url": master_url,
                "sample_url": sample_url,
                "duration": merged.duration_seconds,
            }
            await db.commit()

            _publish_event(
                str(project_id),
                "mastering_complete",
                {
                    "master_url": master_url,
                    "total_duration": merged.duration_seconds,
                    "total_cost": float(project.actual_cost or 0),
                },
            )

            return {
                "status": "completed",
                "master_url": master_url,
                "sample_url": sample_url,
                "duration": merged.duration_seconds,
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_process())
    except SoftTimeLimitExceeded:
        raise
    except Exception as exc:
        logger.error("Mastering failed for project %s: %s", project_id, exc, exc_info=True)
        # Best-effort: mark the job as failed
        try:
            _mark_job_failed(job_id, str(exc))
        except Exception:
            logger.warning("Could not mark job %s as failed", job_id, exc_info=True)
        raise self.retry(exc=exc) from exc
    finally:
        loop.close()


def _mark_job_failed(job_id: str, error_message: str) -> None:
    """Synchronously mark a generation job as failed (best-effort)."""
    import asyncio

    from sqlalchemy import select

    from app.database import async_session
    from app.models.audiobook import AudiobookGenerationJob

    async def _update():
        async with async_session() as db:
            job = (
                await db.execute(select(AudiobookGenerationJob).where(AudiobookGenerationJob.id == job_id))
            ).scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = error_message
                await db.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_update())
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Validate audiobook (ACX compliance)
# ---------------------------------------------------------------------------


@celery_app.task(
    name="mastering.validate_audiobook",
    bind=True,
    max_retries=1,
    default_retry_delay=30,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
)
def validate_audiobook_task(self, project_id: str) -> dict:
    """Run ACX / platform validation on all chapter audio files.

    Parameters
    ----------
    project_id : str
        UUID of the ``AudiobookProject`` whose chapters should be validated.

    Returns
    -------
    dict
        ``{"overall_pass": bool, "chapters": [...]}``
    """
    import asyncio

    from sqlalchemy import select

    from app.database import async_session
    from app.models.audiobook import AudiobookChapter
    from app.services.voiceforge.audio_processor import AudioProcessor

    async def _process():
        async with async_session() as db:
            chapters = (
                (
                    await db.execute(
                        select(AudiobookChapter)
                        .where(AudiobookChapter.audiobook_project_id == project_id)
                        .order_by(AudiobookChapter.chapter_number)
                    )
                )
                .scalars()
                .all()
            )

            processor = AudioProcessor()
            all_results = []

            for ch in chapters:
                if not ch.audio_url:
                    continue
                result = processor.validate_acx(Path(ch.audio_url.replace("s3://", "/tmp/")))  # noqa: S108  # stub: s3:// URL treated as a local path pending real S3 download
                all_results.append(
                    {
                        "chapter": ch.chapter_number,
                        "title": ch.chapter_title,
                        "result": result,
                    }
                )

            overall_pass = all(r["result"].overall_pass for r in all_results)

            _publish_event(
                project_id,
                "validation_complete",
                {
                    "results": {
                        "overall_pass": overall_pass,
                        "chapters": [
                            {
                                "chapter": r["chapter"],
                                "score": r["result"].score,
                                "passed": r["result"].overall_pass,
                            }
                            for r in all_results
                        ],
                    }
                },
            )

            return {
                "overall_pass": overall_pass,
                "chapters": [
                    {
                        "chapter": r["chapter"],
                        "title": r["title"],
                        "score": r["result"].score,
                        "passed": r["result"].overall_pass,
                    }
                    for r in all_results
                ],
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_process())
    except SoftTimeLimitExceeded:
        raise
    except Exception as exc:
        logger.error("Validation failed for project %s: %s", project_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Clone voice
# ---------------------------------------------------------------------------


@celery_app.task(
    name="mastering.clone_voice",
    bind=True,
    max_retries=1,
    default_retry_delay=30,
    acks_late=True,
    soft_time_limit=300,
    time_limit=600,
)
def clone_voice_task(self, org_id: str, name: str, audio_paths: list[str], provider: str) -> dict:
    """Process a voice cloning request.

    Parameters
    ----------
    org_id : str
        Organisation UUID that owns the cloned voice.
    name : str
        Display name for the cloned voice.
    audio_paths : list[str]
        Paths / URLs to the reference audio samples.
    provider : str
        TTS provider to use for cloning (e.g. ``"elevenlabs"``).

    Returns
    -------
    dict
        ``{"status": "completed", "voice_name": ...}`` on success.
    """
    import asyncio

    from app.database import async_session
    from app.services.voiceforge.voice_manager import VoiceManager

    async def _process():
        async with async_session() as db:
            manager = VoiceManager()
            paths = [Path(p) for p in audio_paths]
            voice = await manager.create_clone(db, org_id, name, paths, provider)
            await db.commit()
            return {"status": "completed", "voice_name": name, "voice_id": str(voice.id)}

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_process())
    except SoftTimeLimitExceeded:
        raise
    except Exception as exc:
        logger.error("Voice cloning failed for org %s: %s", org_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    finally:
        loop.close()
