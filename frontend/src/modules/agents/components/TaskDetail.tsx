"use client";

import { cn } from "@/lib/utils";
import { format } from "date-fns";
import type { AgentTask } from "../types";

interface TaskDetailProps {
  task: AgentTask;
  onApprove?: () => void;
  onReject?: () => void;
  onCancel?: () => void;
  onClose?: () => void;
}

export function TaskDetail({
  task,
  onApprove,
  onReject,
  onCancel,
  onClose,
}: TaskDetailProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">{task.title}</h2>
          {task.description && (
            <p className="mt-1 text-muted-foreground">{task.description}</p>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-md border px-3 py-1 text-sm hover:bg-accent"
          >
            Close
          </button>
        )}
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 rounded-lg border p-4 md:grid-cols-4">
        <div>
          <dt className="text-xs font-medium text-muted-foreground">Status</dt>
          <dd className="mt-1 text-sm font-semibold capitalize">
            {task.status.replace(/_/g, " ")}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-muted-foreground">Priority</dt>
          <dd className="mt-1 text-sm capitalize">{task.priority}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-muted-foreground">Tokens Used</dt>
          <dd className="mt-1 text-sm">{task.tokens_used.toLocaleString()}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-muted-foreground">Cost</dt>
          <dd className="mt-1 text-sm">${task.cost_usd.toFixed(4)}</dd>
        </div>
        {task.quality_score !== null && (
          <div>
            <dt className="text-xs font-medium text-muted-foreground">
              Quality Score
            </dt>
            <dd className="mt-1 text-sm">
              {(task.quality_score * 100).toFixed(0)}%
            </dd>
          </div>
        )}
        <div>
          <dt className="text-xs font-medium text-muted-foreground">Created</dt>
          <dd className="mt-1 text-sm">
            {format(new Date(task.created_at), "MMM d, yyyy h:mm a")}
          </dd>
        </div>
        {task.started_at && (
          <div>
            <dt className="text-xs font-medium text-muted-foreground">Started</dt>
            <dd className="mt-1 text-sm">
              {format(new Date(task.started_at), "MMM d, yyyy h:mm a")}
            </dd>
          </div>
        )}
        {task.completed_at && (
          <div>
            <dt className="text-xs font-medium text-muted-foreground">
              Completed
            </dt>
            <dd className="mt-1 text-sm">
              {format(new Date(task.completed_at), "MMM d, yyyy h:mm a")}
            </dd>
          </div>
        )}
      </div>

      {/* Input Data */}
      {task.input_data && Object.keys(task.input_data).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-2">Input</h3>
          <pre className="rounded-lg bg-muted p-4 text-sm overflow-auto max-h-64">
            {JSON.stringify(task.input_data, null, 2)}
          </pre>
        </div>
      )}

      {/* Output Data */}
      {task.output_data && (
        <div>
          <h3 className="text-sm font-semibold mb-2">Output</h3>
          {task.output_data.text ? (
            <div className="rounded-lg bg-muted p-4 text-sm whitespace-pre-wrap">
              {String(task.output_data.text)}
            </div>
          ) : (
            <pre className="rounded-lg bg-muted p-4 text-sm overflow-auto max-h-64">
              {JSON.stringify(task.output_data, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Error */}
      {task.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h3 className="text-sm font-semibold text-red-800 mb-1">Error</h3>
          <p className="text-sm text-red-700">{task.error_message}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        {task.status === "awaiting_approval" && (
          <>
            {onApprove && (
              <button
                onClick={onApprove}
                className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Approve
              </button>
            )}
            {onReject && (
              <button
                onClick={onReject}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Reject
              </button>
            )}
          </>
        )}
        {(task.status === "pending" || task.status === "running") && onCancel && (
          <button
            onClick={onCancel}
            className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            Cancel Task
          </button>
        )}
      </div>
    </div>
  );
}
