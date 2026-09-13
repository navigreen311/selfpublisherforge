import React from "react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { render } from "@/test-utils";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUseReviewStats = jest.fn();
const mockUseAlerts = jest.fn();

const emptyQuery = {
  data: undefined,
  isLoading: false,
  isError: false,
  error: null,
  refetch: jest.fn(),
};

const emptyMutation = {
  mutate: jest.fn(),
  mutateAsync: jest.fn().mockResolvedValue({}),
  isPending: false,
  isError: false,
  error: null,
  reset: jest.fn(),
};

jest.mock("@/modules/reviews/hooks", () => ({
  useReviewStats: () => mockUseReviewStats(),
  useAlerts: () => mockUseAlerts(),
  useSentimentTrend: () => emptyQuery,
  useBookReviewSummaries: () => emptyQuery,
  useReviews: () => emptyQuery,
  useReviewInsights: () => emptyQuery,
  useAlertNotifications: () => emptyQuery,
  useRefreshInsights: () => emptyMutation,
  useMarkReviewRead: () => emptyMutation,
  useFlagReview: () => emptyMutation,
  useDeleteReviewAlert: () => emptyMutation,
}));

// The tab panels have their own suites; here they only need to be identifiable.
jest.mock("@/components/review-intelligence/SentimentTrendChart", () => ({
  SentimentTrendChart: () => <div data-testid="sentiment-trend" />,
}));
jest.mock("@/components/review-intelligence/RatingDistribution", () => ({
  RatingDistribution: () => <div data-testid="rating-distribution" />,
}));
jest.mock("@/components/review-intelligence/BookReviewCards", () => ({
  BookReviewCards: () => <div data-testid="book-review-cards" />,
}));
jest.mock("@/components/review-intelligence/ReviewFeed", () => ({
  ReviewFeed: () => <div data-testid="review-feed" />,
}));
jest.mock("@/components/review-intelligence/ReviewInsights", () => ({
  ReviewInsights: () => <div data-testid="review-insights" />,
}));
jest.mock("@/components/review-intelligence/ReviewAcquisition", () => ({
  ReviewAcquisition: () => <div data-testid="review-acquisition" />,
}));
jest.mock("@/components/review-intelligence/ReviewAlertsTab", () => ({
  ReviewAlertsTab: ({ alerts }: { alerts: unknown[] }) => (
    <div data-testid="review-alerts">{alerts.length} alerts</div>
  ),
}));

import ReviewsPage from "../page";

// ── Test data ────────────────────────────────────────────────────────────

const stats = {
  total: 1284,
  avg_rating: 4.3,
  this_month: 96,
  this_month_change_pct: 12,
  sentiment_score: 78,
  velocity: 24,
  genre_avg_velocity: 18,
  needs_attention: 3,
  book_count: 7,
  rating_distribution: { 5: 800, 4: 300, 3: 100, 2: 50, 1: 34 },
};

beforeEach(() => {
  jest.clearAllMocks();
  mockUseReviewStats.mockReturnValue({ data: stats, isLoading: false });
  mockUseAlerts.mockReturnValue({ data: { items: [] }, isLoading: false });
});

// ── Tests ────────────────────────────────────────────────────────────────

describe("ReviewsPage", () => {
  it("renders the heading and subtitle", () => {
    render(<ReviewsPage />);

    expect(
      screen.getByRole("heading", { name: "Review Intelligence" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Monitor reviews, extract insights, and protect your reputation."
      )
    ).toBeInTheDocument();
  });

  it("renders the six stat cards from the stats query", () => {
    render(<ReviewsPage />);

    expect(screen.getByText("Total Reviews")).toBeInTheDocument();
    expect(screen.getByText("1,284")).toBeInTheDocument();

    expect(screen.getByText("Avg Rating")).toBeInTheDocument();
    expect(screen.getByText("4.3")).toBeInTheDocument();

    expect(screen.getByText("This Month")).toBeInTheDocument();
    expect(screen.getByText("96")).toBeInTheDocument();

    expect(screen.getByText("Needs Attention")).toBeInTheDocument();
  });

  it("shows placeholders in the stat cards while stats load", () => {
    mockUseReviewStats.mockReturnValue({ data: undefined, isLoading: true });
    render(<ReviewsPage />);

    expect(screen.queryByText("Total Reviews")).not.toBeInTheDocument();
  });

  it("falls back to zeroes when the stats query returns nothing", () => {
    mockUseReviewStats.mockReturnValue({ data: undefined, isLoading: false });
    render(<ReviewsPage />);

    expect(screen.getByText("Total Reviews")).toBeInTheDocument();
    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
  });

  it("opens on the books tab", () => {
    render(<ReviewsPage />);

    expect(screen.getByTestId("book-review-cards")).toBeInTheDocument();
    expect(screen.queryByTestId("review-feed")).not.toBeInTheDocument();
  });

  it("switches to the alerts tab and passes it the alerts", async () => {
    const user = userEvent.setup();
    mockUseAlerts.mockReturnValue({
      data: { items: [{ id: "a1" }, { id: "a2" }] },
      isLoading: false,
    });
    render(<ReviewsPage />);

    await user.click(screen.getByRole("button", { name: /alerts/i }));

    expect(await screen.findByTestId("review-alerts")).toHaveTextContent(
      "2 alerts"
    );
  });

  it("switches to the review feed", async () => {
    const user = userEvent.setup();
    render(<ReviewsPage />);

    await user.click(screen.getByRole("button", { name: /review feed/i }));

    expect(await screen.findByTestId("review-feed")).toBeInTheDocument();
  });
});
