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

export default function CampaignDetailPage() {
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
      toast.success("Campaign status updated");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update campaign status";
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
      toast.success("Optimization analysis complete");
    } catch {
      toast.error("Failed to run optimization");
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
          Back to Campaigns
        </Link>
        <div className="border border-red-200 bg-red-50 rounded-lg p-4 text-red-700">
          Campaign not found.
        </div>
      </div>
    );
  }

  const statusActions: Record<string, { label: string; status: Campaign["status"] }[]> = {
    draft: [{ label: "Activate", status: "active" }],
    active: [
      { label: "Pause", status: "paused" },
      { label: "End", status: "ended" },
    ],
    paused: [
      { label: "Resume", status: "active" },
      { label: "Archive", status: "archived" },
    ],
    ended: [{ label: "Archive", status: "archived" }],
  };

  const tabs = [
    { key: "performance" as const, label: "Performance" },
    { key: "keywords" as const, label: "Keywords" },
    { key: "creatives" as const, label: "Creatives" },
    { key: "optimize" as const, label: "AI Optimize" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/advertising" className="hover:text-foreground">
          Advertising
        </Link>
        <span>/</span>
        <Link href="/advertising/campaigns" className="hover:text-foreground">
          Campaigns
        </Link>
        <span>/</span>
        <span className="text-foreground">{campaign.name}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{campaign.name}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
            <span className="capitalize">
              {campaign.platform === "amazon" ? "Amazon Ads" : "Facebook Ads"}
            </span>
            <span>{campaign.campaign_type.replace(/_/g, " ")}</span>
            <StatusBadge status={campaign.status} />
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
          <SummaryCard label="Spend" value={`$${campaign.performance_summary.total_spend.toFixed(2)}`} />
          <SummaryCard label="Sales" value={`$${campaign.performance_summary.total_sales.toFixed(2)}`} />
          <SummaryCard
            label="ACOS"
            value={`${campaign.performance_summary.avg_acos.toFixed(1)}%`}
            target={campaign.target_acos}
          />
          <SummaryCard label="ROAS" value={`${campaign.performance_summary.avg_roas.toFixed(2)}x`} />
          <SummaryCard label="Impressions" value={campaign.performance_summary.total_impressions.toLocaleString()} />
          <SummaryCard label="Clicks" value={campaign.performance_summary.total_clicks.toLocaleString()} />
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
          <h3 className="text-lg font-semibold">Performance Over Time</h3>
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
              <h3 className="text-lg font-semibold">AI Optimization</h3>
              <p className="text-sm text-muted-foreground">
                Analyze campaign performance and get AI-powered bid recommendations.
              </p>
            </div>
            <button
              onClick={handleOptimize}
              disabled={optimizeCampaign.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90 disabled:opacity-50"
            >
              {optimizeCampaign.isPending ? "Analyzing..." : "Run Optimization"}
            </button>
          </div>

          {optimization && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="border rounded-lg p-4 bg-muted/10">
                <h4 className="font-medium mb-2">Analysis Summary</h4>
                <p className="text-sm">{optimization.summary}</p>
                <div className="flex gap-4 mt-3 text-sm">
                  <span>
                    Current ACOS: <strong>{optimization.current_acos.toFixed(1)}%</strong>
                  </span>
                  <span>
                    Target ACOS: <strong>{optimization.target_acos.toFixed(1)}%</strong>
                  </span>
                  {optimization.budget_recommendation && (
                    <span>
                      Recommended Budget:{" "}
                      <strong>${optimization.budget_recommendation.toFixed(2)}/day</strong>
                    </span>
                  )}
                </div>
              </div>

              {/* Bid Adjustments */}
              {optimization.bid_adjustments.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="px-4 py-3 bg-muted/50 font-medium text-sm">
                    Suggested Bid Adjustments ({optimization.bid_adjustments.length})
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-t bg-muted/30">
                        <th className="text-left px-4 py-2">Keyword</th>
                        <th className="text-right px-4 py-2">Current Bid</th>
                        <th className="text-right px-4 py-2">Suggested Bid</th>
                        <th className="text-left px-4 py-2">Reason</th>
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
                    Keywords to Negate ({optimization.keywords_to_negate.length})
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
                    No optimization changes recommended at this time. Your campaign is
                    performing within target parameters.
                  </div>
                )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    paused: "bg-yellow-100 text-yellow-800",
    draft: "bg-gray-100 text-gray-800",
    ended: "bg-red-100 text-red-800",
    archived: "bg-slate-100 text-slate-800",
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.draft}`}>
      {status}
    </span>
  );
}

function SummaryCard({
  label,
  value,
  target,
}: {
  label: string;
  value: string;
  target?: number | null;
}) {
  const isOverTarget = target && parseFloat(value) > target;
  return (
    <div className="border rounded-lg p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`text-lg font-bold ${isOverTarget ? "text-red-600" : ""}`}>
        {value}
      </p>
      {target && (
        <p className="text-xs text-muted-foreground">Target: {target}%</p>
      )}
    </div>
  );
}
