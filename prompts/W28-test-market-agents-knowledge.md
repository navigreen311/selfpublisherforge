# W28: Frontend Tests — Market, Agents, Knowledge Pages

## Branch: `fix/w28-test-market-agents-knowledge`

## Files YOU Own (only create/modify these):
- `frontend/src/app/(dashboard)/market/__tests__/market-page.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/agents/__tests__/agents-page.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/knowledge/__tests__/knowledge-page.test.tsx` (NEW)
- `frontend/src/modules/market/__tests__/hooks.test.ts` (NEW)
- `frontend/src/modules/agents/__tests__/hooks.test.ts` (NEW)

## Task

Write comprehensive tests. Read each page/hook file first.

### market-page.test.tsx — Test:
1. Renders market intelligence page
2. Search/keyword input works
3. Niche score cards display
4. Competitor analysis section
5. Trend charts render
6. Loading/error states

### agents-page.test.tsx — Test:
1. Renders agents dashboard
2. Agent list displays
3. Agent status badges show correctly
4. Uses router.push (NOT window.location.href) for navigation
5. Task list renders
6. Workflow section accessible
7. Emergency stop button present

### knowledge-page.test.tsx — Test:
1. Renders knowledge vault
2. Document list displays
3. Upload area/button present
4. Tag filter works
5. Search functionality
6. Empty state when no documents

### market/hooks.test.ts — Test:
1. `useNicheAnalysis` or similar
2. `useCompetitors` query
3. `useKeywordData` query
4. Error handling

### agents/hooks.test.ts — Test:
1. `useAgents` list hook
2. `useEmergencyStop` mutation
3. `useAgentTasks` query
4. `useWorkflows` query

### Common Setup:
```tsx
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/market",
  useSearchParams: () => new URLSearchParams(),
}));
```

## Verification
```bash
cd frontend && npx jest src/app/\(dashboard\)/market/ src/app/\(dashboard\)/agents/ src/app/\(dashboard\)/knowledge/ src/modules/market/ src/modules/agents/ --passWithNoTests --no-cache 2>&1 | tail -20
```
