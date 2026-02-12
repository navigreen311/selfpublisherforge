# FIX05: Mastering & Validation Router

## Task
Create API endpoints for audiobook mastering and ACX validation.

## File to Create: `backend/app/modules/audiobook/router_mastering.py`

### Endpoints to Implement

```python
router = APIRouter()

# POST /{project_id}/master — Start mastering pipeline
@router.post("/{project_id}/master", response_model=MasteringJobResponse, status_code=202)
async def master_audiobook(
    project_id: UUID,
    body: MasterRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Start the mastering pipeline for the audiobook.
    body contains: target_lufs (-20 default), normalize (bool), noise_gate (bool),
    output_format ("mp3"), sample_rate (44100), bit_rate (192)
    Dispatches a Celery task and returns the job info.
    """

# GET /{project_id}/master/status — Get mastering status
@router.get("/{project_id}/master/status", response_model=MasteringStatusResponse)
async def get_mastering_status(project_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Get current mastering job status for a project."""

# POST /{project_id}/validate — Run ACX validation
@router.post("/{project_id}/validate", response_model=ACXValidationResponse, status_code=200)
async def validate_audiobook(project_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Run ACX compliance validation on the project's audio.
    Returns pass/fail for each chapter + overall result.
    Checks: peak level <= -3dB, RMS -23 to -18 dB, noise floor < -60dB,
    sample rate 44100Hz, MP3 CBR 192kbps, mono channel.
    """
```

### Schemas (from schemas_extended.py)
`MasterRequest`, `MasteringJobResponse`, `MasteringStatusResponse`, `ACXValidationResponse`, `ACXChapterResult`

Import: `from app.modules.audiobook import service_mastering`

## Conventions
- Follow existing router.py patterns
- Mastering is async (returns 202 + job ID)
- Validation can be synchronous (runs checks and returns)
