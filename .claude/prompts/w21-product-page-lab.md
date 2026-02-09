# W21: Product Page Conversion Lab (Module #15)
**Branch:** `ai-feature/product-page-lab`
**Scope:** fullstack

## Mission
Build the Product Page Conversion Lab: Amazon listing analyzer, blurb A/B simulator, Look Inside optimizer, and mobile conversion checker.

## API Endpoints
- POST /api/v1/product-page/analyze — Analyze an Amazon listing (by ASIN or URL)
- POST /api/v1/product-page/blurb/generate — AI-generate optimized blurb variations
- POST /api/v1/product-page/blurb/ab-test — Create A/B test for blurbs
- GET /api/v1/product-page/blurb/ab-test/{id} — Get A/B test results
- POST /api/v1/product-page/look-inside/analyze — Analyze Look Inside preview effectiveness
- POST /api/v1/product-page/mobile-check — Check listing appearance on mobile
- GET /api/v1/product-page/scores/{book_id} — Get conversion optimization scores

## What to Build

### Backend
1. **backend/app/modules/product_page_lab/__init__.py**
2. **backend/app/modules/product_page_lab/router.py** — All endpoints
3. **backend/app/modules/product_page_lab/schemas.py** — ListingAnalysis(title_score, blurb_score, keyword_score, category_score, price_score, overall_score, recommendations[]), BlurbVariant, ABTestConfig, MobileCheckResult
4. **backend/app/modules/product_page_lab/service.py** — Listing analysis, blurb generation, A/B test management
5. **backend/app/modules/product_page_lab/analyzer.py** — Title analysis (keyword presence, length, power words), blurb analysis (hooks, bullet points, CTA, HTML formatting), keyword density, category fit
6. **backend/app/modules/product_page_lab/blurb_generator.py** — AI blurb generation with genre-specific templates, A/B variant creation
7. **backend/app/modules/product_page_lab/mobile_checker.py** — Simulate mobile display: title truncation, blurb fold point, image sizing

### Frontend
8. **frontend/src/app/(dashboard)/product-page/page.tsx** — Product page lab: ASIN input, analysis results, optimization scores
9. **frontend/src/app/(dashboard)/product-page/blurb/page.tsx** — Blurb editor with AI generation and A/B testing
10. **frontend/src/modules/product-page/hooks.ts** — React Query hooks
11. **frontend/src/modules/product-page/components/** — ListingScoreCard, BlurbEditor, ABTestPanel, MobilePreview

### Tests
12. **backend/tests/unit/test_listing_analyzer.py**
13. **backend/tests/integration/test_product_page_api.py**

## Database Tables (from W02, read-only)
ab_tests

## Commit Convention
`feat(product-page): implement product page conversion lab with blurb optimization and A/B testing`
