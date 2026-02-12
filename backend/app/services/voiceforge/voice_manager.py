"""
Voice Manager — handles voice catalog, custom cloning, and character voice assignment.

Features:
- System voice library: pre-configured voices across providers (20+ built-in voices)
- Custom voice cloning: upload 3-5 min of audio → create clone via ElevenLabs or Coqui XTTS
- Character voice mapping: assign different voices to dialogue (fiction books)
- Voice preview: generate 10-second sample of any voice reading user-provided text
- Voice consistency: ensure same voice settings across all chapters
"""

import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.audiobook import AudiobookVoice

logger = logging.getLogger(__name__)

# System voice catalog — built-in voices available to all users
SYSTEM_VOICES = [
    {"name": "Marcus (Narrator)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "male", "age_range": "middle_aged", "accent": "american", "language": "en", "quality_score": 82.0, "cost_per_minute": 0.001},
    {"name": "Elena (Narrator)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "female", "age_range": "young_adult", "accent": "american", "language": "en", "quality_score": 85.0, "cost_per_minute": 0.001},
    {"name": "James (British)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "male", "age_range": "middle_aged", "accent": "british", "language": "en", "quality_score": 80.0, "cost_per_minute": 0.001},
    {"name": "Sophie (British)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "female", "age_range": "young_adult", "accent": "british", "language": "en", "quality_score": 83.0, "cost_per_minute": 0.001},
    {"name": "David (Premium)", "provider": "elevenlabs", "voice_type": "narrator", "gender": "male", "age_range": "middle_aged", "accent": "american", "language": "en", "quality_score": 95.0, "cost_per_minute": 0.03},
    {"name": "Rachel (Premium)", "provider": "elevenlabs", "voice_type": "narrator", "gender": "female", "age_range": "young_adult", "accent": "american", "language": "en", "quality_score": 96.0, "cost_per_minute": 0.03},
    {"name": "Arthur (Premium British)", "provider": "elevenlabs", "voice_type": "narrator", "gender": "male", "age_range": "elderly", "accent": "british", "language": "en", "quality_score": 94.0, "cost_per_minute": 0.03},
    {"name": "Isabella (Premium British)", "provider": "elevenlabs", "voice_type": "narrator", "gender": "female", "age_range": "middle_aged", "accent": "british", "language": "en", "quality_score": 93.0, "cost_per_minute": 0.03},
    {"name": "Carlos (Spanish Accent)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "male", "age_range": "young_adult", "accent": "spanish", "language": "en", "quality_score": 78.0, "cost_per_minute": 0.001},
    {"name": "Anika (Indian Accent)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "female", "age_range": "young_adult", "accent": "indian", "language": "en", "quality_score": 77.0, "cost_per_minute": 0.001},
    {"name": "Chen Wei (Mandarin)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "male", "age_range": "middle_aged", "accent": "chinese", "language": "zh", "quality_score": 76.0, "cost_per_minute": 0.001},
    {"name": "Yuki (Japanese)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "female", "age_range": "young_adult", "accent": "japanese", "language": "ja", "quality_score": 75.0, "cost_per_minute": 0.001},
    {"name": "Hans (German)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "male", "age_range": "middle_aged", "accent": "german", "language": "de", "quality_score": 79.0, "cost_per_minute": 0.001},
    {"name": "Marie (French)", "provider": "coqui_xtts", "voice_type": "narrator", "gender": "female", "age_range": "young_adult", "accent": "french", "language": "fr", "quality_score": 80.0, "cost_per_minute": 0.001},
    {"name": "Old Sage", "provider": "coqui_xtts", "voice_type": "character", "gender": "male", "age_range": "elderly", "accent": "british", "language": "en", "quality_score": 74.0, "cost_per_minute": 0.001},
    {"name": "Young Hero", "provider": "coqui_xtts", "voice_type": "character", "gender": "male", "age_range": "young_adult", "accent": "american", "language": "en", "quality_score": 76.0, "cost_per_minute": 0.001},
    {"name": "Villainess", "provider": "coqui_xtts", "voice_type": "character", "gender": "female", "age_range": "middle_aged", "accent": "british", "language": "en", "quality_score": 75.0, "cost_per_minute": 0.001},
    {"name": "Child Voice", "provider": "coqui_xtts", "voice_type": "character", "gender": "neutral", "age_range": "child", "accent": "american", "language": "en", "quality_score": 70.0, "cost_per_minute": 0.001},
    {"name": "Deep Narrator", "provider": "elevenlabs", "voice_type": "narrator", "gender": "male", "age_range": "elderly", "accent": "american", "language": "en", "quality_score": 92.0, "cost_per_minute": 0.03},
    {"name": "Warm Storyteller", "provider": "elevenlabs", "voice_type": "narrator", "gender": "female", "age_range": "middle_aged", "accent": "american", "language": "en", "quality_score": 91.0, "cost_per_minute": 0.03},
    {"name": "Quick Preview", "provider": "piper", "voice_type": "narrator", "gender": "neutral", "age_range": "middle_aged", "accent": "american", "language": "en", "quality_score": 65.0, "cost_per_minute": 0.0001},
]


class VoiceManager:
    def __init__(self):
        self.settings = get_settings()

    async def get_system_voices(self, db: AsyncSession) -> list[AudiobookVoice]:
        """Return built-in system voices. Seed them if not present."""
        result = await db.execute(
            select(AudiobookVoice).where(AudiobookVoice.is_system_voice == True)  # noqa: E712
        )
        voices = result.scalars().all()
        if not voices:
            voices = await self._seed_system_voices(db)
        return voices

    async def get_org_voices(
        self, db: AsyncSession, org_id: uuid.UUID
    ) -> list[AudiobookVoice]:
        """Return org-specific custom voices + system voices."""
        result = await db.execute(
            select(AudiobookVoice)
            .where(
                (AudiobookVoice.org_id == org_id)
                | (AudiobookVoice.is_system_voice == True)  # noqa: E712
            )
            .where(AudiobookVoice.active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def create_clone(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        name: str,
        audio_samples: list[Path],
        provider: str = "coqui_xtts",
    ) -> AudiobookVoice:
        """Create a cloned voice from audio samples."""
        # Lazy import to avoid circular imports
        from app.services.voiceforge.tts_engine import TTSEngine

        tts = TTSEngine()

        # Validate audio samples
        total_seconds = sum(self._get_duration(p) for p in audio_samples)
        if total_seconds < self.settings.VOICE_CLONE_MIN_AUDIO_SECONDS:
            raise ValueError(
                f"Need at least {self.settings.VOICE_CLONE_MIN_AUDIO_SECONDS}s of audio, "
                f"got {total_seconds:.0f}s"
            )

        # Clone via provider
        clone_result = await tts.clone_voice(audio_samples, name, provider)

        voice = AudiobookVoice(
            org_id=org_id,
            name=name,
            provider=provider,
            provider_voice_id=clone_result.get("voice_id"),
            voice_type="custom",
            clone_source_url=clone_result.get("source_url"),
            voice_settings=clone_result.get("settings", {}),
            is_system_voice=False,
            active=True,
        )
        db.add(voice)
        await db.flush()
        return voice

    async def delete_clone(
        self, db: AsyncSession, voice_id: uuid.UUID, org_id: uuid.UUID
    ) -> bool:
        """Soft-delete a custom voice."""
        result = await db.execute(
            select(AudiobookVoice).where(
                AudiobookVoice.id == voice_id,
                AudiobookVoice.org_id == org_id,
                AudiobookVoice.is_system_voice == False,  # noqa: E712
            )
        )
        voice = result.scalar_one_or_none()
        if not voice:
            return False
        voice.active = False
        await db.flush()
        return True

    async def preview_voice(
        self, db: AsyncSession, voice_id: uuid.UUID, sample_text: str
    ) -> dict:
        """Generate a short preview of a voice."""
        # Lazy import to avoid circular imports
        from app.services.voiceforge.tts_engine import TTSEngine

        result = await db.execute(
            select(AudiobookVoice).where(AudiobookVoice.id == voice_id)
        )
        voice = result.scalar_one_or_none()
        if not voice:
            raise ValueError(f"Voice {voice_id} not found")

        tts = TTSEngine()
        audio = await tts.preview_voice(
            sample_text[:200],
            voice.provider_voice_id or str(voice.id),
            voice.provider,
        )
        return {
            "audio_url": str(audio.audio_path),
            "duration_seconds": audio.duration_seconds,
        }

    async def detect_characters(self, chapter_text: str) -> list[dict]:
        """AI-powered dialogue detection — identify character names in dialogue."""
        # Lazy import to avoid circular imports
        from app.services.voiceforge.ssml_generator import SSMLGenerator

        gen = SSMLGenerator()
        segments = await gen.detect_dialogue(chapter_text)
        characters: dict[str, int] = {}
        for seg in segments:
            if seg.get("character") and seg["character"] != "narrator":
                characters[seg["character"]] = characters.get(seg["character"], 0) + 1
        return [
            {"name": name, "dialogue_count": count}
            for name, count in sorted(characters.items(), key=lambda x: -x[1])
        ]

    async def _seed_system_voices(self, db: AsyncSession) -> list[AudiobookVoice]:
        """Seed system voices into database."""
        voices = []
        for v in SYSTEM_VOICES:
            voice = AudiobookVoice(
                org_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # system org
                is_system_voice=True,
                active=True,
                **v,
            )
            db.add(voice)
            voices.append(voice)
        await db.flush()
        return voices

    def _get_duration(self, audio_path: Path) -> float:
        """Get audio file duration in seconds."""
        try:
            import soundfile as sf

            data, rate = sf.read(str(audio_path))
            return len(data) / rate
        except Exception:
            return 0.0
