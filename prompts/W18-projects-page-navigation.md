# W18: Fix Projects Page — window.location.href

## Branch: `fix/w18-projects-page-navigation`

## Files YOU Own (only modify these):
- `frontend/src/app/(dashboard)/projects/page.tsx`

## Task

### Fix 1: Replace window.location.href with Next.js router

```tsx
// Add import if not present:
import { useRouter } from "next/navigation";

// In component:
const router = useRouter();

// BEFORE:
window.location.href = "/projects/new"

// AFTER:
router.push("/projects/new")
```

Search the entire file for ALL `window.location` occurrences and replace them all.

### Fix 2: Check EmptyState component

If the page uses an EmptyState component with an action callback, ensure it uses router.push.

### Fix 3: General cleanup

- Check for any `console.log` or `console.error` that should be removed
- Check for any `as any` type casts and fix them
- Ensure all buttons/links have proper aria-labels if they're icon-only

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "projects" | head -5 || echo "No type errors"
cd frontend && grep -rn "window.location" src/app/\(dashboard\)/projects/page.tsx || echo "No window.location remaining"
```
