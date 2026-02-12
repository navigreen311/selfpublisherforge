# VF19: Celery Audiobook Generation Tasks

## Task
Create Celery tasks for chapter audio generation.

## Context
- Look at existing Celery setup. Check `backend/app/` for existing task definitions or celery config.
- If no celery app exists yet, check for celery configuration in config.py or a celery.py file.

## Files to Create

### `backend/app/tasks/audiobook_tasks.py`

```python
"""Celery tasks for audiobook chapter audio generation.

All tasks emit WebSocket progress events via Redis pub/sub:
- audiobook:{project_id}:progress — { chapter_id, percent, stage, eta }
- audiobook:{project_id}:complete — { chapter_id, audio_url, duration, cost }
- audiobook:{project_id}:error — { chapter_id, error_message, retry_available }
"""

import json
import logging
import time
from uuid import UUID

logger = logging.getLogger(__name__)

# Import or create Celery app
# Check for existing celery app in the project first
# If backend/app/celery_app.py exists, import from there
# Otherwise create: from celery import Celery; celery_app = Celery('selfpublisherforge')

def _get_celery_app():
    """Get or create the Celery app instance."""
    try:
        from app.celery_app import celery_app
        return celery_app
    except ImportError:
        from celery import Celery
        from app.config import get_settings
        settings = get_settings()
        app = Celery('selfpublisherforge', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
        return app

celery_app = _get_celery_app()

def _publish_event(project_id: str, event_type: str, data: dict):
    """Publish WebSocket event via Redis pub/sub."""
    import redis
    from app.config import get_settings
    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    channel = f"audiobook:{project_id}:events"
    message = json.dumps({"type": event_type, **data})
    r.publish(channel, message)
    r.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_chapter_audio_task(self, job_id: str, chapter_id: str):
    """Generate TTS audio for a single chapter.

    Steps:
    1. Load chapter text from DB
    2. Preprocess text (SSML if available)
    3. Generate TTS via provider
    4. Post-process audio (normalize, noise gate, room tone)
    5. Upload to S3
    6. Update DB records
    7. Emit completion event
    """
    import asyncio
    asyncio.run(_async_generate_chapter(self, job_id, chapter_id))

async def _async_generate_chapter(task, job_id: str, chapter_id: str):
    """Async implementation of chapter generation."""
    from app.database import async_session
    from app.models.audiobook import AudiobookChapter, AudiobookGenerationJob, AudiobookProject
    from app.services.voiceforge.tts_engine import TTSEngine
    from app.services.voiceforge.audio_processor import AudioProcessor
    from sqlalchemy import select

    async with async_session() as db:
        # Load job and chapter
        job = (await db.execute(select(AudiobookGenerationJob).where(AudiobookGenerationJob.id == job_id))).scalar_one()
        chapter = (await db.execute(select(AudiobookChapter).where(AudiobookChapter.id == chapter_id))).scalar_one()
        project = (await db.execute(select(AudiobookProject).where(AudiobookProject.id == chapter.audiobook_project_id))).scalar_one()

        project_id = str(project.id)
        job.status = "processing"
        job.started_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        chapter.status = "generating"
        chapter.generation_attempts += 1
        await db.commit()

        _publish_event(project_id, "chapter_generation_started", {
            "chapter_id": str(chapter.id),
            "chapter_number": chapter.chapter_number,
        })

        try:
            # Step 1: Get text (SSML or plain)
            text = chapter.ssml_text or chapter.source_text

            # Step 2: Generate TTS
            _publish_event(project_id, "chapter_generation_progress", {
                "chapter_id": str(chapter.id), "percent": 20, "stage": "tts_generating", "eta_seconds": 120
            })

            tts = TTSEngine()
            voice_id = str(chapter.voice_id or project.narrator_voice_id)
            # Determine provider from voice record
            from app.models.audiobook import AudiobookVoice
            voice = (await db.execute(select(AudiobookVoice).where(AudiobookVoice.id == voice_id))).scalar_one_or_none()
            provider = voice.provider if voice else "coqui_xtts"

            audio_result = await tts.generate_speech(text, voice_id, provider, chapter.generation_params or {})

            # Step 3: Post-process
            _publish_event(project_id, "chapter_generation_progress", {
                "chapter_id": str(chapter.id), "percent": 60, "stage": "post_processing", "eta_seconds": 60
            })

            processor = AudioProcessor()
            processed = processor.normalize(audio_result.audio_path)
            processed = processor.apply_noise_gate(processed.audio_path)
            processed = processor.add_room_tone(processed.audio_path)
            processed = processor.convert_format(processed.audio_path, target_format=project.output_format or "mp3")

            # Step 4: Upload to S3
            _publish_event(project_id, "chapter_generation_progress", {
                "chapter_id": str(chapter.id), "percent": 85, "stage": "uploading", "eta_seconds": 15
            })
            # TODO: Upload to S3 via storage service
            audio_url = f"s3://{processed.audio_path}"  # placeholder

            # Step 5: Generate waveform data
            waveform = processor.generate_waveform(processed.audio_path)

            # Step 6: Update records
            chapter.status = "review"
            chapter.audio_url = audio_url
            chapter.duration_seconds = processed.duration_seconds
            chapter.file_size_bytes = processed.file_size_bytes
            chapter.waveform_data = {"peaks": waveform.peaks, "duration": waveform.duration_seconds}
            chapter.quality_metrics = {
                "rms_db": processed.rms_db,
                "peak_db": processed.peak_db,
                "noise_floor_db": processed.noise_floor_db,
            }
            chapter.cost_usd = audio_result.cost_usd

            job.status = "completed"
            job.completed_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            job.cost_usd = audio_result.cost_usd
            job.output = {"audio_url": audio_url, "duration": processed.duration_seconds}

            await db.commit()

            _publish_event(project_id, "chapter_generation_complete", {
                "chapter_id": str(chapter.id),
                "audio_url": audio_url,
                "duration_seconds": processed.duration_seconds,
                "cost_usd": float(audio_result.cost_usd),
                "quality_metrics": chapter.quality_metrics,
            })

            await tts.close()

        except Exception as e:
            logger.error("Chapter generation failed: %s", e, exc_info=True)
            chapter.status = "failed"
            job.status = "failed"
            job.error_message = str(e)
            job.retry_count += 1
            await db.commit()

            _publish_event(project_id, "chapter_generation_failed", {
                "chapter_id": str(chapter.id),
                "error": str(e),
                "retry_available": job.retry_count < job.max_retries,
            })

            if job.retry_count < job.max_retries:
                raise task.retry(exc=e)

@celery_app.task(bind=True)
def generate_all_chapters_task(self, project_id: str, parallel: bool = False):
    """Queue generation for all pending chapters in a project."""
    import asyncio
    asyncio.run(_async_generate_all(project_id, parallel))

async def _async_generate_all(project_id: str, parallel: bool):
    from app.database import async_session
    from app.models.audiobook import AudiobookChapter, AudiobookGenerationJob
    from sqlalchemy import select

    async with async_session() as db:
        chapters = (await db.execute(
            select(AudiobookChapter)
            .where(AudiobookChapter.audiobook_project_id == project_id, AudiobookChapter.status == "pending")
            .order_by(AudiobookChapter.chapter_number)
        )).scalars().all()

        for ch in chapters:
            job = AudiobookGenerationJob(
                audiobook_project_id=project_id,
                chapter_id=ch.id,
                job_type="chapter_generate",
                status="queued",
            )
            db.add(job)
            await db.flush()
            generate_chapter_audio_task.delay(str(job.id), str(ch.id))
        await db.commit()
```
