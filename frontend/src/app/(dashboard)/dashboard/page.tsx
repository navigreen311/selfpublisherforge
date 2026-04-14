
"use client";

import { Suspense, useCallback, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
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
  Search,
  Pencil,
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

// Dashboard widgets
import { OnboardingChecklist } from "@/components/dashboard/OnboardingChecklist";
import { WritingProgress } from "@/components/dashboard/WritingProgress";
import { PublishingPipeline } from "@/components/dashboard/PublishingPipeline";
import { UpcomingDeadlines } from "@/components/dashboard/UpcomingDeadlines";
import { AgentActivityFeed } from "@/components/dashboard/AgentActivityFeed";
// Phase 2.1 aggregate widgets (GET /api/v1/dashboard)
import { RevenueTrendChart } from "@/components/dashboard/RevenueTrendChart";
import { AIInsightsPanel } from "@/components/dashboard/AIInsightsPanel";
import { ActivePipelinesPanel } from "@/components/dashboard/ActivePipelinesPanel";

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
  "active projects": Pencil,
  "words today": Pencil,
};

function getIconForKPI(label: string): LucideIcon {
  const normalized = label.toLowerCase();
  for (const [key, icon] of Object.entries(KPI_ICON_MAP)) {
    if (normalized.includes(key)) return icon;
  }
  return BarChart3;
}

// ── Quick Actions ────────────────────────────────────────────────────────

const quickActions = [
  { labelKey: "quickActions.newProject", href: "/projects/new", icon: Plus },
  { labelKey: "quickActions.viewProjects", href: "/projects", icon: ArrowRight },
  { labelKey: "quickActions.aiAgents", href: "/agents", icon: Bot },
  { labelKey: "quickActions.analytics", href: "/analytics", icon: BarChart3 },
  { labelKey: "quickActions.marketResearch", href: "/market", icon: Search },
  { labelKey: "quickActions.writingStudio", href: "/writing", icon: Pencil },
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

function DashboardSkeleton() {
  const t = useTranslations("dashboard");

  return (
    <div className="space-y-6 sm:space-y-8 px-4 sm:px-6 lg:px-0">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm sm:text-base text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button asChild className="w-full sm:w-auto">
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> {t("newProject")}
          </Link>
        </Button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {[1, 2, 3, 4].map((i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
        <Card className="lg:col-span-3"><CardContent className="p-6"><Skeleton className="h-40" /></CardContent></Card>
        <Card className="lg:col-span-2"><CardContent className="p-6"><Skeleton className="h-40" /></CardContent></Card>
      </div>
      <Card><CardContent className="p-6"><Skeleton className="h-24" /></CardContent></Card>
    </div>
  );
}

// ── Error state ─────────────────────────────────────────────────────────

function ErrorState({ onRetry }: { onRetry: () => void }) {
  const t = useTranslations("dashboard");
  return (
    <div className="space-y-6 sm:space-y-8 px-4 sm:px-6 lg:px-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm sm:text-base text-muted-foreground">{t("subtitle")}</p>
        </div>
      </div>
      <Card className="border-destructive/50">
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
            <div className="rounded-full bg-destructive/10 p-3">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-semibold">{t("error.title")}</h3>
              <p className="text-sm text-muted-foreground max-w-md">{t("error.message")}</p>
            </div>
            <Button onClick={onRetry} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              {t("error.retry")}
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
  const t = useTranslations("dashboard");
  const { data: dashboard, isLoading, error, refetch } = useDashboard();
  const [showOnboarding, setShowOnboarding] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("spf-onboarding-dismissed") !== "true";
  });

  const handleDismissOnboarding = useCallback(() => {
    setShowOnboarding(false);
    localStorage.setItem("spf-onboarding-dismissed", "true");
  }, []);

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

  // Map top_books from API
  const recentProjects = (dashboard?.top_books ?? []).slice(0, 5).map((book, index) => ({
    id: String(book.id || index),
    title: String(book.title || "Untitled"),
    type: String(book.format_type || book.type || "book"),
    status: String(book.status || "active"),
    revenue: Number(book.revenue || 0),
    units: Number(book.units || 0),
  }));

  const hasProjects = recentProjects.length > 0 || (kpiStats.length > 0);

  return (
    <div className="space-y-6 sm:space-y-8 px-4 sm:px-6 lg:px-0">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm sm:text-base text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button asChild className="w-full sm:w-auto">
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> {t("newProject")}
          </Link>
        </Button>
      </div>

      {/* ROW 1: Onboarding Checklist (new users only) */}
      {showOnboarding && !hasProjects && (
        <OnboardingChecklist
          hasProjects={hasProjects}
          onDismiss={handleDismissOnboarding}
        />
      )}

      {/* ROW 2: Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {kpiStats.length > 0 ? (
          kpiStats.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))
        ) : (
          <>
            <Card className="hover:border-primary/30 transition-colors">
              <CardContent className="p-4 sm:p-6">
                <p className="text-xs text-muted-foreground">{t("stats.activeProjects")}</p>
                <p className="text-2xl font-bold text-muted-foreground/50 mt-1">0</p>
              </CardContent>
            </Card>
            <Card className="hover:border-primary/30 transition-colors">
              <CardContent className="p-4 sm:p-6">
                <p className="text-xs text-muted-foreground">{t("stats.wordsWrittenToday")}</p>
                <p className="text-2xl font-bold text-muted-foreground/50 mt-1">0</p>
              </CardContent>
            </Card>
            <Card className="hover:border-primary/30 transition-colors">
              <CardContent className="p-4 sm:p-6">
                <p className="text-xs text-muted-foreground">{t("stats.booksPublished")}</p>
                <p className="text-2xl font-bold text-muted-foreground/50 mt-1">0</p>
              </CardContent>
            </Card>
            <Card className="hover:border-primary/30 transition-colors">
              <CardContent className="p-4 sm:p-6">
                <p className="text-xs text-muted-foreground">{t("stats.totalRevenue")}</p>
                <p className="text-2xl font-bold text-muted-foreground/50 mt-1">$0</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* ROW 2b: Revenue Trend (60%) + AI Insights (40%) -- Phase 2.1 aggregate */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
        <div className="lg:col-span-3">
          <RevenueTrendChart />
        </div>
        <div className="lg:col-span-2">
          <AIInsightsPanel />
        </div>
      </div>

      {/* ROW 2c: Active Pipelines (full width) -- Phase 2.1 aggregate */}
      <ActivePipelinesPanel />

      {/* ROW 3: Writing Progress (60%) + Upcoming Deadlines (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
        <div className="lg:col-span-3">
          <WritingProgress />
        </div>
        <div className="lg:col-span-2">
          <UpcomingDeadlines />
        </div>
      </div>

      {/* ROW 4: Publishing Pipeline (full width) */}
      <PublishingPipeline />

      {/* ROW 5: Recent Activity (50%) + Quick Actions (25%) + Agent Activity (25%) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg">{t("recentActivity.title")}</CardTitle>
            <CardDescription className="text-xs sm:text-sm">{t("recentActivity.subtitle")}</CardDescription>
          </CardHeader>
          <CardContent>
            {recentActivity.length > 0 ? (
              <div className="space-y-3 sm:space-y-4">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-2 sm:gap-3 pb-3 sm:pb-4 last:pb-0 border-b last:border-0"
                  >
                    <div
                      className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                        activity.type === "success" ? "bg-green-500" : "bg-blue-500"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs sm:text-sm font-medium">{activity.action}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground truncate">
                        {activity.detail}
                      </p>
                    </div>
                    <span className="text-[10px] sm:text-xs text-muted-foreground whitespace-nowrap">
                      {activity.time}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground">{t("recentActivity.noActivity")}</p>
                <Button variant="outline" size="sm" className="mt-3" asChild>
                  <Link href="/analytics">Import Royalty Data</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base sm:text-lg">{t("quickActions.title")}</CardTitle>
            <CardDescription className="text-xs sm:text-sm">{t("quickActions.subtitle")}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Button
                    key={action.labelKey}
                    variant="outline"
                    className="h-auto py-3 sm:py-4 flex-col gap-1 sm:gap-2"
                    asChild
                  >
                    <Link href={action.href}>
                      <Icon className="h-4 w-4 sm:h-5 sm:w-5" />
                      <span className="text-[10px] sm:text-xs">{t(action.labelKey)}</span>
                    </Link>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Agent Activity */}
        <AgentActivityFeed />
      </div>

      {/* ROW 6: Top Books (full width) */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <CardTitle className="text-base sm:text-lg">{t("topBooks.title")}</CardTitle>
            <CardDescription className="text-xs sm:text-sm">{t("topBooks.subtitle")}</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild className="w-full sm:w-auto">
            <Link href="/analytics">{t("viewAnalytics")}</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {recentProjects.length > 0 ? (
            <div className="space-y-2 sm:space-y-3">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  className="flex items-center justify-between py-2 border-b last:border-0 gap-2"
                >
                  <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                    <BookOpen className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs sm:text-sm font-medium truncate">{project.title}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">
                        {project.units} {t("units")} &middot; $
                        {project.revenue.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </p>
                    </div>
                  </div>
                  <Badge variant={badgeVariant(project.status)} className="shrink-0 text-[10px] sm:text-xs">
                    {project.status}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <BookOpen className="h-8 w-8 mx-auto text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground mt-2">{t("topBooks.noBooks")}</p>
              <Button variant="outline" size="sm" className="mt-3" asChild>
                <Link href="/projects/new">Create Your First Project</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
