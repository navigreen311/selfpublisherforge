import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPut = jest.fn();
const mockPatch = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
  },
}));

// ---------------------------------------------------------------------------
// Import hooks under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import {
  useGenerateStandaloneOutline,
  useBooks,
  useWritingSessions,
  useManuscript,
  useChapters,
  useRecordWritingSession,
  useGenerateOutline,
  useReadabilityScore,
  useCreateChapter,
  useUpdateChapter,
  useReorderChapters,
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
// Tests: useGenerateStandaloneOutline
// ---------------------------------------------------------------------------

describe("useGenerateStandaloneOutline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls correct endpoint /api/v1/writing/outline/generate", async () => {
    const mockResponse = {
      book_title: "Test Book",
      genre: "Fiction",
      total_chapters: 3,
      chapters: [],
      synopsis: "A test synopsis",
    };
    mockPost.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useGenerateStandaloneOutline(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      book_title: "Test Book",
      genre: "Fiction",
      num_chapters: 3,
      tone: "commercial",
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/writing/outline/generate",
      {
        book_title: "Test Book",
        genre: "Fiction",
        num_chapters: 3,
        tone: "commercial",
      }
    );
  });

  it("passes correct payload including optional fields", async () => {
    const mockResponse = {
      book_title: "My Novel",
      genre: "Romance",
      total_chapters: 10,
      chapters: [],
      synopsis: "A love story",
    };
    mockPost.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useGenerateStandaloneOutline(), {
      wrapper: createWrapper(),
    });

    const payload = {
      book_title: "My Novel",
      genre: "Romance",
      target_audience: "Women 25-45",
      num_chapters: 10,
      premise: "Two rivals fall in love",
      tone: "literary",
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/writing/outline/generate",
      payload
    );
    expect(result.current.data).toEqual(mockResponse);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useGenerateStandaloneOutline(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      book_title: "Fail Book",
      genre: "Fiction",
      num_chapters: 5,
      tone: "casual",
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Network error");
  });
});

// ---------------------------------------------------------------------------
// Tests: useBooks
// ---------------------------------------------------------------------------

describe("useBooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches books from /api/v1/books", async () => {
    const mockBooksData = [
      { id: "b1", title: "Book One", status: "draft" },
      { id: "b2", title: "Book Two", status: "writing" },
    ];
    mockGet.mockResolvedValue({ data: mockBooksData });

    const { result } = renderHook(() => useBooks(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/books");
    expect(result.current.data).toEqual(mockBooksData);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Failed to fetch books"));

    const { result } = renderHook(() => useBooks(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useWritingSessions
// ---------------------------------------------------------------------------

describe("useWritingSessions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches all writing sessions from /api/v1/writing-sessions", async () => {
    const mockSessionsData = [
      {
        id: "s1",
        user_id: "u1",
        book_id: "b1",
        words_written: 500,
        duration_minutes: 30,
        created_at: "2025-01-01T00:00:00Z",
      },
    ];
    mockGet.mockResolvedValue({ data: mockSessionsData });

    const { result } = renderHook(() => useWritingSessions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/writing-sessions", {
      params: {},
    });
    expect(result.current.data).toEqual(mockSessionsData);
  });

  it("passes book_id as param when provided", async () => {
    mockGet.mockResolvedValue({ data: [] });

    const { result } = renderHook(() => useWritingSessions("book-123"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/writing-sessions", {
      params: { book_id: "book-123" },
    });
  });
});

// ---------------------------------------------------------------------------
// Tests: useManuscript
// ---------------------------------------------------------------------------

describe("useManuscript", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches manuscript for a given book ID", async () => {
    const mockManuscript = {
      book_id: "b1",
      title: "Test",
      chapters: [],
      total_word_count: 0,
    };
    mockGet.mockResolvedValue({ data: mockManuscript });

    const { result } = renderHook(() => useManuscript("b1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/books/b1/manuscript");
    expect(result.current.data).toEqual(mockManuscript);
  });

  it("does not fetch when bookId is empty", async () => {
    const { result } = renderHook(() => useManuscript(""), {
      wrapper: createWrapper(),
    });

    // Wait a tick to ensure it stays in its initial state
    await new Promise((r) => setTimeout(r, 50));

    expect(mockGet).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe("idle");
  });
});

// ---------------------------------------------------------------------------
// Tests: useChapters
// ---------------------------------------------------------------------------

describe("useChapters", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches chapters for a given book ID", async () => {
    const mockChapters = [
      { id: "ch1", book_id: "b1", title: "Chapter 1", content: "", order: 1 },
    ];
    mockGet.mockResolvedValue({ data: mockChapters });

    const { result } = renderHook(() => useChapters("b1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      "/api/v1/books/b1/manuscript/chapters"
    );
    expect(result.current.data).toEqual(mockChapters);
  });
});

// ---------------------------------------------------------------------------
// Tests: useRecordWritingSession
// ---------------------------------------------------------------------------

describe("useRecordWritingSession", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts writing session to /api/v1/writing-sessions", async () => {
    const mockSessionResponse = { id: "s1", book_id: "b1", words_written: 200 };
    mockPost.mockResolvedValue({ data: mockSessionResponse });

    const { result } = renderHook(() => useRecordWritingSession(), {
      wrapper: createWrapper(),
    });

    const payload = {
      book_id: "b1",
      words_written: 200,
      duration_minutes: 15,
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/writing-sessions", payload);
  });

  it("handles error when recording session fails", async () => {
    mockPost.mockRejectedValue(new Error("Session recording failed"));

    const { result } = renderHook(() => useRecordWritingSession(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      book_id: "b1",
      words_written: 100,
      duration_minutes: 10,
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useGenerateOutline (book-scoped)
// ---------------------------------------------------------------------------

describe("useGenerateOutline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/books/{bookId}/outline/generate", async () => {
    const mockResponse = {
      book_id: "b1",
      chapters: [],
      summary: "Outline summary",
      generated_at: "2025-01-01T00:00:00Z",
    };
    mockPost.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useGenerateOutline("b1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ instructions: "Make it epic" });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/books/b1/outline/generate",
      { instructions: "Make it epic" }
    );
  });
});

// ---------------------------------------------------------------------------
// Tests: useReadabilityScore
// ---------------------------------------------------------------------------

describe("useReadabilityScore", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches readability score for a book", async () => {
    const mockScore = {
      flesch_kincaid_grade: 8.5,
      flesch_reading_ease: 65,
      word_count: 5000,
      reading_level: "8th Grade",
    };
    mockGet.mockResolvedValue({ data: mockScore });

    const { result } = renderHook(() => useReadabilityScore("b1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      "/api/v1/books/b1/manuscript/readability-score"
    );
    expect(result.current.data).toEqual(mockScore);
  });
});

// ---------------------------------------------------------------------------
// Tests: useCreateChapter
// ---------------------------------------------------------------------------

describe("useCreateChapter", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to create chapter endpoint", async () => {
    const mockChapter = {
      id: "ch-new",
      book_id: "b1",
      title: "New Chapter",
      content: "",
      order: 1,
    };
    mockPost.mockResolvedValue({ data: mockChapter });

    const { result } = renderHook(() => useCreateChapter("b1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ title: "New Chapter", content: "Hello world" });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/books/b1/manuscript/chapters",
      { title: "New Chapter", content: "Hello world" }
    );
  });
});

// ---------------------------------------------------------------------------
// Tests: useUpdateChapter
// ---------------------------------------------------------------------------

describe("useUpdateChapter", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("puts to update chapter endpoint", async () => {
    const mockUpdated = {
      id: "ch1",
      book_id: "b1",
      title: "Updated Title",
      content: "Updated content",
    };
    mockPut.mockResolvedValue({ data: mockUpdated });

    const { result } = renderHook(() => useUpdateChapter("b1", "ch1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ title: "Updated Title", content: "Updated content" });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPut).toHaveBeenCalledWith(
      "/api/v1/books/b1/manuscript/chapters/ch1",
      { title: "Updated Title", content: "Updated content" }
    );
  });
});

// ---------------------------------------------------------------------------
// Tests: useReorderChapters
// ---------------------------------------------------------------------------

describe("useReorderChapters", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("patches to reorder chapters endpoint", async () => {
    const reordered = [
      { id: "ch2", order: 1 },
      { id: "ch1", order: 2 },
    ];
    mockPatch.mockResolvedValue({ data: reordered });

    const { result } = renderHook(() => useReorderChapters("b1"), {
      wrapper: createWrapper(),
    });

    const payload = [
      { chapter_id: "ch2", order: 1 },
      { chapter_id: "ch1", order: 2 },
    ];
    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPatch).toHaveBeenCalledWith(
      "/api/v1/books/b1/manuscript/chapters/reorder",
      { chapters: payload }
    );
  });
});
