# FIX04: Voice Management Service

## Task
Create the service layer for voice management operations.

## File to Create: `backend/app/modules/audiobook/service_voices.py`

### Functions to Implement

```python
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audiobook import AudiobookVoice
from app.services.voiceforge.voice_manager import VoiceManager
from app.services.voiceforge.tts_engine import TTSEngine

async def list_voices(
    db: AsyncSession, org_id: UUID,
    provider: str | None, voice_type: str | None,
    gender: str | None, language: str | None,
) -> dict:
    """List system voices + org's custom voices with optional filters.
    - System voices (is_system_voice=True) visible to all
    - Custom voices filtered by org_id
    - Apply provider/voice_type/gender/language filters
    - Only active voices (active=True)
    - Return {items: [...], total: int}
    """

async def get_voice(db: AsyncSession, voice_id: UUID, org_id: UUID) -> AudiobookVoice | None:
    """Get a single voice if it's a system voice or belongs to the org."""

async def preview_voice(db: AsyncSession, voice_id: UUID, org_id: UUID, text: str) -> dict | None:
    """Generate a short audio preview using the voice.
    - Look up voice config
    - Use TTSEngine to synthesize the preview text
    - Return {voice_id, audio_url, duration_seconds, text}
    """

async def clone_voice(db: AsyncSession, org_id: UUID, data) -> AudiobookVoice:
    """Clone a voice from audio samples.
    - Dispatch to VoiceManager.create_clone()
    - Create AudiobookVoice record with provider='custom_clone'
    - Set is_system_voice=False
    """

async def delete_voice(db: AsyncSession, voice_id: UUID, org_id: UUID) -> bool:
    """Deactivate a custom voice (cannot delete system voices).
    - Verify voice belongs to org and is_system_voice=False
    - Set active=False (soft deactivate)
    """
```

## Conventions
- Follow existing service.py patterns (functional, async)
- Always filter by org_id for tenant isolation
- System voices are read-only
