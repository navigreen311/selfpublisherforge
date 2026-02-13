# VF16: Audiobook Mastering & Export Router

## Task
Create endpoints for mastering, export, validation, and download.

## Files to Create/Modify

### Add to `backend/app/modules/audiobook/router.py` (or `router_export.py`)

```
POST   /api/v1/audiobooks/{id}/master                       # Merge all chapters, apply mastering
POST   /api/v1/audiobooks/{id}/export                       # Export in target format
GET    /api/v1/audiobooks/{id}/export/{export_id}/download   # Download final file
POST   /api/v1/audiobooks/{id}/validate                     # Validate against platform specs
GET    /api/v1/audiobooks/{id}/cost                          # Get cost breakdown
```

### Add to service layer

```python
async def master_audiobook(db, project_id, org_id, request) -> dict:
    """Queue mastering job: merge chapters, apply processing chain, export."""
    # 1. Verify all chapters are approved
    # 2. Create mastering job
    # 3. Dispatch Celery task
    from app.tasks.mastering_tasks import master_audiobook_task
    ...

async def export_audiobook(db, project_id, org_id, request) -> dict:
    """Export audiobook in target format for specific platform."""
    # 1. Verify master exists
    # 2. Apply platform-specific formatting (ACX, Findaway, etc.)
    # 3. Create export record
    # 4. Queue format conversion if needed
    ...

async def download_export(db, project_id, export_id, org_id) -> dict:
    """Get download URL for exported audiobook."""
    # Return pre-signed S3 URL
    ...

async def validate_audiobook(db, project_id, org_id) -> dict:
    """Run platform validation on all chapter audio files."""
    from app.services.voiceforge.audio_processor import AudioProcessor
    processor = AudioProcessor()
    # Validate each chapter audio against ACX specs
    # Return aggregate results
    ...

async def get_cost_breakdown(db, project_id, org_id) -> dict:
    """Get detailed cost breakdown for the audiobook project."""
    # Sum costs from generation jobs
    # Compare providers
    # Show per-chapter costs
    ...
```

## Conventions
- Mastering is a long-running operation → dispatch as Celery task
- Export creates downloadable ZIP with chapter MP3s + metadata
- Validation uses AudioProcessor.validate_acx()
- Downloads use pre-signed S3 URLs (expire in 1 hour)
