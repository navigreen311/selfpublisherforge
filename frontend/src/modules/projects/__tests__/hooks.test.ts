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
  useProjects,
  useProject,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  projectKeys,
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

const mockProject = {
  id: "proj-1",
  title: "My Book Project",
  type: "book" as const,
  status: "draft" as const,
  settings: null,
  pen_name_id: null,
  books: [
    { id: "book-1", title: "My First Book", format: "ebook", status: "draft" },
  ],
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const mockProjectsList = [
  mockProject,
  {
    id: "proj-2",
    title: "Series Project",
    type: "series" as const,
    status: "active" as const,
    settings: { genre: "fantasy" },
    pen_name_id: "pen-1",
    books: [
      { id: "book-2", title: "Book Two", format: "paperback", status: "active" },
      { id: "book-3", title: "Book Three", format: "ebook", status: "draft" },
    ],
    created_at: "2025-02-01T00:00:00Z",
    updated_at: "2025-03-01T00:00:00Z",
  },
];

const mockCreatedProject = {
  id: "proj-new",
  title: "New Project",
  type: "book" as const,
  status: "draft" as const,
  settings: null,
  pen_name_id: null,
  books: [],
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-01T00:00:00Z",
};

const mockUpdatedProject = {
  ...mockProject,
  title: "Updated Title",
  status: "active" as const,
  updated_at: "2025-06-01T00:00:00Z",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("Projects hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---------- Query key structure ----------

  describe("projectKeys", () => {
    it("generates correct keys for all", () => {
      expect(projectKeys.all).toEqual(["projects"]);
    });

    it("generates correct keys for list without filters", () => {
      expect(projectKeys.list()).toEqual(["projects", "list", undefined]);
    });

    it("generates correct keys for list with filters", () => {
      expect(projectKeys.list({ status: "active", search: "book" })).toEqual([
        "projects",
        "list",
        { status: "active", search: "book" },
      ]);
    });

    it("generates correct keys for detail", () => {
      expect(projectKeys.detail("proj-1")).toEqual([
        "projects",
        "detail",
        "proj-1",
      ]);
    });
  });

  // ---------- useProjects ----------

  describe("useProjects", () => {
    it("fetches projects list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockProjectsList });

      const { result } = renderHook(() => useProjects(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books", { params: {} });
      expect(result.current.data).toHaveLength(2);
      expect(result.current.data?.[0].title).toBe("My Book Project");
    });

    it("passes status filter parameter", async () => {
      mockGet.mockResolvedValueOnce({ data: [mockProjectsList[1]] });

      const { result } = renderHook(
        () => useProjects({ status: "active" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books", {
        params: { status: "active" },
      });
    });

    it("passes search filter parameter", async () => {
      mockGet.mockResolvedValueOnce({ data: [mockProject] });

      const { result } = renderHook(
        () => useProjects({ search: "My Book" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books", {
        params: { search: "My Book" },
      });
    });

    it("does not pass status param when status is 'all'", async () => {
      mockGet.mockResolvedValueOnce({ data: mockProjectsList });

      const { result } = renderHook(
        () => useProjects({ status: "all" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books", { params: {} });
    });

    it("passes both status and search filters", async () => {
      mockGet.mockResolvedValueOnce({ data: [] });

      const { result } = renderHook(
        () => useProjects({ status: "draft", search: "test" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books", {
        params: { status: "draft", search: "test" },
      });
    });

    it("handles errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useProjects(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Server error");
    });
  });

  // ---------- useProject ----------

  describe("useProject", () => {
    it("fetches a single project by id", async () => {
      mockGet.mockResolvedValueOnce({ data: mockProject });

      const { result } = renderHook(() => useProject("proj-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/books/proj-1");
      expect(result.current.data?.title).toBe("My Book Project");
      expect(result.current.data?.books).toHaveLength(1);
    });

    it("does not fetch when id is empty", async () => {
      const { result } = renderHook(() => useProject(""), {
        wrapper: createWrapper(),
      });

      await waitFor(() =>
        expect(result.current.fetchStatus).toBe("idle")
      );

      expect(mockGet).not.toHaveBeenCalled();
    });

    it("handles errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Not found"));

      const { result } = renderHook(() => useProject("proj-invalid"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Not found");
    });
  });

  // ---------- useCreateProject ----------

  describe("useCreateProject", () => {
    it("creates a project via POST", async () => {
      mockPost.mockResolvedValueOnce({ data: mockCreatedProject });

      const { result } = renderHook(() => useCreateProject(), {
        wrapper: createWrapper(),
      });

      const createData = {
        title: "New Project",
        type: "book" as const,
        genre: "fiction",
        pen_name: "Author X",
        description: "A new book project",
      };

      act(() => {
        result.current.mutate(createData);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith("/api/v1/books", createData);
      expect(result.current.data?.id).toBe("proj-new");
      expect(result.current.data?.title).toBe("New Project");
    });

    it("handles creation errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Validation error"));

      const { result } = renderHook(() => useCreateProject(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ title: "", type: "book" });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Validation error");
    });
  });

  // ---------- useUpdateProject ----------

  describe("useUpdateProject", () => {
    it("updates a project via PATCH", async () => {
      mockPatch.mockResolvedValueOnce({ data: mockUpdatedProject });

      const { result } = renderHook(() => useUpdateProject(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          id: "proj-1",
          data: { title: "Updated Title", status: "active" },
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPatch).toHaveBeenCalledWith("/api/v1/books/proj-1", {
        title: "Updated Title",
        status: "active",
      });
      expect(result.current.data?.title).toBe("Updated Title");
      expect(result.current.data?.status).toBe("active");
    });

    it("handles update errors", async () => {
      mockPatch.mockRejectedValueOnce(new Error("Forbidden"));

      const { result } = renderHook(() => useUpdateProject(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          id: "proj-1",
          data: { title: "Bad Update" },
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Forbidden");
    });
  });

  // ---------- useDeleteProject ----------

  describe("useDeleteProject", () => {
    it("deletes a project via DELETE", async () => {
      mockDelete.mockResolvedValueOnce({});

      const { result } = renderHook(() => useDeleteProject(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("proj-1");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockDelete).toHaveBeenCalledWith("/api/v1/books/proj-1");
    });

    it("handles delete errors", async () => {
      mockDelete.mockRejectedValueOnce(new Error("Project not found"));

      const { result } = renderHook(() => useDeleteProject(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("proj-invalid");
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Project not found");
    });
  });

  // ---------- Data structure correctness ----------

  describe("data structure correctness", () => {
    it("verifies project data structure is preserved", async () => {
      mockGet.mockResolvedValueOnce({ data: mockProject });

      const { result } = renderHook(() => useProject("proj-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const project = result.current.data!;
      expect(typeof project.id).toBe("string");
      expect(typeof project.title).toBe("string");
      expect(["book", "series", "course"]).toContain(project.type);
      expect(["draft", "active", "archived", "completed"]).toContain(
        project.status
      );
      expect(project.books).toBeInstanceOf(Array);
    });

    it("verifies book summary structure within project", async () => {
      mockGet.mockResolvedValueOnce({ data: mockProject });

      const { result } = renderHook(() => useProject("proj-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const project = result.current.data!;
      project.books.forEach((book) => {
        expect(book).toHaveProperty("id");
        expect(book).toHaveProperty("title");
        expect(book).toHaveProperty("format");
        expect(book).toHaveProperty("status");
        expect(typeof book.id).toBe("string");
        expect(typeof book.title).toBe("string");
      });
    });

    it("verifies projects list structure", async () => {
      mockGet.mockResolvedValueOnce({ data: mockProjectsList });

      const { result } = renderHook(() => useProjects(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const projects = result.current.data!;
      expect(projects).toBeInstanceOf(Array);
      expect(projects.length).toBeGreaterThan(0);
      projects.forEach((project) => {
        expect(project).toHaveProperty("id");
        expect(project).toHaveProperty("title");
        expect(project).toHaveProperty("type");
        expect(project).toHaveProperty("status");
        expect(project).toHaveProperty("books");
      });
    });
  });
});
