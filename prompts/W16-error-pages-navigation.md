# W16: Fix Error Pages — window.location + console.error

## Branch: `fix/w16-error-pages-navigation`

## Files YOU Own (only modify these):
- `frontend/src/app/error.tsx`
- `frontend/src/app/(dashboard)/error.tsx`
- `frontend/src/app/global-error.tsx`

## Task

### Fix 1: Replace window.location.href with Next.js router

Both `error.tsx` and `(dashboard)/error.tsx` use `window.location.href` for navigation, causing full page reloads.

```tsx
// Add import:
import { useRouter } from "next/navigation";

// In component:
const router = useRouter();

// BEFORE:
window.location.href = "/dashboard"
window.location.href = "/"

// AFTER:
router.push("/dashboard")
router.push("/")
```

**Note**: Error boundaries are client components ("use client"), so useRouter from next/navigation works.

### Fix 2: Remove console.error in production

Both error.tsx files have `console.error("App error:", error)` or similar.

Replace with conditional logging:
```tsx
// BEFORE:
console.error("App error:", error);

// AFTER:
if (process.env.NODE_ENV === "development") {
  console.error("App error:", error);
}
```

### Fix 3: global-error.tsx

Check `global-error.tsx` for the same issues and fix similarly. Note: global-error.tsx renders its own `<html>` tag and cannot use Next.js router. For this file, `window.location.href = "/"` is acceptable since it's the root error boundary. But still fix console.error.

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "error" | head -10 || echo "No type errors"
cd frontend && grep -rn "window.location.href" src/app/error.tsx src/app/\(dashboard\)/error.tsx || echo "No window.location remaining"
```
