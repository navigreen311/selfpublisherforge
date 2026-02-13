# VF20: Celery Mastering & Voice Cloning Tasks

## Task
Create Celery tasks for audiobook mastering, validation, and voice cloning.

## Files to Create

### `backend/app/tasks/mastering_tasks.py`

```python
"""Celery tasks for audiobook mastering, export, and voice cloning."""

import json
import logging
from app.tasks.audiobook_tasks import _get_celery_app, _publish_event

logger = logging.getLogger(__name__)
celery_app = _get_celery_app()

@celery_app.task(bind=True, max_retries=2)
def master_audiobook_task(self, job_id: str, project_id: str):
    """Merge all approved chapters into final audiobook, apply mastering chain."""
    import asyncio
    asyncio.run(_async_master(self, job_id, project_id))

async def _async_master(task, job_id, project_id):
    from app.database import async_session
    from app.models.audiobook import AudiobookProject, AudiobookChapter, AudiobookGenerationJob
    from app.services.voiceforge.audio_processor import AudioProcessor
    from sqlalchemy import select
    from pathlib import Path

    async with async_session() as db:
        job = (await db.execute(select(AudiobookGenerationJob).where(AudiobookGenerationJob.id == job_id))).scalar_one()
        project = (await db.execute(select(AudiobookProject).where(AudiobookProject.id == project_id))).scalar_one()
        chapters = (await db.execute(
            select(AudiobookChapter)
            .where(AudiobookChapter.audiobook_project_id == project_id, AudiobookChapter.status == "approved")
            .order_by(AudiobookChapter.chapter_number)
        )).scalars().all()

        job.status = "processing"
        await db.commit()

        _publish_event(str(project_id), "mastering_progress", {"percent": 10, "stage": "loading_chapters"})

        try:
            processor = AudioProcessor()
            chapter_paths = [Path(ch.audio_url.replace("s3://", "/tmp/")) for ch in chapters]  # TODO: download from S3

            # Apply mastering chain to each chapter
            mastered_paths = []
            for i, path in enumerate(chapter_paths):
                percent = 10 + int(70 * (i / len(chapter_paths)))
                _publish_event(str(project_id), "mastering_progress", {"percent": percent, "stage": f"mastering_chapter_{i+1}"})

                # Full mastering chain from MasterRequest params
                params = job.input_params or {}
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
            _publish_event(str(project_id), "mastering_progress", {"percent": 85, "stage": "merging"})
            merged = processor.merge_chapters(mastered_paths, output_format=project.output_format or "mp3")

            # Generate retail sample
            sample = processor.generate_retail_sample(merged.audio_path, duration_seconds=300)

            # Embed metadata
            metadata = project.metadata_ or {}
            metadata.update({"title": project.title, "genre": "Audiobook"})
            processor.embed_metadata(merged.audio_path, metadata)

            # Upload to S3
            _publish_event(str(project_id), "mastering_progress", {"percent": 95, "stage": "uploading"})
            master_url = f"s3://{merged.audio_path}"  # TODO: actual S3 upload
            sample_url = f"s3://{sample.audio_path}"

            # Update records
            project.status = "complete"
            project.master_audio_url = master_url
            project.cover_audio_url = sample_url
            project.total_duration_seconds = int(merged.duration_seconds)

            job.status = "completed"
            job.output = {"master_url": master_url, "sample_url": sample_url, "duration": merged.duration_seconds}
            await db.commit()

            _publish_event(str(project_id), "mastering_complete", {
                "master_url": master_url,
                "total_duration": merged.duration_seconds,
                "total_cost": float(project.actual_cost or 0),
            })

        except Exception as e:
            logger.error("Mastering failed: %s", e, exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()
            if job.retry_count < job.max_retries:
                raise task.retry(exc=e)

@celery_app.task(bind=True)
def validate_audiobook_task(self, project_id: str):
    """Run ACX/platform validation on all chapter audio files."""
    import asyncio
    asyncio.run(_async_validate(project_id))

async def _async_validate(project_id):
    from app.database import async_session
    from app.models.audiobook import AudiobookChapter
    from app.services.voiceforge.audio_processor import AudioProcessor
    from sqlalchemy import select
    from pathlib import Path

    async with async_session() as db:
        chapters = (await db.execute(
            select(AudiobookChapter).where(AudiobookChapter.audiobook_project_id == project_id)
            .order_by(AudiobookChapter.chapter_number)
        )).scalars().all()

        processor = AudioProcessor()
        all_results = []
        for ch in chapters:
            if ch.audio_url:
                result = processor.validate_acx(Path(ch.audio_url.replace("s3://", "/tmp/")))
                all_results.append({"chapter": ch.chapter_number, "title": ch.chapter_title, "result": result})

        overall_pass = all(r["result"].overall_pass for r in all_results)
        _publish_event(project_id, "validation_complete", {
            "results": {"overall_pass": overall_pass, "chapters": [{"chapter": r["chapter"], "score": r["result"].score, "passed": r["result"].overall_pass} for r in all_results]}
        })

@celery_app.task(bind=True, max_retries=1)
def clone_voice_task(self, org_id: str, name: str, audio_paths: list[str], provider: str):
    """Process voice cloning request."""
    import asyncio
    asyncio.run(_async_clone_voice(org_id, name, audio_paths, provider))

async def _async_clone_voice(org_id, name, audio_paths, provider):
    from app.database import async_session
    from app.services.voiceforge.voice_manager import VoiceManager
    from pathlib import Path

    async with async_session() as db:
        manager = VoiceManager()
        paths = [Path(p) for p in audio_paths]
        await manager.create_clone(db, org_id, name, paths, provider)
        await db.commit()
```
