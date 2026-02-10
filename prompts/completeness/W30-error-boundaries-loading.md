# W30: Frontend Error Boundaries + Loading Skeletons for All Pages

## Files to modify
- `frontend/src/app/(dashboard)/layout.tsx` — Wrap with ErrorBoundary
- Various page files — Add loading.tsx files for Suspense

## Files to create
- `frontend/src/app/(dashboard)/dashboard/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/projects/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/writing/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/analytics/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/market/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/publishing/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/marketing/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/advertising/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/agents/loading.tsx` — NEW
- `frontend/src/app/(dashboard)/settings/loading.tsx` — NEW

## Context
Next.js 14 App Router supports `loading.tsx` files that automatically show during page transitions. The project has `Skeleton` component from shadcn/ui and an `ErrorBoundary` component in shared/.

## Task

### 1. Check existing error boundary

Read `frontend/src/components/shared/error-boundary.tsx` and `frontend/src/components/shared/loading.tsx`.

### 2. Wrap dashboard layout with ErrorBoundary

Read `frontend/src/app/(dashboard)/layout.tsx` and wrap children with the ErrorBoundary:

```tsx
import { ErrorBoundary } from '@/components/shared/error-boundary';

export default function DashboardLayout({ children }) {
  return (
    <div className="...">
      <Sidebar />
      <main>
        <Header />
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>
    </div>
  );
}
```

### 3. Create loading.tsx for each section

Each loading.tsx should show a skeleton that matches the page layout:

```tsx
// frontend/src/app/(dashboard)/dashboard/loading.tsx
import { Skeleton } from '@/components/ui/skeleton';
import { Card } from '@/components/ui/card';

export default function DashboardLoading() {
  return (
    <div className="space-y-6 p-6">
      {/* KPI Cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="p-4">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-16" />
          </Card>
        ))}
      </div>
      {/* Chart skeleton */}
      <Card className="p-4">
        <Skeleton className="h-4 w-32 mb-4" />
        <Skeleton className="h-64 w-full" />
      </Card>
    </div>
  );
}
```

Create appropriate loading skeletons for each section (dashboard, projects, writing, analytics, etc.) that match the actual page layouts.

### 4. Add not-found.tsx

Create `frontend/src/app/not-found.tsx` if it doesn't exist:

```tsx
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground mt-2">Page not found</p>
      <a href="/dashboard" className="mt-4 text-primary hover:underline">
        Go to Dashboard
      </a>
    </div>
  );
}
```
