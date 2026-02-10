"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAgents, useTasks, useBudgets, useEmergencyStop } from "@/modules/agents/hooks";
import { AgentCard } from "@/modules/agents/components/AgentCard";
import { TaskList } from "@/modules/agents/components/TaskList";
import { BudgetMeter } from "@/modules/agents/components/BudgetMeter";
import { Skeleton } from "@/components/ui/skeleton";
import type { Agent } from "@/modules/agents/types";

export default function AgentDashboardPage() {
  const router = useRouter();
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: tasksData, isLoading: tasksLoading } = useTasks({
    limit: 5,
  });
  const { data: budgetsData } = useBudgets();
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

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Agents</h1>
          <p className="text-muted-foreground">
            Manage your AI agent workforce, monitor tasks, and control budgets.
          </p>
        </div>
        <div>
          {!showConfirmStop ? (
            <button
              onClick={() => setShowConfirmStop(true)}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              Emergency Stop
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600 font-medium">
                Cancel ALL running tasks?
              </span>
              <button
                onClick={handleEmergencyStop}
                disabled={emergencyStop.isPending}
                className="rounded-md bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                {emergencyStop.isPending ? "Stopping..." : "Confirm"}
              </button>
              <button
                onClick={() => setShowConfirmStop(false)}
                className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
              >
                Cancel
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
      <section>
        <h2 className="text-lg font-semibold mb-4">Available Agents</h2>
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
        <section>
          <h2 className="text-lg font-semibold mb-4">Budget Overview</h2>
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
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Tasks</h2>
          <Link
            href="/agents/tasks"
            className="text-sm text-primary hover:underline"
          >
            View all
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
