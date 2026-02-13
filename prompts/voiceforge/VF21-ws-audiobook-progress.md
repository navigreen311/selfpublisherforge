# VF21: WebSocket Handler — Audiobook Progress

## Task
Create WebSocket endpoint for real-time audiobook generation progress updates.

## Context
- Check existing WebSocket setup in `backend/app/modules/realtime/`
- The project uses Redis pub/sub for real-time events
- WebSocket events are published by Celery tasks (VF19/VF20)

## Files to Create/Modify

### Add WebSocket endpoint for audiobook

Look at the existing `realtime` module pattern and add an audiobook WebSocket handler.

If the realtime module uses a `ConnectionManager`, add a new channel handler.

Otherwise create: `backend/app/modules/audiobook/websocket.py`

```python
"""WebSocket endpoint for audiobook generation progress."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.dependencies import get_current_user_ws  # or similar WS auth

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/audiobooks/{project_id}/status")
async def audiobook_status_ws(websocket: WebSocket, project_id: str):
    """WebSocket for real-time audiobook generation progress.

    Subscribes to Redis pub/sub channel: audiobook:{project_id}:events
    Forwards all events to the connected client.

    Events:
    - chapter_generation_started: {chapter_id, chapter_number}
    - chapter_generation_progress: {chapter_id, percent, stage, eta_seconds}
    - chapter_generation_complete: {chapter_id, audio_url, duration_seconds, cost_usd, quality_metrics}
    - chapter_generation_failed: {chapter_id, error, retry_available}
    - mastering_progress: {percent, stage}
    - mastering_complete: {master_url, total_duration, total_cost}
    - validation_complete: {results}
    - cost_update: {chapter_id, cost_usd, total_cost, budget_remaining}
    """
    await websocket.accept()

    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        settings = get_settings()

        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        channel = f"audiobook:{project_id}:events"
        await pubsub.subscribe(channel)

        logger.info("WebSocket connected for audiobook %s", project_id)

        # Listen for events and forward to client
        async def listen_redis():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    await websocket.send_text(data)

        # Also handle client messages (e.g., ping)
        async def listen_client():
            while True:
                try:
                    msg = await websocket.receive_text()
                    # Handle client-side messages if needed
                    if msg == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except WebSocketDisconnect:
                    break

        # Run both listeners concurrently
        await asyncio.gather(listen_redis(), listen_client(), return_exceptions=True)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for audiobook %s", project_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        if pubsub:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        await r.aclose()
```

## Conventions
- Use the project's existing Redis connection pattern
- WebSocket auth may use query param token or first message auth
- Handle disconnection gracefully
- Log connection/disconnection events
