"use client";

import { useState } from "react";
import Link from "next/link";
import { useCampaigns, useCreateCampaign } from "@/modules/advertising/hooks";
import { CampaignCard } from "@/modules/advertising/components/CampaignCard";
import { toast } from "sonner";
import { AD_PLATFORMS, DEFAULT_AD_PLATFORM } from "@/lib/constants";

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

function getCampaignNameError(value: string, touched: boolean): string | undefined {
  if (!touched) return undefined;
  const trimmed = value.trim();
  if (!trimmed) return "Campaign name is required.";
  if (trimmed.length < 2) return "Campaign name must be at least 2 characters.";
  if (trimmed.length > 100) return "Campaign name must be 100 characters or fewer.";
  return undefined;
}

function getDailyBudgetError(value: number, touched: boolean): string | undefined {
  if (!touched) return undefined;
  if (value <= 0) return "Daily budget must be a positive number.";
  if (value > 50000) return "Daily budget cannot exceed $50,000.";
  return undefined;
}

function getTargetAcosError(value: number, touched: boolean): string | undefined {
  if (!touched) return undefined;
  if (value < 0) return "Target ACOS cannot be negative.";
  if (value > 100) return "Target ACOS cannot exceed 100%.";
  return undefined;
}

export default function CampaignsListPage() {
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

  const nameError = getCampaignNameError(newCampaign.name, touchedName);
  const budgetError = getDailyBudgetError(newCampaign.daily_budget, touchedBudget);
  const acosError = getTargetAcosError(newCampaign.target_acos, touchedAcos);

  // Form is valid when there are no errors (checked ignoring touched state)
  const isFormValid =
    !getCampaignNameError(newCampaign.name, true) &&
    !getDailyBudgetError(newCampaign.daily_budget, true) &&
    !getTargetAcosError(newCampaign.target_acos, true);

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
      toast.success("Campaign created successfully");
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
      toast.error("Failed to create campaign");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your advertising campaigns across platforms
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/advertising"
            className="px-4 py-2 border rounded-lg text-sm hover:bg-muted"
            aria-label="Back to advertising dashboard"
          >
            Dashboard
          </Link>
          <button
            aria-label={showCreateForm ? "Cancel creating campaign" : "Create a new campaign"}
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
            {showCreateForm ? "Cancel" : "Create Campaign"}
          </button>
        </div>
      </div>

      {/* Create Campaign Form */}
      {showCreateForm && (
        <div className="border rounded-lg p-5 bg-muted/10 space-y-4">
          <h3 className="font-semibold">New Campaign</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
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
                placeholder="Campaign name"
                aria-label="Campaign name"
              />
              {nameError && (
                <p className="mt-1 text-sm text-red-600">{nameError}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Platform</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.platform}
                onChange={(e) =>
                  setNewCampaign((prev) => ({ ...prev, platform: e.target.value }))
                }
                aria-label="Select advertising platform"
              >
                {Object.entries(AD_PLATFORMS).map(([key, meta]) => (
                  <option key={key} value={key}>
                    {meta.displayName}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Campaign Type</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.campaign_type}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    campaign_type: e.target.value,
                  }))
                }
                aria-label="Select campaign type"
              >
                <option value="sponsored_products">Sponsored Products</option>
                <option value="sponsored_brands">Sponsored Brands</option>
                <option value="sponsored_display">Sponsored Display</option>
                <option value="lockscreen">Lockscreen</option>
                <option value="facebook_feed">Facebook Feed</option>
                <option value="facebook_stories">Facebook Stories</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Daily Budget ($) *</label>
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
                aria-label="Daily budget in dollars"
              />
              {budgetError && (
                <p className="mt-1 text-sm text-red-600">{budgetError}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Bid Strategy</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={newCampaign.bid_strategy}
                onChange={(e) =>
                  setNewCampaign((prev) => ({
                    ...prev,
                    bid_strategy: e.target.value,
                  }))
                }
                aria-label="Select bid strategy"
              >
                <option value="manual">Manual</option>
                <option value="auto_low">Auto (Low)</option>
                <option value="auto_high">Auto (High)</option>
                <option value="rule_based">Rule-based</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Target ACOS (%)</label>
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
                aria-label="Target ACOS percentage"
              />
              {acosError && (
                <p className="mt-1 text-sm text-red-600">{acosError}</p>
              )}
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium mb-1">
                Targeting Keywords (comma-separated)
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
                placeholder="fantasy books, epic fantasy, dragon books"
                aria-label="Targeting keywords, comma-separated"
              />
            </div>
          </div>
          <button
            onClick={handleCreate}
            disabled={createCampaign.isPending || !isFormValid}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Submit new campaign"
          >
            {createCampaign.isPending ? "Creating..." : "Create Campaign"}
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <select
          className="border rounded-lg px-3 py-2 text-sm"
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          aria-label="Filter by advertising platform"
        >
          <option value="">All Platforms</option>
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
          aria-label="Filter by campaign status"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="ended">Ended</option>
          <option value="archived">Archived</option>
        </select>
        {data?.total_count !== undefined && (
          <span className="text-sm text-muted-foreground self-center">
            {data.total_count} campaign(s)
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
          Failed to load campaigns. Please try again.
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
          <p>No campaigns found matching your filters.</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="text-primary hover:underline mt-2"
            aria-label="Create your first advertising campaign"
          >
            Create your first campaign
          </button>
        </div>
      )}
    </div>
  );
}
