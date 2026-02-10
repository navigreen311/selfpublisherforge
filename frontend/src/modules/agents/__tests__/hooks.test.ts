import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ── Mock the api module ──────────────────────────────────────────────────

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

// Import hooks after mock
import {
  useAgents,
  useTasks,
  useWorkflows,
  useEmergencyStop,
  useBudgets,
  useCreateTask,
  useAudit,
  agentKeys,
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

const mockAgentsResponse = {
  items: [
    {
      id: "agent-1",
      org_id: "org-1",
      agent_type: "research",
      name: "Research Agent",
      description: "Handles research tasks",
      is_enabled: true,
      permission_level: "suggest",
      model_id: "gpt-4",
      system_prompt: null,
      max_tokens: 4096,
      temperature: 0.7,
      config: null,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
    {
      id: "agent-2",
      org_id: "org-1",
      agent_type: "editor",
      name: "Editor Agent",
      description: null,
      is_enabled: true,
      permission_level: "auto_execute_low",
      model_id: "gpt-4",
      system_prompt: null,
      max_tokens: 8192,
      temperature: 0.3,
      config: null,
      created_at: "2025-02-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  total_count: 2,
};

const mockTasksResponse = {
  items: [
    {
      id: "task-1",
      org_id: "org-1",
      agent_id: "agent-1",
      workflow_id: null,
      workflow_step_index: null,
      title: "Research Task",
      description: "Analyze data",
      status: "running",
      priority: "high",
      input_data: null,
      output_data: null,
      error_message: null,
      tokens_used: 500,
      cost_usd: 0.015,
      quality_score: null,
      created_by: "user-1",
      approved_by: null,
      started_at: "2025-06-01T00:00:00Z",
      completed_at: null,
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  next_cursor: null,
  has_more: false,
  total_count: 1,
};

const mockWorkflowsResponse = {
  items: [
    {
      id: "wf-1",
      org_id: "org-1",
      name: "Book Research Pipeline",
      description: "Research and outline workflow",
      status: "running",
      steps: [],
      current_step_index: 0,
      context: null,
      error_message: null,
      created_by: "user-1",
      started_at: "2025-06-01T00:00:00Z",
      completed_at: null,
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-06-01T00:00:00Z",
    },
  ],
  next_cursor: null,
  has_more: false,
  total_count: 1,
};

const mockBudgetsResponse = {
  items: [
    {
      id: "budget-1",
      org_id: "org-1",
      agent_id: "agent-1",
      daily_token_limit: 100000,
      daily_usd_limit: 5,
      monthly_usd_limit: 100,
      tokens_used_today: 5000,
      usd_used_today: 0.5,
      usd_used_this_month: 15,
      total_tokens_used: 500000,
      total_usd_used: 50,
      last_reset_daily: null,
      last_reset_monthly: null,
      daily_token_pct: 5,
      daily_usd_pct: 10,
      monthly_usd_pct: 15,
    },
  ],
};

const mockEmergencyStopResponse = {
  tasks_cancelled: 3,
  workflows_cancelled: 1,
  message: "Emergency stop executed successfully.",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("Agent hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── useAgents ──────────────────────────────────────────────────────

  describe("useAgents", () => {
    it("fetches agent list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockAgentsResponse });

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockAgentsResponse);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/agents");
    });

    it("handles fetch error for agents", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeTruthy();
    });
  });

  // ── useTasks ───────────────────────────────────────────────────────

  describe("useTasks", () => {
    it("fetches tasks list without filters", async () => {
      mockGet.mockResolvedValueOnce({ data: mockTasksResponse });

      const { result } = renderHook(() => useTasks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockTasksResponse);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/agents/tasks", {
        params: expect.any(URLSearchParams),
      });
    });

    it("passes filter parameters when provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockTasksResponse });

      const { result } = renderHook(
        () => useTasks({ status: "running", agent_id: "agent-1", limit: 10 }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const callArgs = mockGet.mock.calls[0];
      const params = callArgs[1].params as URLSearchParams;
      expect(params.get("status")).toBe("running");
      expect(params.get("agent_id")).toBe("agent-1");
      expect(params.get("limit")).toBe("10");
    });

    it("handles tasks fetch error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useTasks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  // ── useEmergencyStop ───────────────────────────────────────────────

  describe("useEmergencyStop", () => {
    it("executes emergency stop mutation successfully", async () => {
      mockPost.mockResolvedValueOnce({ data: mockEmergencyStopResponse });

      const { result } = renderHook(() => useEmergencyStop(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate(undefined);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockEmergencyStopResponse);
      expect(mockPost).toHaveBeenCalledWith("/api/v1/agents/emergency-stop");
    });

    it("handles emergency stop error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Stop failed"));

      const { result } = renderHook(() => useEmergencyStop(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate(undefined);
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeTruthy();
    });
  });

  // ── useWorkflows ───────────────────────────────────────────────────

  describe("useWorkflows", () => {
    it("fetches workflows list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockWorkflowsResponse });

      const { result } = renderHook(() => useWorkflows(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockWorkflowsResponse);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/agents/workflows", {
        params: expect.any(URLSearchParams),
      });
    });

    it("handles workflows fetch error", async () => {
      mockGet.mockRejectedValueOnce(new Error("Fetch failed"));

      const { result } = renderHook(() => useWorkflows(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  // ── useBudgets ─────────────────────────────────────────────────────

  describe("useBudgets", () => {
    it("fetches budgets list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockBudgetsResponse });

      const { result } = renderHook(() => useBudgets(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockBudgetsResponse);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/agents/budgets");
    });
  });

  // ── useCreateTask ──────────────────────────────────────────────────

  describe("useCreateTask", () => {
    it("creates a task successfully", async () => {
      const newTask = {
        id: "task-new",
        org_id: "org-1",
        agent_id: "agent-1",
        workflow_id: null,
        workflow_step_index: null,
        title: "New Task",
        description: "A new task",
        status: "pending",
        priority: "medium",
        input_data: null,
        output_data: null,
        error_message: null,
        tokens_used: 0,
        cost_usd: 0,
        quality_score: null,
        created_by: "user-1",
        approved_by: null,
        started_at: null,
        completed_at: null,
        created_at: "2025-06-01T00:00:00Z",
        updated_at: "2025-06-01T00:00:00Z",
      };
      mockPost.mockResolvedValueOnce({ data: newTask });

      const { result } = renderHook(() => useCreateTask(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          agent_id: "agent-1",
          title: "New Task",
          description: "A new task",
          priority: "medium",
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(newTask);
      expect(mockPost).toHaveBeenCalledWith("/api/v1/agents/tasks", {
        agent_id: "agent-1",
        title: "New Task",
        description: "A new task",
        priority: "medium",
      });
    });

    it("handles task creation error", async () => {
      mockPost.mockRejectedValueOnce(new Error("Creation failed"));

      const { result } = renderHook(() => useCreateTask(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          agent_id: "agent-1",
          title: "Failing Task",
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  // ── useAudit ───────────────────────────────────────────────────────

  describe("useAudit", () => {
    it("fetches audit log successfully", async () => {
      const mockAuditResponse = {
        items: [],
        next_cursor: null,
        has_more: false,
        total_count: 0,
      };
      mockGet.mockResolvedValueOnce({ data: mockAuditResponse });

      const { result } = renderHook(() => useAudit(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockAuditResponse);
      expect(mockGet).toHaveBeenCalledWith("/api/v1/agents/audit", {
        params: expect.any(URLSearchParams),
      });
    });

    it("passes filter parameters for audit", async () => {
      mockGet.mockResolvedValueOnce({
        data: { items: [], next_cursor: null, has_more: false, total_count: 0 },
      });

      const { result } = renderHook(
        () => useAudit({ action: "task_created", limit: 20 }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const callArgs = mockGet.mock.calls[0];
      const params = callArgs[1].params as URLSearchParams;
      expect(params.get("action")).toBe("task_created");
      expect(params.get("limit")).toBe("20");
    });
  });

  // ── agentKeys ──────────────────────────────────────────────────────

  describe("agentKeys", () => {
    it("generates correct query key shapes", () => {
      expect(agentKeys.all).toEqual(["agents"]);
      expect(agentKeys.lists()).toEqual(["agents", "list"]);
      expect(agentKeys.list()).toEqual(["agents", "list"]);
      expect(agentKeys.tasks()).toEqual(["agents", "tasks"]);
      expect(agentKeys.task("task-1")).toEqual(["agents", "tasks", "task-1"]);
      expect(agentKeys.workflows()).toEqual(["agents", "workflows"]);
      expect(agentKeys.workflow("wf-1")).toEqual(["agents", "workflows", "wf-1"]);
      expect(agentKeys.budgets()).toEqual(["agents", "budgets"]);
      expect(agentKeys.config("agent-1")).toEqual(["agents", "config", "agent-1"]);
    });
  });
});
