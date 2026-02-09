# W25: Advertising Intelligence (Module #8)
**Branch:** `ai-feature/advertising-intelligence`
**Scope:** fullstack

## Mission
Build the Advertising Intelligence system: Amazon Ads integration, Facebook Ads integration, campaign management, keyword bid optimization, ACOS tracking, and AI ad creative generation.

## API Endpoints
- GET /api/v1/ads/campaigns — List ad campaigns (across platforms)
- POST /api/v1/ads/campaigns — Create campaign
- GET /api/v1/ads/campaigns/{id} — Campaign detail with performance metrics
- PATCH /api/v1/ads/campaigns/{id} — Update campaign
- GET /api/v1/ads/campaigns/{id}/performance — Detailed performance (impressions, clicks, spend, sales, ACOS)
- POST /api/v1/ads/campaigns/{id}/optimize — AI optimize bids/targeting
- GET /api/v1/ads/keyword-bids — Current keyword bids
- PATCH /api/v1/ads/keyword-bids — Update bids
- POST /api/v1/ads/creatives/generate — AI generate ad copy/headlines
- GET /api/v1/ads/creatives — List ad creatives with performance
- GET /api/v1/ads/dashboard — Aggregate ad performance dashboard

## What to Build

### Backend
1. **backend/app/modules/advertising/__init__.py**
2. **backend/app/modules/advertising/router.py** — All endpoints
3. **backend/app/modules/advertising/schemas.py** — AdCampaign, AdPerformance, KeywordBid, AdCreative, OptimizationSuggestion
4. **backend/app/modules/advertising/service.py** — Campaign CRUD, performance aggregation, optimization orchestration
5. **backend/app/modules/advertising/amazon_ads.py** — Amazon Ads API client: campaign management, keyword targeting, bid management, reporting
6. **backend/app/modules/advertising/facebook_ads.py** — Facebook Ads API client (placeholder): campaign creation, audience targeting, reporting
7. **backend/app/modules/advertising/optimizer.py** — AI bid optimization: analyze performance data, suggest bid adjustments, ACOS target enforcement
8. **backend/app/modules/advertising/creative_generator.py** — AI: generate ad headlines, copy, from book data and market research
9. **backend/app/tasks/advertising.py** — Celery: periodic performance sync, auto-optimize bids, budget alerts

### Frontend
10. **frontend/src/app/(dashboard)/advertising/page.tsx** — Ad dashboard: total spend, ACOS, ROI, active campaigns
11. **frontend/src/app/(dashboard)/advertising/campaigns/page.tsx** — Campaign list with filters and performance summary
12. **frontend/src/app/(dashboard)/advertising/campaigns/[id]/page.tsx** — Campaign detail: performance charts, keyword bids, creatives
13. **frontend/src/modules/advertising/hooks.ts** — React Query hooks
14. **frontend/src/modules/advertising/components/** — PerformanceChart, CampaignCard, BidManager, CreativeEditor

### Tests
15. **backend/tests/unit/test_ad_optimizer.py**
16. **backend/tests/integration/test_advertising_api.py**

## Database Tables (from W02, read-only)
campaigns, ad_creatives

## Commit Convention
`feat(ads): implement advertising intelligence with bid optimization and creative generation`
