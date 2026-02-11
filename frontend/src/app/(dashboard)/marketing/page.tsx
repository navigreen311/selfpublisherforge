import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Marketing",
  description: "Plan book launches, manage email sequences, schedule social media, and run ARC campaigns.",
  noindex: true,
});

"use client";

import { useState, useCallback } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { useLaunchPlans, useEmailSequences, useSocialCalendar, useARCCampaigns, useRecentActivity } from "@/modules/marketing/hooks";
import type { RecentActivityItem } from "@/modules/marketing/hooks";
import { ARCTable } from "@/modules/marketing/components/ARCTable";
import { SocialCalendar } from "@/modules/marketing/components/SocialCalendar";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Rocket, Mail, Activity, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useTranslations } from "@/hooks/use-translations";

type Tab = "overview" | "launch-plans" | "email" | "social" | "arc";

interface DeleteTarget {
  id: string;
  name: string;
  type: "launch-plan" | "email-sequence" | "arc-campaign";
}

// Tabs will be localized in the component

const DELETE_CONFIG: Record<
  DeleteTarget["type"],
  { endpoint: string; queryKey: string[]; label: string }
> = {
  "launch-plan": {
    endpoint: "/api/v1/marketing/launch-plans",
    queryKey: ["marketing", "launch-plans"],
    label: "launch plan",
  },
  "email-sequence": {
    endpoint: "/api/v1/marketing/email-sequences",
    queryKey: ["marketing", "email-sequences"],
    label: "email sequence",
  },
  "arc-campaign": {
    endpoint: "/api/v1/marketing/arc",
    queryKey: ["marketing", "arc"],
    label: "ARC campaign",
  },
};

export default function MarketingDashboard() {
  const t = useTranslations("marketing");
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const queryClient = useQueryClient();

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: t("tabs.overview") },
    { id: "launch-plans", label: t("tabs.launchPlans") },
    { id: "email", label: t("tabs.email") },
    { id: "social", label: t("tabs.social") },
    { id: "arc", label: t("tabs.arc") },
  ];

  const { data: launchPlans, isLoading: plansLoading } = useLaunchPlans();
  const { data: emailSequences, isLoading: seqLoading } = useEmailSequences();
  const { data: socialCalendar, isLoading: socialLoading } = useSocialCalendar();
  const { data: arcCampaigns, isLoading: arcLoading } = useARCCampaigns();

  const handleDeleteRequest = useCallback((target: DeleteTarget) => {
    setDeleteTarget(target);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return;

    const config = DELETE_CONFIG[deleteTarget.type];
    setIsDeleting(true);

    try {
      await api.delete(`${config.endpoint}/${deleteTarget.id}`);
      await queryClient.invalidateQueries({ queryKey: config.queryKey });
    } catch {
      // Error handling is managed by the global API interceptor
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  }, [deleteTarget, queryClient]);

  const handleDeleteDialogChange = useCallback(
    (open: boolean) => {
      if (!open && !isDeleting) {
        setDeleteTarget(null);
      }
    },
    [isDeleting]
  );

  const deleteConfig = deleteTarget ? DELETE_CONFIG[deleteTarget.type] : null;

  return (
    <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0">
      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={handleDeleteDialogChange}
        title={t("delete.title", { type: deleteConfig?.label || "item" })}
        description={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.name}"? This action cannot be undone.`
            : ""
        }
        confirmLabel={t("delete.confirm")}
        variant="destructive"
        onConfirm={handleDeleteConfirm}
        loading={isDeleting}
      />

      {/* Page Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold">{t("title")}</h1>
        <p className="text-xs sm:text-sm text-muted-foreground mt-1">
          {t("subtitle")}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b overflow-x-auto -mx-4 sm:mx-0">
        <nav className="flex gap-2 sm:gap-4 px-4 sm:px-0 min-w-max">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <OverviewTab
          plansCount={launchPlans?.total_count || 0}
          sequencesCount={emailSequences?.total_count || 0}
          socialPostsCount={socialCalendar?.posts.length || 0}
          arcCount={arcCampaigns?.total_count || 0}
          setActiveTab={setActiveTab}
          t={t}
        />
      )}

      {activeTab === "launch-plans" && (
        <LaunchPlansTab
          plans={launchPlans?.items || []}
          isLoading={plansLoading}
          onDelete={handleDeleteRequest}
        />
      )}

      {activeTab === "email" && (
        <EmailTab
          sequences={emailSequences?.items || []}
          isLoading={seqLoading}
          onDelete={handleDeleteRequest}
        />
      )}

      {activeTab === "social" && (
        <SocialCalendar calendar={socialCalendar} isLoading={socialLoading} />
      )}

      {activeTab === "arc" && (
        <ARCTable
          campaigns={arcCampaigns?.items || []}
          isLoading={arcLoading}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const ACTIVITY_ICONS: Record<RecentActivityItem["type"], string> = {
  launch_plan: "bg-blue-100 text-blue-700",
  email_sequence: "bg-green-100 text-green-700",
  arc_campaign: "bg-orange-100 text-orange-700",
  social_post: "bg-purple-100 text-purple-700",
};

function formatRelativeDate(dateStr: string, t: (key: string, vars?: Record<string, string | number>) => string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return t("timeAgo.justNow"); // Note: Using exact match from timeAgo JSON
  if (diffMins < 60) return t("timeAgo.minutesAgo", { count: diffMins });
  if (diffHours < 24) return t("timeAgo.hoursAgo", { count: diffHours });
  if (diffDays < 7) return t("timeAgo.daysAgo", { count: diffDays });
  return date.toLocaleDateString();
}

function OverviewTab({
  plansCount,
  sequencesCount,
  socialPostsCount,
  arcCount,
  setActiveTab,
}: {
  plansCount: number;
  sequencesCount: number;
  socialPostsCount: number;
  arcCount: number;
  setActiveTab: (tab: Tab) => void;
}) {
  const t = useTranslations("marketing");
  const { items: recentActivity, isLoading: activityLoading } = useRecentActivity();

  const stats = [
    { label: t("overview.stats.launchPlans"), value: plansCount, color: "bg-blue-500" },
    { label: t("overview.stats.emailSequences"), value: sequencesCount, color: "bg-green-500" },
    { label: t("overview.stats.socialPosts"), value: socialPostsCount, color: "bg-purple-500" },
    { label: t("overview.stats.arcCampaigns"), value: arcCount, color: "bg-orange-500" },
  ];

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-card rounded-lg border p-4 sm:p-6">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full ${stat.color}`} />
              <span className="text-xs sm:text-sm text-muted-foreground">{stat.label}</span>
            </div>
            <div className="text-2xl sm:text-3xl font-bold mt-1 sm:mt-2">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-card rounded-lg border p-4 sm:p-6">
          <h3 className="text-sm sm:text-base font-semibold mb-3 sm:mb-4">{t("overview.quickActions.title")}</h3>
          <div className="space-y-2">
            <Link
              href="/marketing/launch/new"
              className="block p-2 sm:p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs sm:text-sm"
            >
              {t("overview.quickActions.generateLaunchPlan")}
            </Link>
            <Link
              href="/marketing/email"
              className="block p-2 sm:p-3 rounded-lg bg-green-50 hover:bg-green-100 text-green-700 text-xs sm:text-sm"
            >
              {t("overview.quickActions.createEmailSequence")}
            </Link>
          </div>
        </div>

        <div className="bg-card rounded-lg border p-4 sm:p-6">
          <h3 className="text-sm sm:text-base font-semibold mb-3 sm:mb-4">{t("overview.recentActivity.title")}</h3>
          {activityLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <Skeleton className="w-8 h-8 rounded-full" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3 w-3/4" />
                    <Skeleton className="h-2 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentActivity.length === 0 ? (
            <EmptyState
              icon={Activity}
              title={t("overview.recentActivity.noActivity")}
              description={t("overview.recentActivity.description")}
              actionLabel={t("overview.recentActivity.action")}
              onAction={() => setActiveTab("launch-plans")}
            />
          ) : (
            <div className="space-y-2 sm:space-y-3">
              {recentActivity.map((item) => (
                <div key={item.id} className="flex items-start gap-2 sm:gap-3">
                  <div
                    className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] sm:text-xs font-medium ${ACTIVITY_ICONS[item.type]}`}
                  >
                    {item.type === "launch_plan" && "LP"}
                    {item.type === "email_sequence" && "ES"}
                    {item.type === "arc_campaign" && "AC"}
                    {item.type === "social_post" && "SP"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm font-medium text-foreground truncate">
                      {item.action}
                    </p>
                    <p className="text-[10px] sm:text-xs text-muted-foreground truncate">{item.title}</p>
                  </div>
                  <span className="text-[10px] sm:text-xs text-muted-foreground flex-shrink-0">
                    {formatRelativeDate(item.timestamp, t)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LaunchPlansTab({
  plans,
  isLoading,
  onDelete,
}: {
  plans: Array<{
    id: string;
    title: string;
    status: string;
    launch_date?: string;
    genre?: string;
    created_at: string;
  }>;
  isLoading: boolean;
  onDelete: (target: DeleteTarget) => void;
}) {
  const t = useTranslations("marketing");
  const router = useRouter();

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const statusColors: Record<string, string> = {
    draft: "bg-muted text-foreground",
    active: "bg-green-100 text-green-700",
    completed: "bg-blue-100 text-blue-700",
    archived: "bg-red-100 text-red-700",
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3 sm:space-y-4">
      <div className="flex justify-end">
        <Link
          href="/marketing/launch/new"
          className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-xs sm:text-sm text-center"
        >
          + {t("launchPlans.generateNew")}
        </Link>
      </div>

      {plans.length === 0 ? (
        <div className="border rounded-lg">
          <EmptyState
            icon={Rocket}
            title={t("launchPlans.empty.title")}
            description={t("launchPlans.empty.description")}
            actionLabel={t("launchPlans.empty.action")}
            onAction={() => router.push("/marketing/launch/new")}
          />
        </div>
      ) : (
        <div className="space-y-2 sm:space-y-3">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className="bg-card border rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow flex items-center gap-2 sm:gap-3"
            >
              <Link
                href={`/marketing/launch/${plan.id}`}
                className="flex-1 min-w-0"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="text-sm sm:text-base font-semibold truncate">{plan.title}</h3>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-1 text-xs sm:text-sm text-muted-foreground">
                      {plan.genre && <span>{plan.genre}</span>}
                      <span>{t("launchPlans.launch")}: {formatDate(plan.launch_date)}</span>
                    </div>
                  </div>
                  <span
                    className={`text-[10px] sm:text-xs px-2 py-1 rounded-full font-medium whitespace-nowrap ${
                      statusColors[plan.status] || ""
                    }`}
                  >
                    {plan.status}
                  </span>
                </div>
              </Link>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onDelete({
                    id: plan.id,
                    name: plan.title,
                    type: "launch-plan",
                  });
                }}
                className="flex-shrink-0 p-1.5 sm:p-2 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                aria-label={`Delete ${plan.title}`}
              >
                <Trash2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EmailTab({
  sequences,
  isLoading,
  onDelete,
}: {
  sequences: Array<{
    id: string;
    name: string;
    status: string;
    recipient_count: number;
    sent_count: number;
    created_at: string;
  }>;
  isLoading: boolean;
  onDelete: (target: DeleteTarget) => void;
}) {
  const router = useRouter();

  const statusColors: Record<string, string> = {
    draft: "bg-muted text-foreground",
    active: "bg-green-100 text-green-700",
    paused: "bg-yellow-100 text-yellow-700",
    completed: "bg-blue-100 text-blue-700",
    archived: "bg-red-100 text-red-700",
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3 sm:space-y-4">
      <div className="flex justify-end">
        <Link
          href="/marketing/email"
          className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-xs sm:text-sm text-center"
        >
          + Create Sequence
        </Link>
      </div>

      {sequences.length === 0 ? (
        <div className="border rounded-lg">
          <EmptyState
            icon={Mail}
            title={t("emailSequences.empty.title")}
            description={t("emailSequences.empty.description")}
            actionLabel={t("emailSequences.empty.action")}
            onAction={() => router.push("/marketing/email")}
          />
        </div>
      ) : (
        <div className="space-y-3">
          {sequences.map((seq) => (
            <div
              key={seq.id}
              className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow flex items-center gap-3"
            >
              <Link
                href={`/marketing/email?id=${seq.id}`}
                className="flex-1 min-w-0"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{seq.name}</h3>
                    <div className="text-sm text-muted-foreground mt-1">
                      {seq.sent_count} / {seq.recipient_count} {t("emailSequences.sent")}
                    </div>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${
                      statusColors[seq.status] || ""
                    }`}
                  >
                    {seq.status}
                  </span>
                </div>
              </Link>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onDelete({
                    id: seq.id,
                    name: seq.name,
                    type: "email-sequence",
                  });
                }}
                className="flex-shrink-0 p-2 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                aria-label={`Delete ${seq.name}`}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
