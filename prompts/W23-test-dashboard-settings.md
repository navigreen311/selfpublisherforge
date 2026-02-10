# W23: Frontend Tests — Dashboard + Settings Pages

## Branch: `fix/w23-test-dashboard-settings`

## Files YOU Own (only create/modify these):
- `frontend/src/app/(dashboard)/__tests__/dashboard.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/settings/__tests__/profile.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/settings/__tests__/security.test.tsx` (NEW)
- `frontend/src/app/(dashboard)/settings/__tests__/billing.test.tsx` (NEW)

## Task

Write comprehensive Jest + React Testing Library tests. Read each page first.

### Common Mocks:
```tsx
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", email: "test@test.com", name: "Test User" },
    isAuthenticated: true,
  }),
}));

// Mock React Query hooks as needed
jest.mock("@/modules/<module>/hooks", () => ({
  useXxx: () => ({ data: mockData, isLoading: false, error: null }),
}));
```

### dashboard.test.tsx — Test:
1. Renders dashboard with stats cards
2. Shows loading skeleton while data loads
3. Displays recent projects
4. Displays quick action cards
5. Navigation links work

### settings/profile.test.tsx — Test:
1. Renders profile form with user data
2. Name field is editable
3. Email field displays correctly
4. Save button triggers update
5. Success toast on save

### settings/security.test.tsx — Test:
1. Renders password change form
2. MFA section displays
3. Current password required
4. New password validation
5. Shows active sessions if available

### settings/billing.test.tsx — Test:
1. Renders current plan info
2. Shows billing history
3. Upgrade/downgrade buttons
4. Stripe redirect on plan change

## Verification
```bash
cd frontend && npx jest src/app/\(dashboard\)/__tests__/ src/app/\(dashboard\)/settings/__tests__/ --passWithNoTests --no-cache 2>&1 | tail -20
```
