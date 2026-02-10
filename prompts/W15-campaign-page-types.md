# W15: Fix Campaign Page `as any` Cast

## Branch: `fix/w15-campaign-page-types`

## Files YOU Own (only modify these):
- `frontend/src/app/(dashboard)/advertising/campaigns/[id]/page.tsx`

## Task

### Fix 1: Remove `as any` type cast (line ~33)

```tsx
// BEFORE:
await updateCampaign.mutateAsync({ status: newStatus } as any)

// AFTER:
await updateCampaign.mutateAsync({ status: newStatus })
```

Read the `updateCampaign` hook definition to understand the expected type. The hook likely expects a specific update payload type. Fix the type to match.

If the hook is defined in `frontend/src/modules/advertising/hooks.ts`, check what type the mutation function expects. You may need to:

1. Check the hook's mutation function signature
2. Create or import the correct type for the update payload
3. Properly type `newStatus` to match the expected enum/union type

### Fix 2: Check for any other `as any` in the file

Search for all `as any` patterns and fix each one with proper types.

### Fix 3: Add error handling if missing

If the status update call doesn't have proper error handling (try/catch with user feedback), add it:
```tsx
try {
  await updateCampaign.mutateAsync({ status: newStatus });
  toast.success("Campaign status updated");
} catch (error) {
  const message = error instanceof Error ? error.message : "Failed to update campaign";
  toast.error(message);
}
```

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "campaign" || echo "No type errors"
cd frontend && grep -rn "as any" src/app/\(dashboard\)/advertising/ || echo "No as any remaining"
```
