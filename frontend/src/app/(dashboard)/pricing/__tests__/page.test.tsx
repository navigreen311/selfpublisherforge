import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PricingPage from "../page";

// ── Mocks ────────────────────────────────────────────────────────────────

// Mock the pricing hooks module
jest.mock("@/modules/pricing/hooks", () => ({
  usePricingRules: jest.fn(),
}));

// Import after mock so we can control return values
import { usePricingRules } from "@/modules/pricing/hooks";

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock recharts to avoid rendering issues in tests
jest.mock("recharts", () => {
  const OriginalModule = jest.requireActual("recharts");
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="recharts-responsive-container">{children}</div>
    ),
    LineChart: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="recharts-line-chart">{children}</div>
    ),
    BarChart: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="recharts-bar-chart">{children}</div>
    ),
    Line: () => <div data-testid="recharts-line" />,
    Bar: () => <div data-testid="recharts-bar" />,
    XAxis: () => <div data-testid="recharts-xaxis" />,
    YAxis: () => <div data-testid="recharts-yaxis" />,
    CartesianGrid: () => <div data-testid="recharts-grid" />,
    Tooltip: () => <div data-testid="recharts-tooltip" />,
    Legend: () => <div data-testid="recharts-legend" />,
    Cell: () => <div data-testid="recharts-cell" />,
  };
});

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

// ── Test Data Fixtures ──────────────────────────────────────────────────

const mockPricingRules = {
  items: [
    {
      id: "rule1",
      org_id: "org1",
      name: "Dynamic Pricing",
      description: "Automatically adjust prices based on sales",
      book_id: "book1",
      strategy: "dynamic",
      status: "active",
      book_format: "ebook",
      min_price: 2.99,
      max_price: 9.99,
      target_price: 4.99,
      parameters: {},
      is_auto_apply: true,
      last_applied_at: "2024-02-01T00:00:00Z",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-02-01T00:00:00Z",
    },
  ],
  total_count: 1,
  has_more: false,
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("PricingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── 1. Loading State ────────────────────────────────────────────────

  it("renders pricing dashboard with loading state", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Pricing Automation")).toBeInTheDocument();
    expect(
      screen.getByText("Optimize your book prices to maximize royalties and sales")
    ).toBeInTheDocument();
  });

  // ── 2. Success State ────────────────────────────────────────────────

  it("renders pricing dashboard with data", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Pricing Automation")).toBeInTheDocument();
    expect(screen.getByText("Price Simulator")).toBeInTheDocument();
  });

  // ── 3. Header Elements ──────────────────────────────────────────────

  it("renders header with title and simulator link", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Pricing Automation")).toBeInTheDocument();

    const simulatorLink = screen.getByRole("link", { name: /price simulator/i });
    expect(simulatorLink).toHaveAttribute("href", "/pricing/simulator");
  });

  // ── 4. Quick Stats Cards ────────────────────────────────────────────

  it("renders quick stats cards", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Active Rules")).toBeInTheDocument();
    expect(screen.getByText("Avg. Price")).toBeInTheDocument();
    expect(screen.getByText("Avg. Royalty Rate")).toBeInTheDocument();
    expect(screen.getByText("Next Price Change")).toBeInTheDocument();
  });

  // ── 5. Tabs Navigation ──────────────────────────────────────────────

  it("renders tabs for different sections", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByRole("tab", { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /strategies/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /price history/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /royalty analysis/i })).toBeInTheDocument();
  });

  // ── 6. Strategy Cards Section ───────────────────────────────────────

  it("renders pricing strategies section", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Pricing Strategies")).toBeInTheDocument();
  });

  // ── 7. Recent Price Changes ─────────────────────────────────────────

  it("renders recent price changes section", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Recent Price Changes")).toBeInTheDocument();
  });

  // ── 8. Empty State ──────────────────────────────────────────────────

  it("handles empty pricing rules gracefully", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: { items: [], total_count: 0, has_more: false },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Pricing Automation")).toBeInTheDocument();
    expect(screen.getByText("Pricing Strategies")).toBeInTheDocument();
  });

  // ── 9. Dashboard Components Mount ───────────────────────────────────

  it("mounts without crashing", () => {
    (usePricingRules as jest.Mock).mockReturnValue({
      data: mockPricingRules,
      isLoading: false,
      error: null,
    });

    const { container } = renderWithProviders(<PricingPage />);
    expect(container).toBeInTheDocument();
  });
});
