"use client";

import {
  Card,
  CardHeader,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslations } from "@/hooks/use-translations";
import { ThemeCards } from "./ThemeCards";
import type { ReviewInsightsResponse } from "@/modules/reviews/hooks";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ReviewInsightsProps {
  insights: ReviewInsightsResponse | undefined;
  onRefresh: () => void;
  onExport: () => void;
  isRefreshing?: boolean;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function InsightsSkeleton({ message }: { message: string }) {
  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">{message}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
      <Skeleton className="h-32" />
      <Skeleton className="h-48" />
      <Skeleton className="h-64" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Keyword Cloud (div-based, no library)
// ---------------------------------------------------------------------------

function KeywordCloud({
  keywords,
}: {
  keywords: ReviewInsightsResponse["keyword_cloud"];
}) {
  if (!keywords || keywords.length === 0) return null;

  const maxValue = Math.max(...keywords.map((k) => k.value));
  const minValue = Math.min(...keywords.map((k) => k.value));
  const range = maxValue - minValue || 1;

  function getFontSize(value: number): number {
    // Scale between 12px and 32px
    return 12 + ((value - minValue) / range) * 20;
  }

  function getSentimentColor(sentiment: string): string {
    switch (sentiment) {
      case "positive":
        return "text-green-600 dark:text-green-400";
      case "negative":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-muted-foreground";
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-center gap-3 py-4">
      {keywords.map((kw) => (
        <span
          key={kw.text}
          className={`inline-block font-medium transition-opacity hover:opacity-70 ${getSentimentColor(kw.sentiment)}`}
          style={{ fontSize: `${getFontSize(kw.value)}px` }}
          title={`${kw.text}: ${kw.value} mentions`}
        >
          {kw.text}
        </span>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Velocity Chart
// ---------------------------------------------------------------------------

function VelocityChart({
  data,
  t,
}: {
  data: ReviewInsightsResponse["velocity_data"];
  t: ReturnType<typeof useTranslations>;
}) {
  if (!data || data.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <h4 className="text-sm font-semibold">{t("insights.velocityChart")}</h4>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="week"
              tick={{ fontSize: 11 }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="yours"
              name={t("insights.yourReviews")}
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="genre_avg"
              name={t("insights.genreAvg")}
              stroke="#9ca3af"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function ReviewInsights({
  insights,
  onRefresh,
  onExport,
  isRefreshing = false,
  isLoading = false,
}: ReviewInsightsProps) {
  const t = useTranslations("reviews");

  // ---- Loading state ----
  if (isLoading) {
    return (
      <div className="space-y-6">
        <InsightsSkeleton message={t("insights.analyzing")} />
      </div>
    );
  }

  // ---- Empty state ----
  if (!insights) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
        <p className="text-sm text-muted-foreground max-w-sm mb-4">
          {t("insights.emptyState")}
        </p>
        <Button onClick={onRefresh} disabled={isRefreshing}>
          {isRefreshing ? t("insights.refreshing") : t("insights.refreshAnalysis")}
        </Button>
      </div>
    );
  }

  // ---- Format computed_at timestamp ----
  const lastAnalyzed = insights.computed_at
    ? new Date(insights.computed_at).toLocaleString()
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{t("insights.title")}</h3>
          {lastAnalyzed && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {t("insights.lastAnalyzed", { time: lastAnalyzed })}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? t("insights.refreshing") : t("insights.refreshAnalysis")}
          </Button>
          <Button variant="outline" size="sm" onClick={onExport}>
            {t("insights.exportReport")}
          </Button>
        </div>
      </div>

      {/* Row 1: Theme Cards */}
      <ThemeCards
        positiveThemes={insights.positive_themes}
        negativeThemes={insights.negative_themes}
      />

      {/* Row 2: Keyword Cloud */}
      {insights.keyword_cloud && insights.keyword_cloud.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <h4 className="text-sm font-semibold">{t("insights.keywordCloud")}</h4>
          </CardHeader>
          <CardContent>
            <KeywordCloud keywords={insights.keyword_cloud} />
          </CardContent>
        </Card>
      )}

      {/* Row 3: AI Summary + Action Items */}
      <Card>
        <CardHeader className="pb-3">
          <h4 className="text-sm font-semibold">{t("insights.aiSummary")}</h4>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Summary text */}
          {insights.ai_summary && (
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
              {insights.ai_summary}
            </p>
          )}

          {/* Action Items */}
          {insights.action_items && insights.action_items.length > 0 && (
            <div>
              <h5 className="text-sm font-medium mb-2">{t("insights.actionItems")}</h5>
              <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                {insights.action_items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2 pt-2">
            <Button variant="secondary" size="sm">
              {t("insights.applyToBookUpdates")}
            </Button>
            <Button variant="outline" size="sm">
              {t("insights.createRevisionTask")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Row 4: Velocity Chart */}
      <VelocityChart data={insights.velocity_data} t={t} />
    </div>
  );
}
