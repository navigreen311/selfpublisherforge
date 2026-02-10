# W30: Frontend Accessibility Fixes

## Branch: `fix/w30-accessibility-polish`

## Files YOU Own (only modify these):
- `frontend/src/components/layout/sidebar.tsx`
- `frontend/src/modules/product-page/components/MobilePreview.tsx`
- `frontend/src/modules/marketing/components/ARCTable.tsx`
- `frontend/src/app/(dashboard)/agents/page.tsx`

**DO NOT modify**: `frontend/src/components/layout/header.tsx` (owned by W13)

## Task

### Fix 1: sidebar.tsx — Add aria-labels to icon-only buttons

When sidebar is collapsed, navigation items show only icons. Add aria-labels:

```tsx
// For each nav item, ensure tooltip AND aria-label:
<button
  aria-label={item.label}  // "Dashboard", "Projects", etc.
  ...
>
  <item.icon className="h-5 w-5" />
</button>
```

Also add `aria-label` to the sidebar collapse toggle button:
```tsx
<Button
  variant="ghost"
  size="icon"
  aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
>
```

### Fix 2: MobilePreview.tsx — Add alt text (line ~34)

```tsx
// BEFORE:
<div>Book Cover</div>

// AFTER:
<div role="img" aria-label="Book cover preview placeholder">
  Book Cover
</div>
```

### Fix 3: agents/page.tsx — Verify router.push

The audit noted this page was fixed to use `router.push()` instead of `window.location.href`. Verify that's the case. If any `window.location.href` remains, fix it.

### Fix 4: ARCTable.tsx — Add table accessibility

If the table component exists, ensure:
- `<table>` has `aria-label="ARC team members"` or similar
- Column headers use `<th scope="col">`
- Row headers use `<th scope="row">` if applicable

### Fix 5: General accessibility sweep

For each file you own, check:
- All interactive elements have visible focus indicators
- All icon-only buttons have aria-labels
- All form inputs have associated labels
- Color is not the sole means of conveying information

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -10 || echo "No type errors"
cd frontend && grep -rn "aria-label" src/components/layout/sidebar.tsx | wc -l
```
