"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  useCampaign,
  useCampaignPerformance,
  useUpdateCampaign,
  usePauseCampaign,
  useResumeCampaign,
} from "@/modules/advertising/hooks";
import type { Campaign } from "@/modules/advertising/types";
import { PerformanceChart } from "@/modules/advertising/components/PerformanceChart";
import { KeywordsTab } from "@/modules/advertising/components/KeywordsTab";
import { SearchTermsTab } from "@/modules/advertising/components/SearchTermsTab";
import { NegativeKeywordsTab } from "@/modules/advertising/components/NegativeKeywordsTab";
import { BidOptimizerDialog } from "@/modules/advertising/components/BidOptimizerDialog";
import { toast } from "sonner";
import { useTranslations } from "@/hooks/use-translations";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DollarSign,
  ShoppingCart,
  TrendingUp,
  Package,
  Pause,
  Play,
  Pencil,
} from "lucide-react";

export default function CampaignDetailPage() {
  const t = useTranslations("advertising");
  const params = useParams();
  const campaignId = params.id as string;
  const [bidOptimizerOpen, setBidOptimizerOpen] = useState(false);

  const { data: campaign, isLoading } = useCampaign(campaignId);
  const { data: performance } = useCampaignPerformance(campaignId);
  const updateCampaign = useUpdateCampaign(campaignId);
  const pauseCampaign = usePauseCampaign();
  const resumeCampaign = useResumeCampaign();

  const handlePause = async () => {
    try {
      await pauseCampaign.mutateAsync(campaignId);
    } catch {
      // Error handled by hook
    }
  };

  const handleResume = async () => {
    try {
      await resumeCampaign.mutateAsync(campaignId);
    } catch {
      // Error handled by hook
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="h-20 bg-muted rounded-lg animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
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

  const summary = campaign.performance_summary;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
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

      {/* Campaign Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{campaign.name}</h1>
            <StatusBadge status={campaign.status} />
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span className="capitalize">
              {campaign.platform === "amazon"
                ? t("campaignDetail.amazonAds")
                : t("campaignDetail.facebookAds")}
            </span>
            <span className="text-muted-foreground/50">|</span>
            <span className="capitalize">
              {campaign.campaign_type.replace(/_/g, " ")}
            </span>
            <span className="text-muted-foreground/50">|</span>
            <span>${campaign.daily_budget.toFixed(2)}/day budget</span>
          </div>
        </div>
        <div className="flex gap-2">
          {campaign.status === "active" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handlePause}
              disabled={pauseCampaign.isPending}
            >
              <Pause className="h-4 w-4 mr-1" />
              Pause
            </Button>
          )}
          {campaign.status === "paused" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleResume}
              disabled={resumeCampaign.isPending}
            >
              <Play className="h-4 w-4 mr-1" />
              Resume
            </Button>
          )}
          <Button variant="outline" size="sm" asChild>
            <Link href={`/advertising/campaigns/${campaignId}/edit`}>
              <Pencil className="h-4 w-4 mr-1" />
              Edit
            </Link>
          </Button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Spend"
          value={summary ? `$${summary.total_spend.toFixed(2)}` : "$0.00"}
          icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
          subtitle="This month"
        />
        <StatCard
          label="Sales"
          value={summary ? `$${summary.total_sales.toFixed(2)}` : "$0.00"}
          icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
          subtitle="This month"
        />
        <StatCard
          label="ACOS"
          value={summary ? `${summary.avg_acos.toFixed(1)}%` : "0.0%"}
          icon={<ShoppingCart className="h-4 w-4 text-muted-foreground" />}
          subtitle={
            campaign.target_acos
              ? `Target: ${campaign.target_acos}%`
              : "This month"
          }
          valueClassName={
            summary && campaign.target_acos && summary.avg_acos > campaign.target_acos
              ? "text-red-600"
              : summary && summary.avg_acos < 25
              ? "text-green-600"
              : ""
          }
        />
        <StatCard
          label="Orders"
          value={summary ? summary.total_orders.toLocaleString() : "0"}
          icon={<Package className="h-4 w-4 text-muted-foreground" />}
          subtitle="This month"
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="keywords">Keywords</TabsTrigger>
          <TabsTrigger value="search-terms">Search Terms</TabsTrigger>
          <TabsTrigger value="negative-keywords">Negative Keywords</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {t("campaignDetail.performanceOverTime")}
            </h3>
            <PerformanceChart
              data={performance || []}
              metrics={["spend", "sales", "acos"]}
            />
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4">Traffic Metrics</h3>
            <PerformanceChart
              data={performance || []}
              metrics={["impressions", "clicks"]}
            />
          </div>
        </TabsContent>

        <TabsContent value="keywords">
          <KeywordsTab
            campaignId={campaignId}
            onOpenBidOptimizer={() => setBidOptimizerOpen(true)}
          />
        </TabsContent>

        <TabsContent value="search-terms">
          <SearchTermsTab campaignId={campaignId} />
        </TabsContent>

        <TabsContent value="negative-keywords">
          <NegativeKeywordsTab
            campaignId={campaignId}
            negativeKeywords={campaign.negative_keywords || []}
          />
        </TabsContent>
      </Tabs>

      {/* Bid Optimizer Dialog */}
      <BidOptimizerDialog
        open={bidOptimizerOpen}
        onOpenChange={setBidOptimizerOpen}
        campaignId={campaignId}
      />
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: Campaign["status"] }) {
  const config: Record<
    string,
    { label: string; className: string }
  > = {
    active: {
      label: "Active",
      className: "bg-green-100 text-green-800 border-green-200",
    },
    paused: {
      label: "Paused",
      className: "bg-yellow-100 text-yellow-800 border-yellow-200",
    },
    draft: {
      label: "Draft",
      className: "bg-gray-100 text-gray-800 border-gray-200",
    },
    ended: {
      label: "Ended",
      className: "bg-red-100 text-red-800 border-red-200",
    },
    archived: {
      label: "Archived",
      className: "bg-slate-100 text-slate-800 border-slate-200",
    },
  };

  const c = config[status] || config.draft;

  return (
    <Badge variant="outline" className={c.className}>
      {c.label}
    </Badge>
  );
}

function StatCard({
  label,
  value,
  icon,
  subtitle,
  valueClassName,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  subtitle?: string;
  valueClassName?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">{label}</span>
          {icon}
        </div>
        <p className={`text-2xl font-bold ${valueClassName || ""}`}>{value}</p>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}
