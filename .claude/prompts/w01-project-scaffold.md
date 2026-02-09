# W01: Project Scaffold, Shared Types & Configuration
**Branch:** `ai-feature/project-scaffold`
**Scope:** infra

## Mission
Set up the complete project configuration, linting, formatting, type checking, and shared type definitions that all other modules depend on.

## What to Build

### Backend
1. **backend/pyproject.toml** — Ruff linter config, pytest config, project metadata
2. **backend/app/core/rate_limit.py** — Rate limiting middleware using Redis (60/min free, 300/min pro, 1000/min enterprise)
3. **backend/app/core/logging.py** — Structured JSON logging setup with correlation IDs
4. **backend/app/core/middleware.py** — Request logging middleware, timing middleware, correlation ID injection
5. **backend/app/schemas/requests.py** — Common request schemas (SortParams, FilterParams, DateRangeFilter, BulkActionRequest)
6. **backend/app/schemas/responses.py** — Common response schemas (ErrorResponse envelope, SuccessResponse, BulkActionResponse)

### Frontend
7. **frontend/src/types/api.ts** — TypeScript types mirroring all backend Pydantic schemas (error responses, pagination, common enums)
8. **frontend/src/types/modules.ts** — TypeScript interfaces for each module's data types (MarketData, StyleProfile, Campaign, Agent, etc.)
9. **frontend/src/lib/websocket.ts** — WebSocket client utility with auto-reconnect, typed message handling
10. **frontend/src/hooks/use-api.ts** — Generic React Query hooks: useApiQuery, useApiMutation, useApiInfinite with error handling

### Shared
11. **shared/types/enums.py** — All platform enums (PlanTier, UserRole, BookFormat, BookStatus, ProjectType, CampaignStatus, AgentType, etc.)
12. **shared/contracts/module_registry.py** — Registry of all 29 modules with metadata (name, tier, dependencies, API prefix)

### Tests
13. **backend/tests/conftest.py** — Pytest fixtures: async test client, test database, mock Redis, test user factory
14. **backend/tests/unit/test_core_middleware.py** — Tests for rate limiting, logging, correlation IDs

### Docs
15. **docs/architecture.md** — Module dependency map, tier diagram, communication patterns (from blueprint)

## Read-Only Files (do NOT modify)
- backend/app/main.py, config.py, database.py
- backend/app/core/security.py, dependencies.py, exceptions.py, pagination.py
- All frontend layout files, providers, lib/utils.ts, lib/api.ts
- frontend/src/types/index.ts
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
Use `chore:` prefix for config, `feat:` for new utilities, `docs:` for documentation.
