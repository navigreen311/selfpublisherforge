# W27: Frontend Tests — API Client, Auth Hook, Shared Utils

## Branch: `fix/w27-test-api-hooks-utils`

## Files YOU Own (only create/modify these):
- `frontend/src/lib/__tests__/api.test.ts` (NEW)
- `frontend/src/hooks/__tests__/use-auth.test.ts` (NEW)
- `frontend/src/lib/__tests__/store.test.ts` (NEW)

## Task

Write tests for core infrastructure code. Read each file first.

### api.test.ts — Test the API client (`frontend/src/lib/api.ts`):
1. Makes GET requests with correct headers
2. Makes POST requests with JSON body
3. Includes auth token in Authorization header
4. Handles 401 by attempting token refresh
5. Redirects to /login on refresh failure
6. Handles network errors gracefully
7. Returns parsed JSON on success
8. Handles non-JSON responses

```tsx
// Mock fetch
beforeEach(() => {
  global.fetch = jest.fn();
});
afterEach(() => {
  jest.restoreAllMocks();
});
```

### use-auth.test.ts — Test auth hook (`frontend/src/hooks/use-auth.ts`):
1. Returns authenticated state when token exists
2. Login stores token and user data
3. Logout clears token and redirects
4. Register creates account and logs in
5. Token refresh works
6. OAuth functions (loginWithGoogle, loginWithGithub) redirect correctly

### store.test.ts — Test Zustand store (`frontend/src/lib/store.ts`):
1. Initial state is unauthenticated
2. setAuth updates user and tokens
3. clearAuth resets state
4. Persists to localStorage
5. Hydrates from localStorage on init

### Test Utilities:
```tsx
// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => { store[key] = value; }),
    removeItem: jest.fn((key) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });
```

## Verification
```bash
cd frontend && npx jest src/lib/__tests__/ src/hooks/__tests__/ --passWithNoTests --no-cache 2>&1 | tail -20
```
