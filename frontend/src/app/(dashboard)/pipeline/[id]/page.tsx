"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import {
  usePipeline,
  useTimeline,
  useAddTask,
  useUpdateTask,
  useUpdatePipeline,
} from "@/modules/pipeline/hooks";
import { TaskBoard } from "@/modules/pipeline/components/TaskBoard";
import { TimelineView } from "@/modules/pipeline/components/TimelineView";
import { TaskForm } from "@/modules/pipeline/components/TaskForm";
import type { PipelineTask, PipelineStatus } from "@/modules/pipeline/hooks";

type ViewMode = "kanban" | "timeline";

const statusActions: Record<PipelineStatus, { label: string; target: PipelineStatus }[]> = {
  draft: [{ label: "Activate", target: "active" }],
  active: [
    { label: "Pause", target: "paused" },
    { label: "Complete", target: "completed" },
  ],
  paused: [{ label: "Resume", target: "active" }],
  completed: [],
  cancelled: [],
};

export default function PipelineDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [viewMode, setViewMode] = useState<ViewMode>("kanban");
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [selectedTask, setSelectedTask] = useState<PipelineTask | null>(null);

  const { data: pipeline, isLoading, error } = usePipeline(id);
  const { data: timeline } = useTimeline(id);
  const addTaskMutation = useAddTask(id);
  const updatePipelineMutation = useUpdatePipeline(id);

  function handleAddTask(data: {
    title: string;
    type: string;
    description: string;
    due_date: string;
  }) {
    addTaskMutation.mutate(
      {
        title: data.title,
        type: data.type as PipelineTask["type"],
        description: data.description || undefined,
        due_date: data.due_date || undefined,
      },
      {
        onSuccess: () => setShowTaskForm(false),
      }
    );
  }

  function handleStatusChange(target: PipelineStatus) {
    updatePipelineMutation.mutate({ status: target });
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading pipeline...</p>
      </div>
    );
  }

  if (error || !pipeline) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-600">Pipeline not found.</p>
      </div>
    );
  }

  const completedCount = pipeline.tasks.filter(
    (t) => t.status === "completed"
  ).length;
  const progress =
    pipeline.tasks.length > 0
      ? Math.round((completedCount / pipeline.tasks.length) * 100)
      : 0;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-1">{pipeline.name}</h1>
          {pipeline.description && (
            <p className="text-muted-foreground text-sm mb-2">
              {pipeline.description}
            </p>
          )}
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span
              className={cn(
                "text-xs font-medium px-2 py-1 rounded-full",
                pipeline.status === "active"
                  ? "bg-blue-100 text-blue-700"
                  : pipeline.status === "completed"
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-700"
              )}
            >
              {pipeline.status}
            </span>
            {pipeline.deadline && (
              <span>
                Deadline:{" "}
                {format(new Date(pipeline.deadline), "MMM d, yyyy")}
              </span>
            )}
            <span>
              {completedCount}/{pipeline.tasks.length} tasks completed (
              {progress}%)
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {statusActions[pipeline.status]?.map((action) => (
            <button
              key={action.target}
              onClick={() => handleStatusChange(action.target)}
              disabled={updatePipelineMutation.isPending}
              className="px-3 py-1.5 text-xs border rounded-md hover:bg-gray-50"
            >
              {action.label}
            </button>
          ))}
          <button
            onClick={() => setShowTaskForm(!showTaskForm)}
            className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Add Task
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={cn(
              "h-2.5 rounded-full transition-all",
              progress === 100 ? "bg-green-500" : "bg-blue-500"
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Task form */}
      {showTaskForm && (
        <div className="mb-6">
          <TaskForm
            onSubmit={handleAddTask}
            onCancel={() => setShowTaskForm(false)}
            isLoading={addTaskMutation.isPending}
          />
        </div>
      )}

      {/* View toggle */}
      <div className="flex gap-1 mb-4 p-1 bg-gray-100 rounded-md w-fit">
        <button
          onClick={() => setViewMode("kanban")}
          className={cn(
            "px-3 py-1.5 text-xs rounded-md transition-colors",
            viewMode === "kanban"
              ? "bg-white shadow-sm font-medium"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Kanban Board
        </button>
        <button
          onClick={() => setViewMode("timeline")}
          className={cn(
            "px-3 py-1.5 text-xs rounded-md transition-colors",
            viewMode === "timeline"
              ? "bg-white shadow-sm font-medium"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Timeline
        </button>
      </div>

      {/* Views */}
      {viewMode === "kanban" && (
        <TaskBoard
          tasks={pipeline.tasks}
          onTaskClick={(task) => setSelectedTask(task)}
        />
      )}
      {viewMode === "timeline" && timeline && (
        <TimelineView timeline={timeline} />
      )}
      {viewMode === "timeline" && !timeline && (
        <p className="text-muted-foreground text-sm">Loading timeline...</p>
      )}

      {/* Selected task detail panel */}
      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          pipelineId={id}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </div>
  );
}

// ── Task Detail Side Panel ───────────────────────────────────────────────

interface TaskDetailPanelProps {
  task: PipelineTask;
  pipelineId: string;
  onClose: () => void;
}

function TaskDetailPanel({ task, pipelineId, onClose }: TaskDetailPanelProps) {
  const updateTaskMutation = useUpdateTask(pipelineId, task.id);

  const statusOptions = getNextStatuses(task.status);

  function handleStatusChange(newStatus: string) {
    updateTaskMutation.mutate({
      status: newStatus as PipelineTask["status"],
    });
  }

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white border-l shadow-lg z-50 overflow-y-auto">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">Task Details</h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            Close
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Title
            </label>
            <p className="text-sm font-medium">{task.title}</p>
          </div>

          {task.description && (
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Description
              </label>
              <p className="text-sm">{task.description}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Type
              </label>
              <p className="text-sm capitalize">{task.type}</p>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Status
              </label>
              <p className="text-sm capitalize">
                {task.status.replace("_", " ")}
              </p>
            </div>
          </div>

          {task.due_date && (
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Due Date
              </label>
              <p className="text-sm">
                {format(new Date(task.due_date), "MMM d, yyyy")}
              </p>
            </div>
          )}

          {task.depends_on.length > 0 && (
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Dependencies
              </label>
              <p className="text-sm">{task.depends_on.length} task(s)</p>
            </div>
          )}

          {/* Status transition buttons */}
          {statusOptions.length > 0 && (
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-2 block">
                Change Status
              </label>
              <div className="flex flex-wrap gap-2">
                {statusOptions.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleStatusChange(s)}
                    disabled={updateTaskMutation.isPending}
                    className="px-3 py-1.5 text-xs border rounded-md hover:bg-gray-50 capitalize disabled:opacity-50"
                  >
                    {s.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getNextStatuses(current: string): string[] {
  const transitions: Record<string, string[]> = {
    pending: ["in_progress", "blocked", "cancelled"],
    blocked: ["pending", "in_progress", "cancelled"],
    in_progress: ["completed", "blocked", "cancelled"],
    completed: [],
    cancelled: [],
  };
  return transitions[current] || [];
}
