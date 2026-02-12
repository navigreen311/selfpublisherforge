"""Real-time Automatic Speech Recognition engine.

Primary: Faster-Whisper Large-v3 (self-hosted)
Fallback: Deepgram API

Audio format: 16 kHz, 16-bit mono PCM, ~250 ms chunks.
Segments of ~3-5 s are accumulated before transcription.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import logging
import struct
import time
from dataclasses import dataclass, field

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

SESSION_IDLE_TIMEOUT_S = 300  # 5 minutes


@dataclass
class WordTiming:
    """A single word with timing and confidence."""

    word: str
    start_ms: int
    end_ms: int
    confidence: float


@dataclass
class TranscriptEvent:
    """Emitted for every partial or final transcript."""

    is_final: bool
    text: str
    confidence: float
    words: list[WordTiming] = field(default_factory=list)
    language: str = "en"


@dataclass
class ASRSession:
    """Per-connection state for an ASR stream."""

    session_id: str
    language: str
    buffer: bytearray = field(default_factory=bytearray)
    is_active: bool = True
    total_audio_seconds: float = 0.0
    last_activity: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Voice command map
# ---------------------------------------------------------------------------

_VOICE_COMMANDS: dict[str, str] = {
    "new paragraph": "new_paragraph",
    "new line": "new_line",
    "period": "insert_period",
    "comma": "insert_comma",
    "question mark": "insert_question_mark",
    "exclamation mark": "insert_exclamation_mark",
    "delete that": "delete_last_sentence",
    "undo": "undo",
    "bold that": "apply_bold",
    "italic that": "apply_italic",
    "chapter break": "chapter_break",
    "stop dictation": "stop_dictation",
    "read that back": "read_back",
}

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

_SUPPORTED_LANGUAGES: list[dict[str, str]] = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "de", "name": "German"},
    {"code": "fr", "name": "French"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ja", "name": "Japanese"},
    {"code": "zh", "name": "Chinese"},
    {"code": "ko", "name": "Korean"},
    {"code": "it", "name": "Italian"},
    {"code": "nl", "name": "Dutch"},
]


# ---------------------------------------------------------------------------
# ASR Engine
# ---------------------------------------------------------------------------


class ASREngine:
    """Real-time ASR with Faster-Whisper and Deepgram fallback."""

    CHUNK_DURATION_MS = 250
    SEGMENT_DURATION_MS = 3000  # accumulate ~3 s before processing
    SAMPLE_RATE = 16000
    SAMPLE_WIDTH = 2  # 16-bit PCM = 2 bytes per sample
    BYTES_PER_SECOND = SAMPLE_RATE * SAMPLE_WIDTH

    def __init__(self) -> None:
        self.settings = get_settings()
        self._sessions: dict[str, ASRSession] = {}
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._cleanup_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def start_session(
        self,
        session_id: str,
        language: str = "en",
        config: dict | None = None,  # noqa: ARG002 - reserved for future use
    ) -> ASRSession:
        """Initialize a new ASR session."""
        session = ASRSession(session_id=session_id, language=language)
        self._sessions[session_id] = session
        logger.info("ASR session started: %s (lang=%s)", session_id, language)

        # Start the idle-session reaper if not already running.
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._reap_idle_sessions())

        return session

    async def end_session(self, session_id: str) -> TranscriptEvent | None:
        """End session and process any remaining audio in the buffer."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return None

        session.is_active = False
        logger.info(
            "ASR session ended: %s (total_audio=%.1fs)",
            session_id,
            session.total_audio_seconds,
        )

        if len(session.buffer) > 0:
            return await self._process_segment(session, is_final=True)
        return None

    # ------------------------------------------------------------------
    # Audio processing
    # ------------------------------------------------------------------

    async def process_audio_chunk(
        self, session_id: str, audio_chunk: bytes
    ) -> TranscriptEvent | None:
        """Process an incoming audio chunk.

        Returns a ``TranscriptEvent`` when enough audio has been accumulated,
        otherwise ``None``.
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return None

        session.buffer.extend(audio_chunk)
        session.last_activity = time.time()

        chunk_seconds = len(audio_chunk) / self.BYTES_PER_SECOND
        session.total_audio_seconds += chunk_seconds

        buffer_duration_ms = (len(session.buffer) / self.BYTES_PER_SECOND) * 1000

        # Enough for a full segment → produce final transcript and clear buffer.
        if buffer_duration_ms >= self.SEGMENT_DURATION_MS:
            return await self._process_segment(session, is_final=True)

        # At least 1 s of audio → produce a partial (non-final) transcript.
        if buffer_duration_ms >= 1000:
            return await self._get_partial(session)

        return None

    # ------------------------------------------------------------------
    # Primary transcription via Faster-Whisper
    # ------------------------------------------------------------------

    async def _process_segment(
        self, session: ASRSession, *, is_final: bool = True
    ) -> TranscriptEvent:
        """Transcribe a buffered segment via Faster-Whisper, falling back to Deepgram."""
        audio_data = bytes(session.buffer)
        session.buffer.clear()

        try:
            result = await self._transcribe_whisper(audio_data, session.language)
            return TranscriptEvent(
                is_final=is_final,
                text=result["text"],
                confidence=result.get("confidence", 0.9),
                words=result.get("words", []),
                language=session.language,
            )
        except Exception as exc:
            logger.warning("Whisper failed, trying Deepgram fallback: %s", exc)
            return await self._transcribe_deepgram(
                audio_data, session.language, is_final=is_final
            )

    async def _get_partial(self, session: ASRSession) -> TranscriptEvent:
        """Return a partial (non-final) transcript for real-time display.

        The buffer is **not** cleared so the full context is available when the
        segment is finally processed.
        """
        audio_data = bytes(session.buffer)
        try:
            result = await self._transcribe_whisper(audio_data, session.language)
            return TranscriptEvent(
                is_final=False,
                text=result["text"],
                confidence=result.get("confidence", 0.8),
                language=session.language,
            )
        except Exception:
            return TranscriptEvent(is_final=False, text="", confidence=0.0)

    async def _transcribe_whisper(
        self, audio_data: bytes, language: str
    ) -> dict:
        """Call the Faster-Whisper OpenAI-compatible transcription endpoint."""
        endpoint = (
            f"{self.settings.FASTER_WHISPER_ENDPOINT}/v1/audio/transcriptions"
        )
        wav_data = self._pcm_to_wav(audio_data)

        files = {"file": ("audio.wav", wav_data, "audio/wav")}
        data = {
            "model": self.settings.FASTER_WHISPER_MODEL,
            "language": language,
            "response_format": "verbose_json",
        }

        response = await self._http_client.post(endpoint, files=files, data=data)
        response.raise_for_status()
        result = response.json()

        words: list[WordTiming] = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                words.append(
                    WordTiming(
                        word=w["word"].strip(),
                        start_ms=int(w["start"] * 1000),
                        end_ms=int(w["end"] * 1000),
                        confidence=w.get("probability", 0.9),
                    )
                )

        # Aggregate confidence across words (fallback to 0.9).
        avg_confidence = (
            sum(wt.confidence for wt in words) / len(words)
            if words
            else 0.9
        )

        return {
            "text": result.get("text", "").strip(),
            "confidence": round(avg_confidence, 4),
            "words": words,
        }

    # ------------------------------------------------------------------
    # Fallback transcription via Deepgram
    # ------------------------------------------------------------------

    async def _transcribe_deepgram(
        self,
        audio_data: bytes,
        language: str,
        *,
        is_final: bool = True,
    ) -> TranscriptEvent:
        """Fallback transcription via the Deepgram REST API."""
        api_key = self.settings.DEEPGRAM_API_KEY
        if not api_key:
            logger.warning("Deepgram API key not configured; returning empty transcript")
            return TranscriptEvent(is_final=is_final, text="", confidence=0.0)

        wav_data = self._pcm_to_wav(audio_data)
        url = "https://api.deepgram.com/v1/listen"
        params = {
            "model": "nova-2",
            "language": language,
            "punctuate": "true",
            "smart_format": "true",
        }
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav",
        }

        try:
            response = await self._http_client.post(
                url, params=params, headers=headers, content=wav_data
            )
            response.raise_for_status()
            body = response.json()

            channel = (
                body.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
            )
            text = channel.get("transcript", "").strip()
            confidence = channel.get("confidence", 0.0)

            words: list[WordTiming] = []
            for dg_word in channel.get("words", []):
                words.append(
                    WordTiming(
                        word=dg_word.get("word", ""),
                        start_ms=int(dg_word.get("start", 0) * 1000),
                        end_ms=int(dg_word.get("end", 0) * 1000),
                        confidence=dg_word.get("confidence", 0.0),
                    )
                )

            return TranscriptEvent(
                is_final=is_final,
                text=text,
                confidence=confidence,
                words=words,
                language=language,
            )
        except Exception as exc:
            logger.warning("Deepgram fallback also failed: %s", exc)
            return TranscriptEvent(is_final=is_final, text="", confidence=0.0)

    # ------------------------------------------------------------------
    # WAV encoding
    # ------------------------------------------------------------------

    @classmethod
    def _pcm_to_wav(cls, pcm_data: bytes) -> bytes:
        """Wrap raw 16-bit mono PCM in a WAV container."""
        buf = io.BytesIO()
        data_size = len(pcm_data)

        # RIFF header
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + data_size))
        buf.write(b"WAVE")

        # fmt sub-chunk
        buf.write(b"fmt ")
        buf.write(struct.pack("<I", 16))  # sub-chunk size
        buf.write(struct.pack("<H", 1))  # audio format: PCM
        buf.write(struct.pack("<H", 1))  # channels: mono
        buf.write(struct.pack("<I", cls.SAMPLE_RATE))
        buf.write(struct.pack("<I", cls.SAMPLE_RATE * cls.SAMPLE_WIDTH))  # byte rate
        buf.write(struct.pack("<H", cls.SAMPLE_WIDTH))  # block align
        buf.write(struct.pack("<H", 16))  # bits per sample

        # data sub-chunk
        buf.write(b"data")
        buf.write(struct.pack("<I", data_size))
        buf.write(pcm_data)

        return buf.getvalue()

    # ------------------------------------------------------------------
    # Voice commands
    # ------------------------------------------------------------------

    @staticmethod
    def detect_voice_commands(text: str) -> tuple[str, str] | None:
        """Detect voice commands in transcribed text.

        Returns ``(matched_phrase, action_name)`` or ``None``.
        """
        text_lower = text.strip().lower()
        if not text_lower:
            return None

        for phrase, action in _VOICE_COMMANDS.items():
            if (
                text_lower == phrase
                or text_lower.startswith(phrase + " ")
                or text_lower.endswith(" " + phrase)
            ):
                return (phrase, action)
        return None

    # ------------------------------------------------------------------
    # Language support
    # ------------------------------------------------------------------

    @staticmethod
    def get_supported_languages() -> list[dict[str, str]]:
        """Return the list of supported ASR languages."""
        return list(_SUPPORTED_LANGUAGES)

    # ------------------------------------------------------------------
    # Idle session reaper
    # ------------------------------------------------------------------

    async def _reap_idle_sessions(self) -> None:
        """Periodically end sessions that have been idle for > 5 minutes."""
        while self._sessions:
            await asyncio.sleep(60)  # check every minute
            now = time.time()
            expired = [
                sid
                for sid, sess in self._sessions.items()
                if now - sess.last_activity > SESSION_IDLE_TIMEOUT_S
            ]
            for sid in expired:
                logger.info("Reaping idle ASR session: %s", sid)
                await self.end_session(sid)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Shut down the engine: end all sessions, cancel reaper, close HTTP client."""
        # Cancel the reaper task.
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        # End remaining sessions (don't process remaining audio on shutdown).
        for sid in list(self._sessions):
            session = self._sessions.pop(sid, None)
            if session:
                session.is_active = False
                logger.info("ASR session force-closed on shutdown: %s", sid)

        await self._http_client.aclose()
