"""WebSocket endpoints for the four real-time channels.

Each endpoint:
1. Authenticates the connection via a ``token`` query parameter (JWT).
2. Registers the WebSocket with the global ``ConnectionManager``.
3. Relays incoming client messages to the room via ``broadcast``.
4. Cleans up on disconnect.

The router is importable and can be registered on the FastAPI app via::

    from app.modules.realtime.router import router as realtime_router
    app.include_router(realtime_router)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.config import get_settings
from app.core.security import decode_token
from app.modules.realtime.manager import ConnectionManager
from app.modules.realtime.schemas import WSChannel

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level singleton.  ``startup`` / ``shutdown`` events wire it up
# with Redis when the application boots.
manager = ConnectionManager(redis_url=get_settings().REDIS_URL)


# ---------------------------------------------------------------------------
# HTTP health-check so the "realtime" tag appears in the OpenAPI spec
# (WebSocket-only routes are excluded from the spec by default).
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/ws/status",
    summary="WebSocket subsystem status",
    description="Return status information for the WebSocket subsystem including active channels and rooms.",
)
async def ws_status() -> dict[str, Any]:
    """Return basic status information for the WebSocket subsystem."""
    return {
        "status": "ok",
        "channels": [ch.value for ch in WSChannel],
        "rooms": manager.get_all_rooms(),
    }


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _authenticate_ws(token: str | None) -> dict[str, Any]:
    """Validate a JWT from the WebSocket query string.

    Returns the decoded payload dict on success or raises ``ValueError``.
    """
    if not token:
        raise ValueError("Missing authentication token")
    payload = decode_token(token)  # raises ValueError on bad token
    if not payload.get("sub"):
        raise ValueError("Token missing subject")
    return payload


# ---------------------------------------------------------------------------
# Generic handler
# ---------------------------------------------------------------------------

async def _ws_handler(
    websocket: WebSocket,
    channel: WSChannel,
    room_id: str,
    token: str | None,
) -> None:
    """Shared logic for all WebSocket endpoints."""
    # Authenticate
    try:
        user = _authenticate_ws(token)
    except ValueError as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        return

    # Connect
    await manager.connect(websocket, channel, room_id)

    # Send a welcome message with connection metadata
    await manager.send_personal(websocket, {
        "type": "connected",
        "channel": channel.value,
        "room_id": room_id,
        "user_id": user.get("sub"),
    })

    try:
        while True:
            data = await websocket.receive_json()
            # Client messages are broadcast to the room
            data.setdefault("user_id", user.get("sub"))
            await manager.broadcast(channel, room_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, channel, room_id)
    except ConnectionError as exc:
        logger.error(
            "Connection lost on WebSocket: channel=%s room=%s — %s",
            channel.value, room_id, exc,
        )
        await manager.disconnect(websocket, channel, room_id)
    except RuntimeError as exc:
        logger.error(
            "Runtime error on WebSocket: channel=%s room=%s — %s",
            channel.value, room_id, exc,
        )
        await manager.disconnect(websocket, channel, room_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.websocket("/api/v1/ws/writing/{book_id}")
async def ws_writing(
    websocket: WebSocket,
    book_id: str,
    token: str | None = Query(default=None),
) -> None:
    """Live writing collaboration: cursor_move, text_change, ai_suggestion, save_ack."""
    await _ws_handler(websocket, WSChannel.WRITING, book_id, token)


@router.websocket("/api/v1/ws/agents/{org_id}")
async def ws_agents(
    websocket: WebSocket,
    org_id: str,
    token: str | None = Query(default=None),
) -> None:
    """Agent status updates: task_started, task_progress, task_completed, task_failed, budget_alert."""
    await _ws_handler(websocket, WSChannel.AGENTS, org_id, token)


@router.websocket("/api/v1/ws/analytics/{org_id}")
async def ws_analytics(
    websocket: WebSocket,
    org_id: str,
    token: str | None = Query(default=None),
) -> None:
    """Analytics dashboard updates: metric_update, alert_triggered, report_ready."""
    await _ws_handler(websocket, WSChannel.ANALYTICS, org_id, token)


@router.websocket("/api/v1/ws/publishing/{book_id}")
async def ws_publishing(
    websocket: WebSocket,
    book_id: str,
    token: str | None = Query(default=None),
) -> None:
    """Publishing pipeline status: validation_progress, upload_progress, listing_synced."""
    await _ws_handler(websocket, WSChannel.PUBLISHING, book_id, token)


@router.websocket("/api/v1/ws/audiobook/{project_id}")
async def ws_audiobook(
    websocket: WebSocket,
    project_id: str,
    token: str | None = Query(default=None),
) -> None:
    """Audiobook generation progress.

    Events: chapter_generation_started/progress/complete/failed,
    mastering_progress/complete, validation_complete, cost_update.
    """
    await _ws_handler(websocket, WSChannel.AUDIOBOOK, project_id, token)
