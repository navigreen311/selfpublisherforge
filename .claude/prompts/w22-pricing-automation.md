# W22: Intelligent Pricing Automation (Module #22)
**Branch:** `ai-feature/pricing-automation`
**Scope:** api

## Mission
Build the Intelligent Pricing Automation system: price elasticity testing, competitor price monitoring, promotional calendar, cross-format pricing, KU vs. wide distribution calculator.

## API Endpoints
- GET /api/v1/pricing/rules — List pricing rules for org
- POST /api/v1/pricing/rules — Create pricing rule
- PATCH /api/v1/pricing/rules/{id} — Update rule
- DELETE /api/v1/pricing/rules/{id} — Delete rule
- POST /api/v1/pricing/simulate — Simulate price change impact
- GET /api/v1/pricing/competitors/{book_id} — Competitor pricing data
- POST /api/v1/pricing/ab-test — Create pricing A/B test
- GET /api/v1/pricing/promotions — Get promotional calendar
- POST /api/v1/pricing/promotions — Schedule promotion
- POST /api/v1/pricing/ku-calculator — KU vs. wide revenue calculator

## Pricing Strategies
- Competitive match (match or undercut category average)
- Value-based (premium pricing for high-review books)
- Penetration (low launch price, raise after reviews)
- Dynamic (adjust based on BSR trends)
- Promotional (scheduled price drops for visibility)

## What to Build

### Backend
1. **backend/app/modules/pricing_automation/__init__.py**
2. **backend/app/modules/pricing_automation/router.py** — All endpoints
3. **backend/app/modules/pricing_automation/schemas.py** — PricingRule, PriceSimulation, Promotion, KUCalculation
4. **backend/app/modules/pricing_automation/service.py** — Rule management, price simulation, competitor monitoring
5. **backend/app/modules/pricing_automation/strategies.py** — Pricing strategy implementations
6. **backend/app/modules/pricing_automation/simulator.py** — Revenue impact simulation: model elasticity curve, projected sales at price points
7. **backend/app/modules/pricing_automation/ku_calculator.py** — KU page read revenue vs. wide distribution revenue comparison
8. **backend/app/tasks/pricing_automation.py** — Celery: periodic competitor price checks, auto-adjust triggers

### Tests
9. **backend/tests/unit/test_pricing_strategies.py**
10. **backend/tests/unit/test_ku_calculator.py**
11. **backend/tests/integration/test_pricing_api.py**

## Database Tables (from W02, read-only)
pricing_rules

## Commit Convention
`feat(pricing): implement intelligent pricing automation with strategies and KU calculator`
