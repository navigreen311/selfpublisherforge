import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import DashboardPage from "../dashboard/page";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockRefetch = jest.fn();

jest.mock("@/modules/analytics/hooks", () => ({
  useDashboard: jest.fn(),
}));

import { useDashboard } from "@/modules/analytics/hooks";

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-book-open" {...props} />
  ),
  DollarSign: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-dollar-sign" {...props} />
  ),
  TrendingUp: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-trending-up" {...props} />
  ),
  BarChart3: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-bar-chart" {...props} />
  ),
  Plus: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-plus" {...props} />
  ),
  ArrowRight: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-arrow-right" {...props} />
  ),
  Bot: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-bot" {...props} />
  ),
  RefreshCw: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-refresh" {...props} />
  ),
  AlertCircle: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-alert-circle" {...props} />
  ),
}));

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

const mockRecentRoyalties = [
  {
    id: "r1",
    org_id: "org1",
    book_id: "b1",
    platform: "kdp",
    marketplace: "US",
    title: "My First Book",
    asin: "B00TEST1",
    isbn: null,
    format_type: "ebook",
    units_sold: 100,
    units_refunded: 2,
    net_units: 98,
    list_price: 9.99,
    royalty_rate: 0.7,
    gross_revenue: 999.0,
    net_revenue: 685.3,
    currency: "USD",
    period_start: "2025-01-01",
    period_end: "2025-01-31",
    import_batch_id: "batch1",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "r2",
    org_id: "org1",
    book_id: "b2",
    platform: "ingram_spark",
    marketplace: "US",
    title: "My Second Book",
    asin: null,
    isbn: "978-0-TEST",
    format_type: "paperback",
    units_sold: 50,
    units_refunded: 0,
    net_units: 50,
    list_price: 14.99,
    royalty_rate: 0.55,
    gross_revenue: 749.5,
    net_revenue: 412.23,
    currency: "USD",
    period_start: "2025-01-01",
    period_end: "2025-01-31",
    import_batch_id: "batch1",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
  },
];

const mockTopBooks = [
  {
    id: 1,
    title: "My First Book",
    format_type: "ebook",
    status: "published",
    revenue: 685.3,
    units: 98,
  },
  {
    id: 2,
    title: "My Second Book",
    format_type: "paperback",
    status: "active",
    revenue: 412.23,
    units: 50,
  },
  {
    id: 3,
    title: "Draft Novel",
    format_type: "ebook",
    status: "draft",
    revenue: 0,
    units: 0,
  },
];

const fullDashboardData = {
  kpis: mockKpis,
  revenue_chart: [],
  top_books: mockTopBooks,
  platform_breakdown: { kdp: 685.3, ingram_spark: 412.23 },
  recent_royalties: mockRecentRoyalties,
  period_start: "2025-01-01",
  period_end: "2025-01-31",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("DashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRefetch.mockResolvedValue({});
  });

  // 1. Renders dashboard with stats cards
  it("renders dashboard with stats cards", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$12,450.00")).toBeInTheDocument();
    expect(screen.getByText("Units Sold")).toBeInTheDocument();
    expect(screen.getByText("1,230")).toBeInTheDocument();
    expect(screen.getByText("Total Books")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("Avg Revenue")).toBeInTheDocument();
    expect(screen.getByText("$830.00")).toBeInTheDocument();
  });

  // 2. Shows loading skeleton while data loads
  it("shows loading skeleton while data loads", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    // The skeleton renders the Dashboard heading
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Welcome back! Here is an overview of your publishing activity."
      )
    ).toBeInTheDocument();

    // The skeleton body is placeholder blocks; Quick Actions arrives with data.
    expect(screen.queryByText("Quick Actions")).not.toBeInTheDocument();

    // The skeleton keeps the header CTA, which reads "+ New Project".
    expect(screen.getByText("+ New Project")).toBeInTheDocument();
  });

  // 3. Displays recent projects (top books)
  it("displays recent projects (top books)", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText("Top Performing Books")).toBeInTheDocument();
    expect(screen.getByText("My First Book")).toBeInTheDocument();
    expect(screen.getByText("My Second Book")).toBeInTheDocument();
    expect(screen.getByText("Draft Novel")).toBeInTheDocument();

    // Status badges
    expect(screen.getByText("published")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("draft")).toBeInTheDocument();
  });

  // 4. Displays quick action cards
  it("displays quick action cards", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText("Quick Actions")).toBeInTheDocument();
    expect(screen.getByText("View Projects")).toBeInTheDocument();
    expect(screen.getByText("AI Agents")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();

    // The header CTA reads "+ New Project"; the quick-action tile "New Project".
    expect(screen.getByText("+ New Project")).toBeInTheDocument();
    expect(screen.getByText("New Project")).toBeInTheDocument();
  });

  // 5. Navigation links work
  it("navigation links have correct hrefs", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    // Quick action links
    const newProjectLinks = screen.getAllByRole("link", {
      name: /new project/i,
    });
    expect(
      newProjectLinks.some(
        (link) => link.getAttribute("href") === "/projects/new"
      )
    ).toBe(true);

    const viewProjectsLink = screen.getByRole("link", {
      name: /view projects/i,
    });
    expect(viewProjectsLink).toHaveAttribute("href", "/projects");

    const aiAgentsLink = screen.getByRole("link", { name: /ai agents/i });
    expect(aiAgentsLink).toHaveAttribute("href", "/agents");

    // View analytics link in Top Books section
    const analyticsLink = screen.getByRole("link", {
      name: /view analytics/i,
    });
    expect(analyticsLink).toHaveAttribute("href", "/analytics");
  });

  // Additional: error state and retry
  it("renders error state and retry button calls refetch", async () => {
    const user = userEvent.setup();

    (useDashboard as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    expect(
      screen.getByText("Failed to load dashboard data")
    ).toBeInTheDocument();

    const retryButton = screen.getByRole("button", { name: /try again/i });
    await user.click(retryButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  // Additional: empty states
  it("renders empty state when no KPI data is available", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: {
        kpis: [],
        revenue_chart: [],
        top_books: [],
        platform_breakdown: {},
        recent_royalties: [],
        period_start: "2025-01-01",
        period_end: "2025-01-31",
      },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    // The empty KPI state is four zeroed stat cards, not a sentence.
    expect(screen.getByText("Active Projects")).toBeInTheDocument();
    expect(screen.getByText("Books Published")).toBeInTheDocument();
  });

  it("renders empty state when no recent activity exists", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: {
        kpis: mockKpis,
        revenue_chart: [],
        top_books: [],
        platform_breakdown: {},
        recent_royalties: [],
        period_start: "2025-01-01",
        period_end: "2025-01-31",
      },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    expect(
      screen.getByText(
        "No recent activity yet. Create your first project to get started!"
      )
    ).toBeInTheDocument();
  });

  it("renders recent activity from royalty records", () => {
    (useDashboard as jest.Mock).mockReturnValue({
      data: fullDashboardData,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(screen.getByText("Royalty: kdp")).toBeInTheDocument();
    expect(screen.getByText("Royalty: ingram spark")).toBeInTheDocument();
  });
});
