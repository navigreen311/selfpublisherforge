"""Realtime Service

Thin service layer that delegates to the ConnectionManager for WebSocket
operations. Provides a consistent module interface matching other backend modules.
"""

from __future__ import annotations

import logging
from typing import Any

from app.modules.realtime.manager import connection_manager
from app.modules.realtime.schemas import WSChannel

logger = logging.getLogger(__name__)


class RealtimeService:
    """Service wrapper around the WebSocket ConnectionManager.

    Covers what the manager actually provides. Per-user delivery
    (send_to_user / disconnect_user) is not here because the manager
    keys connections by channel and room, not by user; both wrappers
    called signatures that do not exist.
    """

    async def broadcast_to_channel(self, channel: WSChannel, room_id: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all connections in a channel/room."""
        await connection_manager.broadcast(channel, room_id, message)

    async def get_active_connections(self, channel: WSChannel, room_id: str) -> int:
        """Return the number of active connections in a channel/room."""
        return connection_manager.get_connection_count(channel, room_id)


realtime_service = RealtimeService()
