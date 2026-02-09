# W11: Celery Task Queue & Event Bus
**Branch:** `ai-feature/task-queue-events`
**Scope:** infra

## Mission
Implement the async task processing infrastructure: Celery configuration, task routing, event bus (Redis Streams), dead letter queue, retry policies, and monitoring integration.

## What to Build

### Backend
1. **backend/app/tasks/config.py** — Enhanced Celery configuration:
   - Task routing: ai_tasks -> ai_queue, email_tasks -> email_queue, file_tasks -> file_queue, analytics_tasks -> analytics_queue
   - Priority queues (high, default, low)
   - Retry policies: exponential backoff, max retries per task type
   - Result backend configuration
   - Task serialization and deserialization

2. **backend/app/tasks/base.py** — Base task classes:
   - TrackedTask — logs start/end/error, tracks duration, injects correlation ID
   - OrgScopedTask — includes org_id context for multi-tenant tasks
   - AITask — includes token tracking, cost calculation, budget checking

3. **backend/app/tasks/scheduler.py** — Celery Beat schedule:
   - Market data refresh (every 6h)
   - Analytics aggregation (daily at 2am UTC)
   - KDP health check (every 4h)
   - Stale session cleanup (daily)
   - Usage meter reset (monthly)

4. **backend/app/core/events.py** — Event bus implementation:
   - RedisEventPublisher implementing shared EventPublisher interface
   - publish_event(event: BaseEvent) — Write to Redis Stream
   - subscribe_events(event_types: list[EventType], callback) — Consumer group
   - Event replay capability for debugging
   - Dead letter handling for failed events

5. **backend/app/tasks/dead_letter.py** — Dead letter queue:
   - Store failed tasks/events for manual retry
   - Admin API for viewing and retrying dead letters

### Tests
6. **backend/tests/unit/test_task_base.py** — Test TrackedTask, OrgScopedTask
7. **backend/tests/unit/test_event_bus.py** — Test event publishing, subscribing, dead letter

## Commit Convention
`feat(tasks): implement Celery task queue with event bus and dead letter handling`
