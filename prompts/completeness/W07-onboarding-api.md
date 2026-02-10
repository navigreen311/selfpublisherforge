# W07: Onboarding Wizard — Wire to Real APIs

## Files to modify
- `frontend/src/app/(dashboard)/onboarding/page.tsx` — Add API integrations
- `frontend/src/components/shared/onboarding-wizard.tsx` — May need step completion callbacks

## Context
The onboarding wizard has 4 steps but no functional handlers:
1. Welcome — just UI
2. Create Project — form inputs but no submission
3. Connect KDP — button with no handler
4. AI Generation — button with no handler

Backend endpoints available:
- POST `/api/v1/books` — Create a new book/project
- POST `/api/v1/publishing/accounts` — Connect publishing account
- POST `/api/v1/ai-writing/generate` — Generate content

## Task

### 1. Wire Step 2 (Create Project)

Add state management for form inputs (title, genre, description). On "Next", POST to `/api/v1/books` to create the project. Store the returned book_id for subsequent steps.

```tsx
const [bookTitle, setBookTitle] = useState('');
const [genre, setGenre] = useState('');
const createProject = useMutation({
  mutationFn: (data) => api.post('/api/v1/books', data),
});
```

### 2. Wire Step 3 (Connect KDP)

Add handler for "Connect KDP Account" button. POST to `/api/v1/publishing/accounts` with platform="kdp". Allow skipping this step.

### 3. Wire Step 4 (AI Generation)

Add handler for "Generate Book Description" button. POST to `/api/v1/ai-writing/generate` with the book_id from step 2. Display the generated content. Allow skipping.

### 4. Add proper state management

Track which steps are completed. Show loading spinners on API calls. Show success/error toasts. On final completion, redirect to `/dashboard`.

### 5. Handle the "skip" case gracefully

Each step after Welcome should have a "Skip" option. If user skips everything, still redirect to dashboard.
