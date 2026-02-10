# W25: Frontend Tests for Dashboard + Analytics Pages

## Files to create
- `frontend/src/app/(dashboard)/dashboard/__tests__/page.test.tsx` — NEW

## Context
The frontend uses:
- Next.js 14 with App Router
- React Query for data fetching
- Jest + React Testing Library for tests
- Components from shadcn/ui

Check `frontend/jest.config.js` or `frontend/package.json` for test configuration.

## Task

### 1. Check test setup

Read the frontend test config and any existing test files to understand patterns:
- `frontend/src/components/layout/__tests__/sidebar.test.tsx`
- `frontend/src/components/shared/__tests__/loading.test.tsx`
- `frontend/src/lib/__tests__/utils.test.ts`

### 2. Write dashboard page tests

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from '../page';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

// Mock the hooks
jest.mock('@/modules/analytics/hooks', () => ({
  useDashboard: jest.fn(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe('DashboardPage', () => {
  it('renders loading state initially', () => {
    (useDashboard as jest.Mock).mockReturnValue({ isLoading: true });
    renderWithProviders(<DashboardPage />);
    // Check for skeleton or loading indicator
  });

  it('renders KPI cards with data', async () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: {
        kpis: [{ label: 'Revenue', value: '$1,000', change_percent: 5.0, change_direction: 'up' }],
        revenue_chart: [],
        top_books: [],
      },
      isLoading: false,
    });
    renderWithProviders(<DashboardPage />);
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('$1,000')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useDashboard as jest.Mock).mockReturnValue({
      error: new Error('Failed'),
      isLoading: false,
    });
    renderWithProviders(<DashboardPage />);
    expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
  });
});
```

Write at least 5 tests covering loading, success, error, and empty states.
