"use client";

import Link from "next/link";
import type { Campaign } from "../hooks";

interface CampaignCardProps {
  campaign: Campaign;
}

const STATUS_STYLES: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
  draft: "bg-gray-100 text-gray-800",
  ended: "bg-red-100 text-red-800",
  archived: "bg-slate-100 text-slate-800",
};

const PLATFORM_LABELS: Record<string, string> = {
  amazon: "Amazon Ads",
  facebook: "Facebook Ads",
};

export function CampaignCard({ campaign }: CampaignCardProps) {
  const perf = campaign.performance_summary;

  return (
    <Link href={`/advertising/campaigns/${campaign.id}`}>
      <div className="border rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-semibold text-lg">{campaign.name}</h3>
            <p className="text-sm text-muted-foreground">
              {PLATFORM_LABELS[campaign.platform] || campaign.platform}
              {" - "}
              {campaign.campaign_type.replace(/_/g, " ")}
            </p>
          </div>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
              STATUS_STYLES[campaign.status] || STATUS_STYLES.draft
            }`}
          >
            {campaign.status}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
          <MetricBlock
            label="Daily Budget"
            value={`$${campaign.daily_budget.toFixed(2)}`}
          />
          <MetricBlock
            label="Spend"
            value={perf ? `$${perf.total_spend.toFixed(2)}` : "-"}
          />
          <MetricBlock
            label="Sales"
            value={perf ? `$${perf.total_sales.toFixed(2)}` : "-"}
          />
          <MetricBlock
            label="ACOS"
            value={perf ? `${perf.avg_acos.toFixed(1)}%` : "-"}
            highlight={
              perf && campaign.target_acos
                ? perf.avg_acos > campaign.target_acos
                  ? "danger"
                  : "success"
                : undefined
            }
          />
        </div>

        {perf && (
          <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
            <span>{perf.total_impressions.toLocaleString()} impressions</span>
            <span>{perf.total_clicks.toLocaleString()} clicks</span>
            <span>CTR: {perf.avg_ctr.toFixed(2)}%</span>
            <span>ROAS: {perf.avg_roas.toFixed(2)}x</span>
          </div>
        )}
      </div>
    </Link>
  );
}

function MetricBlock({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "success" | "danger";
}) {
  const highlightClass =
    highlight === "success"
      ? "text-green-600"
      : highlight === "danger"
      ? "text-red-600"
      : "";

  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`text-sm font-semibold ${highlightClass}`}>{value}</p>
    </div>
  );
}
