import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/competitors",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock the competitor hooks
const mockMutate = jest.fn();
const mockUseCompetitorAnalyses = jest.fn();
const mockUseCompetitorAlerts = jest.fn();
const mockUseGapAnalysis = jest.fn();
const mockUseAnalyzeCompetitor = jest.fn();

jest.mock("@/modules/competitors/hooks", () => ({
  useCompetitorAnalyses: (...args: unknown[]) => mockUseCompetitorAnalyses(...args),
  useCompetitorAlerts: (...args: unknown[]) => mockUseCompetitorAlerts(...args),
  useGapAnalysis: (...args: unknown[]) => mockUseGapAnalysis(...args),
  useAnalyzeCompetitor: (...args: unknown[]) => mockUseAnalyzeCompetitor(...args),
}));

// Mock competitor components to simple stubs
jest.mock("@/modules/competitors/components/CompetitorTable", () => ({
  CompetitorTable: ({
    analyses,
    isLoading,
  }: {
    analyses: Array<{ id: string; book?: { title: string } }>;
    isLoading?: boolean;
  }) => (
    <div data-testid="competitor-table">
      {isLoading ? (
        <div>Loading...</div>
      ) : analyses.length === 0 ? (
        <div>No competitor analyses yet</div>
      ) : (
        analyses.map((a) => (
          <div key={a.id} data-testid={`analysis-${a.id}`}>
            {a.book?.title ?? "Unknown"}
          </div>
        ))
      )}
    </div>
  ),
}));

jest.mock("@/modules/competitors/components/GapAnalysis", () => ({
  GapAnalysisComponent: ({ analysis }: { analysis: { niche: string } }) => (
    <div data-testid="gap-analysis">Gap Analysis: {analysis.niche}</div>
  ),
}));

jest.mock("@/modules/competitors/components/OpportunityCard", () => ({
  OpportunityCard: ({ opportunity }: { opportunity: { id: string } }) => (
    <div data-testid="opportunity-card">Opportunity: {opportunity.id}</div>
  ),
}));

jest.mock("@/modules/competitors/components/CompetitorCompare", () => ({
  CompetitorCompare: ({ analyses }: { analyses: unknown[] }) => (
    <div data-testid="competitor-compare">Comparing {analyses.length} competitors</div>
  ),
}));

// Mock UI components
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={`animate-pulse ${className || ""}`} />
  ),
}));

jest.mock("@/components/ui/badge", () => ({
  Badge: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <span data-testid="badge" className={className}>
      {children}
    </span>
  ),
}));

jest.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children, value, onValueChange }: { children: React.ReactNode; value: string; onValueChange: (v: string) => void }) => (
    <div data-testid="tabs">{children}</div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <button data-testid={`tab-trigger-${value}`}>{children}</button>
  ),
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid={`tab-content-${value}`}>{children}</div>
  ),
}));

jest.mock("@/components/ui/alert", () => ({
  Alert: ({ children }: { children: React.ReactNode }) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Import the component under test (AFTER mocks)
import CompetitorsPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

// ── Fixture data ─────────────────────────────────────────────────────────

const mockAnalyses = [
  {
    id: "analysis-1",
    org_id: "org-1",
    book_id: "book-1",
    status: "completed" as const,
    overall_score: 75,
    sentiment_score: 0.8,
    weakness_count: 5,
    strength_count: 10,
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
    book: {
      id: "book-1",
      asin: "B00TEST1",
      title: "Competitor Book 1",
      author: "Author A",
      bsr: 1200,
      price: 9.99,
      rating: 4.5,
      review_count: 1000,
    },
    weaknesses: [],
  },
  {
    id: "analysis-2",
    org_id: "org-1",
    book_id: "book-2",
    status: "completed" as const,
    overall_score: 60,
    sentiment_score: 0.65,
    weakness_count: 8,
    strength_count: 7,
    created_at: "2025-06-02T00:00:00Z",
    updated_at: "2025-06-02T00:00:00Z",
    book: {
      id: "book-2",
      asin: "B00TEST2",
      title: "Competitor Book 2",
      author: "Author B",
      bsr: 5000,
      price: 12.99,
      rating: 4.2,
      review_count: 500,
    },
    weaknesses: [],
  },
];

const mockAlerts = [
  {
    id: "alert-1",
    org_id: "org-1",
    book_id: "book-1",
    alert_type: "price_change" as const,
    severity: "warning" as const,
    title: "Price dropped on Competitor Book 1",
    description: "Price changed from $12.99 to $9.99",
    data: {},
    read: false,
    dismissed: false,
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

const mockGapAnalysis = {
  id: "gap-1",
  org_id: "org-1",
  niche: "productivity for remote workers",
  books_analyzed: 15,
  cover_gaps: [],
  title_gaps: [],
  content_gaps: [],
  summary: "Analysis complete",
  recommendations: [],
  status: "completed",
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-01T00:00:00Z",
};

// ── Default mock return values ───────────────────────────────────────────

function setDefaultMocks(overrides?: {
  analyses?: unknown;
  analysesLoading?: boolean;
  alerts?: unknown;
  alertsLoading?: boolean;
}) {
  mockUseCompetitorAnalyses.mockReturnValue({
    data: overrides?.analyses ?? [],
    isLoading: overrides?.analysesLoading ?? false,
  });

  mockUseCompetitorAlerts.mockReturnValue({
    data: overrides?.alerts ?? [],
    isLoading: overrides?.alertsLoading ?? false,
  });

  mockUseGapAnalysis.mockReturnValue({
    mutate: mockMutate,
    data: undefined,
    isPending: false,
    isError: false,
  });

  mockUseAnalyzeCompetitor.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
    isError: false,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("CompetitorsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the competitor analysis page with heading and description", () => {
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByText("Competitor Analysis")).toBeInTheDocument();
    expect(
      screen.getByText("Analyze competitors, discover gaps, and identify opportunities")
    ).toBeInTheDocument();
  });

  it("renders tabs for analyses, gaps, compare, and alerts", () => {
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByTestId("tab-trigger-analyses")).toBeInTheDocument();
    expect(screen.getByTestId("tab-trigger-gaps")).toBeInTheDocument();
    expect(screen.getByTestId("tab-trigger-compare")).toBeInTheDocument();
    expect(screen.getByTestId("tab-trigger-alerts")).toBeInTheDocument();
  });

  it("displays competitor table when analyses are available", () => {
    setDefaultMocks({ analyses: mockAnalyses });
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByTestId("competitor-table")).toBeInTheDocument();
    expect(screen.getByTestId("analysis-analysis-1")).toBeInTheDocument();
    expect(screen.getByTestId("analysis-analysis-2")).toBeInTheDocument();
  });

  it("shows loading skeletons when analyses are loading", () => {
    setDefaultMocks({ analysesLoading: true });
    renderWithProviders(<CompetitorsPage />);

    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it("displays empty state when no analyses exist", () => {
    setDefaultMocks({ analyses: [] });
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByText("No competitor analyses yet")).toBeInTheDocument();
  });

  it("renders gap analysis input and button", () => {
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    const input = screen.getByPlaceholderText(
      /Enter a niche to analyze gaps/i
    );
    expect(input).toBeInTheDocument();

    const button = screen.getByRole("button", { name: /Analyze Gaps/i });
    expect(button).toBeInTheDocument();
  });

  it("triggers gap analysis when button is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    const input = screen.getByPlaceholderText(
      /Enter a niche to analyze gaps/i
    );
    await user.type(input, "productivity for remote workers");

    const button = screen.getByRole("button", { name: /Analyze Gaps/i });
    await user.click(button);

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        request: expect.objectContaining({
          niche: "productivity for remote workers",
        }),
      }),
      expect.any(Object)
    );
  });

  it("triggers gap analysis on Enter key press", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    const input = screen.getByPlaceholderText(
      /Enter a niche to analyze gaps/i
    );
    await user.type(input, "productivity for remote workers{Enter}");

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        request: expect.objectContaining({
          niche: "productivity for remote workers",
        }),
      }),
      expect.any(Object)
    );
  });

  it("disables gap analysis button when input is empty", () => {
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    const button = screen.getByRole("button", { name: /Analyze Gaps/i });
    expect(button).toBeDisabled();
  });

  it("displays unread alert count badge", () => {
    setDefaultMocks({ alerts: mockAlerts });
    renderWithProviders(<CompetitorsPage />);

    // Badge should show unread count
    const badges = screen.getAllByTestId("badge");
    const unreadBadge = badges.find((b) => b.textContent === "1");
    expect(unreadBadge).toBeInTheDocument();
  });

  it("renders alerts when available", () => {
    setDefaultMocks({ alerts: mockAlerts });
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByText("Price dropped on Competitor Book 1")).toBeInTheDocument();
    expect(screen.getByText("Price changed from $12.99 to $9.99")).toBeInTheDocument();
  });

  it("shows empty state when no alerts exist", () => {
    setDefaultMocks({ alerts: [] });
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByText("No competitor alerts yet")).toBeInTheDocument();
  });

  it("renders compare component in compare tab", () => {
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByTestId("competitor-compare")).toBeInTheDocument();
  });

  it("does not trigger gap analysis when input is whitespace only", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<CompetitorsPage />);

    const input = screen.getByPlaceholderText(
      /Enter a niche to analyze gaps/i
    );
    await user.type(input, "   ");

    const button = screen.getByRole("button", { name: /Analyze Gaps/i });
    expect(button).toBeDisabled();
  });
});
