import React from "react";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { render } from "@/test-utils";

// ── Mocks ────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/market",
  useSearchParams: () => new URLSearchParams(),
}));

const mockAnalyzeNiche = jest.fn();
const mockTrackCompetitor = jest.fn();
const mockUseNicheAnalysis = jest.fn();

jest.mock("@/modules/market/hooks", () => ({
  useNicheAnalysis: () => mockUseNicheAnalysis(),
  useTrackCompetitor: () => ({
    mutate: mockTrackCompetitor,
    mutateAsync: jest.fn().mockResolvedValue({}),
    isPending: false,
    isError: false,
    error: null,
    reset: jest.fn(),
  }),
}));

// The four result panels and the three sibling tabs are separately covered;
// stub them so this suite is about the page's own search-and-dispatch logic.
jest.mock("@/components/market-research/NicheScorecard", () => ({
  NicheScorecard: ({ analysis }: { analysis: { niche: string } }) => (
    <div data-testid="niche-scorecard">{analysis.niche}</div>
  ),
}));
jest.mock("@/components/market-research/CompetitorBooksTable", () => ({
  CompetitorBooksTable: ({ books }: { books: unknown[] }) => (
    <div data-testid="competitor-books">{books?.length ?? 0} competitors</div>
  ),
}));
jest.mock("@/components/market-research/MarketCharts", () => ({
  MarketCharts: () => <div data-testid="market-charts" />,
}));
jest.mock("@/components/market-research/AIMarketSummary", () => ({
  AIMarketSummary: () => <div data-testid="ai-market-summary" />,
}));
jest.mock("@/components/market-research/KeywordResearch", () => ({
  KeywordResearch: () => <div data-testid="keyword-research" />,
}));
jest.mock("@/components/market-research/CategoryExplorer", () => ({
  CategoryExplorer: () => <div data-testid="category-explorer" />,
}));
jest.mock("@/components/market-research/TrendTracker", () => ({
  TrendTracker: () => <div data-testid="trend-tracker" />,
}));

// Import the component under test (AFTER mocks)
import MarketResearchPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

const PLACEHOLDER = "Enter a niche topic or keyword (e.g., 'keto diet for beginners')";

const analysis = {
  niche: "Cozy Mystery",
  opportunity_score: 78,
  top_competitors: [{ asin: "B001" }, { asin: "B002" }],
  charts_data: {},
};

function idle() {
  return {
    mutate: mockAnalyzeNiche,
    data: undefined,
    isPending: false,
    isError: false,
    error: null,
    reset: jest.fn(),
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockUseNicheAnalysis.mockReturnValue(idle());
});

// ── Tests ────────────────────────────────────────────────────────────────

describe("MarketResearchPage", () => {
  describe("page shell", () => {
    it("renders the heading and description", () => {
      render(<MarketResearchPage />);

      expect(screen.getByRole("heading", { name: "Market Research" })).toBeInTheDocument();
      expect(
        screen.getByText("Analyze market trends, competitors, and find profitable niches.")
      ).toBeInTheDocument();
    });

    it("renders the four research tabs, opening on the niche analyzer", () => {
      render(<MarketResearchPage />);

      for (const tab of [
        "Niche Analyzer",
        "Keyword Research",
        "Category Explorer",
        "Trends",
      ]) {
        expect(screen.getByRole("tab", { name: tab })).toBeInTheDocument();
      }
      expect(screen.getByRole("tab", { name: "Niche Analyzer" })).toHaveAttribute(
        "aria-selected",
        "true"
      );
    });
  });

  describe("niche search", () => {
    it("disables Analyze Niche until something is typed", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      const button = screen.getByRole("button", { name: "Analyze Niche" });
      expect(button).toBeDisabled();

      await user.type(screen.getByPlaceholderText(PLACEHOLDER), "cozy mystery");
      expect(button).toBeEnabled();
    });

    it("analyses the typed niche with the default filters", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.type(screen.getByPlaceholderText(PLACEHOLDER), "cozy mystery");
      await user.click(screen.getByRole("button", { name: "Analyze Niche" }));

      expect(mockAnalyzeNiche).toHaveBeenCalledWith({
        niche: "cozy mystery",
        marketplace: "US",
        format: undefined,
        date_range: "90d",
      });
    });

    it("analyses on Enter as well as on the button", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.type(screen.getByPlaceholderText(PLACEHOLDER), "dark romance{Enter}");

      expect(mockAnalyzeNiche).toHaveBeenCalledWith(
        expect.objectContaining({ niche: "dark romance" })
      );
    });

    it("ignores a whitespace-only query", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.type(screen.getByPlaceholderText(PLACEHOLDER), "   {Enter}");

      expect(mockAnalyzeNiche).not.toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "Analyze Niche" })).toBeDisabled();
    });

    it("sends the chosen marketplace, format and date range", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.selectOptions(screen.getByLabelText("Marketplace"), "UK");
      await user.selectOptions(screen.getByLabelText("Format"), "paperback");
      await user.selectOptions(screen.getByLabelText("Date Range"), "30d");
      await user.type(screen.getByPlaceholderText(PLACEHOLDER), "keto");
      await user.click(screen.getByRole("button", { name: "Analyze Niche" }));

      expect(mockAnalyzeNiche).toHaveBeenCalledWith({
        niche: "keto",
        marketplace: "UK",
        format: "paperback",
        date_range: "30d",
      });
    });

    it("analyses a suggested niche in one click and fills the input", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.click(screen.getByRole("button", { name: "Cozy Mystery" }));

      expect(mockAnalyzeNiche).toHaveBeenCalledWith(
        expect.objectContaining({ niche: "Cozy Mystery" })
      );
      expect(screen.getByPlaceholderText(PLACEHOLDER)).toHaveValue("Cozy Mystery");
    });
  });

  describe("analysis states", () => {
    it("shows Analyzing... while the mutation is pending", () => {
      mockUseNicheAnalysis.mockReturnValue({ ...idle(), isPending: true });
      render(<MarketResearchPage />);

      expect(screen.getByRole("button", { name: "Analyzing..." })).toBeInTheDocument();
    });

    it("announces a failed analysis", () => {
      mockUseNicheAnalysis.mockReturnValue({
        ...idle(),
        isError: true,
        error: new Error("boom"),
      });
      render(<MarketResearchPage />);

      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to analyze niche. Please try again."
      );
    });

    it("renders the four result panels once data arrives", () => {
      mockUseNicheAnalysis.mockReturnValue({ ...idle(), data: analysis });
      render(<MarketResearchPage />);

      expect(screen.getByTestId("niche-scorecard")).toHaveTextContent("Cozy Mystery");
      expect(screen.getByTestId("competitor-books")).toHaveTextContent("2 competitors");
      expect(screen.getByTestId("market-charts")).toBeInTheDocument();
      expect(screen.getByTestId("ai-market-summary")).toBeInTheDocument();
    });

    it("renders no result panels before an analysis runs", () => {
      render(<MarketResearchPage />);

      expect(screen.queryByTestId("niche-scorecard")).not.toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });

  describe("sibling tabs", () => {
    it("swaps in the keyword research panel", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.click(screen.getByRole("tab", { name: "Keyword Research" }));

      expect(await screen.findByTestId("keyword-research")).toBeInTheDocument();
    });

    it("swaps in the category explorer", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.click(screen.getByRole("tab", { name: "Category Explorer" }));

      expect(await screen.findByTestId("category-explorer")).toBeInTheDocument();
    });

    it("swaps in the trend tracker", async () => {
      const user = userEvent.setup();
      render(<MarketResearchPage />);

      await user.click(screen.getByRole("tab", { name: "Trends" }));

      expect(await screen.findByTestId("trend-tracker")).toBeInTheDocument();
    });
  });
});
