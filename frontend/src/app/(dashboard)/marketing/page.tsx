"use client";

import { useState, useCallback } from "react";
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

type Tab = "overview" | "launch-plans" | "email" | "social" | "arc";

interface DeleteTarget {
  id: string;
  name: string;
  type: "launch-plan" | "email-sequence" | "arc-campaign";
}

const tabs: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "launch-plans", label: "Launch Plans" },
  { id: "email", label: "Email Sequences" },
  { id: "social", label: "Social Media" },
  { id: "arc", label: "ARC Campaigns" },
];

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
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const queryClient = useQueryClient();

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
    <div className="space-y-6">
      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={handleDeleteDialogChange}
        title={`Delete ${deleteConfig?.label || "item"}?`}
        description={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.name}"? This action cannot be undone.`
            : ""
        }
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDeleteConfirm}
        loading={isDeleting}
      />

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold">Marketing & Launch Command</h1>
        <p className="text-gray-500 mt-1">
          Manage launch plans, email campaigns, social media, and ARC distribution.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
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

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
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
  const { items: recentActivity, isLoading: activityLoading } = useRecentActivity();

  const stats = [
    { label: "Launch Plans", value: plansCount, color: "bg-blue-500" },
    { label: "Email Sequences", value: sequencesCount, color: "bg-green-500" },
    { label: "Social Posts", value: socialPostsCount, color: "bg-purple-500" },
    { label: "ARC Campaigns", value: arcCount, color: "bg-orange-500" },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg border p-6">
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${stat.color}`} />
              <span className="text-sm text-gray-500">{stat.label}</span>
            </div>
            <div className="text-3xl font-bold mt-2">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-6">
          <h3 className="font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-2">
            <Link
              href="/marketing/launch/new"
              className="block p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-sm"
            >
              Generate a new launch plan with AI
            </Link>
            <Link
              href="/marketing/email"
              className="block p-3 rounded-lg bg-green-50 hover:bg-green-100 text-green-700 text-sm"
            >
              Create an email sequence
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h3 className="font-semibold mb-4">Recent Activity</h3>
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
              title="No recent activity"
              description="Activity will appear here as you create campaigns, send emails, and publish posts."
              actionLabel="Create a launch plan"
              onAction={() => setActiveTab("launch-plans")}
            />
          ) : (
            <div className="space-y-3">
              {recentActivity.map((item) => (
                <div key={item.id} className="flex items-start gap-3">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium ${ACTIVITY_ICONS[item.type]}`}
                  >
                    {item.type === "launch_plan" && "LP"}
                    {item.type === "email_sequence" && "ES"}
                    {item.type === "arc_campaign" && "AC"}
                    {item.type === "social_post" && "SP"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.action}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{item.title}</p>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0">
                    {formatRelativeDate(item.timestamp)}
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
    draft: "bg-gray-100 text-gray-700",
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
    <div className="space-y-4">
      <div className="flex justify-end">
        <Link
          href="/marketing/launch/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          + Generate Launch Plan
        </Link>
      </div>

      {plans.length === 0 ? (
        <div className="border rounded-lg">
          <EmptyState
            icon={Rocket}
            title="No launch plans yet"
            description="Generate your first AI-powered launch plan to coordinate your book launch."
            actionLabel="Generate Launch Plan"
            onAction={() => router.push("/marketing/launch/new")}
          />
        </div>
      ) : (
        <div className="space-y-3">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow flex items-center gap-3"
            >
              <Link
                href={`/marketing/launch/${plan.id}`}
                className="flex-1 min-w-0"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{plan.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                      {plan.genre && <span>{plan.genre}</span>}
                      <span>Launch: {formatDate(plan.launch_date)}</span>
                    </div>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${
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
                className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                aria-label={`Delete ${plan.title}`}
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
    draft: "bg-gray-100 text-gray-700",
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
    <div className="space-y-4">
      <div className="flex justify-end">
        <Link
          href="/marketing/email"
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
        >
          + Create Sequence
        </Link>
      </div>

      {sequences.length === 0 ? (
        <div className="border rounded-lg">
          <EmptyState
            icon={Mail}
            title="No email sequences yet"
            description="Create your first email sequence to engage your readers and build your audience."
            actionLabel="Create Sequence"
            onAction={() => router.push("/marketing/email")}
          />
        </div>
      ) : (
        <div className="space-y-3">
          {sequences.map((seq) => (
            <div
              key={seq.id}
              className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow flex items-center gap-3"
            >
              <Link
                href={`/marketing/email?id=${seq.id}`}
                className="flex-1 min-w-0"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{seq.name}</h3>
                    <div className="text-sm text-gray-500 mt-1">
                      {seq.sent_count} / {seq.recipient_count} sent
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
                className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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
