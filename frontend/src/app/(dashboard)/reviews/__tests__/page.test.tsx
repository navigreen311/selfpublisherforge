import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ReviewsPage from "../page";

jest.mock("@/modules/reviews/hooks", () => ({
  useAlerts: jest.fn(),
  useReviews: jest.fn(),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("@/modules/reviews/components/AlertsPanel", () => ({
  AlertsPanel: ({ alerts }: any) => (
    <div data-testid="alerts-panel">{alerts.length} alerts</div>
  ),
}));

jest.mock("@/modules/reviews/components/ReviewList", () => ({
  ReviewList: ({ reviews }: any) => (
    <div data-testid="review-list">{reviews.length} reviews</div>
  ),
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: any) => <div data-testid="skeleton" className={className} />,
}));

jest.mock("@/components/ui/select", () => ({
  Select: ({ children }: any) => <div>{children}</div>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children }: any) => <div>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: () => <div>Select</div>,
}));

import { useAlerts, useReviews } from "@/modules/reviews/hooks";
import { SentimentLabel } from "@/modules/reviews/types";

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

describe("ReviewsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    (useAlerts as jest.Mock).mockReturnValue({
      data: { items: [] },
      isLoading: false,
      error: null,
    });
    (useReviews as jest.Mock).mockReturnValue({
      data: { items: [], total_count: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review Intelligence")).toBeInTheDocument();
  });

  it("shows key elements and KPI cards", () => {
    (useAlerts as jest.Mock).mockReturnValue({
      data: { items: [] },
      isLoading: false,
      error: null,
    });
    (useReviews as jest.Mock).mockReturnValue({
      data: { items: [], total_count: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByText("Review Intelligence")).toBeInTheDocument();
    expect(screen.getByText("Total Reviews")).toBeInTheDocument();
    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    expect(screen.getByText("Positive Reviews")).toBeInTheDocument();
    expect(screen.getByText("Negative Reviews")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useAlerts as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    (useReviews as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
  });

  it("shows error state", () => {
    (useAlerts as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    (useReviews as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Failed to load"),
    });

    renderWithProviders(<ReviewsPage />);

    expect(
      screen.getByText("Failed to load review data. Please try again.")
    ).toBeInTheDocument();
  });

  it("displays reviews and alerts when data is available", () => {
    const mockAlerts = [
      { id: "1", severity: "high", message: "Test alert" },
    ];
    const mockReviews = [
      { id: "1", sentiment: SentimentLabel.POSITIVE, text: "Great book!" },
      { id: "2", sentiment: SentimentLabel.NEGATIVE, text: "Not good" },
    ];

    (useAlerts as jest.Mock).mockReturnValue({
      data: { items: mockAlerts },
      isLoading: false,
      error: null,
    });
    (useReviews as jest.Mock).mockReturnValue({
      data: { items: mockReviews, total_count: 2 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<ReviewsPage />);

    expect(screen.getByTestId("alerts-panel")).toBeInTheDocument();
    expect(screen.getByTestId("review-list")).toBeInTheDocument();
  });
});
