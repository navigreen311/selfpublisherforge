# VF08: ASR Engine Service

## Task
Create the Automatic Speech Recognition engine for real-time dictation.

## Files to Create

### `backend/app/services/voiceforge/asr_engine.py`

Real-time speech-to-text using Faster-Whisper Large-v3 (primary) with Deepgram fallback.

**Architecture:**
- Client sends audio chunks via WebSocket (16kHz, 16-bit PCM, 250ms chunks)
- Server accumulates chunks into segments (~3-5 seconds)
- Faster-Whisper processes segments and returns partial + final transcripts
- Voice Activity Detection (VAD) detects speech boundaries
- Voice commands intercepted before transcript is emitted

```python
import asyncio
import httpx
import io
import logging
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class WordTiming:
    word: str
    start_ms: int
    end_ms: int
    confidence: float

@dataclass
class TranscriptEvent:
    is_final: bool
    text: str
    confidence: float
    words: list[WordTiming] = field(default_factory=list)
    language: str = "en"

@dataclass
class ASRSession:
    session_id: str
    language: str
    buffer: bytearray = field(default_factory=bytearray)
    is_active: bool = True
    total_audio_seconds: float = 0.0
    last_activity: float = field(default_factory=time.time)

class ASREngine:
    """Real-time ASR with Faster-Whisper and Deepgram fallback."""

    CHUNK_DURATION_MS = 250
    SEGMENT_DURATION_MS = 3000  # accumulate ~3s before processing
    SAMPLE_RATE = 16000
    SAMPLE_WIDTH = 2  # 16-bit

    def __init__(self):
        self.settings = get_settings()
        self._sessions: dict[str, ASRSession] = {}
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def start_session(self, session_id: str, language: str = "en", config: dict | None = None) -> ASRSession:
        """Initialize a new ASR session."""
        session = ASRSession(session_id=session_id, language=language)
        self._sessions[session_id] = session
        logger.info("ASR session started: %s (lang=%s)", session_id, language)
        return session

    async def process_audio_chunk(self, session_id: str, audio_chunk: bytes) -> TranscriptEvent | None:
        """Process an incoming audio chunk. Returns transcript event when segment is ready."""
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return None

        session.buffer.extend(audio_chunk)
        session.last_activity = time.time()

        # Calculate buffer duration
        buffer_duration_ms = (len(session.buffer) / (self.SAMPLE_RATE * self.SAMPLE_WIDTH)) * 1000

        # If buffer has enough audio, process it
        if buffer_duration_ms >= self.SEGMENT_DURATION_MS:
            return await self._process_segment(session)

        # Return partial result if we have at least 1 second
        if buffer_duration_ms >= 1000:
            return await self._get_partial(session)

        return None

    async def end_session(self, session_id: str) -> TranscriptEvent | None:
        """End session and process remaining audio buffer."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return None

        session.is_active = False

        # Process any remaining buffer
        if len(session.buffer) > 0:
            return await self._process_segment(session, is_final=True)
        return None

    async def _process_segment(self, session: ASRSession, is_final: bool = True) -> TranscriptEvent:
        """Send buffered audio to Faster-Whisper for transcription."""
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
        except Exception as e:
            logger.warning("Whisper failed, trying Deepgram fallback: %s", e)
            return await self._transcribe_deepgram(audio_data, session.language, is_final)

    async def _get_partial(self, session: ASRSession) -> TranscriptEvent:
        """Get a partial (non-final) transcript for real-time display."""
        audio_data = bytes(session.buffer)  # don't clear — we'll reprocess with more context
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

    async def _transcribe_whisper(self, audio_data: bytes, language: str) -> dict:
        """Transcribe via Faster-Whisper server."""
        endpoint = f"{self.settings.FASTER_WHISPER_ENDPOINT}/v1/audio/transcriptions"
        # Create WAV-format bytes from raw PCM
        wav_data = self._pcm_to_wav(audio_data)
        files = {"file": ("audio.wav", wav_data, "audio/wav")}
        data = {"model": self.settings.FASTER_WHISPER_MODEL, "language": language, "response_format": "verbose_json"}
        response = await self._http_client.post(endpoint, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        words = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                words.append(WordTiming(
                    word=w["word"].strip(),
                    start_ms=int(w["start"] * 1000),
                    end_ms=int(w["end"] * 1000),
                    confidence=w.get("probability", 0.9),
                ))
        return {"text": result.get("text", "").strip(), "confidence": 0.9, "words": words}

    async def _transcribe_deepgram(self, audio_data: bytes, language: str, is_final: bool) -> TranscriptEvent:
        """Fallback transcription via Deepgram API."""
        if not self.settings.DEEPGRAM_API_KEY:
            return TranscriptEvent(is_final=is_final, text="", confidence=0.0)
        # POST to Deepgram /v1/listen
        ...
        return TranscriptEvent(is_final=is_final, text="[deepgram fallback]", confidence=0.5)

    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert raw PCM to WAV format."""
        buf = io.BytesIO()
        # WAV header
        data_size = len(pcm_data)
        buf.write(b'RIFF')
        buf.write(struct.pack('<I', 36 + data_size))
        buf.write(b'WAVE')
        buf.write(b'fmt ')
        buf.write(struct.pack('<I', 16))  # chunk size
        buf.write(struct.pack('<H', 1))   # PCM format
        buf.write(struct.pack('<H', 1))   # mono
        buf.write(struct.pack('<I', self.SAMPLE_RATE))
        buf.write(struct.pack('<I', self.SAMPLE_RATE * self.SAMPLE_WIDTH))
        buf.write(struct.pack('<H', self.SAMPLE_WIDTH))
        buf.write(struct.pack('<H', 16))  # bits per sample
        buf.write(b'data')
        buf.write(struct.pack('<I', data_size))
        buf.write(pcm_data)
        return buf.getvalue()

    def detect_voice_commands(self, text: str) -> tuple[str, str] | None:
        """Detect voice commands in transcribed text."""
        text_lower = text.strip().lower()
        commands = {
            "new paragraph": "new_paragraph",
            "new line": "new_line",
            "period": "insert_period",
            "comma": "insert_comma",
            "question mark": "insert_question_mark",
            "delete that": "delete_last_sentence",
            "undo": "undo",
            "bold that": "apply_bold",
            "italic that": "apply_italic",
            "chapter break": "chapter_break",
            "stop dictation": "stop_dictation",
            "read that back": "read_back",
        }
        for phrase, action in commands.items():
            if text_lower == phrase or text_lower.startswith(phrase + " ") or text_lower.endswith(" " + phrase):
                return (phrase, action)
        return None

    def get_supported_languages(self) -> list[dict]:
        """Return supported languages."""
        return [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "de", "name": "German"},
            {"code": "fr", "name": "French"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ja", "name": "Japanese"},
        ]

    async def close(self):
        await self._http_client.aclose()
```

Implement all methods fully.

## Conventions
- Use `httpx.AsyncClient` for HTTP calls
- Voice commands are case-insensitive
- Session cleanup: sessions idle > 5 minutes should be auto-ended
- Log at INFO level for session lifecycle, WARNING for fallbacks
