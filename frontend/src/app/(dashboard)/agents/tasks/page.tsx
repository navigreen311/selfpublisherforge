"use client";

import { useState } from "react";
import {
  useTasks,
  useCreateTask,
  useApproveTask,
  useRejectTask,
  useCancelTask,
  useAgents,
} from "@/modules/agents/hooks";
import { TaskList } from "@/modules/agents/components/TaskList";
import { TaskDetail } from "@/modules/agents/components/TaskDetail";
import type { AgentTask, TaskStatus } from "@/modules/agents/types";

const STATUS_OPTIONS: { value: TaskStatus | ""; label: string }[] = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "running", label: "Running" },
  { value: "awaiting_approval", label: "Awaiting Approval" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
];

export default function TasksPage() {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("");
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskAgentId, setNewTaskAgentId] = useState("");
  const [newTaskDescription, setNewTaskDescription] = useState("");

  const { data: agentsData } = useAgents();
  const { data: tasksData, isLoading } = useTasks(
    statusFilter ? { status: statusFilter as TaskStatus } : undefined
  );
  const createTask = useCreateTask();
  const approveTask = useApproveTask();
  const rejectTask = useRejectTask();
  const cancelTask = useCancelTask();

  const tasks = tasksData?.items || [];
  const agents = agentsData?.items || [];

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !newTaskAgentId) return;
    createTask.mutate(
      {
        agent_id: newTaskAgentId,
        title: newTaskTitle,
        description: newTaskDescription || undefined,
      },
      {
        onSuccess: () => {
          setShowCreateForm(false);
          setNewTaskTitle("");
          setNewTaskDescription("");
          setNewTaskAgentId("");
        },
      }
    );
  };

  if (selectedTask) {
    return (
      <div className="space-y-4">
        <TaskDetail
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onApprove={() => {
            approveTask.mutate(
              { taskId: selectedTask.id },
              {
                onSuccess: (updatedTask) => {
                  setSelectedTask(updatedTask);
                },
              }
            );
          }}
          onReject={() => {
            const reason = prompt("Reason for rejection:");
            if (!reason) return;
            rejectTask.mutate(
              { taskId: selectedTask.id, reason },
              {
                onSuccess: (updatedTask) => {
                  setSelectedTask(updatedTask);
                },
              }
            );
          }}
          onCancel={() => {
            cancelTask.mutate(
              { taskId: selectedTask.id, reason: "Cancelled by user" },
              {
                onSuccess: (updatedTask) => {
                  setSelectedTask(updatedTask);
                },
              }
            );
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agent Tasks</h1>
          <p className="text-muted-foreground">
            View, approve, reject, and manage agent tasks.
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {showCreateForm ? "Cancel" : "New Task"}
        </button>
      </div>

      {/* Create task form */}
      {showCreateForm && (
        <form
          onSubmit={handleCreateTask}
          className="rounded-lg border p-4 space-y-3"
        >
          <h3 className="text-sm font-semibold">Create New Task</h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <label className="block text-xs font-medium mb-1">Agent</label>
              <select
                value={newTaskAgentId}
                onChange={(e) => setNewTaskAgentId(e.target.value)}
                className="w-full rounded-md border px-2 py-1.5 text-sm"
                required
              >
                <option value="">Select agent...</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Title</label>
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="Task title..."
                className="w-full rounded-md border px-2 py-1.5 text-sm"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">
              Description
            </label>
            <textarea
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              placeholder="Optional description..."
              className="w-full rounded-md border px-2 py-1.5 text-sm"
              rows={2}
            />
          </div>
          <button
            type="submit"
            disabled={createTask.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {createTask.isPending ? "Creating..." : "Create Task"}
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "")}
          className="rounded-md border px-3 py-1.5 text-sm"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className="text-sm text-muted-foreground">
          {tasksData?.total_count ?? 0} total tasks
        </span>
      </div>

      {/* Task list */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading tasks...</div>
      ) : (
        <TaskList
          tasks={tasks}
          onSelect={setSelectedTask}
          onApprove={(task) =>
            approveTask.mutate({ taskId: task.id })
          }
          onReject={(task) => {
            const reason = prompt("Reason for rejection:");
            if (reason) rejectTask.mutate({ taskId: task.id, reason });
          }}
          onCancel={(task) =>
            cancelTask.mutate({ taskId: task.id, reason: "Cancelled by user" })
          }
        />
      )}
    </div>
  );
}
