/**
 * React Query hooks and WebSocket integration for the AI Agent System.
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type {
  Agent,
  AgentConfigUpdate,
  AgentListResponse,
  AgentTask,
  AuditListResponse,
  BudgetListResponse,
  BudgetStatus,
  BudgetUpdate,
  EmergencyStopResponse,
  TaskCreate,
  TaskListResponse,
  TaskStatus,
  WorkflowCreate,
  WorkflowListResponse,
  AgentWorkflow,
} from "./types";

const API_PREFIX = "/api/v1/agents";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const agentKeys = {
  all: ["agents"] as const,
  lists: () => [...agentKeys.all, "list"] as const,
  list: () => [...agentKeys.lists()] as const,
  config: (id: string) => [...agentKeys.all, "config", id] as const,
  tasks: () => [...agentKeys.all, "tasks"] as const,
  taskList: (filters?: Record<string, string>) =>
    [...agentKeys.tasks(), filters] as const,
  task: (id: string) => [...agentKeys.tasks(), id] as const,
  workflows: () => [...agentKeys.all, "workflows"] as const,
  workflow: (id: string) => [...agentKeys.workflows(), id] as const,
  budgets: () => [...agentKeys.all, "budgets"] as const,
  audit: (filters?: Record<string, string>) =>
    [...agentKeys.all, "audit", filters] as const,
};

// ---------------------------------------------------------------------------
// Agent hooks
// ---------------------------------------------------------------------------

export function useAgents() {
  return useQuery<AgentListResponse>({
    queryKey: agentKeys.list(),
    queryFn: async () => {
      const { data } = await api.get<AgentListResponse>(API_PREFIX);
      return data;
    },
  });
}

export function useAgentConfig(agentId: string) {
  return useQuery<Agent>({
    queryKey: agentKeys.config(agentId),
    queryFn: async () => {
      const { data } = await api.get<Agent>(
        `${API_PREFIX}/${agentId}/config`
      );
      return data;
    },
    enabled: !!agentId,
  });
}

export function useUpdateAgentConfig() {
  const queryClient = useQueryClient();

  return useMutation<Agent, Error, { agentId: string; updates: AgentConfigUpdate }>({
    mutationFn: async ({ agentId, updates }) => {
      const { data } = await api.patch<Agent>(
        `${API_PREFIX}/${agentId}/config`,
        updates
      );
      return data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.config(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: agentKeys.list() });
    },
  });
}

// ---------------------------------------------------------------------------
// Task hooks
// ---------------------------------------------------------------------------

export function useTasks(filters?: {
  status?: TaskStatus;
  agent_id?: string;
  cursor?: string;
  limit?: number;
}) {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.agent_id) params.set("agent_id", filters.agent_id);
  if (filters?.cursor) params.set("cursor", filters.cursor);
  if (filters?.limit) params.set("limit", String(filters.limit));

  return useQuery<TaskListResponse>({
    queryKey: agentKeys.taskList(
      filters ? Object.fromEntries(params) : undefined
    ),
    queryFn: async () => {
      const { data } = await api.get<TaskListResponse>(
        `${API_PREFIX}/tasks`,
        { params }
      );
      return data;
    },
  });
}

export function useTask(taskId: string) {
  return useQuery<AgentTask>({
    queryKey: agentKeys.task(taskId),
    queryFn: async () => {
      const { data } = await api.get<AgentTask>(
        `${API_PREFIX}/tasks/${taskId}`
      );
      return data;
    },
    enabled: !!taskId,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation<AgentTask, Error, TaskCreate>({
    mutationFn: async (payload) => {
      const { data } = await api.post<AgentTask>(
        `${API_PREFIX}/tasks`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.tasks() });
    },
  });
}

export function useApproveTask() {
  const queryClient = useQueryClient();

  return useMutation<
    AgentTask,
    Error,
    { taskId: string; feedback?: string }
  >({
    mutationFn: async ({ taskId, feedback }) => {
      const { data } = await api.post<AgentTask>(
        `${API_PREFIX}/tasks/${taskId}/approve`,
        { feedback }
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.task(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: agentKeys.tasks() });
    },
  });
}

export function useRejectTask() {
  const queryClient = useQueryClient();

  return useMutation<
    AgentTask,
    Error,
    { taskId: string; reason: string; regenerate?: boolean }
  >({
    mutationFn: async ({ taskId, reason, regenerate = false }) => {
      const { data } = await api.post<AgentTask>(
        `${API_PREFIX}/tasks/${taskId}/reject`,
        { reason, regenerate }
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.task(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: agentKeys.tasks() });
    },
  });
}

export function useCancelTask() {
  const queryClient = useQueryClient();

  return useMutation<AgentTask, Error, { taskId: string; reason?: string }>({
    mutationFn: async ({ taskId, reason }) => {
      const { data } = await api.post<AgentTask>(
        `${API_PREFIX}/tasks/${taskId}/cancel`,
        { reason }
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.task(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: agentKeys.tasks() });
    },
  });
}

// ---------------------------------------------------------------------------
// Workflow hooks
// ---------------------------------------------------------------------------

export function useWorkflows(cursor?: string, limit?: number) {
  const params = new URLSearchParams();
  if (cursor) params.set("cursor", cursor);
  if (limit) params.set("limit", String(limit));

  return useQuery<WorkflowListResponse>({
    queryKey: agentKeys.workflows(),
    queryFn: async () => {
      const { data } = await api.get<WorkflowListResponse>(
        `${API_PREFIX}/workflows`,
        { params }
      );
      return data;
    },
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation<AgentWorkflow, Error, WorkflowCreate>({
    mutationFn: async (payload) => {
      const { data } = await api.post<AgentWorkflow>(
        `${API_PREFIX}/workflows`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.workflows() });
    },
  });
}

// ---------------------------------------------------------------------------
// Budget hooks
// ---------------------------------------------------------------------------

export function useBudgets() {
  return useQuery<BudgetListResponse>({
    queryKey: agentKeys.budgets(),
    queryFn: async () => {
      const { data } = await api.get<BudgetListResponse>(
        `${API_PREFIX}/budgets`
      );
      return data;
    },
  });
}

export function useUpdateBudget() {
  const queryClient = useQueryClient();

  return useMutation<
    BudgetStatus,
    Error,
    { agentId: string; updates: BudgetUpdate }
  >({
    mutationFn: async ({ agentId, updates }) => {
      const { data } = await api.patch<BudgetStatus>(
        `${API_PREFIX}/budgets?agent_id=${agentId}`,
        updates
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.budgets() });
    },
  });
}

// ---------------------------------------------------------------------------
// Emergency stop
// ---------------------------------------------------------------------------

export function useEmergencyStop() {
  const queryClient = useQueryClient();

  return useMutation<EmergencyStopResponse, Error>({
    mutationFn: async () => {
      const { data } = await api.post<EmergencyStopResponse>(
        `${API_PREFIX}/emergency-stop`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: agentKeys.workflows() });
    },
  });
}

// ---------------------------------------------------------------------------
// Audit hooks
// ---------------------------------------------------------------------------

export function useAudit(filters?: {
  action?: string;
  cursor?: string;
  limit?: number;
}) {
  const params = new URLSearchParams();
  if (filters?.action) params.set("action", filters.action);
  if (filters?.cursor) params.set("cursor", filters.cursor);
  if (filters?.limit) params.set("limit", String(filters.limit));

  return useQuery<AuditListResponse>({
    queryKey: agentKeys.audit(
      filters ? Object.fromEntries(params) : undefined
    ),
    queryFn: async () => {
      const { data } = await api.get<AuditListResponse>(
        `${API_PREFIX}/audit`,
        { params }
      );
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// WebSocket hook for real-time task updates
// ---------------------------------------------------------------------------

export function useTaskUpdates(onUpdate: (task: AgentTask) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    const wsUrl =
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/agents/tasks";

    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;

    const url = token ? `${wsUrl}?token=${token}` : wsUrl;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "task_update" && data.task) {
          onUpdate(data.task as AgentTask);
        }
      } catch {
        // Ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [onUpdate]);

  useEffect(() => {
    connect();

    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
