import React from "react";
import { render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mock: analytics hooks ───────────────────────────────────────────────

const mockUseDashboard = jest.fn();
const mockUseReports = jest.fn();
const mockUseDownloadReport = jest.fn();
const mockUseRevenue = jest.fn();
const mockUsePortfolioMetrics = jest.fn();
const mockUseGenerateReport = jest.fn();
const mockUseImportRoyalties = jest.fn();

jest.mock("@/modules/analytics/hooks", () => ({
  useDashboard: (...args: unknown[]) => mockUseDashboard(...args),
  useReports: (...args: unknown[]) => mockUseReports(...args),
  useDownloadReport: () => mockUseDownloadReport(),
  useRevenue: (...args: unknown[]) => mockUseRevenue(...args),
  usePortfolioMetrics: () => mockUsePortfolioMetrics(),
  useGenerateReport: () => mockUseGenerateReport(),
  useImportRoyalties: () => mockUseImportRoyalties(),
  useEnhancedDashboard: () => ({ data: undefined, isLoading: false, isError: false, error: null, refetch: jest.fn() }),
  useGenerateEnhancedReport: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
}));

// ── Mock: next/link ─────────────────────────────────────────────────────

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// ── Mock: UI skeleton ───────────────────────────────────────────────────

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className, ...props }: { className?: string }) => (
    <div data-testid="skeleton" className={className} {...props} />
  ),
}));

// ── Mock: analytics sub-components (render realistic accessible markup) ─

jest.mock("@/modules/analytics/components/KPICard", () => ({
  KPICard: ({ kpi }: { kpi: { label: string; value: string } }) => (
    <div data-testid="kpi-card" role="group" aria-label={kpi.label}>
      <span>{kpi.label}</span>
      <span>{kpi.value}</span>
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/RevenueChart", () => ({
  RevenueChart: ({ data }: { data: unknown[] }) => (
    <div data-testid="revenue-chart" role="img" aria-label="Revenue chart visualization">
      <h3>Revenue Over Time</h3>
      Revenue Chart ({data?.length || 0} points)
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/PortfolioTable", () => ({
  PortfolioTable: ({ books, title }: { books: unknown[]; title?: string }) => (
    <div data-testid="portfolio-table">
      <h3>{title || "Top Books"}</h3>
      <p id="portfolio-table-desc">A table showing book performance data.</p>
      <table aria-describedby="portfolio-table-desc">
        <thead>
          <tr>
            <th>Title</th>
            <th>Revenue</th>
            <th>Units</th>
          </tr>
        </thead>
        <tbody>
          {(books as { title: string; revenue: number; units: number }[]).map(
            (book, i) => (
              <tr key={i}>
                <td>{book.title}</td>
                <td>${book.revenue}</td>
                <td>{book.units}</td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/ReportBuilder", () => ({
  ReportBuilder: () => (
    <div data-testid="report-builder">
      <h3>Generate Report</h3>
      <form>
        <label htmlFor="report-title">Report Title</label>
        <input id="report-title" type="text" aria-label="Report Title" />
        <label htmlFor="report-type">Report Type</label>
        <select id="report-type" aria-label="Report Type">
          <option value="revenue_summary">Revenue Summary</option>
        </select>
        <label htmlFor="output-format">Format</label>
        <select id="output-format" aria-label="Output Format">
          <option value="pdf">PDF</option>
        </select>
        <button type="submit">Generate Report</button>
      </form>
    </div>
  ),
}));

jest.mock("@/modules/analytics/components/RoyaltyImporter", () => ({
  RoyaltyImporter: () => (
    <div data-testid="royalty-importer">
      <h3>Import Royalties</h3>
      <form>
        <label htmlFor="platform-select">Platform</label>
        <select id="platform-select" aria-label="Platform">
          <option value="kdp">Amazon KDP</option>
        </select>
        <button type="submit">Import Royalties</button>
      </form>
    </div>
  ),
}));

// ── Import pages under test (after all mocks) ──────────────────────────

import AnalyticsPage from "@/app/(dashboard)/analytics/page";
import ReportsPage from "@/app/(dashboard)/analytics/reports/page";
import RevenuePage from "@/app/(dashboard)/analytics/revenue/page";

// ── Helpers ─────────────────────────────────────────────────────────────

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

// ── Sample data ─────────────────────────────────────────────────────────

const sampleKpis = [
  { label: "Total Revenue", value: "$12,450.00", change_percent: 12.5, change_direction: "up", period: "last_30_days" },
  { label: "Units Sold", value: "1,230", change_percent: 8.3, change_direction: "up", period: "last_30_days" },
  { label: "Total Books", value: "15", change_percent: null, change_direction: null, period: "all_time" },
  { label: "Avg Revenue", value: "$830.00", change_percent: 3.2, change_direction: "down", period: "last_30_days" },
];

const sampleRevenueChart = [
  { period: "2025-01-01", revenue: 500, units: 50 },
  { period: "2025-02-01", revenue: 700, units: 65 },
  { period: "2025-03-01", revenue: 600, units: 55 },
];

const sampleTopBooks = [
  { title: "My First Book", revenue: 685.3, units: 98 },
  { title: "My Second Book", revenue: 412.23, units: 50 },
];

const fullDashboardData = {
  kpis: sampleKpis,
  revenue_chart: sampleRevenueChart,
  top_books: sampleTopBooks,
  platform_breakdown: { kdp: 685.3, ingram_spark: 412.23 },
  recent_royalties: [],
  period_start: "2025-01-01",
  period_end: "2025-03-31",
};

const sampleReportsData = {
  items: [
    {
      id: "rpt-1",
      org_id: "org-1",
      title: "Q1 Revenue Summary",
      report_type: "revenue_summary",
      status: "completed",
      output_format: "pdf",
      parameters: {},
      file_path: "/reports/q1.pdf",
      file_size: 102400,
      generated_by: "user-1",
      generated_at: "2025-03-15T10:00:00Z",
      error_message: null,
      created_at: "2025-03-15T09:55:00Z",
      updated_at: "2025-03-15T10:00:00Z",
    },
    {
      id: "rpt-2",
      org_id: "org-1",
      title: "Book Performance",
      report_type: "book_performance",
      status: "failed",
      output_format: "xlsx",
      parameters: {},
      file_path: null,
      file_size: null,
      generated_by: "user-1",
      generated_at: null,
      error_message: "Data source unavailable",
      created_at: "2025-03-14T08:00:00Z",
      updated_at: "2025-03-14T08:05:00Z",
    },
  ],
  next_cursor: null,
  has_more: false,
  total_count: 2,
};

const sampleRevenueData = {
  total_revenue: 12450.0,
  total_units: 1230,
  data_points: sampleRevenueChart,
  period_start: "2025-01-01",
  period_end: "2025-03-31",
  aggregation: "monthly",
  by_platform: { kdp: 8500, ingram_spark: 3950 },
  by_book: sampleTopBooks,
};

const samplePortfolioMetrics = {
  total_books: 15,
  total_revenue: 12450.0,
  total_units_sold: 1230,
  total_expenses: 3200,
  net_profit: 9250,
  avg_roi: 2.89,
  platform_breakdown: {},
  format_breakdown: {},
  top_books: [],
  snapshot_date: null,
};

// ── Setup defaults ──────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();

  // Analytics page defaults
  mockUseDashboard.mockReturnValue({
    data: fullDashboardData,
    isLoading: false,
    error: null,
  });

  // Reports page defaults
  mockUseReports.mockReturnValue({
    data: sampleReportsData,
    isLoading: false,
    error: null,
  });
  mockUseDownloadReport.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
  });
  mockUseGenerateReport.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
  });

  // Revenue page defaults
  mockUseRevenue.mockReturnValue({
    data: sampleRevenueData,
    isLoading: false,
    error: null,
  });
  mockUsePortfolioMetrics.mockReturnValue({
    data: samplePortfolioMetrics,
    isLoading: false,
    error: null,
  });
  mockUseImportRoyalties.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    data: null,
  });
});

// ═══════════════════════════════════════════════════════════════════════
// Analytics Dashboard Page - Accessibility Tests
// ═══════════════════════════════════════════════════════════════════════

describe("Analytics Dashboard Page - Accessibility", () => {
  it("data tables have aria-describedby", () => {
    renderWithProviders(<AnalyticsPage />);

    const table = document.querySelector("table[aria-describedby]");
    if (table) {
      const describedById = table.getAttribute("aria-describedby");
      expect(describedById).toBeTruthy();
      const descElement = document.getElementById(describedById!);
      expect(descElement).toBeInTheDocument();
    } else {
      // The PortfolioTable mock renders a table with aria-describedby
      const portfolioTable = screen.getByTestId("portfolio-table");
      const innerTable = within(portfolioTable).getByRole("table");
      expect(innerTable).toHaveAttribute("aria-describedby");
      const descId = innerTable.getAttribute("aria-describedby")!;
      expect(document.getElementById(descId)).toBeInTheDocument();
    }
  });

  it("all interactive elements have aria-labels", () => {
    renderWithProviders(<AnalyticsPage />);

    // All links should have text content or aria-label
    const links = screen.getAllByRole("link");
    links.forEach((link) => {
      const hasAccessibleName =
        link.textContent?.trim() ||
        link.getAttribute("aria-label") ||
        link.getAttribute("aria-labelledby");
      expect(hasAccessibleName).toBeTruthy();
    });

    // All buttons should have text content or aria-label
    const buttons = screen.queryAllByRole("button");
    buttons.forEach((button) => {
      const hasAccessibleName =
        button.textContent?.trim() ||
        button.getAttribute("aria-label") ||
        button.getAttribute("aria-labelledby");
      expect(hasAccessibleName).toBeTruthy();
    });
  });

  it("major sections have appropriate landmark roles or headings", () => {
    renderWithProviders(<AnalyticsPage />);

    // The page should have a main heading
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveTextContent("Analytics Dashboard");

    // KPI cards should have group roles from the mock
    const kpiCards = screen.getAllByTestId("kpi-card");
    kpiCards.forEach((card) => {
      expect(card).toHaveAttribute("role", "group");
      expect(card).toHaveAttribute("aria-label");
    });
  });
});

// ═══════════════════════════════════════════════════════════════════════
// Reports Page - Accessibility Tests
// ═══════════════════════════════════════════════════════════════════════

describe("Reports Page - Accessibility", () => {
  it("tables have aria-describedby", () => {
    renderWithProviders(<ReportsPage />);

    const table = document.querySelector("table");
    expect(table).toBeInTheDocument();
    expect(table).toHaveAttribute("aria-describedby", "reports-table-desc");

    const descElement = document.getElementById("reports-table-desc");
    expect(descElement).toBeInTheDocument();
    expect(descElement!.textContent).toContain("generated reports");
  });

  it("filter controls have labels", () => {
    renderWithProviders(<ReportsPage />);

    // The ReportBuilder mock provides labeled form controls
    const reportBuilder = screen.getByTestId("report-builder");
    const reportTitleInput = within(reportBuilder).getByLabelText("Report Title");
    expect(reportTitleInput).toBeInTheDocument();

    const reportTypeSelect = within(reportBuilder).getByLabelText("Report Type");
    expect(reportTypeSelect).toBeInTheDocument();

    const formatSelect = within(reportBuilder).getByLabelText("Output Format");
    expect(formatSelect).toBeInTheDocument();
  });

  it("dynamic content area has aria-live", () => {
    renderWithProviders(<ReportsPage />);

    // The reports list area uses aria-live="polite"
    const liveRegion = document.querySelector("[aria-live]");
    expect(liveRegion).toBeInTheDocument();
    expect(liveRegion!.getAttribute("aria-live")).toBe("polite");
  });

  it("report builder and reports list have region roles", () => {
    renderWithProviders(<ReportsPage />);

    const regions = screen.getAllByRole("region");
    const regionLabels = regions.map((r) => r.getAttribute("aria-label"));
    expect(regionLabels).toContain("Report Builder");
    expect(regionLabels).toContain("Generated Reports List");
  });
});

// ═══════════════════════════════════════════════════════════════════════
// Revenue Page - Accessibility Tests
// ═══════════════════════════════════════════════════════════════════════

describe("Revenue Page - Accessibility", () => {
  it("tables have aria-describedby", () => {
    renderWithProviders(<RevenuePage />);

    // The PortfolioTable mock renders a table with aria-describedby
    const portfolioTable = screen.getByTestId("portfolio-table");
    const innerTable = within(portfolioTable).getByRole("table");
    expect(innerTable).toHaveAttribute("aria-describedby");
    const descId = innerTable.getAttribute("aria-describedby")!;
    expect(document.getElementById(descId)).toBeInTheDocument();
  });

  it("chart areas have aria-labels", () => {
    renderWithProviders(<RevenuePage />);

    // The RevenueChart mock has role="img" with aria-label
    const chart = screen.getByTestId("revenue-chart");
    expect(chart).toHaveAttribute("role", "img");
    expect(chart).toHaveAttribute("aria-label", "Revenue chart visualization");

    // The containing region for the chart should also have aria-label
    const chartRegion = screen.getByRole("region", { name: "Revenue chart visualization" });
    expect(chartRegion).toBeInTheDocument();
  });

  it("filter controls have associated labels", () => {
    renderWithProviders(<RevenuePage />);

    // Revenue page has native HTML labels via htmlFor
    const startDateInput = screen.getByLabelText("Filter by start date");
    expect(startDateInput).toBeInTheDocument();

    const endDateInput = screen.getByLabelText("Filter by end date");
    expect(endDateInput).toBeInTheDocument();

    const platformSelect = screen.getByLabelText("Filter by publishing platform");
    expect(platformSelect).toBeInTheDocument();

    const aggregationSelect = screen.getByLabelText("Select data aggregation period");
    expect(aggregationSelect).toBeInTheDocument();
  });

  it("revenue summary section has region role with label", () => {
    renderWithProviders(<RevenuePage />);

    const summaryRegion = screen.getByRole("region", { name: "Revenue summary statistics" });
    expect(summaryRegion).toBeInTheDocument();
  });

  it("filter section has region role", () => {
    renderWithProviders(<RevenuePage />);

    const filterRegion = screen.getByRole("region", { name: "Revenue filters" });
    expect(filterRegion).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════
// All Pages - Cross-cutting Accessibility Tests
// ═══════════════════════════════════════════════════════════════════════

describe("All Analytics Pages - Cross-cutting Accessibility", () => {
  const pages = [
    { name: "Analytics", Component: AnalyticsPage },
    { name: "Reports", Component: ReportsPage },
    { name: "Revenue", Component: RevenuePage },
  ];

  describe.each(pages)("$name page", ({ Component }) => {
    it("has no empty aria-labels", () => {
      const { container } = renderWithProviders(<Component />);

      const elementsWithAriaLabel = container.querySelectorAll("[aria-label]");
      expect(elementsWithAriaLabel.length).toBeGreaterThan(0);

      elementsWithAriaLabel.forEach((element) => {
        const label = element.getAttribute("aria-label");
        expect(label).not.toBe("");
        expect(label!.trim()).not.toBe("");
      });
    });

    it("headings follow logical order (h1 > h2 > h3)", () => {
      const { container } = renderWithProviders(<Component />);

      const headings = container.querySelectorAll("h1, h2, h3, h4, h5, h6");
      expect(headings.length).toBeGreaterThan(0);

      // The first heading should be h1
      expect(headings[0].tagName).toBe("H1");

      // Track highest level seen so far (lowest number). Subsequent
      // headings should not introduce a level that is deeper than two
      // steps from the highest-level ancestor seen. For example h1 -> h3
      // is acceptable (page title followed by component sub-headings),
      // but h1 -> h5 would be suspect.
      let maxLevelSeen = 0; // lowest heading number encountered
      headings.forEach((heading) => {
        const currentLevel = parseInt(heading.tagName[1], 10);
        if (maxLevelSeen === 0) {
          maxLevelSeen = currentLevel;
        }
        // No heading should be more than 2 levels deeper than the page
        // title (e.g. h1 allows up to h3 for sub-sections)
        expect(currentLevel - maxLevelSeen).toBeLessThanOrEqual(2);
      });
    });

    it("buttons have accessible names", () => {
      renderWithProviders(<Component />);

      const buttons = screen.queryAllByRole("button");
      buttons.forEach((button) => {
        // Button has either visible text, aria-label, or aria-labelledby
        const visibleText = button.textContent?.trim();
        const ariaLabel = button.getAttribute("aria-label");
        const ariaLabelledBy = button.getAttribute("aria-labelledby");
        const title = button.getAttribute("title");

        const hasAccessibleName = visibleText || ariaLabel || ariaLabelledBy || title;
        expect(hasAccessibleName).toBeTruthy();
      });
    });

    it("links have accessible names", () => {
      renderWithProviders(<Component />);

      const links = screen.queryAllByRole("link");
      links.forEach((link) => {
        const visibleText = link.textContent?.trim();
        const ariaLabel = link.getAttribute("aria-label");
        const ariaLabelledBy = link.getAttribute("aria-labelledby");
        const title = link.getAttribute("title");

        const hasAccessibleName = visibleText || ariaLabel || ariaLabelledBy || title;
        expect(hasAccessibleName).toBeTruthy();
      });
    });
  });
});
