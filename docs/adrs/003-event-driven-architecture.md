# ADR-003: Event-Driven Architecture

**Date**: 2025-06-18
**Status**: Accepted

## Context

SelfPublisherForge consists of 29 modules that need to communicate and react to events across the system. Several cross-cutting concerns drive the need for asynchronous processing and event-driven communication:

- **Long-running operations**: AI content generation (manuscripts, covers, outlines), EPUB/PDF production, multi-platform publishing sync, sentiment analysis, and competitive analysis can take seconds to minutes. These cannot block HTTP request/response cycles.
- **Inter-module reactions**: When a book is created, multiple modules need to react -- the analytics module initializes tracking, the notification module alerts team members, the publishing validation module queues a compliance pre-check. Tight coupling via direct function calls would create a dependency web.
- **Real-time user feedback**: Users need live progress updates during AI generation, agent task execution, and publishing operations. Polling is wasteful and introduces latency.
- **Scheduled operations**: BSR tracking, royalty imports, price optimization, and ad bid adjustments need to run on recurring schedules (hourly, daily).
- **Reliability**: Failed operations (external API timeouts, rate limits) need automatic retry with backoff, dead letter handling, and observability.

We evaluated three approaches for the async task processing and event delivery infrastructure.

### Task Queue alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| **Celery + Redis** | Mature (12+ years), rich feature set (retries, rate limits, chains, chords, canvas), Redis already in stack as cache/rate limiter, large community, Flower monitoring UI | Redis broker has weaker durability guarantees than AMQP, Celery's codebase is large, Python-only |
| **Celery + RabbitMQ** | AMQP provides stronger delivery guarantees, message acknowledgment, routing exchanges | Adds another infrastructure service to deploy/monitor/maintain, team has no RabbitMQ operational experience, overkill for current scale |
| **Dramatiq + Redis** | Simpler API than Celery, good defaults, Redis or RabbitMQ broker | Smaller community, fewer integrations, less battle-tested at scale, no built-in beat scheduler |
| **Huey** | Lightweight, minimal dependencies | Too simple for complex workflows (chains, groups), limited monitoring |

### Event Bus alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| **Redis Streams** | Consumer groups, persistent ordered log, no extra infrastructure (Redis already in stack), low latency, `XACK` for reliable delivery | Limited to Redis memory, no built-in schema registry, less mature than dedicated brokers |
| **Apache Kafka** | Industry-standard event streaming, durable log, partitioning, excellent throughput | Massive operational overhead (ZooKeeper/KRaft, topic management, consumer lag monitoring), overkill for current event volume, requires JVM infrastructure |
| **RabbitMQ (as event bus)** | Flexible routing (exchanges, bindings), message acknowledgment | Another service to operate, pub/sub pattern requires careful exchange configuration, team lacks AMQP expertise |
| **AWS SNS/SQS** | Fully managed, scalable, no infrastructure to maintain | Adds AWS vendor coupling for local development, higher latency than in-process Redis, cost per message at scale |

## Decision

We will use a two-layer asynchronous architecture:

### Layer 1: Celery + Redis for background task processing

All long-running operations are implemented as Celery tasks, organized by feature domain in `backend/app/tasks/`. Redis serves as the Celery broker (message transport) and result backend.

**Task organization** (16 task modules):

- `advertising.py` -- Ad campaign sync, bid optimization, creative generation
- `agent_system.py` -- Agent task execution, governance checks, audit logging
- `analytics.py` -- Revenue aggregation, royalty import, report generation
- `ai_writing.py` -- Manuscript generation, outline creation, editing passes
- `competitor_finder.py` -- Competitive analysis, review scraping, gap detection
- `knowledge_vault.py` -- Document import, AI extraction, search indexing
- `market_intelligence.py` -- BSR tracking, niche analysis, trend computation
- `marketing.py` -- Email sequences, ARC management, social posting
- `notifications.py` -- Email delivery via SendGrid, in-app notification dispatch
- `portfolio_economics.py` -- Backlist analysis, audience profiling, seasonal scoring
- `pricing_automation.py` -- Price strategy execution, KU calculations, simulation
- `production_pipeline.py` -- EPUB/PDF generation, format conversion
- `publishing_ops.py` -- Platform sync, listing updates, distribution
- `review_intelligence.py` -- Sentiment analysis, velocity tracking, alert evaluation
- `style_cloning.py` -- Voice fingerprint extraction, style profile generation
- `dead_letter.py` -- Failed task retry, dead letter queue management

**Celery Beat** runs as a dedicated process for scheduled tasks (hourly BSR checks, daily royalty imports, periodic cleanup).

**Flower** provides a web UI for monitoring task queues, worker status, and task history.

**Reliability configuration**:
- `autoretry_for` with exponential backoff for transient failures (API timeouts, rate limits)
- `max_retries` per task type (typically 3-5)
- Dead letter queue for tasks that exhaust retries
- `acks_late=True` for at-least-once delivery semantics
- `task_reject_on_worker_lost=True` to requeue tasks if a worker crashes

### Layer 2: Redis Streams for inter-module events

Modules publish domain events to Redis Streams, and interested modules subscribe via consumer groups. Event types are defined in `shared/types/events.py` as a typed enumeration.

**Example event flow**:

1. The `books` module creates a new book and publishes `book.created` to the `books` stream.
2. The `analytics` module (consumer group `analytics-cg`) receives the event and initializes sales tracking for the new book.
3. The `notifications` module (consumer group `notifications-cg`) receives the same event and sends a team notification.
4. The `publishing-validation` module (consumer group `pub-validation-cg`) receives the event and queues a background compliance pre-check.

Each consumer group tracks its own position in the stream, enabling independent processing rates and failure recovery. `XACK` confirms processing, and unacknowledged messages are retried.

### Real-time delivery (WebSocket)

For events that need to reach the frontend immediately (AI generation progress, agent task updates, notification delivery), the backend publishes to Redis pub/sub channels. The WebSocket manager (`backend/app/modules/realtime/`) subscribes to relevant channels and pushes typed JSON messages to connected clients.

The frontend WebSocket client (`frontend/src/lib/websocket.ts`) implements auto-reconnect with exponential backoff and typed message handling.

## Consequences

### Positive

- **No additional infrastructure**: Both Celery brokering and Redis Streams use the Redis instance already required for caching and rate limiting. This keeps the local development Docker Compose stack and production AWS infrastructure simple.
- **Battle-tested reliability**: Celery has over a decade of production use, handling retries, rate limiting, task chaining, and monitoring. The failure modes are well-documented and the community is large.
- **Decoupled modules**: Redis Streams enable modules to react to events without direct imports or function calls. Adding a new subscriber to an existing event requires no changes to the publisher.
- **Observability**: Flower provides immediate visibility into task queues, worker health, and task latency. Redis Streams positions and consumer lag are monitorable via the redis-exporter and Prometheus.
- **Flexible scheduling**: Celery Beat supports cron-like schedules, interval-based execution, and solar schedules, covering all recurring task patterns in the platform.
- **Ordered, durable events**: Redis Streams provide ordered, persistent event logs with consumer group semantics. Unlike pub/sub (fire-and-forget), messages survive consumer downtime and are delivered when the consumer reconnects.

### Negative

- **Redis durability limitations**: Redis is primarily an in-memory store. While Redis persistence (RDB snapshots, AOF logging) and AWS ElastiCache multi-AZ mitigate data loss risk, Redis Streams do not provide the same durability guarantees as Kafka or RabbitMQ with disk-backed storage. For the current event volume and criticality level, this tradeoff is acceptable. Critical state is always persisted to PostgreSQL before events are published.
- **No schema registry for events**: Event payloads are validated by convention (Python dataclasses/Pydantic models in `shared/types/events.py`) rather than by a formal schema registry. A mismatch between publisher and subscriber event schemas would cause runtime errors. This is mitigated by shared type definitions and integration tests.
- **Celery complexity**: Celery's configuration surface is large, and debugging task failures across worker processes requires familiarity with its internals (prefetch multiplier, visibility timeout, task serialization). New team members face a learning curve.
- **Python-only task workers**: Celery workers must be Python processes. If a future module requires a non-Python worker (e.g., for GPU-accelerated processing), a separate task execution mechanism would be needed.
- **Redis memory pressure**: Redis Streams and Celery broker queues consume Redis memory. High task volume or slow consumers could increase memory usage. This is monitored via redis-exporter metrics and mitigated by stream trimming (`MAXLEN`) and Celery's `task_default_queue` TTL settings.
- **Eventual consistency**: Inter-module communication via events is inherently eventually consistent. Modules may briefly see stale state after an event is published but before it is processed. The API layer and frontend handle this by designing UIs that expect and display in-progress states.
