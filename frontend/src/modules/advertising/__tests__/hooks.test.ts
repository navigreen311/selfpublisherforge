/**
 * Tests for advertising module React Query hooks.
 */
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------
const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPatch = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
  },
}));

// ---------------------------------------------------------------------------
// Import hooks (must be AFTER mocks)
// ---------------------------------------------------------------------------
import {
  useCampaigns,
  useCampaign,
  useCreateCampaign,
  useUpdateCampaign,
  useCampaignPerformance,
  useOptimizeCampaign,
  useKeywordBids,
  useUpdateKeywordBids,
  useCreatives,
  useGenerateCreatives,
  useAdDashboard,
} from "../hooks";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const mockCampaignsResponse = {
  items: [
    {
      id: "camp-1",
      org_id: "org-1",
      name: "Fantasy Campaign",
      platform: "amazon",
      campaign_type: "sponsored_products",
      status: "active",
      daily_budget: 25,
      bid_strategy: "manual",
      targeting_keywords: ["fantasy books"],
      negative_keywords: [],
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  has_more: false,
  total_count: 1,
};

const mockSingleCampaign = {
  id: "camp-1",
  org_id: "org-1",
  name: "Fantasy Campaign",
  platform: "amazon",
  campaign_type: "sponsored_products",
  status: "active",
  daily_budget: 25,
  bid_strategy: "manual",
  targeting_keywords: ["fantasy books"],
  negative_keywords: [],
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-01T00:00:00Z",
};

const mockPerformanceData = [
  {
    id: "perf-1",
    campaign_id: "camp-1",
    date: "2025-07-01",
    impressions: 1000,
    clicks: 30,
    spend: 25.0,
    sales: 75.0,
    orders: 3,
    acos: 33.3,
    roas: 3.0,
    ctr: 3.0,
    cpc: 0.83,
    conversion_rate: 10.0,
  },
];

const mockKeywordBids = [
  {
    id: "kw-1",
    campaign_id: "camp-1",
    keyword: "fantasy books",
    match_type: "exact",
    bid_amount: 0.75,
    is_negative: false,
    is_active: true,
    impressions: 500,
    clicks: 15,
    spend: 11.25,
    sales: 45.0,
    acos: 25.0,
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

const mockCreatives = [
  {
    id: "cr-1",
    org_id: "org-1",
    campaign_id: "camp-1",
    headline: "Epic Fantasy Awaits",
    body_text: "Discover a new world of adventure",
    call_to_action: "Buy Now",
    status: "active",
    impressions: 2000,
    clicks: 60,
    ctr: 3.0,
    conversions: 5,
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

const mockDashboard = {
  total_active_campaigns: 3,
  total_spend_today: 50.0,
  total_spend_month: 1500.0,
  total_sales_month: 4500.0,
  overall_acos: 33.3,
  overall_roas: 3.0,
  top_campaigns: [mockSingleCampaign],
  platform_breakdown: {},
  recent_optimizations: [],
};

const mockOptimizationSuggestion = {
  campaign_id: "camp-1",
  campaign_name: "Fantasy Campaign",
  current_acos: 35.0,
  target_acos: 30.0,
  bid_adjustments: [],
  keywords_to_add: ["epic fantasy"],
  keywords_to_negate: ["free fantasy"],
  summary: "Adjust bids to improve ACOS",
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Advertising Hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---- Campaign Hooks ----

  describe("useCampaigns", () => {
    it("fetches campaign list from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCampaignsResponse });

      const { result } = renderHook(() => useCampaigns(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns",
        { params: undefined }
      );
      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].name).toBe("Fantasy Campaign");
    });

    it("passes filter params to the API", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCampaignsResponse });

      const params = { platform: "amazon", status: "active", limit: 10 };
      const { result } = renderHook(() => useCampaigns(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns",
        { params }
      );
    });

    it("handles error state", async () => {
      mockGet.mockRejectedValueOnce(new Error("API error"));

      const { result } = renderHook(() => useCampaigns(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeTruthy();
    });
  });

  describe("useCampaign", () => {
    it("fetches a single campaign by id", async () => {
      mockGet.mockResolvedValueOnce({ data: mockSingleCampaign });

      const { result } = renderHook(() => useCampaign("camp-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/ads/campaigns/camp-1");
      expect(result.current.data?.name).toBe("Fantasy Campaign");
    });

    it("does not fetch when id is empty", async () => {
      const { result } = renderHook(() => useCampaign(""), {
        wrapper: createWrapper(),
      });

      expect(mockGet).not.toHaveBeenCalled();
      expect(result.current.isFetching).toBe(false);
    });

    it("handles fetch error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Not found"));

      const { result } = renderHook(() => useCampaign("camp-999"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeTruthy();
    });
  });

  describe("useUpdateCampaign", () => {
    it("patches the correct campaign endpoint", async () => {
      const updatedCampaign = { ...mockSingleCampaign, name: "Updated Campaign" };
      mockPatch.mockResolvedValueOnce({ data: updatedCampaign });

      const { result } = renderHook(() => useUpdateCampaign("camp-1"), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({ name: "Updated Campaign" });

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns/camp-1",
        { name: "Updated Campaign" }
      );
    });

    it("handles update error", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Update failed"));

      const { result } = renderHook(() => useUpdateCampaign("camp-1"), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({ name: "Failed Update" })
      ).rejects.toThrow("Update failed");
    });
  });

  describe("useCreateCampaign", () => {
    it("posts to the create campaign endpoint", async () => {
      const createdCampaign = { ...mockSingleCampaign, id: "camp-new" };
      mockPost.mockResolvedValueOnce({ data: createdCampaign });

      const { result } = renderHook(() => useCreateCampaign(), {
        wrapper: createWrapper(),
      });

      const newCampaign = {
        name: "New Campaign",
        platform: "amazon",
        campaign_type: "sponsored_products",
        daily_budget: 30,
      };

      await result.current.mutateAsync(newCampaign);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns",
        newCampaign
      );
    });

    it("handles creation error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Creation failed"));

      const { result } = renderHook(() => useCreateCampaign(), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({
          name: "Failed Campaign",
          platform: "amazon",
          campaign_type: "sponsored_products",
          daily_budget: 30,
        })
      ).rejects.toThrow("Creation failed");
    });
  });

  // ---- Performance Hooks ----

  describe("useCampaignPerformance", () => {
    it("fetches performance data for a campaign", async () => {
      mockGet.mockResolvedValueOnce({ data: mockPerformanceData });

      const { result } = renderHook(() => useCampaignPerformance("camp-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns/camp-1/performance",
        { params: undefined }
      );
      expect(result.current.data).toHaveLength(1);
    });

    it("passes date params to the endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockPerformanceData });

      const params = { date_from: "2025-07-01", date_to: "2025-07-31" };
      const { result } = renderHook(
        () => useCampaignPerformance("camp-1", params),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns/camp-1/performance",
        { params }
      );
    });

    it("does not fetch when campaignId is empty", async () => {
      const { result } = renderHook(() => useCampaignPerformance(""), {
        wrapper: createWrapper(),
      });

      expect(mockGet).not.toHaveBeenCalled();
      expect(result.current.isFetching).toBe(false);
    });
  });

  // ---- Optimization Hooks ----

  describe("useOptimizeCampaign", () => {
    it("posts to the optimize endpoint", async () => {
      mockPost.mockResolvedValueOnce({ data: mockOptimizationSuggestion });

      const { result } = renderHook(() => useOptimizeCampaign("camp-1"), {
        wrapper: createWrapper(),
      });

      const params = { target_acos: 30, max_bid_increase_pct: 20 };
      await result.current.mutateAsync(params);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/ads/campaigns/camp-1/optimize",
        params
      );
    });

    it("handles optimization error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Optimization failed"));

      const { result } = renderHook(() => useOptimizeCampaign("camp-1"), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({ target_acos: 30 })
      ).rejects.toThrow("Optimization failed");
    });
  });

  // ---- Keyword Bid Hooks ----

  describe("useKeywordBids", () => {
    it("fetches keyword bids for a campaign", async () => {
      mockGet.mockResolvedValueOnce({ data: mockKeywordBids });

      const { result } = renderHook(() => useKeywordBids("camp-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/keyword-bids",
        { params: { campaign_id: "camp-1" } }
      );
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].keyword).toBe("fantasy books");
    });

    it("fetches all keyword bids when no campaignId is provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockKeywordBids });

      const { result } = renderHook(() => useKeywordBids(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/keyword-bids",
        { params: {} }
      );
    });

    it("handles error state", async () => {
      mockGet.mockRejectedValueOnce(new Error("Bid fetch failed"));

      const { result } = renderHook(() => useKeywordBids("camp-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeTruthy();
    });
  });

  describe("useUpdateKeywordBids", () => {
    it("patches keyword bids", async () => {
      const updatedBids = [{ ...mockKeywordBids[0], bid_amount: 1.0 }];
      mockPatch.mockResolvedValueOnce({ data: updatedBids });

      const { result } = renderHook(() => useUpdateKeywordBids(), {
        wrapper: createWrapper(),
      });

      const updates = [{ id: "kw-1", bid_amount: 1.0 }];
      await result.current.mutateAsync(updates);

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/ads/keyword-bids",
        { updates }
      );
    });

    it("handles update error", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Bid update failed"));

      const { result } = renderHook(() => useUpdateKeywordBids(), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync([{ id: "kw-1", bid_amount: 1.0 }])
      ).rejects.toThrow("Bid update failed");
    });
  });

  // ---- Creative Hooks ----

  describe("useCreatives", () => {
    it("fetches creatives for a campaign", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCreatives });

      const { result } = renderHook(() => useCreatives("camp-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/creatives",
        { params: { campaign_id: "camp-1" } }
      );
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].headline).toBe("Epic Fantasy Awaits");
    });

    it("fetches all creatives when no campaignId is provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockCreatives });

      const { result } = renderHook(() => useCreatives(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/ads/creatives",
        { params: {} }
      );
    });
  });

  describe("useGenerateCreatives", () => {
    it("posts to the generate creatives endpoint", async () => {
      const generatedResponse = {
        variations: [
          {
            headline: "Generated Headline",
            body_text: "Generated body",
            call_to_action: "Buy Now",
            reasoning: "High impact headline",
          },
        ],
        platform: "amazon",
        book_title: "My Book",
      };
      mockPost.mockResolvedValueOnce({ data: generatedResponse });

      const { result } = renderHook(() => useGenerateCreatives(), {
        wrapper: createWrapper(),
      });

      const request = {
        book_title: "My Book",
        book_description: "A fantasy adventure",
        genre: "Fantasy",
        num_variations: 3,
      };

      await result.current.mutateAsync(request);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/ads/creatives/generate",
        request
      );
    });

    it("handles generation error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Generation failed"));

      const { result } = renderHook(() => useGenerateCreatives(), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({
          book_title: "My Book",
          book_description: "A book",
        })
      ).rejects.toThrow("Generation failed");
    });
  });

  // ---- Dashboard Hook ----

  describe("useAdDashboard", () => {
    it("fetches dashboard data from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockDashboard });

      const { result } = renderHook(() => useAdDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/ads/dashboard");
      expect(result.current.data?.total_active_campaigns).toBe(3);
      expect(result.current.data?.overall_acos).toBe(33.3);
    });

    it("handles dashboard fetch error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Dashboard error"));

      const { result } = renderHook(() => useAdDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeTruthy();
    });
  });
});
