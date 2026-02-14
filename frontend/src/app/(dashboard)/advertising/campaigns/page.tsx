"use client";

import { useState } from "react";
import Link from "next/link";
import { useCampaigns } from "@/modules/advertising/hooks";
import { CampaignCard } from "@/modules/advertising/components/CampaignCard";
import { CampaignWizard } from "@/modules/advertising/components/CampaignWizard";
import { AD_PLATFORMS } from "@/lib/constants";
import { useTranslations } from "@/hooks/use-translations";

export default function CampaignsListPage() {
  const t = useTranslations("advertising");
  const [platformFilter, setPlatformFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [wizardOpen, setWizardOpen] = useState(false);

  const { data, isLoading, error } = useCampaigns({
    platform: platformFilter || undefined,
    status: statusFilter || undefined,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("campaigns.title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("campaigns.subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/advertising"
            className="px-4 py-2 border rounded-lg text-sm hover:bg-muted"
            aria-label={t("campaigns.backToDashboard")}
          >
            {t("campaigns.dashboard")}
          </Link>
          <button
            aria-label={t("campaigns.createNew")}
            onClick={() => setWizardOpen(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90"
          >
            {t("campaigns.createCampaign")}
          </button>
        </div>
      </div>

      {/* Campaign Creation Wizard */}
      <CampaignWizard open={wizardOpen} onOpenChange={setWizardOpen} />

      {/* Filters */}
      <div className="flex gap-3">
        <select
          className="border rounded-lg px-3 py-2 text-sm"
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          aria-label={t("campaigns.filterPlatform")}
        >
          <option value="">{t("campaigns.allPlatforms")}</option>
          {Object.entries(AD_PLATFORMS).map(([key, meta]) => (
            <option key={key} value={key}>
              {meta.displayName}
            </option>
          ))}
        </select>
        <select
          className="border rounded-lg px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label={t("campaigns.filterStatus")}
        >
          <option value="">{t("campaigns.allStatuses")}</option>
          <option value="draft">{t("campaigns.draft")}</option>
          <option value="active">{t("campaigns.active")}</option>
          <option value="paused">{t("campaigns.paused")}</option>
          <option value="ended">{t("campaigns.ended")}</option>
          <option value="archived">{t("campaigns.archived")}</option>
        </select>
        {data?.total_count !== undefined && (
          <span className="text-sm text-muted-foreground self-center">
            {t("campaigns.campaignCount", { count: data.total_count.toString() })}
          </span>
        )}
      </div>

      {/* Campaign List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="border border-red-200 bg-red-50 rounded-lg p-4 text-red-700">
          {t("campaigns.loadError")}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="space-y-3">
          {data.items.map((campaign) => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}
          {data.has_more && (
            <p className="text-center text-sm text-muted-foreground py-4">
              More campaigns available. Scroll down or adjust filters.
            </p>
          )}
        </div>
      ) : (
        <div className="border rounded-lg p-8 text-center text-muted-foreground">
          <p>{t("campaigns.noCampaignsFound")}</p>
          <button
            onClick={() => setWizardOpen(true)}
            className="text-primary hover:underline mt-2"
            aria-label={t("campaigns.createFirstLabel")}
          >
            {t("campaigns.createFirstPrompt")}
          </button>
        </div>
      )}
    </div>
  );
}
