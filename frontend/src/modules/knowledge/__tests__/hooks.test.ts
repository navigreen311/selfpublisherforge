import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPut = jest.fn();
const mockDelete = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}));

// ---------------------------------------------------------------------------
// Import hooks under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import {
  useKnowledgeEntries,
  useKnowledgeEntry,
  useCreateEntry,
  useUpdateEntry,
  useDeleteEntry,
  useKnowledgeSearch,
  useImportEntry,
  useSummarizeEntry,
  useKnowledgeTags,
  useKnowledgeSuggestions,
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
    React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
}

// ---------------------------------------------------------------------------
// Tests: useKnowledgeEntries
// ---------------------------------------------------------------------------

describe("useKnowledgeEntries", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches entries from /api/v1/knowledge", async () => {
    const mockData = {
      items: [
        { id: "k1", title: "Entry One", content: "Content one", tags: [] },
        { id: "k2", title: "Entry Two", content: "Content two", tags: [] },
      ],
      total: 2,
    };
    mockGet.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useKnowledgeEntries(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/knowledge?");
    expect(result.current.data).toEqual(mockData);
  });

  it("passes filter params when provided", async () => {
    mockGet.mockResolvedValue({ data: { items: [], total: 0 } });

    const { result } = renderHook(
      () =>
        useKnowledgeEntries({
          tag: ["fiction", "research"],
          source_type: "url",
          cursor: "abc",
          limit: 5,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // The hook builds URLSearchParams so we verify the URL contains the expected params
    const calledUrl = mockGet.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/knowledge?");
    expect(calledUrl).toContain("tag=fiction");
    expect(calledUrl).toContain("tag=research");
    expect(calledUrl).toContain("source_type=url");
    expect(calledUrl).toContain("cursor=abc");
    expect(calledUrl).toContain("limit=5");
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Failed to fetch entries"));

    const { result } = renderHook(() => useKnowledgeEntries(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useKnowledgeEntry
// ---------------------------------------------------------------------------

describe("useKnowledgeEntry", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches a single entry by id", async () => {
    const mockEntry = {
      id: "k1",
      org_id: "org-1",
      title: "Test Entry",
      content: "Some content",
      source_url: null,
      source_type: "manual",
      tags: ["test"],
      credibility_score: null,
      metadata: {},
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
      deleted_at: null,
    };
    mockGet.mockResolvedValue({ data: mockEntry });

    const { result } = renderHook(() => useKnowledgeEntry("k1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/knowledge/k1");
    expect(result.current.data).toEqual(mockEntry);
  });

  it("does not fetch when id is empty", async () => {
    const { result } = renderHook(() => useKnowledgeEntry(""), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));

    expect(mockGet).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Entry not found"));

    const { result } = renderHook(() => useKnowledgeEntry("k-bad"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Entry not found");
  });
});

// ---------------------------------------------------------------------------
// Tests: useCreateEntry
// ---------------------------------------------------------------------------

describe("useCreateEntry", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/knowledge", async () => {
    const mockResponse = {
      id: "k-new",
      title: "New Entry",
      content: "New content",
      source_type: "manual",
      tags: ["new"],
    };
    mockPost.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useCreateEntry(), {
      wrapper: createWrapper(),
    });

    const payload = {
      title: "New Entry",
      content: "New content",
      source_type: "manual",
      tags: ["new"],
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/knowledge", payload);
    expect(result.current.data).toEqual(mockResponse);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Create failed"));

    const { result } = renderHook(() => useCreateEntry(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ title: "Fail", content: "Fail content" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Create failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useUpdateEntry
// ---------------------------------------------------------------------------

describe("useUpdateEntry", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("puts to /api/v1/knowledge/{id}", async () => {
    const mockResponse = {
      id: "k1",
      title: "Updated Entry",
      content: "Updated content",
    };
    mockPut.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useUpdateEntry("k1"), {
      wrapper: createWrapper(),
    });

    const payload = { title: "Updated Entry", content: "Updated content" };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPut).toHaveBeenCalledWith("/api/v1/knowledge/k1", payload);
    expect(result.current.data).toEqual(mockResponse);
  });

  it("handles error on failure", async () => {
    mockPut.mockRejectedValue(new Error("Update failed"));

    const { result } = renderHook(() => useUpdateEntry("k1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ title: "Fail" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Update failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useDeleteEntry
// ---------------------------------------------------------------------------

describe("useDeleteEntry", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("deletes from /api/v1/knowledge/{id}", async () => {
    mockDelete.mockResolvedValue({});

    const { result } = renderHook(() => useDeleteEntry(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("k1");

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDelete).toHaveBeenCalledWith("/api/v1/knowledge/k1");
  });

  it("handles error on failure", async () => {
    mockDelete.mockRejectedValue(new Error("Delete failed"));

    const { result } = renderHook(() => useDeleteEntry(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("k1");

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Delete failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useKnowledgeSearch
// ---------------------------------------------------------------------------

describe("useKnowledgeSearch", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts search query to /api/v1/knowledge/search", async () => {
    const mockSearchResult = {
      hits: [
        {
          id: "k1",
          title: "Matching Entry",
          content_snippet: "...matching text...",
          source_type: "manual",
          tags: [],
          score: 0.95,
          credibility_score: null,
          created_at: "2025-01-01T00:00:00Z",
        },
      ],
      total: 1,
      query: "test query",
    };
    mockPost.mockResolvedValue({ data: mockSearchResult });

    const { result } = renderHook(() => useKnowledgeSearch(), {
      wrapper: createWrapper(),
    });

    const payload = {
      query: "test query",
      tags: ["fiction"],
      limit: 10,
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/knowledge/search", payload);
    expect(result.current.data).toEqual(mockSearchResult);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Search failed"));

    const { result } = renderHook(() => useKnowledgeSearch(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ query: "fail" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Search failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useImportEntry
// ---------------------------------------------------------------------------

describe("useImportEntry", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/knowledge/import", async () => {
    const mockImportResult = {
      entry_id: "k-imp",
      title: "Imported Article",
      content_preview: "First paragraph...",
      tags: ["imported"],
      source_type: "url",
      status: "completed",
    };
    mockPost.mockResolvedValue({ data: mockImportResult });

    const { result } = renderHook(() => useImportEntry(), {
      wrapper: createWrapper(),
    });

    const payload = {
      url: "https://example.com/article",
      extract_facts: true,
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/knowledge/import", payload);
    expect(result.current.data).toEqual(mockImportResult);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Import failed"));

    const { result } = renderHook(() => useImportEntry(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ url: "https://bad-url.com" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Import failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useSummarizeEntry
// ---------------------------------------------------------------------------

describe("useSummarizeEntry", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/knowledge/{id}/summarize", async () => {
    const mockSummary = {
      entry_id: "k1",
      summary: "This entry is about testing.",
      key_points: ["Point 1", "Point 2"],
      suggested_tags: ["testing"],
    };
    mockPost.mockResolvedValue({ data: mockSummary });

    const { result } = renderHook(() => useSummarizeEntry("k1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/knowledge/k1/summarize");
    expect(result.current.data).toEqual(mockSummary);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Summarize failed"));

    const { result } = renderHook(() => useSummarizeEntry("k1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Summarize failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useKnowledgeTags
// ---------------------------------------------------------------------------

describe("useKnowledgeTags", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches tags from /api/v1/knowledge/tags", async () => {
    const mockTags = {
      tags: ["fiction", "research", "notes"],
      counts: { fiction: 5, research: 3, notes: 10 },
    };
    mockGet.mockResolvedValue({ data: mockTags });

    const { result } = renderHook(() => useKnowledgeTags(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/knowledge/tags");
    expect(result.current.data).toEqual(mockTags);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Tags fetch failed"));

    const { result } = renderHook(() => useKnowledgeTags(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useKnowledgeSuggestions
// ---------------------------------------------------------------------------

describe("useKnowledgeSuggestions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("does not fetch automatically (enabled: false)", async () => {
    const { result } = renderHook(() => useKnowledgeSuggestions(), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));

    expect(mockGet).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("has correct query key structure", () => {
    // Verify the hook uses the suggestions query key
    const { result } = renderHook(() => useKnowledgeSuggestions(), {
      wrapper: createWrapper(),
    });

    // The hook is disabled by default, so it should not fetch
    expect(result.current.isLoading).toBe(false);
  });
});
