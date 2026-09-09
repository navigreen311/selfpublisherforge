"""WebSocket endpoint for audiobook generation progress.

Subscribes to Redis pub/sub channel for a specific audiobook project
and relays generation progress events to the client in real time.

Events:
  - chapter_generation_started: {chapter_id, chapter_number}
  - chapter_generation_progress: {chapter_id, percent, stage}
  - chapter_generation_complete: {chapter_id, duration_seconds, audio_url}
  - chapter_generation_failed: {chapter_id, error}
  - mastering_progress: {percent, stage}
  - mastering_complete: {master_audio_url}
  - validation_complete: {passed, issues}
  - cost_update: {total_cost_usd, provider}
"""

from __future__ import annotations

import contextlib
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.config import get_settings
from app.core.security import decode_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/audiobook/{project_id}")
async def audiobook_progress_ws(
    websocket: WebSocket,
    project_id: str,
    token: str | None = Query(default=None),
) -> None:
    """Stream audiobook generation progress events via Redis pub/sub."""
    # Authenticate
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return
    try:
        payload = decode_token(token)
        if not payload.get("sub"):
            raise ValueError("Token missing subject")
    except (ValueError, Exception) as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        return

    await websocket.accept()
    logger.info("Audiobook WS connected: project=%s user=%s", project_id, payload.get("sub"))

    # Subscribe to Redis pub/sub for this project
    import redis.asyncio as aioredis

    redis = aioredis.from_url(get_settings().REDIS_URL)
    channel_name = f"audiobook:progress:{project_id}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel_name)

    try:
        while True:
            # Check for messages from Redis
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                await websocket.send_text(data)

            # Check for client messages (ping/disconnect)
            with contextlib.suppress(Exception):
                client_msg = await websocket.receive_text()
                cmd = json.loads(client_msg)
                if cmd.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        logger.info("Audiobook WS disconnected: project=%s", project_id)
    except Exception as exc:
        logger.error("Audiobook WS error: %s", exc, exc_info=True)
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
        await redis.close()
