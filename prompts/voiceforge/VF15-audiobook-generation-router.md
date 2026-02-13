# VF15: Audiobook Generation Router

## Task
Create endpoints for chapter audio generation, regeneration, and approval.

## Files to Create/Modify

### Add to `backend/app/modules/audiobook/router.py` (or create `router_generation.py`)

```
POST   /api/v1/audiobooks/{id}/chapters/{ch_id}/generate     # Generate audio for single chapter
POST   /api/v1/audiobooks/{id}/generate-all                   # Queue all chapters for generation
GET    /api/v1/audiobooks/{id}/chapters/{ch_id}/audio         # Get chapter audio file
POST   /api/v1/audiobooks/{id}/chapters/{ch_id}/regenerate    # Regenerate chapter audio
PATCH  /api/v1/audiobooks/{id}/chapters/{ch_id}/approve       # Approve chapter audio
POST   /api/v1/audiobooks/{id}/chapters/{ch_id}/segments/{seg}/regenerate  # Regenerate specific segment
```

### Add to `backend/app/modules/audiobook/service.py` (or create `service_generation.py`)

```python
async def generate_chapter_audio(db, project_id, chapter_id, org_id, request) -> dict:
    """Queue chapter audio generation as Celery task."""
    # 1. Validate project and chapter exist, belong to org
    # 2. Update chapter status to 'preprocessing'
    # 3. Create AudiobookGenerationJob record
    # 4. Dispatch Celery task (from app.tasks.audiobook_tasks)
    # 5. Return job info with celery_task_id
    from app.tasks.audiobook_tasks import generate_chapter_audio_task
    job = AudiobookGenerationJob(
        audiobook_project_id=project_id,
        chapter_id=chapter_id,
        job_type="chapter_generate",
        status="queued",
        priority=5,
    )
    db.add(job)
    await db.flush()
    task = generate_chapter_audio_task.delay(str(job.id), str(chapter_id))
    job.celery_task_id = task.id
    await db.flush()
    return job

async def generate_all_chapters(db, project_id, org_id, request) -> dict:
    """Queue all pending chapters for generation."""
    # Get all chapters with status 'pending'
    # Create jobs for each
    # Dispatch tasks (sequential or parallel based on request.parallel)
    ...

async def regenerate_segment(db, project_id, chapter_id, segment_index, org_id, request) -> dict:
    """Regenerate a specific segment (sentence/paragraph) of a chapter."""
    # 1. Get chapter and its SSML/text
    # 2. Identify segment at given index
    # 3. Generate TTS for just that segment
    # 4. Splice new audio into existing chapter audio
    # 5. Update audio_edits JSONB
    ...

async def approve_chapter(db, project_id, chapter_id, org_id, request) -> dict:
    """Approve or request changes for a chapter's audio."""
    # Update chapter status to 'approved' or back to 'review'
    # If approved, increment project.completed_chapters
    ...

async def get_chapter_audio(db, project_id, chapter_id, org_id) -> dict:
    """Get chapter audio URL and metadata."""
    ...
```

## Conventions
- Generation endpoints return the job/task info, not the audio itself (async processing)
- Audio retrieval returns pre-signed S3 URLs
- Use existing Celery patterns from the project
- Import tasks lazily to avoid circular imports
