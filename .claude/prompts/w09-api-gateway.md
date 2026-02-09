# W09: API Gateway Middleware
**Branch:** `ai-feature/api-gateway`
**Scope:** api

## Mission
Implement API gateway functionality: request validation, rate limiting, API versioning, request/response logging, CORS, OpenAPI documentation enhancement, and health monitoring.

## What to Build

### Backend
1. **backend/app/core/rate_limit.py** — Redis-based rate limiter:
   - Sliding window algorithm
   - Tier-based limits: Free (60/min), Pro (300/min), Enterprise (1000/min)
   - Response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
   - Endpoint-specific overrides (e.g., AI generation has lower limits)

2. **backend/app/core/middleware.py** — Middleware stack:
   - RequestTimingMiddleware — Add X-Response-Time header
   - CorrelationIDMiddleware — Generate/propagate X-Request-ID
   - RequestLoggingMiddleware — Log method, path, status, duration, user_id
   - SecurityHeadersMiddleware — HSTS, CSP, X-Frame-Options, X-Content-Type-Options

3. **backend/app/core/logging.py** — Structured JSON logging:
   - Configure Python logging with JSON formatter
   - Include correlation_id, user_id, org_id in all log entries
   - Log levels: DEBUG/INFO for dev, WARNING+ for prod
   - Request/response body logging (sanitized — strip passwords, tokens)

4. **backend/app/api/v1/health.py** — Enhanced health endpoints:
   - GET /health — Basic health (for load balancers)
   - GET /health/ready — Readiness (DB, Redis, Elasticsearch connectivity)
   - GET /health/detailed — Full health with version, uptime, dependency status (admin only)

5. **backend/app/core/error_handler.py** — Global error handlers:
   - AppException handler -> JSON error envelope
   - ValidationError handler -> 422 with field details
   - 404 handler
   - 500 handler with request_id for debugging

6. **backend/app/core/versioning.py** — API versioning utilities for future v2 support

### Tests
7. **backend/tests/unit/test_rate_limit.py** — Test sliding window, tier limits, header injection
8. **backend/tests/unit/test_middleware.py** — Test correlation ID, timing, security headers
9. **backend/tests/integration/test_health.py** — Test health endpoints

## Database Tables Used
- None directly (uses Redis for rate limiting state)

## Dependencies
- Uses: backend/app/config.py (read-only, for Redis URL, environment settings)
- Uses: backend/app/database.py (read-only, for health check DB connection)
- External: redis-py, python-json-logger

## Important Notes
- W01 may also create rate_limit.py, logging.py, and middleware.py. Coordinate: if W01 creates placeholder files, W09 should REPLACE the content with full implementations. If W01 has not run yet, create these files from scratch.
- The router in health.py should be importable and registerable in main.py during integration.

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
`feat(gateway): implement API gateway middleware with rate limiting, logging, and health checks`
