# W05: Billing & Subscriptions (Stripe)
**Branch:** `ai-feature/billing-subscriptions`
**Scope:** fullstack

## Mission
Implement Stripe billing integration with plan selection, subscription management, usage metering, invoicing, and webhook handling.

## Pricing Tiers
- Free: $0/mo — 1 project, 5 AI generations/day
- Starter: $29/mo — 5 projects, 50 AI generations/day
- Pro: $79/mo — 25 projects, 200 AI generations/day
- Business: $199/mo — unlimited projects, 500 AI generations/day
- Enterprise: $499+/mo — custom

## What to Build

### Backend
1. **backend/app/modules/billing/__init__.py**
2. **backend/app/modules/billing/router.py** — Endpoints:
   - GET /api/v1/billing/plans — List available plans
   - GET /api/v1/billing/subscription — Get current subscription
   - POST /api/v1/billing/subscribe — Create Stripe checkout session
   - POST /api/v1/billing/portal — Create Stripe billing portal session
   - POST /api/v1/billing/webhook — Stripe webhook handler
   - GET /api/v1/billing/usage — Get current usage stats
   - GET /api/v1/billing/invoices — List invoices

3. **backend/app/modules/billing/schemas.py** — PlanInfo, SubscriptionResponse, UsageStats, CheckoutRequest
4. **backend/app/modules/billing/service.py** — Stripe customer creation, checkout, portal, webhook event handling (subscription.created, updated, deleted, invoice.paid, invoice.payment_failed), usage tracking
5. **backend/app/modules/billing/plans.py** — Plan definitions with limits (projects, AI generations, features)

### Frontend
6. **frontend/src/app/(dashboard)/settings/billing/page.tsx** — Plan comparison, current plan, usage, upgrade/downgrade
7. **frontend/src/modules/billing/hooks.ts** — React Query hooks for billing API
8. **frontend/src/modules/billing/components/** — PlanCard, UsageMeter, InvoiceList
   - **frontend/src/modules/billing/components/PlanCard.tsx**
   - **frontend/src/modules/billing/components/UsageMeter.tsx**
   - **frontend/src/modules/billing/components/InvoiceList.tsx**

### Tests
9. **backend/tests/unit/test_billing_service.py** — Test plan limits, usage tracking, webhook handling
10. **backend/tests/integration/test_billing_api.py** — Test endpoints with mocked Stripe

## Database Tables Used (read-only, created by W02)
- organizations (plan_tier, subscription_status, limits fields)

## Dependencies
- Uses: backend/app/core/dependencies.py (get_current_user, require_role)
- Uses: backend/app/core/exceptions.py (AppException)
- External: stripe Python SDK

## Read-Only (do NOT modify)
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/core/security.py
- backend/app/core/dependencies.py
- backend/app/core/exceptions.py
- backend/app/core/pagination.py
- backend/app/schemas/common.py
- frontend/src/app/layout.tsx
- frontend/src/components/providers.tsx
- frontend/src/lib/utils.ts
- frontend/src/lib/api.ts
- frontend/src/types/index.ts
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
`feat(billing): implement Stripe billing with plan management and usage metering`
