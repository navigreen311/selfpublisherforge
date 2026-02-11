# SelfPublisherForge

AI-powered, end-to-end self-publishing platform for independent authors, small publishers, and publishing agencies. From manuscript to market, SelfPublisherForge provides 29 integrated modules covering writing, publishing, marketing, analytics, and AI automation.

## Features

### Core Platform
- **User Authentication** -- Email/password login, OAuth (Google + GitHub), JWT (access + refresh tokens), multi-factor authentication (MFA), password reset, session management
- **Organization Management** -- Multi-tenant workspaces with role-based access control, team invitations, row-level data isolation via `org_id`
- **Billing & Subscriptions** -- Stripe integration with tiered plan management (Free, Starter, Pro, Business, Enterprise), usage metering, invoices, webhooks (upgrade/downgrade/failure/cancel), and per-endpoint rate limiting with tier multipliers
- **Notifications** -- In-app and email notification delivery via SendGrid, with real-time push through WebSockets and full notification center UI
- **Internationalization** -- i18n framework with support for English, Spanish, and German
- **Accessibility & Design** -- WCAG 2.1 AA compliant, mobile responsive, error boundaries, empty states, SEO meta tags, and Open Graph support

### Writing & Content
- **AI Writing Studio** -- Manuscript editor with chapter management, AI-powered content generation, readability analysis, writing prompts, and deep NLP analyzers (syntax, rhythm, vocabulary, tone)
- **Style Cloning Engine** -- NLP pipeline for voice fingerprint analysis, style profile generation, writing conformity scoring, and style profile manager with real-time conformity checking
- **Knowledge Vault** -- Research management with Elasticsearch full-text search, document importing, and AI-assisted note extraction
- **Cover Design Studio** -- AI cover generation with template system, design analysis, cover image management, and full-featured frontend studio with drag-and-drop editing

### Publishing & Distribution
- **Production Pipeline** -- Workflow engine for EPUB and PDF generation with configurable formatting templates
- **Publishing Operations** -- Multi-platform publishing support (KDP, IngramSpark, Draft2Digital) with listing sync and export management
- **KDP Validation** -- Compliance scanning covering print specs, ebook validation, cover dimensions, content policy rules, and full-featured validation dashboard with pre-flight checks

### Marketing & Sales
- **Marketing Launch Planner** -- Campaign planning with ARC (Advance Reader Copy) management, email builder, and social media content generation
- **Advertising Intelligence** -- Amazon Ads (AMS) and Facebook Ads campaign management with bid optimization and creative generation
- **Product Page Lab** -- A/B testing for book listings with mobile rendering checks, blurb generation, and conversion analysis
- **Pricing Automation** -- Dynamic pricing strategies, Kindle Unlimited (KU) page-read calculator, price simulation, rule-based optimization, and full-featured frontend tools
- **Review Intelligence** -- Sentiment analysis, review velocity tracking, reputation monitoring, alert system, and full-featured dashboard with real-time alerts
- **Competitor Finder** -- Competitive gap detection, review analysis across competitor titles, opportunity blueprint generation, and full-featured frontend with gap analysis tools

### Analytics & Intelligence
- **Revenue & Royalty Tracking** -- Multi-platform royalty import, revenue aggregation, and custom report builder
- **Portfolio Economics** -- Backlist analysis, audience DNA profiling, greenlight scoring for new titles, seasonal trend calendars, and full-featured dashboard with opportunity detection
- **Market Intelligence Engine** -- Niche analysis, BSR tracking, competitor scoring, and Amazon marketplace data via API

### AI & Automation
- **Agent System** -- Autonomous agent framework with workflow engine, governance rules, audit logging, task execution, and 10 pre-built marketplace templates
- **LLM Orchestration** -- Multi-provider model routing (Anthropic Claude, OpenAI GPT) with response caching, quality scoring, and cost tracking
- **WebSocket Real-Time Updates** -- Live event streaming via Redis pub/sub with auto-reconnect client, used for agent progress, AI generation, and notifications
- **Notification Center** -- Real-time notification system with WebSocket updates, in-app notifications, and full-featured frontend center
- **Background Task Processing** -- Celery workers with Redis broker for long-running operations, dead letter handling, and scheduled task beats

### Chrome Extension
- **Amazon Research Assistant** -- Browser extension (Manifest V3) for extracting Amazon product data, tracking BSR, researching niches, and saving clips to your SelfPublisherForge account. Supports 10 Amazon marketplaces with sidebar panel and popup interface. Enhanced with deeper metadata extraction.

### Platform Administration
- **Admin Panel** -- Enterprise-tier administration dashboard with user management, organization management, billing oversight, system health monitoring, and analytics (Enterprise tier only)

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
| **Monitoring** | Prometheus, Grafana, AlertManager, CloudWatch |
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
| Frontend - Cover Studio | http://localhost:3000/cover-studio |
| Frontend - Review Intelligence | http://localhost:3000/review-intelligence |
| Frontend - Competitor Finder | http://localhost:3000/competitor-finder |
| Frontend - Style Profiles | http://localhost:3000/style-profiles |
| Frontend - Pricing Tools | http://localhost:3000/pricing |
| Frontend - Portfolio Economics | http://localhost:3000/portfolio-economics |
| Frontend - Notifications | http://localhost:3000/notifications |
| Frontend - KDP Validation | http://localhost:3000/kdp-validation |
| Frontend - Admin Panel | http://localhost:3000/admin (Enterprise) |
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
│       ├── modules/           # 19 frontend feature modules
│       │   ├── admin/              # Admin panel (Enterprise)
│       │   ├── analytics/          # Analytics dashboards
│       │   ├── competitor-finder/  # Competitor research and gap analysis
│       │   ├── cover-design/       # Cover Design Studio
│       │   ├── kdp-validation/     # KDP validation dashboard
│       │   ├── notifications/      # Notification Center
│       │   ├── portfolio-economics/ # Portfolio Economics dashboard
│       │   ├── pricing/            # Pricing Automation tools
│       │   ├── review-intelligence/ # Review Intelligence dashboard
│       │   └── style-profiles/     # Style Profile manager
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
│   ├── monitoring/            # Prometheus, Grafana, AlertManager configs + alert rules
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
- **AWS Secrets Manager** -- Secrets management

### Monitoring

- **Prometheus** -- Metrics collection from PostgreSQL, Redis, and Node exporters
- **Grafana** -- Dashboards with latency P50/P95/P99, error rates, queue depth
- **AlertManager** -- Alert routing with tiers P0 (immediate, PagerDuty) through P3 (next business day, Slack)
- **CloudWatch** -- ECS logs, ALB metrics, auto-scaling triggers

## Deployment Guide

Full deployment documentation is in [`docs/deploy.md`](docs/deploy.md). Below is a condensed step-by-step.

### Prerequisites

- **AWS account** with IAM credentials configured (`aws configure`)
- **Domain name** pointing to your AWS ALB (e.g., `selfpublisherforge.com`)
- **SSL certificate** provisioned via AWS Certificate Manager (ACM)
- **Terraform >= 1.6.0** installed locally
- **Docker** and **Docker Compose** installed
- GitHub repository secrets configured (see `docs/deploy.md` for full list)

### Step-by-Step Deployment

<details>
<summary><strong>Step 1: Configure environment variables</strong></summary>

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env — fill in all API keys and connection strings

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local — set API URL and Stripe publishable key
```

See the [Environment Variables](#environment-variables) section and `backend/.env.example` for detailed descriptions of each variable.

</details>

<details>
<summary><strong>Step 2: Run database migrations</strong></summary>

```bash
cd backend
alembic upgrade head
```

This applies all pending migrations to your PostgreSQL database. Ensure `DATABASE_URL` in your `.env` is correct before running.

</details>

<details>
<summary><strong>Step 3: Build and push Docker images</strong></summary>

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build images
make build

# Tag and push
docker tag selfpublisherforge-api:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/selfpublisherforge-api:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/selfpublisherforge-api:latest

docker tag selfpublisherforge-frontend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/selfpublisherforge-frontend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/selfpublisherforge-frontend:latest
```

</details>

<details>
<summary><strong>Step 4: Apply Terraform infrastructure</strong></summary>

```bash
# Preview changes
make tf-plan ENV=staging

# Apply (creates ECS, RDS, ElastiCache, S3, ALB, etc.)
make tf-apply ENV=staging

# For production (requires manual approval)
make tf-plan ENV=production
make tf-apply ENV=production
```

</details>

<details>
<summary><strong>Step 5: Deploy via GitHub Actions</strong></summary>

- **Staging**: Push or merge to `main` -- triggers automatic staging deployment.
- **Production**: Push a version tag to trigger blue-green production deployment:

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

</details>

<details>
<summary><strong>Step 6: Verify health checks</strong></summary>

```bash
# Check API health endpoint
curl -f https://staging.selfpublisherforge.com/api/health

# Verify ECS service stability
aws ecs describe-services \
  --cluster selfpublisherforge-staging \
  --services selfpublisherforge-api-staging \
  --query 'services[0].deployments'
```

</details>

## Chrome Extension Installation

The Chrome extension (`extension/` directory) is a Manifest V3 extension for extracting Amazon product data.

### Developer Mode Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked** and select the `extension/` directory from this repository
4. The extension icon will appear in your toolbar

### Configuration

1. Click the extension icon and open the popup
2. Set the **API URL** to your backend instance:
   - Development: `http://localhost:8000`
   - Production: `https://api.selfpublisherforge.com`
3. Enter your **authentication token** (obtain one via `POST /api/v1/auth/login`)

### Usage

1. Navigate to any Amazon product page (supported marketplaces: US, UK, DE, FR, CA, AU, JP, IT, ES, IN)
2. The content script automatically extracts product data on `/dp/` and `/gp/product/` pages
3. Open the **side panel** (click the extension icon or use the toolbar) to view extracted data, track BSR, research niches, and save clips to your SelfPublisherForge account

## Database Migrations

Migrations are managed by [Alembic](https://alembic.sqlalchemy.org/) and live in `backend/migrations/`.

```bash
# Create a new migration (auto-detects model changes)
cd backend
alembic revision --autogenerate -m "add user preferences table"

# Apply all pending migrations
alembic upgrade head

# Rollback the last migration
alembic downgrade -1

# View current migration status
alembic current

# View migration history
alembic history --verbose
```

> **Tip**: Always review auto-generated migrations before applying. Alembic may not detect all changes (e.g., column renames, index changes) and manual edits may be required.

## Monitoring Setup

The monitoring stack runs alongside the application in `docker-compose.yml` and is configured in `infra/monitoring/`.

### Stack Components

| Component | Port | Purpose |
|---|---|---|
| **Prometheus** | 9090 | Metrics collection and alerting rules |
| **Grafana** | 3001 | Dashboards and visualization |
| **AlertManager** | 9093 | Alert routing (Slack, PagerDuty) |
| **postgres-exporter** | 9187 | PostgreSQL metrics |
| **redis-exporter** | 9121 | Redis metrics |
| **node-exporter** | 9100 | Host system metrics |
| **elasticsearch-exporter** | 9114 | Elasticsearch metrics |

### Development

Access Grafana at [http://localhost:3001](http://localhost:3001) (default credentials: `admin` / value of `GRAFANA_PASSWORD` env var, defaults to `admin`). Prometheus datasource is pre-configured via `infra/monitoring/grafana-datasources.yml`.

### Production

- **AWS CloudWatch** -- ECS logs, ALB metrics, auto-scaling triggers
- **Prometheus** -- Application and infrastructure metrics scraped from exporters
- **Grafana** -- Dashboards with latency percentiles, error rates, and queue depth
- **AlertManager** -- Alert routing with tiers P0 (immediate, PagerDuty) through P3 (next business day, Slack). See `infra/monitoring/alerts.yml`.

## Troubleshooting

<details>
<summary><strong>Database connection failures</strong></summary>

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check connection string in .env
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/selfpublisherforge

# Test connection directly
docker-compose exec postgres psql -U postgres -d selfpublisherforge -c "SELECT 1"

# Reset development database (WARNING: destroys all data)
docker-compose down -v   # removes volumes
docker-compose up -d postgres
cd backend && alembic upgrade head
```

</details>

<details>
<summary><strong>Redis connection failures</strong></summary>

```bash
# Verify Redis is running
docker-compose ps redis

# Test connectivity
docker-compose exec redis redis-cli ping
# Expected: PONG

# Check Redis URL in .env
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/1
```

</details>

<details>
<summary><strong>API key configuration issues</strong></summary>

- Ensure all required API keys are set in `backend/.env` (not the placeholder values from `.env.example`).
- The `ANTHROPIC_API_KEY` is required for AI features. `OPENAI_API_KEY` is a fallback.
- `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are required for billing features.
- `SENDGRID_API_KEY` is required for email delivery.
- If a key is missing, the backend logs will show a clear error on startup or when the feature is invoked.

</details>

<details>
<summary><strong>Checking service logs</strong></summary>

```bash
# Tail backend logs
docker-compose logs -f backend

# Tail Celery worker logs
docker-compose logs -f celery-worker

# Tail all services
docker-compose logs -f

# Filter for errors
docker-compose logs backend 2>&1 | grep -i error

# Using Make
make logs SERVICE=backend
```

</details>

<details>
<summary><strong>Resetting the development database</strong></summary>

```bash
# Stop services and remove volumes
docker-compose down -v

# Restart PostgreSQL
docker-compose up -d postgres

# Wait for health check, then run migrations
docker-compose exec postgres pg_isready -U postgres
cd backend && alembic upgrade head

# Restart all services
docker-compose up -d
```

</details>

## API Authentication

All API endpoints (except login, registration, and health checks) require a valid JWT token.

### Login

```bash
# Obtain tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'

# Response:
# {
#   "access_token": "eyJhbG...",
#   "refresh_token": "eyJhbG...",
#   "token_type": "bearer"
# }
```

### Authenticated Requests

Include the `Authorization` header on all subsequent requests:

```bash
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <access_token>"
```

### Token Refresh

Access tokens expire after 15 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`). Use the refresh token to obtain a new access token without re-authenticating:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# Response:
# {
#   "access_token": "eyJhbG...(new)...",
#   "refresh_token": "eyJhbG...(new)...",
#   "token_type": "bearer"
# }
```

Refresh tokens expire after 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`).

## Contributing

1. Create a feature branch: `git checkout -b ai-feature/your-feature-name`
2. Follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
3. Write or update tests for all changes
4. Ensure all tests pass: `make test`
5. Ensure code is formatted: `make lint`
6. Open a pull request to `main`

## License

Proprietary -- Green Companies LLC
