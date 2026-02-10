# W14: Fix CreativeEditor `as any` Cast + Add Validation

## Branch: `fix/w14-creative-editor-types`

## Files YOU Own (only modify these):
- `frontend/src/modules/advertising/components/CreativeEditor.tsx`

## Task

### Fix 1: Remove `as any` type cast (line ~39)

The mutateAsync call uses `as any` to bypass TypeScript:
```tsx
} as any)
```

Fix by properly typing the mutation parameter. Read the hook definition to understand the expected type. Create a proper interface if needed:

```tsx
// Instead of:
await mutateAsync({ ...params } as any);

// Do:
await mutateAsync({ ...params });  // with properly typed params
```

If the hook expects a different shape than what's being passed, fix the data structure to match. If the hook's type is wrong, fix the hook type in the hooks file — but ONLY if the hooks file is `frontend/src/modules/advertising/hooks.ts`.

### Fix 2: Add client-side validation

The form for book title and description (lines ~65-100) lacks required field validation:

1. Add validation before submission:
```tsx
if (!title.trim()) {
  toast.error("Book title is required");
  return;
}
if (!description.trim()) {
  toast.error("Description is required");
  return;
}
```

2. Add visual required indicators to input labels.

### Fix 3: Improve error handling in catch block (lines ~42-43)

```tsx
// BEFORE:
catch (error) {
  // generic toast
}

// AFTER:
catch (error) {
  const message = error instanceof Error ? error.message : "Failed to generate creative";
  toast.error(message);
}
```

## Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "CreativeEditor" || echo "No type errors"
```
