import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ── Mock the API module ──────────────────────────────────────────────────

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// ── Import hooks under test (after mocks) ────────────────────────────────

import {
  useAnalyzeListing,
  useGenerateBlurb,
  useCreateABTest,
  useABTestResults,
  useAnalyzeLookInside,
  useMobileCheck,
  useConversionScores,
} from "../hooks";

// ── Helpers ──────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

// ── Test Data ────────────────────────────────────────────────────────────

const mockListingAnalysis = {
  asin: "B00TEST123",
  title: "Test Book Title",
  title_score: 85,
  blurb_score: 72,
  keyword_score: 68,
  category_score: 90,
  price_score: 80,
  overall_score: 79,
  title_analysis: {
    score: 85,
    length: 45,
    has_keywords: true,
    keyword_matches: ["thriller", "mystery"],
    power_words: ["gripping", "unputdownable"],
    issues: [],
  },
  blurb_analysis: {
    score: 72,
    word_count: 150,
    has_hook: true,
    has_bullet_points: false,
    has_cta: true,
    has_html_formatting: true,
    readability_grade: 8.5,
    emotional_words: ["thrilling", "suspense"],
    issues: ["Consider adding bullet points"],
  },
  keyword_analysis: {
    score: 68,
    keywords_found: ["thriller", "mystery", "suspense"],
    keyword_density: 3.2,
    missing_high_value_keywords: ["bestseller"],
    over_stuffed: false,
  },
  category_analysis: {
    score: 90,
    current_categories: ["Mystery & Thriller"],
    suggested_categories: ["Mystery & Thriller", "Suspense"],
    category_rank_potential: "Top 100",
  },
  price_analysis: {
    score: 80,
    current_price: 4.99,
    genre_avg_price: 3.99,
    suggested_range: "$2.99-$4.99",
    issues: [],
  },
  recommendations: [
    {
      area: "blurb",
      severity: "warning" as const,
      message: "Missing bullet points",
      suggestion: "Add 3-5 bullet points highlighting key features",
    },
  ],
  analyzed_at: "2025-06-01T00:00:00Z",
};

const mockBlurbResponse = {
  original_score: 72,
  variants: [
    {
      variant_id: "v-1",
      content: "An optimized blurb variant...",
      style: "emotional",
      hook_type: "question",
      estimated_conversion_score: 85,
      highlights: ["Strong hook", "Clear CTA"],
    },
    {
      variant_id: "v-2",
      content: "Another blurb variant...",
      style: "direct",
      hook_type: "statement",
      estimated_conversion_score: 82,
      highlights: ["Concise", "Keyword-rich"],
    },
  ],
  generation_metadata: { model: "gpt-4", tokens_used: 500 },
};

const mockABTestResponse = {
  id: "ab-1",
  book_id: "book-1",
  name: "Blurb A/B Test",
  status: "running" as const,
  variant_a: {
    variant_label: "A",
    content: "Original blurb",
    impressions: 1000,
    clicks: 50,
    click_through_rate: 5.0,
    conversion_rate: 2.5,
    estimated_score: 72,
  },
  variant_b: {
    variant_label: "B",
    content: "Optimized blurb",
    impressions: 1000,
    clicks: 75,
    click_through_rate: 7.5,
    conversion_rate: 3.8,
    estimated_score: 85,
  },
  winner: undefined,
  confidence: undefined,
  started_at: "2025-06-01T00:00:00Z",
  completed_at: undefined,
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-02T00:00:00Z",
};

const mockMobileCheckResult = {
  overall_score: 78,
  title_display: {
    field: "title",
    original_length: 45,
    visible_length: 40,
    is_truncated: true,
    visible_text: "Test Book Title: A Gripping Thriller...",
    truncated_text: " of Mystery",
  },
  subtitle_display: undefined,
  blurb_fold_point: 120,
  blurb_above_fold: "First 120 characters of the blurb...",
  blurb_above_fold_word_count: 20,
  cover_aspect_ratio_ok: true,
  cover_readable_at_thumbnail: true,
  price_visibility: "prominent",
  buy_button_proximity: "near",
  recommendations: [
    {
      area: "title",
      severity: "info" as const,
      message: "Title is slightly truncated on mobile",
      suggestion: "Consider shortening title to under 40 characters",
    },
  ],
  device_previews: {
    iphone_14: { width: 390, height: 844 },
    pixel_7: { width: 412, height: 915 },
  },
};

const mockLookInsideAnalysis = {
  overall_score: 82,
  hook_strength: 88,
  first_page_impact: 85,
  pacing_score: 78,
  toc_effectiveness: 75,
  sections: [
    {
      section: "opening_hook",
      score: 88,
      feedback: "Strong opening that grabs attention",
      suggestions: ["Consider starting with dialogue"],
    },
    {
      section: "first_chapter",
      score: 85,
      feedback: "Good pacing and character introduction",
      suggestions: [],
    },
  ],
  recommendations: [
    {
      area: "look_inside",
      severity: "info" as const,
      message: "Table of contents could be more descriptive",
      suggestion: "Use chapter titles that hint at content",
    },
  ],
};

const mockConversionScores = {
  book_id: "book-1",
  listing_score: 79,
  blurb_score: 72,
  mobile_score: 78,
  look_inside_score: 82,
  overall_score: 78,
  last_analyzed_at: "2025-06-01T00:00:00Z",
  recommendations_count: 5,
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("Product Page hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---------- useAnalyzeListing ----------

  describe("useAnalyzeListing", () => {
    it("analyzes a listing by ASIN via POST", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockListingAnalysis },
      });

      const { result } = renderHook(() => useAnalyzeListing(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ asin: "B00TEST123" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/analyze",
        { asin: "B00TEST123" }
      );
      expect(result.current.data?.overall_score).toBe(79);
      expect(result.current.data?.asin).toBe("B00TEST123");
    });

    it("analyzes a listing by URL", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockListingAnalysis },
      });

      const { result } = renderHook(() => useAnalyzeListing(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ url: "https://amazon.com/dp/B00TEST123" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/analyze",
        { url: "https://amazon.com/dp/B00TEST123" }
      );
    });

    it("analyzes a listing by book_id", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockListingAnalysis },
      });

      const { result } = renderHook(() => useAnalyzeListing(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ book_id: "book-1" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/analyze",
        { book_id: "book-1" }
      );
    });

    it("handles analysis errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("ASIN not found"));

      const { result } = renderHook(() => useAnalyzeListing(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ asin: "INVALID" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("ASIN not found");
    });
  });

  // ---------- useGenerateBlurb ----------

  describe("useGenerateBlurb", () => {
    it("generates blurb variants via POST", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockBlurbResponse },
      });

      const { result } = renderHook(() => useGenerateBlurb(), {
        wrapper: createWrapper(),
      });

      const request = {
        current_blurb: "An existing blurb...",
        genre: "thriller",
        target_audience: "adults",
        keywords: ["mystery", "suspense"],
        tone: "dramatic",
        num_variants: 2,
      };

      act(() => {
        result.current.mutate(request);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/blurb/generate",
        request
      );
      expect(result.current.data?.variants).toHaveLength(2);
      expect(result.current.data?.original_score).toBe(72);
    });

    it("handles blurb generation errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Generation failed"));

      const { result } = renderHook(() => useGenerateBlurb(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          current_blurb: "test",
          genre: "fiction",
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Generation failed");
    });
  });

  // ---------- useCreateABTest ----------

  describe("useCreateABTest", () => {
    it("creates an A/B test via POST", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockABTestResponse },
      });

      const { result } = renderHook(() => useCreateABTest(), {
        wrapper: createWrapper(),
      });

      const request = {
        book_id: "book-1",
        name: "Blurb A/B Test",
        variant_a: "Original blurb",
        variant_b: "Optimized blurb",
        duration_days: 14,
      };

      act(() => {
        result.current.mutate(request);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/blurb/ab-test",
        request
      );
      expect(result.current.data?.id).toBe("ab-1");
      expect(result.current.data?.status).toBe("running");
    });

    it("handles A/B test creation errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Book not found"));

      const { result } = renderHook(() => useCreateABTest(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          book_id: "invalid",
          name: "Test",
          variant_a: "A",
          variant_b: "B",
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Book not found");
    });
  });

  // ---------- useABTestResults ----------

  describe("useABTestResults", () => {
    it("fetches A/B test results successfully", async () => {
      mockGet.mockResolvedValueOnce({
        data: { data: mockABTestResponse },
      });

      const { result } = renderHook(() => useABTestResults("ab-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/product-page/blurb/ab-test/ab-1"
      );
      expect(result.current.data?.id).toBe("ab-1");
      expect(result.current.data?.variant_a.click_through_rate).toBe(5.0);
      expect(result.current.data?.variant_b.click_through_rate).toBe(7.5);
    });

    it("does not fetch when testId is undefined", async () => {
      const { result } = renderHook(() => useABTestResults(undefined), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("does not fetch when testId is empty string", async () => {
      const { result } = renderHook(() => useABTestResults(""), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles errors fetching A/B test results", async () => {
      mockGet.mockRejectedValueOnce(new Error("Test not found"));

      const { result } = renderHook(() => useABTestResults("ab-invalid"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Test not found");
    });
  });

  // ---------- useAnalyzeLookInside ----------

  describe("useAnalyzeLookInside", () => {
    it("analyzes Look Inside preview via POST", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockLookInsideAnalysis },
      });

      const { result } = renderHook(() => useAnalyzeLookInside(), {
        wrapper: createWrapper(),
      });

      const request = {
        book_id: "book-1",
        preview_text: "Chapter 1: The beginning of the story...",
        genre: "thriller",
        chapter_titles: ["Chapter 1: The Beginning", "Chapter 2: The Middle"],
      };

      act(() => {
        result.current.mutate(request);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/look-inside/analyze",
        request
      );
      expect(result.current.data?.overall_score).toBe(82);
      expect(result.current.data?.hook_strength).toBe(88);
      expect(result.current.data?.sections).toHaveLength(2);
    });

    it("handles Look Inside analysis errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Analysis failed"));

      const { result } = renderHook(() => useAnalyzeLookInside(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          preview_text: "text",
          genre: "fiction",
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Analysis failed");
    });
  });

  // ---------- useMobileCheck ----------

  describe("useMobileCheck", () => {
    it("checks mobile display via POST", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockMobileCheckResult },
      });

      const { result } = renderHook(() => useMobileCheck(), {
        wrapper: createWrapper(),
      });

      const request = {
        title: "Test Book Title: A Gripping Thriller of Mystery",
        blurb: "An exciting blurb about the book...",
        author_name: "Test Author",
        cover_image_url: "https://example.com/cover.jpg",
        price: 4.99,
      };

      act(() => {
        result.current.mutate(request);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/product-page/mobile-check",
        request
      );
      expect(result.current.data?.overall_score).toBe(78);
      expect(result.current.data?.cover_aspect_ratio_ok).toBe(true);
      expect(result.current.data?.title_display.is_truncated).toBe(true);
    });

    it("handles mobile check errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Invalid request"));

      const { result } = renderHook(() => useMobileCheck(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          title: "Title",
          blurb: "Blurb",
          author_name: "Author",
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Invalid request");
    });
  });

  // ---------- useConversionScores ----------

  describe("useConversionScores", () => {
    it("fetches conversion scores successfully", async () => {
      mockGet.mockResolvedValueOnce({
        data: { data: mockConversionScores },
      });

      const { result } = renderHook(() => useConversionScores("book-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/product-page/scores/book-1"
      );
      expect(result.current.data?.overall_score).toBe(78);
      expect(result.current.data?.book_id).toBe("book-1");
      expect(result.current.data?.recommendations_count).toBe(5);
    });

    it("does not fetch when bookId is undefined", async () => {
      const { result } = renderHook(() => useConversionScores(undefined), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("does not fetch when bookId is empty string", async () => {
      const { result } = renderHook(() => useConversionScores(""), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles errors fetching conversion scores", async () => {
      mockGet.mockRejectedValueOnce(new Error("Book not found"));

      const { result } = renderHook(() => useConversionScores("invalid"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Book not found");
    });
  });

  // ---------- Data structure correctness ----------

  describe("data structure correctness", () => {
    it("verifies listing analysis sub-scores structure", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockListingAnalysis },
      });

      const { result } = renderHook(() => useAnalyzeListing(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ asin: "B00TEST123" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const analysis = result.current.data!;
      expect(typeof analysis.title_score).toBe("number");
      expect(typeof analysis.blurb_score).toBe("number");
      expect(typeof analysis.keyword_score).toBe("number");
      expect(typeof analysis.category_score).toBe("number");
      expect(typeof analysis.price_score).toBe("number");
      expect(typeof analysis.overall_score).toBe("number");
      expect(analysis.recommendations).toBeInstanceOf(Array);
      expect(analysis.title_analysis).toHaveProperty("score");
      expect(analysis.blurb_analysis).toHaveProperty("score");
      expect(analysis.keyword_analysis).toHaveProperty("score");
    });

    it("verifies blurb variant structure", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockBlurbResponse },
      });

      const { result } = renderHook(() => useGenerateBlurb(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          current_blurb: "test",
          genre: "fiction",
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const response = result.current.data!;
      expect(typeof response.original_score).toBe("number");
      expect(response.variants).toBeInstanceOf(Array);
      response.variants.forEach((variant) => {
        expect(variant).toHaveProperty("variant_id");
        expect(variant).toHaveProperty("content");
        expect(variant).toHaveProperty("style");
        expect(variant).toHaveProperty("estimated_conversion_score");
        expect(typeof variant.estimated_conversion_score).toBe("number");
      });
    });

    it("verifies A/B test response structure", async () => {
      mockGet.mockResolvedValueOnce({
        data: { data: mockABTestResponse },
      });

      const { result } = renderHook(() => useABTestResults("ab-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const test = result.current.data!;
      expect(test).toHaveProperty("id");
      expect(test).toHaveProperty("book_id");
      expect(test).toHaveProperty("status");
      expect(test).toHaveProperty("variant_a");
      expect(test).toHaveProperty("variant_b");
      expect(typeof test.variant_a.click_through_rate).toBe("number");
      expect(typeof test.variant_a.conversion_rate).toBe("number");
      expect(typeof test.variant_b.click_through_rate).toBe("number");
      expect(typeof test.variant_b.conversion_rate).toBe("number");
    });

    it("verifies mobile check result structure", async () => {
      mockPost.mockResolvedValueOnce({
        data: { data: mockMobileCheckResult },
      });

      const { result } = renderHook(() => useMobileCheck(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          title: "Title",
          blurb: "Blurb",
          author_name: "Author",
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const check = result.current.data!;
      expect(typeof check.overall_score).toBe("number");
      expect(check.title_display).toHaveProperty("is_truncated");
      expect(typeof check.blurb_fold_point).toBe("number");
      expect(typeof check.cover_aspect_ratio_ok).toBe("boolean");
      expect(typeof check.cover_readable_at_thumbnail).toBe("boolean");
      expect(check.recommendations).toBeInstanceOf(Array);
      expect(check.device_previews).toBeDefined();
    });

    it("verifies conversion scores structure", async () => {
      mockGet.mockResolvedValueOnce({
        data: { data: mockConversionScores },
      });

      const { result } = renderHook(() => useConversionScores("book-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const scores = result.current.data!;
      expect(typeof scores.overall_score).toBe("number");
      expect(typeof scores.recommendations_count).toBe("number");
      expect(scores).toHaveProperty("book_id");
      expect(scores).toHaveProperty("listing_score");
      expect(scores).toHaveProperty("blurb_score");
      expect(scores).toHaveProperty("mobile_score");
      expect(scores).toHaveProperty("look_inside_score");
    });
  });
});
