"use client";

import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import type { AgentTask, TaskStatus } from "../types";

const STATUS_STYLES: Record<TaskStatus, string> = {
  pending: "bg-gray-100 text-gray-800",
  running: "bg-blue-100 text-blue-800",
  awaiting_approval: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-600",
};

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "Pending",
  running: "Running",
  awaiting_approval: "Awaiting Approval",
  approved: "Approved",
  rejected: "Rejected",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

const PRIORITY_STYLES: Record<string, string> = {
  low: "text-gray-500",
  medium: "text-blue-500",
  high: "text-orange-500",
  critical: "text-red-600 font-semibold",
};

interface TaskListProps {
  tasks: AgentTask[];
  onSelect?: (task: AgentTask) => void;
  onApprove?: (task: AgentTask) => void;
  onReject?: (task: AgentTask) => void;
  onCancel?: (task: AgentTask) => void;
}

export function TaskList({
  tasks,
  onSelect,
  onApprove,
  onReject,
  onCancel,
}: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-dashed p-8 text-muted-foreground">
        No tasks found.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-accent/50 cursor-pointer"
          onClick={() => onSelect?.(task)}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium truncate">{task.title}</h4>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                  STATUS_STYLES[task.status]
                )}
              >
                {STATUS_LABELS[task.status]}
              </span>
              <span
                className={cn(
                  "text-xs",
                  PRIORITY_STYLES[task.priority]
                )}
              >
                {task.priority}
              </span>
            </div>
            <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
              <span>
                {formatDistanceToNow(new Date(task.created_at), {
                  addSuffix: true,
                })}
              </span>
              {task.tokens_used > 0 && (
                <span>{task.tokens_used.toLocaleString()} tokens</span>
              )}
              {task.cost_usd > 0 && (
                <span>${task.cost_usd.toFixed(4)}</span>
              )}
              {task.quality_score !== null && (
                <span>Quality: {(task.quality_score * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>

          {task.status === "awaiting_approval" && (
            <div className="flex gap-1 ml-2" onClick={(e) => e.stopPropagation()}>
              {onApprove && (
                <button
                  onClick={() => onApprove(task)}
                  className="rounded-md bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700"
                >
                  Approve
                </button>
              )}
              {onReject && (
                <button
                  onClick={() => onReject(task)}
                  className="rounded-md bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700"
                >
                  Reject
                </button>
              )}
            </div>
          )}

          {(task.status === "pending" || task.status === "running") &&
            onCancel && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCancel(task);
                }}
                className="ml-2 rounded-md border px-2 py-1 text-xs hover:bg-accent"
              >
                Cancel
              </button>
            )}
        </div>
      ))}
    </div>
  );
}
