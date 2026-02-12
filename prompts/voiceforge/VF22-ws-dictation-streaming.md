# VF22: WebSocket Handler — Dictation Streaming

## Task
Create bidirectional WebSocket endpoint for real-time dictation (audio in, transcript out).

## Files to Create

### `backend/app/modules/dictation/websocket.py`

```python
"""WebSocket endpoint for real-time dictation streaming.

Client sends audio chunks (16kHz, 16-bit PCM, 250ms)
Server returns transcript events (partial and final)

Protocol:
  Client → Server:
    - Binary frames: audio chunk data
    - Text frames: JSON commands {"type": "pause"|"resume"|"end_session"|"set_language", ...}

  Server → Client:
    - {"type": "partial_transcript", "text": "...", "confidence": 0.8}
    - {"type": "final_transcript", "text": "...", "confidence": 0.95, "words": [...]}
    - {"type": "voice_command", "command": "new paragraph", "action": "new_paragraph"}
    - {"type": "error", "message": "...", "recoverable": true}
    - {"type": "session_metrics", "wpm": 45, "accuracy": 0.92, "duration": 120}
"""

import asyncio
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/dictation/{session_id}")
async def dictation_ws(websocket: WebSocket, session_id: str):
    """Bidirectional WebSocket for real-time dictation."""
    await websocket.accept()

    from app.services.voiceforge.asr_engine import ASREngine
    asr = ASREngine()
    session = await asr.start_session(session_id)

    words_count = 0
    start_time = time.time()

    logger.info("Dictation WebSocket connected: %s", session_id)

    try:
        while True:
            message = await websocket.receive()

            # Binary frame = audio chunk
            if "bytes" in message:
                audio_chunk = message["bytes"]
                result = await asr.process_audio_chunk(session_id, audio_chunk)

                if result:
                    # Check for voice commands
                    command = asr.detect_voice_commands(result.text)
                    if command:
                        await websocket.send_text(json.dumps({
                            "type": "voice_command",
                            "command": command[0],
                            "action": command[1],
                        }))
                        continue

                    if result.is_final:
                        words_count += len(result.text.split())
                        await websocket.send_text(json.dumps({
                            "type": "final_transcript",
                            "text": result.text,
                            "confidence": result.confidence,
                            "words": [
                                {"word": w.word, "start_ms": w.start_ms, "end_ms": w.end_ms, "confidence": w.confidence}
                                for w in result.words
                            ],
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "partial_transcript",
                            "text": result.text,
                            "confidence": result.confidence,
                        }))

            # Text frame = JSON command
            elif "text" in message:
                try:
                    cmd = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                if cmd.get("type") == "pause":
                    # Pause processing (but keep connection)
                    await websocket.send_text(json.dumps({"type": "session_paused"}))

                elif cmd.get("type") == "resume":
                    await websocket.send_text(json.dumps({"type": "session_resumed"}))

                elif cmd.get("type") == "end_session":
                    # Process remaining buffer
                    final = await asr.end_session(session_id)
                    if final and final.text:
                        words_count += len(final.text.split())
                        await websocket.send_text(json.dumps({
                            "type": "final_transcript",
                            "text": final.text,
                            "confidence": final.confidence,
                            "words": [
                                {"word": w.word, "start_ms": w.start_ms, "end_ms": w.end_ms, "confidence": w.confidence}
                                for w in final.words
                            ],
                        }))

                    # Send session metrics
                    duration = int(time.time() - start_time)
                    wpm = (words_count / duration * 60) if duration > 0 else 0
                    await websocket.send_text(json.dumps({
                        "type": "session_metrics",
                        "wpm": round(wpm, 1),
                        "accuracy": 0.92,  # TODO: calculate from confidence scores
                        "duration": duration,
                    }))
                    break

                elif cmd.get("type") == "set_language":
                    session.language = cmd.get("language", "en")

                elif cmd.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info("Dictation WebSocket disconnected: %s", session_id)
        await asr.end_session(session_id)
    except Exception as e:
        logger.error("Dictation WebSocket error: %s", e, exc_info=True)
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
                "recoverable": False,
            }))
        except Exception:
            pass
    finally:
        await asr.close()
        # Update session record in DB
        try:
            from app.database import async_session as db_session_factory
            from app.models.dictation import DictationSession
            from sqlalchemy import select
            async with db_session_factory() as db:
                sess = (await db.execute(
                    select(DictationSession).where(DictationSession.id == session_id)
                )).scalar_one_or_none()
                if sess:
                    sess.duration_seconds = int(time.time() - start_time)
                    sess.words_dictated = words_count
                    sess.status = "completed"
                    await db.commit()
        except Exception:
            pass
```

## Conventions
- Binary frames for audio data, text frames for JSON commands
- Handle disconnects gracefully — always clean up ASR session
- Update DB session record on disconnect
