"""Service layer for audiobook voice management."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audiobook import AudiobookVoice
from app.modules.audiobook.schemas_extended import VoiceCloneRequest

logger = logging.getLogger(__name__)


async def list_voices(
    db: AsyncSession,
    org_id: uuid.UUID,
    provider: str | None = None,
    voice_type: str | None = None,
    gender: str | None = None,
    language: str | None = None,
) -> dict:
    """List available voices: system voices + the org's custom voices."""
    query = select(AudiobookVoice).where(
        AudiobookVoice.active.is_(True),
        AudiobookVoice.deleted_at.is_(None),
        or_(
            AudiobookVoice.is_system_voice.is_(True),
            AudiobookVoice.org_id == org_id,
        ),
    )

    if provider:
        query = query.where(AudiobookVoice.provider == provider)
    if voice_type:
        query = query.where(AudiobookVoice.voice_type == voice_type)
    if gender:
        query = query.where(AudiobookVoice.gender == gender)
    if language:
        query = query.where(AudiobookVoice.language == language)

    query = query.order_by(AudiobookVoice.name)
    result = await db.execute(query)
    items = list(result.scalars().all())
    return {"items": items, "total": len(items)}


async def get_voice(
    db: AsyncSession,
    voice_id: uuid.UUID,
    org_id: uuid.UUID,
) -> AudiobookVoice | None:
    """Get a single voice if it's a system voice or belongs to the org."""
    stmt = select(AudiobookVoice).where(
        AudiobookVoice.id == voice_id,
        AudiobookVoice.active.is_(True),
        AudiobookVoice.deleted_at.is_(None),
        or_(
            AudiobookVoice.is_system_voice.is_(True),
            AudiobookVoice.org_id == org_id,
        ),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def preview_voice(
    db: AsyncSession,
    voice_id: uuid.UUID,
    org_id: uuid.UUID,
    text: str,
) -> dict | None:
    """Generate a preview audio clip for a voice."""
    voice = await get_voice(db, voice_id, org_id)
    if not voice:
        return None

    # If the voice already has a sample, return it for the default text
    if voice.sample_audio_url:
        return {
            "voice_id": voice.id,
            "text": text,
            "audio_url": voice.sample_audio_url,
            "duration_seconds": None,
        }

    # TODO: Integrate with TTS provider to generate on-the-fly preview
    logger.info("On-the-fly voice preview not yet implemented for voice %s", voice_id)
    return {
        "voice_id": voice.id,
        "text": text,
        "audio_url": "",
        "duration_seconds": None,
    }


async def clone_voice(
    db: AsyncSession,
    org_id: uuid.UUID,
    request: VoiceCloneRequest,
) -> AudiobookVoice:
    """Clone a voice from an audio sample and register it as a custom voice."""
    voice = AudiobookVoice(
        org_id=org_id,
        name=request.name,
        provider=request.provider,
        voice_type=request.voice_type,
        gender=request.gender,
        language=request.language,
        clone_source_url=request.clone_source_url,
        voice_settings=request.voice_settings,
        is_system_voice=False,
    )
    db.add(voice)
    await db.flush()
    await db.refresh(voice)
    return voice


async def delete_voice(
    db: AsyncSession,
    voice_id: uuid.UUID,
    org_id: uuid.UUID,
) -> bool:
    """Soft-delete a custom voice. System voices cannot be deleted."""
    stmt = select(AudiobookVoice).where(
        AudiobookVoice.id == voice_id,
        AudiobookVoice.org_id == org_id,
        AudiobookVoice.is_system_voice.is_(False),
        AudiobookVoice.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    voice = result.scalar_one_or_none()
    if not voice:
        return False
    voice.active = False
    voice.deleted_at = datetime.now(UTC)
    await db.flush()
    return True
