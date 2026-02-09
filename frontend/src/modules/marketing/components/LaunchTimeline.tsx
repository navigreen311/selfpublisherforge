"use client";

import { useState } from "react";
import type { LaunchPhase, PhaseTask } from "../hooks";

interface LaunchTimelineProps {
  phases: LaunchPhase[];
  onTaskStatusChange?: (taskId: string, status: PhaseTask["status"]) => void;
}

const phaseColors: Record<string, string> = {
  pre_launch: "border-blue-500 bg-blue-50",
  launch_week: "border-green-500 bg-green-50",
  post_launch: "border-purple-500 bg-purple-50",
};

const phaseLabels: Record<string, string> = {
  pre_launch: "Pre-Launch",
  launch_week: "Launch Week",
  post_launch: "Post-Launch",
};

const statusColors: Record<string, string> = {
  pending: "bg-gray-200 text-gray-700",
  in_progress: "bg-yellow-200 text-yellow-800",
  completed: "bg-green-200 text-green-800",
  skipped: "bg-red-200 text-red-800",
};

export function LaunchTimeline({ phases, onTaskStatusChange }: LaunchTimelineProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(
    new Set(phases.map((p) => p.id))
  );

  const togglePhase = (phaseId: string) => {
    setExpandedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(phaseId)) {
        next.delete(phaseId);
      } else {
        next.add(phaseId);
      }
      return next;
    });
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getCompletionRate = (tasks: PhaseTask[]) => {
    if (tasks.length === 0) return 0;
    const completed = tasks.filter((t) => t.status === "completed").length;
    return Math.round((completed / tasks.length) * 100);
  };

  return (
    <div className="space-y-4">
      {phases.map((phase) => {
        const isExpanded = expandedPhases.has(phase.id);
        const completionRate = getCompletionRate(phase.tasks);
        const colorClass = phaseColors[phase.phase_type] || "border-gray-300 bg-gray-50";

        return (
          <div key={phase.id} className={`border-l-4 rounded-lg ${colorClass}`}>
            <button
              className="w-full p-4 text-left flex items-center justify-between"
              onClick={() => togglePhase(phase.id)}
            >
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-lg">
                    {phaseLabels[phase.phase_type] || phase.name}
                  </h3>
                  <span className="text-sm text-gray-500">
                    {phase.tasks.length} tasks
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {formatDate(phase.start_date)} - {formatDate(phase.end_date)}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-medium">{completionRate}%</div>
                  <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full transition-all"
                      style={{ width: `${completionRate}%` }}
                    />
                  </div>
                </div>
                <span className="text-gray-400">{isExpanded ? "\u25B2" : "\u25BC"}</span>
              </div>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4 space-y-2">
                {phase.tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 p-3 bg-white rounded border"
                  >
                    <input
                      type="checkbox"
                      checked={task.status === "completed"}
                      onChange={() =>
                        onTaskStatusChange?.(
                          task.id,
                          task.status === "completed" ? "pending" : "completed"
                        )
                      }
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-medium ${
                            task.status === "completed" ? "line-through text-gray-400" : ""
                          }`}
                        >
                          {task.title}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            statusColors[task.status] || ""
                          }`}
                        >
                          {task.status}
                        </span>
                      </div>
                      {task.description && (
                        <p className="text-sm text-gray-500 mt-1">{task.description}</p>
                      )}
                    </div>
                    {task.due_date && (
                      <span className="text-xs text-gray-400">{formatDate(task.due_date)}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
