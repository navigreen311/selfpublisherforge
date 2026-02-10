# Changelog

All notable changes to SelfPublisherForge will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-09

Initial release of SelfPublisherForge with 29 feature modules, full CI/CD pipeline,
infrastructure-as-code, and 2,183+ passing backend tests.

### Added

#### Core Platform
- **Authentication System** -- JWT access/refresh tokens, multi-factor authentication (MFA), password reset flow, session management with rate limiting
- **User & Organization Management** -- Multi-tenant workspaces, role-based access control, team invitations, row-level data isolation via `org_id`
- **Billing & Subscriptions** -- Stripe integration with 5 subscription tiers (Free, Starter, Pro, Business, Enterprise), usage metering, invoice generation, webhook handling
- **Notification Service** -- In-app and email notification delivery via SendGrid, real-time push through WebSocket channel
- **API Gateway** -- FastAPI middleware stack with rate limiting (Redis sliding window), structured logging, CORS, error handling, health checks, API versioning

#### Writing & Content (4 modules)
- **AI Writing Studio** -- Manuscript editor with chapter management, AI-powered content generation via LLM orchestration, readability scoring, and writing prompts
- **Style Cloning Engine** -- NLP pipeline for voice fingerprint extraction, style profile generation, ingestion of reference texts, and writing conformity analysis
- **Knowledge Vault** -- Research management with Elasticsearch full-text search, multi-format document importing, and AI-assisted note extraction
- **Cover Design Studio** -- AI-powered cover generation with template system, design analysis, and cover image management

#### Publishing & Distribution (3 modules)
- **Production Pipeline** -- Configurable workflow engine for EPUB and PDF book generation with formatting templates
- **Publishing Operations** -- Multi-platform publishing support for KDP, IngramSpark, and Draft2Digital with EPUB/PDF export and listing synchronization
- **KDP Validation** -- Comprehensive compliance scanning covering print specifications, ebook format validation, cover dimension checks, and content policy rules

#### Marketing & Sales (6 modules)
- **Marketing Launch Planner** -- Campaign planning with ARC (Advance Reader Copy) management, email sequence builder, and social media content generation
- **Advertising Intelligence** -- Amazon Ads (AMS) and Facebook Ads campaign management with bid optimization, budget allocation, and creative generation
- **Product Page Lab** -- A/B testing framework for book listings with mobile rendering checks, AI blurb generation, and conversion rate analysis
- **Pricing Automation** -- Dynamic pricing strategies, Kindle Unlimited page-read calculator, price simulation engine, and rule-based optimization
- **Review Intelligence** -- Sentiment analysis, review velocity tracking, reputation scoring, alert rules, and notification triggers
- **Competitor Finder** -- Competitive gap detection, cross-title review analysis via NLP, and opportunity blueprint generation

#### Analytics & Intelligence (3 modules)
- **Revenue & Royalty Tracking** -- Multi-platform royalty import (KDP, IngramSpark, D2D), revenue aggregation, custom report builder with export
- **Portfolio Economics** -- Backlist profitability analysis, audience DNA profiling, greenlight scoring for new titles, and seasonal trend calendars
- **Market Intelligence Engine** -- Amazon niche analysis, BSR tracking, competitor scoring, keyword data, and marketplace API integration

#### AI & Automation (4 modules)
- **Agent System** -- Autonomous AI agent framework with workflow engine, governance rules, budget enforcement, audit logging, and multi-step task execution
- **LLM Orchestration** -- Multi-provider model routing (Anthropic Claude, OpenAI GPT), response caching, quality scoring, cost tracking, and provider failover
- **WebSocket Real-Time** -- Live event streaming via Redis pub/sub with typed JSON messages, auto-reconnect client with exponential backoff
- **Background Task Processing** -- Celery worker pool with Redis broker, 18 task modules across all features, dead letter queue handling, scheduled beat tasks

#### Chrome Extension
- **Amazon Research Assistant** -- Manifest V3 Chrome extension for extracting Amazon product data from 10 international marketplaces, BSR tracking, niche research, and clip saving with sidebar panel and popup interfaces

#### Frontend
- **Next.js 14 Application** -- App Router with SSR, 13 frontend feature modules, dashboard layout, authentication flows, and design system built on shadcn/ui and Tailwind CSS
- **State Management** -- Zustand for client state, TanStack React Query for server state, WebSocket client with auto-reconnect
- **UI Component Library** -- Reusable layout components, shared utilities, and themed UI primitives

#### Infrastructure & DevOps
- **Docker Compose** -- Full local development environment with 12 services: backend, frontend, PostgreSQL 16, Redis 7, Elasticsearch 8, Celery worker, Celery beat, Flower, Prometheus, and 3 metric exporters
- **Terraform IaC** -- Complete AWS infrastructure: ECS Fargate services, RDS PostgreSQL (multi-AZ production), ElastiCache Redis, OpenSearch, S3, ALB, ECR, VPC networking, SSM secrets
- **CI Pipeline** -- GitHub Actions workflow with backend lint/type-check/test/security-scan, frontend lint/type-check/test/security-scan, Docker build validation, and integration tests
- **Staging Deployment** -- Automatic deploy to ECS on merge to `main` with E2E Playwright tests and Slack notifications
- **Production Deployment** -- Tag-based blue-green deployment via AWS CodeDeploy with health checks, automatic rollback on >1% error rate, and Slack notifications
- **Monitoring Stack** -- Prometheus metrics collection, Datadog APM dashboard (latency P50/P95/P99, error rates, queue depth), Grafana datasources, and 4-tier alert system (P0-P3)

#### Database & Data
- **Complete Schema** -- SQLAlchemy 2.0 async ORM models covering users, organizations, projects, books, content, analytics, agents, publishing, and marketing entities
- **Alembic Migrations** -- Versioned database migration system with upgrade/downgrade support

#### Shared Infrastructure
- **Type Contracts** -- Shared API contracts and module registry between backend and frontend
- **Event System** -- Redis Streams event bus with typed `EventType` enumerations for inter-module communication
- **Celery Task Scheduler** -- Centralized task configuration with per-module task files, dead letter handling, and beat schedule

#### Testing
- **2,183+ Backend Tests Passing** -- Comprehensive test suite covering unit tests, integration tests, e2e tests, and smoke tests across all 29 modules
- **Test Infrastructure** -- Pytest fixtures with async support, test database configuration, CI service containers (PostgreSQL, Redis)
- **Frontend Tests** -- Jest test suite with coverage reporting

#### Documentation
- **Architecture Overview** -- Module dependency graph, tier hierarchy diagram, communication patterns, data flow, and design decision rationale (`docs/architecture.md`)
- **Deployment Guide** -- Environment configuration, deployment procedures, rollback instructions, infrastructure management, monitoring, and common operations (`docs/deploy.md`)
- **AI Development Instructions** -- CLAUDE.md with development process, coding conventions, and automation guidelines

### Infrastructure Details

| Component | Technology | Purpose |
|---|---|---|
| API Runtime | FastAPI on ECS Fargate | REST API with async endpoints |
| Frontend Runtime | Next.js 14 on ECS Fargate | SSR React application |
| Primary Database | PostgreSQL 16 (RDS) | Relational data storage |
| Cache & Broker | Redis 7 (ElastiCache) | Caching, rate limits, pub/sub, Celery broker |
| Search Engine | Elasticsearch 8 / OpenSearch | Full-text search for Knowledge Vault |
| Object Storage | AWS S3 | Book files, covers, exports, assets |
| Task Queue | Celery + Redis | Background job processing |
| Container Registry | AWS ECR | Docker image storage |
| Load Balancer | AWS ALB | Traffic routing and health checks |
| DNS & CDN | AWS CloudFront | Content delivery |
| Secrets | AWS SSM Parameter Store | Encrypted configuration |
| IaC | Terraform | Infrastructure provisioning |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Monitoring | Prometheus + Datadog | Metrics, APM, alerting |

## [Unreleased]

_No unreleased changes at this time._

## [0.9.0] - 2026-02-10

Comprehensive hardening release replacing stubs with real implementations, adding auth enforcement,
real document generation, async database queries, form validation, accessibility improvements,
monitoring fixes, and project governance documentation.

### Added
- Market intelligence auth enforcement on all endpoints with org_id multi-tenancy filtering
- Real PDF generation with ReportLab (title pages, table of contents, chapters, ISBN barcodes)
- Real XLSX export with openpyxl (multi-sheet workbooks with formatting)
- PA-API 5.0 client with HMAC-SHA256 request signing for Amazon Product Advertising API
- Celery task dispatch for publishing operations, analytics pipelines, and competitor finder workflows
- Zod form validation schemas for all frontend forms
- Confirmation dialogs for destructive operations across the UI
- Focus trap for modal accessibility (keyboard navigation support)
- Platform constants module for consistent naming across services
- E2E smoke tests integrated into CI pipeline
- Architecture Decision Records (ADRs) for documenting key design choices
- CONTRIBUTING.md guide with development workflow and contribution standards
- CODEOWNERS file for automated PR review assignment

### Changed
- Portfolio economics router uses real database queries (removed hardcoded placeholder data)
- Audience service functions converted to async with real database queries
- Chrome extension service refactored to use real data aggregation instead of mock data
- Amazon Ads integration raises `AmazonAdsNotConfiguredError` instead of returning silent stubs
- Stripe initialization changed to lazy loading with clear error messaging on misconfiguration
- Config validation now warns about empty optional credentials at startup

### Fixed
- Frontend TypeScript errors including infinite query types and ReactNode type mismatches
- OAuth callback page wrapped in proper Suspense boundary
- Prometheus and AlertManager alert rules updated to use correct metric names
- CI coverage thresholds now properly enforced across backend and frontend
- Market intelligence multi-tenancy with consistent org_id filtering on all queries

### Security
- All market intelligence endpoints now require authentication (previously some were unprotected)
- Added Terraform environment validation documentation for infrastructure security review
