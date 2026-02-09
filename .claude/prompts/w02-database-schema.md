# W02: Database Schema & Alembic Migrations
**Branch:** `ai-feature/database-schema`
**Scope:** api

## Mission
Create ALL SQLAlchemy models and Alembic migrations for the entire platform's database schema. This is the foundation that every other module depends on.

## What to Build

### SQLAlchemy Models
Create one model file per domain area in `backend/app/models/`:

1. **backend/app/models/organization.py** — Organization model:
   - id (UUID PK), name, slug (unique), plan_tier (enum), subscription_status, settings (JSONB), limits (JSONB), created_at, updated_at, deleted_at

2. **backend/app/models/user.py** — User, ApiKey, UserSession models:
   - users: id, org_id (FK), email (unique), password_hash, name, role (enum: owner/admin/editor/writer/viewer), preferences (JSONB), onboarding_state, email_verified_at
   - api_keys: id, org_id, user_id (FK), key_hash, name, scopes (ARRAY), last_used_at, expires_at
   - user_sessions: id, user_id (FK), token_hash, device_info (JSONB), ip_address, expires_at

3. **backend/app/models/project.py** — Project, Book, Series, PenName, BookVersion:
   - projects: id, org_id, title, type (enum: book/series/course), status, settings (JSONB), pen_name_id (FK nullable)
   - books: id, project_id (FK), title, subtitle, isbn, asin, format (enum: ebook/print/audio), status, metadata (JSONB)
   - series: id, org_id, name, genre_id, book_order (ARRAY), reading_order (ARRAY), status
   - pen_names: id, org_id, name, bio, brand_guidelines (JSONB), active (bool)
   - book_versions: id, book_id (FK), version_number (int), manuscript_url, changelog (TEXT), created_by (FK)

4. **backend/app/models/content.py** — Manuscript, Chapter, StyleProfile, WritingSession, ContentAsset:
   - manuscripts: id, book_id (FK), content_type (enum), content (TEXT), word_count, status
   - chapters: id, manuscript_id (FK), title, order_index (int), content (TEXT), word_count, status, ai_metrics (JSONB)
   - style_profiles: id, org_id, name, voice_fingerprint (JSONB), vocabulary_stats (JSONB), sentence_patterns (JSONB), sample_sources (ARRAY)
   - writing_sessions: id, user_id, book_id, chapter_id, words_written, duration_seconds, ai_assists_used
   - content_assets: id, org_id, asset_type, file_url, file_size, mime_type, metadata (JSONB)

5. **backend/app/models/market.py** — MarketCategory, MarketKeyword, CompetitorBook, CompetitorReview, MarketSnapshot:
   - market_categories: id, amazon_node_id, name, path (ARRAY), parent_id, book_count, avg_bsr, competition_score
   - market_keywords: id, keyword, search_volume, competition_score, cpc_estimate, trend_direction, last_updated
   - competitor_books: id, asin, title, author, bsr_current, bsr_history (JSONB), price, reviews_count, rating, category_ids (ARRAY)
   - competitor_reviews: id, competitor_book_id (FK), rating, review_text, sentiment_score, weakness_signals (JSONB), date
   - market_snapshots: id, category_id (FK), snapshot_date, top_100_asins (ARRAY), metrics (JSONB)

6. **backend/app/models/publishing.py** — PublishingAccount, Listing, UploadValidation, ComplianceScan, PricingRule:
   - publishing_accounts: id, org_id, platform (enum: kdp/ingramspark/d2d/acx), credentials_encrypted (TEXT), status, health_score
   - listings: id, book_id (FK), publishing_account_id (FK), platform_id, status, listing_data (JSONB), last_synced
   - upload_validations: id, book_id (FK), validation_type (enum), results (JSONB), passed (bool), errors (ARRAY), warnings (ARRAY)
   - compliance_scans: id, book_id, scan_type, findings (JSONB), risk_level (enum: green/yellow/red), reviewed_by
   - pricing_rules: id, book_id, strategy, rules (JSONB), current_price (Numeric), last_adjusted

7. **backend/app/models/marketing.py** — Campaign, AdCreative, LaunchPlan, EmailSequence, ReaderPanel:
   - campaigns: id, org_id, book_id (FK), platform (enum), status, budget (Numeric), spend (Numeric), results (JSONB)
   - ad_creatives: id, campaign_id (FK), type (enum), content (TEXT), performance (JSONB), active (bool)
   - launch_plans: id, book_id, launch_date, phases (JSONB), status, checklist (JSONB)
   - email_sequences: id, org_id, name, trigger, emails (JSONB), subscriber_count, performance (JSONB)
   - reader_panels: id, org_id, name, panel_size, recruitment_criteria (JSONB), tests (ARRAY)

8. **backend/app/models/agent.py** — Agent, AgentTask, AgentWorkflow, AgentBudget, AuditTrail:
   - agents: id, org_id, agent_type (enum), name, configuration (JSONB), permission_level (enum), active
   - agent_tasks: id, agent_id (FK), task_type, input (JSONB), output (JSONB), status, cost_tokens, cost_usd (Numeric), quality_score (Float)
   - agent_workflows: id, org_id, name, steps (JSONB), trigger_conditions (JSONB), active
   - agent_budgets: id, org_id, budget_type (enum), limit_value (Numeric), spent_value (Numeric), period, alerts_sent (int)
   - audit_trail: id, org_id, actor_type (enum), actor_id, action, resource_type, resource_id, details (JSONB), timestamp

9. **backend/app/models/analytics.py** — AnalyticsEvent, RoyaltyRecord, PortfolioMetric, ABTest, Report:
   - analytics_events: id, org_id, event_type, entity_type, entity_id, data (JSONB), timestamp (partitioned by month)
   - royalty_records: id, book_id, platform, period_start, period_end, units_sold, revenue (Numeric), royalty (Numeric), currency
   - portfolio_metrics: id, org_id, snapshot_date, total_books, total_revenue (Numeric), roi_by_book (JSONB), projections (JSONB)
   - ab_tests: id, entity_type, entity_id, variants (JSONB), traffic_split (Float), status, results (JSONB), winner_id
   - reports: id, org_id, report_type, parameters (JSONB), generated_url, status, created_at

10. **backend/app/models/__init__.py** — Import all models so Alembic can discover them

### Migrations
11. **Create initial Alembic migration** that creates all tables. Use `alembic revision --autogenerate -m "initial_schema"` pattern but write it manually since we can't run Alembic without a DB.

### Indexes
Add all indexes specified in the blueprint:
- B-tree on all FKs (org_id, user_id, book_id, project_id)
- B-tree on status columns
- GIN on all JSONB columns
- GIN on ARRAY columns
- Full-text indexes on chapters.content, competitor_reviews.review_text
- BRIN on analytics_events.timestamp, audit_trail.timestamp
- Partial indexes WHERE deleted_at IS NULL
- Composite (org_id, created_at DESC) on high-traffic tables

### Tests
12. **backend/tests/unit/test_models.py** — Test model instantiation, relationships, default values, soft delete behavior

## Read-Only (do NOT modify)
- backend/app/database.py (use Base and BaseModel from there)
- backend/app/config.py
- backend/app/main.py
- backend/app/core/security.py, dependencies.py, exceptions.py, pagination.py
- backend/app/schemas/common.py
- frontend/src/app/layout.tsx, frontend/src/components/providers.tsx
- frontend/src/lib/utils.ts, frontend/src/lib/api.ts
- frontend/src/types/index.ts
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
`feat: add complete database schema and migrations`
