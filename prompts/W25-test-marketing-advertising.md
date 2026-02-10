# W25: Frontend Tests — Marketing + Advertising Modules

## Branch: `fix/w25-test-marketing-advertising`

## Files YOU Own (only create/modify these):
- `frontend/src/app/(dashboard)/marketing/__tests__/marketing-page.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/advertising/__tests__/advertising-page.test.tsx` (NEW)
- `frontend/src/modules/marketing/__tests__/hooks.test.ts` (NEW)
- `frontend/src/modules/advertising/__tests__/hooks.test.ts` (NEW)

## Task

Write comprehensive tests. Read each page/hook file first.

### marketing-page.test.tsx — Test:
1. Renders marketing dashboard
2. Shows launch plans section
3. Shows email campaigns section
4. Empty state renders when no data
5. EmptyState action buttons use router.push (not window.location)
6. Recent activity section renders
7. Loading states work

### advertising-page.test.tsx — Test:
1. Renders advertising dashboard
2. Campaign list displays
3. Create campaign button works
4. Campaign metrics cards display
5. Loading and error states

### marketing/hooks.test.ts — Test:
1. `useRecentActivity` fetches from correct endpoint
2. `useLaunchPlans` returns typed data
3. Error states handled
4. Other hooks in the file

### advertising/hooks.test.ts — Test:
1. `useCampaigns` fetches campaign list
2. `useUpdateCampaign` mutation works
3. `useCreateCreative` mutation works
4. Error handling for each hook

### Mock Pattern:
```tsx
// Mock fetch globally
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ data: [] }),
  })
) as jest.Mock;
```

## Verification
```bash
cd frontend && npx jest src/app/\(dashboard\)/marketing/ src/app/\(dashboard\)/advertising/ src/modules/marketing/ src/modules/advertising/ --passWithNoTests --no-cache 2>&1 | tail -20
```
