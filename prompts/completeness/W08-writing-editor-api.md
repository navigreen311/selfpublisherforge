# W08: Writing Editor [bookId] Page — Wire to Chapter API

## Files to modify
- `frontend/src/app/(dashboard)/writing/[bookId]/page.tsx` — Wire to chapter API
- `frontend/src/modules/writing/hooks.ts` — Add chapter hooks if missing

## Context
The writing editor page should load a specific book's chapters and allow editing. Check the current state of the page and wire it to the backend.

Backend endpoints:
- GET `/api/v1/books/{bookId}` — Get book details
- GET `/api/v1/books/{bookId}/chapters` — List chapters (if exists)
- The AI writing module at `/api/v1/ai-writing/` provides generation endpoints

## Task

### 1. Check current state of [bookId]/page.tsx

Read the file and understand what's currently implemented. If it has hardcoded data, replace with API calls.

### 2. Add hooks for chapter management

```typescript
export function useBook(bookId: string) {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: () => api.get(`/api/v1/books/${bookId}`).then(r => r.data),
  });
}

export function useChapters(bookId: string) {
  return useQuery({
    queryKey: ['chapters', bookId],
    queryFn: () => api.get(`/api/v1/books/${bookId}/chapters`).then(r => r.data),
  });
}

export function useSaveChapter() {
  return useMutation({
    mutationFn: ({ bookId, chapterId, content }) =>
      api.patch(`/api/v1/books/${bookId}/chapters/${chapterId}`, { content }),
  });
}
```

### 3. Wire the editor component

Connect the existing editor component to use real chapter data. Add auto-save functionality (debounced mutation on content change). Show save status indicator.

### 4. Wire AI panel

Connect the AI assistance panel (if it exists in the writing module components) to the AI writing generation endpoint.
