"use client";

import { useState } from "react";
import { useLaunchPlans, useEmailSequences, useSocialCalendar, useARCCampaigns } from "@/modules/marketing/hooks";
import { ARCTable } from "@/modules/marketing/components/ARCTable";
import { SocialCalendar } from "@/modules/marketing/components/SocialCalendar";
import Link from "next/link";

type Tab = "overview" | "launch-plans" | "email" | "social" | "arc";

const tabs: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "launch-plans", label: "Launch Plans" },
  { id: "email", label: "Email Sequences" },
  { id: "social", label: "Social Media" },
  { id: "arc", label: "ARC Campaigns" },
];

export default function MarketingDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const { data: launchPlans, isLoading: plansLoading } = useLaunchPlans();
  const { data: emailSequences, isLoading: seqLoading } = useEmailSequences();
  const { data: socialCalendar, isLoading: socialLoading } = useSocialCalendar();
  const { data: arcCampaigns, isLoading: arcLoading } = useARCCampaigns();

  return (
    <div className="space-y-6">
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
        />
      )}

      {activeTab === "launch-plans" && (
        <LaunchPlansTab
          plans={launchPlans?.items || []}
          isLoading={plansLoading}
        />
      )}

      {activeTab === "email" && (
        <EmailTab
          sequences={emailSequences?.items || []}
          isLoading={seqLoading}
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

function OverviewTab({
  plansCount,
  sequencesCount,
  socialPostsCount,
  arcCount,
}: {
  plansCount: number;
  sequencesCount: number;
  socialPostsCount: number;
  arcCount: number;
}) {
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
          <p className="text-sm text-gray-400">No recent activity to show.</p>
        </div>
      </div>
    </div>
  );
}

function LaunchPlansTab({
  plans,
  isLoading,
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
}) {
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
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-200 rounded-lg" />
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
        <div className="text-center py-12 text-gray-400 border rounded-lg">
          <p className="text-lg">No launch plans yet.</p>
          <p className="text-sm mt-1">Generate your first AI-powered launch plan.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {plans.map((plan) => (
            <Link
              key={plan.id}
              href={`/marketing/launch/${plan.id}`}
              className="block bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
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
          ))}
        </div>
      )}
    </div>
  );
}

function EmailTab({
  sequences,
  isLoading,
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
}) {
  const statusColors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    active: "bg-green-100 text-green-700",
    paused: "bg-yellow-100 text-yellow-700",
    completed: "bg-blue-100 text-blue-700",
    archived: "bg-red-100 text-red-700",
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="h-16 bg-gray-200 rounded-lg" />
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
        <div className="text-center py-12 text-gray-400 border rounded-lg">
          <p className="text-lg">No email sequences yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sequences.map((seq) => (
            <Link
              key={seq.id}
              href={`/marketing/email?id=${seq.id}`}
              className="block bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
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
          ))}
        </div>
      )}
    </div>
  );
}
