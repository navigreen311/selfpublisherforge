import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Dashboard",
  description: "View your publishing activity, track book performance, and monitor royalties in one place.",
  noindex: true,
});

"use client";

import {
  BookOpen,
  DollarSign,
  TrendingUp,
  BarChart3,
  Plus,
  ArrowRight,
  Bot,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { StatCard } from "@/components/shared/stat-card";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { useDashboard } from "@/modules/analytics/hooks";
import type { KPICard as KPICardType, RoyaltyRecord } from "@/modules/analytics/hooks";
import { type LucideIcon } from "lucide-react";

// ── Icon mapping for KPI labels ─────────────────────────────────────────

const KPI_ICON_MAP: Record<string, LucideIcon> = {
  "total revenue": DollarSign,
  "monthly revenue": DollarSign,
  revenue: DollarSign,
  "total books": BookOpen,
  books: BookOpen,
  "units sold": TrendingUp,
  "total units": TrendingUp,
  units: TrendingUp,
  "net profit": DollarSign,
  "avg revenue": BarChart3,
  "average revenue": BarChart3,
};

function getIconForKPI(label: string): LucideIcon {
  const normalized = label.toLowerCase();
  for (const [key, icon] of Object.entries(KPI_ICON_MAP)) {
    if (normalized.includes(key)) return icon;
  }
  return BarChart3;
}

// ── Quick Actions (static — kept as-is per prompt instructions) ─────────

const quickActions = [
  { label: "New Project", href: "/projects/new", icon: Plus },
  { label: "View Projects", href: "/projects", icon: ArrowRight },
  { label: "AI Agents", href: "/agents", icon: Bot },
  { label: "Analytics", href: "/analytics", icon: ArrowRight },
];

// ── Helper: format relative time ────────────────────────────────────────

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

// ── Skeleton components ─────────────────────────────────────────────────

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-3 w-28" />
          </div>
          <Skeleton className="h-12 w-12 rounded-full" />
        </div>
      </CardContent>
    </Card>
  );
}

function ActivitySkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="flex items-start gap-3 pb-4 last:pb-0 border-b last:border-0"
        >
          <Skeleton className="mt-1 h-2 w-2 rounded-full shrink-0" />
          <div className="flex-1 min-w-0 space-y-1">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-64" />
          </div>
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

function ProjectsSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="flex items-center justify-between py-2 border-b last:border-0"
        >
          <div className="flex items-center gap-3">
            <Skeleton className="h-4 w-4" />
            <div className="space-y-1">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here is an overview of your publishing activity.
          </p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> New Project
          </Link>
        </Button>
      </div>

      {/* Stats Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Skeleton */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
            <CardDescription>Your latest publishing activity</CardDescription>
          </CardHeader>
          <CardContent>
            <ActivitySkeleton />
          </CardContent>
        </Card>

        {/* Quick Actions (rendered normally even while loading) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Common tasks at a glance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Button
                    key={action.label}
                    variant="outline"
                    className="h-auto py-4 flex-col gap-2"
                    asChild
                  >
                    <Link href={action.href}>
                      <Icon className="h-5 w-5" />
                      <span className="text-xs">{action.label}</span>
                    </Link>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects Skeleton */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Recent Projects</CardTitle>
            <CardDescription>Your latest projects</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/projects">View all</Link>
          </Button>
        </CardHeader>
        <CardContent>
          <ProjectsSkeleton />
        </CardContent>
      </Card>
    </div>
  );
}

// ── Error state ─────────────────────────────────────────────────────────

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here is an overview of your publishing activity.
          </p>
        </div>
      </div>

      <Card className="border-destructive/50">
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
            <div className="rounded-full bg-destructive/10 p-3">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-semibold">Failed to load dashboard data</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                We could not retrieve your dashboard information. This may be due to a
                network issue or a server error. Please try again.
              </p>
            </div>
            <Button onClick={onRetry} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Try again
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Badge variant helper ────────────────────────────────────────────────

const badgeVariant = (status: string) => {
  switch (status) {
    case "active":
    case "published":
      return "default" as const;
    case "draft":
      return "secondary" as const;
    case "archived":
      return "outline" as const;
    default:
      return "secondary" as const;
  }
};

// ── Main Dashboard Page ─────────────────────────────────────────────────

export default function DashboardPage() {
  const { data: dashboard, isLoading, error, refetch } = useDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <ErrorState onRetry={() => refetch()} />;
  }

  // Map KPI data from API to StatCard props
  const kpiStats = (dashboard?.kpis ?? []).map((kpi: KPICardType) => ({
    label: kpi.label,
    value: kpi.value,
    icon: getIconForKPI(kpi.label),
    trend:
      kpi.change_percent != null
        ? {
            value: Math.abs(kpi.change_percent),
            isPositive: kpi.change_direction === "up",
          }
        : undefined,
  }));

  // Map recent royalties to activity items
  const recentActivity = (dashboard?.recent_royalties ?? [])
    .slice(0, 5)
    .map((royalty: RoyaltyRecord) => ({
      id: royalty.id,
      action: `Royalty: ${royalty.platform.replace("_", " ")}`,
      detail: `${royalty.title} — ${royalty.net_units} units, $${royalty.net_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} revenue`,
      time: formatRelativeTime(royalty.created_at),
      type: royalty.net_revenue > 0 ? ("success" as const) : ("info" as const),
    }));

  // Map top_books from API to recent projects display
  const recentProjects = (dashboard?.top_books ?? []).slice(0, 5).map((book, index) => ({
    id: String(book.id || index),
    title: String(book.title || "Untitled"),
    type: String(book.format_type || book.type || "book"),
    status: String(book.status || "active"),
    revenue: Number(book.revenue || 0),
    units: Number(book.units || 0),
  }));

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here is an overview of your publishing activity.
          </p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> New Project
          </Link>
        </Button>
      </div>

      {/* Stats Grid — real KPI data from API */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiStats.length > 0 ? (
          kpiStats.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))
        ) : (
          <Card className="col-span-full">
            <CardContent className="p-6 text-center text-muted-foreground">
              No KPI data available yet. Import royalty data to get started.
            </CardContent>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity — from recent_royalties */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
            <CardDescription>Your latest royalty activity</CardDescription>
          </CardHeader>
          <CardContent>
            {recentActivity.length > 0 ? (
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-3 pb-4 last:pb-0 border-b last:border-0"
                  >
                    <div
                      className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                        activity.type === "success"
                          ? "bg-green-500"
                          : "bg-blue-500"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">{activity.action}</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {activity.detail}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {activity.time}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-6">
                No recent activity. Import your first royalty report to see data here.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions — kept as-is */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Common tasks at a glance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Button
                    key={action.label}
                    variant="outline"
                    className="h-auto py-4 flex-col gap-2"
                    asChild
                  >
                    <Link href={action.href}>
                      <Icon className="h-5 w-5" />
                      <span className="text-xs">{action.label}</span>
                    </Link>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects — from top_books API data */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Top Books</CardTitle>
            <CardDescription>Your best-performing titles</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/analytics">View analytics</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {recentProjects.length > 0 ? (
            <div className="space-y-3">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{project.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {project.units} units &middot; $
                        {project.revenue.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </p>
                    </div>
                  </div>
                  <Badge variant={badgeVariant(project.status)}>
                    {project.status}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-6">
              No book data available yet. Import royalty data to see your top
              performers.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
