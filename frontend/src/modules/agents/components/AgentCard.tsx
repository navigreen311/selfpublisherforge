"use client";

import { cn } from "@/lib/utils";
import type { Agent } from "../types";

const AGENT_TYPE_LABELS: Record<string, string> = {
  research: "Research",
  writing_assistant: "Writing Assistant",
  editor: "Editor",
  marketing_copy: "Marketing Copy",
};

const PERMISSION_LABELS: Record<string, string> = {
  draft_only: "Draft Only",
  suggest: "Suggest",
  auto_execute_low: "Auto (Low Risk)",
  auto_execute_high: "Auto (High Risk)",
  full_autonomous: "Full Autonomous",
};

const PERMISSION_COLORS: Record<string, string> = {
  draft_only: "bg-gray-100 text-gray-800",
  suggest: "bg-blue-100 text-blue-800",
  auto_execute_low: "bg-green-100 text-green-800",
  auto_execute_high: "bg-yellow-100 text-yellow-800",
  full_autonomous: "bg-red-100 text-red-800",
};

interface AgentCardProps {
  agent: Agent;
  onConfigure?: (agent: Agent) => void;
  onCreateTask?: (agent: Agent) => void;
}

export function AgentCard({ agent, onConfigure, onCreateTask }: AgentCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border p-4 shadow-sm transition-shadow hover:shadow-md",
        !agent.is_enabled && "opacity-60"
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold">{agent.name}</h3>
          <span className="text-sm text-muted-foreground">
            {AGENT_TYPE_LABELS[agent.agent_type] || agent.agent_type}
          </span>
        </div>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
            PERMISSION_COLORS[agent.permission_level] || "bg-gray-100"
          )}
        >
          {PERMISSION_LABELS[agent.permission_level] || agent.permission_level}
        </span>
      </div>

      {agent.description && (
        <p className="mt-2 text-sm text-muted-foreground">{agent.description}</p>
      )}

      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <span>Model: {agent.model_id}</span>
        <span>|</span>
        <span>Max tokens: {agent.max_tokens.toLocaleString()}</span>
      </div>

      <div className="mt-4 flex gap-2">
        {onCreateTask && (
          <button
            onClick={() => onCreateTask(agent)}
            disabled={!agent.is_enabled}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            New Task
          </button>
        )}
        {onConfigure && (
          <button
            onClick={() => onConfigure(agent)}
            className="rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-accent"
          >
            Configure
          </button>
        )}
      </div>
    </div>
  );
}
