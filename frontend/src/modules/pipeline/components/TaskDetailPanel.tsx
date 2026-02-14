"use client";

import { useState, useCallback, useEffect } from "react";
import { format } from "date-fns";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useUpdateTask,
  useDeleteTask,
  useAddChecklistItem,
  useToggleChecklistItem,
  usePipelineActivity,
} from "../hooks";
import { TaskChecklist } from "./TaskChecklist";
import type {
  PipelineTask,
  PipelineStage,
  TaskStatus,
  TaskPriority,
  ActivityEntry,
} from "../types";

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "in_progress", label: "In Progress" },
  { value: "blocked", label: "Blocked" },
  { value: "completed", label: "Completed" },
  { value: "cancelled", label: "Cancelled" },
];

const PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

interface TaskDetailPanelProps {
  task: PipelineTask;
  pipelineId: string;
  stages?: PipelineStage[];
  open: boolean;
  onClose: () => void;
}

export function TaskDetailPanel({
  task,
  pipelineId,
  stages,
  open,
  onClose,
}: TaskDetailPanelProps) {
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description ?? "");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const updateTask = useUpdateTask(pipelineId, task.id);
  const deleteTask = useDeleteTask(pipelineId);
  const addChecklistItem = useAddChecklistItem(pipelineId, task.id);
  const toggleChecklistItem = useToggleChecklistItem(pipelineId, task.id);
  const { data: activity } = usePipelineActivity(pipelineId);

  // Reset local state when task changes
  useEffect(() => {
    setTitle(task.title);
    setDescription(task.description ?? "");
    setShowDeleteConfirm(false);
  }, [task.id, task.title, task.description]);

  const taskActivity = (activity ?? []).filter((a) => a.task_id === task.id);

  const handleFieldUpdate = useCallback(
    (field: string, value: string) => {
      updateTask.mutate({ [field]: value || undefined });
    },
    [updateTask]
  );

  function handleTitleBlur() {
    const trimmed = title.trim();
    if (trimmed && trimmed !== task.title) {
      handleFieldUpdate("title", trimmed);
    }
  }

  function handleDescriptionBlur() {
    if (description !== (task.description ?? "")) {
      handleFieldUpdate("description", description);
    }
  }

  function handleDelete() {
    deleteTask.mutate(task.id, {
      onSuccess: () => onClose(),
    });
  }

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-lg p-0">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-6">
            <SheetHeader>
              <SheetTitle className="sr-only">Task Details</SheetTitle>
              <SheetDescription className="sr-only">
                Edit task properties and view activity
              </SheetDescription>
            </SheetHeader>

            {/* Editable title */}
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={handleTitleBlur}
              className="text-lg font-semibold w-full border-0 border-b border-transparent hover:border-gray-200 focus:border-primary focus:outline-none bg-transparent px-0 py-1"
            />

            {/* Dropdowns row */}
            <div className="grid grid-cols-2 gap-3">
              {/* Stage */}
              {stages && stages.length > 0 && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">
                    Stage
                  </label>
                  <select
                    value={task.stage_id ?? ""}
                    onChange={(e) =>
                      handleFieldUpdate("stage_id", e.target.value)
                    }
                    className="w-full border rounded-md px-2 py-1.5 text-sm bg-card"
                  >
                    <option value="">None</option>
                    {stages.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Status */}
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Status
                </label>
                <select
                  value={task.status}
                  onChange={(e) =>
                    handleFieldUpdate("status", e.target.value)
                  }
                  className="w-full border rounded-md px-2 py-1.5 text-sm bg-card"
                >
                  {STATUS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Priority */}
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Priority
                </label>
                <select
                  value={task.priority ?? ""}
                  onChange={(e) =>
                    handleFieldUpdate("priority", e.target.value)
                  }
                  className="w-full border rounded-md px-2 py-1.5 text-sm bg-card"
                >
                  <option value="">None</option>
                  {PRIORITY_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Due Date */}
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  value={task.due_date?.split("T")[0] ?? ""}
                  onChange={(e) =>
                    handleFieldUpdate("due_date", e.target.value)
                  }
                  className="w-full border rounded-md px-2 py-1.5 text-sm bg-card"
                />
              </div>
            </div>

            <Separator />

            {/* Description */}
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                onBlur={handleDescriptionBlur}
                placeholder="Add a description..."
                rows={3}
                className="w-full border rounded-md px-3 py-2 text-sm resize-none"
              />
            </div>

            <Separator />

            {/* Checklist */}
            <div>
              <h4 className="text-sm font-medium mb-2">Checklist</h4>
              <TaskChecklist
                items={task.checklist ?? []}
                onAdd={(label) => addChecklistItem.mutate({ label })}
                onToggle={(itemId, done) =>
                  toggleChecklistItem.mutate({ checklistItemId: itemId, done })
                }
                isAdding={addChecklistItem.isPending}
              />
            </div>

            <Separator />

            {/* Activity log */}
            <div>
              <h4 className="text-sm font-medium mb-2">Activity</h4>
              {taskActivity.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  No activity recorded yet.
                </p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {taskActivity.map((entry) => (
                    <div
                      key={entry.id}
                      className="flex items-start gap-2 text-xs"
                    >
                      <Badge variant="secondary" className="shrink-0 text-[10px]">
                        {entry.action}
                      </Badge>
                      <span className="text-muted-foreground">
                        {format(new Date(entry.created_at), "MMM d, h:mm a")}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Delete task */}
            <div>
              {!showDeleteConfirm ? (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="flex items-center gap-2 text-sm text-destructive hover:text-destructive/80"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete task
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-destructive">
                    Are you sure?
                  </span>
                  <button
                    onClick={handleDelete}
                    disabled={deleteTask.isPending}
                    className="px-3 py-1 text-xs bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 disabled:opacity-50"
                  >
                    {deleteTask.isPending ? "Deleting..." : "Yes, delete"}
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="px-3 py-1 text-xs border rounded-md hover:bg-muted"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
