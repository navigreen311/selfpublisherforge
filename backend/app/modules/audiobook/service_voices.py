"""Service layer for voice management — listing, previewing, cloning, and deleting voices."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audiobook import AudiobookVoice

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# List voices
# ---------------------------------------------------------------------------


async def list_voices(
    db: AsyncSession,
    org_id: UUID,
    provider: str | None = None,
    voice_type: str | None = None,
    gender: str | None = None,
    language: str | None = None,
) -> dict:
    """List system voices + org's custom voices with optional filters.

    System voices (``is_system_voice=True``) are visible to all organisations.
    Custom voices are filtered by *org_id* for tenant isolation.
    Only active voices (``active=True``) are returned.

    Returns ``{items: [...], total: int}``.
    """
    query = select(AudiobookVoice).where(
        or_(
            AudiobookVoice.is_system_voice == True,  # noqa: E712
            AudiobookVoice.org_id == org_id,
        ),
        AudiobookVoice.active == True,  # noqa: E712
    )

    if provider is not None:
        query = query.where(AudiobookVoice.provider == provider)
    if voice_type is not None:
        query = query.where(AudiobookVoice.voice_type == voice_type)
    if gender is not None:
        query = query.where(AudiobookVoice.gender == gender)
    if language is not None:
        query = query.where(AudiobookVoice.language == language)

    query = query.order_by(AudiobookVoice.name)
    result = await db.execute(query)
    voices = list(result.scalars().all())

    return {"items": voices, "total": len(voices)}


# ---------------------------------------------------------------------------
# Get single voice
# ---------------------------------------------------------------------------


async def get_voice(
    db: AsyncSession,
    voice_id: UUID,
    org_id: UUID,
) -> AudiobookVoice | None:
    """Get a single voice if it is a system voice or belongs to the org."""
    query = select(AudiobookVoice).where(
        AudiobookVoice.id == voice_id,
        AudiobookVoice.active == True,  # noqa: E712
        or_(
            AudiobookVoice.is_system_voice == True,  # noqa: E712
            AudiobookVoice.org_id == org_id,
        ),
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Preview voice
# ---------------------------------------------------------------------------


async def preview_voice(
    db: AsyncSession,
    voice_id: UUID,
    org_id: UUID,
    text: str,
) -> dict | None:
    """Generate a short audio preview using the voice.

    Looks up the voice config, verifies access, then delegates to
    :class:`TTSEngine` for synthesis.

    Returns ``{voice_id, audio_url, duration_seconds, text}`` or ``None``
    if the voice is not found / not accessible.
    """
    voice = await get_voice(db, voice_id, org_id)
    if not voice:
        return None

    from app.services.voiceforge.tts_engine import TTSEngine

    tts = TTSEngine()
    try:
        audio = await tts.preview_voice(
            sample_text=text,
            voice_id=voice.provider_voice_id or str(voice.id),
            provider=voice.provider,
        )
    finally:
        await tts.close()

    logger.info(
        "Voice preview generated: voice=%s provider=%s duration=%.1fs",
        voice_id,
        voice.provider,
        audio.duration_seconds,
    )

    return {
        "voice_id": voice.id,
        "audio_url": str(audio.audio_path),
        "duration_seconds": audio.duration_seconds,
        "text": text,
    }


# ---------------------------------------------------------------------------
# Clone voice
# ---------------------------------------------------------------------------


async def clone_voice(
    db: AsyncSession,
    org_id: UUID,
    data,
) -> AudiobookVoice:
    """Clone a voice from audio samples.

    Dispatches to :class:`VoiceManager.create_clone` and creates an
    :class:`AudiobookVoice` record with ``provider='custom_clone'`` and
    ``is_system_voice=False``.

    *data* is expected to carry ``name`` (str) and ``audio_samples`` (list[Path]).
    """
    from app.services.voiceforge.voice_manager import VoiceManager

    manager = VoiceManager()
    voice = await manager.create_clone(
        db=db,
        org_id=org_id,
        name=data.name,
        audio_samples=data.audio_samples,
        provider="custom_clone",
    )

    logger.info(
        "Voice cloned: voice=%s org=%s name=%s",
        voice.id,
        org_id,
        data.name,
    )

    return voice


# ---------------------------------------------------------------------------
# Delete voice
# ---------------------------------------------------------------------------


async def delete_voice(
    db: AsyncSession,
    voice_id: UUID,
    org_id: UUID,
) -> bool:
    """Deactivate a custom voice (cannot delete system voices).

    Verifies the voice belongs to *org_id* and is **not** a system voice,
    then sets ``active=False`` (soft deactivate).
    """
    query = select(AudiobookVoice).where(
        AudiobookVoice.id == voice_id,
        AudiobookVoice.org_id == org_id,
        AudiobookVoice.is_system_voice == False,  # noqa: E712
    )
    result = await db.execute(query)
    voice = result.scalar_one_or_none()

    if not voice:
        return False

    voice.active = False
    await db.flush()

    logger.info("Voice deactivated: voice=%s org=%s", voice_id, org_id)
    return True
