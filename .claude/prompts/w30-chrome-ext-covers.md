# W30: Chrome Extension + Cover & Visual Design Studio (Modules #5 + Chrome Ext)
**Branch:** `ai-feature/chrome-ext-covers`
**Scope:** ui

## Mission
Build the Chrome Extension (Manifest V3) for Amazon data extraction and quick research, plus the Cover & Visual Design Studio for AI-generated covers.

## Chrome Extension Features
- Amazon product page data extraction (title, BSR, price, reviews, categories, keywords)
- Competitor BSR tracking sidebar
- Quick niche research panel
- One-click save to SelfPublisherForge account
- Knowledge Vault clip-and-save

## Cover Design Features
- AI-generated cover concepts (via DALL-E / Midjourney API placeholder)
- Template library (by genre)
- Batch cover generation for A/B testing
- Competitor cover analysis
- Cover dimension validation per platform

## API Endpoints (backend)

### Covers
- POST /api/v1/covers/generate — Generate cover concept via AI
- GET /api/v1/covers/templates — List cover templates by genre
- POST /api/v1/covers/analyze-competitors — Analyze competitor covers in a niche
- POST /api/v1/covers/{id}/variations — Generate variations of a cover
- GET /api/v1/covers/book/{book_id} — List covers for a book
- DELETE /api/v1/covers/{id} — Delete cover

### Chrome Extension API
- POST /api/v1/extension/extract — Save extracted Amazon data
- GET /api/v1/extension/quick-research — Quick niche data for sidebar
- POST /api/v1/extension/clip — Save clip to Knowledge Vault

## What to Build

### Chrome Extension (new directory: extension/)
1. **extension/manifest.json** — Manifest V3: permissions, content scripts, popup, background service worker
2. **extension/popup/popup.html** — Extension popup: login status, quick actions
3. **extension/popup/popup.js** — Popup logic: auth check, API calls
4. **extension/content/amazon-extractor.js** — Content script: extract data from Amazon product pages (title, BSR, price, reviews, categories, keywords from page DOM)
5. **extension/sidebar/sidebar.html** — Research sidebar overlay
6. **extension/sidebar/sidebar.js** — Sidebar logic: display niche data, competitor info
7. **extension/background/service-worker.js** — Background: API communication, data sync, auth token management
8. **extension/styles/popup.css** — Extension styling

### Backend (Cover Design)
9. **backend/app/modules/cover_design/__init__.py**
10. **backend/app/modules/cover_design/router.py** — All cover endpoints
11. **backend/app/modules/cover_design/schemas.py** — CoverGenerateRequest, CoverResponse, CoverTemplate, CompetitorCoverAnalysis
12. **backend/app/modules/cover_design/service.py** — Cover generation orchestration, template management, competitor analysis
13. **backend/app/modules/cover_design/generator.py** — AI cover generation: build prompt from genre/mood/elements, call image generation API, post-process
14. **backend/app/modules/cover_design/templates.py** — Built-in cover templates: romance, thriller, sci-fi, nonfiction, children's, etc. (dimension specs, font recommendations, layout guidance)
15. **backend/app/modules/cover_design/analyzer.py** — Analyze competitor covers: dominant colors, text placement, imagery style

### Backend (Extension API)
16. **backend/app/modules/chrome_extension/__init__.py**
17. **backend/app/modules/chrome_extension/router.py** — Extension endpoints
18. **backend/app/modules/chrome_extension/schemas.py** — ExtractedData, QuickResearch, ClipData
19. **backend/app/modules/chrome_extension/service.py** — Save extracted data, serve quick research, clip to knowledge vault

### Tests
20. **backend/tests/unit/test_cover_generator.py**
21. **backend/tests/integration/test_cover_api.py**
22. **backend/tests/integration/test_extension_api.py**

## Commit Convention
`feat(covers+ext): implement cover design studio and Chrome extension for Amazon research`
