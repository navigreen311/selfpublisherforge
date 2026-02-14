"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface RecentTasksListProps {
  tasks: any[];
  onViewOutput: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
}

function getStatusIcon(status: string): string {
  switch (status) {
    case "completed":
      return "✅";
    case "running":
    case "pending":
      return "⏳";
    case "failed":
    case "error":
      return "❌";
    default:
      return "⏳";
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-800";
    case "running":
    case "pending":
      return "bg-blue-100 text-blue-800";
    case "failed":
    case "error":
      return "bg-red-100 text-red-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
}

function formatTimeAgo(date: string | Date): string {
  const now = new Date();
  const past = new Date(date);
  const seconds = Math.floor((now.getTime() - past.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function formatTokens(tokens: number): string {
  if (tokens >= 1000000) {
    return (tokens / 1000000).toFixed(1) + "M";
  }
  if (tokens >= 1000) {
    return (tokens / 1000).toFixed(1) + "k";
  }
  return tokens.toString();
}

function renderStars(rating: number): string {
  return "⭐".repeat(Math.round(rating));
}

export function RecentTasksList({
  tasks,
  onViewOutput,
  onRetry,
}: RecentTasksListProps) {
  if (tasks.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          No recent tasks found
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <Card key={task.id} className="transition-shadow hover:shadow-md">
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-start gap-3">
                  <span className="text-xl" aria-label={task.status}>
                    {getStatusIcon(task.status)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-semibold text-sm">
                        {task.agent_name || "Unknown Agent"}
                      </h4>
                      <Badge
                        variant="outline"
                        className={cn("text-xs", getStatusColor(task.status))}
                      >
                        {task.status}
                      </Badge>
                      {task.task_type && (
                        <span className="text-xs text-muted-foreground">
                          {task.task_type}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-muted-foreground mt-1">
                      {formatTimeAgo(task.created_at || task.updated_at)}
                    </p>

                    {task.description && (
                      <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                        {task.description}
                      </p>
                    )}

                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground flex-wrap">
                      {task.total_tokens && (
                        <span>Tokens: {formatTokens(task.total_tokens)}</span>
                      )}
                      {task.total_cost && (
                        <span>Cost: ${task.total_cost.toFixed(3)}</span>
                      )}
                      {task.rating && task.rating > 0 && (
                        <span className="flex items-center gap-1">
                          {renderStars(task.rating)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 shrink-0">
                {task.status === "running" || task.status === "pending" ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onViewOutput(task.id)}
                  >
                    View Progress
                  </Button>
                ) : (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onViewOutput(task.id)}
                    >
                      View Output
                    </Button>
                    {task.status === "failed" && onRetry && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onRetry(task.id)}
                      >
                        Retry
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
