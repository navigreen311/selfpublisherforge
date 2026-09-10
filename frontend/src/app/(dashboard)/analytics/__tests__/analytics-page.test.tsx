import React from "react";
import { render, screen, within } from "@testing-library/react";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUseEnhancedDashboard = jest.fn();

jest.mock("@/modules/analytics/hooks", () => ({
  useEnhancedDashboard: (...args: unknown[]) => mockUseEnhancedDashboard(...args),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// The overview tab renders three recharts-backed panels. They have their own
// suites; here they only need to be identifiable.
jest.mock("@/modules/analytics/components/RevenueOverviewChart", () => ({
  RevenueOverviewChart: ({ data }: { data: unknown[] }) => (
    <div data-testid="revenue-overview-chart">{data?.length ?? 0} points</div>
  ),
}));

jest.mock("@/modules/analytics/components/RevenueBreakdownCharts", () => ({
  RevenueBreakdownCharts: ({
    revenueByBook,
    revenueByFormat,
  }: {
    revenueByBook: unknown[];
    revenueByFormat: unknown[];
  }) => (
    <div data-testid="revenue-breakdown-charts">
      {revenueByBook?.length ?? 0}/{revenueByFormat?.length ?? 0}
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/AnalyticsInsightsPanel", () => ({
  AnalyticsInsightsPanel: ({ insights }: { insights: unknown[] }) => (
    <div data-testid="analytics-insights">{insights?.length ?? 0} insights</div>
  ),
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={className} />
  ),
}));

// ── Import component under test (after mocks) ────────────────────────────

import AnalyticsDashboardPage from "../page";

// ── Test data ────────────────────────────────────────────────────────────

const dashboardData = {
  stats: [
    { label: "Total Revenue", value: "$12,450.00", change_percent: 12.5, change_direction: "up" },
    { label: "Units Sold", value: "1,230", change_percent: 8.3, change_direction: "up" },
    { label: "Royalties", value: "$8,715.00", change_percent: -3.2, change_direction: "down" },
    { label: "Total Books", value: "15", change_percent: null, change_direction: null },
  ],
  trend_data: [
    { period: "2025-01-01", revenue: 500 },
    { period: "2025-02-01", revenue: 700 },
  ],
  revenue_by_book: [{ title: "My First Book", revenue: 685.3 }],
  revenue_by_format: [{ format: "ebook", revenue: 500 }],
  insights: [{ title: "Revenue is up" }],
};

function loaded(data: unknown = dashboardData) {
  mockUseEnhancedDashboard.mockReturnValue({ data, isLoading: false, error: null });
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Tests ────────────────────────────────────────────────────────────────

describe("AnalyticsDashboardPage", () => {
  describe("page shell", () => {
    it("renders the heading and subtitle", () => {
      loaded();
      render(<AnalyticsDashboardPage />);

      expect(
        screen.getByRole("heading", { name: "Analytics Dashboard" })
      ).toBeInTheDocument();
      expect(
        screen.getByText("Track your revenue, sales, and book performance")
      ).toBeInTheDocument();
    });

    it("links to the revenue details and reports pages", () => {
      loaded();
      render(<AnalyticsDashboardPage />);

      const nav = screen.getByRole("navigation", { name: "Analytics navigation" });
      expect(within(nav).getByRole("link", { name: /revenue analytics/i })).toHaveAttribute(
        "href",
        "/analytics/revenue"
      );
      expect(within(nav).getByRole("link", { name: /reports/i })).toHaveAttribute(
        "href",
        "/analytics/reports"
      );
    });
  });

  describe("dashboard states", () => {
    it("renders skeletons while loading", () => {
      mockUseEnhancedDashboard.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });
      render(<AnalyticsDashboardPage />);

      expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
      expect(screen.queryByText("Total Revenue")).not.toBeInTheDocument();
    });

    it("renders an error message when the query fails", () => {
      mockUseEnhancedDashboard.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("boom"),
      });
      render(<AnalyticsDashboardPage />);

      expect(
        screen.getByText("Failed to load dashboard data. Please try again.")
      ).toBeInTheDocument();
      // The heading belongs to the page, not the dashboard, so it survives.
      expect(
        screen.getByRole("heading", { name: "Analytics Dashboard" })
      ).toBeInTheDocument();
    });

    it("renders a stat card per stat, with its change percentage", () => {
      loaded();
      render(<AnalyticsDashboardPage />);

      expect(screen.getByText("Total Revenue")).toBeInTheDocument();
      expect(screen.getByText("$12,450.00")).toBeInTheDocument();
      expect(screen.getByText("12.5%")).toBeInTheDocument();
      // A negative change is rendered as its absolute value.
      expect(screen.getByText("3.2%")).toBeInTheDocument();
      // Total Books has no change_percent, so no percentage row.
      expect(screen.getByText("15")).toBeInTheDocument();
    });

    it("falls back to four empty cards when there are no stats", () => {
      loaded({ ...dashboardData, stats: [] });
      render(<AnalyticsDashboardPage />);

      expect(screen.getAllByText("No data available")).toHaveLength(4);
    });

    it("passes the dashboard data through to the overview panels", () => {
      loaded();
      render(<AnalyticsDashboardPage />);

      expect(screen.getByTestId("revenue-overview-chart")).toHaveTextContent("2 points");
      expect(screen.getByTestId("revenue-breakdown-charts")).toHaveTextContent("1/1");
      expect(screen.getByTestId("analytics-insights")).toHaveTextContent("1 insights");
    });

    it("does not crash when the dashboard payload is undefined", () => {
      mockUseEnhancedDashboard.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      });
      render(<AnalyticsDashboardPage />);

      expect(screen.getAllByText("No data available")).toHaveLength(4);
      expect(screen.getByTestId("revenue-overview-chart")).toHaveTextContent("0 points");
    });

    it("renders every analytics tab", () => {
      loaded();
      render(<AnalyticsDashboardPage />);

      for (const tab of ["Overview", "Sales", "Books", "Advertising", "KDP Reports"]) {
        expect(screen.getByRole("tab", { name: tab })).toBeInTheDocument();
      }
    });

    it("defaults to the 30-day period with comparison off", () => {
      loaded();
      render(<AnalyticsDashboardPage />);

      expect(mockUseEnhancedDashboard).toHaveBeenCalledWith("30d", "none");
      expect(screen.getByLabelText("Compare with previous period")).not.toBeChecked();
    });
  });
});
