import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Advertising",
  description: "Manage advertising campaigns across Amazon Ads, Facebook Ads, and BookBub to promote your books.",
  noindex: true,
});

"use client";

import Link from "next/link";
import { useAdDashboard } from "@/modules/advertising/hooks";
import { CampaignCard } from "@/modules/advertising/components/CampaignCard";
import { Skeleton } from "@/components/ui/skeleton";
import { AD_PLATFORMS } from "@/lib/constants";
import { useTranslations } from "@/hooks/use-translations";

export default function AdvertisingDashboardPage() {
  const t = useTranslations("advertising");
  const { data: dashboard, isLoading, error } = useAdDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <div className="border border-red-200 bg-red-50 rounded-lg p-4 text-red-700">
          {t("failedToLoad")}
        </div>
      </div>
    );
  }

  if (!dashboard) return null;
  const d = dashboard;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <Link
          href="/advertising/campaigns"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90"
          aria-label={t("viewAllCampaignsLabel")}
        >
          View All Campaigns
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label={t("activeCampaigns")}
          value={d.total_active_campaigns.toString()}
        />
        <KPICard
          label={t("todaySpend")}
          value={`$${d.total_spend_today.toFixed(2)}`}
        />
        <KPICard
          label={t("monthlySpend")}
          value={`$${d.total_spend_month.toFixed(2)}`}
          subtext={t("sales", { value: d.total_sales_month.toFixed(2) })}
        />
        <KPICard
          label={t("overallAcos")}
          value={`${d.overall_acos.toFixed(1)}%`}
          subtext={t("roas", { value: d.overall_roas.toFixed(2) })}
          highlight={d.overall_acos > 40 ? "danger" : d.overall_acos > 0 ? "success" : undefined}
        />
      </div>

      {/* Platform Breakdown */}
      {Object.keys(d.platform_breakdown).length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">{t("platformPerformance")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(d.platform_breakdown).map(([platform, perf]) => (
              <div key={platform} className="border rounded-lg p-4">
                <h3 className="font-medium capitalize mb-3">
                  {AD_PLATFORMS[platform]?.displayName ?? platform}
                </h3>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">{t("spend")}</p>
                    <p className="font-semibold">${perf.total_spend.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("salesLabel")}</p>
                    <p className="font-semibold">${perf.total_sales.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("acos")}</p>
                    <p className="font-semibold">{perf.avg_acos.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("impressions")}</p>
                    <p className="font-semibold">
                      {perf.total_impressions.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("clicks")}</p>
                    <p className="font-semibold">
                      {perf.total_clicks.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("roasLabel")}</p>
                    <p className="font-semibold">{perf.avg_roas.toFixed(2)}x</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Campaigns */}
      <div>
        <h2 className="text-lg font-semibold mb-3">{t("topCampaigns")}</h2>
        {d.top_campaigns.length > 0 ? (
          <div className="space-y-3">
            {d.top_campaigns.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </div>
        ) : (
          <div className="border rounded-lg p-8 text-center text-muted-foreground">
            <p>{t("noCampaigns")}</p>
            <Link
              href="/advertising/campaigns"
              className="text-primary hover:underline mt-2 inline-block"
              aria-label={t("createFirstCampaignLabel")}
            >
              Create your first campaign
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function KPICard({
  label,
  value,
  subtext,
  highlight,
}: {
  label: string;
  value: string;
  subtext?: string;
  highlight?: "success" | "danger";
}) {
  const valueClass =
    highlight === "success"
      ? "text-green-600"
      : highlight === "danger"
      ? "text-red-600"
      : "";

  return (
    <div className="border rounded-lg p-5">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${valueClass}`}>{value}</p>
      {subtext && (
        <p className="text-xs text-muted-foreground mt-1">{subtext}</p>
      )}
    </div>
  );
}
