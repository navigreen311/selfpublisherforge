"use client";

import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const PERMISSION_LABELS: Record<string, string> = {
  draft_only: "Draft Only",
  suggest: "Suggest",
  auto_execute_low: "Auto-Apply",
};

const PERMISSION_COLORS: Record<string, string> = {
  draft_only: "bg-gray-100 text-gray-800",
  suggest: "bg-blue-100 text-blue-800",
  auto_execute_low: "bg-green-100 text-green-800",
  auto_execute_high: "bg-yellow-100 text-yellow-800",
  full_autonomous: "bg-red-100 text-red-800",
};

interface AgentStats {
  task_count: number;
  avg_execution_time: number;
  avg_rating: number;
}

interface EnhancedAgentCardProps {
  agent: any;
  stats?: AgentStats;
  onNewTask: (agentId: string) => void;
  onConfigure: (agentId: string) => void;
  onHistory?: (agentId: string) => void;
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  return `${Math.round(seconds / 60)}m`;
}

export function EnhancedAgentCard({
  agent,
  stats,
  onNewTask,
  onConfigure,
  onHistory,
}: EnhancedAgentCardProps) {
  const permissionLabel =
    PERMISSION_LABELS[agent.permission_level] || agent.permission_level;
  const permissionColor =
    PERMISSION_COLORS[agent.permission_level] || "bg-gray-100 text-gray-800";

  return (
    <Card
      className={cn(
        "transition-shadow hover:shadow-md",
        !agent.is_enabled && "opacity-60"
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            {agent.icon && <span className="text-2xl">{agent.icon}</span>}
            <div>
              <h3 className="text-lg font-semibold leading-tight">
                {agent.name}
              </h3>
              {agent.category && (
                <Badge variant="secondary" className="mt-1">
                  {agent.category}
                </Badge>
              )}
            </div>
          </div>
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
              permissionColor
            )}
          >
            {permissionLabel}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-3">
        {agent.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {agent.description}
          </p>
        )}

        {stats && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Tasks: {stats.task_count}</span>
            <span>·</span>
            <span>Avg: {formatTime(stats.avg_execution_time)}</span>
            {stats.avg_rating > 0 && (
              <>
                <span>·</span>
                <span className="flex items-center">
                  ⭐ {stats.avg_rating.toFixed(1)}
                </span>
              </>
            )}
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          <span className="font-medium">Model:</span> {agent.model_id}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2 pt-0">
        <Button
          size="sm"
          onClick={() => onNewTask(agent.id)}
          disabled={!agent.is_enabled}
          className="flex-1"
        >
          New Task
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onConfigure(agent.id)}
        >
          Configure
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onHistory?.(agent.id)}
        >
          History
        </Button>
      </CardFooter>
    </Card>
  );
}
