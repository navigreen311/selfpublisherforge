"""Multi-provider Text-to-Speech engine with intelligent routing.

Supported providers:
- **Coqui XTTS v2** — Self-hosted, cost-effective (~$0.001/min).
  Best for drafts, previews, and budget-tier audiobooks.
- **Piper** — Ultra-fast, lowest cost (~$0.0001/min).
  Best for quick previews.
- **ElevenLabs** — Premium cloud API (~$0.03/min), highest quality.
  Best for final production, premium tier, and voice cloning.
"""

from __future__ import annotations

import logging
import re
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import get_settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class AudioResult:
    """Result of a TTS generation call."""

    audio_path: Path
    duration_seconds: float
    sample_rate: int
    file_size_bytes: int
    provider: str
    cost_usd: float


@dataclass
class CostEstimate:
    """Pre-generation cost estimate for a text + provider pair."""

    provider: str
    estimated_duration_minutes: float
    cost_per_minute: float
    total_cost: float
    word_count: int


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROVIDER_RATES: dict[str, float] = {
    "coqui_xtts": 0.001,
    "piper": 0.0001,
    "elevenlabs": 0.03,
}

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Default pause durations (seconds) injected between segments.
_SENTENCE_PAUSE = 0.4
_PARAGRAPH_PAUSE = 0.8

# Preview hard-limit (words).
_PREVIEW_MAX_WORDS = 25


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class TTSEngine:
    """Core TTS engine with provider abstraction.

    Usage::

        engine = TTSEngine()
        result = await engine.generate_speech(
            text="Hello, world!",
            voice_id="default",
            provider="coqui_xtts",
        )
        print(result.audio_path, result.cost_usd)
        await engine.close()
    """

    WORDS_PER_MINUTE = 150  # average narration speed

    def __init__(self) -> None:
        self.settings = get_settings()
        self._http_client = httpx.AsyncClient(timeout=300.0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        provider: str,
        params: dict | None = None,
    ) -> AudioResult:
        """Generate speech audio from *text* using the specified *provider*."""
        if provider == "coqui_xtts":
            return await self._generate_coqui(text, voice_id, params or {})
        if provider == "elevenlabs":
            return await self._generate_elevenlabs(text, voice_id, params or {})
        if provider == "piper":
            return await self._generate_piper(text, voice_id, params or {})
        raise AppException(
            status_code=400,
            code="TTS_UNKNOWN_PROVIDER",
            message=f"Unknown TTS provider: {provider}",
        )

    async def generate_chapter(
        self,
        chapter_text: str,
        voice_config: dict,
        project_config: dict,
    ) -> AudioResult:
        """Generate audio for an entire chapter with sentence-level processing.

        The chapter text is split into paragraphs and then sentences.
        Each sentence is synthesised individually and short silence gaps
        are inserted between sentences and paragraphs.  The resulting
        WAV segments are concatenated into a single file.
        """
        provider: str = voice_config.get("provider", "coqui_xtts")
        voice_id: str = voice_config.get("voice_id", "default")
        params: dict = voice_config.get("params", {})
        sample_rate: int = project_config.get("sample_rate", 22050)

        paragraphs = [p.strip() for p in chapter_text.split("\n\n") if p.strip()]
        if not paragraphs:
            raise AppException(
                status_code=422,
                code="TTS_EMPTY_TEXT",
                message="Chapter text is empty — nothing to synthesise.",
            )

        all_pcm: list[bytes] = []
        total_cost = 0.0

        for para_idx, paragraph in enumerate(paragraphs):
            sentences = _SENTENCE_SPLIT_RE.split(paragraph)
            for sent_idx, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue

                logger.info(
                    "Chapter TTS | para=%d sent=%d provider=%s len=%d",
                    para_idx,
                    sent_idx,
                    provider,
                    len(sentence),
                )
                result = await self.generate_speech(sentence, voice_id, provider, params)
                total_cost += result.cost_usd

                pcm = _read_wav_pcm(result.audio_path)
                all_pcm.append(pcm)

                # Sentence pause (silence).
                all_pcm.append(_silence_pcm(sample_rate, _SENTENCE_PAUSE))

            # Paragraph pause (longer silence).
            all_pcm.append(_silence_pcm(sample_rate, _PARAGRAPH_PAUSE))

        combined_pcm = b"".join(all_pcm)
        out_path = _temp_wav_path("chapter")
        _write_wav(out_path, combined_pcm, sample_rate)

        duration = len(combined_pcm) / 2 / sample_rate  # 16-bit mono
        file_size = out_path.stat().st_size

        logger.info(
            "Chapter generated | provider=%s duration=%.1fs cost=$%.4f path=%s",
            provider,
            duration,
            total_cost,
            out_path,
        )

        return AudioResult(
            audio_path=out_path,
            duration_seconds=round(duration, 2),
            sample_rate=sample_rate,
            file_size_bytes=file_size,
            provider=provider,
            cost_usd=round(total_cost, 6),
        )

    async def preview_voice(
        self,
        sample_text: str,
        voice_id: str,
        provider: str,
    ) -> AudioResult:
        """Quick voice preview — limited to ~25 words / ~10 seconds."""
        words = sample_text.split()
        if len(words) > _PREVIEW_MAX_WORDS:
            sample_text = " ".join(words[:_PREVIEW_MAX_WORDS])
            logger.info("Preview text trimmed to %d words", _PREVIEW_MAX_WORDS)

        logger.info("Voice preview | provider=%s voice=%s", provider, voice_id)
        return await self.generate_speech(sample_text, voice_id, provider)

    async def clone_voice(
        self,
        audio_samples: list[Path],
        voice_name: str,
        provider: str,
    ) -> dict:
        """Create a cloned voice from audio samples."""
        if provider == "elevenlabs":
            return await self._clone_elevenlabs(audio_samples, voice_name)
        if provider == "coqui_xtts":
            return await self._clone_coqui(audio_samples, voice_name)
        raise AppException(
            status_code=400,
            code="TTS_CLONE_UNSUPPORTED",
            message=f"Voice cloning not supported for provider: {provider}",
        )

    def estimate_cost(self, text: str, provider: str) -> CostEstimate:
        """Estimate generation cost based on text length and provider."""
        word_count = len(text.split())
        duration_minutes = word_count / self.WORDS_PER_MINUTE
        rate = _PROVIDER_RATES.get(provider, 0.01)
        return CostEstimate(
            provider=provider,
            estimated_duration_minutes=round(duration_minutes, 2),
            cost_per_minute=rate,
            total_cost=round(duration_minutes * rate, 6),
            word_count=word_count,
        )

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    async def _generate_coqui(self, text: str, voice_id: str, params: dict) -> AudioResult:
        """Generate via self-hosted Coqui XTTS server."""
        endpoint = self.settings.COQUI_XTTS_ENDPOINT
        language = params.get("language", "en")

        payload: dict = {
            "text": text,
            "speaker_wav": voice_id,
            "language": language,
        }

        logger.info("Coqui XTTS request | endpoint=%s voice=%s len=%d", endpoint, voice_id, len(text))

        try:
            response = await self._http_client.post(
                f"{endpoint}/tts_to_audio/",
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Coqui XTTS HTTP error: %s", exc)
            raise AppException(
                status_code=502,
                code="TTS_COQUI_ERROR",
                message=f"Coqui XTTS generation failed: {exc.response.status_code}",
                details=[str(exc)],
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Coqui XTTS connection error: %s", exc)
            raise AppException(
                status_code=503,
                code="TTS_COQUI_UNAVAILABLE",
                message="Coqui XTTS service is unavailable.",
                details=[str(exc)],
            ) from exc

        audio_bytes = response.content
        out_path = _temp_wav_path("coqui")
        out_path.write_bytes(audio_bytes)

        sample_rate = _detect_wav_sample_rate(audio_bytes)
        duration = _estimate_wav_duration(audio_bytes, sample_rate)
        cost = self.estimate_cost(text, "coqui_xtts")

        logger.info("Coqui XTTS done | duration=%.1fs path=%s", duration, out_path)

        return AudioResult(
            audio_path=out_path,
            duration_seconds=round(duration, 2),
            sample_rate=sample_rate,
            file_size_bytes=len(audio_bytes),
            provider="coqui_xtts",
            cost_usd=cost.total_cost,
        )

    async def _generate_elevenlabs(self, text: str, voice_id: str, params: dict) -> AudioResult:
        """Generate via ElevenLabs API."""
        api_key = self.settings.ELEVENLABS_API_KEY
        if not api_key:
            raise AppException(
                status_code=500,
                code="TTS_ELEVENLABS_NO_KEY",
                message="ElevenLabs API key is not configured.",
            )

        model_id = params.get("model_id", "eleven_multilingual_v2")
        stability = params.get("stability", 0.5)
        similarity_boost = params.get("similarity_boost", 0.75)
        style = params.get("style", 0.0)
        output_format = params.get("output_format", "mp3_44100_128")

        url = f"{_ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
            },
        }

        logger.info("ElevenLabs request | voice=%s model=%s len=%d", voice_id, model_id, len(text))

        try:
            response = await self._http_client.post(
                url,
                json=payload,
                headers=headers,
                params={"output_format": output_format},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("ElevenLabs HTTP error: %s", exc)
            raise AppException(
                status_code=502,
                code="TTS_ELEVENLABS_ERROR",
                message=f"ElevenLabs generation failed: {exc.response.status_code}",
                details=[str(exc)],
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ElevenLabs connection error: %s", exc)
            raise AppException(
                status_code=503,
                code="TTS_ELEVENLABS_UNAVAILABLE",
                message="ElevenLabs API is unavailable.",
                details=[str(exc)],
            ) from exc

        audio_bytes = response.content
        suffix = ".mp3" if "mp3" in output_format else ".wav"
        out_path = _temp_audio_path("elevenlabs", suffix)
        out_path.write_bytes(audio_bytes)

        # ElevenLabs returns MP3 by default; estimate duration from text.
        cost = self.estimate_cost(text, "elevenlabs")
        duration = cost.estimated_duration_minutes * 60

        logger.info("ElevenLabs done | duration=%.1fs path=%s", duration, out_path)

        return AudioResult(
            audio_path=out_path,
            duration_seconds=round(duration, 2),
            sample_rate=44100,
            file_size_bytes=len(audio_bytes),
            provider="elevenlabs",
            cost_usd=cost.total_cost,
        )

    async def _generate_piper(self, text: str, voice_id: str, params: dict) -> AudioResult:
        """Generate via self-hosted Piper TTS."""
        endpoint = self.settings.PIPER_ENDPOINT

        payload: dict = {
            "text": text,
            "voice": voice_id,
        }
        if "speed" in params:
            payload["speed"] = params["speed"]

        logger.info("Piper request | endpoint=%s voice=%s len=%d", endpoint, voice_id, len(text))

        try:
            response = await self._http_client.post(
                f"{endpoint}/synthesize",
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Piper HTTP error: %s", exc)
            raise AppException(
                status_code=502,
                code="TTS_PIPER_ERROR",
                message=f"Piper TTS generation failed: {exc.response.status_code}",
                details=[str(exc)],
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Piper connection error: %s", exc)
            raise AppException(
                status_code=503,
                code="TTS_PIPER_UNAVAILABLE",
                message="Piper TTS service is unavailable.",
                details=[str(exc)],
            ) from exc

        audio_bytes = response.content
        out_path = _temp_wav_path("piper")
        out_path.write_bytes(audio_bytes)

        sample_rate = _detect_wav_sample_rate(audio_bytes)
        duration = _estimate_wav_duration(audio_bytes, sample_rate)
        cost = self.estimate_cost(text, "piper")

        logger.info("Piper done | duration=%.1fs path=%s", duration, out_path)

        return AudioResult(
            audio_path=out_path,
            duration_seconds=round(duration, 2),
            sample_rate=sample_rate,
            file_size_bytes=len(audio_bytes),
            provider="piper",
            cost_usd=cost.total_cost,
        )

    # ------------------------------------------------------------------
    # Voice cloning
    # ------------------------------------------------------------------

    async def _clone_elevenlabs(self, audio_samples: list[Path], name: str) -> dict:
        """Clone voice via ElevenLabs API."""
        api_key = self.settings.ELEVENLABS_API_KEY
        if not api_key:
            raise AppException(
                status_code=500,
                code="TTS_ELEVENLABS_NO_KEY",
                message="ElevenLabs API key is not configured.",
            )

        url = f"{_ELEVENLABS_BASE_URL}/voices/add"
        headers = {"xi-api-key": api_key}

        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for sample in audio_samples:
            files.append(("files", (sample.name, sample.read_bytes(), "audio/mpeg")))

        logger.info("ElevenLabs clone | name=%s samples=%d", name, len(audio_samples))

        try:
            response = await self._http_client.post(
                url,
                headers=headers,
                data={"name": name, "description": f"Cloned voice: {name}"},
                files=files,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("ElevenLabs clone HTTP error: %s", exc)
            raise AppException(
                status_code=502,
                code="TTS_CLONE_ERROR",
                message=f"ElevenLabs voice cloning failed: {exc.response.status_code}",
                details=[str(exc)],
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ElevenLabs clone connection error: %s", exc)
            raise AppException(
                status_code=503,
                code="TTS_ELEVENLABS_UNAVAILABLE",
                message="ElevenLabs API is unavailable.",
                details=[str(exc)],
            ) from exc

        result = response.json()
        logger.info("ElevenLabs clone done | voice_id=%s", result.get("voice_id"))
        return {
            "voice_id": result.get("voice_id"),
            "name": name,
            "provider": "elevenlabs",
        }

    async def _clone_coqui(self, audio_samples: list[Path], name: str) -> dict:
        """Clone voice via Coqui XTTS (uses speaker_wav parameter).

        Coqui XTTS performs zero-shot voice cloning by accepting a
        reference ``speaker_wav`` audio file at synthesis time.  This
        method registers the sample paths so they can be referenced as a
        ``voice_id`` in subsequent ``generate_speech`` calls.
        """
        if not audio_samples:
            raise AppException(
                status_code=422,
                code="TTS_CLONE_NO_SAMPLES",
                message="At least one audio sample is required for voice cloning.",
            )

        # Use the first sample as the primary speaker reference.
        primary_sample = audio_samples[0]
        if not primary_sample.exists():
            raise AppException(
                status_code=422,
                code="TTS_CLONE_SAMPLE_NOT_FOUND",
                message=f"Audio sample not found: {primary_sample}",
            )

        logger.info("Coqui clone | name=%s sample=%s", name, primary_sample)

        return {
            "voice_id": str(primary_sample),
            "name": name,
            "provider": "coqui_xtts",
            "speaker_wav": str(primary_sample),
            "additional_samples": [str(s) for s in audio_samples[1:]],
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http_client.aclose()


# ---------------------------------------------------------------------------
# WAV helpers (private)
# ---------------------------------------------------------------------------


def _temp_wav_path(prefix: str) -> Path:
    """Create a temporary WAV file path (caller writes the content)."""
    fd, path = tempfile.mkstemp(suffix=".wav", prefix=f"vf_tts_{prefix}_")
    # Close the fd immediately — we only need the path.
    import os

    os.close(fd)
    return Path(path)


def _temp_audio_path(prefix: str, suffix: str = ".wav") -> Path:
    """Create a temporary audio file path with an arbitrary suffix."""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=f"vf_tts_{prefix}_")
    import os

    os.close(fd)
    return Path(path)


def _detect_wav_sample_rate(data: bytes) -> int:
    """Read the sample rate from a WAV file header.

    Falls back to 22050 if the header cannot be parsed.
    """
    if len(data) < 28:  # WAV header minimum
        return 22050
    # WAV header: bytes 24-27 are the sample rate (little-endian uint32).
    return struct.unpack_from("<I", data, 24)[0] or 22050


def _estimate_wav_duration(data: bytes, sample_rate: int) -> float:
    """Estimate WAV duration from raw byte length.

    Assumes 16-bit mono PCM.
    """
    header_size = 44
    pcm_bytes = max(len(data) - header_size, 0)
    # 16-bit = 2 bytes per sample, mono = 1 channel.
    return pcm_bytes / (2 * sample_rate) if sample_rate else 0.0


def _read_wav_pcm(path: Path) -> bytes:
    """Read raw PCM data from a WAV file, skipping the 44-byte header."""
    raw = path.read_bytes()
    return raw[44:]


def _silence_pcm(sample_rate: int, duration_seconds: float) -> bytes:
    """Generate silent 16-bit mono PCM data for a given duration."""
    num_samples = int(sample_rate * duration_seconds)
    return b"\x00\x00" * num_samples


def _write_wav(path: Path, pcm_data: bytes, sample_rate: int) -> None:
    """Write raw 16-bit mono PCM data as a valid WAV file."""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)
    file_size = 36 + data_size  # RIFF chunk size (file size - 8)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        file_size,
        b"WAVE",
        b"fmt ",
        16,  # fmt chunk size
        1,  # PCM format
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    path.write_bytes(header + pcm_data)
