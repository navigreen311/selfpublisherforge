# W24: Frontend Tests — Writing Module

## Branch: `fix/w24-test-writing-module`

## Files YOU Own (only create/modify these):
- `frontend/src/app/(dashboard)/writing/__tests__/writing-page.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/writing/outline/__tests__/outline-page.test.tsx` (NEW)
- `frontend/src/modules/writing/__tests__/hooks.test.ts` (NEW)

## Task

Write comprehensive tests for the writing module. Read each file first.

### Common Mocks:
```tsx
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/writing",
}));

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", org_id: "org1" },
    isAuthenticated: true,
  }),
}));
```

### writing-page.test.tsx — Test:
1. Renders writing studio page
2. Shows quick action cards (AI Outline Generator, etc.)
3. AI Outline Generator card links to /writing/outline
4. Shows recent writing projects
5. Loading state displays skeleton

### outline-page.test.tsx — Test:
1. Renders outline generation form
2. All form fields present (title, genre, tone, audience, chapters, premise)
3. Form validation (title required)
4. Submit triggers mutation
5. Results display with chapters
6. Chapter reorder (up/down) works
7. Export to clipboard works
8. Loading state during generation

### hooks.test.ts — Test:
1. `useGenerateStandaloneOutline` hook calls correct endpoint
2. Hook passes correct payload
3. Error handling on failure
4. Other writing hooks in the file

Use `@tanstack/react-query` test utilities:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";

const wrapper = ({ children }) => (
  <QueryClientProvider client={new QueryClient()}>
    {children}
  </QueryClientProvider>
);
```

## Verification
```bash
cd frontend && npx jest src/app/\(dashboard\)/writing/ src/modules/writing/ --passWithNoTests --no-cache 2>&1 | tail -20
```
