"use client";

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";
import {
  useTasks,
  useCreateTask,
  useApproveTask,
  useRejectTask,
  useCancelTask,
  useAgents,
} from "@/modules/agents/hooks";
import { RecentTasksList } from "@/modules/agents/components/RecentTasksList";
import { TaskExecutionView } from "@/modules/agents/components/TaskExecutionView";
import { NewTaskModal } from "@/modules/agents/components/NewTaskModal";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { AgentTask, TaskStatus } from "@/modules/agents/types";
import { useTranslations } from "@/hooks/use-translations";

export default function TasksPage() {
  const t = useTranslations("agents");
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [agentFilter, setAgentFilter] = useState<string>("all");
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [showNewTask, setShowNewTask] = useState(false);

  const STATUS_FILTERS: { value: TaskStatus | "all"; label: string }[] = [
    { value: "all", label: "All" },
    { value: "pending", label: "Pending" },
    { value: "running", label: "Running" },
    { value: "completed", label: "Complete" },
    { value: "failed", label: "Failed" },
  ];

  const { data: agentsData } = useAgents();
  const { data: tasksData, isLoading } = useTasks(
    statusFilter !== "all" ? { status: statusFilter as TaskStatus } : undefined
  );

  const tasks = tasksData?.items || [];
  const agents = agentsData?.items || [];

  // Filter by agent if selected
  const filteredTasks = agentFilter === "all"
    ? tasks
    : tasks.filter(task => task.agent_id === agentFilter);

  const handleTaskClick = (taskId: string) => {
    setActiveTaskId(taskId);
  };

  // Show task execution view if active task is set
  if (activeTaskId) {
    return (
      <TaskExecutionView
        taskId={activeTaskId}
        onClose={() => setActiveTaskId(null)}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("tasks.title")}</h1>
          <p className="text-muted-foreground">
            {t("tasks.subtitle")}
          </p>
        </div>
        <Button onClick={() => setShowNewTask(true)} className="inline-flex items-center gap-2">
          <Plus className="h-4 w-4" />
          {t("tasks.newTask")}
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Status filter pills */}
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setStatusFilter(filter.value)}
              className={cn(
                "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
                statusFilter === filter.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {/* Agent filter dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Agent:</label>
          <Select value={agentFilter} onValueChange={setAgentFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Agents" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Agents</SelectItem>
              {agents.map((agent) => (
                <SelectItem key={agent.id} value={agent.id}>
                  {agent.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Task count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredTasks.length} of {tasksData?.total_count ?? 0} tasks
      </div>

      {/* Task list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading tasks...
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
          <p className="text-muted-foreground">No tasks found</p>
          <Button
            onClick={() => setShowNewTask(true)}
            variant="link"
            className="mt-2"
          >
            Create your first task
          </Button>
        </div>
      ) : (
        <RecentTasksList
          tasks={filteredTasks}
          onViewOutput={handleTaskClick}
        />
      )}

      {/* New task modal */}
      <NewTaskModal
        open={showNewTask}
        onOpenChange={setShowNewTask}
        agents={agents}
      />
    </div>
  );
}
