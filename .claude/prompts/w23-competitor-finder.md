# W23: SERP & Competitor Weakness Finder (Module #17)
**Branch:** `ai-feature/competitor-finder`
**Scope:** api

## Mission
Build the Competitor Weakness Finder: review scraping and NLP analysis, weakness signal detection, opportunity blueprint generation, cover/title gap alerts.

## API Endpoints
- POST /api/v1/competitors/analyze — Deep analyze a competitor book (reviews, listing, positioning)
- GET /api/v1/competitors/{id}/weaknesses — Get detected weaknesses from reviews
- POST /api/v1/competitors/batch-analyze — Analyze top N books in a category
- GET /api/v1/competitors/{id}/opportunity — Get opportunity blueprint (how to beat this competitor)
- POST /api/v1/competitors/gap-analysis — Cover/title/content gap analysis for a niche
- GET /api/v1/competitors/alerts — Get competitor alerts (price changes, new books, BSR shifts)

## Weakness Signal Types
- Content quality complaints (shallow, outdated, errors)
- Format/layout issues (poor formatting, no TOC, bad images)
- Missing features (no workbook, no audio, no updates)
- Pricing complaints (too expensive, no value)
- Coverage gaps (topics not addressed, incomplete)

## What to Build

### Backend
1. **backend/app/modules/competitor_finder/__init__.py**
2. **backend/app/modules/competitor_finder/router.py** — All endpoints
3. **backend/app/modules/competitor_finder/schemas.py** — CompetitorAnalysis, WeaknessSignal, OpportunityBlueprint, GapAnalysis
4. **backend/app/modules/competitor_finder/service.py** — Analysis orchestration, alert management
5. **backend/app/modules/competitor_finder/review_analyzer.py** — NLP analysis of reviews: sentiment scoring, weakness signal extraction (AI-powered), complaint categorization
6. **backend/app/modules/competitor_finder/opportunity_generator.py** — AI: generate opportunity blueprint from weakness data (how to write a better book)
7. **backend/app/modules/competitor_finder/gap_detector.py** — Cover style gaps, title pattern gaps, content coverage gaps
8. **backend/app/tasks/competitor_finder.py** — Celery: async batch analysis, periodic alert checks

### Tests
9. **backend/tests/unit/test_review_analyzer.py**
10. **backend/tests/unit/test_gap_detector.py**
11. **backend/tests/integration/test_competitor_api.py**

## Database Tables (from W02, read-only)
competitor_books, competitor_reviews

## Commit Convention
`feat(competitor): implement competitor weakness finder with review NLP and opportunity blueprints`
