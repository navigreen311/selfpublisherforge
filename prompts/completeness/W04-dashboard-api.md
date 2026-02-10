# W04: Dashboard Page — Wire to Real Analytics API

## Files to modify
- `frontend/src/app/(dashboard)/dashboard/page.tsx` — Replace hardcoded data with API calls

## Context
- The analytics API exists at `/api/v1/analytics/dashboard` and returns: kpis, revenue_chart, top_books, platform_breakdown, recent_royalties
- The analytics hooks exist at `frontend/src/modules/analytics/hooks.ts` with `useDashboard()` hook
- The API client exists at `frontend/src/lib/api.ts` (axios instance with auth)
- The analytics page at `frontend/src/app/(dashboard)/analytics/page.tsx` already uses these hooks successfully

## Task

Replace ALL hardcoded data in the dashboard page:

1. Import and use `useDashboard` from `@/modules/analytics/hooks`
2. Replace the hardcoded `stats` array with KPI data from the API response
3. Replace hardcoded "recent activity" with data from recent_royalties or a new `/api/v1/analytics/events` call
4. Replace hardcoded "recent projects" with a fetch to `/api/v1/books` (or the project listing endpoint)
5. Add loading skeletons using the existing `Skeleton` component from `@/components/ui/skeleton`
6. Add error state handling with a retry button
7. Keep the "Quick Actions" section as-is (it's just navigation links)

Pattern to follow from analytics page:
```tsx
const { data, isLoading, error } = useDashboard();
if (isLoading) return <DashboardSkeleton />;
if (error) return <ErrorState onRetry={refetch} />;
```

Map the API KPI data to StatCard components. The API returns KPICard objects with: label, value, change_percent, change_direction.
