"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  useCampaign,
  useCampaignPerformance,
  useUpdateCampaign,
  useOptimizeCampaign,
} from "@/modules/advertising/hooks";
import type { Campaign, OptimizationSuggestion } from "@/modules/advertising/hooks";
import { PerformanceChart } from "@/modules/advertising/components/PerformanceChart";
import { BidManager } from "@/modules/advertising/components/BidManager";
import { CreativeEditor } from "@/modules/advertising/components/CreativeEditor";
import { toast } from "sonner";
import { useTranslations } from "@/hooks/use-translations";

export default function CampaignDetailPage() {
  const t = useTranslations("advertising");
  const params = useParams();
  const campaignId = params.id as string;
  const [activeTab, setActiveTab] = useState<"performance" | "keywords" | "creatives" | "optimize">(
    "performance"
  );
  const [optimization, setOptimization] = useState<OptimizationSuggestion | null>(null);

  const { data: campaign, isLoading } = useCampaign(campaignId);
  const { data: performance } = useCampaignPerformance(campaignId);
  const updateCampaign = useUpdateCampaign(campaignId);
  const optimizeCampaign = useOptimizeCampaign(campaignId);

  const handleStatusChange = async (newStatus: Campaign["status"]) => {
    try {
      await updateCampaign.mutateAsync({ status: newStatus });
      toast.success(t("campaignDetail.statusUpdated"));
    } catch (error) {
      const message = error instanceof Error ? error.message : t("campaignDetail.statusUpdateError");
      toast.error(message);
    }
  };

  const handleOptimize = async () => {
    try {
      const result = await optimizeCampaign.mutateAsync({
        target_acos: campaign?.target_acos || 30,
        min_data_points: 1,
      });
      setOptimization(result);
      toast.success(t("campaignDetail.optimizationComplete"));
    } catch {
      toast.error(t("campaignDetail.optimizationError"));
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="h-64 bg-muted rounded-lg animate-pulse" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="space-y-4">
        <Link href="/advertising/campaigns" className="text-primary hover:underline text-sm">
          {t("campaignDetail.backToCampaigns")}
        </Link>
        <div className="border border-red-200 bg-red-50 rounded-lg p-4 text-red-700">
          {t("campaignDetail.notFound")}
        </div>
      </div>
    );
  }

  const statusActions: Record<string, { label: string; status: Campaign["status"] }[]> = {
    draft: [{ label: t("campaignDetail.activate"), status: "active" }],
    active: [
      { label: t("campaignDetail.pause"), status: "paused" },
      { label: t("campaignDetail.end"), status: "ended" },
    ],
    paused: [
      { label: t("campaignDetail.resume"), status: "active" },
      { label: t("campaignDetail.archive"), status: "archived" },
    ],
    ended: [{ label: t("campaignDetail.archive"), status: "archived" }],
  };

  const tabs = [
    { key: "performance" as const, label: t("campaignDetail.performance") },
    { key: "keywords" as const, label: t("campaignDetail.keywords") },
    { key: "creatives" as const, label: t("campaignDetail.creatives") },
    { key: "optimize" as const, label: t("campaignDetail.aiOptimize") },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/advertising" className="hover:text-foreground">
          {t("campaignDetail.advertising")}
        </Link>
        <span>/</span>
        <Link href="/advertising/campaigns" className="hover:text-foreground">
          {t("campaignDetail.campaigns")}
        </Link>
        <span>/</span>
        <span className="text-foreground">{campaign.name}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{campaign.name}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
            <span className="capitalize">
              {campaign.platform === "amazon" ? t("campaignDetail.amazonAds") : t("campaignDetail.facebookAds")}
            </span>
            <span>{campaign.campaign_type.replace(/_/g, " ")}</span>
            <StatusBadge status={campaign.status} t={t} />
          </div>
        </div>
        <div className="flex gap-2">
          {(statusActions[campaign.status] || []).map((action) => (
            <button
              key={action.status}
              onClick={() => handleStatusChange(action.status)}
              disabled={updateCampaign.isPending}
              className="px-3 py-1.5 border rounded-lg text-sm hover:bg-muted disabled:opacity-50"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      {campaign.performance_summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <SummaryCard label={t("campaignDetail.spend")} value={`$${campaign.performance_summary.total_spend.toFixed(2)}`} />
          <SummaryCard label={t("campaignDetail.sales")} value={`$${campaign.performance_summary.total_sales.toFixed(2)}`} />
          <SummaryCard
            label={t("campaignDetail.acos")}
            value={`${campaign.performance_summary.avg_acos.toFixed(1)}%`}
            target={campaign.target_acos}
            t={t}
          />
          <SummaryCard label={t("campaignDetail.roas")} value={`${campaign.performance_summary.avg_roas.toFixed(2)}x`} />
          <SummaryCard label={t("campaignDetail.impressions")} value={campaign.performance_summary.total_impressions.toLocaleString()} />
          <SummaryCard label={t("campaignDetail.clicks")} value={campaign.performance_summary.total_clicks.toLocaleString()} />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "performance" && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold">{t("campaignDetail.performanceOverTime")}</h3>
          <PerformanceChart
            data={performance || []}
            metrics={["spend", "sales", "acos"]}
          />
          <PerformanceChart
            data={performance || []}
            metrics={["impressions", "clicks"]}
          />
        </div>
      )}

      {activeTab === "keywords" && (
        <BidManager campaignId={campaignId} />
      )}

      {activeTab === "creatives" && (
        <CreativeEditor
          campaignId={campaignId}
          bookId={campaign.book_id || undefined}
        />
      )}

      {activeTab === "optimize" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">{t("campaignDetail.aiOptimization")}</h3>
              <p className="text-sm text-muted-foreground">
                {t("campaignDetail.aiOptimizationDesc")}
              </p>
            </div>
            <button
              onClick={handleOptimize}
              disabled={optimizeCampaign.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90 disabled:opacity-50"
            >
              {optimizeCampaign.isPending ? t("campaignDetail.analyzing") : t("campaignDetail.runOptimization")}
            </button>
          </div>

          {optimization && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="border rounded-lg p-4 bg-muted/10">
                <h4 className="font-medium mb-2">{t("campaignDetail.analysisSummary")}</h4>
                <p className="text-sm">{optimization.summary}</p>
                <div className="flex gap-4 mt-3 text-sm">
                  <span>
                    {t("campaignDetail.currentAcos", { value: optimization.current_acos.toFixed(1) })}
                  </span>
                  <span>
                    {t("campaignDetail.targetAcos", { value: optimization.target_acos.toFixed(1) })}
                  </span>
                  {optimization.budget_recommendation && (
                    <span>
                      {t("campaignDetail.recommendedBudget", { value: optimization.budget_recommendation.toFixed(2) })}
                    </span>
                  )}
                </div>
              </div>

              {/* Bid Adjustments */}
              {optimization.bid_adjustments.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="px-4 py-3 bg-muted/50 font-medium text-sm">
                    {t("campaignDetail.suggestedBids", { count: optimization.bid_adjustments.length.toString() })}
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-t bg-muted/30">
                        <th className="text-left px-4 py-2">{t("campaignDetail.keyword")}</th>
                        <th className="text-right px-4 py-2">{t("campaignDetail.currentBid")}</th>
                        <th className="text-right px-4 py-2">{t("campaignDetail.suggestedBid")}</th>
                        <th className="text-left px-4 py-2">{t("campaignDetail.reason")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {optimization.bid_adjustments.map((adj, i) => (
                        <tr key={i} className="border-t">
                          <td className="px-4 py-2 font-medium">{adj.keyword}</td>
                          <td className="px-4 py-2 text-right">${adj.current_bid.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right">
                            <span
                              className={
                                adj.suggested_bid < adj.current_bid
                                  ? "text-red-600"
                                  : "text-green-600"
                              }
                            >
                              ${adj.suggested_bid.toFixed(2)}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-muted-foreground text-xs">
                            {adj.reason}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Keywords to Negate */}
              {optimization.keywords_to_negate.length > 0 && (
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">
                    {t("campaignDetail.keywordsToNegate", { count: optimization.keywords_to_negate.length.toString() })}
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {optimization.keywords_to_negate.map((kw, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {optimization.bid_adjustments.length === 0 &&
                optimization.keywords_to_negate.length === 0 && (
                  <div className="border rounded-lg p-6 text-center text-muted-foreground">
                    {t("campaignDetail.noChanges")}
                  </div>
                )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status, t }: { status: string; t: (key: string) => string }) {
  const styles: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    paused: "bg-yellow-100 text-yellow-800",
    draft: "bg-gray-100 text-gray-800",
    ended: "bg-red-100 text-red-800",
    archived: "bg-slate-100 text-slate-800",
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.draft}`}>
      {t(`campaigns.${status}`)}
    </span>
  );
}

function SummaryCard({
  label,
  value,
  target,
  t,
}: {
  label: string;
  value: string;
  target?: number | null;
  t?: (key: string, params?: Record<string, string>) => string;
}) {
  const isOverTarget = target && parseFloat(value) > target;
  return (
    <div className="border rounded-lg p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`text-lg font-bold ${isOverTarget ? "text-red-600" : ""}`}>
        {value}
      </p>
      {target && t && (
        <p className="text-xs text-muted-foreground">{t("campaignDetail.target", { target: target.toString() })}</p>
      )}
    </div>
  );
}
