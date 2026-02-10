# W22: Frontend Tests — Auth Pages

## Branch: `fix/w22-test-auth-pages`

## Files YOU Own (only create/modify these):
- `frontend/src/app/(auth)/__tests__/login.test.tsx` (NEW)
- `frontend/src/app/(auth)/__tests__/register.test.tsx` (NEW)
- `frontend/src/app/(auth)/__tests__/reset-password.test.tsx` (NEW)
- `frontend/src/app/(auth)/__tests__/forgot-password.test.tsx` (NEW)

## Task

Write comprehensive Jest + React Testing Library tests for all auth pages. Read each page component first to understand what to test.

### Test Structure for Each Page:

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock the API/auth hooks
jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    login: jest.fn(),
    register: jest.fn(),
    isAuthenticated: false,
  }),
}));
```

### login.test.tsx — Test:
1. Renders login form with email and password fields
2. Shows validation errors for empty fields
3. Calls login on form submit with correct credentials
4. Shows error message on failed login
5. Has link to register page
6. Has link to forgot password
7. OAuth buttons render (Google, GitHub)

### register.test.tsx — Test:
1. Renders registration form
2. Password validation rules display and update
3. Password strength indicator works
4. Passwords must match
5. Form submission with valid data
6. Error handling for duplicate email

### reset-password.test.tsx — Test:
1. Renders password reset form
2. Password validation (using shared validation)
3. Passwords must match
4. Success state after reset

### forgot-password.test.tsx — Test:
1. Renders email input
2. Validates email format
3. Shows success message after submission
4. Has link back to login

## Verification
```bash
cd frontend && npx jest src/app/\(auth\)/__tests__/ --passWithNoTests --no-cache 2>&1 | tail -20
```
