"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface AgentStats {
  total_tasks: number;
  running_tasks: number;
  total_tokens: number;
  total_cost: number;
}

interface AgentStatsBarProps {
  stats: AgentStats | undefined;
  isLoading: boolean;
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "k";
  }
  return num.toString();
}

function formatCurrency(amount: number): string {
  return "$" + amount.toFixed(2);
}

function StatCard({
  label,
  value,
  isLoading,
}: {
  label: string;
  value: string;
  isLoading: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          {isLoading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <p className="text-2xl font-bold">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function AgentStatsBar({ stats, isLoading }: AgentStatsBarProps) {
  const totalTasks = stats?.total_tasks ?? 0;
  const runningTasks = stats?.running_tasks ?? 0;
  const totalTokens = stats?.total_tokens ?? 0;
  const totalCost = stats?.total_cost ?? 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Total Tasks"
        value={totalTasks.toString()}
        isLoading={isLoading}
      />
      <StatCard
        label="Running"
        value={runningTasks.toString()}
        isLoading={isLoading}
      />
      <StatCard
        label="Tokens Used"
        value={formatNumber(totalTokens)}
        isLoading={isLoading}
      />
      <StatCard
        label="Monthly Cost"
        value={formatCurrency(totalCost)}
        isLoading={isLoading}
      />
    </div>
  );
}
