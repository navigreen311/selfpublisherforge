# FIX07: Export & Download Router

## Task
Create API endpoints for audiobook export and download.

## File to Create: `backend/app/modules/audiobook/router_export.py`

### Endpoints to Implement

```python
router = APIRouter()

# POST /{project_id}/export — Start export in specified format
@router.post("/{project_id}/export", response_model=ExportJobResponse, status_code=202)
async def export_audiobook(
    project_id: UUID,
    body: ExportRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Start audiobook export.
    body contains: format ("mp3", "m4b", "flac", "wav"),
    include_chapters (bool), include_cover (bool),
    platform ("acx", "findaway", "generic")
    Returns job info with export_id.
    """

# GET /{project_id}/exports — List all exports for a project
@router.get("/{project_id}/exports", response_model=ExportListResponse)
async def list_exports(project_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    """List all export jobs for a project."""

# GET /{project_id}/exports/{export_id} — Get export status
@router.get("/{project_id}/exports/{export_id}", response_model=ExportJobResponse)
async def get_export(project_id: UUID, export_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Get specific export job status and download URL if complete."""

# GET /{project_id}/exports/{export_id}/download — Get download URL
@router.get("/{project_id}/exports/{export_id}/download")
async def download_export(project_id: UUID, export_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Get a pre-signed download URL for a completed export.
    Returns {download_url, expires_at, filename, file_size_bytes}
    """
```

### Schemas (from schemas_extended.py)
`ExportRequest`, `ExportJobResponse`, `ExportListResponse`, `DownloadResponse`

Import: `from app.modules.audiobook import service_export`

## Conventions
- Follow existing router.py patterns
- Export is async (returns 202 + job ID)
- Download returns a pre-signed URL, not the file itself
