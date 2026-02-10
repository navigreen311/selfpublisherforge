# SelfPublisherForge

AI-powered, end-to-end self-publishing platform for independent authors, small publishers, and publishing agencies. From manuscript to market, SelfPublisherForge provides 29 integrated modules covering writing, publishing, marketing, analytics, and AI automation.

## Features

### Core Platform
- **User Authentication** -- Email/password login, JWT (access + refresh tokens), multi-factor authentication (MFA), password reset, session management
- **Organization Management** -- Multi-tenant workspaces with role-based access control, team invitations, row-level data isolation via `org_id`
- **Billing & Subscriptions** -- Stripe integration with tiered plan management (Free, Starter, Pro, Business, Enterprise), usage metering, invoices, and webhooks
- **Notifications** -- In-app and email notification delivery via SendGrid, with real-time push through WebSockets

### Writing & Content
- **AI Writing Studio** -- Manuscript editor with chapter management, AI-powered content generation, readability analysis, and writing prompts
- **Style Cloning Engine** -- NLP pipeline for voice fingerprint analysis, style profile generation, and writing conformity scoring
- **Knowledge Vault** -- Research management with Elasticsearch full-text search, document importing, and AI-assisted note extraction
- **Cover Design Studio** -- AI cover generation with template system, design analysis, and cover image management

### Publishing & Distribution
- **Production Pipeline** -- Workflow engine for EPUB and PDF generation with configurable formatting templates
- **Publishing Operations** -- Multi-platform publishing support (KDP, IngramSpark, Draft2Digital) with listing sync and export management
- **KDP Validation** -- Compliance scanning covering print specs, ebook validation, cover dimensions, and content policy rules

### Marketing & Sales
- **Marketing Launch Planner** -- Campaign planning with ARC (Advance Reader Copy) management, email builder, and social media content generation
- **Advertising Intelligence** -- Amazon Ads (AMS) and Facebook Ads campaign management with bid optimization and creative generation
- **Product Page Lab** -- A/B testing for book listings with mobile rendering checks, blurb generation, and conversion analysis
- **Pricing Automation** -- Dynamic pricing strategies, Kindle Unlimited (KU) page-read calculator, price simulation, and rule-based optimization
- **Review Intelligence** -- Sentiment analysis, review velocity tracking, reputation monitoring, and alert system
- **Competitor Finder** -- Competitive gap detection, review analysis across competitor titles, and opportunity blueprint generation

### Analytics & Intelligence
- **Revenue & Royalty Tracking** -- Multi-platform royalty import, revenue aggregation, and custom report builder
- **Portfolio Economics** -- Backlist analysis, audience DNA profiling, greenlight scoring for new titles, and seasonal trend calendars
- **Market Intelligence Engine** -- Niche analysis, BSR tracking, competitor scoring, and Amazon marketplace data via API

### AI & Automation
- **Agent System** -- Autonomous agent framework with workflow engine, governance rules, audit logging, and task execution
- **LLM Orchestration** -- Multi-provider model routing (Anthropic Claude, OpenAI GPT) with response caching, quality scoring, and cost tracking
- **WebSocket Real-Time Updates** -- Live event streaming via Redis pub/sub with auto-reconnect client, used for agent progress, AI generation, and notifications
- **Background Task Processing** -- Celery workers with Redis broker for long-running operations, dead letter handling, and scheduled task beats

### Chrome Extension
- **Amazon Research Assistant** -- Browser extension (Manifest V3) for extracting Amazon product data, tracking BSR, researching niches, and saving clips to your SelfPublisherForge account. Supports 10 Amazon marketplaces with sidebar panel and popup interface.

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Celery, Alembic |
| **Frontend** | Next.js 14 (App Router), TypeScript, React 18, TanStack React Query, Zustand, Tailwind CSS, shadcn/ui |
| **Database** | PostgreSQL 16, Redis 7 (cache, rate limiting, pub/sub, task broker) |
| **Search** | Elasticsearch 8.x |
| **AI/ML** | Anthropic Claude API, OpenAI GPT (fallback) |
| **Storage** | AWS S3 / Cloudflare R2 |
| **Payments** | Stripe (subscriptions, invoices, webhooks) |
| **Email** | SendGrid |
| **Infrastructure** | Docker, AWS (ECS, RDS, ElastiCache, S3, CloudFront, ALB), Terraform |
| **CI/CD** | GitHub Actions (CI, staging deploy, production blue-green deploy) |
| **Monitoring** | Prometheus, Datadog, Grafana, CloudWatch |
| **Chrome Extension** | Manifest V3, Content Scripts, Side Panel API |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Node.js 20+
- Git

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/navigreen311/selfpublisherforge.git
cd selfpublisherforge

# Start all services
docker compose up --build -d
```

Services will be available at:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Flower (Celery monitor) | http://localhost:5555 |
| Prometheus | http://localhost:9090 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Elasticsearch | localhost:9200 |

### Manual Backend Setup

```bash
cd backend
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values (see Environment Variables below)

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

### Manual Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your values

npm run dev
```

### Environment Variables

#### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | JWT signing key | `change-me-to-a-random-string` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/selfpublisherforge` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint | `http://localhost:9200` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | -- |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | -- |
| `STRIPE_SECRET_KEY` | Stripe secret key | -- |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | -- |
| `SENDGRID_API_KEY` | SendGrid email API key | -- |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 | -- |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 | -- |
| `S3_BUCKET` | S3 bucket name | `selfpublisherforge-assets` |
| `CELERY_BROKER_URL` | Celery broker (Redis) | `redis://localhost:6379/1` |

See `backend/.env.example` for the complete list.

#### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket endpoint | `ws://localhost:8000` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe public key | -- |

## Running Tests

### Backend Tests

```bash
# Run all backend tests
cd backend && pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_agent_system.py -v

# Run integration tests
pytest tests/integration/ -v

# Run end-to-end tests
pytest tests/e2e/ -v
```

### Frontend Tests

```bash
# Run all frontend tests
cd frontend && npx jest --coverage

# Run with CI reporter
npx jest --coverage --ci

# Run E2E tests with Playwright
npx playwright test
```

### Using Make

```bash
make test              # Run all tests (backend + frontend)
make test-backend      # Backend tests with coverage
make test-frontend     # Frontend tests with coverage
make test-e2e          # Playwright E2E tests
make test-integration  # Backend integration tests
```

## Project Structure

```
selfpublisherforge/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/           # API route handlers (versioned)
│   │   ├── core/             # Security, middleware, rate limiting, logging, pagination
│   │   ├── models/           # SQLAlchemy ORM models (user, org, project, content, etc.)
│   │   ├── modules/          # 26 feature modules (business logic + routes + schemas)
│   │   │   ├── advertising/       # AMS + Facebook ad campaigns
│   │   │   ├── agent_system/      # Agent framework, governance, workflow engine
│   │   │   ├── ai_writing/        # Manuscript generation, readability analysis
│   │   │   ├── analytics/         # Revenue dashboards, royalty import, reports
│   │   │   ├── auth/              # JWT auth, MFA, password reset
│   │   │   ├── billing/           # Stripe plans, subscriptions, usage metering
│   │   │   ├── chrome_extension/  # Extension API endpoints
│   │   │   ├── competitor_finder/ # Competitive gap detection, opportunity scoring
│   │   │   ├── cover_design/      # AI cover generation, templates
│   │   │   ├── kdp_validation/    # Print, ebook, cover, compliance validation
│   │   │   ├── knowledge_vault/   # Research management, ES search, AI import
│   │   │   ├── llm_orchestration/ # Multi-provider LLM routing, caching, cost tracking
│   │   │   ├── market_intelligence/ # Niche analysis, BSR tracking
│   │   │   ├── marketing/         # Launch planner, ARC, email/social campaigns
│   │   │   ├── notifications/     # In-app + email notification delivery
│   │   │   ├── portfolio_economics/ # Backlist, audience DNA, greenlight, seasonal
│   │   │   ├── pricing_automation/  # Dynamic pricing, KU calculator, simulation
│   │   │   ├── product_page_lab/    # A/B testing, blurb gen, mobile checks
│   │   │   ├── production_pipeline/ # EPUB + PDF workflow engine
│   │   │   ├── publishing_ops/      # Multi-platform publish, listing sync
│   │   │   ├── realtime/           # WebSocket manager, Redis pub/sub events
│   │   │   ├── review_intelligence/ # Sentiment analysis, velocity, alerts
│   │   │   ├── storage/            # S3/R2 uploads, presigned URLs
│   │   │   ├── style_cloning/      # NLP voice fingerprinting, profile generation
│   │   │   └── users/              # User CRUD, org management
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Cross-cutting services (email, storage, AI)
│   │   └── tasks/             # Celery task definitions (18 task modules)
│   ├── migrations/            # Alembic database migrations
│   └── tests/                 # 2,183+ passing tests (unit, integration, e2e)
├── frontend/                  # Next.js 14 React frontend
│   └── src/
│       ├── app/               # App Router pages and layouts
│       │   ├── (auth)/        # Authentication pages (login, register, reset)
│       │   └── (dashboard)/   # Dashboard pages (protected)
│       ├── components/        # Reusable UI components (layout, shared, ui)
│       ├── hooks/             # Custom React hooks
│       ├── lib/               # Utilities (API client, WebSocket, helpers)
│       ├── modules/           # 13 frontend feature modules
│       └── types/             # TypeScript type definitions
├── extension/                 # Chrome extension (Manifest V3)
│   ├── background/            # Service worker
│   ├── content/               # Amazon product page extractor
│   ├── popup/                 # Extension popup UI
│   ├── sidebar/               # Side panel UI
│   └── manifest.json
├── shared/                    # Shared type contracts and events
│   ├── contracts/             # API contracts, module registry
│   ├── events/                # Event type definitions
│   └── types/                 # Shared enums and types
├── infra/                     # Infrastructure and deployment
│   ├── terraform/             # AWS infrastructure-as-code (ECS, RDS, ElastiCache, S3, etc.)
│   ├── docker/                # Production Docker Compose config
│   ├── monitoring/            # Prometheus, Datadog, Grafana configs + alert rules
│   └── scripts/               # Deploy, rollback, setup, and build scripts
├── docs/                      # Architecture and deployment documentation
├── .github/workflows/         # CI/CD pipelines (ci.yml, deploy-staging.yml, deploy-production.yml)
├── docker-compose.yml         # Local development services
├── Makefile                   # Development and deployment commands
└── CLAUDE.md                  # AI development instructions
```

## Module Registry

The platform consists of 29 modules across 5 subscription tiers. Higher tiers include all modules from lower tiers.

| # | Module | Tier | API Prefix | Description |
|---|---|---|---|---|
| 1 | auth | Free | `/auth` | JWT authentication, MFA, password reset |
| 2 | org | Free | `/orgs` | Organization and team management |
| 3 | projects | Free | `/projects` | Project workspace management |
| 4 | books | Free | `/books` | Book metadata and lifecycle |
| 5 | market-research | Starter | `/market-research` | Market and niche analysis |
| 6 | keyword-research | Starter | `/keywords` | Keyword discovery and tracking |
| 7 | style-profiles | Free | `/style-profiles` | Voice fingerprint and style analysis |
| 8 | brand-kits | Starter | `/brand-kits` | Brand identity management |
| 9 | ai-outline | Starter | `/ai/outlines` | AI-powered book outline generation |
| 10 | ai-writing | Pro | `/ai/writing` | AI manuscript generation |
| 11 | ai-editing | Pro | `/ai/editing` | AI editing and revision |
| 12 | ai-cover | Pro | `/ai/covers` | AI cover design generation |
| 13 | formatting | Starter | `/formatting` | Book formatting and templates |
| 14 | publishing-validation | Starter | `/publishing/validation` | KDP and platform compliance checks |
| 15 | publishing-distribution | Pro | `/publishing/distribution` | Multi-platform distribution |
| 16 | email-marketing | Pro | `/marketing/email` | Email campaign builder |
| 17 | social-marketing | Pro | `/marketing/social` | Social media content generation |
| 18 | ad-campaigns | Business | `/marketing/ads` | AMS and Facebook ad management |
| 19 | agent-framework | Pro | `/agents` | Autonomous AI agent runtime |
| 20 | agent-marketplace | Pro | `/agents/marketplace` | Pre-built agent templates |
| 21 | agent-builder | Business | `/agents/builder` | Custom agent creation |
| 22 | sales-analytics | Starter | `/analytics/sales` | Revenue and sales dashboards |
| 23 | marketing-analytics | Pro | `/analytics/marketing` | Campaign performance analytics |
| 24 | reports | Pro | `/reports` | Custom report generation |
| 25 | notifications | Free | `/notifications` | In-app and email notifications |
| 26 | user-settings | Free | `/settings` | User preferences and settings |
| 27 | admin | Enterprise | `/admin` | Platform administration |
| 28 | billing | Free | `/billing` | Stripe subscription management |
| 29 | usage-tracking | Free | `/usage` | API and feature usage metering |

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full architecture overview including:
- Module dependency graph (Mermaid diagram)
- Tier hierarchy and subscription gating
- Communication patterns (REST, Redis Streams, WebSocket, Celery)
- Data flow diagram
- Key design decisions and rationale

## CI/CD Pipeline

### Continuous Integration (`ci.yml`)

Runs on every push and pull request:
- **Backend**: Ruff lint, ruff format check, mypy type check, pytest with coverage, pip-audit security scan
- **Frontend**: ESLint, TypeScript type check, Jest with coverage, npm audit security scan
- **Docker**: Build validation for both API and frontend images
- **Integration**: Cross-module integration tests with PostgreSQL and Redis service containers

### Staging Deployment (`deploy-staging.yml`)

Triggers automatically on merge to `main`:
1. Builds and pushes Docker images to AWS ECR
2. Updates ECS task definitions (API, frontend, worker, beat)
3. Deploys to staging ECS cluster
4. Runs Playwright E2E tests against staging
5. Sends Slack notification

### Production Deployment (`deploy-production.yml`)

Triggers on version tag push (`v*.*.*`):
1. Builds and pushes versioned Docker images to ECR
2. Saves current task definitions for rollback
3. Performs blue-green deployment via AWS CodeDeploy
4. Runs health checks and monitors error rate
5. Auto-rollback if error rate exceeds 1% or health check fails
6. Sends Slack notification

See [`docs/deploy.md`](docs/deploy.md) for complete deployment and operations documentation.

## Development Commands

```bash
make help              # Show all available commands
make dev               # Start all services with hot reload
make dev-down          # Stop all services
make test              # Run all tests
make lint              # Run all linters
make format            # Auto-format all code
make migrate           # Run database migrations
make migrate-create MSG="description"  # Create new migration
make security-scan     # Run pip-audit + npm audit
make build             # Build production Docker images
make deploy-staging    # Deploy to staging
make deploy-prod TAG=v1.2.3  # Deploy to production
make tf-plan ENV=staging     # Preview Terraform changes
make tf-apply ENV=staging    # Apply Terraform changes
make logs SERVICE=backend    # Tail service logs
make shell             # Shell into API container
make db-shell          # PostgreSQL CLI
make redis-shell       # Redis CLI
make clean             # Remove containers, volumes, and artifacts
```

## Infrastructure

### AWS Resources (Terraform)

All infrastructure is defined in `infra/terraform/` and deployed per environment:

- **ECS Fargate** -- API, frontend, Celery worker, and Celery beat services
- **RDS PostgreSQL 16** -- Primary database (multi-AZ in production)
- **ElastiCache Redis 7** -- Caching, rate limiting, pub/sub, task broker
- **OpenSearch** -- Full-text search (Elasticsearch-compatible)
- **S3** -- Asset storage (book files, covers, exports)
- **ALB** -- Application load balancer with health checks
- **ECR** -- Docker image registry
- **SSM Parameter Store** -- Secrets management

### Monitoring

- **Prometheus** -- Metrics collection from PostgreSQL, Redis, and Node exporters
- **Datadog** -- APM dashboard with latency P50/P95/P99, error rates, queue depth
- **Alert tiers** -- P0 (immediate, PagerDuty) through P3 (next business day, Slack)
- **CloudWatch** -- ECS logs, ALB metrics, auto-scaling triggers

## Contributing

1. Create a feature branch: `git checkout -b ai-feature/your-feature-name`
2. Follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
3. Write or update tests for all changes
4. Ensure all tests pass: `make test`
5. Ensure code is formatted: `make lint`
6. Open a pull request to `main`

## License

Proprietary -- Green Companies LLC
