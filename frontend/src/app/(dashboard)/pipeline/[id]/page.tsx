"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import {
  usePipeline,
  useTimeline,
  useAddTask,
  useUpdatePipeline,
  usePipelineStages,
} from "@/modules/pipeline/hooks";
import { BoardView } from "@/modules/pipeline/components/BoardView";
import { ListView } from "@/modules/pipeline/components/ListView";
import { TimelineView } from "@/modules/pipeline/components/TimelineView";
import { TaskForm } from "@/modules/pipeline/components/TaskForm";
import { Skeleton } from "@/components/ui/skeleton";
import type { PipelineStatus, ViewMode } from "@/modules/pipeline/hooks";
import { useTranslations } from "@/hooks/use-translations";
import {
  LayoutGrid,
  List,
  GanttChart,
  Plus,
} from "lucide-react";

const VIEW_MODES: { value: ViewMode; label: string; icon: React.ReactNode }[] = [
  { value: "board", label: "Board", icon: <LayoutGrid className="h-3.5 w-3.5" /> },
  { value: "list", label: "List", icon: <List className="h-3.5 w-3.5" /> },
  { value: "timeline", label: "Timeline", icon: <GanttChart className="h-3.5 w-3.5" /> },
];

export default function PipelineDetailPage() {
  const t = useTranslations("pipeline");
  const params = useParams();
  const id = params.id as string;

  const statusActions: Record<
    PipelineStatus,
    { label: string; target: PipelineStatus }[]
  > = {
    draft: [{ label: t("detail.activate"), target: "active" }],
    active: [
      { label: t("detail.pause"), target: "paused" },
      { label: t("detail.complete"), target: "completed" },
    ],
    paused: [{ label: t("detail.resume"), target: "active" }],
    completed: [],
    cancelled: [],
  };

  const [viewMode, setViewMode] = useState<ViewMode>("board");
  const [showTaskForm, setShowTaskForm] = useState(false);

  const { data: pipeline, isPending, error } = usePipeline(id);
  const { data: timeline } = useTimeline(id);
  const { data: stages } = usePipelineStages(id);
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
        type: data.type as "writing" | "editing" | "proofreading" | "formatting" | "review",
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

  if (isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-6 w-96" />
        <Skeleton className="h-3 w-full" />
        <div className="flex gap-4 mt-6">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-72" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !pipeline) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-600">{t("detail.pipelineNotFound")}</p>
      </div>
    );
  }

  const completedCount = pipeline.tasks.filter(
    (task) => task.status === "completed"
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
          <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
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
                {t("detail.deadline")}:{" "}
                {format(new Date(pipeline.deadline), "MMM d, yyyy")}
              </span>
            )}
            <span>
              {t("detail.tasksCompleted", {
                completed: completedCount,
                total: pipeline.tasks.length,
                progress,
              })}
            </span>
          </div>
          {/* Stages summary */}
          {stages && stages.length > 0 && (
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              {stages
                .sort((a, b) => a.order_index - b.order_index)
                .map((stage) => (
                  <span
                    key={stage.id}
                    className="text-[10px] font-medium px-2 py-0.5 rounded-full border"
                    style={
                      stage.color
                        ? {
                            backgroundColor: `${stage.color}20`,
                            borderColor: stage.color,
                            color: stage.color,
                          }
                        : undefined
                    }
                  >
                    {stage.name} ({stage.tasks?.length ?? 0})
                  </span>
                ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 flex-wrap">
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
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <Plus className="h-3.5 w-3.5" />
            {t("detail.addTask")}
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

      {/* View toggle: Board / List / Timeline */}
      <div className="flex gap-1 mb-4 p-1 bg-gray-100 rounded-md w-fit">
        {VIEW_MODES.map((mode) => (
          <button
            key={mode.value}
            onClick={() => setViewMode(mode.value)}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md transition-colors",
              viewMode === mode.value
                ? "bg-white shadow-sm font-medium"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {mode.icon}
            {mode.label}
          </button>
        ))}
      </div>

      {/* Views */}
      {viewMode === "board" && (
        <BoardView pipelineId={id} tasks={pipeline.tasks} />
      )}
      {viewMode === "list" && (
        <ListView pipelineId={id} tasks={pipeline.tasks} />
      )}
      {viewMode === "timeline" && timeline && (
        <TimelineView timeline={timeline} />
      )}
      {viewMode === "timeline" && !timeline && (
        <p className="text-muted-foreground text-sm">
          {t("detail.loadingTimeline")}
        </p>
      )}
    </div>
  );
}
