"""WebSocket endpoint for real-time dictation streaming.

Client sends audio chunks (16kHz, 16-bit PCM, 250ms)
Server returns transcript events (partial and final)

Protocol:
  Client -> Server:
    - Binary frames: audio chunk data
    - Text frames: JSON commands {"type": "pause"|"resume"|"end_session"|"set_language", ...}

  Server -> Client:
    - {"type": "partial_transcript", "text": "...", "confidence": 0.8}
    - {"type": "final_transcript", "text": "...", "confidence": 0.95, "words": [...]}
    - {"type": "voice_command", "command": "new paragraph", "action": "new_paragraph"}
    - {"type": "error", "message": "...", "recoverable": true}
    - {"type": "session_metrics", "wpm": 45, "accuracy": 0.92, "duration": 120}
"""

from __future__ import annotations

import contextlib
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/dictation/{session_id}")
async def dictation_ws(websocket: WebSocket, session_id: str) -> None:
    """Bidirectional WebSocket for real-time dictation."""
    await websocket.accept()

    from app.services.voiceforge.asr_engine import ASREngine

    asr = ASREngine()
    session = await asr.start_session(session_id)

    words_count = 0
    start_time = time.time()
    confidence_scores: list[float] = []

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
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "voice_command",
                                    "command": command[0],
                                    "action": command[1],
                                }
                            )
                        )
                        continue

                    if result.is_final:
                        words_count += len(result.text.split())
                        confidence_scores.append(result.confidence)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_transcript",
                                    "text": result.text,
                                    "confidence": result.confidence,
                                    "words": [
                                        {
                                            "word": w.word,
                                            "start_ms": w.start_ms,
                                            "end_ms": w.end_ms,
                                            "confidence": w.confidence,
                                        }
                                        for w in result.words
                                    ],
                                }
                            )
                        )
                    else:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "partial_transcript",
                                    "text": result.text,
                                    "confidence": result.confidence,
                                }
                            )
                        )

            # Text frame = JSON command
            elif "text" in message:
                try:
                    cmd = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                cmd_type = cmd.get("type")

                if cmd_type == "pause":
                    await websocket.send_text(json.dumps({"type": "session_paused"}))

                elif cmd_type == "resume":
                    await websocket.send_text(json.dumps({"type": "session_resumed"}))

                elif cmd_type == "end_session":
                    await _flush_and_send_metrics(
                        websocket,
                        asr,
                        session_id,
                        words_count,
                        confidence_scores,
                        start_time,
                    )
                    break

                elif cmd_type == "set_language":
                    session.language = cmd.get("language", "en")

                elif cmd_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info("Dictation WebSocket disconnected: %s", session_id)
        await asr.end_session(session_id)
    except Exception as exc:
        logger.error("Dictation WebSocket error: %s", exc, exc_info=True)
        with contextlib.suppress(Exception):
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": str(exc),
                        "recoverable": False,
                    }
                )
            )
    finally:
        await asr.close()
        await _update_session_record(session_id, words_count, start_time)


async def _flush_and_send_metrics(
    websocket: WebSocket,
    asr: object,
    session_id: str,
    words_count: int,
    confidence_scores: list[float],
    start_time: float,
) -> None:
    """Process remaining ASR buffer and send session metrics."""
    final = await asr.end_session(session_id)  # type: ignore[union-attr]
    if final and final.text:
        words_count += len(final.text.split())
        confidence_scores.append(final.confidence)
        await websocket.send_text(
            json.dumps(
                {
                    "type": "final_transcript",
                    "text": final.text,
                    "confidence": final.confidence,
                    "words": [
                        {
                            "word": w.word,
                            "start_ms": w.start_ms,
                            "end_ms": w.end_ms,
                            "confidence": w.confidence,
                        }
                        for w in final.words
                    ],
                }
            )
        )

    duration = int(time.time() - start_time)
    wpm = (words_count / duration * 60) if duration > 0 else 0
    avg_accuracy = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    await websocket.send_text(
        json.dumps(
            {
                "type": "session_metrics",
                "wpm": round(wpm, 1),
                "accuracy": round(avg_accuracy, 3),
                "duration": duration,
            }
        )
    )


async def _update_session_record(
    session_id: str,
    words_count: int,
    start_time: float,
) -> None:
    """Persist session statistics to the database."""
    try:
        from sqlalchemy import select

        from app.database import async_session as db_session_factory
        from app.models.dictation import DictationSession

        async with db_session_factory() as db:
            sess = (
                await db.execute(select(DictationSession).where(DictationSession.id == session_id))
            ).scalar_one_or_none()
            if sess:
                sess.duration_seconds = int(time.time() - start_time)
                sess.words_dictated = words_count
                sess.status = "completed"
                await db.commit()
    except Exception:
        logger.warning(
            "Failed to update dictation session record: %s",
            session_id,
            exc_info=True,
        )
