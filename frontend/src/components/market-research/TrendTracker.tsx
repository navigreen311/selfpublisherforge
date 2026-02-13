"use client";

import { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  X,
} from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { useMarketTrends, useTrendChart } from "@/modules/market/hooks";
import type { MarketTrend, TrendingTopic } from "@/modules/market/hooks";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type TimeRange = "3mo" | "6mo" | "12mo" | "2y";

const TIME_RANGE_DAYS: Record<TimeRange, number> = {
  "3mo": 90,
  "6mo": 180,
  "12mo": 365,
  "2y": 730,
};

const TIME_RANGE_PERIOD: Record<TimeRange, string> = {
  "3mo": "3m",
  "6mo": "6m",
  "12mo": "12m",
  "2y": "24m",
};

const CHART_COLORS = [
  "#3b82f6", // blue
  "#22c55e", // green
  "#f59e0b", // amber
  "#8b5cf6", // violet
  "#ef4444", // red
];

const MAX_KEYWORDS = 5;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Render filled dots for trend strength (1-5 scale based on change_pct). */
function StrengthDots({ changePct }: { changePct: number }) {
  const abs = Math.abs(changePct);
  let dots: number;
  if (abs >= 100) dots = 5;
  else if (abs >= 50) dots = 4;
  else if (abs >= 25) dots = 3;
  else if (abs >= 10) dots = 2;
  else dots = 1;

  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`Strength ${dots} of 5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={cn(
            "inline-block h-1.5 w-1.5 rounded-full",
            i < dots ? "bg-current" : "bg-muted"
          )}
        />
      ))}
    </span>
  );
}

/** Derive trending up/down lists from MarketTrend[] when not provided by API. */
function deriveTrendingLists(trends: MarketTrend[]) {
  const up: TrendingTopic[] = [];
  const down: TrendingTopic[] = [];

  for (const trend of trends) {
    const topic = trend.label || trend.keyword || "Unknown";
    if (trend.direction === "up" || trend.change_pct > 0) {
      up.push({ topic, change_pct: trend.change_pct, direction: "up" });
    } else if (trend.direction === "down" || trend.change_pct < 0) {
      down.push({ topic, change_pct: trend.change_pct, direction: "down" });
    }
  }

  // Sort by absolute change descending
  up.sort((a, b) => b.change_pct - a.change_pct);
  down.sort((a, b) => a.change_pct - b.change_pct);

  return { up, down };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface TrendingPanelProps {
  title: string;
  icon: React.ReactNode;
  items: TrendingTopic[];
  variant: "up" | "down";
  onItemClick?: (topic: string) => void;
}

function TrendingPanel({ title, icon, items, variant, onItemClick }: TrendingPanelProps) {
  const badgeClass =
    variant === "up"
      ? "bg-green-100 text-green-700 hover:bg-green-200"
      : "bg-red-100 text-red-700 hover:bg-red-200";

  const textColorClass = variant === "up" ? "text-green-600" : "text-red-600";

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No trends detected
          </p>
        ) : (
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item.topic}>
                <button
                  type="button"
                  onClick={() => onItemClick?.(item.topic)}
                  className="flex w-full items-center justify-between gap-2 rounded-md px-3 py-2 text-left transition-colors hover:bg-muted/50"
                >
                  <span className="text-sm font-medium truncate">
                    {item.topic}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={cn("text-xs", textColorClass)}>
                      <StrengthDots changePct={item.change_pct} />
                    </span>
                    <Badge
                      className={cn(
                        "text-xs font-medium border-transparent",
                        badgeClass
                      )}
                    >
                      {item.change_pct > 0 ? "+" : ""}
                      {item.change_pct.toFixed(1)}%
                    </Badge>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

interface KeywordPillProps {
  keyword: string;
  color: string;
  onRemove: () => void;
}

function KeywordPill({ keyword, color, onRemove }: KeywordPillProps) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium"
      style={{ borderColor: color, color }}
    >
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      {keyword}
      <button
        type="button"
        onClick={onRemove}
        className="ml-0.5 rounded-full p-0.5 hover:bg-muted transition-colors"
        aria-label={`Remove ${keyword}`}
      >
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface TrendTrackerProps {
  onAnalyzeTrend?: (topic: string) => void;
}

export function TrendTracker({ onAnalyzeTrend }: TrendTrackerProps) {
  const t = useTranslations("market");

  // ---- State ----
  const [selectedPeriod, setSelectedPeriod] = useState<TimeRange>("12mo");
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState("");

  // ---- Data fetching ----
  const days = TIME_RANGE_DAYS[selectedPeriod];
  const {
    data: trendsData,
    isLoading: trendsLoading,
  } = useMarketTrends(undefined, undefined, days);

  const chartPeriod = TIME_RANGE_PERIOD[selectedPeriod];
  const {
    data: chartData,
    isLoading: chartLoading,
  } = useTrendChart(selectedKeywords, chartPeriod);

  // ---- Derived trending lists ----
  const { trendingUp, trendingDown } = useMemo(() => {
    if (!trendsData) return { trendingUp: [], trendingDown: [] };

    if (trendsData.trending_up && trendsData.trending_down) {
      return {
        trendingUp: trendsData.trending_up,
        trendingDown: trendsData.trending_down,
      };
    }

    const derived = deriveTrendingLists(trendsData.trends ?? []);
    return { trendingUp: derived.up, trendingDown: derived.down };
  }, [trendsData]);

  // ---- Build chart data for recharts ----
  const rechartsData = useMemo(() => {
    if (!chartData?.series || chartData.series.length === 0) return [];

    // Collect all unique dates
    const dateMap = new Map<string, Record<string, number>>();
    for (const series of chartData.series) {
      for (const point of series.data) {
        if (!dateMap.has(point.date)) {
          dateMap.set(point.date, {});
        }
        dateMap.get(point.date)![series.keyword] = point.value;
      }
    }

    // Sort by date and produce array
    return Array.from(dateMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, values]) => ({
        date: new Date(date).toLocaleDateString("en-US", {
          month: "short",
          year: "2-digit",
        }),
        ...values,
      }));
  }, [chartData]);

  // ---- Seasonal insights ----
  const seasonalInsights = useMemo(() => {
    if (!trendsData?.trends) return [];
    // Extract insights from trends that have seasonal patterns
    const insights: string[] = [];
    for (const trend of trendsData.trends) {
      if (trend.data_points && trend.data_points.length >= 6) {
        const label = trend.label || trend.keyword || "";
        if (trend.direction === "up" && trend.change_pct > 20) {
          insights.push(
            `${label} is showing strong upward momentum (+${trend.change_pct.toFixed(1)}%) over the selected period.`
          );
        } else if (trend.direction === "down" && trend.change_pct < -20) {
          insights.push(
            `${label} has declined ${Math.abs(trend.change_pct).toFixed(1)}% - consider timing your launch around seasonal peaks.`
          );
        }
      }
    }
    if (insights.length === 0 && trendsData.trends.length > 0) {
      insights.push(
        "Market trends appear stable across the selected period. Monitor for seasonal shifts."
      );
    }
    return insights;
  }, [trendsData]);

  // ---- Keyword management ----
  const handleAddKeyword = () => {
    const kw = keywordInput.trim();
    if (
      kw &&
      selectedKeywords.length < MAX_KEYWORDS &&
      !selectedKeywords.includes(kw)
    ) {
      setSelectedKeywords((prev) => [...prev, kw]);
      setKeywordInput("");
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setSelectedKeywords((prev) => prev.filter((k) => k !== keyword));
  };

  const handleKeywordKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  // ---- Render ----
  return (
    <div className="space-y-6">
      {/* Header with time range selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-2xl font-semibold tracking-tight">
          {t("trends.title")}
        </h2>

        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {t("trends.timeRange")}
          </span>
          <Select
            value={selectedPeriod}
            onValueChange={(val) => setSelectedPeriod(val as TimeRange)}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3mo">{t("trends.range3m")}</SelectItem>
              <SelectItem value="6mo">{t("trends.range6m")}</SelectItem>
              <SelectItem value="12mo">{t("trends.range12m")}</SelectItem>
              <SelectItem value="2y">{t("trends.range2y")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Trending panels (2 cards side by side) */}
      {trendsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-6 space-y-3">
              <Skeleton className="h-5 w-32" />
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 space-y-3">
              <Skeleton className="h-5 w-32" />
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </CardContent>
          </Card>
        </div>
      ) : trendingUp.length === 0 && trendingDown.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-muted p-3 mb-3">
              <TrendingUp className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">
              {t("trends.noTrends")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TrendingPanel
            title={t("trends.trendingUp")}
            icon={<TrendingUp className="h-5 w-5 text-green-600" />}
            items={trendingUp}
            variant="up"
            onItemClick={onAnalyzeTrend}
          />
          <TrendingPanel
            title={t("trends.trendingDown")}
            icon={<TrendingDown className="h-5 w-5 text-red-600" />}
            items={trendingDown}
            variant="down"
            onItemClick={onAnalyzeTrend}
          />
        </div>
      )}

      {/* Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("trends.chartTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Keyword selector */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={handleKeywordKeyDown}
                placeholder={t("trends.addKeyword")}
                disabled={selectedKeywords.length >= MAX_KEYWORDS}
                className="flex h-9 w-full max-w-xs rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddKeyword}
                disabled={
                  !keywordInput.trim() ||
                  selectedKeywords.length >= MAX_KEYWORDS
                }
              >
                Add
              </Button>
            </div>

            {/* Selected keyword pills */}
            {selectedKeywords.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedKeywords.map((kw, idx) => (
                  <KeywordPill
                    key={kw}
                    keyword={kw}
                    color={CHART_COLORS[idx % CHART_COLORS.length]}
                    onRemove={() => handleRemoveKeyword(kw)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Chart */}
          {selectedKeywords.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-sm text-muted-foreground">
                {t("trends.addKeyword")}
              </p>
            </div>
          ) : chartLoading ? (
            <Skeleton className="h-[300px] w-full" />
          ) : rechartsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={rechartsData}>
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {selectedKeywords.map((kw, idx) => (
                  <Line
                    key={kw}
                    type="monotone"
                    dataKey={kw}
                    stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-sm text-muted-foreground">
                {t("trends.noTrends")}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Seasonal Insights */}
      {seasonalInsights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              {t("trends.seasonalInsights")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {seasonalInsights.map((insight, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground/60" />
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
