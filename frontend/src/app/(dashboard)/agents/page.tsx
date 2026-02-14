
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Plus } from "lucide-react";
import { useAgents, useTasks, useAgentUsage, useEmergencyStop } from "@/modules/agents/hooks";
import { Button } from "@/components/ui/button";
import { AgentStatsBar } from "@/modules/agents/components/AgentStatsBar";
import { EnhancedAgentCard } from "@/modules/agents/components/EnhancedAgentCard";
import { RecentTasksList } from "@/modules/agents/components/RecentTasksList";
import { NewTaskModal } from "@/modules/agents/components/NewTaskModal";
import { ConfigureAgentPanel } from "@/modules/agents/components/ConfigureAgentPanel";
import { CreateAgentModal } from "@/modules/agents/components/CreateAgentModal";
import { TaskExecutionView } from "@/modules/agents/components/TaskExecutionView";
import { Skeleton } from "@/components/ui/skeleton";
import type { Agent } from "@/modules/agents/types";
import { useTranslations } from "@/hooks/use-translations";

export default function AgentDashboardPage() {
  const t = useTranslations("agents");
  const router = useRouter();
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: tasksData, isLoading: tasksLoading } = useTasks({
    limit: 10,
  });
  const { data: usageData, isLoading: usageLoading } = useAgentUsage();
  const emergencyStop = useEmergencyStop();
  const [showConfirmStop, setShowConfirmStop] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(undefined);
  const [showNewTask, setShowNewTask] = useState(false);
  const [showConfigure, setShowConfigure] = useState(false);
  const [showCreateAgent, setShowCreateAgent] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | undefined>(undefined);

  const agents = agentsData?.items || [];
  const recentTasks = tasksData?.items || [];

  const handleEmergencyStop = () => {
    emergencyStop.mutate(undefined, {
      onSuccess: () => {
        setShowConfirmStop(false);
      },
    });
  };

  const handleNewTask = (agentId: string) => {
    setSelectedAgentId(agentId);
    setShowNewTask(true);
  };

  const handleConfigure = (agentId: string) => {
    setSelectedAgentId(agentId);
    setShowConfigure(true);
  };

  const handleTaskClick = (taskId: string) => {
    setActiveTaskId(taskId);
  };

  // Show task execution view if active task is set
  if (activeTaskId) {
    return (
      <TaskExecutionView
        taskId={activeTaskId}
        onClose={() => setActiveTaskId(undefined)}
      />
    );
  }

  // Full-page loading skeleton while initial data is being fetched
  if (agentsLoading && tasksLoading) {
    return (
      <div className="space-y-8" aria-label={t("loadingDashboard")}>
        {/* Header skeleton */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-40" />
            <Skeleton className="h-5 w-96" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-36" />
          </div>
        </div>

        {/* Stats bar skeleton */}
        <Skeleton className="h-24 w-full" />

        {/* Agents grid skeleton */}
        <section aria-label={t("loadingAgents")}>
          <Skeleton className="h-6 w-40 mb-4" />
          <div className="grid gap-4 md:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        </section>

        {/* Tasks skeleton */}
        <section aria-label={t("loadingTasks")}>
          <Skeleton className="h-6 w-32 mb-4" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <p className="text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setShowCreateAgent(true)}
            className="inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            {t("createAgent")}
          </Button>
          {!showConfirmStop ? (
            <Button
              variant="destructive"
              onClick={() => setShowConfirmStop(true)}
              disabled={emergencyStop.isPending}
              aria-label={t("emergencyStopLabel")}
            >
              {t("emergencyStop")}
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600 font-medium">
                {t("confirmStopMessage")}
              </span>
              <Button
                variant="destructive"
                onClick={handleEmergencyStop}
                disabled={emergencyStop.isPending}
                aria-label={t("confirmStopLabel")}
                size="sm"
              >
                {emergencyStop.isPending && (
                  <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                )}
                {emergencyStop.isPending ? t("stopping") : t("confirm")}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowConfirmStop(false)}
                disabled={emergencyStop.isPending}
                aria-label={t("cancelStopLabel")}
                size="sm"
              >
                {t("cancel")}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Emergency stop result */}
      {emergencyStop.isSuccess && (
        <div role="alert" className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {emergencyStop.data.message}
        </div>
      )}

      {/* Agent usage stats bar */}
      <AgentStatsBar stats={usageData} isLoading={usageLoading} />

      {/* Available agents */}
      <section aria-labelledby="available-agents-heading">
        <h2 id="available-agents-heading" className="text-lg font-semibold mb-4">{t("availableAgents")}</h2>
        {agentsLoading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {agents.map((agent) => (
              <EnhancedAgentCard
                key={agent.id}
                agent={agent}
                onNewTask={() => handleNewTask(agent.id)}
                onConfigure={() => handleConfigure(agent.id)}
              />
            ))}
          </div>
        )}
      </section>

      {/* Recent tasks */}
      <section aria-labelledby="recent-tasks-heading">
        <div className="flex items-center justify-between mb-4">
          <h2 id="recent-tasks-heading" className="text-lg font-semibold">{t("recentTasks")}</h2>
          <Link
            href="/agents/tasks"
            aria-label={t("viewAllLabel")}
            className="text-sm text-primary hover:underline"
          >
            {t("viewAll")}
          </Link>
        </div>
        {tasksLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <RecentTasksList
            tasks={recentTasks}
            onViewOutput={handleTaskClick}
          />
        )}
      </section>

      {/* Modals */}
      <NewTaskModal
        open={showNewTask}
        onOpenChange={setShowNewTask}
        agentId={selectedAgentId}
        agents={agents}
      />

      <ConfigureAgentPanel
        open={showConfigure}
        onOpenChange={setShowConfigure}
        agent={agents.find(a => a.id === selectedAgentId) || null}
      />

      <CreateAgentModal
        open={showCreateAgent}
        onOpenChange={setShowCreateAgent}
      />
    </div>
  );
}
