# W27: Analytics & Business Intelligence (Module #9)
**Branch:** `ai-feature/analytics-bi`
**Scope:** fullstack

## Mission
Build the Analytics & BI system: revenue dashboard, royalty import pipeline, portfolio metrics, custom report builder, and data export.

## API Endpoints
- GET /api/v1/analytics/dashboard — Main analytics dashboard (KPIs, charts, trends)
- GET /api/v1/analytics/revenue — Revenue data (by book, by period, by platform)
- GET /api/v1/analytics/royalties — Royalty records (imported from platforms)
- POST /api/v1/analytics/royalties/import — Import royalty data (CSV upload or API)
- GET /api/v1/analytics/portfolio — Portfolio-level metrics (total books, revenue, ROI)
- POST /api/v1/analytics/reports/generate — Generate custom report (PDF/XLSX)
- GET /api/v1/analytics/reports — List generated reports
- GET /api/v1/analytics/reports/{id}/download — Download report file
- POST /api/v1/analytics/events — Record analytics event
- GET /api/v1/analytics/trends — Trend data for key metrics

## What to Build

### Backend
1. **backend/app/modules/analytics/__init__.py**
2. **backend/app/modules/analytics/router.py** — All endpoints
3. **backend/app/modules/analytics/schemas.py** — DashboardData, RevenueReport, RoyaltyRecord, PortfolioMetrics, ReportRequest, TrendData
4. **backend/app/modules/analytics/service.py** — Dashboard aggregation, revenue calculations, report generation
5. **backend/app/modules/analytics/royalty_importer.py** — Parse royalty CSVs from KDP, IngramSpark, D2D; normalize and store
6. **backend/app/modules/analytics/metrics.py** — Calculate portfolio metrics: total revenue, ROI per book, revenue trends, platform breakdown
7. **backend/app/modules/analytics/report_builder.py** — Generate reports: revenue summary, book performance, marketing ROI (output PDF/XLSX)
8. **backend/app/modules/analytics/aggregator.py** — Time-series aggregation: daily, weekly, monthly rollups of analytics_events
9. **backend/app/tasks/analytics.py** — Celery: daily metric aggregation, scheduled report generation, royalty sync

### Frontend
10. **frontend/src/app/(dashboard)/analytics/page.tsx** — Analytics dashboard: revenue chart, top books, platform breakdown, KPI cards
11. **frontend/src/app/(dashboard)/analytics/revenue/page.tsx** — Detailed revenue view with filters
12. **frontend/src/app/(dashboard)/analytics/reports/page.tsx** — Report builder and download list
13. **frontend/src/modules/analytics/hooks.ts** — React Query hooks
14. **frontend/src/modules/analytics/components/** — RevenueChart, PortfolioTable, KPICard, ReportBuilder, RoyaltyImporter

### Tests
15. **backend/tests/unit/test_metrics.py**
16. **backend/tests/unit/test_royalty_importer.py**
17. **backend/tests/integration/test_analytics_api.py**

## Database Tables (from W02, read-only)
analytics_events, royalty_records, portfolio_metrics, reports

## Commit Convention
`feat(analytics): implement analytics & BI with revenue dashboard, royalty import, and reports`
