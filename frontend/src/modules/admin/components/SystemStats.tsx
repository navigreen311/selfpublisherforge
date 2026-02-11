"use client";

import { Users, Building2, DollarSign, Activity, Database, Zap } from "lucide-react";
import { StatCard } from "@/components/shared/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { PlatformStats } from "../types";

interface SystemStatsProps {
  stats: PlatformStats | undefined;
  isLoading: boolean;
}

export function SystemStats({ stats, isLoading }: SystemStatsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="bg-card rounded-lg border p-6">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-32" />
          </div>
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
        <p className="text-red-800">Failed to load platform statistics.</p>
      </div>
    );
  }

  const activeUserPercentage = stats.total_users > 0
    ? ((stats.active_users / stats.total_users) * 100).toFixed(1)
    : "0.0";

  const activeOrgPercentage = stats.total_organizations > 0
    ? ((stats.active_organizations / stats.total_organizations) * 100).toFixed(1)
    : "0.0";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Total Users"
        value={stats.total_users.toLocaleString()}
        icon={Users}
      />
      <StatCard
        label="Active Users"
        value={`${stats.active_users.toLocaleString()} (${activeUserPercentage}%)`}
        icon={Activity}
      />
      <StatCard
        label="Organizations"
        value={stats.total_organizations.toLocaleString()}
        icon={Building2}
      />
      <StatCard
        label="Active Orgs"
        value={`${stats.active_organizations.toLocaleString()} (${activeOrgPercentage}%)`}
        icon={Building2}
      />
      <StatCard
        label="MRR"
        value={`$${(stats.mrr / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        icon={DollarSign}
      />
      <StatCard
        label="Active Subscriptions"
        value={stats.active_subscriptions.toLocaleString()}
        icon={DollarSign}
      />
      <StatCard
        label="API Calls Today"
        value={stats.total_api_calls_today.toLocaleString()}
        icon={Zap}
      />
      <StatCard
        label="Storage Used"
        value={`${stats.total_storage_gb.toFixed(2)} GB`}
        icon={Database}
      />
    </div>
  );
}
