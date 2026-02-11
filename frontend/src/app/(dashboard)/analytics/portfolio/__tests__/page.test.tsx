import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...rest}>
        {children}
      </a>
    );
  };
});

// Mock the Skeleton component
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={className} />
  ),
}));

// Mock the hooks
const mockUsePortfolioOverview = jest.fn();
jest.mock("@/modules/analytics/hooks", () => ({
  usePortfolioOverview: () => mockUsePortfolioOverview(),
}));

// Mock the components
jest.mock("@/modules/analytics/components/PortfolioOverview", () => ({
  PortfolioOverview: ({ overview }: { overview: unknown }) => (
    <div data-testid="portfolio-overview">
      {JSON.stringify(overview)}
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/BacklistTable", () => ({
  BacklistTable: ({ books }: { books: unknown[] }) => (
    <div data-testid="backlist-table">
      Books: {books.length}
    </div>
  ),
}));

// ─── Import after mocks ─────────────────────────────────────────────────────

import PortfolioPage from "../page";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("PortfolioPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading state while fetching data", () => {
    mockUsePortfolioOverview.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(<PortfolioPage />);

    expect(screen.getByText("Portfolio Economics")).toBeInTheDocument();
    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
  });

  it("renders error state when data fetch fails", () => {
    mockUsePortfolioOverview.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Failed to fetch"),
    });

    render(<PortfolioPage />);

    expect(screen.getByText("Portfolio Economics")).toBeInTheDocument();
    expect(
      screen.getByText("Failed to load portfolio data. Please try again.")
    ).toBeInTheDocument();
  });

  it("renders empty state when no data is available", () => {
    mockUsePortfolioOverview.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<PortfolioPage />);

    expect(screen.getByText("Portfolio Economics")).toBeInTheDocument();
    expect(screen.getByText("No portfolio data available.")).toBeInTheDocument();
  });

  it("renders portfolio overview and backlist table when data is loaded", () => {
    const mockOverview = {
      org_id: "org-123",
      total_books: 5,
      active_books: 4,
      total_revenue: 10000,
      total_investment: 5000,
      portfolio_roi: 100,
      monthly_revenue: 500,
      monthly_trend: 5.5,
      top_performers: [
        {
          book_id: "book-1",
          title: "Best Seller",
          genre: "Romance",
          monthly_revenue: 300,
          monthly_units: 50,
          total_revenue: 5000,
          roi: 200,
          status: "active",
        },
      ],
      underperformers: [
        {
          book_id: "book-2",
          title: "Needs Work",
          genre: "Thriller",
          monthly_revenue: 50,
          monthly_units: 5,
          total_revenue: 500,
          roi: -20,
          status: "active",
        },
      ],
      genre_distribution: { romance: 3, thriller: 2 },
      revenue_by_genre: { romance: 7000, thriller: 3000 },
      updated_at: "2024-01-01T00:00:00Z",
    };

    mockUsePortfolioOverview.mockReturnValue({
      data: mockOverview,
      isLoading: false,
      error: null,
    });

    render(<PortfolioPage />);

    expect(screen.getByText("Portfolio Economics")).toBeInTheDocument();
    expect(screen.getByTestId("portfolio-overview")).toBeInTheDocument();
    expect(screen.getByTestId("backlist-table")).toBeInTheDocument();
    expect(screen.getByText("Books: 2")).toBeInTheDocument(); // 1 top + 1 under
  });

  it("renders empty state when portfolio has no books", () => {
    const mockOverview = {
      org_id: "org-123",
      total_books: 0,
      active_books: 0,
      total_revenue: 0,
      total_investment: 0,
      portfolio_roi: 0,
      monthly_revenue: 0,
      monthly_trend: 0,
      top_performers: [],
      underperformers: [],
      genre_distribution: {},
      revenue_by_genre: {},
      updated_at: "2024-01-01T00:00:00Z",
    };

    mockUsePortfolioOverview.mockReturnValue({
      data: mockOverview,
      isLoading: false,
      error: null,
    });

    render(<PortfolioPage />);

    expect(screen.getByText("No Books Yet")).toBeInTheDocument();
    expect(
      screen.getByText("Start building your portfolio by adding books to your projects.")
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Projects" })).toHaveAttribute(
      "href",
      "/projects"
    );
  });

  it("renders navigation links to audience and greenlight pages", () => {
    const mockOverview = {
      org_id: "org-123",
      total_books: 1,
      active_books: 1,
      total_revenue: 1000,
      total_investment: 500,
      portfolio_roi: 100,
      monthly_revenue: 100,
      monthly_trend: 0,
      top_performers: [
        {
          book_id: "book-1",
          title: "Test Book",
          genre: "Fiction",
          monthly_revenue: 100,
          monthly_units: 10,
          total_revenue: 1000,
          roi: 100,
          status: "active",
        },
      ],
      underperformers: [],
      genre_distribution: { fiction: 1 },
      revenue_by_genre: { fiction: 1000 },
      updated_at: "2024-01-01T00:00:00Z",
    };

    mockUsePortfolioOverview.mockReturnValue({
      data: mockOverview,
      isLoading: false,
      error: null,
    });

    render(<PortfolioPage />);

    const audienceLink = screen.getByRole("link", { name: "Audience DNA" });
    expect(audienceLink).toBeInTheDocument();
    expect(audienceLink).toHaveAttribute("href", "/analytics/portfolio/audience");

    const greenlightLink = screen.getByRole("link", { name: "Greenlight Gate" });
    expect(greenlightLink).toBeInTheDocument();
    expect(greenlightLink).toHaveAttribute("href", "/analytics/portfolio/greenlight");
  });
});
