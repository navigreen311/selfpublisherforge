import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/market",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock the market hooks
const mockMutate = jest.fn();
const mockUseCategories = jest.fn();
const mockUseCategoryAnalysis = jest.fn();
const mockUseNicheAnalysis = jest.fn();
const mockUseMarketTrends = jest.fn();
const mockUseMarketSnapshots = jest.fn();

jest.mock("@/modules/market/hooks", () => ({
  useCategories: (...args: unknown[]) => mockUseCategories(...args),
  useCategoryAnalysis: (...args: unknown[]) => mockUseCategoryAnalysis(...args),
  useNicheAnalysis: (...args: unknown[]) => mockUseNicheAnalysis(...args),
  useMarketTrends: (...args: unknown[]) => mockUseMarketTrends(...args),
  useMarketSnapshots: (...args: unknown[]) => mockUseMarketSnapshots(...args),
  useTrackCompetitor: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
  useAIMarketSummary: () => ({ data: undefined, isLoading: false, isError: false, error: null, refetch: jest.fn() }),
}));

// Mock market components to simple stubs
jest.mock("@/modules/market/components", () => ({
  CategoryTree: ({
    categories,
    onSelect,
    selectedId,
  }: {
    categories: unknown[];
    onSelect: (cat: unknown) => void;
    selectedId?: string;
  }) => (
    <div data-testid="category-tree">
      {(categories as Array<{ id: string; name: string }>).map((c) => (
        <button key={c.id} onClick={() => onSelect(c)} data-testid={`cat-${c.id}`}>
          {c.name}
        </button>
      ))}
    </div>
  ),
  NicheScoreCard: ({ analysis }: { analysis: { niche: string; opportunity_score: number } }) => (
    <div data-testid="niche-score-card">
      <span>Niche: {analysis.niche}</span>
      <span>Opportunity: {analysis.opportunity_score}</span>
    </div>
  ),
  TrendChart: ({ trend }: { trend: { label: string } }) => (
    <div data-testid="trend-chart">{trend.label}</div>
  ),
}));

// Mock Skeleton
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={`animate-pulse ${className || ""}`} />
  ),
}));

// Import the component under test (AFTER mocks)
import MarketDashboardPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Fixture data ─────────────────────────────────────────────────────────

const mockCategories = [
  { id: "cat-1", name: "Fiction", parent_id: null, children: [], book_count: 1200 },
  { id: "cat-2", name: "Non-Fiction", parent_id: null, children: [], book_count: 800 },
];

const mockCategoryAnalysisData = {
  category_id: "cat-1",
  category_name: "Fiction",
  book_count: 1200,
  avg_bsr: 45000,
  median_bsr: 38000,
  avg_price: 12.99,
  avg_reviews: 142,
  avg_rating: 4.2,
  competition_score: 65,
  bsr_distribution: { "0-10k": 100, "10k-50k": 500, "50k-100k": 600 },
  top_books: [
    {
      asin: "B00TEST1",
      title: "Top Fiction Book",
      author: "Author A",
      bsr: 1200,
      price: 9.99,
      reviews_count: 5000,
      rating: 4.5,
      image_url: null,
    },
  ],
};

const mockNicheData = {
  niche: "self-help for millennials",
  demand_score: 82,
  supply_score: 45,
  opportunity_score: 78,
  top_competitors: [],
  gap_analysis: [],
  avg_monthly_revenue: 5000,
  avg_bsr: 30000,
  recommendation: "Strong opportunity",
  analyzed_at: "2025-06-01T00:00:00Z",
};

const mockTrendsData = {
  trends: [
    {
      label: "Fiction Trend",
      category_id: "cat-1",
      keyword: null,
      direction: "up" as const,
      data_points: [{ date: "2025-01-01", value: 100 }],
      change_pct: 12.5,
    },
  ],
  period_start: "2025-01-01",
  period_end: "2025-01-31",
};

const mockSnapshots = [
  {
    id: "snap-1",
    category_id: "cat-1",
    category_name: "Fiction",
    snapshot_date: "2025-06-01T00:00:00Z",
    avg_bsr: 45000,
    avg_price: 12.99,
    book_count: 1200,
    avg_reviews: 142,
    competition_score: 65,
  },
];

// ── Default mock return values ───────────────────────────────────────────

function setDefaultMocks(overrides?: {
  categories?: unknown;
  catsLoading?: boolean;
  categoryAnalysis?: unknown;
  nicheAnalysis?: unknown;
  trends?: unknown;
  snapshots?: unknown;
}) {
  mockUseCategories.mockReturnValue({
    data: overrides?.categories ?? mockCategories,
    isLoading: overrides?.catsLoading ?? false,
  });

  mockUseCategoryAnalysis.mockReturnValue({
    data: overrides?.categoryAnalysis ?? undefined,
  });

  mockUseNicheAnalysis.mockReturnValue({
    mutate: mockMutate,
    data: overrides?.nicheAnalysis ?? undefined,
    isPending: false,
    isError: false,
  });

  mockUseMarketTrends.mockReturnValue({
    data: overrides?.trends ?? undefined,
  });

  mockUseMarketSnapshots.mockReturnValue({
    data: overrides?.snapshots ?? [],
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("MarketDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Renders market intelligence page
  it("renders the market intelligence page with heading and description", () => {
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByText("Market Intelligence")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Analyze niches, explore categories, and discover market opportunities"
      )
    ).toBeInTheDocument();
  });

  // 2. Search/keyword input works
  it("renders search input and allows typing a niche query", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    const input = screen.getByPlaceholderText(
      "Enter a niche to analyze (e.g., 'self-help for millennials')..."
    );
    expect(input).toBeInTheDocument();

    await user.type(input, "romance novels");
    expect(input).toHaveValue("romance novels");
  });

  it("triggers niche analysis when Analyze Niche button is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    const input = screen.getByPlaceholderText(
      "Enter a niche to analyze (e.g., 'self-help for millennials')..."
    );
    await user.type(input, "romance novels");

    const analyzeButton = screen.getByRole("button", { name: /analyze niche/i });
    await user.click(analyzeButton);

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({ niche: "romance novels" })
    );
  });

  it("triggers niche analysis on Enter key press", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    const input = screen.getByPlaceholderText(
      "Enter a niche to analyze (e.g., 'self-help for millennials')..."
    );
    await user.type(input, "romance novels{Enter}");

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({ niche: "romance novels" })
    );
  });

  it("disables Analyze Niche button when input is empty", () => {
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    const analyzeButton = screen.getByRole("button", { name: /analyze niche/i });
    expect(analyzeButton).toBeDisabled();
  });

  // 3. Niche score cards display
  it("displays NicheScoreCard when niche analysis data is available", () => {
    setDefaultMocks({ nicheAnalysis: mockNicheData });
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByTestId("niche-score-card")).toBeInTheDocument();
    expect(screen.getByText(/self-help for millennials/)).toBeInTheDocument();
  });

  // 4. Competitor analysis section (category analysis with top books)
  it("renders category analysis with top books when a category is selected", () => {
    setDefaultMocks({ categoryAnalysis: mockCategoryAnalysisData });
    renderWithProviders(<MarketDashboardPage />);

    // "Fiction" appears both in category tree and in analysis heading
    const fictionElements = screen.getAllByText("Fiction");
    expect(fictionElements.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Top Books")).toBeInTheDocument();
    expect(screen.getByText("Top Fiction Book")).toBeInTheDocument();
    expect(screen.getByText("BSR Distribution")).toBeInTheDocument();
  });

  it("shows placeholder text when no category is selected", () => {
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    expect(
      screen.getByText("Select a category from the tree to view analysis")
    ).toBeInTheDocument();
  });

  // 5. Trend charts render
  it("renders trend charts when trends data is available", () => {
    setDefaultMocks({ trends: mockTrendsData });
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByText("Market Trends")).toBeInTheDocument();
    expect(screen.getByTestId("trend-chart")).toBeInTheDocument();
    expect(screen.getByText("Fiction Trend")).toBeInTheDocument();
  });

  it("renders snapshots section when snapshot data is available", () => {
    setDefaultMocks({ snapshots: mockSnapshots });
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByText("Recent Snapshots")).toBeInTheDocument();
    expect(screen.getByText(/1 daily snapshots available/)).toBeInTheDocument();
  });

  // 6. Loading/error states
  it("renders loading skeletons when categories are loading", () => {
    setDefaultMocks({ catsLoading: true });
    renderWithProviders(<MarketDashboardPage />);

    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders error state when niche analysis fails", () => {
    mockUseCategories.mockReturnValue({ data: mockCategories, isLoading: false });
    mockUseCategoryAnalysis.mockReturnValue({ data: undefined });
    mockUseNicheAnalysis.mockReturnValue({
      mutate: mockMutate,
      data: undefined,
      isPending: false,
      isError: true,
    });
    mockUseMarketTrends.mockReturnValue({ data: undefined });
    mockUseMarketSnapshots.mockReturnValue({ data: [] });

    renderWithProviders(<MarketDashboardPage />);

    expect(
      screen.getByText("Failed to analyze niche. Please try again.")
    ).toBeInTheDocument();
  });

  it("shows Analyzing... text while niche analysis is pending", () => {
    mockUseCategories.mockReturnValue({ data: mockCategories, isLoading: false });
    mockUseCategoryAnalysis.mockReturnValue({ data: undefined });
    mockUseNicheAnalysis.mockReturnValue({
      mutate: mockMutate,
      data: undefined,
      isPending: true,
      isError: false,
    });
    mockUseMarketTrends.mockReturnValue({ data: undefined });
    mockUseMarketSnapshots.mockReturnValue({ data: [] });

    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByText("Analyzing...")).toBeInTheDocument();
  });

  it("renders category tree with category nodes", () => {
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByTestId("category-tree")).toBeInTheDocument();
    expect(screen.getByText("Fiction")).toBeInTheDocument();
    expect(screen.getByText("Non-Fiction")).toBeInTheDocument();
  });

  it("does not show trends section when no trend data exists", () => {
    setDefaultMocks({ trends: { trends: [], period_start: "", period_end: "" } });
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.queryByText("Market Trends")).not.toBeInTheDocument();
  });

  it("does not mutate when search input is whitespace only", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<MarketDashboardPage />);

    const input = screen.getByPlaceholderText(
      "Enter a niche to analyze (e.g., 'self-help for millennials')..."
    );
    await user.type(input, "   ");

    const analyzeButton = screen.getByRole("button", { name: /analyz/i });
    expect(analyzeButton).toBeDisabled();
  });

  it("renders stat cards when category analysis data is present", () => {
    setDefaultMocks({ categoryAnalysis: mockCategoryAnalysisData });
    renderWithProviders(<MarketDashboardPage />);

    expect(screen.getByText("Books")).toBeInTheDocument();
    expect(screen.getByText("1,200")).toBeInTheDocument();
    expect(screen.getByText("Avg BSR")).toBeInTheDocument();
    expect(screen.getByText("Avg Price")).toBeInTheDocument();
    expect(screen.getByText("$12.99")).toBeInTheDocument();
    expect(screen.getByText("Competition")).toBeInTheDocument();
    expect(screen.getByText("65/100")).toBeInTheDocument();
  });
});
