"""ConnectionManager: tracks WebSocket connections, broadcasts messages, and
bridges to Redis pub/sub for multi-instance fanout."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.modules.realtime.schemas import WSChannel

logger = logging.getLogger(__name__)

# Redis is optional at import time so the module stays testable without a live
# Redis instance.
try:
    import redis.asyncio as aioredis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]


def _channel_key(channel: WSChannel, room_id: str) -> str:
    """Return the Redis pub/sub channel key for a given channel + room."""
    return f"ws:{channel.value}:{room_id}"


class ConnectionManager:
    """Manages WebSocket connections, per-room broadcasting, and Redis pub/sub.

    * ``active_connections`` maps ``(channel, room_id)`` -> set of WebSocket
      instances.
    * When *redis_url* is supplied, published messages are fanned out through
      Redis so that every backend instance can relay them to its local clients.
    * A background heartbeat (ping) task keeps connections alive.
    """

    def __init__(self, redis_url: str | None = None, heartbeat_interval: float = 30.0) -> None:
        # (channel, room_id) -> set[WebSocket]
        self.active_connections: dict[tuple[WSChannel, str], set[WebSocket]] = {}
        self._redis_url = redis_url
        self._redis: Any | None = None
        self._pubsub: Any | None = None
        self._listener_task: asyncio.Task[None] | None = None
        self._subscriber_channels: set[str] = set()
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    async def _get_redis(self) -> Any | None:
        """Lazily initialise the Redis client."""
        if aioredis is None or self._redis_url is None:
            return None
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def _ensure_subscribed(self, channel_key: str) -> None:
        """Subscribe to *channel_key* on Redis if not already subscribed."""
        redis = await self._get_redis()
        if redis is None:
            return
        if channel_key in self._subscriber_channels:
            return
        if self._pubsub is None:
            self._pubsub = redis.pubsub()
        await self._pubsub.subscribe(channel_key)
        self._subscriber_channels.add(channel_key)
        # Start the listener loop if it is not running yet.
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._redis_listener())

    async def _redis_listener(self) -> None:
        """Background task: read messages from Redis pub/sub and relay them to
        local WebSocket connections."""
        if self._pubsub is None:
            return
        try:
            async for raw_message in self._pubsub.listen():
                if raw_message["type"] != "message":
                    continue
                try:
                    payload: dict[str, Any] = json.loads(raw_message["data"])
                    channel = WSChannel(payload["channel"])
                    room_id: str = payload["room_id"]
                    await self._local_broadcast(channel, room_id, payload)
                except Exception:
                    logger.exception("Error processing Redis pub/sub message")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Redis listener crashed")

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        """Periodically ping every connected WebSocket."""
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval)
                for key, sockets in list(self.active_connections.items()):
                    dead: list[WebSocket] = []
                    for ws in list(sockets):
                        try:
                            await ws.send_json({"type": "ping", "ts": datetime.now(timezone.utc).isoformat()})
                        except Exception:
                            dead.append(ws)
                    for ws in dead:
                        sockets.discard(ws)
                    if not sockets:
                        self.active_connections.pop(key, None)
        except asyncio.CancelledError:
            pass

    def _ensure_heartbeat(self) -> None:
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket, channel: WSChannel, room_id: str) -> None:
        """Accept *websocket* and register it under *(channel, room_id)*."""
        await websocket.accept()
        key = (channel, room_id)
        if key not in self.active_connections:
            self.active_connections[key] = set()
        self.active_connections[key].add(websocket)

        # Ensure Redis subscription for this room.
        channel_key = _channel_key(channel, room_id)
        await self._ensure_subscribed(channel_key)

        # Start heartbeat if not running.
        self._ensure_heartbeat()

        logger.info("WS connected: channel=%s room=%s", channel.value, room_id)

    async def disconnect(self, websocket: WebSocket, channel: WSChannel, room_id: str) -> None:
        """Remove *websocket* from the room and clean up empty rooms."""
        key = (channel, room_id)
        conns = self.active_connections.get(key)
        if conns is not None:
            conns.discard(websocket)
            if not conns:
                self.active_connections.pop(key, None)
        logger.info("WS disconnected: channel=%s room=%s", channel.value, room_id)

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def _local_broadcast(self, channel: WSChannel, room_id: str, message: dict[str, Any]) -> None:
        """Send *message* to every local WebSocket in the room."""
        key = (channel, room_id)
        conns = self.active_connections.get(key)
        if not conns:
            return
        dead: list[WebSocket] = []
        for ws in list(conns):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
                else:
                    dead.append(ws)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.discard(ws)

    async def broadcast(self, channel: WSChannel, room_id: str, message: dict[str, Any]) -> None:
        """Broadcast *message* to all connections in the room.

        If Redis is available the message is published there so that all
        backend instances relay it; otherwise it is sent locally only.
        """
        # Ensure envelope fields
        message.setdefault("channel", channel.value)
        message.setdefault("room_id", room_id)
        message.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        redis = await self._get_redis()
        if redis is not None:
            channel_key = _channel_key(channel, room_id)
            await redis.publish(channel_key, json.dumps(message, default=str))
        else:
            await self._local_broadcast(channel, room_id, message)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a single WebSocket connection."""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
        except Exception:
            logger.warning("Failed to send personal message")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_connection_count(self, channel: WSChannel, room_id: str) -> int:
        """Return the number of active connections in the specified room."""
        key = (channel, room_id)
        conns = self.active_connections.get(key)
        return len(conns) if conns else 0

    def get_all_rooms(self) -> list[tuple[str, str, int]]:
        """Return a list of ``(channel, room_id, connection_count)`` tuples."""
        return [
            (ch.value, rid, len(conns))
            for (ch, rid), conns in self.active_connections.items()
            if conns
        ]

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Gracefully tear down background tasks and Redis resources."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub is not None:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        if self._redis is not None:
            await self._redis.close()
