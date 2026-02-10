# W26: Frontend Tests for Projects + Writing Studio Pages

## Files to create
- `frontend/src/app/(dashboard)/projects/__tests__/page.test.tsx` — NEW
- `frontend/src/app/(dashboard)/writing/__tests__/page.test.tsx` — NEW

## Task

### 1. Read existing test patterns

Check `frontend/src/components/` tests for patterns.

### 2. Write projects page tests

```tsx
describe('ProjectsPage', () => {
  it('renders loading skeleton', () => { ... });
  it('renders project cards from API data', () => { ... });
  it('filters projects by search term', () => { ... });
  it('shows empty state when no projects', () => { ... });
  it('navigates to new project on create button click', () => { ... });
});
```

### 3. Write writing studio page tests

```tsx
describe('WritingStudioPage', () => {
  it('renders loading state', () => { ... });
  it('renders book list from API', () => { ... });
  it('shows empty state for new users', () => { ... });
  it('shows writing sessions table', () => { ... });
});
```

### 4. Mock patterns

Mock the hooks (useProjects, useBooks) rather than the API directly. This tests the page component in isolation.

Write at least 8 tests total (4 per page).
