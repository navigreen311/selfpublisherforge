# FIX08: Export & Download Service

## Task
Create the service layer for audiobook export and download operations.

## File to Create: `backend/app/modules/audiobook/service_export.py`

### Functions to Implement

```python
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

async def start_export(db: AsyncSession, project_id: UUID, org_id: UUID, options: dict) -> dict:
    """Start audiobook export.
    1. Verify project exists, belongs to org, and has completed mastering
    2. Create AudiobookGenerationJob with job_type='format_convert'
    3. Store export options in input_params (format, platform, etc.)
    4. TODO: Dispatch Celery task for conversion
    5. Return {export_id, status, format, created_at}
    """

async def list_exports(db: AsyncSession, project_id: UUID, org_id: UUID) -> dict:
    """List all export jobs for a project.
    - Query AudiobookGenerationJob where job_type='format_convert' and project_id
    - Return {items: [...], total: int}
    """

async def get_export(db: AsyncSession, project_id: UUID, export_id: UUID, org_id: UUID) -> dict | None:
    """Get a specific export job status."""

async def get_download_url(db: AsyncSession, project_id: UUID, export_id: UUID, org_id: UUID) -> dict | None:
    """Get download URL for a completed export.
    - Verify export is completed
    - Generate pre-signed S3 URL (or local file URL for dev)
    - Return {download_url, expires_at, filename, file_size_bytes}
    - For now, return the output.audio_url from the job if available
    """
```

## Conventions
- Follow existing service.py patterns
- Verify org_id ownership in all operations
- Use AudiobookGenerationJob to track export jobs
