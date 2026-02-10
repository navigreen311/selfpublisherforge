# W06: Writing Studio — Wire to Real API

## Files to modify
- `frontend/src/app/(dashboard)/writing/page.tsx` — Replace SAMPLE_BOOKS with API
- `frontend/src/modules/writing/hooks.ts` — Verify/add hooks for book listing

## Context
- Writing module hooks exist at `frontend/src/modules/writing/hooks.ts`
- The backend has book endpoints and writing session tracking
- API base: `/api/v1/books` for listing books, `/api/v1/books/{id}/chapters` for chapters

## Task

### 1. Update writing/page.tsx

Remove the `SAMPLE_BOOKS` hardcoded array and the hardcoded writing sessions table data.

Replace with:
```tsx
import { useBooks } from '@/modules/writing/hooks'; // or create if missing

export default function WritingStudioPage() {
  const { data: books, isLoading, error } = useBooks();
  // ... render with real data
}
```

### 2. Add/update hooks

If `useBooks()` doesn't exist in the writing hooks, create it:
```typescript
export function useBooks() {
  return useQuery({
    queryKey: ['books'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/books');
      return data;
    },
  });
}

export function useWritingSessions(bookId?: string) {
  return useQuery({
    queryKey: ['writing-sessions', bookId],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/analytics/events', {
        params: { event_type: 'writing_session', entity_id: bookId }
      });
      return data;
    },
    enabled: !!bookId,
  });
}
```

### 3. Add loading and error states

Use Skeleton components for loading. Show empty state with "Start your first book" CTA when no books exist. Add error boundary.
