# W26: Frontend Tests — Publishing + Analytics Modules

## Branch: `fix/w26-test-publishing-analytics`

## Files YOU Own (only create/modify these):
- `frontend/src/app/(dashboard)/publishing/__tests__/publishing-page.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/analytics/__tests__/analytics-page.test.tsx` (NEW)
- `frontend/src/modules/publishing/__tests__/hooks.test.ts` (NEW)
- `frontend/src/modules/analytics/__tests__/hooks.test.ts` (NEW)

## Task

Write comprehensive tests. Read each page/hook file first.

### publishing-page.test.tsx — Test:
1. Renders publishing dashboard
2. Shows export section
3. Shows metadata section
4. Shows book listings
5. Loading states work
6. Empty states for no books

### analytics-page.test.tsx — Test:
1. Renders analytics dashboard
2. Revenue cards display
3. Charts section renders
4. Reports section accessible
5. Date range selector works
6. Loading/error states

### publishing/hooks.test.ts — Test:
1. `useBooks` or equivalent list hook
2. `useExportBook` mutation
3. `useMetadata` query
4. Error handling

### analytics/hooks.test.ts — Test:
1. `useRevenueSummary` or equivalent
2. `useReports` list hook
3. `useGenerateReport` mutation
4. Data transformation correctness

### Common Pattern:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};
```

## Verification
```bash
cd frontend && npx jest src/app/\(dashboard\)/publishing/ src/app/\(dashboard\)/analytics/ src/modules/publishing/ src/modules/analytics/ --passWithNoTests --no-cache 2>&1 | tail -20
```
