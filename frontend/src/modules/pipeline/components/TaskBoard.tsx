"use client";

import { cn } from "@/lib/utils";
import { format } from "date-fns";
import type { PipelineTask, TaskStatus } from "../hooks";

const COLUMNS: { key: TaskStatus; label: string; color: string }[] = [
  { key: "pending", label: "To Do", color: "border-t-gray-400" },
  { key: "in_progress", label: "In Progress", color: "border-t-blue-500" },
  { key: "blocked", label: "Blocked", color: "border-t-yellow-500" },
  { key: "completed", label: "Done", color: "border-t-green-500" },
];

const typeColors: Record<string, string> = {
  writing: "bg-purple-100 text-purple-700",
  editing: "bg-blue-100 text-blue-700",
  proofreading: "bg-teal-100 text-teal-700",
  formatting: "bg-orange-100 text-orange-700",
  review: "bg-pink-100 text-pink-700",
};

interface TaskBoardProps {
  tasks: PipelineTask[];
  onTaskClick?: (task: PipelineTask) => void;
}

export function TaskBoard({ tasks, onTaskClick }: TaskBoardProps) {
  const grouped: Record<TaskStatus, PipelineTask[]> = {
    pending: [],
    in_progress: [],
    blocked: [],
    completed: [],
    cancelled: [],
  };

  for (const task of tasks) {
    if (grouped[task.status]) {
      grouped[task.status].push(task);
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {COLUMNS.map((col) => (
        <div
          key={col.key}
          className={cn(
            "bg-gray-50 rounded-lg p-3 border-t-4",
            col.color
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold">{col.label}</h4>
            <span className="text-xs bg-gray-200 rounded-full px-2 py-0.5">
              {grouped[col.key].length}
            </span>
          </div>
          <div className="space-y-2">
            {grouped[col.key]
              .sort((a, b) => a.position - b.position)
              .map((task) => (
                <div
                  key={task.id}
                  className="bg-white rounded-md border p-3 cursor-pointer hover:shadow-sm transition-shadow"
                  onClick={() => onTaskClick?.(task)}
                >
                  <p className="text-sm font-medium mb-1">{task.title}</p>
                  <div className="flex flex-wrap gap-1 mb-2">
                    <span
                      className={cn(
                        "text-[10px] font-medium px-1.5 py-0.5 rounded",
                        typeColors[task.type] || "bg-gray-100 text-gray-600"
                      )}
                    >
                      {task.type}
                    </span>
                  </div>
                  {task.due_date && (
                    <p className="text-[10px] text-muted-foreground">
                      Due: {format(new Date(task.due_date), "MMM d")}
                    </p>
                  )}
                  {task.depends_on.length > 0 && (
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {task.depends_on.length} dep(s)
                    </p>
                  )}
                </div>
              ))}
            {grouped[col.key].length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">
                No tasks
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
