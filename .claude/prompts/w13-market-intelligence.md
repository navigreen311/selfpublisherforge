# W13: Market Intelligence Engine (Module #1)
**Branch:** `ai-feature/market-intelligence`
**Scope:** fullstack

## Mission
Build the Market Intelligence Engine: Amazon category browser, keyword research tool, competitor tracking, niche scoring algorithm, and market trends dashboard.

## API Endpoints
- GET /api/v1/market/categories — Browse Amazon category taxonomy (tree structure)
- GET /api/v1/market/categories/{id}/analysis — Category analysis with BSR distribution, competition score
- POST /api/v1/market/keywords/research — Keyword research: search volume, competition, CPC, trends
- GET /api/v1/market/keywords/suggestions — AI-suggested keywords for a genre/niche
- POST /api/v1/market/analyze-niche — Comprehensive niche analysis (demand_score, supply_score, opportunity_score 0-100, top_competitors, gap_analysis)
- GET /api/v1/market/competitors — List tracked competitor books
- POST /api/v1/market/competitors/track — Start tracking a competitor (by ASIN)
- GET /api/v1/market/competitors/{id} — Competitor detail with BSR history
- GET /api/v1/market/trends — Market trend data for categories and keywords
- GET /api/v1/market/snapshots — Daily category snapshots

## What to Build

### Backend
1. **backend/app/modules/market_intelligence/__init__.py**
2. **backend/app/modules/market_intelligence/router.py** — All endpoints above
3. **backend/app/modules/market_intelligence/schemas.py** — NicheAnalysisRequest, NicheAnalysisResponse (demand_score, supply_score, opportunity_score, top_competitors, gap_analysis), KeywordResearchRequest/Response, CategoryTree, CompetitorDetail
4. **backend/app/modules/market_intelligence/service.py** — Niche scoring algorithm, keyword analysis, competitor tracking
5. **backend/app/modules/market_intelligence/amazon_client.py** — Amazon Product API client (with mock for development)
6. **backend/app/modules/market_intelligence/scoring.py** — Niche scoring: demand (search volume, BSR distribution, trend) + supply (title count, review barriers, quality) = opportunity
7. **backend/app/tasks/market_intelligence.py** — Celery tasks: refresh category data, update BSR history, generate market snapshots

### Frontend
8. **frontend/src/app/(dashboard)/market/page.tsx** — Market intelligence dashboard: search bar, category tree, niche analysis results
9. **frontend/src/app/(dashboard)/market/keywords/page.tsx** — Keyword research tool
10. **frontend/src/app/(dashboard)/market/competitors/page.tsx** — Competitor tracking list with BSR charts
11. **frontend/src/modules/market/hooks.ts** — React Query hooks
12. **frontend/src/modules/market/components/** — CategoryTree, NicheScoreCard, KeywordTable, CompetitorChart, TrendChart

### Tests
13. **backend/tests/unit/test_market_scoring.py** — Test niche scoring algorithm
14. **backend/tests/integration/test_market_api.py** — Test all market endpoints

## Database Tables (from W02, read-only)
market_categories, market_keywords, competitor_books, competitor_reviews, market_snapshots

## Commit Convention
`feat(market): implement market intelligence engine with niche analysis and competitor tracking`
