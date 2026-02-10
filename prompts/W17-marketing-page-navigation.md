# W17: Fix Marketing Page — window.location.href

## Branch: `fix/w17-marketing-page-navigation`

## Files YOU Own (only modify these):
- `frontend/src/app/(dashboard)/marketing/page.tsx`

## Task

### Fix 1: Replace window.location.href with Next.js router

There are 2+ instances of `window.location.href` for internal navigation (lines ~291, ~376):

```tsx
// Add at top:
import { useRouter } from "next/navigation";

// In component:
const router = useRouter();

// BEFORE:
window.location.href = "/marketing/launch/new"
window.location.href = "/marketing/email"

// AFTER:
router.push("/marketing/launch/new")
router.push("/marketing/email")
```

Search the entire file for ALL `window.location` occurrences and replace them all.

### Fix 2: Review EmptyState callbacks

The EmptyState components pass callback functions. Make sure they use router.push:

```tsx
<EmptyState
  ...
  actionLabel="Create Launch Plan"
  onAction={() => router.push("/marketing/launch/new")}
/>
```

### Fix 3: Check for any hardcoded data

The audit noted "Recent Activity" was previously hardcoded. Verify it now uses the `useRecentActivity` hook. If it doesn't, wire it up.

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "marketing" | head -5 || echo "No type errors"
cd frontend && grep -rn "window.location" src/app/\(dashboard\)/marketing/page.tsx || echo "No window.location remaining"
```
