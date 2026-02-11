import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "AI Agents",
  description: "Manage autonomous AI agents to automate your publishing workflows, monitor budgets, and track task progress.",
  noindex: true,
});

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { useAgents, useTasks, useBudgets, useEmergencyStop } from "@/modules/agents/hooks";
import { AgentCard } from "@/modules/agents/components/AgentCard";
import { TaskList } from "@/modules/agents/components/TaskList";
import { BudgetMeter } from "@/modules/agents/components/BudgetMeter";
import { Skeleton } from "@/components/ui/skeleton";
import type { Agent } from "@/modules/agents/types";
import { useTranslations } from "@/hooks/use-translations";

export default function AgentDashboardPage() {
  const t = useTranslations("agents");
  const router = useRouter();
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: tasksData, isLoading: tasksLoading } = useTasks({
    limit: 5,
  });
  const { data: budgetsData, isLoading: budgetsLoading } = useBudgets();
  const emergencyStop = useEmergencyStop();
  const [showConfirmStop, setShowConfirmStop] = useState(false);

  const agents = agentsData?.items || [];
  const recentTasks = tasksData?.items || [];
  const budgets = budgetsData?.items || [];

  const handleEmergencyStop = () => {
    emergencyStop.mutate(undefined, {
      onSuccess: () => {
        setShowConfirmStop(false);
      },
    });
  };

  // Map agent IDs to names for budget display
  const agentNameMap = new Map(agents.map((a) => [a.id, a.name]));

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
          <Skeleton className="h-10 w-36" />
        </div>

        {/* Agents grid skeleton */}
        <section aria-label={t("loadingAgents")}>
          <Skeleton className="h-6 w-40 mb-4" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-36" />
            ))}
          </div>
        </section>

        {/* Budget skeleton */}
        <section aria-label={t("loadingBudget")}>
          <Skeleton className="h-6 w-40 mb-4" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(2)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </section>

        {/* Tasks skeleton */}
        <section aria-label={t("loadingTasks")}>
          <Skeleton className="h-6 w-32 mb-4" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
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
        <div>
          {!showConfirmStop ? (
            <button
              onClick={() => setShowConfirmStop(true)}
              disabled={emergencyStop.isPending}
              aria-label={t("emergencyStopLabel")}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              {t("emergencyStop")}
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600 font-medium">
                {t("confirmStopMessage")}
              </span>
              <button
                onClick={handleEmergencyStop}
                disabled={emergencyStop.isPending}
                aria-label={t("confirmStopLabel")}
                className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                {emergencyStop.isPending && (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                )}
                {emergencyStop.isPending ? t("stopping") : t("confirm")}
              </button>
              <button
                onClick={() => setShowConfirmStop(false)}
                disabled={emergencyStop.isPending}
                aria-label={t("cancelStopLabel")}
                className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
              >
                {t("cancel")}
              </button>
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

      {/* Available agents */}
      <section aria-labelledby="available-agents-heading">
        <h2 id="available-agents-heading" className="text-lg font-semibold mb-4">{t("availableAgents")}</h2>
        {agentsLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-36" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onCreateTask={() => {
                  router.push(`/agents/tasks?create=true&agent_id=${agent.id}`);
                }}
                onConfigure={() => {
                  router.push(`/agents/settings?agent_id=${agent.id}`);
                }}
              />
            ))}
          </div>
        )}
      </section>

      {/* Budget overview */}
      {budgets.length > 0 && (
        <section aria-labelledby="budget-overview-heading">
          <h2 id="budget-overview-heading" className="text-lg font-semibold mb-4">{t("budgetOverview")}</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {budgets.map((budget) => (
              <BudgetMeter
                key={budget.id}
                budget={budget}
                agentName={agentNameMap.get(budget.agent_id) || "Unknown Agent"}
              />
            ))}
          </div>
        </section>
      )}

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
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <TaskList tasks={recentTasks} />
        )}
      </section>
    </div>
  );
}
