/**
 * Tests for marketing module React Query hooks.
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
  useLaunchPlans,
  useLaunchPlan,
  useGenerateLaunchPlan,
  useUpdateLaunchPlan,
  useEmailSequences,
  useCreateEmailSequence,
  useUpdateEmailSequence,
  useTriggerEmailSend,
  useSocialCalendar,
  useGenerateSocialContent,
  useARCCampaigns,
  useCreateARCCampaign,
  useSendARCCopies,
  useRecentActivity,
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

const mockLaunchPlansResponse = {
  items: [
    {
      id: "lp-1",
      org_id: "org-1",
      book_id: "book-1",
      title: "Fantasy Launch",
      status: "draft",
      created_by: "user-1",
      phases: [],
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  total_count: 1,
  has_more: false,
};

const mockSinglePlan = {
  id: "lp-1",
  org_id: "org-1",
  book_id: "book-1",
  title: "Fantasy Launch",
  status: "draft",
  created_by: "user-1",
  phases: [],
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-01T00:00:00Z",
};

const mockEmailSequencesResponse = {
  items: [
    {
      id: "es-1",
      org_id: "org-1",
      name: "Welcome Series",
      status: "active",
      recipient_count: 100,
      sent_count: 50,
      emails: [],
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  total_count: 1,
  has_more: false,
};

const mockSocialCalendarResponse = {
  posts: [
    {
      id: "sp-1",
      org_id: "org-1",
      platform: "twitter",
      content: "Check out my new book!",
      status: "published",
      published_at: "2025-07-01T00:00:00Z",
      created_at: "2025-06-15T00:00:00Z",
      updated_at: "2025-07-01T00:00:00Z",
    },
  ],
  total_scheduled: 2,
  total_published: 1,
  total_draft: 1,
  platforms: { twitter: 1 },
};

const mockARCCampaignsResponse = {
  items: [
    {
      id: "arc-1",
      org_id: "org-1",
      book_id: "book-1",
      name: "ARC Campaign 1",
      status: "active",
      total_copies: 50,
      sent_copies: 20,
      reviews_received: 5,
      recipients: [],
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  total_count: 1,
  has_more: false,
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Marketing Hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---- Launch Plan Hooks ----

  describe("useLaunchPlans", () => {
    it("fetches from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockLaunchPlansResponse });

      const { result } = renderHook(() => useLaunchPlans(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/marketing/launch-plans",
        { params: undefined }
      );
    });

    it("returns typed paginated data", async () => {
      mockGet.mockResolvedValueOnce({ data: mockLaunchPlansResponse });

      const { result } = renderHook(() => useLaunchPlans(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockLaunchPlansResponse);
      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].title).toBe("Fantasy Launch");
      expect(result.current.data?.total_count).toBe(1);
    });

    it("passes params to the API call", async () => {
      mockGet.mockResolvedValueOnce({ data: mockLaunchPlansResponse });

      const params = { status: "active", limit: 5, offset: 0 };
      const { result } = renderHook(() => useLaunchPlans(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/marketing/launch-plans",
        { params }
      );
    });

    it("handles API error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useLaunchPlans(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeTruthy();
    });
  });

  describe("useLaunchPlan", () => {
    it("fetches a single plan from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: { data: mockSinglePlan } });

      const { result } = renderHook(() => useLaunchPlan("lp-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/marketing/launch-plans/lp-1");
      expect(result.current.data).toEqual(mockSinglePlan);
    });

    it("does not fetch when id is empty", async () => {
      const { result } = renderHook(() => useLaunchPlan(""), {
        wrapper: createWrapper(),
      });

      // Should remain idle - never fires the request
      expect(mockGet).not.toHaveBeenCalled();
      expect(result.current.isFetching).toBe(false);
    });
  });

  describe("useGenerateLaunchPlan", () => {
    it("posts to the generate endpoint", async () => {
      const generatedPlan = { ...mockSinglePlan, id: "lp-new" };
      mockPost.mockResolvedValueOnce({ data: { data: generatedPlan } });

      const { result } = renderHook(() => useGenerateLaunchPlan(), {
        wrapper: createWrapper(),
      });

      const request = {
        book_id: "book-1",
        book_title: "My Fantasy Book",
        genre: "Fantasy",
        target_audience: "Young adults",
        launch_date: "2025-09-01",
      };

      await result.current.mutateAsync(request);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/marketing/launch-plan/generate",
        request
      );
    });

    it("handles mutation error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Generation failed"));

      const { result } = renderHook(() => useGenerateLaunchPlan(), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({
          book_id: "book-1",
          book_title: "My Book",
          genre: "Fantasy",
          target_audience: "Adults",
          launch_date: "2025-09-01",
        })
      ).rejects.toThrow("Generation failed");
    });
  });

  describe("useUpdateLaunchPlan", () => {
    it("patches the correct endpoint", async () => {
      const updatedPlan = { ...mockSinglePlan, title: "Updated Title" };
      mockPatch.mockResolvedValueOnce({ data: { data: updatedPlan } });

      const { result } = renderHook(() => useUpdateLaunchPlan("lp-1"), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({ title: "Updated Title" });

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/marketing/launch-plans/lp-1",
        { title: "Updated Title" }
      );
    });
  });

  // ---- Email Sequence Hooks ----

  describe("useEmailSequences", () => {
    it("fetches from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockEmailSequencesResponse });

      const { result } = renderHook(() => useEmailSequences(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/marketing/email-sequences",
        { params: undefined }
      );
      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].name).toBe("Welcome Series");
    });

    it("handles error state", async () => {
      mockGet.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useEmailSequences(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeTruthy();
    });
  });

  describe("useCreateEmailSequence", () => {
    it("posts to the create endpoint", async () => {
      const newSequence = { ...mockEmailSequencesResponse.items[0], id: "es-new" };
      mockPost.mockResolvedValueOnce({ data: { data: newSequence } });

      const { result } = renderHook(() => useCreateEmailSequence(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({ name: "New Sequence", status: "draft" });

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/marketing/email-sequences",
        { name: "New Sequence", status: "draft" }
      );
    });
  });

  describe("useUpdateEmailSequence", () => {
    it("patches the correct endpoint", async () => {
      const updatedSeq = { ...mockEmailSequencesResponse.items[0], name: "Updated" };
      mockPatch.mockResolvedValueOnce({ data: { data: updatedSeq } });

      const { result } = renderHook(() => useUpdateEmailSequence("es-1"), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({ name: "Updated" });

      expect(mockPatch).toHaveBeenCalledWith(
        "/api/v1/marketing/email-sequences/es-1",
        { name: "Updated" }
      );
    });
  });

  describe("useTriggerEmailSend", () => {
    it("posts to the send endpoint", async () => {
      const sentSeq = { ...mockEmailSequencesResponse.items[0], sent_count: 51 };
      mockPost.mockResolvedValueOnce({ data: { data: sentSeq } });

      const { result } = renderHook(() => useTriggerEmailSend("es-1"), {
        wrapper: createWrapper(),
      });

      const payload = { recipient_emails: ["test@example.com"] };
      await result.current.mutateAsync(payload);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/marketing/email-sequences/es-1/send",
        payload
      );
    });

    it("handles send error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Send failed"));

      const { result } = renderHook(() => useTriggerEmailSend("es-1"), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({ recipient_emails: ["test@example.com"] })
      ).rejects.toThrow("Send failed");
    });
  });

  // ---- Social Media Hooks ----

  describe("useSocialCalendar", () => {
    it("fetches from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockSocialCalendarResponse });

      const { result } = renderHook(() => useSocialCalendar(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/marketing/social/calendar",
        { params: undefined }
      );
      expect(result.current.data?.posts).toHaveLength(1);
      expect(result.current.data?.total_published).toBe(1);
    });

    it("passes filter params", async () => {
      mockGet.mockResolvedValueOnce({ data: mockSocialCalendarResponse });

      const params = { start_date: "2025-07-01", platform: "twitter" };
      const { result } = renderHook(() => useSocialCalendar(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/marketing/social/calendar",
        { params }
      );
    });
  });

  describe("useGenerateSocialContent", () => {
    it("posts to the generate endpoint", async () => {
      const generatedPosts = [mockSocialCalendarResponse.posts[0]];
      mockPost.mockResolvedValueOnce({ data: { data: generatedPosts } });

      const { result } = renderHook(() => useGenerateSocialContent(), {
        wrapper: createWrapper(),
      });

      const request = {
        book_title: "My Book",
        genre: "Fantasy",
        target_audience: "Young adults",
        book_description: "A fantasy adventure",
      };

      await result.current.mutateAsync(request);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/marketing/social/generate",
        request
      );
    });
  });

  // ---- ARC Campaign Hooks ----

  describe("useARCCampaigns", () => {
    it("fetches from the correct endpoint", async () => {
      mockGet.mockResolvedValueOnce({ data: mockARCCampaignsResponse });

      const { result } = renderHook(() => useARCCampaigns(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/marketing/arc",
        { params: undefined }
      );
      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].name).toBe("ARC Campaign 1");
    });

    it("handles error state", async () => {
      mockGet.mockRejectedValueOnce(new Error("ARC fetch failed"));

      const { result } = renderHook(() => useARCCampaigns(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeTruthy();
    });
  });

  describe("useCreateARCCampaign", () => {
    it("posts to the create endpoint", async () => {
      const newCampaign = { ...mockARCCampaignsResponse.items[0], id: "arc-new" };
      mockPost.mockResolvedValueOnce({ data: { data: newCampaign } });

      const { result } = renderHook(() => useCreateARCCampaign(), {
        wrapper: createWrapper(),
      });

      const payload = {
        book_id: "book-1",
        name: "New ARC Campaign",
        recipients: [{ name: "Reviewer", email: "reviewer@example.com" }],
      };

      await result.current.mutateAsync(payload);

      expect(mockPost).toHaveBeenCalledWith("/api/v1/marketing/arc", payload);
    });
  });

  describe("useSendARCCopies", () => {
    it("posts to the send endpoint", async () => {
      const sentCampaign = { ...mockARCCampaignsResponse.items[0], sent_copies: 25 };
      mockPost.mockResolvedValueOnce({ data: { data: sentCampaign } });

      const { result } = renderHook(() => useSendARCCopies("arc-1"), {
        wrapper: createWrapper(),
      });

      const payload = { recipient_ids: ["r-1", "r-2"], custom_message: "Enjoy!" };
      await result.current.mutateAsync(payload);

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/marketing/arc/arc-1/send",
        payload
      );
    });

    it("handles send error", async () => {
      mockPost.mockRejectedValueOnce(new Error("ARC send failed"));

      const { result } = renderHook(() => useSendARCCopies("arc-1"), {
        wrapper: createWrapper(),
      });

      await expect(
        result.current.mutateAsync({ recipient_ids: ["r-1"] })
      ).rejects.toThrow("ARC send failed");
    });
  });

  // ---- Recent Activity Hook ----

  describe("useRecentActivity", () => {
    it("derives activity from existing marketing data", async () => {
      // useRecentActivity calls useLaunchPlans, useEmailSequences, useARCCampaigns, useSocialCalendar
      // We need to return data for all four internal hooks
      mockGet
        .mockResolvedValueOnce({ data: mockLaunchPlansResponse })   // useLaunchPlans
        .mockResolvedValueOnce({ data: mockEmailSequencesResponse }) // useEmailSequences
        .mockResolvedValueOnce({ data: mockARCCampaignsResponse })  // useARCCampaigns
        .mockResolvedValueOnce({ data: mockSocialCalendarResponse }); // useSocialCalendar

      const { result } = renderHook(() => useRecentActivity(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Should have combined items from all sources
      expect(result.current.items.length).toBeGreaterThan(0);

      // Each item should have the expected shape
      for (const item of result.current.items) {
        expect(item).toHaveProperty("id");
        expect(item).toHaveProperty("type");
        expect(item).toHaveProperty("action");
        expect(item).toHaveProperty("title");
        expect(item).toHaveProperty("timestamp");
      }
    });

    it("returns empty items when all data sources are empty", async () => {
      const emptyPaginated = { items: [], total_count: 0, has_more: false };
      const emptyCalendar = { posts: [], total_scheduled: 0, total_published: 0, total_draft: 0, platforms: {} };

      mockGet
        .mockResolvedValueOnce({ data: emptyPaginated })   // useLaunchPlans
        .mockResolvedValueOnce({ data: emptyPaginated })    // useEmailSequences
        .mockResolvedValueOnce({ data: emptyPaginated })    // useARCCampaigns
        .mockResolvedValueOnce({ data: emptyCalendar });    // useSocialCalendar

      const { result } = renderHook(() => useRecentActivity(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      expect(result.current.items).toEqual([]);
    });

    it("respects the limit parameter", async () => {
      // Create many items that will exceed the limit
      const manyPlans = {
        items: Array.from({ length: 10 }, (_, i) => ({
          id: `lp-${i}`,
          org_id: "org-1",
          book_id: "book-1",
          title: `Plan ${i}`,
          status: "draft",
          created_by: "user-1",
          phases: [],
          created_at: "2025-06-01T00:00:00Z",
          updated_at: new Date(Date.now() - i * 86_400_000).toISOString(),
        })),
        total_count: 10,
        has_more: false,
      };
      const emptyPaginated = { items: [], total_count: 0, has_more: false };
      const emptyCalendar = { posts: [], total_scheduled: 0, total_published: 0, total_draft: 0, platforms: {} };

      mockGet
        .mockResolvedValueOnce({ data: manyPlans })
        .mockResolvedValueOnce({ data: emptyPaginated })
        .mockResolvedValueOnce({ data: emptyPaginated })
        .mockResolvedValueOnce({ data: emptyCalendar });

      const { result } = renderHook(() => useRecentActivity(3), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      expect(result.current.items.length).toBeLessThanOrEqual(3);
    });

    it("sorts activity by timestamp descending", async () => {
      const plansWithDates = {
        items: [
          {
            id: "lp-old",
            org_id: "org-1",
            book_id: "book-1",
            title: "Old Plan",
            status: "draft",
            created_by: "user-1",
            phases: [],
            created_at: "2025-01-01T00:00:00Z",
            updated_at: "2025-01-01T00:00:00Z",
          },
          {
            id: "lp-new",
            org_id: "org-1",
            book_id: "book-1",
            title: "New Plan",
            status: "active",
            created_by: "user-1",
            phases: [],
            created_at: "2025-07-01T00:00:00Z",
            updated_at: "2025-07-01T00:00:00Z",
          },
        ],
        total_count: 2,
        has_more: false,
      };
      const emptyPaginated = { items: [], total_count: 0, has_more: false };
      const emptyCalendar = { posts: [], total_scheduled: 0, total_published: 0, total_draft: 0, platforms: {} };

      mockGet
        .mockResolvedValueOnce({ data: plansWithDates })
        .mockResolvedValueOnce({ data: emptyPaginated })
        .mockResolvedValueOnce({ data: emptyPaginated })
        .mockResolvedValueOnce({ data: emptyCalendar });

      const { result } = renderHook(() => useRecentActivity(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Newest item should be first
      expect(result.current.items[0].title).toBe("New Plan");
      expect(result.current.items[1].title).toBe("Old Plan");
    });
  });
});
