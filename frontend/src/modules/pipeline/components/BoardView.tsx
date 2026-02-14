"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Plus } from "lucide-react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  usePipelineStages,
  useCreateStage,
  useAddTask,
} from "../hooks";
import { TaskCard } from "./TaskCard";
import { TaskDetailPanel } from "./TaskDetailPanel";
import type { PipelineTask, PipelineStage } from "../types";

interface BoardViewProps {
  pipelineId: string;
  /** Fallback tasks when stages are not yet loaded */
  tasks?: PipelineTask[];
}

export function BoardView({ pipelineId, tasks = [] }: BoardViewProps) {
  const { data: stages, isLoading: stagesLoading } =
    usePipelineStages(pipelineId);
  const createStage = useCreateStage(pipelineId);
  const addTask = useAddTask(pipelineId);

  const [selectedTask, setSelectedTask] = useState<PipelineTask | null>(null);
  const [newStageName, setNewStageName] = useState("");
  const [showNewStageInput, setShowNewStageInput] = useState(false);
  const [addingTaskInStage, setAddingTaskInStage] = useState<string | null>(
    null
  );
  const [newTaskTitle, setNewTaskTitle] = useState("");

  function handleCreateStage() {
    const trimmed = newStageName.trim();
    if (!trimmed) return;
    createStage.mutate(
      { name: trimmed, order_index: (stages?.length ?? 0) },
      {
        onSuccess: () => {
          setNewStageName("");
          setShowNewStageInput(false);
        },
      }
    );
  }

  function handleAddTask(stageId: string) {
    const trimmed = newTaskTitle.trim();
    if (!trimmed) return;
    addTask.mutate(
      { title: trimmed, stage_id: stageId },
      {
        onSuccess: () => {
          setNewTaskTitle("");
          setAddingTaskInStage(null);
        },
      }
    );
  }

  function handleStageKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleCreateStage();
    }
    if (e.key === "Escape") {
      setShowNewStageInput(false);
      setNewStageName("");
    }
  }

  function handleTaskKeyDown(e: React.KeyboardEvent, stageId: string) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTask(stageId);
    }
    if (e.key === "Escape") {
      setAddingTaskInStage(null);
      setNewTaskTitle("");
    }
  }

  if (stagesLoading) {
    return (
      <div className="flex gap-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-64 w-72 shrink-0" />
        ))}
      </div>
    );
  }

  // If no stages exist yet, show a prompt to create the first one
  const stageList = stages ?? [];

  // Group fallback tasks by stage_id (for tasks without stages, create an "Unsorted" virtual column)
  function getTasksForStage(stageId: string): PipelineTask[] {
    const stage = stageList.find((s) => s.id === stageId);
    if (stage && stage.tasks?.length > 0) {
      return [...stage.tasks].sort(
        (a, b) => (a.order_index ?? a.position) - (b.order_index ?? b.position)
      );
    }
    // Fall back to pipeline tasks matching this stage
    return tasks
      .filter((t) => t.stage_id === stageId)
      .sort(
        (a, b) => (a.order_index ?? a.position) - (b.order_index ?? b.position)
      );
  }

  return (
    <>
      <ScrollArea className="w-full">
        <div className="flex gap-4 pb-4 min-h-[400px]">
          {stageList
            .sort((a, b) => a.order_index - b.order_index)
            .map((stage) => {
              const stageTasks = getTasksForStage(stage.id);
              return (
                <div
                  key={stage.id}
                  className={cn(
                    "bg-gray-50 rounded-lg p-3 w-72 shrink-0 border-t-4 flex flex-col",
                    stage.color
                      ? `border-t-[${stage.color}]`
                      : "border-t-gray-300"
                  )}
                  style={
                    stage.color
                      ? { borderTopColor: stage.color }
                      : undefined
                  }
                >
                  {/* Stage header */}
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold truncate">
                      {stage.name}
                    </h4>
                    <span className="text-xs bg-gray-200 rounded-full px-2 py-0.5">
                      {stageTasks.length}
                    </span>
                  </div>

                  {/* Task cards */}
                  <div className="space-y-2 flex-1">
                    {stageTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onClick={() => setSelectedTask(task)}
                      />
                    ))}
                    {stageTasks.length === 0 && (
                      <p className="text-xs text-muted-foreground text-center py-4">
                        No tasks
                      </p>
                    )}
                  </div>

                  {/* Add task at bottom */}
                  {addingTaskInStage === stage.id ? (
                    <div className="mt-2">
                      <input
                        type="text"
                        autoFocus
                        value={newTaskTitle}
                        onChange={(e) => setNewTaskTitle(e.target.value)}
                        onKeyDown={(e) => handleTaskKeyDown(e, stage.id)}
                        onBlur={() => {
                          if (!newTaskTitle.trim()) {
                            setAddingTaskInStage(null);
                          }
                        }}
                        placeholder="Task title..."
                        className="w-full border rounded-md px-2 py-1.5 text-sm"
                        disabled={addTask.isPending}
                      />
                      <div className="flex gap-1 mt-1">
                        <button
                          onClick={() => handleAddTask(stage.id)}
                          disabled={!newTaskTitle.trim() || addTask.isPending}
                          className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
                        >
                          {addTask.isPending ? "Adding..." : "Add"}
                        </button>
                        <button
                          onClick={() => {
                            setAddingTaskInStage(null);
                            setNewTaskTitle("");
                          }}
                          className="px-2 py-1 text-xs border rounded hover:bg-muted"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setAddingTaskInStage(stage.id);
                        setNewTaskTitle("");
                      }}
                      className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground w-full justify-center py-1.5 rounded hover:bg-gray-100"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add Task
                    </button>
                  )}
                </div>
              );
            })}

          {/* Add Stage column */}
          <div className="w-72 shrink-0">
            {showNewStageInput ? (
              <div className="bg-gray-50 rounded-lg p-3 border border-dashed">
                <input
                  type="text"
                  autoFocus
                  value={newStageName}
                  onChange={(e) => setNewStageName(e.target.value)}
                  onKeyDown={handleStageKeyDown}
                  placeholder="Stage name..."
                  className="w-full border rounded-md px-2 py-1.5 text-sm mb-2"
                  disabled={createStage.isPending}
                />
                <div className="flex gap-1">
                  <button
                    onClick={handleCreateStage}
                    disabled={!newStageName.trim() || createStage.isPending}
                    className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
                  >
                    {createStage.isPending ? "Creating..." : "Add Stage"}
                  </button>
                  <button
                    onClick={() => {
                      setShowNewStageInput(false);
                      setNewStageName("");
                    }}
                    className="px-3 py-1 text-xs border rounded hover:bg-muted"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowNewStageInput(true)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground w-full justify-center py-8 rounded-lg border-2 border-dashed hover:border-gray-400 transition-colors"
              >
                <Plus className="h-4 w-4" />
                Add Stage
              </button>
            )}
          </div>
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>

      {/* Task detail panel */}
      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          pipelineId={pipelineId}
          stages={stageList}
          open={!!selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </>
  );
}
