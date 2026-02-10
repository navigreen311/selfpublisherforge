# Contributing to SelfPublisherForge

Thank you for your interest in contributing to SelfPublisherForge! We welcome contributions from developers of all experience levels. This guide will help you get started and ensure a smooth collaboration process.

Please review and follow our [Code of Conduct](CODE_OF_CONDUCT.md) in all interactions within the project. We are committed to maintaining a respectful, inclusive, and harassment-free community.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Architecture Overview](#architecture-overview)
- [Testing Guide](#testing-guide)
- [Issue Reporting](#issue-reporting)
- [Pull Request Process](#pull-request-process)
- [Review Process](#review-process)

---

## Getting Started

### Prerequisites

Ensure the following tools are installed on your machine before you begin:

| Tool | Minimum Version | Purpose |
|---|---|---|
| **Node.js** | 18+ (20+ recommended) | Frontend development |
| **Python** | 3.12+ | Backend development |
| **Docker** | Latest stable | Containerized services |
| **Docker Compose** | v2+ | Multi-service orchestration |
| **Git** | Latest stable | Version control |

### Fork and Clone

1. **Fork** the repository on GitHub by clicking the "Fork" button on the [SelfPublisherForge repo](https://github.com/navigreen311/selfpublisherforge).

2. **Clone** your fork locally:

   ```bash
   git clone https://github.com/<your-username>/selfpublisherforge.git
   cd selfpublisherforge
   ```

3. **Add the upstream remote** so you can pull future changes:

   ```bash
   git remote add upstream https://github.com/navigreen311/selfpublisherforge.git
   git fetch upstream
   ```

### Development Setup

The fastest way to get the full stack running locally is with Docker Compose:

```bash
# Start all services (backend, frontend, PostgreSQL, Redis, Elasticsearch, Celery, etc.)
docker compose up --build -d
```

Once running, the services will be available at:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Flower (Celery monitor) | http://localhost:5555 |

#### Environment Configuration

1. **Backend**: Copy the example environment file and fill in your values:

   ```bash
   cp backend/.env.example backend/.env
   ```

   At a minimum, the defaults will work for local development with Docker. For AI and payment features, you will need valid API keys for Anthropic, Stripe, and SendGrid.

2. **Frontend**: Copy the example environment file:

   ```bash
   cp frontend/.env.example frontend/.env.local
   ```

   The default values (`NEXT_PUBLIC_API_URL=http://localhost:8000`) are sufficient for local development.

#### Manual Setup (Without Docker)

If you prefer running services directly on your host:

**Backend:**

```bash
cd backend
python -m venv .venv

# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Note: You will still need PostgreSQL 16, Redis 7, and Elasticsearch 8 running locally or via Docker.

---

## Development Workflow

### Branch Naming

Create a new branch for every change. Use the following prefixes:

| Prefix | Purpose | Example |
|---|---|---|
| `feature/` | New functionality | `feature/export-to-epub` |
| `fix/` | Bug fixes | `fix/login-token-refresh` |
| `docs/` | Documentation updates | `docs/api-authentication-guide` |
| `refactor/` | Code restructuring | `refactor/billing-service-cleanup` |

```bash
# Always branch from the latest main
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. Every commit message must follow this format:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer]
```

**Types:**

| Type | When to Use |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `chore` | Build process, CI, dependency updates |
| `perf` | Performance improvements |
| `style` | Formatting, whitespace (no logic changes) |

**Examples:**

```
feat(billing): add Stripe webhook retry logic
fix(auth): prevent token refresh race condition
test(agent-system): add integration tests for workflow engine
docs: update deployment guide with rollback steps
refactor(market-intelligence): extract BSR tracking into separate service
```

### Pull Request Process

1. **Ensure your branch is up to date** with `main`:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run the full test suite and linter** before pushing:

   ```bash
   make test
   make lint
   ```

3. **Push your branch** to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request** against the `main` branch of the upstream repository.

5. **Fill in the PR template** with:
   - A clear description of what changed and why
   - How to test the changes
   - Screenshots or recordings for UI changes
   - Any related issue numbers (e.g., `Closes #42`)

6. **Wait for CI to pass.** All status checks must be green before a review is requested.

7. **Address reviewer feedback** by pushing additional commits to the same branch. Do not force-push during review.

---

## Code Standards

### Backend (Python)

- **Formatter**: [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting
- **Type Checking**: [mypy](https://mypy-lang.org/) with strict mode. All functions must have type annotations.
- **Async/Await**: Use `async def` for all I/O-bound operations (database queries, HTTP calls, file operations). The backend is built on FastAPI with SQLAlchemy 2.0 async.
- **Pydantic Schemas**: Use Pydantic v2 models for all request/response validation.
- **Module Structure**: Business logic belongs in `backend/app/modules/<module_name>/`. Each module should contain its own `router.py`, `service.py`, `schemas.py`, and `models.py` as needed.
- **Error Handling**: Raise appropriate HTTP exceptions with clear error messages. Use structured logging.

```bash
# Check formatting and lint
cd backend
ruff check .
ruff format --check .

# Run type checking
mypy app/
```

### Frontend (TypeScript / React)

- **TypeScript**: Strict mode enabled (`"strict": true` in `tsconfig.json`). No `any` types unless absolutely unavoidable and explicitly justified.
- **React**: Functional components only. Use React hooks for state and side effects.
- **State Management**: Zustand for client state, TanStack React Query for server state.
- **Styling**: Tailwind CSS utility classes. Use the shadcn/ui component library for UI primitives.
- **Linting**: ESLint with Next.js recommended rules.
- **File Naming**: Use kebab-case for files (`market-intelligence-panel.tsx`), PascalCase for components (`MarketIntelligencePanel`).

```bash
# Lint and type-check
cd frontend
npx next lint
npx tsc --noEmit
```

### Testing Requirements

| Layer | Minimum Coverage | Notes |
|---|---|---|
| Backend | 75% | Unit + integration tests required for all new modules |
| Frontend | 60% | Component tests + hook tests for new features |

All new features and bug fixes must include corresponding tests. PRs that reduce overall coverage below these thresholds will not be merged.

---

## Architecture Overview

SelfPublisherForge is a monorepo containing the following top-level directories:

```
selfpublisherforge/
├── backend/          # FastAPI Python backend (26 feature modules)
│   ├── app/
│   │   ├── api/v1/       # Versioned API route handlers
│   │   ├── core/         # Middleware, security, rate limiting, logging
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── modules/      # Feature modules (business logic, routes, schemas)
│   │   ├── schemas/      # Shared Pydantic schemas
│   │   ├── services/     # Cross-cutting services (email, storage, AI)
│   │   └── tasks/        # Celery background task definitions
│   ├── migrations/       # Alembic database migrations
│   └── tests/            # Backend test suite
├── frontend/         # Next.js 14 React frontend (13 feature modules)
│   └── src/
│       ├── app/          # App Router pages and layouts
│       ├── components/   # Reusable UI components
│       ├── hooks/        # Custom React hooks
│       ├── lib/          # Utilities (API client, WebSocket, helpers)
│       ├── modules/      # Frontend feature modules
│       └── types/        # TypeScript type definitions
├── extension/        # Chrome extension (Manifest V3)
├── shared/           # Shared type contracts and event definitions
├── infra/            # Terraform IaC, Docker configs, monitoring, scripts
├── docs/             # Architecture and deployment documentation
└── docker-compose.yml
```

**Key technologies:**

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Celery, Alembic
- **Frontend**: Next.js 14 (App Router), TypeScript, React 18, TanStack React Query, Zustand, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL 16, Redis 7, Elasticsearch 8.x
- **Infrastructure**: Docker, AWS (ECS Fargate, RDS, ElastiCache, S3), Terraform, GitHub Actions

For a detailed architecture overview including module dependency graphs and communication patterns, see [`docs/architecture.md`](docs/architecture.md).

---

## Testing Guide

### Running Backend Tests

```bash
# Run all backend tests
cd backend && python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_agent_system.py -v

# Run only unit tests
python -m pytest tests/unit/ -v

# Run integration tests (requires running PostgreSQL and Redis)
python -m pytest tests/integration/ -v

# Run end-to-end tests
python -m pytest tests/e2e/ -v

# Run tests matching a keyword
python -m pytest tests/ -v -k "billing"
```

### Running Frontend Tests

```bash
# Run all frontend tests
cd frontend && npm test

# Run with coverage
npx jest --coverage

# Run tests in CI mode
npx jest --coverage --ci

# Run a specific test file
npx jest src/modules/billing/__tests__/billing.test.tsx

# Run E2E tests with Playwright
npx playwright test

# Run Playwright tests with a visible browser
npx playwright test --headed
```

### Using Make Shortcuts

The project includes Make targets for common test workflows:

```bash
make test              # Run all tests (backend + frontend)
make test-backend      # Backend tests with coverage
make test-frontend     # Frontend tests with coverage
make test-e2e          # Playwright E2E tests
make test-integration  # Backend integration tests
```

### Writing Tests

- **Backend**: Use `pytest` with async fixtures. Place tests in `backend/tests/` following the module structure (e.g., `tests/test_billing.py` or `tests/unit/test_billing_service.py`).
- **Frontend**: Use Jest with React Testing Library. Place tests alongside the code they test using `__tests__/` directories or `.test.tsx` suffixes.
- Always test both the happy path and error/edge cases.
- For API endpoints, test request validation, authorization, and expected response shapes.

---

## Issue Reporting

We use GitHub Issues to track bugs and feature requests. Before opening a new issue, please search existing issues to avoid duplicates.

### Bug Reports

When reporting a bug, include as much detail as possible:

- **Title**: A concise summary (e.g., "Login fails with MFA enabled on Safari")
- **Environment**: OS, browser, Node.js version, Python version, Docker version
- **Steps to Reproduce**: Numbered, minimal steps to trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots / Logs**: Include console output, error messages, or screenshots
- **Severity**: Critical (data loss, security), High (feature broken), Medium (workaround exists), Low (cosmetic)

### Feature Requests

When proposing a new feature:

- **Title**: A brief description (e.g., "Add bulk import for royalty data")
- **Problem Statement**: What pain point does this solve? Who is affected?
- **Proposed Solution**: How should it work from a user's perspective?
- **Alternatives Considered**: Other approaches you evaluated and why they were less ideal
- **Additional Context**: Mockups, reference implementations, or links to related issues

### Labels

Maintainers will triage issues and apply labels. Common labels include:

| Label | Meaning |
|---|---|
| `bug` | Confirmed bug |
| `enhancement` | Feature request |
| `good first issue` | Suitable for new contributors |
| `help wanted` | Community contributions welcome |
| `priority: critical` | Must be fixed immediately |
| `priority: high` | Should be addressed in the current sprint |
| `module: billing` | Related to the billing module (similar labels exist for all modules) |

---

## Pull Request Process

1. PRs must target the `main` branch.
2. All CI checks must pass (linting, type checking, tests, security scans, Docker builds).
3. At least **one approving review** from a maintainer is required before merging.
4. PRs should be focused: one feature, one fix, or one refactor per PR. Avoid bundling unrelated changes.
5. Keep PRs reasonably sized. If a feature is large, break it into smaller, reviewable increments.
6. Update the `CHANGELOG.md` under the `[Unreleased]` section if your change is user-facing.
7. Update documentation in `docs/` or the `README.md` if your change affects setup, configuration, or public APIs.

---

## Review Process

Reviewers evaluate pull requests against the following criteria:

### Correctness
- Does the code do what it claims to do?
- Are edge cases handled?
- Are error conditions handled gracefully with appropriate HTTP status codes and messages?

### Code Quality
- Does the code follow the project's style conventions (Ruff for Python, ESLint for TypeScript)?
- Are type annotations complete and accurate (mypy, TypeScript strict)?
- Is the code readable and well-organized?
- Are functions and modules appropriately sized and focused?

### Testing
- Are there tests for the new or changed functionality?
- Do the tests cover both success and failure paths?
- Does test coverage meet the minimum thresholds (75% backend, 60% frontend)?

### Security
- Are user inputs validated and sanitized?
- Are authentication and authorization checks in place?
- Are secrets kept out of the codebase?
- Are dependencies free of known vulnerabilities (pip-audit, npm audit)?

### Performance
- Are database queries efficient? Are N+1 queries avoided?
- Is caching used appropriately (Redis)?
- Are async patterns used correctly for I/O-bound operations?

### Documentation
- Are public API changes reflected in the Swagger docs?
- Is the CHANGELOG updated for user-facing changes?
- Are complex algorithms or business logic commented?

### Compatibility
- Does the change maintain backward compatibility with existing API contracts?
- Are database migrations reversible?

---

## Getting Help

If you have questions or need guidance:

- Open a [GitHub Discussion](https://github.com/navigreen311/selfpublisherforge/discussions) for general questions.
- Reference the [`docs/`](docs/) directory for architecture and deployment guides.
- Check the [README](README.md) for setup instructions and troubleshooting.

We appreciate every contribution, whether it is a bug report, documentation improvement, or a major feature. Thank you for helping make SelfPublisherForge better!
