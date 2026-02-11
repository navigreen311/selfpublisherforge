import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUseAlerts = jest.fn();
const mockUseReviews = jest.fn();

jest.mock("@/modules/reviews/hooks", () => ({
  useAlerts: (...args: unknown[]) => mockUseAlerts(...args),
  useReviews: (...args: unknown[]) => mockUseReviews(...args),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("@/modules/reviews/components/AlertsPanel", () => ({
  AlertsPanel: ({ alerts }: { alerts: unknown[] }) => (
    <div data-testid="alerts-panel">
      Alerts Panel ({alerts?.length || 0} alerts)
    </div>
  ),
}));

jest.mock("@/modules/reviews/components/ReviewList", () => ({
  ReviewList: ({ reviews }: { reviews: unknown[] }) => (
    <div data-testid="review-list">
      Review List ({reviews?.length || 0} reviews)
    </div>
  ),
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className, ...props }: { className?: string }) => (
    <div data-testid="skeleton" className={className} {...props} />
  ),
}));

jest.mock("@/components/ui/select", () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-value={value}>{children}</div>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <div>{placeholder}</div>,
}));

// ── Import component under test (after mocks) ───────────────────────────

import ReviewsPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Test Data ────────────────────────────────────────────────────────────

const mockAlerts = [
  {
    id: "alert-1",
    org_id: "org-1",
    book_id: "book-1",
    alert_type: "negative_spike",
    severity: "high",
    title: "Negative Review Spike",
    description: "Detected 5 negative reviews in the last 24 hours",
    data: { count: 5 },
    is_acknowledged: false,
    acknowledged_at: null,
    acknowledged_by: null,
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T10:00:00Z",
  },
  {
    id: "alert-2",
    org_id: "org-1",
    book_id: "book-2",
    alert_type: "velocity_drop",
    severity: "medium",
    title: "Review Velocity Drop",
    description: "Review rate dropped by 40% this week",
    data: { change_pct: -40 },
    is_acknowledged: false,
    acknowledged_at: null,
    acknowledged_by: null,
    created_at: "2025-01-14T15:00:00Z",
    updated_at: "2025-01-14T15:00:00Z",
  },
];

const mockReviews = [
  {
    id: "review-1",
    org_id: "org-1",
    book_id: "book-1",
    source: "amazon",
    source_review_id: "amz-123",
    reviewer_name: "John Doe",
    reviewer_profile_url: null,
    star_rating: 5.0,
    title: "Great book!",
    body: "This book was amazing. Highly recommend.",
    review_date: "2025-01-10T12:00:00Z",
    verified_purchase: true,
    helpful_count: 10,
    is_competitor: false,
    sentiment: "positive",
    sentiment_score: 0.9,
    themes: null,
    analyzed_at: "2025-01-10T13:00:00Z",
    created_at: "2025-01-10T12:00:00Z",
    updated_at: "2025-01-10T13:00:00Z",
  },
  {
    id: "review-2",
    org_id: "org-1",
    book_id: "book-1",
    source: "goodreads",
    source_review_id: "gr-456",
    reviewer_name: "Jane Smith",
    reviewer_profile_url: null,
    star_rating: 2.0,
    title: "Disappointing",
    body: "Expected more from this book. The plot was weak.",
    review_date: "2025-01-12T14:00:00Z",
    verified_purchase: false,
    helpful_count: 3,
    is_competitor: false,
    sentiment: "negative",
    sentiment_score: -0.6,
    themes: null,
    analyzed_at: "2025-01-12T15:00:00Z",
    created_at: "2025-01-12T14:00:00Z",
    updated_at: "2025-01-12T15:00:00Z",
  },
];

// ── Tests ────────────────────────────────────────────────────────────────

describe("ReviewsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Renders review intelligence page
  it("renders the review intelligence page with heading", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: mockAlerts, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review Intelligence")).toBeInTheDocument();
  });

  // 2. KPI cards display correctly
  it("renders KPI cards with correct data", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: mockAlerts, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Total Reviews")).toBeInTheDocument();
    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    expect(screen.getByText("Positive Reviews")).toBeInTheDocument();
    expect(screen.getByText("Negative Reviews")).toBeInTheDocument();

    // Check that total count is displayed
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  // 3. Alerts panel renders when there are alerts
  it("renders alerts panel when alerts exist", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: mockAlerts, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    const alertsPanel = screen.getByTestId("alerts-panel");
    expect(alertsPanel).toBeInTheDocument();
    expect(alertsPanel).toHaveTextContent("2 alerts");
  });

  // 4. Alerts panel does not render when there are no alerts
  it("does not render alerts panel when there are no alerts", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: [], next_cursor: null, has_more: false, total_count: 0 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.queryByTestId("alerts-panel")).not.toBeInTheDocument();
  });

  // 5. Review list renders
  it("renders the review list with data", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: mockAlerts, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    const reviewList = screen.getByTestId("review-list");
    expect(reviewList).toBeInTheDocument();
    expect(reviewList).toHaveTextContent("2 reviews");
  });

  // 6. Loading states
  it("renders loading skeletons when data is loading", () => {
    mockUseAlerts.mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    mockUseReviews.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    const { container } = renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review Intelligence")).toBeInTheDocument();
    const skeletons = container.querySelectorAll('[data-testid="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  // 7. Error state
  it("renders error state when fetch fails", () => {
    mockUseAlerts.mockReturnValue({
      data: undefined,
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review Intelligence")).toBeInTheDocument();
    expect(
      screen.getByText("Failed to load review data. Please try again.")
    ).toBeInTheDocument();
  });

  // 8. Navigation links
  it("renders link to analytics page", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: mockAlerts, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    const analyticsLink = screen.getByText("Analytics");
    expect(analyticsLink).toBeInTheDocument();
    expect(analyticsLink.closest("a")).toHaveAttribute("href", "/reviews/analytics");
  });

  // 9. Book selector section
  it("renders book selector section", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: mockAlerts, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: mockReviews, next_cursor: null, has_more: false, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review by Book")).toBeInTheDocument();
    expect(
      screen.getByText("Select a book to view detailed review analytics, sentiment trends, and alerts.")
    ).toBeInTheDocument();
  });

  // 10. Does not render review list in loading state
  it("does not render review list when data is loading", () => {
    mockUseAlerts.mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    mockUseReviews.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.queryByTestId("review-list")).not.toBeInTheDocument();
  });

  // 11. Handles empty review data
  it("handles empty review data gracefully", () => {
    mockUseAlerts.mockReturnValue({
      data: { items: [], next_cursor: null, has_more: false, total_count: 0 },
      isLoading: false,
    });
    mockUseReviews.mockReturnValue({
      data: { items: [], next_cursor: null, has_more: false, total_count: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review Intelligence")).toBeInTheDocument();
    const reviewList = screen.getByTestId("review-list");
    expect(reviewList).toHaveTextContent("0 reviews");
  });
});
