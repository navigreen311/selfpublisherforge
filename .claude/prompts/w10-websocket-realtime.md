# W10: WebSocket & Real-time Event System
**Branch:** `ai-feature/websocket-realtime`
**Scope:** api

## Mission
Implement WebSocket server infrastructure for real-time features: live writing collaboration, agent status updates, analytics dashboard updates, and publishing pipeline status.

## WebSocket Channels (from blueprint)
- ws://api/v1/ws/writing/{book_id} — cursor_move, text_change, ai_suggestion, save_ack
- ws://api/v1/ws/agents/{org_id} — task_started, task_progress, task_completed, task_failed, budget_alert
- ws://api/v1/ws/analytics/{org_id} — metric_update, alert_triggered, report_ready
- ws://api/v1/ws/publishing/{book_id} — validation_progress, upload_progress, listing_synced

## What to Build

### Backend
1. **backend/app/modules/realtime/__init__.py**
2. **backend/app/modules/realtime/manager.py** — ConnectionManager class:
   - Track active connections by channel + room_id
   - Broadcast to all connections in a room
   - Send to specific connection
   - Redis pub/sub for multi-instance support
   - Connection authentication via JWT in query params
   - Heartbeat/ping-pong for connection health

3. **backend/app/modules/realtime/router.py** — WebSocket endpoints:
   - WS /api/v1/ws/writing/{book_id}
   - WS /api/v1/ws/agents/{org_id}
   - WS /api/v1/ws/analytics/{org_id}
   - WS /api/v1/ws/publishing/{book_id}

4. **backend/app/modules/realtime/schemas.py** — WebSocket message types:
   - WSMessage(type, channel, room_id, data, timestamp)
   - Typed event schemas for each channel

5. **backend/app/modules/realtime/events.py** — Event publisher:
   - publish_to_channel(channel, room_id, event) — Push event to Redis pub/sub
   - subscribe_to_channel(channel, room_id) — Listen to Redis pub/sub
   - Integration with shared/types/events.py EventPublisher interface

### Frontend
6. **frontend/src/lib/websocket.ts** — REPLACE placeholder with full implementation:
   - WebSocketManager class with auto-reconnect, exponential backoff
   - Channel subscription/unsubscription
   - Typed message handlers
   - Connection state management (connecting, connected, disconnected, error)

7. **frontend/src/hooks/use-websocket.ts** — React hook wrapping WebSocketManager:
   - useWebSocket(channel, roomId) — returns { isConnected, lastMessage, sendMessage }
   - Auto-connect on mount, disconnect on unmount

### Tests
8. **backend/tests/unit/test_ws_manager.py** — Test connection tracking, broadcast, Redis pub/sub
9. **backend/tests/integration/test_websocket.py** — Test WebSocket endpoints with test client

## Database Tables Used
- None directly (stateless, uses Redis for pub/sub and connection tracking)

## Dependencies
- Uses: backend/app/core/security.py (read-only, for JWT validation of WebSocket connections)
- Uses: backend/app/config.py (read-only, for Redis URL)
- External: redis-py (for pub/sub), websockets

## Important Notes
- W01 may create a placeholder frontend/src/lib/websocket.ts. If it exists, W10 should REPLACE the content with the full implementation.
- The router in router.py should be importable and registerable in main.py during integration.
- WebSocket authentication: extract JWT from query parameter `?token=xxx`, validate using the same logic as HTTP auth.

## Read-Only (do NOT modify)
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/core/security.py
- backend/app/core/dependencies.py
- backend/app/core/exceptions.py
- backend/app/core/pagination.py
- backend/app/schemas/common.py
- frontend/src/app/layout.tsx
- frontend/src/components/providers.tsx
- frontend/src/lib/utils.ts
- frontend/src/lib/api.ts
- frontend/src/types/index.ts
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
`feat(realtime): implement WebSocket server with Redis pub/sub for real-time events`
