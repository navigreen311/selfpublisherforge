import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ── Mock the api module ──────────────────────────────────────────────────

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// Import hooks after mock
import {
  useCategories,
  useCategoryAnalysis,
  useKeywordResearch,
  useKeywordSuggestions,
  useNicheAnalysis,
  useCompetitors,
  useTrackCompetitor,
  useCompetitorDetail,
  useMarketTrends,
  useMarketSnapshots,
} from "../hooks";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function createWrapper() {
  const queryClient = createQueryClient();
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
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
  bsr_distribution: {},
  top_books: [],
};

const mockNicheResponse = {
  niche: "self-help",
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

const mockKeywordData = {
  keywords: [
    {
      keyword: "romance novels",
      search_volume: 50000,
      competition: 0.7,
      cpc: 1.5,
      trend: "up",
      trend_data: [100, 110, 120],
      relevance_score: 0.9,
    },
  ],
  marketplace: "US",
  generated_at: "2025-06-01T00:00:00Z",
};

const mockCompetitors = [
  {
    id: "comp-1",
    asin: "B00TEST1",
    title: "Competitor Book",
    author: "Author A",
    bsr: 5000,
    price: 14.99,
    reviews_count: 200,
    rating: 4.3,
    marketplace: "US",
    tracked_since: "2025-01-01T00:00:00Z",
  },
];

const mockTrendsResponse = {
  trends: [
    {
      label: "Fiction Trend",
      category_id: "cat-1",
      keyword: null,
      direction: "up",
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

// ── Tests ────────────────────────────────────────────────────────────────

describe("Market hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── useCategories ──────────────────────────────────────────────────

  describe("useCategories", () => {
    it("fetches categories successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCategories });

      const { result } = renderHook(() => useCategories(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockCategories);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/categories", {
        params: {},
      });
    });

    it("passes root_id param when provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCategories });

      const { result } = renderHook(() => useCategories("root-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/categories", {
        params: { root_id: "root-1" },
      });
    });

    it("handles fetch error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useCategories(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeTruthy();
    });
  });

  // ── useCategoryAnalysis ────────────────────────────────────────────

  describe("useCategoryAnalysis", () => {
    it("fetches category analysis when categoryId is provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCategoryAnalysisData });

      const { result } = renderHook(() => useCategoryAnalysis("cat-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockCategoryAnalysisData);
      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/market/categories/cat-1/analysis"
      );
    });

    it("does not fetch when categoryId is empty", () => {
      const { result } = renderHook(() => useCategoryAnalysis(""), {
        wrapper: createWrapper(),
      });

      expect(result.current.isFetching).toBe(false);
      expect(mockGet).not.toHaveBeenCalled();
    });
  });

  // ── useNicheAnalysis ───────────────────────────────────────────────

  describe("useNicheAnalysis", () => {
    it("performs niche analysis mutation successfully", async () => {
      mockPost.mockResolvedValueOnce({ data: mockNicheResponse });

      const { result } = renderHook(() => useNicheAnalysis(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ niche: "self-help" });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockNicheResponse);
      expect(mockPost).toHaveBeenCalledWith("/api/v1/market/analyze-niche", {
        niche: "self-help",
      });
    });

    it("passes category_id when provided", async () => {
      mockPost.mockResolvedValueOnce({ data: mockNicheResponse });

      const { result } = renderHook(() => useNicheAnalysis(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ niche: "self-help", category_id: "cat-1" });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith("/api/v1/market/analyze-niche", {
        niche: "self-help",
        category_id: "cat-1",
      });
    });

    it("handles niche analysis error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Analysis failed"));

      const { result } = renderHook(() => useNicheAnalysis(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ niche: "invalid" });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeTruthy();
    });
  });

  // ── useCompetitors ─────────────────────────────────────────────────

  describe("useCompetitors", () => {
    it("fetches competitors list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCompetitors });

      const { result } = renderHook(() => useCompetitors(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockCompetitors);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/competitors", {
        params: { marketplace: "US" },
      });
    });

    it("passes custom marketplace param", async () => {
      mockGet.mockResolvedValueOnce({ data: [] });

      const { result } = renderHook(() => useCompetitors("UK"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/competitors", {
        params: { marketplace: "UK" },
      });
    });

    it("handles competitors fetch error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useCompetitors(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  // ── useKeywordResearch ─────────────────────────────────────────────

  describe("useKeywordResearch", () => {
    it("performs keyword research mutation successfully", async () => {
      mockPost.mockResolvedValueOnce({ data: mockKeywordData });

      const { result } = renderHook(() => useKeywordResearch(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ keywords: ["romance novels"] });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockKeywordData);
      expect(mockPost).toHaveBeenCalledWith("/api/v1/market/keywords/research", {
        keywords: ["romance novels"],
      });
    });

    it("handles keyword research error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Research failed"));

      const { result } = renderHook(() => useKeywordResearch(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ keywords: ["test"] });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  // ── useMarketTrends ────────────────────────────────────────────────

  describe("useMarketTrends", () => {
    it("fetches market trends successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockTrendsResponse });

      const { result } = renderHook(() => useMarketTrends("cat-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockTrendsResponse);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/trends", {
        params: expect.objectContaining({ category_id: "cat-1", days: 30 }),
      });
    });

    it("passes keyword parameter when provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockTrendsResponse });

      const { result } = renderHook(
        () => useMarketTrends(undefined, "romance", 60),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/trends", {
        params: expect.objectContaining({ keyword: "romance", days: 60 }),
      });
    });
  });

  // ── useMarketSnapshots ─────────────────────────────────────────────

  describe("useMarketSnapshots", () => {
    it("fetches market snapshots successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockSnapshots });

      const { result } = renderHook(() => useMarketSnapshots("cat-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockSnapshots);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/snapshots", {
        params: expect.objectContaining({ category_id: "cat-1", limit: 30 }),
      });
    });

    it("fetches snapshots without category filter", async () => {
      mockGet.mockResolvedValueOnce({ data: [] });

      const { result } = renderHook(() => useMarketSnapshots(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/market/snapshots", {
        params: { limit: 30 },
      });
    });
  });

  // ── useKeywordSuggestions ──────────────────────────────────────────

  describe("useKeywordSuggestions", () => {
    it("fetches keyword suggestions when genre is provided", async () => {
      mockGet.mockResolvedValueOnce({
        data: [
          {
            keyword: "romantic comedy",
            search_volume: 30000,
            competition: 0.6,
            cpc: 1.2,
            trend: "up",
            trend_data: [100, 110],
            relevance_score: 0.85,
          },
        ],
      });

      const { result } = renderHook(() => useKeywordSuggestions("romance"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/market/keywords/suggestions",
        { params: { genre: "romance", limit: 20 } }
      );
    });

    it("does not fetch when genre is empty", () => {
      const { result } = renderHook(() => useKeywordSuggestions(""), {
        wrapper: createWrapper(),
      });

      expect(result.current.isFetching).toBe(false);
      expect(mockGet).not.toHaveBeenCalled();
    });
  });
});
