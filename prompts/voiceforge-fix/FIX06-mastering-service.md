# FIX06: Mastering & Validation Service

## Task
Create the service layer for audiobook mastering and ACX validation.

## File to Create: `backend/app/modules/audiobook/service_mastering.py`

### Functions to Implement

```python
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audiobook import AudiobookProject, AudiobookChapter, AudiobookGenerationJob

async def start_mastering(db: AsyncSession, project_id: UUID, org_id: UUID, options: dict) -> dict:
    """Start the mastering pipeline.
    1. Verify project exists and belongs to org
    2. Verify all chapters have audio (status = approved)
    3. Create an AudiobookGenerationJob with job_type='master_merge'
    4. Dispatch Celery task: master_audiobook_task.delay(str(job.id))
    5. Update project status to 'mastering'
    6. Return job info {job_id, status, project_id}
    """

async def get_mastering_status(db: AsyncSession, project_id: UUID, org_id: UUID) -> dict:
    """Get the latest mastering job status.
    - Query AudiobookGenerationJob where project_id and job_type='master_merge'
    - Order by created_at desc, take first
    - Return {job_id, status, started_at, completed_at, output}
    """

async def validate_acx(db: AsyncSession, project_id: UUID, org_id: UUID) -> dict:
    """Run ACX compliance validation.
    1. Load project with chapters
    2. For each chapter with audio_url, use AudioProcessor.validate_acx()
    3. Compile results: {passed: bool, chapters: [{chapter_id, passed, issues: [...]}], summary}
    4. ACX specs: peak <= -3dB, RMS -23 to -18 dB, noise floor < -60dB, 44100Hz, 192kbps MP3, mono
    NOTE: If audio files aren't accessible locally, create a stub that returns mock validation results
    and marks it with a TODO for when storage is configured.
    """
```

### Imports
```python
from app.services.voiceforge.audio_processor import AudioProcessor
from app.tasks.mastering_tasks import master_audiobook_task
```

## Conventions
- Follow existing service.py patterns
- Always verify org_id ownership before operations
- Use Celery tasks for long-running operations
