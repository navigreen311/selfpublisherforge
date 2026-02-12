"""Celery tasks for audiobook chapter audio generation.

Handles:
- Single chapter TTS generation with post-processing
- Batch generation of all pending chapters in a project
- WebSocket progress events via Redis pub/sub

All tasks emit WebSocket progress events via Redis pub/sub:
- audiobook:{project_id}:events — multiplexed channel carrying typed payloads:
    chapter_generation_started  — { chapter_id, chapter_number }
    chapter_generation_progress — { chapter_id, percent, stage, eta_seconds }
    chapter_generation_complete — { chapter_id, audio_url, duration_seconds, cost_usd, quality_metrics }
    chapter_generation_failed   — { chapter_id, error, retry_available }

Time limit strategy
-------------------
- generate_chapter_audio:  soft=600,  hard=900   (TTS + post-processing per chapter)
- generate_all_chapters:   soft=3300, hard=3600   (orchestrator — queues subtasks)
"""

import asyncio
import json
import logging
from datetime import UTC, datetime

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.models.audiobook import (
    AudiobookChapter,
    AudiobookGenerationJob,
    AudiobookProject,
    AudiobookVoice,
)
from app.services.voiceforge.audio_processor import AudioProcessor
from app.services.voiceforge.tts_engine import TTSEngine
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Async helper — matches pattern used in advertising.py, analytics.py, etc.
# ---------------------------------------------------------------------------
def _run_async(coro):
    """Helper to run async code in Celery sync tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Redis pub/sub helper for WebSocket progress events
# ---------------------------------------------------------------------------
def _publish_event(project_id: str, event_type: str, data: dict):
    """Publish a typed WebSocket event via Redis pub/sub.

    All events for a project are multiplexed onto a single channel so the
    WebSocket handler (VF21) can subscribe once and demux by ``type``.
    """
    import redis

    from app.config import get_settings

    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    channel = f"audiobook:{project_id}:events"
    message = json.dumps({"type": event_type, **data})
    r.publish(channel, message)
    r.close()


# ---------------------------------------------------------------------------
# Task: Generate audio for a single chapter
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.audiobook_tasks.generate_chapter_audio",
    bind=True,
    max_retries=3,
    soft_time_limit=600,
    time_limit=900,
)
def generate_chapter_audio(self, job_id: str, chapter_id: str):
    """Generate TTS audio for a single chapter.

    Steps:
    1. Load chapter text from DB
    2. Generate TTS via provider (Coqui XTTS, ElevenLabs, etc.)
    3. Post-process audio (normalize, noise gate, room tone, format convert)
    4. Upload to S3 (placeholder — wired via storage service)
    5. Generate waveform peaks for UI visualisation
    6. Update DB records (chapter + job)
    7. Emit completion event
    """
    logger.info("Starting chapter audio generation (job=%s, chapter=%s)", job_id, chapter_id)
    _run_async(_generate_chapter_async(self, job_id, chapter_id))
    logger.info("Chapter audio generation completed (job=%s, chapter=%s)", job_id, chapter_id)


async def _generate_chapter_async(task, job_id: str, chapter_id: str):
    """Async implementation of single-chapter TTS generation."""
    async with async_session() as db:
        try:
            # Load job, chapter, and project
            job = (
                await db.execute(select(AudiobookGenerationJob).where(AudiobookGenerationJob.id == job_id))
            ).scalar_one()
            chapter = (await db.execute(select(AudiobookChapter).where(AudiobookChapter.id == chapter_id))).scalar_one()
            project = (
                await db.execute(select(AudiobookProject).where(AudiobookProject.id == chapter.audiobook_project_id))
            ).scalar_one()

            project_id = str(project.id)

            # Mark in-progress
            job.status = "processing"
            job.started_at = datetime.now(UTC)
            chapter.status = "generating"
            chapter.generation_attempts += 1
            await db.commit()

            _publish_event(
                project_id,
                "chapter_generation_started",
                {
                    "chapter_id": str(chapter.id),
                    "chapter_number": chapter.chapter_number,
                },
            )

            # ------------------------------------------------------------------
            # Step 1: Resolve text (prefer SSML over plain text)
            # ------------------------------------------------------------------
            text = chapter.ssml_text or chapter.source_text

            # ------------------------------------------------------------------
            # Step 2: Resolve voice and provider
            # ------------------------------------------------------------------
            voice_id = str(chapter.voice_id or project.narrator_voice_id)
            voice = (await db.execute(select(AudiobookVoice).where(AudiobookVoice.id == voice_id))).scalar_one_or_none()
            provider = voice.provider if voice else "coqui_xtts"

            # ------------------------------------------------------------------
            # Step 3: Generate TTS
            # ------------------------------------------------------------------
            _publish_event(
                project_id,
                "chapter_generation_progress",
                {
                    "chapter_id": str(chapter.id),
                    "percent": 20,
                    "stage": "tts_generating",
                    "eta_seconds": 120,
                },
            )

            tts = TTSEngine()
            audio_result = await tts.generate_speech(text, voice_id, provider, chapter.generation_params or {})

            # ------------------------------------------------------------------
            # Step 4: Post-process audio
            # ------------------------------------------------------------------
            _publish_event(
                project_id,
                "chapter_generation_progress",
                {
                    "chapter_id": str(chapter.id),
                    "percent": 60,
                    "stage": "post_processing",
                    "eta_seconds": 60,
                },
            )

            processor = AudioProcessor()
            processed = processor.normalize(audio_result.audio_path)
            processed = processor.apply_noise_gate(processed.audio_path)
            processed = processor.add_room_tone(processed.audio_path)
            processed = processor.convert_format(
                processed.audio_path,
                target_format=project.output_format or "mp3",
            )

            # ------------------------------------------------------------------
            # Step 5: Upload to storage
            # ------------------------------------------------------------------
            _publish_event(
                project_id,
                "chapter_generation_progress",
                {
                    "chapter_id": str(chapter.id),
                    "percent": 85,
                    "stage": "uploading",
                    "eta_seconds": 15,
                },
            )
            # TODO: Upload via StorageService once wired (VF06)
            audio_url = f"s3://{processed.audio_path}"  # placeholder

            # ------------------------------------------------------------------
            # Step 6: Generate waveform data for UI
            # ------------------------------------------------------------------
            waveform = processor.generate_waveform(processed.audio_path)

            # ------------------------------------------------------------------
            # Step 7: Persist results
            # ------------------------------------------------------------------
            chapter.status = "review"
            chapter.audio_url = audio_url
            chapter.duration_seconds = processed.duration_seconds
            chapter.file_size_bytes = processed.file_size_bytes
            chapter.waveform_data = {
                "peaks": waveform.peaks,
                "duration": waveform.duration_seconds,
            }
            chapter.quality_metrics = {
                "rms_db": processed.rms_db,
                "peak_db": processed.peak_db,
                "noise_floor_db": processed.noise_floor_db,
            }
            chapter.cost_usd = audio_result.cost_usd

            job.status = "completed"
            job.completed_at = datetime.now(UTC)
            job.cost_usd = audio_result.cost_usd
            job.output = {
                "audio_url": audio_url,
                "duration": processed.duration_seconds,
            }

            await db.commit()

            _publish_event(
                project_id,
                "chapter_generation_complete",
                {
                    "chapter_id": str(chapter.id),
                    "audio_url": audio_url,
                    "duration_seconds": processed.duration_seconds,
                    "cost_usd": float(audio_result.cost_usd),
                    "quality_metrics": chapter.quality_metrics,
                },
            )

            await tts.close()

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "generate_chapter_audio hit soft time limit (job=%s, chapter=%s)",
                job_id,
                chapter_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error("Chapter generation failed: %s", e, exc_info=True)

            # Update status in a fresh transaction
            try:
                chapter.status = "failed"
                job.status = "failed"
                job.error_message = str(e)
                job.retry_count += 1
                await db.commit()

                _publish_event(
                    project_id,
                    "chapter_generation_failed",
                    {
                        "chapter_id": str(chapter.id),
                        "error": str(e),
                        "retry_available": job.retry_count < job.max_retries,
                    },
                )
            except SQLAlchemyError:
                logger.error(
                    "Failed to update failure status for chapter %s",
                    chapter_id,
                    exc_info=True,
                )

            if job.retry_count < job.max_retries:
                raise task.retry(exc=e) from e


# ---------------------------------------------------------------------------
# Task: Orchestrate generation for all pending chapters in a project
# ---------------------------------------------------------------------------
@celery_app.task(
    name="app.tasks.audiobook_tasks.generate_all_chapters",
    bind=True,
    max_retries=1,
    soft_time_limit=3300,
    time_limit=3600,
)
def generate_all_chapters(self, project_id: str, parallel: bool = False):
    """Queue generation jobs for all pending chapters in a project.

    Creates an ``AudiobookGenerationJob`` per chapter and dispatches
    ``generate_chapter_audio`` subtasks.  When ``parallel=True`` all
    subtasks fire immediately; otherwise they are chained sequentially.
    """
    logger.info("Queuing chapter generation for project %s (parallel=%s)", project_id, parallel)
    _run_async(_generate_all_async(project_id, parallel))
    logger.info("All chapter generation jobs queued for project %s", project_id)


async def _generate_all_async(project_id: str, parallel: bool):
    """Async implementation of batch chapter queuing."""
    async with async_session() as db:
        try:
            chapters = (
                (
                    await db.execute(
                        select(AudiobookChapter)
                        .where(
                            AudiobookChapter.audiobook_project_id == project_id,
                            AudiobookChapter.status == "pending",
                        )
                        .order_by(AudiobookChapter.chapter_number)
                    )
                )
                .scalars()
                .all()
            )

            if not chapters:
                logger.info("No pending chapters found for project %s", project_id)
                return

            _publish_event(
                project_id,
                "batch_generation_started",
                {
                    "total_chapters": len(chapters),
                    "parallel": parallel,
                },
            )

            for ch in chapters:
                job = AudiobookGenerationJob(
                    audiobook_project_id=project_id,
                    chapter_id=ch.id,
                    job_type="chapter_generate",
                    status="queued",
                )
                db.add(job)
                await db.flush()

                generate_chapter_audio.delay(str(job.id), str(ch.id))

            await db.commit()

            logger.info(
                "Queued %d chapter generation jobs for project %s",
                len(chapters),
                project_id,
            )

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning(
                "generate_all_chapters hit soft time limit (project=%s)",
                project_id,
            )
            raise
        except Exception as e:
            await db.rollback()
            logger.error("Batch chapter queuing failed for project %s: %s", project_id, e)
            raise


# ─── Periodic Task Schedule ──────────────────────────────────────────────────
# Beat schedules are registered centrally in app.tasks.scheduler.CELERY_BEAT_SCHEDULE
# Audiobook tasks are event-driven (on-demand), so no beat entries are needed.
