"use client";

import { formatDistanceToNow } from "date-fns";
import type { AuditEntry } from "../types";

const ACTION_LABELS: Record<string, string> = {
  task_created: "Task Created",
  task_started: "Task Started",
  task_completed: "Task Completed",
  task_failed: "Task Failed",
  task_approved: "Task Approved",
  task_rejected: "Task Rejected",
  task_cancelled: "Task Cancelled",
  workflow_created: "Workflow Created",
  workflow_started: "Workflow Started",
  workflow_completed: "Workflow Completed",
  workflow_failed: "Workflow Failed",
  config_updated: "Config Updated",
  budget_updated: "Budget Updated",
  budget_alert: "Budget Alert",
  emergency_stop: "Emergency Stop",
  permission_changed: "Permission Changed",
};

const ACTION_COLORS: Record<string, string> = {
  task_completed: "text-green-600",
  task_approved: "text-green-600",
  workflow_completed: "text-green-600",
  task_failed: "text-red-600",
  task_rejected: "text-red-600",
  workflow_failed: "text-red-600",
  emergency_stop: "text-red-600 font-semibold",
  budget_alert: "text-yellow-600",
  task_cancelled: "text-gray-500",
};

interface AuditLogProps {
  entries: AuditEntry[];
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export function AuditLog({ entries, onLoadMore, hasMore }: AuditLogProps) {
  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-dashed p-8 text-muted-foreground">
        No audit entries found.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {entries.map((entry) => (
        <div
          key={entry.id}
          className="flex items-start gap-3 rounded-lg border p-3 text-sm"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className={
                  ACTION_COLORS[entry.action] || "text-muted-foreground"
                }
              >
                {ACTION_LABELS[entry.action] || entry.action}
              </span>
              <span className="text-xs text-muted-foreground">
                on {entry.resource_type}
              </span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              <span>Actor: {entry.actor_type}</span>
              {entry.ip_address && (
                <span className="ml-2">IP: {entry.ip_address}</span>
              )}
              <span className="ml-2">
                {formatDistanceToNow(new Date(entry.created_at), {
                  addSuffix: true,
                })}
              </span>
            </div>
            {entry.details && Object.keys(entry.details).length > 0 && (
              <details className="mt-1">
                <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                  Details
                </summary>
                <pre className="mt-1 rounded bg-muted p-2 text-xs overflow-auto max-h-32">
                  {JSON.stringify(entry.details, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      ))}

      {hasMore && onLoadMore && (
        <button
          onClick={onLoadMore}
          className="w-full rounded-md border py-2 text-sm text-muted-foreground hover:bg-accent"
        >
          Load more
        </button>
      )}
    </div>
  );
}
