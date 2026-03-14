"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, Activity, Building2, BookOpen, Zap, Database, DollarSign, TrendingUp, AlertCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { PlatformStatsDetailed } from "@/modules/admin/types";

interface SystemStatsProps {
  stats: PlatformStatsDetailed | undefined;
  isLoading: boolean;
  isError?: boolean;
  error?: unknown;
}

// Format helpers
function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return "0";
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}k`;
  return num.toString();
}

function formatBytes(bytes: number | undefined | null): string {
  if (bytes === undefined || bytes === null) return "0 B";
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  if (bytes >= 1_024) return `${(bytes / 1_024).toFixed(1)} KB`;
  return `${bytes} B`;
}

function formatCurrency(amount: number | undefined | null): string {
  if (amount === undefined || amount === null) return "$0";
  return `$${amount.toLocaleString()}`;
}

interface StatCardProps {
  label: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  isLoading: boolean;
}

function StatCard({ label, value, subtitle, icon: Icon, isLoading }: StatCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32 mb-1" />
              {subtitle && <Skeleton className="h-3 w-20" />}
            </div>
            <Skeleton className="h-10 w-10 rounded-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <h3 className="text-2xl font-bold mt-1">{value}</h3>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          <div className="ml-4">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Icon className="h-5 w-5 text-primary" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const resp = (error as any).response;
    if (resp?.status === 403) return "You do not have permission to view platform statistics.";
    if (resp?.status === 401) return "Please log in to view platform statistics.";
  }
  return "Failed to load platform statistics. Please try again later.";
}

export function SystemStats({ stats, isLoading, isError, error }: SystemStatsProps) {
  if (isError) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm">{getErrorMessage(error)}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Row 1 */}
      <StatCard
        label="Total Users"
        value={formatNumber(stats?.users_total)}
        icon={Users}
        isLoading={isLoading}
      />
      <StatCard
        label="Active This Week"
        value={formatNumber(stats?.users_active_week)}
        icon={Activity}
        isLoading={isLoading}
      />
      <StatCard
        label="Organizations"
        value={formatNumber(stats?.organizations)}
        icon={Building2}
        isLoading={isLoading}
      />
      <StatCard
        label="Total Books"
        value={formatNumber(stats?.books)}
        icon={BookOpen}
        isLoading={isLoading}
      />

      {/* Row 2 */}
      <StatCard
        label="AI Tasks This Month"
        value={formatNumber(stats?.ai_tasks_month)}
        icon={Zap}
        isLoading={isLoading}
      />
      <StatCard
        label="Tokens Used"
        value={formatNumber(stats?.tokens_month)}
        icon={TrendingUp}
        isLoading={isLoading}
      />
      <StatCard
        label="Storage Used"
        value={formatBytes(stats?.storage_used_bytes)}
        icon={Database}
        isLoading={isLoading}
      />
      <StatCard
        label="Monthly Revenue"
        value={formatCurrency(stats?.monthly_revenue)}
        icon={DollarSign}
        isLoading={isLoading}
      />
    </div>
  );
}
