import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

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
// Mock the auth store
// ---------------------------------------------------------------------------

const mockUser = { org_id: "org-123", id: "user-1", email: "test@test.com" };

jest.mock("@/lib/store", () => ({
  useAuthStore: () => ({ user: mockUser }),
}));

// ---------------------------------------------------------------------------
// Import hooks under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import {
  usePipelines,
  usePipeline,
  useTimeline,
  usePipelineTemplates,
  useCreatePipeline,
  useUpdatePipeline,
  useAddTask,
  useUpdateTask,
  useCreateTemplate,
  pipelineKeys,
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
// Tests: pipelineKeys (query key structure)
// ---------------------------------------------------------------------------

describe("pipelineKeys", () => {
  it("has correct 'all' key", () => {
    expect(pipelineKeys.all).toEqual(["pipelines"]);
  });

  it("has correct 'lists' key", () => {
    expect(pipelineKeys.lists()).toEqual(["pipelines", "list"]);
  });

  it("has correct 'list' key with filters", () => {
    const filters = { page: 1, pageSize: 20 };
    expect(pipelineKeys.list(filters)).toEqual([
      "pipelines",
      "list",
      filters,
    ]);
  });

  it("has correct 'details' key", () => {
    expect(pipelineKeys.details()).toEqual(["pipelines", "detail"]);
  });

  it("has correct 'detail' key with id", () => {
    expect(pipelineKeys.detail("p1")).toEqual(["pipelines", "detail", "p1"]);
  });

  it("has correct 'timeline' key with id", () => {
    expect(pipelineKeys.timeline("p1")).toEqual([
      "pipelines",
      "timeline",
      "p1",
    ]);
  });

  it("has correct 'templates' key", () => {
    expect(pipelineKeys.templates()).toEqual(["pipelines", "templates"]);
  });
});

// ---------------------------------------------------------------------------
// Tests: usePipelines
// ---------------------------------------------------------------------------

describe("usePipelines", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches pipelines from /api/v1/pipelines", async () => {
    const mockData = {
      items: [
        { id: "p1", name: "Pipeline One", status: "active" },
        { id: "p2", name: "Pipeline Two", status: "draft" },
      ],
      total: 2,
      page: 1,
      page_size: 20,
      pages: 1,
    };
    mockGet.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => usePipelines(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/pipelines", {
      params: { org_id: "org-123", page: 1, page_size: 20 },
    });
    expect(result.current.data).toEqual(mockData);
  });

  it("passes status and bookId as params when provided", async () => {
    mockGet.mockResolvedValue({ data: { items: [], total: 0, page: 1, page_size: 10, pages: 0 } });

    const { result } = renderHook(() => usePipelines(2, 10, "active", "book-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/pipelines", {
      params: {
        org_id: "org-123",
        page: 2,
        page_size: 10,
        status: "active",
        book_id: "book-1",
      },
    });
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Failed to fetch pipelines"));

    const { result } = renderHook(() => usePipelines(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: usePipeline
// ---------------------------------------------------------------------------

describe("usePipeline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches a single pipeline by id", async () => {
    const mockPipeline = {
      id: "p1",
      org_id: "org-123",
      book_id: "b1",
      name: "My Pipeline",
      status: "active",
      settings: {},
      tasks: [],
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    };
    mockGet.mockResolvedValue({ data: mockPipeline });

    const { result } = renderHook(() => usePipeline("p1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/pipelines/p1", {
      params: { org_id: "org-123" },
    });
    expect(result.current.data).toEqual(mockPipeline);
  });

  it("does not fetch when id is empty", async () => {
    const { result } = renderHook(() => usePipeline(""), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));

    expect(mockGet).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Pipeline not found"));

    const { result } = renderHook(() => usePipeline("p-bad"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Pipeline not found");
  });
});

// ---------------------------------------------------------------------------
// Tests: useTimeline
// ---------------------------------------------------------------------------

describe("useTimeline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches timeline for a pipeline", async () => {
    const mockTimeline = {
      pipeline_id: "p1",
      pipeline_name: "My Pipeline",
      deadline: null,
      tasks: [],
      critical_path: [],
    };
    mockGet.mockResolvedValue({ data: mockTimeline });

    const { result } = renderHook(() => useTimeline("p1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/pipelines/p1/timeline", {
      params: { org_id: "org-123" },
    });
    expect(result.current.data).toEqual(mockTimeline);
  });

  it("does not fetch when id is empty", async () => {
    const { result } = renderHook(() => useTimeline(""), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));

    expect(mockGet).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Timeline fetch failed"));

    const { result } = renderHook(() => useTimeline("p1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: usePipelineTemplates
// ---------------------------------------------------------------------------

describe("usePipelineTemplates", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches templates from /api/v1/pipelines/templates", async () => {
    const mockTemplates = [
      {
        id: "t1",
        org_id: "org-123",
        name: "Standard Template",
        task_definitions: [],
        is_public: true,
        created_at: "2025-01-01T00:00:00Z",
        updated_at: "2025-01-01T00:00:00Z",
      },
    ];
    mockGet.mockResolvedValue({ data: mockTemplates });

    const { result } = renderHook(() => usePipelineTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/pipelines/templates", {
      params: { org_id: "org-123" },
    });
    expect(result.current.data).toEqual(mockTemplates);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Templates fetch failed"));

    const { result } = renderHook(() => usePipelineTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useCreatePipeline
// ---------------------------------------------------------------------------

describe("useCreatePipeline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/pipelines", async () => {
    const mockResponse = {
      id: "p-new",
      org_id: "org-123",
      book_id: "b1",
      name: "New Pipeline",
      status: "draft",
      settings: {},
      tasks: [],
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    };
    mockPost.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useCreatePipeline(), {
      wrapper: createWrapper(),
    });

    const payload = {
      name: "New Pipeline",
      book_id: "b1",
      description: "A test pipeline",
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/pipelines", payload, {
      params: { org_id: "org-123" },
    });
    expect(result.current.data).toEqual(mockResponse);
  });

  it("passes optional fields in payload", async () => {
    mockPost.mockResolvedValue({ data: { id: "p-new" } });

    const { result } = renderHook(() => useCreatePipeline(), {
      wrapper: createWrapper(),
    });

    const payload = {
      name: "Template Pipeline",
      book_id: "b1",
      deadline: "2025-06-01",
      template_id: "t1",
      settings: { auto_assign: true },
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/pipelines", payload, {
      params: { org_id: "org-123" },
    });
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Create failed"));

    const { result } = renderHook(() => useCreatePipeline(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: "Fail", book_id: "b1" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Create failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useUpdatePipeline
// ---------------------------------------------------------------------------

describe("useUpdatePipeline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("patches to /api/v1/pipelines/{id}", async () => {
    const mockResponse = {
      id: "p1",
      name: "Updated Pipeline",
      status: "active",
    };
    mockPatch.mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(() => useUpdatePipeline("p1"), {
      wrapper: createWrapper(),
    });

    const payload = { name: "Updated Pipeline", status: "active" as const };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPatch).toHaveBeenCalledWith("/api/v1/pipelines/p1", payload, {
      params: { org_id: "org-123" },
    });
    expect(result.current.data).toEqual(mockResponse);
  });

  it("handles error on failure", async () => {
    mockPatch.mockRejectedValue(new Error("Update failed"));

    const { result } = renderHook(() => useUpdatePipeline("p1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: "Fail" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Update failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useAddTask
// ---------------------------------------------------------------------------

describe("useAddTask", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/pipelines/{pipelineId}/tasks", async () => {
    const mockTask = {
      id: "task-new",
      pipeline_id: "p1",
      title: "Write Chapter 1",
      type: "writing",
      status: "pending",
      position: 0,
    };
    mockPost.mockResolvedValue({ data: mockTask });

    const { result } = renderHook(() => useAddTask("p1"), {
      wrapper: createWrapper(),
    });

    const payload = {
      title: "Write Chapter 1",
      type: "writing" as const,
      description: "Write the first chapter",
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/pipelines/p1/tasks",
      payload,
      { params: { org_id: "org-123" } }
    );
    expect(result.current.data).toEqual(mockTask);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Add task failed"));

    const { result } = renderHook(() => useAddTask("p1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ title: "Fail Task" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Add task failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useUpdateTask
// ---------------------------------------------------------------------------

describe("useUpdateTask", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("patches to /api/v1/pipelines/{pipelineId}/tasks/{taskId}", async () => {
    const mockUpdated = {
      id: "task-1",
      pipeline_id: "p1",
      title: "Updated Task",
      status: "completed",
    };
    mockPatch.mockResolvedValue({ data: mockUpdated });

    const { result } = renderHook(() => useUpdateTask("p1", "task-1"), {
      wrapper: createWrapper(),
    });

    const payload = { title: "Updated Task", status: "completed" as const };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPatch).toHaveBeenCalledWith(
      "/api/v1/pipelines/p1/tasks/task-1",
      payload,
      { params: { org_id: "org-123" } }
    );
    expect(result.current.data).toEqual(mockUpdated);
  });

  it("handles error on failure", async () => {
    mockPatch.mockRejectedValue(new Error("Update task failed"));

    const { result } = renderHook(() => useUpdateTask("p1", "task-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ status: "completed" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Update task failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useCreateTemplate
// ---------------------------------------------------------------------------

describe("useCreateTemplate", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to /api/v1/pipelines/templates", async () => {
    const mockTemplate = {
      id: "t-new",
      org_id: "org-123",
      name: "New Template",
      task_definitions: [],
      is_public: false,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    };
    mockPost.mockResolvedValue({ data: mockTemplate });

    const { result } = renderHook(() => useCreateTemplate(), {
      wrapper: createWrapper(),
    });

    const payload = {
      name: "New Template",
      description: "A reusable template",
      task_definitions: [
        { title: "Draft", type: "writing" as const, position: 0 },
        { title: "Edit", type: "editing" as const, position: 1 },
      ],
      is_public: false,
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/pipelines/templates",
      payload,
      { params: { org_id: "org-123" } }
    );
    expect(result.current.data).toEqual(mockTemplate);
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Template creation failed"));

    const { result } = renderHook(() => useCreateTemplate(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: "Fail Template" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Template creation failed");
  });
});
