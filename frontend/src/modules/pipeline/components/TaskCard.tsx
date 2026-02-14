"use client";

import { cn } from "@/lib/utils";
import { format, isPast, isThisWeek } from "date-fns";
import {
  Circle,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Calendar,
  CheckSquare,
} from "lucide-react";
import type { PipelineTask, TaskStatus } from "../types";

const statusIcons: Record<TaskStatus, React.ReactNode> = {
  pending: <Circle className="h-3.5 w-3.5 text-gray-400" />,
  in_progress: <Loader2 className="h-3.5 w-3.5 text-blue-500" />,
  blocked: <AlertTriangle className="h-3.5 w-3.5 text-yellow-500" />,
  completed: <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />,
  cancelled: <XCircle className="h-3.5 w-3.5 text-red-400" />,
};

const priorityDots: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-yellow-500",
  low: "bg-gray-400",
};

interface TaskCardProps {
  task: PipelineTask;
  onClick?: () => void;
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  const checklist = task.checklist ?? [];
  const doneCount = checklist.filter((c) => c.done).length;
  const totalCount = checklist.length;

  const dueDate = task.due_date ? new Date(task.due_date) : null;
  const isOverdue = dueDate && isPast(dueDate) && task.status !== "completed";
  const isDueThisWeek =
    dueDate && !isOverdue && isThisWeek(dueDate, { weekStartsOn: 1 });

  return (
    <div
      className="bg-white rounded-md border p-3 cursor-pointer hover:shadow-sm transition-shadow"
      onClick={onClick}
    >
      {/* Top row: status icon + title + priority dot */}
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0">{statusIcons[task.status]}</span>
        <p className="text-sm font-medium flex-1 leading-tight">{task.title}</p>
        {task.priority && (
          <span
            className={cn(
              "h-2.5 w-2.5 rounded-full shrink-0 mt-1",
              priorityDots[task.priority] ?? "bg-gray-300"
            )}
            title={`Priority: ${task.priority}`}
          />
        )}
      </div>

      {/* Bottom row: due date + checklist */}
      <div className="flex items-center gap-3 mt-2">
        {dueDate && (
          <span
            className={cn(
              "inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded font-medium",
              isOverdue
                ? "bg-red-100 text-red-700"
                : isDueThisWeek
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-gray-100 text-muted-foreground"
            )}
          >
            <Calendar className="h-2.5 w-2.5" />
            {format(dueDate, "MMM d")}
          </span>
        )}
        {totalCount > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
            <CheckSquare className="h-2.5 w-2.5" />
            {doneCount}/{totalCount}
          </span>
        )}
      </div>
    </div>
  );
}
