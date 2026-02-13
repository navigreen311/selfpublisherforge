# FIX03: Voice Management Router

## Task
Create API endpoints for managing TTS voices.

## File to Create: `backend/app/modules/audiobook/router_voices.py`

### Endpoints to Implement

```python
router = APIRouter()

# GET /voices — List all available voices (system + org custom)
@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(
    provider: str | None = Query(None, description="Filter by provider"),
    voice_type: str | None = Query(None, description="Filter: narrator, character, custom"),
    gender: str | None = Query(None),
    language: str | None = Query(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    # Returns system voices + org's custom voices
    return await service_voices.list_voices(db, current_user["org_id"], provider, voice_type, gender, language)

# GET /voices/{voice_id} — Get voice details
@router.get("/voices/{voice_id}", response_model=VoiceResponse)
async def get_voice(voice_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    voice = await service_voices.get_voice(db, voice_id, current_user["org_id"])
    if not voice:
        raise HTTPException(404, "Voice not found")
    return voice

# GET /voices/{voice_id}/preview — Get preview audio URL
@router.get("/voices/{voice_id}/preview")
async def preview_voice(
    voice_id: UUID,
    text: str = Query("The quick brown fox jumps over the lazy dog.", max_length=500),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await service_voices.preview_voice(db, voice_id, current_user["org_id"], text)
    if not result:
        raise HTTPException(404, "Voice not found")
    return result

# POST /voices/clone — Clone a voice from audio samples
@router.post("/voices/clone", response_model=VoiceResponse, status_code=201)
async def clone_voice(body: VoiceCloneRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    return await service_voices.clone_voice(db, current_user["org_id"], body)

# DELETE /voices/{voice_id} — Deactivate a custom voice
@router.delete("/voices/{voice_id}", status_code=204)
async def delete_voice(voice_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    deleted = await service_voices.delete_voice(db, voice_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(404, "Voice not found or is a system voice")
```

### Schemas (from schemas_extended.py)
`VoiceResponse`, `VoiceListResponse`, `VoiceCloneRequest`, `VoicePreviewResponse`

Import: `from app.modules.audiobook import service_voices`

## Conventions
- Follow existing router.py patterns exactly
- System voices cannot be deleted (only custom/cloned voices)
