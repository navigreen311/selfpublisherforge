# W05: Projects Page + New Project — Wire to Real API

## Files to modify
- `frontend/src/app/(dashboard)/projects/page.tsx` — Replace sampleProjects with API
- `frontend/src/app/(dashboard)/projects/new/page.tsx` — Wire form to real API
- `frontend/src/modules/projects/hooks.ts` — NEW: Create project hooks

## Task

### 1. Create project hooks module

Create `frontend/src/modules/projects/hooks.ts`:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useProjects(filters?: { status?: string; search?: string }) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/books', { params: filters });
      return data;
    },
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (project: CreateProjectData) => {
      const { data } = await api.post('/api/v1/books', project);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  });
}

export function useDeleteProject() { ... }
```

### 2. Update projects/page.tsx

Remove `sampleProjects` array. Use `useProjects()` hook with search/filter params. Add loading skeleton and error states. Keep the same UI layout but populate with real data.

### 3. Update projects/new/page.tsx

Replace the `setTimeout` mock with `useCreateProject()` mutation. On success, redirect to the project detail page. Show loading state on submit button. Show error toast on failure.
