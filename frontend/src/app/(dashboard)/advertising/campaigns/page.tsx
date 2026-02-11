"use client";

import { useState } from "react";
import Link from "next/link";
import { useCampaigns, useCreateCampaign } from "@/modules/advertising/hooks";
import { CampaignCard } from "@/modules/advertising/components/CampaignCard";
import { toast } from "sonner";
import { AD_PLATFORMS, DEFAULT_AD_PLATFORM } from "@/lib/constants";
import { useTranslations } from "@/hooks/use-translations";

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

function getCampaignNameError(value: string, touched: boolean, t: (key: string) => string): string | undefined {
  if (!touched) return undefined;
  const trimmed = value.trim();
  if (!trimmed) return t("campaigns.nameRequired");
  if (trimmed.length < 2) return t("campaigns.nameMinLength");
  if (trimmed.length > 100) return t("campaigns.nameMaxLength");
  return undefined;
}

function getDailyBudgetError(value: number, touched: boolean, t: (key: string) => string): string | undefined {
  if (!touched) return undefined;
  if (value <= 0) return t("campaigns.budgetRequired");
  if (value > 50000) return t("campaigns.budgetMax");
  return undefined;
}

function getTargetAcosError(value: number, touched: boolean, t: (key: string) => string): string | undefined {
  if (!touched) return undefined;
  if (value < 0) return t("campaigns.acosNegative");
  if (value > 100) return t("campaigns.acosMax");
  return undefined;
}

export default function CampaignsListPage() {
  const t = useTranslations("advertising");
  const [platformFilter, setPlatformFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data, isLoading, error } = useCampaigns({
    platform: platformFilter || undefined,
    status: statusFilter || undefined,
  });

  const createCampaign = useCreateCampaign();

  const [newCampaign, setNewCampaign] = useState({
    name: "",
    platform: DEFAULT_AD_PLATFORM as string,
    campaign_type: "sponsored_products",
    daily_budget: 25,
    bid_strategy: "manual",
    target_acos: 30,
    targeting_keywords: "",
  });

  // -- Touched state for inline validation --
  const [touchedName, setTouchedName] = useState(false);
  const [touchedBudget, setTouchedBudget] = useState(false);
  const [touchedAcos, setTouchedAcos] = useState(false);

  const nameError = getCampaignNameError(newCampaign.name, touchedName, t);
  const budgetError = getDailyBudgetError(newCampaign.daily_budget, touchedBudget, t);
  const acosError = getTargetAcosError(newCampaign.target_acos, touchedAcos, t);

  // Form is valid when there are no errors (checked ignoring touched state)
  const isFormValid =
    !getCampaignNameError(newCampaign.name, true, t) &&
    !getDailyBudgetError(newCampaign.daily_budget, true, t) &&
    !getTargetAcosError(newCampaign.target_acos, true, t);

  const handleCreate = async () => {
    // Mark all fields as touched to reveal any remaining errors
    setTouchedName(true);
    setTouchedBudget(true);
    setTouchedAcos(true);

    if (!isFormValid) return;

    try {
      await createCampaign.mutateAsync({
        ...newCampaign,
        targeting_keywords: newCampaign.targeting_keywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
      });
      toast.success(t("campaigns.successCreated"));
      setShowCreateForm(false);
      setNewCampaign({
        name: "",
        platform: DEFAULT_AD_PLATFORM,
        campaign_type: "sponsored_products",
        daily_budget: 25,
        bid_strategy: "manual",
        target_acos: 30,
        targeting_keywords: "",
      });
      setTouchedName(false);
      setTouchedBudget(false);
      setTouchedAcos(false);
    } catch {
      toast.error(t("campaigns.errorCreated"));
    }
  };

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
            aria-label={showCreateForm ? t("campaigns.cancelCreating") : t("campaigns.createNew")}
            onClick={() => {
              if (showCreateForm) {
                // Closing -- reset form and touched state
                setNewCampaign({
                  name: "",
                  platform: DEFAULT_AD_PLATFORM,
                  campaign_type: "sponsored_products",
                  daily_budget: 25,
                  bid_strategy: "manual",
                  target_acos: 30,
                  targeting_keywords: "",
                });
                setTouchedName(false);
                setTouchedBudget(false);
                setTouchedAcos(false);
              }
              setShowCreateForm(!showCreateForm);
            }}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90"
          >
            {showCreateForm ? t("campaigns.cancel") : t("campaigns.createCampaign")}
          </button>
        </div>
      </div>

      {/* Create Campaign Form */}
      {showCreateForm && (
        <div className="border rounded-lg p-5 bg-muted/10 space-y-4">
          <h3 className="font-semibold">{t("campaigns.newCampaign")}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t("campaigns.name")} *</label>
              <input
                type="text"
                className={`w-full border rounded-lg px-3 py-2 text-sm ${
                  nameError ? "border-red-500 focus:ring-red-500" : ""
                }`}
                value={newCampaign.name}
                onChange={(e) =>
                  setNewCampaign((prev) => ({ ...prev, name: e.target.value }))
                }
                onBlur={() => setTouchedName(true)}
                placeholder={t("campaigns.namePlaceholder")}
                aria-label={t("campaigns.name")}
              />
              {nameError && (
                <p className="mt-1 text-sm text-red-600">{nameError}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t("campaigns.platform")}</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.platform}
                onChange={(e) =>
                  setNewCampaign((prev) => ({ ...prev, platform: e.target.value }))
                }
                aria-label={t("campaigns.selectPlatform")}
              >
                {Object.entries(AD_PLATFORMS).map(([key, meta]) => (
                  <option key={key} value={key}>
                    {meta.displayName}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t("campaigns.campaignType")}</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.campaign_type}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    campaign_type: e.target.value,
                  }))
                }
                aria-label={t("campaigns.selectType")}
              >
                <option value="sponsored_products">{t("campaigns.sponsoredProducts")}</option>
                <option value="sponsored_brands">{t("campaigns.sponsoredBrands")}</option>
                <option value="sponsored_display">{t("campaigns.sponsoredDisplay")}</option>
                <option value="lockscreen">{t("campaigns.lockscreen")}</option>
                <option value="facebook_feed">{t("campaigns.facebookFeed")}</option>
                <option value="facebook_stories">{t("campaigns.facebookStories")}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t("campaigns.dailyBudget")} *</label>
              <input
                type="number"
                min="1"
                step="1"
                className={`w-full border rounded-lg px-3 py-2 text-sm ${
                  budgetError ? "border-red-500 focus:ring-red-500" : ""
                }`}
                value={newCampaign.daily_budget}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    daily_budget: parseFloat(e.target.value) || 0,
                  }))
                }
                onBlur={() => setTouchedBudget(true)}
                aria-label={t("campaigns.budgetLabel")}
              />
              {budgetError && (
                <p className="mt-1 text-sm text-red-600">{budgetError}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t("campaigns.bidStrategy")}</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.bid_strategy}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    bid_strategy: e.target.value,
                  }))
                }
                aria-label={t("campaigns.selectStrategy")}
              >
                <option value="manual">{t("campaigns.manual")}</option>
                <option value="auto_low">{t("campaigns.autoLow")}</option>
                <option value="auto_high">{t("campaigns.autoHigh")}</option>
                <option value="rule_based">{t("campaigns.ruleBased")}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t("campaigns.targetAcos")}</label>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                className={`w-full border rounded-lg px-3 py-2 text-sm ${
                  acosError ? "border-red-500 focus:ring-red-500" : ""
                }`}
                value={newCampaign.target_acos}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    target_acos: parseFloat(e.target.value) || 0,
                  }))
                }
                onBlur={() => setTouchedAcos(true)}
                aria-label={t("campaigns.acosLabel")}
              />
              {acosError && (
                <p className="mt-1 text-sm text-red-600">{acosError}</p>
              )}
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium mb-1">
                {t("campaigns.targetingKeywords")}
              </label>
              <input
                type="text"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.targeting_keywords}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    targeting_keywords: e.target.value,
                  }))
                }
                placeholder={t("campaigns.keywordsPlaceholder")}
                aria-label={t("campaigns.keywordsLabel")}
              />
            </div>
          </div>
          <button
            onClick={handleCreate}
            disabled={createCampaign.isPending || !isFormValid}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={t("campaigns.submit")}
          >
            {createCampaign.isPending ? t("campaigns.creating") : t("campaigns.create")}
          </button>
        </div>
      )}

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
            onClick={() => setShowCreateForm(true)}
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
