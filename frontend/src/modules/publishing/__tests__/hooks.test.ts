import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ── Mock the API module ──────────────────────────────────────────────────

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPatch = jest.fn();
const mockDelete = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}));

// ── Import hooks under test (after mocks) ────────────────────────────────

import {
  usePublishingAccounts,
  useCreateAccount,
  useDeleteAccount,
  useExportEpub,
  useExportPdf,
  useFormattingTemplates,
  useBookMetadata,
  useUpdateMetadata,
  useListings,
  useSyncListing,
  publishingKeys,
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

const mockAccountsData = [
  {
    id: "acc-1",
    org_id: "org-1",
    platform: "kdp",
    account_name: "My KDP Account",
    account_email: "user@kdp.com",
    is_active: true,
    last_synced_at: null,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
];

const mockMetadataData = {
  book_id: "book-1",
  title: "Test Book",
  subtitle: null,
  description: "A test book",
  authors: ["Author A"],
  keywords: ["fiction"],
  categories: ["Fantasy"],
  language: "en",
  isbn: null,
  asin: null,
  publisher: null,
  publication_date: null,
  pricing: { currency: "USD", list_price: 9.99, sale_price: null },
  series_name: null,
  series_number: null,
  page_count: null,
  age_range: null,
  updated_at: "2025-06-01T00:00:00Z",
};

const mockListingsData = [
  {
    id: "lst-1",
    book_id: "book-1",
    account_id: "acc-1",
    platform: "kdp",
    platform_listing_id: "B00TEST",
    status: "active",
    listing_url: "https://amazon.com/dp/B00TEST",
    title: "Test Book",
    current_price: 9.99,
    current_rank: 1234,
    reviews_count: 10,
    rating: 4.2,
    last_synced_at: "2025-06-01T00:00:00Z",
    sync_errors: [],
    created_at: "2025-03-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

const mockExportResponse = {
  id: "export-1",
  book_id: "book-1",
  format: "epub",
  status: "completed",
  file_url: "https://files.example.com/export-1.epub",
  file_size_bytes: 1024000,
  page_count: null,
  created_at: "2025-06-01T00:00:00Z",
  message: "Export completed successfully",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("Publishing hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---------- Query key structure ----------

  describe("publishingKeys", () => {
    it("generates correct query keys for accounts", () => {
      expect(publishingKeys.accounts()).toEqual(["publishing", "accounts"]);
    });

    it("generates correct query keys for templates", () => {
      expect(publishingKeys.templates()).toEqual(["publishing", "templates"]);
    });

    it("generates correct query keys for listings", () => {
      expect(publishingKeys.listings()).toEqual(["publishing", "listings"]);
    });

    it("generates correct query keys for metadata with bookId", () => {
      expect(publishingKeys.metadata("book-123")).toEqual([
        "publishing",
        "metadata",
        "book-123",
      ]);
    });
  });

  // ---------- usePublishingAccounts (list hook) ----------

  describe("usePublishingAccounts", () => {
    it("fetches accounts from the API successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockAccountsData });

      const { result } = renderHook(() => usePublishingAccounts(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/publishing/accounts");
      expect(result.current.data).toEqual(mockAccountsData);
    });

    it("handles API errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => usePublishingAccounts(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
      expect(result.current.error?.message).toBe("Network error");
    });
  });

  // ---------- useCreateAccount (mutation) ----------

  describe("useCreateAccount", () => {
    it("creates a new account via POST", async () => {
      const newAccount = {
        ...mockAccountsData[0],
        id: "acc-new",
        account_name: "New Account",
      };
      mockPost.mockResolvedValueOnce({ data: newAccount });

      const { result } = renderHook(() => useCreateAccount(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          platform: "kdp",
          account_name: "New Account",
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith("/api/v1/publishing/accounts", {
        platform: "kdp",
        account_name: "New Account",
      });
      expect(result.current.data).toEqual(newAccount);
    });

    it("handles creation errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Duplicate account"));

      const { result } = renderHook(() => useCreateAccount(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          platform: "kdp",
          account_name: "Test",
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Duplicate account");
    });
  });

  // ---------- useExportEpub (mutation) ----------

  describe("useExportEpub", () => {
    it("exports a book as EPUB via POST", async () => {
      mockPost.mockResolvedValueOnce({ data: mockExportResponse });

      const { result } = renderHook(() => useExportEpub(), {
        wrapper: createWrapper(),
      });

      const exportReq = {
        book_id: "book-1",
        format: "epub" as const,
        chapters: [{ title: "Ch1", content: "Content", order: 1 }],
      };

      act(() => {
        result.current.mutate(exportReq);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/publishing/export/epub",
        exportReq
      );
      expect(result.current.data).toEqual(mockExportResponse);
    });

    it("handles export errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Export failed"));

      const { result } = renderHook(() => useExportEpub(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          book_id: "book-1",
          format: "epub",
          chapters: [],
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Export failed");
    });
  });

  // ---------- useExportPdf (mutation) ----------

  describe("useExportPdf", () => {
    it("exports a book as PDF via POST", async () => {
      const pdfResponse = { ...mockExportResponse, format: "pdf" };
      mockPost.mockResolvedValueOnce({ data: pdfResponse });

      const { result } = renderHook(() => useExportPdf(), {
        wrapper: createWrapper(),
      });

      const exportReq = {
        book_id: "book-1",
        format: "pdf" as const,
        chapters: [{ title: "Ch1", content: "Content", order: 1 }],
        trim_size: "6x9",
      };

      act(() => {
        result.current.mutate(exportReq);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/publishing/export/pdf",
        exportReq
      );
    });
  });

  // ---------- useBookMetadata (query) ----------

  describe("useBookMetadata", () => {
    it("fetches book metadata by ID", async () => {
      mockGet.mockResolvedValueOnce({ data: mockMetadataData });

      const { result } = renderHook(() => useBookMetadata("book-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books/book-1/metadata");
      expect(result.current.data).toEqual(mockMetadataData);
    });

    it("does not fetch when bookId is empty", async () => {
      const { result } = renderHook(() => useBookMetadata(""), {
        wrapper: createWrapper(),
      });

      // Query should be disabled and never fire
      expect(result.current.fetchStatus).toBe("idle");
      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles metadata fetch errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Not found"));

      const { result } = renderHook(() => useBookMetadata("book-missing"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Not found");
    });
  });

  // ---------- useUpdateMetadata (mutation) ----------

  describe("useUpdateMetadata", () => {
    it("updates book metadata via PATCH", async () => {
      const updatedMetadata = { ...mockMetadataData, title: "Updated Title" };
      mockPatch.mockResolvedValueOnce({ data: updatedMetadata });

      const { result } = renderHook(() => useUpdateMetadata("book-1"), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ title: "Updated Title" });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPatch).toHaveBeenCalledWith("/api/v1/books/book-1/metadata", {
        title: "Updated Title",
      });
      expect(result.current.data?.title).toBe("Updated Title");
    });
  });

  // ---------- useListings (list hook) ----------

  describe("useListings", () => {
    it("fetches listings from the API", async () => {
      mockGet.mockResolvedValueOnce({ data: mockListingsData });

      const { result } = renderHook(() => useListings(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/publishing/listings");
      expect(result.current.data).toEqual(mockListingsData);
      expect(result.current.data?.[0].status).toBe("active");
    });

    it("handles listings fetch errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useListings(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  // ---------- useSyncListing (mutation) ----------

  describe("useSyncListing", () => {
    it("syncs a listing via POST", async () => {
      const syncResponse = {
        listing_id: "lst-1",
        status: "syncing",
        message: "Sync started",
      };
      mockPost.mockResolvedValueOnce({ data: syncResponse });

      const { result } = renderHook(() => useSyncListing(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("lst-1");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/publishing/listings/lst-1/sync"
      );
      expect(result.current.data).toEqual(syncResponse);
    });
  });

  // ---------- useDeleteAccount (mutation) ----------

  describe("useDeleteAccount", () => {
    it("deletes an account via DELETE", async () => {
      mockDelete.mockResolvedValueOnce({});

      const { result } = renderHook(() => useDeleteAccount(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("acc-1");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockDelete).toHaveBeenCalledWith(
        "/api/v1/publishing/accounts/acc-1"
      );
    });

    it("handles deletion errors", async () => {
      mockDelete.mockRejectedValueOnce(new Error("Forbidden"));

      const { result } = renderHook(() => useDeleteAccount(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("acc-1");
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Forbidden");
    });
  });

  // ---------- useFormattingTemplates (query) ----------

  describe("useFormattingTemplates", () => {
    it("fetches formatting templates from the API", async () => {
      const templatesData = [
        {
          id: "tpl-1",
          org_id: null,
          name: "Standard Fiction",
          genre: "fiction",
          description: "Standard template",
          trim_size: "6x9",
          style_settings: {},
          is_builtin: true,
          created_at: "2025-01-01T00:00:00Z",
          updated_at: "2025-01-01T00:00:00Z",
        },
      ];
      mockGet.mockResolvedValueOnce({ data: templatesData });

      const { result } = renderHook(() => useFormattingTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/publishing/templates");
      expect(result.current.data).toEqual(templatesData);
    });
  });
});
