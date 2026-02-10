# ADR-001: Tech Stack Selection

**Date**: 2025-06-15
**Status**: Accepted

## Context

SelfPublisherForge is an AI-powered self-publishing platform with 29 integrated modules spanning writing, publishing, marketing, analytics, and AI automation. The platform must support:

- **High concurrency**: Multiple long-running AI generation requests, background task processing, and real-time WebSocket connections running simultaneously.
- **Rapid feature development**: A small team needs to ship 29 modules covering diverse domains (billing, NLP, advertising, analytics) without excessive boilerplate.
- **Type safety across the stack**: With a large surface area of API contracts, schemas, and data models, runtime errors from type mismatches are costly.
- **SEO and performance for public pages**: Book landing pages, marketing pages, and the documentation site benefit from server-side rendering.
- **Mature ecosystem**: The platform integrates with Stripe, SendGrid, AWS services, Anthropic, and OpenAI -- requiring well-maintained client libraries.
- **Relational data integrity**: The domain model has deep relationships (organizations, users, projects, books, chapters, campaigns, analytics) with complex queries, aggregations, and transactional requirements.

We evaluated several combinations of backend framework, ORM, frontend framework, and database.

### Backend alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI (Python)** | Async-native, automatic OpenAPI/Swagger docs, Pydantic validation, rich AI/ML library ecosystem | Python GIL limits CPU-bound work (mitigated by Celery workers) |
| **Django + DRF** | Batteries-included (admin, ORM, auth), large community | Synchronous by default, async support still maturing, heavier ORM opinions |
| **Express/NestJS (Node.js)** | Single language across stack, strong async I/O | Weaker AI/ML ecosystem, less mature type validation without additional libraries |

### Frontend alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| **Next.js 14 (App Router)** | SSR/SSG/ISR, React Server Components, file-based routing, excellent DX | App Router still maturing, some ecosystem libraries lag behind |
| **Remix** | Excellent data loading patterns, progressive enhancement | Smaller ecosystem, fewer UI component libraries |
| **SPA (Vite + React)** | Simple, fast dev server, full client-side control | No SSR out of the box, poor SEO for public pages, requires separate API proxy |

### Database alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| **PostgreSQL** | ACID, JSON columns, full-text search, mature async drivers (asyncpg), rich indexing | Requires more ops than managed NoSQL |
| **MySQL** | Widespread, good tooling | Weaker JSON support, fewer advanced index types, no native array columns |
| **MongoDB** | Flexible schema, fast prototyping | No ACID transactions across documents (pre-5.0), poor fit for relational domain model |

### ORM alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| **SQLAlchemy 2.0 (async)** | Mature, type-safe `mapped_column`, async session support, Alembic migrations | Steeper learning curve than lighter ORMs |
| **Tortoise ORM** | Django-like, async-first | Smaller community, fewer escape hatches for complex queries |
| **Raw asyncpg** | Maximum performance, full control | No migration tooling, manual schema mapping, maintenance burden |

## Decision

We will use the following technology stack:

- **Backend**: Python 3.12+ with FastAPI as the web framework and SQLAlchemy 2.0 (async mode) as the ORM, with Alembic for database migrations.
- **Frontend**: Next.js 14 using the App Router with TypeScript, React 18, TanStack React Query (server state), Zustand (client state), Tailwind CSS, and shadcn/ui components.
- **Database**: PostgreSQL 16 as the primary relational database.
- **Cache / Broker**: Redis 7 for caching, rate limiting, pub/sub event streaming, and Celery task brokering.

### Rationale

**FastAPI + async Python** was chosen because:

1. Python's AI/ML ecosystem is unmatched. Direct integration with Anthropic, OpenAI, and NLP libraries (used by style cloning, sentiment analysis, and content generation) is first-class.
2. FastAPI's automatic OpenAPI documentation eliminates the need to maintain a separate API spec for 29 modules. Pydantic schemas serve as both validation and documentation.
3. Native `async/await` support handles concurrent I/O-bound workloads (database queries, external API calls, WebSocket connections) efficiently. CPU-bound tasks are offloaded to Celery workers.
4. Python 3.12 brings performance improvements (specializing adaptive interpreter) and better error messages, reducing debugging time.

**SQLAlchemy 2.0 async** was chosen because:

1. The 2.0 API with `mapped_column` and type annotations provides IDE autocompletion and static analysis support across all 29 module models.
2. Alembic's autogenerate capability accelerates schema evolution -- critical when iterating rapidly on a large domain model.
3. SQLAlchemy's escape hatches (raw SQL, hybrid properties, custom types) handle the complex analytics queries required by portfolio economics and revenue tracking.

**Next.js 14 App Router** was chosen because:

1. React Server Components reduce client-side JavaScript for data-heavy dashboard pages (analytics, revenue reports), improving perceived performance.
2. File-based routing with layouts and loading states maps naturally to the platform's nested navigation (dashboard > module > detail).
3. SSR is essential for public-facing pages (book landing pages, marketing site) to ensure SEO indexing.
4. The React ecosystem offers the widest selection of UI component libraries. shadcn/ui provides accessible, customizable primitives that integrate with Tailwind CSS.

**PostgreSQL 16** was chosen because:

1. The domain model is deeply relational: organizations have users, projects, books, chapters, campaigns, analytics events, and billing records. PostgreSQL's ACID guarantees and foreign key constraints enforce data integrity at the database level.
2. JSONB columns provide schema flexibility where needed (AI generation parameters, marketplace-specific metadata) without sacrificing query performance.
3. PostgreSQL's advanced indexing (GIN for full-text search, GiST for range queries, partial indexes) supports the diverse query patterns across 29 modules.
4. The `asyncpg` driver is the fastest Python PostgreSQL driver, aligning with FastAPI's async architecture.

**Redis 7** was chosen because it consolidates four infrastructure needs (cache, rate limiter, event bus, task broker) into a single service, reducing operational complexity and latency. Redis Streams provide durable, ordered event delivery with consumer groups, replacing the need for a separate message broker for inter-module events.

## Consequences

### Positive

- **Unified AI ecosystem**: Python's dominance in AI/ML means all LLM providers, NLP libraries, and data processing tools have first-class Python SDKs. No FFI or subprocess overhead.
- **Automatic API documentation**: FastAPI generates interactive Swagger UI and ReDoc for all 29 modules' endpoints, reducing onboarding friction for frontend developers and external integrators.
- **Type safety end-to-end**: Pydantic schemas (backend) and TypeScript (frontend) catch contract mismatches at build time. Shared type contracts in `shared/types/` further reduce drift.
- **Flexible rendering**: Next.js App Router supports SSR, SSG, ISR, and client-side rendering per route, allowing optimization based on each page's characteristics.
- **Simplified infrastructure**: Redis serving four roles (cache, rate limiter, event bus, task broker) means one fewer service to deploy, monitor, and maintain.
- **Strong migration tooling**: Alembic autogenerate + SQLAlchemy 2.0 mapped columns makes schema changes trackable and reversible.

### Negative

- **Two-language stack**: Python (backend) and TypeScript (frontend) require developers to be proficient in both. There is no shared code execution between server and client (unlike a full-stack JS framework).
- **Python GIL for CPU-bound work**: CPU-intensive operations (NLP processing, PDF generation) cannot be parallelized within a single process. This is mitigated by offloading to Celery workers, but adds architectural complexity.
- **App Router maturity**: Next.js 14 App Router introduced breaking changes from the Pages Router. Some third-party libraries and patterns have not fully adapted, occasionally requiring workarounds.
- **Redis as single point of failure**: Redis serves four critical roles. A Redis outage would impact caching, rate limiting, event delivery, and background task processing simultaneously. This is mitigated in production by using AWS ElastiCache with multi-AZ failover.
- **SQLAlchemy learning curve**: SQLAlchemy 2.0's dual legacy/modern API can confuse developers new to the library. The async session pattern requires care around lazy loading and session lifecycle.
