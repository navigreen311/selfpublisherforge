"use client";

import Link from "next/link";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import type { PipelineSummary, PipelineStatus } from "../hooks";

const statusColors: Record<PipelineStatus, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-blue-100 text-blue-700",
  paused: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

interface PipelineCardProps {
  pipeline: PipelineSummary;
}

export function PipelineCard({ pipeline }: PipelineCardProps) {
  const progress =
    pipeline.task_count > 0
      ? Math.round((pipeline.completed_task_count / pipeline.task_count) * 100)
      : 0;

  return (
    <Link href={`/pipeline/${pipeline.id}`}>
      <div className="border rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-lg truncate pr-2">
            {pipeline.name}
          </h3>
          <span
            className={cn(
              "text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap",
              statusColors[pipeline.status]
            )}
          >
            {pipeline.status}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>
              {pipeline.completed_task_count}/{pipeline.task_count} tasks
            </span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn(
                "h-2 rounded-full transition-all",
                progress === 100 ? "bg-green-500" : "bg-blue-500"
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Footer: deadline + overdue */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          {pipeline.deadline ? (
            <span>
              Deadline:{" "}
              {format(new Date(pipeline.deadline), "MMM d, yyyy")}
            </span>
          ) : (
            <span>No deadline</span>
          )}
          {pipeline.overdue_task_count > 0 && (
            <span className="text-red-600 font-medium">
              {pipeline.overdue_task_count} overdue
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
