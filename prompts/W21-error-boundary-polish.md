# W21: Fix Error Boundary + Global Error Console Logging

## Branch: `fix/w21-error-boundary-polish`

## Files YOU Own (only modify these):
- `frontend/src/components/shared/error-boundary.tsx`
- `frontend/src/app/(dashboard)/onboarding/page.tsx`

## Task

### Fix 1: error-boundary.tsx — Remove production console.error (line ~32)

```tsx
// BEFORE:
console.error("ErrorBoundary caught:", error, errorInfo);

// AFTER:
if (process.env.NODE_ENV === "development") {
  console.error("ErrorBoundary caught:", error, errorInfo);
}
```

### Fix 2: onboarding/page.tsx — Fix placeholder text

The audit noted placeholder sample description in the AIGenerationStep (lines ~318-324). Check if this is a static placeholder that should be dynamic. If it's a placeholder that shows before AI generates content, it's fine. If it's supposed to be user-customizable, add proper state management.

Also check for any `window.location.href` usage and replace with `useRouter().push()`.

### Fix 3: Review error boundary error display

The error boundary shows "Something went wrong" without details. In development mode, show the error message:

```tsx
{process.env.NODE_ENV === "development" && error?.message && (
  <pre className="mt-4 p-3 bg-muted rounded text-xs overflow-auto max-h-40">
    {error.message}
  </pre>
)}
```

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "error-boundary\|onboarding" || echo "No type errors"
cd frontend && grep -rn "console.error" src/components/shared/error-boundary.tsx
```
