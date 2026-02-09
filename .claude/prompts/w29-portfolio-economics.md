# W29: Portfolio Economics + Audience DNA + Seasonal Calendar (Modules #16, #26, #27)
**Branch:** `ai-feature/portfolio-economics`
**Scope:** api

## Mission
Build three related intelligence modules: Portfolio Economics Engine (pre-writing ROI forecast, kill/scale decisions, backlist compounding), Audience DNA Builder (reader persona, also-bought intelligence), and Seasonal Publishing Calendar (niche seasonality, launch date recommendations).

## API Endpoints

### Portfolio Economics
- GET /api/v1/portfolio — Portfolio overview (total books, revenue, ROI, projections)
- POST /api/v1/portfolio/greenlight — Greenlight Gate: pre-writing ROI forecast for a book idea
- POST /api/v1/portfolio/kill-scale — Kill/scale recommendation for existing books
- GET /api/v1/portfolio/backlist — Backlist compounding planner: revenue projections over 1/3/5 years
- GET /api/v1/portfolio/recommendations — AI recommendations for portfolio optimization

### Audience DNA
- POST /api/v1/audience/analyze — Build audience profile from book data and market research
- GET /api/v1/audience/personas/{book_id} — Reader personas for a book
- GET /api/v1/audience/also-bought/{book_id} — Also-bought intelligence
- GET /api/v1/audience/growth — Audience growth tracking
- POST /api/v1/audience/churn-prediction — Churn prediction for reader engagement

### Seasonal Calendar
- GET /api/v1/seasonal/calendar — Full seasonal calendar with niche-specific events
- GET /api/v1/seasonal/niche/{genre} — Seasonality data for a niche/genre
- POST /api/v1/seasonal/recommend-launch — AI recommend optimal launch date
- GET /api/v1/seasonal/events — Upcoming events and triggers relevant to user's genres

## What to Build

### Backend
1. **backend/app/modules/portfolio_economics/__init__.py**
2. **backend/app/modules/portfolio_economics/router.py** — Portfolio + Audience + Seasonal endpoints
3. **backend/app/modules/portfolio_economics/schemas.py** — GreenlightResult, KillScaleDecision, BacklistProjection, AudiencePersona, AlsoBought, SeasonalEvent, LaunchRecommendation
4. **backend/app/modules/portfolio_economics/portfolio_service.py** — ROI forecasting, kill/scale algorithm, backlist projections
5. **backend/app/modules/portfolio_economics/greenlight.py** — Pre-writing ROI forecast: market size * capture rate * price * royalty rate - costs = projected ROI
6. **backend/app/modules/portfolio_economics/backlist.py** — Compounding revenue model: monthly decay rate, promotion boosts, series multiplier
7. **backend/app/modules/portfolio_economics/audience_service.py** — Audience analysis, persona generation, also-bought graph, churn prediction
8. **backend/app/modules/portfolio_economics/seasonal_service.py** — Seasonality data, event calendar, launch date optimization
9. **backend/app/tasks/portfolio_economics.py** — Celery: daily portfolio metric snapshots, audience data refresh

### Tests
10. **backend/tests/unit/test_greenlight.py** — Test ROI forecasting
11. **backend/tests/unit/test_backlist.py** — Test compounding revenue model
12. **backend/tests/integration/test_portfolio_api.py**

## Database Tables (from W02, read-only)
portfolio_metrics, analytics_events, royalty_records

## Commit Convention
`feat(portfolio): implement portfolio economics, audience DNA, and seasonal calendar`
