import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PortfolioPage from "../page";

jest.mock("@/modules/analytics/hooks", () => ({
  usePortfolioOverview: jest.fn(),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("@/modules/analytics/components/PortfolioOverview", () => ({
  PortfolioOverview: ({ overview }: any) => (
    <div data-testid="portfolio-overview">Portfolio data</div>
  ),
}));

jest.mock("@/modules/analytics/components/BacklistTable", () => ({
  BacklistTable: ({ books }: any) => (
    <div data-testid="backlist-table">{books.length} books</div>
  ),
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: any) => <div data-testid="skeleton" className={className} />,
}));

import { usePortfolioOverview } from "@/modules/analytics/hooks";

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

describe("PortfolioPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: {
        top_performers: [],
        underperformers: [],
      },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PortfolioPage />);

    expect(screen.getByText("Portfolio Economics")).toBeInTheDocument();
  });

  it("shows key elements and navigation", () => {
    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: {
        top_performers: [],
        underperformers: [],
      },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PortfolioPage />);

    expect(screen.getByText("Portfolio Economics")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /audience dna/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /greenlight gate/i })).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<PortfolioPage />);

    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
  });

  it("shows error state", () => {
    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Failed to load"),
    });

    renderWithProviders(<PortfolioPage />);

    expect(
      screen.getByText("Failed to load portfolio data. Please try again.")
    ).toBeInTheDocument();
  });

  it("shows empty state when no data available", () => {
    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PortfolioPage />);

    expect(screen.getByText("No portfolio data available.")).toBeInTheDocument();
  });

  it("displays portfolio overview and backlist when data is available", () => {
    const mockOverview = {
      top_performers: [
        { id: "1", title: "Book 1", revenue: 1000 },
      ],
      underperformers: [
        { id: "2", title: "Book 2", revenue: 50 },
      ],
    };

    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: mockOverview,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PortfolioPage />);

    expect(screen.getByTestId("portfolio-overview")).toBeInTheDocument();
    expect(screen.getByTestId("backlist-table")).toBeInTheDocument();
  });

  it("shows empty state when no books exist", () => {
    (usePortfolioOverview as jest.Mock).mockReturnValue({
      data: {
        top_performers: [],
        underperformers: [],
      },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PortfolioPage />);

    expect(screen.getByText("No Books Yet")).toBeInTheDocument();
    expect(
      screen.getByText("Start building your portfolio by adding books to your projects.")
    ).toBeInTheDocument();
  });
});
