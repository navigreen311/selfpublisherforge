
"use client";

import { useState } from "react";
import Link from "next/link";
import { useAdDashboard, useEnhancedDashboard } from "@/modules/advertising/hooks";
import { CampaignCard } from "@/modules/advertising/components/CampaignCard";
import { PerformanceTrendChart } from "@/modules/advertising/components/PerformanceTrendChart";
import { TopCampaignsTable } from "@/modules/advertising/components/TopCampaignsTable";
import { AIInsightsPanel } from "@/modules/advertising/components/AIInsightsPanel";
import { Skeleton } from "@/components/ui/skeleton";
import { AD_PLATFORMS } from "@/lib/constants";
import { useTranslations } from "@/hooks/use-translations";

export default function AdvertisingDashboardPage() {
  const t = useTranslations("advertising");
  const { data: dashboard, isLoading, error } = useAdDashboard();
  const [period, setPeriod] = useState("30d");
  const {
    data: enhanced,
    isLoading: enhancedLoading,
  } = useEnhancedDashboard(period);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-64 lg:col-span-2" />
          <Skeleton className="h-64" />
        </div>
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
          {t("viewAllCampaigns")}
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

      {/* Performance Trend Chart */}
      {enhancedLoading ? (
        <Skeleton className="h-96" />
      ) : enhanced?.trend_data ? (
        <PerformanceTrendChart
          data={enhanced.trend_data}
          period={period}
          onPeriodChange={setPeriod}
        />
      ) : null}

      {/* Top Campaigns Table & AI Insights - side by side on large screens */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {enhancedLoading ? (
            <Skeleton className="h-64" />
          ) : enhanced?.top_campaigns ? (
            <TopCampaignsTable campaigns={enhanced.top_campaigns} />
          ) : null}
        </div>
        <div>
          {enhancedLoading ? (
            <Skeleton className="h-64" />
          ) : (
            <AIInsightsPanel insights={enhanced?.insights ?? []} />
          )}
        </div>
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

      {/* Top Campaigns (original list) */}
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
              {t("createFirstCampaign")}
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
