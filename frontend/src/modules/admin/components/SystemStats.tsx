"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, Activity, Building2, BookOpen, Zap, Database, DollarSign, TrendingUp } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface SystemStatsProps {
  stats: any;
  isLoading: boolean;
}

// Format helpers
function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return "0";
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}k`;
  return num.toString();
}

function formatBytes(bytes: number | undefined | null): string {
  if (bytes === undefined || bytes === null) return "--";
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

export function SystemStats({ stats, isLoading }: SystemStatsProps) {
  // Calculate derived values
  const usersThisMonth = stats?.new_users_this_month ?? 0;
  const usersThisMonthText = usersThisMonth > 0 ? `+${formatNumber(usersThisMonth)} this month` : undefined;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Row 1 */}
      <StatCard
        label="Total Users"
        value={formatNumber(stats?.total_users)}
        subtitle={usersThisMonthText}
        icon={Users}
        isLoading={isLoading}
      />
      <StatCard
        label="Active This Week"
        value={formatNumber(stats?.active_users_week ?? stats?.active_users)}
        icon={Activity}
        isLoading={isLoading}
      />
      <StatCard
        label="Organizations"
        value={formatNumber(stats?.total_organizations)}
        icon={Building2}
        isLoading={isLoading}
      />
      <StatCard
        label="Total Books"
        value={formatNumber(stats?.total_books ?? stats?.books)}
        icon={BookOpen}
        isLoading={isLoading}
      />

      {/* Row 2 */}
      <StatCard
        label="AI Tasks This Month"
        value={formatNumber(stats?.ai_tasks_month ?? stats?.ai_tasks_this_month)}
        icon={Zap}
        isLoading={isLoading}
      />
      <StatCard
        label="Tokens Used"
        value={formatNumber(stats?.tokens_month ?? stats?.tokens_used)}
        icon={TrendingUp}
        isLoading={isLoading}
      />
      <StatCard
        label="Storage Used"
        value={formatBytes(stats?.storage_used_bytes ?? (stats?.total_storage_gb ? stats.total_storage_gb * 1_073_741_824 : null))}
        icon={Database}
        isLoading={isLoading}
      />
      <StatCard
        label="Monthly Revenue"
        value={formatCurrency(stats?.monthly_revenue ?? (stats?.mrr ? stats.mrr / 100 : null))}
        icon={DollarSign}
        isLoading={isLoading}
      />
    </div>
  );
}
