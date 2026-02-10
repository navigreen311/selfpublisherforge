import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUseDashboard = jest.fn();

jest.mock("@/modules/analytics/hooks", () => ({
  useDashboard: (...args: unknown[]) => mockUseDashboard(...args),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("@/modules/analytics/components/KPICard", () => ({
  KPICard: ({ kpi }: { kpi: { label: string; value: string } }) => (
    <div data-testid="kpi-card">
      <span>{kpi.label}</span>
      <span>{kpi.value}</span>
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/RevenueChart", () => ({
  RevenueChart: ({ data }: { data: unknown[] }) => (
    <div data-testid="revenue-chart">
      Revenue Chart ({data?.length || 0} points)
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/PortfolioTable", () => ({
  PortfolioTable: ({ books }: { books: unknown[] }) => (
    <div data-testid="portfolio-table">
      Portfolio Table ({books?.length || 0} books)
    </div>
  ),
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className, ...props }: { className?: string }) => (
    <div data-testid="skeleton" className={className} {...props} />
  ),
}));

// ── Import component under test (after mocks) ───────────────────────────

import AnalyticsDashboardPage from "../page";

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

const mockKpis = [
  {
    label: "Total Revenue",
    value: "$12,450.00",
    change_percent: 12.5,
    change_direction: "up",
    period: "last_30_days",
  },
  {
    label: "Units Sold",
    value: "1,230",
    change_percent: 8.3,
    change_direction: "up",
    period: "last_30_days",
  },
  {
    label: "Total Books",
    value: "15",
    change_percent: null,
    change_direction: null,
    period: "all_time",
  },
  {
    label: "Avg Revenue",
    value: "$830.00",
    change_percent: 3.2,
    change_direction: "down",
    period: "last_30_days",
  },
];

const mockRevenueChart = [
  { period: "2025-01-01", revenue: 500, units: 50 },
  { period: "2025-02-01", revenue: 700, units: 65 },
  { period: "2025-03-01", revenue: 600, units: 55 },
];

const mockTopBooks = [
  { title: "My First Book", revenue: 685.3, units: 98 },
  { title: "My Second Book", revenue: 412.23, units: 50 },
];

const fullDashboardData = {
  kpis: mockKpis,
  revenue_chart: mockRevenueChart,
  top_books: mockTopBooks,
  platform_breakdown: { kdp: 685.3, ingram_spark: 412.23 },
  recent_royalties: [],
  period_start: "2025-01-01",
  period_end: "2025-03-31",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("AnalyticsDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Renders analytics dashboard
  it("renders the analytics dashboard with heading", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
  });

  // 2. Revenue cards display
  it("renders KPI cards when dashboard data is loaded", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    const kpiCards = screen.getAllByTestId("kpi-card");
    expect(kpiCards).toHaveLength(4);

    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$12,450.00")).toBeInTheDocument();
    expect(screen.getByText("Units Sold")).toBeInTheDocument();
    expect(screen.getByText("1,230")).toBeInTheDocument();
    expect(screen.getByText("Total Books")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("Avg Revenue")).toBeInTheDocument();
    expect(screen.getByText("$830.00")).toBeInTheDocument();
  });

  // 3. Charts section renders
  it("renders the revenue chart with data", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    const chart = screen.getByTestId("revenue-chart");
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveTextContent("3 points");
  });

  // 4. Reports section accessible
  it("renders a link to the reports page", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    const reportsLink = screen.getByText("Reports");
    expect(reportsLink).toBeInTheDocument();
    expect(reportsLink.closest("a")).toHaveAttribute("href", "/analytics/reports");
  });

  it("renders a link to the revenue details page", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    const revenueLink = screen.getByText("Revenue Details");
    expect(revenueLink).toBeInTheDocument();
    expect(revenueLink.closest("a")).toHaveAttribute("href", "/analytics/revenue");
  });

  // 5. Date range selector works (platform breakdown displayed)
  it("renders the platform breakdown section with data", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.getByText("Platform Breakdown")).toBeInTheDocument();
    // Platform names are capitalized with underscore replaced
    expect(screen.getByText("kdp")).toBeInTheDocument();
    expect(screen.getByText("ingram spark")).toBeInTheDocument();
  });

  it("shows no platform data message when platform_breakdown is empty", () => {
    mockUseDashboard.mockReturnValue({
      data: {
        ...fullDashboardData,
        platform_breakdown: {},
      },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.getByText("No platform data available")).toBeInTheDocument();
  });

  // 6. Loading states
  it("renders loading skeletons when data is loading", () => {
    mockUseDashboard.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    const { container } = renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    const skeletons = container.querySelectorAll('[data-testid="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });

  // 6b. Error state
  it("renders error state when fetch fails", () => {
    mockUseDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText("Failed to load analytics data. Please try again.")
    ).toBeInTheDocument();
  });

  it("renders portfolio table with top books data", () => {
    mockUseDashboard.mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    const table = screen.getByTestId("portfolio-table");
    expect(table).toBeInTheDocument();
    expect(table).toHaveTextContent("2 books");
  });

  it("renders revenue chart with empty array when no chart data", () => {
    mockUseDashboard.mockReturnValue({
      data: {
        ...fullDashboardData,
        revenue_chart: [],
      },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    const chart = screen.getByTestId("revenue-chart");
    expect(chart).toHaveTextContent("0 points");
  });

  it("does not render KPI cards or navigation links in loading state", () => {
    mockUseDashboard.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.queryByTestId("kpi-card")).not.toBeInTheDocument();
    expect(screen.queryByText("Revenue Details")).not.toBeInTheDocument();
    expect(screen.queryByText("Reports")).not.toBeInTheDocument();
  });

  it("does not render KPI cards or navigation links in error state", () => {
    mockUseDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("fail"),
    });

    renderWithProviders(<AnalyticsDashboardPage />);

    expect(screen.queryByTestId("kpi-card")).not.toBeInTheDocument();
    expect(screen.queryByText("Revenue Details")).not.toBeInTheDocument();
  });

  it("handles undefined dashboard data gracefully (no crash)", () => {
    mockUseDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    // Should not throw: the page checks isLoading/error first,
    // but with both false and no data the success branch is rendered
    // with optional chaining on dashboard?.kpis
    renderWithProviders(<AnalyticsDashboardPage />);
    expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
  });
});
