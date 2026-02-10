"use client";

import { cn } from "@/lib/utils";
import { format, differenceInDays } from "date-fns";
import type { TimelineView as TimelineViewType, TimelineTask } from "../hooks";

const statusBarColors: Record<string, string> = {
  pending: "bg-gray-300",
  in_progress: "bg-blue-500",
  blocked: "bg-yellow-500",
  completed: "bg-green-500",
  cancelled: "bg-red-300",
};

const typeLabels: Record<string, string> = {
  writing: "WR",
  editing: "ED",
  proofreading: "PR",
  formatting: "FM",
  review: "RV",
};

interface TimelineViewProps {
  timeline: TimelineViewType;
}

export function TimelineView({ timeline }: TimelineViewProps) {
  const tasks = timeline.tasks;
  const criticalSet = new Set(timeline.critical_path);

  // Determine timeline range
  const dates = tasks
    .flatMap((t) => [t.start_date, t.due_date].filter(Boolean))
    .map((d) => new Date(d as string).getTime());

  if (timeline.deadline) {
    dates.push(new Date(timeline.deadline).getTime());
  }

  const minDate = dates.length > 0 ? new Date(Math.min(...dates)) : new Date();
  const maxDate = dates.length > 0 ? new Date(Math.max(...dates)) : new Date();
  const totalDays = Math.max(differenceInDays(maxDate, minDate), 1);

  function getBarStyle(task: TimelineTask) {
    const start = task.start_date ? new Date(task.start_date) : minDate;
    const end = task.due_date ? new Date(task.due_date) : maxDate;
    const left = Math.max(0, (differenceInDays(start, minDate) / totalDays) * 100);
    const width = Math.max(
      2,
      (differenceInDays(end, start) / totalDays) * 100
    );
    return { left: `${left}%`, width: `${Math.min(width, 100 - left)}%` };
  }

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg">{timeline.pipeline_name}</h3>
        {timeline.deadline && (
          <span className="text-sm text-muted-foreground">
            Deadline: {format(new Date(timeline.deadline), "MMM d, yyyy")}
          </span>
        )}
      </div>

      {/* Timeline header row */}
      <div className="flex items-center border-b pb-2 text-xs text-muted-foreground">
        <div className="w-48 shrink-0 font-medium">Task</div>
        <div className="flex-1 flex justify-between px-2">
          <span>{format(minDate, "MMM d")}</span>
          <span>{format(maxDate, "MMM d")}</span>
        </div>
      </div>

      {/* Task rows */}
      {tasks
        .sort((a, b) => {
          const aStart = a.start_date
            ? new Date(a.start_date).getTime()
            : 0;
          const bStart = b.start_date
            ? new Date(b.start_date).getTime()
            : 0;
          return aStart - bStart;
        })
        .map((task) => {
          const barStyle = getBarStyle(task);
          const isCritical = criticalSet.has(task.id);
          return (
            <div
              key={task.id}
              className={cn(
                "flex items-center py-2 border-b last:border-b-0",
                isCritical && "bg-red-50"
              )}
            >
              <div className="w-48 shrink-0 flex items-center gap-2 pr-2">
                <span className="text-[10px] font-mono bg-gray-100 rounded px-1">
                  {typeLabels[task.type] || "??"}
                </span>
                <span className="text-sm truncate" title={task.title}>
                  {task.title}
                </span>
              </div>
              <div className="flex-1 relative h-6">
                <div
                  className={cn(
                    "absolute top-1 h-4 rounded-full",
                    statusBarColors[task.status] || "bg-gray-300",
                    isCritical && "ring-2 ring-red-400"
                  )}
                  style={barStyle}
                  title={`${task.title} (${task.status}) - ${Math.round(task.progress * 100)}%`}
                >
                  {/* Progress fill inside bar */}
                  <div
                    className="h-full rounded-full bg-white/30"
                    style={{ width: `${task.progress * 100}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}

      {tasks.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No tasks in this pipeline yet.
        </p>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-4 pt-4 text-xs text-muted-foreground">
        {Object.entries(statusBarColors).map(([status, color]) => (
          <div key={status} className="flex items-center gap-1.5">
            <div className={cn("w-3 h-3 rounded-full", color)} />
            <span className="capitalize">{status.replace("_", " ")}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-gray-300 ring-2 ring-red-400" />
          <span>Critical path</span>
        </div>
      </div>
    </div>
  );
}
