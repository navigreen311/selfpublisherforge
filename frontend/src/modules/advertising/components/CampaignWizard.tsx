"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ShoppingCart,
  BookMarked,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Check,
  Target,
  DollarSign,
  Calendar,
  Sparkles,
  Plus,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useProjects } from "@/modules/projects/hooks";
import { useCreateCampaign, useSuggestKeywords } from "../hooks";
import type { KeywordSuggestion } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CampaignWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type WizardStep = 1 | 2 | 3;

type Platform = "amazon" | "facebook" | "bookbub";

type AmazonAdType = "sponsored_products" | "sponsored_brands" | "lockscreen";

type TargetingType = "automatic" | "manual" | "asin";

type BiddingStrategy = "dynamic_down" | "dynamic_up_down" | "fixed";

type ScheduleType = "immediate" | "scheduled";

interface SelectedKeyword {
  keyword: string;
  matchType: "exact" | "phrase" | "broad";
  bid: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PLATFORMS: {
  value: Platform;
  label: string;
  icon: React.ElementType;
  description: string;
}[] = [
  {
    value: "amazon",
    label: "Amazon Ads",
    icon: ShoppingCart,
    description: "Reach readers on the world's largest bookstore",
  },
  {
    value: "facebook",
    label: "Facebook / Meta",
    icon: BookMarked,
    description: "Target readers based on interests and demographics",
  },
  {
    value: "bookbub",
    label: "BookBub Ads",
    icon: BookOpen,
    description: "Advertise to avid readers on BookBub",
  },
];

const AMAZON_AD_TYPES: {
  value: AmazonAdType;
  label: string;
  description: string;
}[] = [
  {
    value: "sponsored_products",
    label: "Sponsored Products",
    description:
      "Appear in search results and product pages. Best for driving direct sales.",
  },
  {
    value: "sponsored_brands",
    label: "Sponsored Brands",
    description:
      "Showcase your brand and catalog at the top of search results.",
  },
  {
    value: "lockscreen",
    label: "Lockscreen Ads",
    description:
      "Display ads on Kindle e-reader lockscreens. Great for discovery.",
  },
];

const TARGETING_TYPES: {
  value: TargetingType;
  label: string;
  description: string;
}[] = [
  {
    value: "automatic",
    label: "Automatic",
    description: "AI manages keywords and targets based on your book",
  },
  {
    value: "manual",
    label: "Manual",
    description: "Choose your own keywords and set individual bids",
  },
  {
    value: "asin",
    label: "ASIN Targeting",
    description: "Target specific competitor books by their ASINs",
  },
];

const AUTO_MATCH_TYPES = [
  { key: "close_match", label: "Close match", description: "Closely related search terms" },
  { key: "loose_match", label: "Loose match", description: "Loosely related search terms" },
  { key: "substitutes", label: "Substitutes", description: "Similar products shoppers view" },
  { key: "complements", label: "Complements", description: "Products often bought together" },
];

const BIDDING_STRATEGIES: {
  value: BiddingStrategy;
  label: string;
  description: string;
}[] = [
  {
    value: "dynamic_down",
    label: "Dynamic bids - down only",
    description:
      "Amazon lowers your bids when a click is less likely to convert",
  },
  {
    value: "dynamic_up_down",
    label: "Dynamic bids - up and down",
    description:
      "Amazon raises or lowers bids based on conversion likelihood",
  },
  {
    value: "fixed",
    label: "Fixed bids",
    description: "Amazon uses your exact bid for all opportunities",
  },
];

const STEPS: { step: WizardStep; label: string; icon: React.ElementType }[] = [
  { step: 1, label: "Platform & Type", icon: Target },
  { step: 2, label: "Book & Targeting", icon: BookOpen },
  { step: 3, label: "Budget & Schedule", icon: DollarSign },
];

// ---------------------------------------------------------------------------
// Step Indicator
// ---------------------------------------------------------------------------

function StepIndicator({ current }: { current: WizardStep }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map(({ step, label, icon: Icon }, idx) => {
        const isActive = step === current;
        const isComplete = step < current;
        return (
          <div key={step} className="flex items-center gap-2">
            {idx > 0 && (
              <div
                className={cn(
                  "h-px w-8",
                  isComplete ? "bg-primary" : "bg-border"
                )}
              />
            )}
            <div
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive && "bg-primary text-primary-foreground",
                isComplete && "bg-primary/10 text-primary",
                !isActive && !isComplete && "bg-muted text-muted-foreground"
              )}
            >
              {isComplete ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Icon className="h-3.5 w-3.5" />
              )}
              <span className="hidden sm:inline">{label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reusable Selection Card
// ---------------------------------------------------------------------------

function SelectionCard({
  selected,
  onClick,
  icon: Icon,
  label,
  description,
  disabled,
}: {
  selected: boolean;
  onClick: () => void;
  icon?: React.ElementType;
  label: string;
  description?: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "text-left border rounded-lg p-4 transition-all space-y-1 w-full",
        selected
          ? "ring-2 ring-primary border-primary shadow-sm"
          : "hover:shadow-md hover:border-primary/30",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-5 w-5 text-muted-foreground" />}
          <span className="font-semibold text-sm">{label}</span>
        </div>
        {selected && <Check className="h-4 w-4 text-primary shrink-0" />}
      </div>
      {description && (
        <p className="text-xs text-muted-foreground pl-7">{description}</p>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Step 1: Platform & Type
// ---------------------------------------------------------------------------

function StepPlatformType({
  platform,
  onPlatformChange,
  adType,
  onAdTypeChange,
}: {
  platform: Platform;
  onPlatformChange: (p: Platform) => void;
  adType: AmazonAdType;
  onAdTypeChange: (t: AmazonAdType) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Label className="text-sm font-semibold">Advertising Platform</Label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {PLATFORMS.map((p) => (
            <SelectionCard
              key={p.value}
              selected={platform === p.value}
              onClick={() => onPlatformChange(p.value)}
              icon={p.icon}
              label={p.label}
              description={p.description}
            />
          ))}
        </div>
      </div>

      {platform === "amazon" && (
        <div className="space-y-3">
          <Label className="text-sm font-semibold">Ad Type</Label>
          <div className="grid grid-cols-1 gap-3">
            {AMAZON_AD_TYPES.map((t) => (
              <SelectionCard
                key={t.value}
                selected={adType === t.value}
                onClick={() => onAdTypeChange(t.value)}
                label={t.label}
                description={t.description}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2: Book & Targeting
// ---------------------------------------------------------------------------

function StepBookTargeting({
  bookId,
  onBookIdChange,
  campaignName,
  onCampaignNameChange,
  targetingType,
  onTargetingTypeChange,
  autoMatchTypes,
  onAutoMatchTypesChange,
  selectedKeywords,
  onSelectedKeywordsChange,
  customKeyword,
  onCustomKeywordChange,
  customMatchType,
  onCustomMatchTypeChange,
  customBid,
  onCustomBidChange,
  onAddCustomKeyword,
  negativeKeywords,
  onNegativeKeywordsChange,
  suggestedKeywords,
  isSuggestingKeywords,
  onSuggestKeywords,
}: {
  bookId: string;
  onBookIdChange: (id: string) => void;
  campaignName: string;
  onCampaignNameChange: (name: string) => void;
  targetingType: TargetingType;
  onTargetingTypeChange: (t: TargetingType) => void;
  autoMatchTypes: string[];
  onAutoMatchTypesChange: (types: string[]) => void;
  selectedKeywords: SelectedKeyword[];
  onSelectedKeywordsChange: (kws: SelectedKeyword[]) => void;
  customKeyword: string;
  onCustomKeywordChange: (kw: string) => void;
  customMatchType: "exact" | "phrase" | "broad";
  onCustomMatchTypeChange: (mt: "exact" | "phrase" | "broad") => void;
  customBid: string;
  onCustomBidChange: (bid: string) => void;
  onAddCustomKeyword: () => void;
  negativeKeywords: string;
  onNegativeKeywordsChange: (nk: string) => void;
  suggestedKeywords: KeywordSuggestion[];
  isSuggestingKeywords: boolean;
  onSuggestKeywords: () => void;
}) {
  const { data: projects, isLoading: projectsLoading } = useProjects();

  const toggleAutoMatchType = (key: string) => {
    if (autoMatchTypes.includes(key)) {
      onAutoMatchTypesChange(autoMatchTypes.filter((t) => t !== key));
    } else {
      onAutoMatchTypesChange([...autoMatchTypes, key]);
    }
  };

  const toggleSuggestedKeyword = (suggestion: KeywordSuggestion) => {
    const exists = selectedKeywords.find(
      (k) => k.keyword === suggestion.keyword
    );
    if (exists) {
      onSelectedKeywordsChange(
        selectedKeywords.filter((k) => k.keyword !== suggestion.keyword)
      );
    } else {
      onSelectedKeywordsChange([
        ...selectedKeywords,
        {
          keyword: suggestion.keyword,
          matchType: "broad",
          bid: suggestion.suggested_bid,
        },
      ]);
    }
  };

  const removeKeyword = (keyword: string) => {
    onSelectedKeywordsChange(
      selectedKeywords.filter((k) => k.keyword !== keyword)
    );
  };

  return (
    <div className="space-y-6">
      {/* Book Selector */}
      <div className="space-y-2">
        <Label className="text-sm font-semibold">Book</Label>
        {projectsLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading books...
          </div>
        ) : (
          <Select value={bookId} onValueChange={onBookIdChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select a book to advertise" />
            </SelectTrigger>
            <SelectContent>
              {projects?.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  {project.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Campaign Name */}
      <Input
        label="Campaign Name"
        value={campaignName}
        onChange={(e) => onCampaignNameChange(e.target.value)}
        placeholder="e.g. My Book - Amazon SP - Feb 2026"
      />

      {/* Targeting Type */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold">Targeting Type</Label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {TARGETING_TYPES.map((t) => (
            <SelectionCard
              key={t.value}
              selected={targetingType === t.value}
              onClick={() => onTargetingTypeChange(t.value)}
              label={t.label}
              description={t.description}
            />
          ))}
        </div>
      </div>

      {/* Automatic Targeting Options */}
      {targetingType === "automatic" && (
        <div className="space-y-3 border rounded-lg p-4 bg-muted/10">
          <Label className="text-sm font-semibold">Match Types</Label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {AUTO_MATCH_TYPES.map((mt) => (
              <label
                key={mt.key}
                className={cn(
                  "flex items-start gap-3 border rounded-lg p-3 cursor-pointer transition-all",
                  autoMatchTypes.includes(mt.key)
                    ? "border-primary bg-primary/5"
                    : "hover:border-primary/30"
                )}
              >
                <input
                  type="checkbox"
                  checked={autoMatchTypes.includes(mt.key)}
                  onChange={() => toggleAutoMatchType(mt.key)}
                  className="mt-0.5 h-4 w-4 rounded border-input text-primary focus:ring-primary"
                />
                <div>
                  <span className="text-sm font-medium">{mt.label}</span>
                  <p className="text-xs text-muted-foreground">
                    {mt.description}
                  </p>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Manual Targeting Options */}
      {targetingType === "manual" && (
        <div className="space-y-4 border rounded-lg p-4 bg-muted/10">
          {/* AI Suggested Keywords */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-semibold">
                AI Suggested Keywords
              </Label>
              <Button
                variant="outline"
                size="sm"
                onClick={onSuggestKeywords}
                disabled={!bookId || isSuggestingKeywords}
              >
                {isSuggestingKeywords ? (
                  <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                )}
                {isSuggestingKeywords ? "Analyzing..." : "Get Suggestions"}
              </Button>
            </div>
            {suggestedKeywords.length > 0 && (
              <div className="border rounded-md overflow-hidden">
                <div className="grid grid-cols-[1fr_auto_auto_auto] gap-2 px-3 py-2 bg-muted text-xs font-medium text-muted-foreground">
                  <span>Keyword</span>
                  <span>Volume</span>
                  <span>Bid</span>
                  <span></span>
                </div>
                <div className="max-h-[200px] overflow-y-auto">
                  {suggestedKeywords.map((suggestion) => {
                    const isSelected = selectedKeywords.some(
                      (k) => k.keyword === suggestion.keyword
                    );
                    return (
                      <label
                        key={suggestion.keyword}
                        className={cn(
                          "grid grid-cols-[1fr_auto_auto_auto] gap-2 px-3 py-2 items-center cursor-pointer text-sm border-t hover:bg-muted/50",
                          isSelected && "bg-primary/5"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSuggestedKeyword(suggestion)}
                            className="h-4 w-4 rounded border-input text-primary focus:ring-primary"
                          />
                          <span className="truncate">{suggestion.keyword}</span>
                        </div>
                        <span className="text-muted-foreground text-xs">
                          {suggestion.search_volume.toLocaleString()}
                        </span>
                        <span className="text-xs">
                          ${suggestion.suggested_bid.toFixed(2)}
                        </span>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-[10px]",
                            suggestion.competition === "low" &&
                              "text-green-700 border-green-300",
                            suggestion.competition === "medium" &&
                              "text-yellow-700 border-yellow-300",
                            suggestion.competition === "high" &&
                              "text-red-700 border-red-300"
                          )}
                        >
                          {suggestion.competition}
                        </Badge>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}
            {!bookId && (
              <p className="text-xs text-muted-foreground">
                Select a book above to get AI keyword suggestions.
              </p>
            )}
          </div>

          {/* Add Custom Keywords */}
          <div className="space-y-2">
            <Label className="text-sm font-semibold">Add Custom Keywords</Label>
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  value={customKeyword}
                  onChange={(e) => onCustomKeywordChange(e.target.value)}
                  placeholder="Enter keyword"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      onAddCustomKeyword();
                    }
                  }}
                />
              </div>
              <Select
                value={customMatchType}
                onValueChange={(v) =>
                  onCustomMatchTypeChange(v as "exact" | "phrase" | "broad")
                }
              >
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="broad">Broad</SelectItem>
                  <SelectItem value="phrase">Phrase</SelectItem>
                  <SelectItem value="exact">Exact</SelectItem>
                </SelectContent>
              </Select>
              <div className="w-[90px]">
                <Input
                  type="number"
                  step="0.01"
                  min="0.02"
                  value={customBid}
                  onChange={(e) => onCustomBidChange(e.target.value)}
                  placeholder="$0.75"
                />
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={onAddCustomKeyword}
                disabled={!customKeyword.trim()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Your Keywords */}
          {selectedKeywords.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-semibold">
                Your Keywords ({selectedKeywords.length})
              </Label>
              <div className="border rounded-md max-h-[200px] overflow-y-auto">
                {selectedKeywords.map((kw) => (
                  <div
                    key={`${kw.keyword}-${kw.matchType}`}
                    className="flex items-center justify-between px-3 py-2 text-sm border-b last:border-b-0"
                  >
                    <div className="flex items-center gap-2">
                      <span>{kw.keyword}</span>
                      <Badge variant="outline" className="text-[10px]">
                        {kw.matchType}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-xs">
                        ${kw.bid.toFixed(2)}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeKeyword(kw.keyword)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Negative Keywords */}
          <div className="space-y-2">
            <Label className="text-sm font-semibold">Negative Keywords</Label>
            <Textarea
              value={negativeKeywords}
              onChange={(e) => onNegativeKeywordsChange(e.target.value)}
              placeholder="Enter negative keywords, separated by commas"
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              These keywords prevent your ads from showing for irrelevant
              searches.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3: Budget & Schedule
// ---------------------------------------------------------------------------

function StepBudgetSchedule({
  dailyBudget,
  onDailyBudgetChange,
  biddingStrategy,
  onBiddingStrategyChange,
  defaultBid,
  onDefaultBidChange,
  scheduleType,
  onScheduleTypeChange,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
}: {
  dailyBudget: string;
  onDailyBudgetChange: (v: string) => void;
  biddingStrategy: BiddingStrategy;
  onBiddingStrategyChange: (s: BiddingStrategy) => void;
  defaultBid: string;
  onDefaultBidChange: (v: string) => void;
  scheduleType: ScheduleType;
  onScheduleTypeChange: (s: ScheduleType) => void;
  startDate: string;
  onStartDateChange: (d: string) => void;
  endDate: string;
  onEndDateChange: (d: string) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Daily Budget */}
      <div className="space-y-2">
        <Label className="text-sm font-semibold">Daily Budget</Label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            $
          </span>
          <input
            type="number"
            step="1"
            min="1"
            value={dailyBudget}
            onChange={(e) => onDailyBudgetChange(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background pl-7 pr-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            placeholder="25"
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Recommended: $10-15/day for new campaigns
        </p>
      </div>

      {/* Bidding Strategy */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold">Bidding Strategy</Label>
        <div className="grid grid-cols-1 gap-3">
          {BIDDING_STRATEGIES.map((s) => (
            <SelectionCard
              key={s.value}
              selected={biddingStrategy === s.value}
              onClick={() => onBiddingStrategyChange(s.value)}
              label={s.label}
              description={s.description}
            />
          ))}
        </div>
      </div>

      {/* Default Bid */}
      <div className="space-y-2">
        <Label className="text-sm font-semibold">Default Bid</Label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            $
          </span>
          <input
            type="number"
            step="0.01"
            min="0.02"
            value={defaultBid}
            onChange={(e) => onDefaultBidChange(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background pl-7 pr-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            placeholder="0.75"
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Suggested range: $0.25 - $1.50 for book advertising
        </p>
      </div>

      {/* Schedule */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold">Schedule</Label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <SelectionCard
            selected={scheduleType === "immediate"}
            onClick={() => onScheduleTypeChange("immediate")}
            icon={Sparkles}
            label="Start immediately"
            description="Campaign runs continuously until you pause it"
          />
          <SelectionCard
            selected={scheduleType === "scheduled"}
            onClick={() => onScheduleTypeChange("scheduled")}
            icon={Calendar}
            label="Set dates"
            description="Choose specific start and end dates"
          />
        </div>

        {scheduleType === "scheduled" && (
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="space-y-1.5">
              <Label className="text-sm">Start Date</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => onStartDateChange(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm">End Date</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => onEndDateChange(e.target.value)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Wizard
// ---------------------------------------------------------------------------

export function CampaignWizard({ open, onOpenChange }: CampaignWizardProps) {
  const router = useRouter();

  // Step state
  const [step, setStep] = useState<WizardStep>(1);

  // Step 1 state
  const [platform, setPlatform] = useState<Platform>("amazon");
  const [adType, setAdType] = useState<AmazonAdType>("sponsored_products");

  // Step 2 state
  const [bookId, setBookId] = useState("");
  const [campaignName, setCampaignName] = useState("");
  const [targetingType, setTargetingType] = useState<TargetingType>("automatic");
  const [autoMatchTypes, setAutoMatchTypes] = useState<string[]>([
    "close_match",
    "loose_match",
    "substitutes",
    "complements",
  ]);
  const [selectedKeywords, setSelectedKeywords] = useState<SelectedKeyword[]>(
    []
  );
  const [customKeyword, setCustomKeyword] = useState("");
  const [customMatchType, setCustomMatchType] = useState<
    "exact" | "phrase" | "broad"
  >("broad");
  const [customBid, setCustomBid] = useState("0.75");
  const [negativeKeywords, setNegativeKeywords] = useState("");
  const [suggestedKeywords, setSuggestedKeywords] = useState<
    KeywordSuggestion[]
  >([]);

  // Step 3 state
  const [dailyBudget, setDailyBudget] = useState("25");
  const [biddingStrategy, setBiddingStrategy] =
    useState<BiddingStrategy>("dynamic_down");
  const [defaultBid, setDefaultBid] = useState("0.75");
  const [scheduleType, setScheduleType] = useState<ScheduleType>("immediate");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Hooks
  const createCampaign = useCreateCampaign();
  const suggestKeywordsMutation = useSuggestKeywords();
  const { data: projects } = useProjects();

  // Auto-suggest campaign name when book or platform changes
  useEffect(() => {
    if (bookId && projects) {
      const book = projects.find((p) => p.id === bookId);
      if (book) {
        const platformLabel = PLATFORMS.find(
          (p) => p.value === platform
        )?.label;
        const typeLabel =
          platform === "amazon"
            ? AMAZON_AD_TYPES.find((t) => t.value === adType)?.label
            : "";
        const parts = [book.title, platformLabel, typeLabel].filter(Boolean);
        setCampaignName(parts.join(" - "));
      }
    }
  }, [bookId, platform, adType, projects]);

  // Reset all state
  const reset = useCallback(() => {
    setStep(1);
    setPlatform("amazon");
    setAdType("sponsored_products");
    setBookId("");
    setCampaignName("");
    setTargetingType("automatic");
    setAutoMatchTypes([
      "close_match",
      "loose_match",
      "substitutes",
      "complements",
    ]);
    setSelectedKeywords([]);
    setCustomKeyword("");
    setCustomMatchType("broad");
    setCustomBid("0.75");
    setNegativeKeywords("");
    setSuggestedKeywords([]);
    setDailyBudget("25");
    setBiddingStrategy("dynamic_down");
    setDefaultBid("0.75");
    setScheduleType("immediate");
    setStartDate("");
    setEndDate("");
  }, []);

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen && !createCampaign.isPending) {
      reset();
    }
    onOpenChange(nextOpen);
  };

  const handleAddCustomKeyword = () => {
    const trimmed = customKeyword.trim();
    if (!trimmed) return;
    if (selectedKeywords.some((k) => k.keyword === trimmed)) {
      toast.error("Keyword already added");
      return;
    }
    setSelectedKeywords([
      ...selectedKeywords,
      {
        keyword: trimmed,
        matchType: customMatchType,
        bid: parseFloat(customBid) || 0.75,
      },
    ]);
    setCustomKeyword("");
  };

  const handleSuggestKeywords = () => {
    if (!bookId) return;
    suggestKeywordsMutation.mutate(bookId, {
      onSuccess: (data) => {
        setSuggestedKeywords(data);
        toast.success(`Found ${data.length} keyword suggestions`);
      },
    });
  };

  const canProceed = (): boolean => {
    if (step === 1) return !!platform;
    if (step === 2) return !!bookId && !!campaignName.trim();
    if (step === 3) {
      const budget = parseFloat(dailyBudget);
      if (!budget || budget <= 0) return false;
      const bid = parseFloat(defaultBid);
      if (!bid || bid <= 0) return false;
      if (scheduleType === "scheduled" && (!startDate || !endDate))
        return false;
      return true;
    }
    return true;
  };

  const handleNext = () => {
    if (step < 3) {
      setStep((s) => (s + 1) as WizardStep);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((s) => (s - 1) as WizardStep);
    }
  };

  const handleLaunch = async () => {
    const budget = parseFloat(dailyBudget);
    const bid = parseFloat(defaultBid);
    if (!budget || !bid) return;

    const negKws = negativeKeywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);

    const targetingKws =
      targetingType === "manual"
        ? selectedKeywords.map((k) => k.keyword)
        : undefined;

    try {
      const campaign = await createCampaign.mutateAsync({
        name: campaignName,
        platform: platform,
        campaign_type:
          platform === "amazon" ? adType : `${platform}_default`,
        daily_budget: budget,
        bid_strategy: biddingStrategy,
        target_acos: 30,
        targeting_keywords: targetingKws,
        negative_keywords: negKws.length > 0 ? negKws : undefined,
      });
      toast.success("Campaign created successfully!");
      reset();
      onOpenChange(false);
      if (campaign?.id) {
        router.push(`/advertising/campaigns/${campaign.id}`);
      }
    } catch {
      // Error is handled by the mutation's onError
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Campaign</DialogTitle>
          <DialogDescription>
            Set up a new advertising campaign in three easy steps.
          </DialogDescription>
        </DialogHeader>

        <StepIndicator current={step} />

        {/* Step content */}
        {step === 1 && (
          <StepPlatformType
            platform={platform}
            onPlatformChange={setPlatform}
            adType={adType}
            onAdTypeChange={setAdType}
          />
        )}

        {step === 2 && (
          <StepBookTargeting
            bookId={bookId}
            onBookIdChange={setBookId}
            campaignName={campaignName}
            onCampaignNameChange={setCampaignName}
            targetingType={targetingType}
            onTargetingTypeChange={setTargetingType}
            autoMatchTypes={autoMatchTypes}
            onAutoMatchTypesChange={setAutoMatchTypes}
            selectedKeywords={selectedKeywords}
            onSelectedKeywordsChange={setSelectedKeywords}
            customKeyword={customKeyword}
            onCustomKeywordChange={setCustomKeyword}
            customMatchType={customMatchType}
            onCustomMatchTypeChange={setCustomMatchType}
            customBid={customBid}
            onCustomBidChange={setCustomBid}
            onAddCustomKeyword={handleAddCustomKeyword}
            negativeKeywords={negativeKeywords}
            onNegativeKeywordsChange={setNegativeKeywords}
            suggestedKeywords={suggestedKeywords}
            isSuggestingKeywords={suggestKeywordsMutation.isPending}
            onSuggestKeywords={handleSuggestKeywords}
          />
        )}

        {step === 3 && (
          <StepBudgetSchedule
            dailyBudget={dailyBudget}
            onDailyBudgetChange={setDailyBudget}
            biddingStrategy={biddingStrategy}
            onBiddingStrategyChange={setBiddingStrategy}
            defaultBid={defaultBid}
            onDefaultBidChange={setDefaultBid}
            scheduleType={scheduleType}
            onScheduleTypeChange={setScheduleType}
            startDate={startDate}
            onStartDateChange={setStartDate}
            endDate={endDate}
            onEndDateChange={setEndDate}
          />
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={step === 1 ? () => handleOpenChange(false) : handleBack}
            disabled={createCampaign.isPending}
          >
            {step === 1 ? (
              <>Cancel</>
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </>
            )}
          </Button>

          {step < 3 ? (
            <Button onClick={handleNext} disabled={!canProceed()}>
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={handleLaunch}
              disabled={createCampaign.isPending || !canProceed()}
            >
              {createCampaign.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              {createCampaign.isPending
                ? "Launching..."
                : "Launch Campaign"}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
