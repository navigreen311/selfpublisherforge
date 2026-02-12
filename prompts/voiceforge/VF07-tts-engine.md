# VF07: TTS Engine Service

## Task
Create the core Text-to-Speech engine service with multi-provider support.

## Files to Create

### `backend/app/services/voiceforge/__init__.py`
```python
"""VoiceForge AI integration services — TTS, ASR, audio processing."""
```

### `backend/app/services/voiceforge/tts_engine.py`

Multi-provider TTS engine with intelligent routing:

**Providers:**
- Coqui XTTS v2: Self-hosted, cost-effective (~$0.001/min). Use for drafts, previews, budget-tier audiobooks.
- Piper: Ultra-fast, lowest cost. Use for quick previews.
- ElevenLabs: Premium cloud API (~$0.03/min), highest quality. Use for final production, premium tier, voice cloning.

**TTSEngine class:**

```python
import httpx
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from app.config import get_settings

@dataclass
class AudioResult:
    audio_path: Path
    duration_seconds: float
    sample_rate: int
    file_size_bytes: int
    provider: str
    cost_usd: float

@dataclass
class CostEstimate:
    provider: str
    estimated_duration_minutes: float
    cost_per_minute: float
    total_cost: float
    word_count: int

class TTSEngine:
    """Core TTS engine with provider abstraction."""

    WORDS_PER_MINUTE = 150  # average narration speed

    def __init__(self):
        self.settings = get_settings()
        self._http_client = httpx.AsyncClient(timeout=300.0)

    async def generate_speech(self, text: str, voice_id: str, provider: str, params: dict | None = None) -> AudioResult:
        """Generate speech audio from text using specified provider."""
        # Route to appropriate provider
        if provider == "coqui_xtts":
            return await self._generate_coqui(text, voice_id, params or {})
        elif provider == "elevenlabs":
            return await self._generate_elevenlabs(text, voice_id, params or {})
        elif provider == "piper":
            return await self._generate_piper(text, voice_id, params or {})
        raise ValueError(f"Unknown TTS provider: {provider}")

    async def generate_chapter(self, chapter_text: str, voice_config: dict, project_config: dict) -> AudioResult:
        """Generate audio for an entire chapter with sentence-level processing."""
        # Split text into sentences/paragraphs
        # Generate each segment
        # Concatenate with appropriate pauses
        # Return combined audio
        ...

    async def preview_voice(self, sample_text: str, voice_id: str, provider: str) -> AudioResult:
        """Quick voice preview — 10-second max sample."""
        # Use fastest available method
        # Limit text to ~25 words
        ...

    async def clone_voice(self, audio_samples: list[Path], voice_name: str, provider: str) -> dict:
        """Create a cloned voice from audio samples."""
        if provider == "elevenlabs":
            return await self._clone_elevenlabs(audio_samples, voice_name)
        elif provider == "coqui_xtts":
            return await self._clone_coqui(audio_samples, voice_name)
        raise ValueError(f"Voice cloning not supported for provider: {provider}")

    def estimate_cost(self, text: str, provider: str) -> CostEstimate:
        """Estimate generation cost based on text length and provider."""
        word_count = len(text.split())
        duration_minutes = word_count / self.WORDS_PER_MINUTE
        rates = {"coqui_xtts": 0.001, "piper": 0.0001, "elevenlabs": 0.03}
        rate = rates.get(provider, 0.01)
        return CostEstimate(
            provider=provider,
            estimated_duration_minutes=duration_minutes,
            cost_per_minute=rate,
            total_cost=duration_minutes * rate,
            word_count=word_count,
        )

    async def _generate_coqui(self, text: str, voice_id: str, params: dict) -> AudioResult:
        """Generate via self-hosted Coqui XTTS server."""
        endpoint = self.settings.COQUI_XTTS_ENDPOINT
        # POST to /tts_to_audio/ with text, speaker_wav, language
        # Save response audio to temp file
        # Return AudioResult
        ...

    async def _generate_elevenlabs(self, text: str, voice_id: str, params: dict) -> AudioResult:
        """Generate via ElevenLabs API."""
        # POST to https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
        # With model_id, voice_settings (stability, similarity_boost, style)
        # Save response audio to temp file
        ...

    async def _generate_piper(self, text: str, voice_id: str, params: dict) -> AudioResult:
        """Generate via self-hosted Piper TTS."""
        endpoint = self.settings.PIPER_ENDPOINT
        # POST text, get WAV back
        ...

    async def _clone_elevenlabs(self, audio_samples: list[Path], name: str) -> dict:
        """Clone voice via ElevenLabs API."""
        # POST to /v1/voices/add with files and name
        ...

    async def _clone_coqui(self, audio_samples: list[Path], name: str) -> dict:
        """Clone voice via Coqui XTTS (use speaker_wav parameter)."""
        ...

    async def close(self):
        await self._http_client.aclose()
```

Implement all methods fully with proper error handling, logging, temp file management, and httpx calls.

## Conventions
- Use `httpx.AsyncClient` for all HTTP calls (already in project deps)
- Save audio to temp files, return paths
- All costs in USD
- Log all provider calls at INFO level
- Raise `AppException` (from `app.core.exceptions`) on failures
