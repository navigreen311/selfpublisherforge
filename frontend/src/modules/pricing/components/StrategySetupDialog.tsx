"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useProjects } from "@/modules/projects/hooks";
import { useCreateStrategy } from "../hooks";
import type { StrategyCreatePayload } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StrategySetupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  strategyType:
    | "competitive_match"
    | "value_based"
    | "penetration"
    | "dynamic"
    | "promotional";
}

interface DynamicRule {
  id: string;
  condition: "bsr_below" | "daily_sales_above";
  threshold: string;
  adjustPct: string;
}

interface PromoWindow {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  promoPrice: string;
  autoRevert: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STRATEGY_META: Record<
  StrategySetupDialogProps["strategyType"],
  { title: string; description: string }
> = {
  competitive_match: {
    title: "Competitive Match",
    description:
      "Price based on competitor analysis to stay competitive in your market.",
  },
  value_based: {
    title: "Value-Based",
    description:
      "Price based on perceived value and quality of your content.",
  },
  penetration: {
    title: "Penetration",
    description:
      "Lower prices to gain market share and build readership quickly.",
  },
  dynamic: {
    title: "Dynamic",
    description:
      "Automatically adjust prices based on demand, competition, and sales data.",
  },
  promotional: {
    title: "Promotional",
    description:
      "Temporary price reductions for launches, holidays, or marketing campaigns.",
  },
};

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function StrategySetupDialog({
  open,
  onOpenChange,
  strategyType,
}: StrategySetupDialogProps) {
  const { data: projects } = useProjects();
  const createStrategy = useCreateStrategy();

  // ---- Common state ----
  const [selectedBookIds, setSelectedBookIds] = useState<string[]>([]);
  const [minPrice, setMinPrice] = useState("2.99");
  const [maxPrice, setMaxPrice] = useState("9.99");
  const [autoApply, setAutoApply] = useState(false);

  // ---- Competitive Match state ----
  const [competitivePosition, setCompetitivePosition] = useState<
    "match_lowest" | "below_average" | "at_average" | "premium"
  >("at_average");
  const [belowAverageAmount, setBelowAverageAmount] = useState("0.50");
  const [premiumAmount, setPremiumAmount] = useState("1.00");
  const [checkFrequency, setCheckFrequency] = useState("weekly");
  const [competitorAsins, setCompetitorAsins] = useState<string[]>([""]);
  const [autoDetectCompetitors, setAutoDetectCompetitors] = useState(false);

  // ---- Value-Based state ----
  const [premiumMultiplier, setPremiumMultiplier] = useState([15]);
  const [reviewThreshold, setReviewThreshold] = useState("25");
  const [ratingThreshold, setRatingThreshold] = useState("4.0");
  const [basePriceOn, setBasePriceOn] = useState<
    "category_average" | "median" | "top_10_average"
  >("category_average");

  // ---- Penetration state ----
  const [startingPrice, setStartingPrice] = useState("0.99");
  const [targetPrice, setTargetPrice] = useState("4.99");
  const [rampMode, setRampMode] = useState<"manual" | "automatic">("manual");
  const [weekPrices, setWeekPrices] = useState({
    week1: "0.99",
    week2: "1.99",
    week4: "4.99",
  });
  const [reviewMilestones, setReviewMilestones] = useState({
    milestone1: "10",
    milestone2: "25",
    milestone3: "50",
  });
  const [targetBsr, setTargetBsr] = useState("50000");

  // ---- Dynamic state ----
  const [dynamicRules, setDynamicRules] = useState<DynamicRule[]>([
    { id: generateId(), condition: "bsr_below", threshold: "10000", adjustPct: "5" },
    { id: generateId(), condition: "daily_sales_above", threshold: "20", adjustPct: "3" },
  ]);
  const [sensitivity, setSensitivity] = useState([50]);
  const [dynamicCheckFrequency, setDynamicCheckFrequency] = useState("daily");

  // ---- Promotional state ----
  const [promoWindows, setPromoWindows] = useState<PromoWindow[]>([
    {
      id: generateId(),
      name: "",
      startDate: "",
      endDate: "",
      promoPrice: "",
      autoRevert: true,
    },
  ]);

  // ---- Reset on close or strategy change ----
  const resetForm = useCallback(() => {
    setSelectedBookIds([]);
    setMinPrice("2.99");
    setMaxPrice("9.99");
    setAutoApply(false);
    setCompetitivePosition("at_average");
    setBelowAverageAmount("0.50");
    setPremiumAmount("1.00");
    setCheckFrequency("weekly");
    setCompetitorAsins([""]);
    setAutoDetectCompetitors(false);
    setPremiumMultiplier([15]);
    setReviewThreshold("25");
    setRatingThreshold("4.0");
    setBasePriceOn("category_average");
    setStartingPrice("0.99");
    setTargetPrice("4.99");
    setRampMode("manual");
    setWeekPrices({ week1: "0.99", week2: "1.99", week4: "4.99" });
    setReviewMilestones({ milestone1: "10", milestone2: "25", milestone3: "50" });
    setTargetBsr("50000");
    setDynamicRules([
      { id: generateId(), condition: "bsr_below", threshold: "10000", adjustPct: "5" },
      { id: generateId(), condition: "daily_sales_above", threshold: "20", adjustPct: "3" },
    ]);
    setSensitivity([50]);
    setDynamicCheckFrequency("daily");
    setPromoWindows([
      {
        id: generateId(),
        name: "",
        startDate: "",
        endDate: "",
        promoPrice: "",
        autoRevert: true,
      },
    ]);
  }, []);

  useEffect(() => {
    resetForm();
  }, [strategyType, resetForm]);

  useEffect(() => {
    if (!open) resetForm();
  }, [open, resetForm]);

  // ---- Validation ----
  const showRoyaltyWarning =
    parseFloat(minPrice) < 2.99 || parseFloat(maxPrice) > 9.99;

  function validate(): string | null {
    if (selectedBookIds.length === 0) return "Select at least one book.";
    if (!minPrice || isNaN(Number(minPrice)) || Number(minPrice) < 0)
      return "Min price must be a valid positive number.";
    if (!maxPrice || isNaN(Number(maxPrice)) || Number(maxPrice) < 0)
      return "Max price must be a valid positive number.";
    if (Number(minPrice) >= Number(maxPrice))
      return "Min price must be less than max price.";
    return null;
  }

  // ---- Submit ----
  function handleSubmit() {
    const error = validate();
    if (error) {
      // Could use toast here, but simple alert for now
      alert(error);
      return;
    }

    const config: Record<string, unknown> = {
      min_price: parseFloat(minPrice),
      max_price: parseFloat(maxPrice),
      auto_apply: autoApply,
    };

    switch (strategyType) {
      case "competitive_match":
        config.competitive_position = competitivePosition;
        if (competitivePosition === "below_average")
          config.below_average_amount = parseFloat(belowAverageAmount);
        if (competitivePosition === "premium")
          config.premium_amount = parseFloat(premiumAmount);
        config.check_frequency = checkFrequency;
        config.auto_detect_competitors = autoDetectCompetitors;
        if (!autoDetectCompetitors)
          config.competitor_asins = competitorAsins.filter((a) => a.trim());
        break;

      case "value_based":
        config.premium_multiplier = premiumMultiplier[0] / 100;
        config.review_threshold = parseInt(reviewThreshold, 10);
        config.rating_threshold = parseFloat(ratingThreshold);
        config.base_price_on = basePriceOn;
        break;

      case "penetration":
        config.starting_price = parseFloat(startingPrice);
        config.target_price = parseFloat(targetPrice);
        config.ramp_mode = rampMode;
        if (rampMode === "manual") {
          config.ramp_schedule = {
            week_1: parseFloat(weekPrices.week1),
            week_2: parseFloat(weekPrices.week2),
            week_4: parseFloat(weekPrices.week4),
          };
        } else {
          config.review_milestones = {
            milestone_1: parseInt(reviewMilestones.milestone1, 10),
            milestone_2: parseInt(reviewMilestones.milestone2, 10),
            milestone_3: parseInt(reviewMilestones.milestone3, 10),
          };
        }
        config.target_bsr = parseInt(targetBsr, 10);
        break;

      case "dynamic":
        config.rules = dynamicRules.map((r) => ({
          condition: r.condition,
          threshold: parseFloat(r.threshold),
          adjust_pct: parseFloat(r.adjustPct),
        }));
        config.sensitivity = sensitivity[0];
        config.check_frequency = dynamicCheckFrequency;
        break;

      case "promotional":
        config.promo_windows = promoWindows
          .filter((w) => w.name && w.startDate && w.endDate && w.promoPrice)
          .map((w) => ({
            name: w.name,
            start_date: w.startDate,
            end_date: w.endDate,
            promo_price: parseFloat(w.promoPrice),
            auto_revert: w.autoRevert,
          }));
        break;
    }

    const payload: StrategyCreatePayload = {
      type: strategyType,
      name: STRATEGY_META[strategyType].title,
      book_ids: selectedBookIds,
      config,
      auto_apply: autoApply,
    };

    createStrategy.mutate(payload, {
      onSuccess: () => onOpenChange(false),
    });
  }

  // ---- Book toggle ----
  function toggleBook(bookId: string) {
    setSelectedBookIds((prev) =>
      prev.includes(bookId) ? prev.filter((id) => id !== bookId) : [...prev, bookId]
    );
  }

  // ---- Dynamic rule helpers ----
  function addDynamicRule() {
    setDynamicRules((prev) => [
      ...prev,
      { id: generateId(), condition: "bsr_below", threshold: "", adjustPct: "" },
    ]);
  }

  function removeDynamicRule(id: string) {
    setDynamicRules((prev) => prev.filter((r) => r.id !== id));
  }

  function updateDynamicRule(id: string, field: keyof DynamicRule, value: string) {
    setDynamicRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  }

  // ---- Promo window helpers ----
  function addPromoWindow() {
    setPromoWindows((prev) => [
      ...prev,
      {
        id: generateId(),
        name: "",
        startDate: "",
        endDate: "",
        promoPrice: "",
        autoRevert: true,
      },
    ]);
  }

  function removePromoWindow(id: string) {
    setPromoWindows((prev) => prev.filter((w) => w.id !== id));
  }

  function updatePromoWindow(id: string, field: keyof PromoWindow, value: string | boolean) {
    setPromoWindows((prev) =>
      prev.map((w) => (w.id === id ? { ...w, [field]: value } : w))
    );
  }

  function addPresetPromotion(preset: string) {
    const now = new Date();
    let name = "";
    let startDate = "";
    let endDate = "";
    let promoPrice = "0.99";

    switch (preset) {
      case "launch_week": {
        name = "Launch Week";
        startDate = now.toISOString().split("T")[0];
        const end = new Date(now);
        end.setDate(end.getDate() + 7);
        endDate = end.toISOString().split("T")[0];
        promoPrice = "0.99";
        break;
      }
      case "holiday_sale": {
        name = "Holiday Sale";
        startDate = `${now.getFullYear()}-12-20`;
        endDate = `${now.getFullYear()}-12-31`;
        promoPrice = "1.99";
        break;
      }
      case "bookbub_deal": {
        name = "BookBub Deal";
        startDate = now.toISOString().split("T")[0];
        const bbEnd = new Date(now);
        bbEnd.setDate(bbEnd.getDate() + 3);
        endDate = bbEnd.toISOString().split("T")[0];
        promoPrice = "0.99";
        break;
      }
      case "countdown_deal": {
        name = "Countdown Deal";
        startDate = now.toISOString().split("T")[0];
        const cdEnd = new Date(now);
        cdEnd.setDate(cdEnd.getDate() + 7);
        endDate = cdEnd.toISOString().split("T")[0];
        promoPrice = "0.99";
        break;
      }
    }

    setPromoWindows((prev) => [
      ...prev,
      { id: generateId(), name, startDate, endDate, promoPrice, autoRevert: true },
    ]);
  }

  // ---- Competitor ASIN helpers ----
  function addAsinField() {
    setCompetitorAsins((prev) => [...prev, ""]);
  }

  function updateAsin(index: number, value: string) {
    setCompetitorAsins((prev) => prev.map((a, i) => (i === index ? value : a)));
  }

  function removeAsin(index: number) {
    setCompetitorAsins((prev) => prev.filter((_, i) => i !== index));
  }

  // ---- Render helpers ----
  const meta = STRATEGY_META[strategyType];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl p-0">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle>{meta.title} Strategy</DialogTitle>
          <DialogDescription>{meta.description}</DialogDescription>
        </DialogHeader>

        <div className="max-h-[70vh] overflow-y-auto px-6 pb-2 space-y-6">
          {/* ---- Book Selector ---- */}
          <section>
            <Label className="text-sm font-semibold">Select Books</Label>
            <div className="mt-2 space-y-2 rounded-md border p-3 max-h-40 overflow-y-auto">
              {projects && projects.length > 0 ? (
                projects.map((project) => (
                  <label
                    key={project.id}
                    className="flex items-center gap-3 cursor-pointer hover:bg-muted/50 rounded p-1.5 -m-1"
                  >
                    <Checkbox
                      checked={selectedBookIds.includes(project.id)}
                      onCheckedChange={() => toggleBook(project.id)}
                    />
                    <span className="text-sm flex-1">{project.title}</span>
                    <Badge variant="outline" className="text-xs">
                      {project.status}
                    </Badge>
                  </label>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No books found.</p>
              )}
            </div>
          </section>

          <Separator />

          {/* ---- Price Boundaries ---- */}
          <section>
            <Label className="text-sm font-semibold">Price Boundaries</Label>
            <div className="mt-2 grid grid-cols-2 gap-4">
              <Input
                label="Min Price ($)"
                type="number"
                step="0.01"
                min="0"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
              />
              <Input
                label="Max Price ($)"
                type="number"
                step="0.01"
                min="0"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
              />
            </div>
            {showRoyaltyWarning && (
              <p className="mt-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md px-3 py-2">
                KDP 70% royalty requires $2.99-$9.99 price range
              </p>
            )}
          </section>

          <Separator />

          {/* ---- Strategy-Specific Config ---- */}
          {strategyType === "competitive_match" && (
            <CompetitiveMatchConfig
              competitivePosition={competitivePosition}
              setCompetitivePosition={setCompetitivePosition}
              belowAverageAmount={belowAverageAmount}
              setBelowAverageAmount={setBelowAverageAmount}
              premiumAmount={premiumAmount}
              setPremiumAmount={setPremiumAmount}
              checkFrequency={checkFrequency}
              setCheckFrequency={setCheckFrequency}
              competitorAsins={competitorAsins}
              autoDetectCompetitors={autoDetectCompetitors}
              setAutoDetectCompetitors={setAutoDetectCompetitors}
              addAsinField={addAsinField}
              updateAsin={updateAsin}
              removeAsin={removeAsin}
            />
          )}

          {strategyType === "value_based" && (
            <ValueBasedConfig
              premiumMultiplier={premiumMultiplier}
              setPremiumMultiplier={setPremiumMultiplier}
              reviewThreshold={reviewThreshold}
              setReviewThreshold={setReviewThreshold}
              ratingThreshold={ratingThreshold}
              setRatingThreshold={setRatingThreshold}
              basePriceOn={basePriceOn}
              setBasePriceOn={setBasePriceOn}
            />
          )}

          {strategyType === "penetration" && (
            <PenetrationConfig
              startingPrice={startingPrice}
              setStartingPrice={setStartingPrice}
              targetPrice={targetPrice}
              setTargetPrice={setTargetPrice}
              rampMode={rampMode}
              setRampMode={setRampMode}
              weekPrices={weekPrices}
              setWeekPrices={setWeekPrices}
              reviewMilestones={reviewMilestones}
              setReviewMilestones={setReviewMilestones}
              targetBsr={targetBsr}
              setTargetBsr={setTargetBsr}
            />
          )}

          {strategyType === "dynamic" && (
            <DynamicConfig
              rules={dynamicRules}
              addRule={addDynamicRule}
              removeRule={removeDynamicRule}
              updateRule={updateDynamicRule}
              sensitivity={sensitivity}
              setSensitivity={setSensitivity}
              checkFrequency={dynamicCheckFrequency}
              setCheckFrequency={setDynamicCheckFrequency}
            />
          )}

          {strategyType === "promotional" && (
            <PromotionalConfig
              windows={promoWindows}
              addWindow={addPromoWindow}
              removeWindow={removePromoWindow}
              updateWindow={updatePromoWindow}
              addPreset={addPresetPromotion}
            />
          )}

          <Separator />

          {/* ---- Auto-Apply Toggle ---- */}
          <section>
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-semibold">Auto-Apply</Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {autoApply
                    ? "Price changes will be applied automatically."
                    : "You will be notified for approval before changes are applied."}
                </p>
              </div>
              <Switch checked={autoApply} onCheckedChange={setAutoApply} />
            </div>
          </section>
        </div>

        <DialogFooter className="px-6 pb-6 pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={createStrategy.isPending}
          >
            {createStrategy.isPending ? "Saving..." : "Save Strategy"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ===========================================================================
// Strategy-specific sub-components
// ===========================================================================

// ---- Competitive Match ----

interface CompetitiveMatchConfigProps {
  competitivePosition: "match_lowest" | "below_average" | "at_average" | "premium";
  setCompetitivePosition: (v: "match_lowest" | "below_average" | "at_average" | "premium") => void;
  belowAverageAmount: string;
  setBelowAverageAmount: (v: string) => void;
  premiumAmount: string;
  setPremiumAmount: (v: string) => void;
  checkFrequency: string;
  setCheckFrequency: (v: string) => void;
  competitorAsins: string[];
  autoDetectCompetitors: boolean;
  setAutoDetectCompetitors: (v: boolean) => void;
  addAsinField: () => void;
  updateAsin: (index: number, value: string) => void;
  removeAsin: (index: number) => void;
}

function CompetitiveMatchConfig({
  competitivePosition,
  setCompetitivePosition,
  belowAverageAmount,
  setBelowAverageAmount,
  premiumAmount,
  setPremiumAmount,
  checkFrequency,
  setCheckFrequency,
  competitorAsins,
  autoDetectCompetitors,
  setAutoDetectCompetitors,
  addAsinField,
  updateAsin,
  removeAsin,
}: CompetitiveMatchConfigProps) {
  return (
    <section className="space-y-5">
      <div>
        <Label className="text-sm font-semibold">Competitive Position</Label>
        <div className="mt-2 space-y-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="competitive-position"
              className="h-4 w-4 text-primary accent-primary"
              checked={competitivePosition === "match_lowest"}
              onChange={() => setCompetitivePosition("match_lowest")}
            />
            <span className="text-sm">Match lowest competitor price</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="competitive-position"
              className="h-4 w-4 text-primary accent-primary"
              checked={competitivePosition === "below_average"}
              onChange={() => setCompetitivePosition("below_average")}
            />
            <span className="text-sm">Below average by</span>
            <Input
              type="number"
              step="0.01"
              min="0"
              className="w-24 h-8"
              value={belowAverageAmount}
              onChange={(e) => setBelowAverageAmount(e.target.value)}
              disabled={competitivePosition !== "below_average"}
              placeholder="$0.50"
            />
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="competitive-position"
              className="h-4 w-4 text-primary accent-primary"
              checked={competitivePosition === "at_average"}
              onChange={() => setCompetitivePosition("at_average")}
            />
            <span className="text-sm">At average competitor price</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="competitive-position"
              className="h-4 w-4 text-primary accent-primary"
              checked={competitivePosition === "premium"}
              onChange={() => setCompetitivePosition("premium")}
            />
            <span className="text-sm">Premium (above average by</span>
            <Input
              type="number"
              step="0.01"
              min="0"
              className="w-24 h-8"
              value={premiumAmount}
              onChange={(e) => setPremiumAmount(e.target.value)}
              disabled={competitivePosition !== "premium"}
              placeholder="$1.00"
            />
            <span className="text-sm">)</span>
          </label>
        </div>
      </div>

      <div>
        <Label className="text-sm font-semibold">Check Frequency</Label>
        <Select value={checkFrequency} onValueChange={setCheckFrequency}>
          <SelectTrigger className="mt-2 w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="daily">Daily</SelectItem>
            <SelectItem value="weekly">Weekly</SelectItem>
            <SelectItem value="biweekly">Bi-weekly</SelectItem>
            <SelectItem value="monthly">Monthly</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label className="text-sm font-semibold">Competitor ASINs</Label>

        <label className="flex items-center gap-2 mt-2 cursor-pointer">
          <Checkbox
            checked={autoDetectCompetitors}
            onCheckedChange={(checked) => setAutoDetectCompetitors(checked === true)}
          />
          <span className="text-sm">Auto-detect competitors</span>
        </label>

        {!autoDetectCompetitors && (
          <div className="mt-3 space-y-2">
            {competitorAsins.map((asin, index) => (
              <div key={index} className="flex items-center gap-2">
                <Input
                  className="flex-1 h-8"
                  placeholder="e.g. B0XXXXXXXXX"
                  value={asin}
                  onChange={(e) => updateAsin(index, e.target.value)}
                />
                {competitorAsins.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-muted-foreground"
                    onClick={() => removeAsin(index)}
                  >
                    Remove
                  </Button>
                )}
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addAsinField}
            >
              + Add ASIN
            </Button>
          </div>
        )}
      </div>
    </section>
  );
}

// ---- Value-Based ----

interface ValueBasedConfigProps {
  premiumMultiplier: number[];
  setPremiumMultiplier: (v: number[]) => void;
  reviewThreshold: string;
  setReviewThreshold: (v: string) => void;
  ratingThreshold: string;
  setRatingThreshold: (v: string) => void;
  basePriceOn: "category_average" | "median" | "top_10_average";
  setBasePriceOn: (v: "category_average" | "median" | "top_10_average") => void;
}

function ValueBasedConfig({
  premiumMultiplier,
  setPremiumMultiplier,
  reviewThreshold,
  setReviewThreshold,
  ratingThreshold,
  setRatingThreshold,
  basePriceOn,
  setBasePriceOn,
}: ValueBasedConfigProps) {
  return (
    <section className="space-y-5">
      <div>
        <Label className="text-sm font-semibold">
          Premium Multiplier: {premiumMultiplier[0]}% above category average
        </Label>
        <Slider
          className="mt-3"
          min={5}
          max={30}
          step={1}
          value={premiumMultiplier}
          onValueChange={setPremiumMultiplier}
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>5%</span>
          <span>30%</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Review Threshold (min reviews)"
          type="number"
          min="0"
          value={reviewThreshold}
          onChange={(e) => setReviewThreshold(e.target.value)}
        />
        <Input
          label="Rating Threshold (min stars)"
          type="number"
          step="0.1"
          min="1"
          max="5"
          value={ratingThreshold}
          onChange={(e) => setRatingThreshold(e.target.value)}
        />
      </div>

      <div>
        <Label className="text-sm font-semibold">Base Price On</Label>
        <div className="mt-2 space-y-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="base-price-on"
              className="h-4 w-4 accent-primary"
              checked={basePriceOn === "category_average"}
              onChange={() => setBasePriceOn("category_average")}
            />
            <span className="text-sm">Category average</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="base-price-on"
              className="h-4 w-4 accent-primary"
              checked={basePriceOn === "median"}
              onChange={() => setBasePriceOn("median")}
            />
            <span className="text-sm">Median</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="base-price-on"
              className="h-4 w-4 accent-primary"
              checked={basePriceOn === "top_10_average"}
              onChange={() => setBasePriceOn("top_10_average")}
            />
            <span className="text-sm">Top 10 average</span>
          </label>
        </div>
      </div>
    </section>
  );
}

// ---- Penetration ----

interface PenetrationConfigProps {
  startingPrice: string;
  setStartingPrice: (v: string) => void;
  targetPrice: string;
  setTargetPrice: (v: string) => void;
  rampMode: "manual" | "automatic";
  setRampMode: (v: "manual" | "automatic") => void;
  weekPrices: { week1: string; week2: string; week4: string };
  setWeekPrices: (v: { week1: string; week2: string; week4: string }) => void;
  reviewMilestones: { milestone1: string; milestone2: string; milestone3: string };
  setReviewMilestones: (v: { milestone1: string; milestone2: string; milestone3: string }) => void;
  targetBsr: string;
  setTargetBsr: (v: string) => void;
}

function PenetrationConfig({
  startingPrice,
  setStartingPrice,
  targetPrice,
  setTargetPrice,
  rampMode,
  setRampMode,
  weekPrices,
  setWeekPrices,
  reviewMilestones,
  setReviewMilestones,
  targetBsr,
  setTargetBsr,
}: PenetrationConfigProps) {
  return (
    <section className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Starting Price ($)"
          type="number"
          step="0.01"
          min="0"
          value={startingPrice}
          onChange={(e) => setStartingPrice(e.target.value)}
        />
        <Input
          label="Target Price (full price after ramp-up) ($)"
          type="number"
          step="0.01"
          min="0"
          value={targetPrice}
          onChange={(e) => setTargetPrice(e.target.value)}
        />
      </div>

      <div>
        <Label className="text-sm font-semibold">Ramp-Up Schedule</Label>
        <div className="mt-2 space-y-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="ramp-mode"
              className="h-4 w-4 accent-primary"
              checked={rampMode === "manual"}
              onChange={() => setRampMode("manual")}
            />
            <span className="text-sm">Manual weekly schedule</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="ramp-mode"
              className="h-4 w-4 accent-primary"
              checked={rampMode === "automatic"}
              onChange={() => setRampMode("automatic")}
            />
            <span className="text-sm">Automatic ramp based on review count</span>
          </label>
        </div>

        {rampMode === "manual" ? (
          <div className="mt-3 grid grid-cols-3 gap-3">
            <Input
              label="Week 1 ($)"
              type="number"
              step="0.01"
              min="0"
              value={weekPrices.week1}
              onChange={(e) => setWeekPrices({ ...weekPrices, week1: e.target.value })}
            />
            <Input
              label="Week 2 ($)"
              type="number"
              step="0.01"
              min="0"
              value={weekPrices.week2}
              onChange={(e) => setWeekPrices({ ...weekPrices, week2: e.target.value })}
            />
            <Input
              label="Week 4 ($)"
              type="number"
              step="0.01"
              min="0"
              value={weekPrices.week4}
              onChange={(e) => setWeekPrices({ ...weekPrices, week4: e.target.value })}
            />
          </div>
        ) : (
          <div className="mt-3 space-y-3">
            <p className="text-xs text-muted-foreground">
              Set review count milestones that trigger price increases.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <Input
                label="Milestone 1 (reviews)"
                type="number"
                min="0"
                value={reviewMilestones.milestone1}
                onChange={(e) =>
                  setReviewMilestones({ ...reviewMilestones, milestone1: e.target.value })
                }
              />
              <Input
                label="Milestone 2 (reviews)"
                type="number"
                min="0"
                value={reviewMilestones.milestone2}
                onChange={(e) =>
                  setReviewMilestones({ ...reviewMilestones, milestone2: e.target.value })
                }
              />
              <Input
                label="Milestone 3 (reviews)"
                type="number"
                min="0"
                value={reviewMilestones.milestone3}
                onChange={(e) =>
                  setReviewMilestones({ ...reviewMilestones, milestone3: e.target.value })
                }
              />
            </div>
          </div>
        )}
      </div>

      <Input
        label="Target BSR Rank"
        type="number"
        min="1"
        value={targetBsr}
        onChange={(e) => setTargetBsr(e.target.value)}
        helperText="The BSR rank you want to achieve during penetration."
      />
    </section>
  );
}

// ---- Dynamic ----

interface DynamicConfigProps {
  rules: DynamicRule[];
  addRule: () => void;
  removeRule: (id: string) => void;
  updateRule: (id: string, field: keyof DynamicRule, value: string) => void;
  sensitivity: number[];
  setSensitivity: (v: number[]) => void;
  checkFrequency: string;
  setCheckFrequency: (v: string) => void;
}

function DynamicConfig({
  rules,
  addRule,
  removeRule,
  updateRule,
  sensitivity,
  setSensitivity,
  checkFrequency,
  setCheckFrequency,
}: DynamicConfigProps) {
  const sensitivityLabel =
    sensitivity[0] <= 25
      ? "Low (conservative)"
      : sensitivity[0] <= 50
        ? "Moderate"
        : sensitivity[0] <= 75
          ? "High"
          : "High (aggressive)";

  return (
    <section className="space-y-5">
      <div>
        <Label className="text-sm font-semibold">Dynamic Rules</Label>
        <div className="mt-2 space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="flex items-center gap-2 rounded-md border p-3 text-sm"
            >
              <span className="shrink-0">If</span>
              <Select
                value={rule.condition}
                onValueChange={(v) =>
                  updateRule(rule.id, "condition", v)
                }
              >
                <SelectTrigger className="w-44 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bsr_below">BSR drops below</SelectItem>
                  <SelectItem value="daily_sales_above">Daily sales &gt;</SelectItem>
                </SelectContent>
              </Select>
              <Input
                type="number"
                min="0"
                className="w-24 h-8"
                placeholder="value"
                value={rule.threshold}
                onChange={(e) => updateRule(rule.id, "threshold", e.target.value)}
              />
              <span className="shrink-0">
                {rule.condition === "bsr_below" ? ", lower price by" : ", raise price by"}
              </span>
              <Input
                type="number"
                min="0"
                className="w-20 h-8"
                placeholder="%"
                value={rule.adjustPct}
                onChange={(e) => updateRule(rule.id, "adjustPct", e.target.value)}
              />
              <span className="shrink-0">%</span>
              {rules.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 px-2 text-muted-foreground ml-auto"
                  onClick={() => removeRule(rule.id)}
                >
                  Remove
                </Button>
              )}
            </div>
          ))}
          <Button type="button" variant="outline" size="sm" onClick={addRule}>
            + Add Rule
          </Button>
        </div>
      </div>

      <div>
        <Label className="text-sm font-semibold">
          Sensitivity: {sensitivityLabel}
        </Label>
        <Slider
          className="mt-3"
          min={0}
          max={100}
          step={5}
          value={sensitivity}
          onValueChange={setSensitivity}
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>Low (conservative)</span>
          <span>High (aggressive)</span>
        </div>
      </div>

      <div>
        <Label className="text-sm font-semibold">Check Frequency</Label>
        <Select value={checkFrequency} onValueChange={setCheckFrequency}>
          <SelectTrigger className="mt-2 w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="daily">Daily</SelectItem>
            <SelectItem value="weekly">Weekly</SelectItem>
            <SelectItem value="biweekly">Bi-weekly</SelectItem>
            <SelectItem value="monthly">Monthly</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </section>
  );
}

// ---- Promotional ----

interface PromotionalConfigProps {
  windows: PromoWindow[];
  addWindow: () => void;
  removeWindow: (id: string) => void;
  updateWindow: (id: string, field: keyof PromoWindow, value: string | boolean) => void;
  addPreset: (preset: string) => void;
}

function PromotionalConfig({
  windows,
  addWindow,
  removeWindow,
  updateWindow,
  addPreset,
}: PromotionalConfigProps) {
  return (
    <section className="space-y-5">
      <div>
        <Label className="text-sm font-semibold">Preset Promotions</Label>
        <div className="mt-2 flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addPreset("launch_week")}
          >
            Launch Week
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addPreset("holiday_sale")}
          >
            Holiday Sale
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addPreset("bookbub_deal")}
          >
            BookBub Deal
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addPreset("countdown_deal")}
          >
            Countdown Deal
          </Button>
        </div>
      </div>

      <div>
        <Label className="text-sm font-semibold">Promotional Windows</Label>
        <div className="mt-2 space-y-3">
          {windows.map((window) => (
            <div
              key={window.id}
              className="rounded-md border p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <Input
                  className="flex-1 h-8 max-w-xs"
                  placeholder="Promotion name"
                  value={window.name}
                  onChange={(e) => updateWindow(window.id, "name", e.target.value)}
                />
                {windows.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-muted-foreground"
                    onClick={() => removeWindow(window.id)}
                  >
                    Remove
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Start Date</Label>
                  <Input
                    type="date"
                    className="h-8"
                    value={window.startDate}
                    onChange={(e) => updateWindow(window.id, "startDate", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">End Date</Label>
                  <Input
                    type="date"
                    className="h-8"
                    value={window.endDate}
                    onChange={(e) => updateWindow(window.id, "endDate", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Promo Price ($)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    className="h-8"
                    value={window.promoPrice}
                    onChange={(e) => updateWindow(window.id, "promoPrice", e.target.value)}
                  />
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={window.autoRevert}
                  onCheckedChange={(checked) =>
                    updateWindow(window.id, "autoRevert", checked === true)
                  }
                />
                <span className="text-sm">Auto-revert to original price after end date</span>
              </label>
            </div>
          ))}
          <Button type="button" variant="outline" size="sm" onClick={addWindow}>
            + Add Window
          </Button>
        </div>
      </div>
    </section>
  );
}
