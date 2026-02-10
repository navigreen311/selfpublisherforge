# API Reference

> **Base URL:** `/api/v1`
>
> **Interactive docs:** When the server is running, full interactive documentation is
> available at [`/api/v1/docs`](http://localhost:8000/api/v1/docs) (Swagger UI) and
> [`/api/v1/redoc`](http://localhost:8000/api/v1/redoc) (ReDoc).
>
> **OpenAPI spec:** A machine-readable OpenAPI 3.x JSON spec can be exported by
> running `python -m scripts.export_openapi` from the `backend/` directory, or
> fetched live at `/api/v1/openapi.json`.

---

## Authentication

Most endpoints require a **Bearer token** in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the login or register endpoints and can be refreshed
using the refresh endpoint. Some endpoints (billing plans, health check,
extension version) are publicly accessible without authentication.

---

## Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check and version |
| `GET` | `/api/v1/health` | Service health check (prefixed) |

---

## Auth

Prefix: `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register a new user and organization |
| `POST` | `/auth/login` | Authenticate with email, password, and optional MFA code |
| `POST` | `/auth/refresh` | Refresh an access token using a refresh token |
| `POST` | `/auth/logout` | Invalidate a session (refresh token) |
| `POST` | `/auth/forgot-password` | Request a password-reset email |
| `POST` | `/auth/reset-password` | Reset password with a valid reset token |
| `POST` | `/auth/verify-email` | Verify email address with registration token |
| `POST` | `/auth/mfa/setup` | Generate TOTP secret and backup codes for MFA |
| `POST` | `/auth/mfa/verify` | Verify a TOTP code to finalize MFA activation |
| `POST` | `/auth/mfa/disable` | Disable MFA (requires password confirmation) |
| `GET` | `/auth/oauth/google` | Get Google OAuth2 authorization URL |
| `GET` | `/auth/oauth/google/callback` | Handle Google OAuth2 callback |
| `GET` | `/auth/oauth/github` | Get GitHub OAuth authorization URL |
| `GET` | `/auth/oauth/github/callback` | Handle GitHub OAuth callback |

---

## Users & Settings

Prefix: `/api/v1`

### User Profile

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/me` | Get current user profile |
| `PATCH` | `/users/me` | Update user profile fields |
| `PATCH` | `/users/me/preferences` | Update user preferences (JSONB merge) |

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/me/sessions` | List active login sessions |
| `DELETE` | `/users/me/sessions/{session_id}` | Revoke a specific session |

### Organizations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/orgs/{org_id}` | Get organization details |
| `PATCH` | `/orgs/{org_id}` | Update organization settings (owner/admin) |
| `GET` | `/orgs/{org_id}/members` | List organization members |
| `POST` | `/orgs/{org_id}/invite` | Invite a new member (owner/admin) |
| `PATCH` | `/orgs/{org_id}/members/{user_id}/role` | Change member role (owner only) |
| `DELETE` | `/orgs/{org_id}/members/{user_id}` | Remove a member (owner/admin) |

### API Keys

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/orgs/{org_id}/api-keys` | Create an API key (owner/admin) |
| `GET` | `/orgs/{org_id}/api-keys` | List active API keys |
| `DELETE` | `/orgs/{org_id}/api-keys/{key_id}` | Revoke an API key (owner/admin) |

---

## Writing Studio

Prefix: `/api/v1`

### AI Generation

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate` | Unified AI content generation (SSE streaming or sync) |

### Manuscripts & Chapters

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/books/{book_id}/manuscript` | Get full manuscript with all chapters |
| `GET` | `/books/{book_id}/manuscript/chapters` | List chapters in order |
| `GET` | `/books/{book_id}/manuscript/chapters/{chapter_id}` | Get a single chapter |
| `POST` | `/books/{book_id}/manuscript/chapters` | Create a new chapter |
| `PUT` | `/books/{book_id}/manuscript/chapters/{chapter_id}` | Update chapter title or content |
| `PATCH` | `/books/{book_id}/manuscript/chapters/reorder` | Reorder chapters |

### Analysis

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/books/{book_id}/manuscript/analyze` | Analyze manuscript readability, pacing, word count |
| `GET` | `/books/{book_id}/manuscript/readability-score` | Get Flesch-Kincaid readability metrics |

### Outlines

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/books/{book_id}/outline/generate` | AI-generate a book outline (book-bound) |
| `POST` | `/writing/outline/generate` | AI-generate a standalone book outline |

### Writing Sessions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/writing-sessions` | Record a writing session for productivity tracking |

---

## Style Cloning

Prefix: `/api/v1/style-profiles`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/style-profiles` | Create a new voice/style profile |
| `GET` | `/style-profiles` | List organization style profiles |
| `GET` | `/style-profiles/{profile_id}` | Get profile details and style card |
| `GET` | `/style-profiles/{profile_id}/fingerprint` | Get detailed voice fingerprint |
| `POST` | `/style-profiles/{profile_id}/analyze` | Add samples and re-analyze profile |
| `POST` | `/style-profiles/{profile_id}/generate-sample` | Generate text matching the profile |
| `POST` | `/style-profiles/{profile_id}/conformity-check` | Check text conformity (0-100 score) |
| `DELETE` | `/style-profiles/{profile_id}` | Soft-delete a style profile |

---

## Publishing

Prefix: `/api/v1/publishing`

### Accounts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/publishing/accounts` | List connected publishing platform accounts |
| `POST` | `/publishing/accounts` | Connect a new publishing account (KDP, IngramSpark, etc.) |
| `DELETE` | `/publishing/accounts/{account_id}` | Disconnect a publishing account |

### Export

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/publishing/export/epub` | Generate EPUB from manuscript |
| `POST` | `/publishing/export/pdf` | Generate print-ready PDF |

### Templates

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/publishing/templates` | List formatting templates |
| `POST` | `/publishing/templates` | Create a custom formatting template |

### Book Metadata

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/books/{book_id}/metadata` | Get book metadata (title, keywords, categories) |
| `PATCH` | `/books/{book_id}/metadata` | Update book metadata |

### Listings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/publishing/listings` | List all book listings across platforms |
| `POST` | `/publishing/listings/{listing_id}/sync` | Sync a listing with its platform |

---

## KDP Validation

Prefix: `/api/v1/publishing`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/publishing/validate` | Run full pre-flight validation (print, ebook, cover, compliance) |
| `POST` | `/publishing/validate/print` | Validate print file (margins, bleed, spine, DPI) |
| `POST` | `/publishing/validate/ebook` | Validate ebook (TOC, images, links, file size) |
| `POST` | `/publishing/validate/cover` | Validate cover (resolution, dimensions, safe zones) |
| `GET` | `/publishing/validate/{validation_id}/results` | Get stored validation results |
| `POST` | `/publishing/compliance-scan` | Scan content for policy violations and trademarks |

---

## Production Pipeline

Prefix: `/api/v1/pipelines`

### Templates

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pipelines/templates` | Save a reusable pipeline template |
| `GET` | `/pipelines/templates` | List pipeline templates |

### Pipelines

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pipelines` | Create a new production pipeline |
| `GET` | `/pipelines` | List pipelines (paginated, filterable by status/book) |
| `GET` | `/pipelines/{pipeline_id}` | Get pipeline detail with tasks |
| `PATCH` | `/pipelines/{pipeline_id}` | Update pipeline settings |

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pipelines/{pipeline_id}/tasks` | Add a task to a pipeline |
| `PATCH` | `/pipelines/{pipeline_id}/tasks/{task_id}` | Update task status or assignee |

### Timeline

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/pipelines/{pipeline_id}/timeline` | Get Gantt-style timeline view |

---

## Cover Design Studio

Prefix: `/api/v1/covers`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/covers/generate` | Generate an AI cover concept |
| `GET` | `/covers/templates` | List cover templates by genre |
| `POST` | `/covers/analyze-competitors` | Analyze competitor cover designs |
| `POST` | `/covers/{cover_id}/variations` | Generate variations of a cover |
| `GET` | `/covers/book/{book_id}` | List covers for a book |
| `DELETE` | `/covers/{cover_id}` | Soft-delete a cover |

---

## Product Page Lab

Prefix: `/api/v1/product-page`

### Listing Analysis

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/product-page/analyze` | Analyze an Amazon listing for conversion optimization |

### Blurb Generation & A/B Testing

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/product-page/blurb/generate` | AI-generate optimized blurb variations |
| `POST` | `/product-page/blurb/ab-test` | Create an A/B test for blurbs |
| `GET` | `/product-page/blurb/ab-tests` | List A/B tests |
| `GET` | `/product-page/blurb/ab-test/{test_id}` | Get A/B test by ID |
| `PATCH` | `/product-page/blurb/ab-test/{test_id}` | Update an A/B test |
| `POST` | `/product-page/blurb/ab-test/{test_id}/start` | Start a DRAFT or PAUSED A/B test |
| `GET` | `/product-page/blurb/ab-test/{test_id}/results` | Get detailed A/B test results |

### Additional Analysis

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/product-page/look-inside/analyze` | Analyze Look Inside preview effectiveness |
| `POST` | `/product-page/mobile-check` | Simulate listing appearance on mobile |
| `GET` | `/product-page/scores/{book_id}` | Get conversion optimization scores |

---

## Marketing

Prefix: `/api/v1/marketing`

### Launch Plans

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/marketing/launch-plan/generate` | AI-generate a book launch plan |
| `GET` | `/marketing/launch-plans` | List launch plans (with pagination) |
| `GET` | `/marketing/launch-plans/{plan_id}` | Get full launch plan details |
| `PATCH` | `/marketing/launch-plans/{plan_id}` | Update launch plan |

### Email Sequences

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/marketing/email-sequences` | Create an email marketing sequence |
| `GET` | `/marketing/email-sequences` | List email sequences |
| `PATCH` | `/marketing/email-sequences/{sequence_id}` | Update an email sequence |
| `POST` | `/marketing/email-sequences/{sequence_id}/send` | Trigger sending an email sequence |

### Social Media

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/marketing/social/generate` | AI-generate social media posts |
| `GET` | `/marketing/social/calendar` | Get scheduled social media calendar |

### ARC Campaigns

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/marketing/arc` | Create an ARC (Advanced Reader Copy) campaign |
| `GET` | `/marketing/arc` | List ARC campaigns |
| `POST` | `/marketing/arc/{campaign_id}/send` | Send ARC copies to recipients |

---

## Advertising

Prefix: `/api/v1/ads`

### Campaigns

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ads/campaigns` | List ad campaigns across platforms |
| `POST` | `/ads/campaigns` | Create a new ad campaign |
| `GET` | `/ads/campaigns/{campaign_id}` | Get campaign detail with performance |
| `PATCH` | `/ads/campaigns/{campaign_id}` | Update campaign settings |
| `GET` | `/ads/campaigns/{campaign_id}/performance` | Get detailed performance data |
| `POST` | `/ads/campaigns/{campaign_id}/optimize` | AI-optimize bids and targeting |

### Keyword Bids

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ads/keyword-bids` | List keyword bids |
| `PATCH` | `/ads/keyword-bids` | Bulk update keyword bids |

### Creatives

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ads/creatives/generate` | AI-generate ad copy and headlines |
| `GET` | `/ads/creatives` | List ad creatives with performance data |

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ads/dashboard` | Aggregate advertising performance dashboard |

### Facebook Ads

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ads/facebook/campaigns` | Create a Facebook ad campaign |
| `GET` | `/ads/facebook/campaigns` | List Facebook campaigns |
| `GET` | `/ads/facebook/campaigns/{campaign_id}` | Get Facebook campaign details |
| `PATCH` | `/ads/facebook/campaigns/{campaign_id}` | Update Facebook campaign |
| `POST` | `/ads/facebook/campaigns/{campaign_id}/pause` | Pause a Facebook campaign |
| `GET` | `/ads/facebook/campaigns/{campaign_id}/metrics` | Get Facebook campaign metrics |

---

## Review Intelligence

Prefix: `/api/v1/reviews`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/reviews` | List reviews for organization books |
| `GET` | `/reviews/book/{book_id}` | Get reviews for a specific book |
| `GET` | `/reviews/sentiment/{book_id}` | Get sentiment breakdown and key themes |
| `GET` | `/reviews/velocity/{book_id}` | Get review velocity over time |
| `GET` | `/reviews/alerts` | List review alerts (negative, velocity drop, etc.) |
| `PATCH` | `/reviews/alerts/{alert_id}/acknowledge` | Acknowledge a review alert |
| `POST` | `/reviews/analyze` | Batch analyze reviews (themes, complaints, praise) |
| `GET` | `/reviews/reputation/{book_id}` | Get reputation score and health metrics |
| `POST` | `/reviews/acquisition/tips` | Get AI tips for improving review acquisition |

---

## Analytics

Prefix: `/api/v1/analytics`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics/dashboard` | Main analytics dashboard with KPIs and trends |
| `GET` | `/analytics/revenue` | Revenue data by book, date range, platform |
| `GET` | `/analytics/royalties` | List royalty records (paginated) |
| `POST` | `/analytics/royalties/import` | Import royalty data from CSV |
| `GET` | `/analytics/portfolio` | Portfolio-level metrics (books, revenue, ROI) |
| `POST` | `/analytics/reports/generate` | Generate a custom report (PDF or XLSX) |
| `GET` | `/analytics/reports` | List generated reports |
| `GET` | `/analytics/reports/{report_id}/download` | Download a completed report |
| `POST` | `/analytics/events` | Record a custom analytics event |
| `GET` | `/analytics/trends` | Trend data for key metrics |

---

## Market Intelligence

Prefix: `/api/v1/market`

### Categories

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/market/categories` | Browse Amazon category taxonomy |
| `GET` | `/market/categories/{category_id}/analysis` | Category analysis with BSR and competition |

### Keywords

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/market/keywords/research` | Research keywords (volume, competition, CPC) |
| `GET` | `/market/keywords/suggestions` | AI-suggested keywords for a genre |

### Niche Analysis

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/market/analyze-niche` | Comprehensive niche analysis with scoring |

### Competitors

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/market/competitors` | List tracked competitor books |
| `POST` | `/market/competitors/track` | Start tracking a competitor by ASIN |
| `GET` | `/market/competitors/{competitor_id}` | Get competitor detail with BSR history |

### Trends & Snapshots

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/market/trends` | Market trend data for categories and keywords |
| `GET` | `/market/snapshots` | Daily category snapshots |

---

## Competitor Weakness Finder

Prefix: `/api/v1/competitors`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/competitors/analyze` | Deep analyze a competitor book |
| `GET` | `/competitors/{analysis_id}/weaknesses` | Get detected weakness signals |
| `POST` | `/competitors/batch-analyze` | Batch analyze top N books in a category |
| `GET` | `/competitors/{analysis_id}/opportunity` | Get AI opportunity blueprint |
| `POST` | `/competitors/gap-analysis` | Cover/title/content gap analysis |
| `GET` | `/competitors/alerts` | Get competitor alerts (price, BSR, reviews) |

---

## Pricing Automation

Prefix: `/api/v1/pricing`

### Rules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/pricing/rules` | List pricing rules |
| `POST` | `/pricing/rules` | Create an automated pricing rule |
| `PATCH` | `/pricing/rules/{rule_id}` | Update a pricing rule |
| `DELETE` | `/pricing/rules/{rule_id}` | Delete a pricing rule |

### Simulation & Competitor Pricing

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pricing/simulate` | Simulate price change impact |
| `GET` | `/pricing/competitors/{book_id}` | Get competitor pricing data |

### A/B Tests & Promotions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pricing/ab-test` | Create a pricing A/B test |
| `GET` | `/pricing/promotions` | Get promotional calendar |
| `POST` | `/pricing/promotions` | Schedule a promotion |

### KU Calculator

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pricing/ku-calculator` | KU vs. wide distribution revenue calculator |

---

## Knowledge Vault

Prefix: `/api/v1/knowledge`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/knowledge` | Create a knowledge entry |
| `GET` | `/knowledge` | List knowledge entries (paginated, filterable) |
| `GET` | `/knowledge/{entry_id}` | Get knowledge entry detail |
| `PUT` | `/knowledge/{entry_id}` | Update a knowledge entry |
| `DELETE` | `/knowledge/{entry_id}` | Soft-delete a knowledge entry |
| `POST` | `/knowledge/{entry_id}/summarize` | AI-summarize a knowledge entry |
| `POST` | `/knowledge/search` | Full-text search via Elasticsearch |
| `POST` | `/knowledge/import` | Import from URL or file with AI extraction |
| `GET` | `/knowledge/tags` | List all unique tags |
| `GET` | `/knowledge/suggestions` | AI-suggested research topics |

---

## Portfolio Economics

Prefix: `/api/v1/portfolio`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/portfolio` | Portfolio overview (books, revenue, ROI, projections) |
| `POST` | `/portfolio/greenlight` | Pre-writing ROI forecast for a book idea |
| `POST` | `/portfolio/kill-scale` | Kill/scale recommendation for an existing book |
| `GET` | `/portfolio/backlist` | Backlist compounding revenue projections |
| `GET` | `/portfolio/recommendations` | AI portfolio optimization recommendations |

---

## Audience DNA

Prefix: `/api/v1/audience`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/audience/analyze` | Build audience personas from book/market data |
| `GET` | `/audience/personas/{book_id}` | Get reader personas for a book |
| `GET` | `/audience/also-bought/{book_id}` | Also-bought intelligence |
| `GET` | `/audience/growth` | Audience growth tracking over time |
| `POST` | `/audience/churn-prediction` | Predict churn risk for reader engagement |

---

## Seasonal Calendar

Prefix: `/api/v1/seasonal`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/seasonal/calendar` | Full seasonal calendar with niche events |
| `GET` | `/seasonal/niche/{genre}` | Seasonality data for a specific genre |
| `POST` | `/seasonal/recommend-launch` | AI-recommend optimal launch date |
| `GET` | `/seasonal/events` | Upcoming events relevant to genres |

---

## Billing

Prefix: `/api/v1/billing`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/billing/plans` | List available billing plans (public, no auth) |
| `GET` | `/billing/subscription` | Get current subscription details |
| `POST` | `/billing/subscribe` | Create a Stripe Checkout session (owner/admin) |
| `POST` | `/billing/portal` | Create a Stripe billing portal session |
| `POST` | `/billing/webhook` | Handle Stripe webhook events (signature auth) |
| `GET` | `/billing/usage` | Get usage statistics (API calls, storage, AI tokens) |
| `GET` | `/billing/invoices` | List invoices |

---

## Storage

Prefix: `/api/v1/storage`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/storage/upload` | Request a presigned S3 upload URL |
| `POST` | `/storage/upload/complete` | Confirm file upload completion |
| `GET` | `/storage/assets` | List organization assets |
| `GET` | `/storage/assets/{asset_id}` | Get asset detail with download URL |
| `DELETE` | `/storage/assets/{asset_id}` | Soft-delete an asset |
| `POST` | `/storage/assets/{asset_id}/process` | Trigger asset processing (resize, parse) |

---

## Notifications

Prefix: `/api/v1/notifications`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/notifications` | List notifications (paginated, newest first) |
| `PATCH` | `/notifications/{notification_id}/read` | Mark a notification as read |
| `POST` | `/notifications/read-all` | Mark all notifications as read |
| `GET` | `/notifications/unread-count` | Get unread notification count |
| `GET` | `/notifications/preferences` | Get notification preferences |
| `PATCH` | `/notifications/preferences` | Update notification preferences |

---

## AI Agents

Prefix: `/api/v1/agents`

### Agents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/agents` | List available AI agent types |
| `GET` | `/agents/{agent_id}/config` | Get agent configuration |
| `PATCH` | `/agents/{agent_id}/config` | Update agent config (admin/owner) |

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents/tasks` | Create a new agent task |
| `GET` | `/agents/tasks` | List agent tasks (filterable) |
| `GET` | `/agents/tasks/{task_id}` | Get task detail |
| `POST` | `/agents/tasks/{task_id}/approve` | Approve task output |
| `POST` | `/agents/tasks/{task_id}/reject` | Reject task output |
| `POST` | `/agents/tasks/{task_id}/cancel` | Cancel a task |

### Workflows

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents/workflows` | Create a multi-step workflow |
| `GET` | `/agents/workflows` | List workflows |

### Budgets & Controls

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/agents/budgets` | Get agent budget status |
| `PATCH` | `/agents/budgets` | Update agent budget limits (admin/owner) |
| `POST` | `/agents/emergency-stop` | Emergency stop all agents (admin/owner) |
| `GET` | `/agents/audit` | Get agent audit trail |

---

## LLM Orchestration

Prefix: `/api/v1/llm`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/llm/status` | LLM orchestration health and status |
| `GET` | `/llm/models` | List supported LLM models with providers |
| `GET` | `/llm/routes` | List task-type to model routing config |

---

## Chrome Extension

Prefix: `/api/v1/extension`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/extension/version` | Get current published extension version (public) |
| `POST` | `/extension/extract` | Save extracted Amazon product data |
| `GET` | `/extension/quick-research` | Quick niche research data for sidebar |
| `POST` | `/extension/clip` | Save a clip to the Knowledge Vault |

---

## WebSocket (Real-time)

| Path | Description |
|------|-------------|
| `/ws/notifications` | Real-time notification delivery |
| `/ws/collaboration` | Real-time document collaboration |
| `/ws/pipeline` | Real-time pipeline status updates |
| `/ws/analytics` | Real-time analytics streaming |

WebSocket connections require a `token` query parameter containing a valid JWT.
