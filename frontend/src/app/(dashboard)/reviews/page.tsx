"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useReviewStats,
  useSentimentTrend,
  useBookReviewSummaries,
  useReviews,
  useReviewInsights,
  useRefreshInsights,
  useAlerts,
  useAlertNotifications,
  useMarkReviewRead,
  useFlagReview,
  useDeleteReviewAlert,
} from "@/modules/reviews/hooks";
import type { ReviewListParams, SentimentLabel } from "@/modules/reviews/hooks";
import { SentimentTrendChart } from "@/components/review-intelligence/SentimentTrendChart";
import { RatingDistribution } from "@/components/review-intelligence/RatingDistribution";
import { BookReviewCards } from "@/components/review-intelligence/BookReviewCards";
import { ReviewFeed } from "@/components/review-intelligence/ReviewFeed";
import { ReviewInsights } from "@/components/review-intelligence/ReviewInsights";
import { ReviewAcquisition } from "@/components/review-intelligence/ReviewAcquisition";
import { ReviewAlertsTab } from "@/components/review-intelligence/ReviewAlertsTab";
import {
  Star,
  TrendingUp,
  TrendingDown,
  ArrowUp,
  ArrowDown,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

type TabKey = "books" | "feed" | "insights" | "acquisition" | "alerts";

const TABS: { key: TabKey; labelKey: string }[] = [
  { key: "books", labelKey: "tabs.yourBooks" },
  { key: "feed", labelKey: "tabs.reviewFeed" },
  { key: "insights", labelKey: "tabs.insights" },
  { key: "acquisition", labelKey: "tabs.acquisition" },
  { key: "alerts", labelKey: "tabs.alerts" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSentimentColor(score: number): string {
  if (score >= 70) return "text-green-600";
  if (score >= 40) return "text-yellow-600";
  return "text-red-600";
}

function renderStars(rating: number) {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.25;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className="flex items-center gap-0.5">
      {[...Array(fullStars)].map((_, i) => (
        <Star key={`f-${i}`} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
      ))}
      {hasHalfStar && (
        <Star className="h-4 w-4 fill-yellow-400/50 text-yellow-400" />
      )}
      {[...Array(emptyStars)].map((_, i) => (
        <Star key={`e-${i}`} className="h-4 w-4 text-gray-300" />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stat Card Shell
// ---------------------------------------------------------------------------

function StatCard({
  children,
  isLoading,
}: {
  children: React.ReactNode;
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <div className="rounded-lg border bg-card p-5 shadow-sm space-y-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-20 mt-1" />
        <Skeleton className="h-3 w-32 mt-1" />
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-5 shadow-sm">{children}</div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ReviewsPage() {
  const t = useTranslations("reviews");
  const [activeTab, setActiveTab] = useState<TabKey>("books");

  // Feed tab state
  const [feedBookFilter, setFeedBookFilter] = useState("all");
  const [feedRatingFilter, setFeedRatingFilter] = useState<number | null>(null);
  const [feedSentimentFilter, setFeedSentimentFilter] = useState<string | null>(null);
  const [feedSortBy, setFeedSortBy] = useState("newest");
  const [feedCursor, setFeedCursor] = useState<string | undefined>(undefined);

  // Chart state
  const [trendPeriod, setTrendPeriod] = useState("6m");
  const [trendBookFilter, setTrendBookFilter] = useState("all");

  // Build review list params from feed state
  const reviewListParams: ReviewListParams = {
    limit: 20,
    cursor: feedCursor,
    sentiment: feedSentimentFilter ? (feedSentimentFilter as SentimentLabel) : undefined,
    min_rating: feedRatingFilter ?? undefined,
    book_id: feedBookFilter === "all" ? undefined : feedBookFilter,
    sort_by: feedSortBy === "highest" || feedSortBy === "lowest" ? "star_rating" : "review_date",
    sort_dir: feedSortBy === "oldest" || feedSortBy === "highest" ? "asc" : "desc",
  };

  // ---- Data hooks ----
  const { data: stats, isLoading: statsLoading } = useReviewStats();
  const { data: sentimentTrend, isLoading: trendLoading } = useSentimentTrend(
    trendBookFilter === "all" ? undefined : trendBookFilter,
    trendPeriod,
  );
  const { data: bookSummaries, isLoading: booksLoading } = useBookReviewSummaries();
  const { data: reviewsData, isLoading: reviewsLoading } = useReviews(reviewListParams);
  const { data: insightsData, isLoading: insightsLoading } = useReviewInsights();
  const refreshInsights = useRefreshInsights();
  const { data: alertsData, isLoading: alertsLoading } = useAlerts();
  const { data: alertNotifications } = useAlertNotifications();
  const markReadMutation = useMarkReviewRead();
  const flagMutation = useFlagReview();
  const deleteAlertMutation = useDeleteReviewAlert();

  // ---- Stat values (safe defaults) ----
  const total = stats?.total ?? 0;
  const avgRating = stats?.avg_rating ?? 0;
  const thisMonth = stats?.this_month ?? 0;
  const thisMonthChangePct = stats?.this_month_change_pct ?? 0;
  const sentimentScore = stats?.sentiment_score ?? 0;
  const velocity = stats?.velocity ?? 0;
  const genreAvgVelocity = stats?.genre_avg_velocity ?? 0;
  const needsAttention = stats?.needs_attention ?? 0;
  const bookCount = stats?.book_count ?? 0;
  const ratingDistribution = stats?.rating_distribution ?? {};

  // ---- Render active tab content ----
  function renderTabContent() {
    switch (activeTab) {
      case "books":
        return (
          <BookReviewCards
            books={bookSummaries ?? []}
            isLoading={booksLoading}
            onViewReviews={(bookId) => {
              setFeedBookFilter(bookId);
              setActiveTab("feed");
            }}
            onRunAnalysis={() => {}}
            onAcquisition={() => {
              setActiveTab("acquisition");
            }}
          />
        );

      case "feed":
        return (
          <ReviewFeed
            reviews={reviewsData?.items ?? []}
            total={reviewsData?.total_count ?? 0}
            hasMore={reviewsData?.has_more ?? false}
            onLoadMore={() => {
              if (reviewsData?.next_cursor) {
                setFeedCursor(reviewsData.next_cursor);
              }
            }}
            onMarkRead={(reviewId, read) => markReadMutation.mutate({ reviewId, read })}
            onFlag={(reviewId, flagged) => flagMutation.mutate({ reviewId, flagged })}
            bookFilter={feedBookFilter}
            onBookFilterChange={setFeedBookFilter}
            ratingFilter={feedRatingFilter}
            onRatingFilterChange={setFeedRatingFilter}
            sentimentFilter={feedSentimentFilter}
            onSentimentFilterChange={setFeedSentimentFilter}
            sortBy={feedSortBy}
            onSortChange={setFeedSortBy}
            isLoading={reviewsLoading}
          />
        );

      case "insights":
        return (
          <ReviewInsights
            insights={insightsData}
            isLoading={insightsLoading}
            onRefresh={() => refreshInsights.mutate({})}
            onExport={() => {}}
            isRefreshing={refreshInsights.isPending}
          />
        );

      case "acquisition":
        return <ReviewAcquisition />;

      case "alerts":
        return (
          <ReviewAlertsTab
            alerts={alertsData?.items ?? []}
            notifications={alertNotifications ?? []}
            onCreateAlert={() => {}}
            onEditAlert={() => {}}
            onDeleteAlert={(alertId) => deleteAlertMutation.mutate(alertId)}
            onAcknowledge={() => {}}
            isLoading={alertsLoading}
          />
        );

      default:
        return null;
    }
  }

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* Page Header                                                         */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          {t("title")}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("subtitle")}
        </p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Row 1: Stat Cards                                                   */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Total Reviews */}
        <StatCard isLoading={statsLoading}>
          <p className="text-sm font-medium text-muted-foreground">
            {t("stats.totalReviews")}
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {total.toLocaleString()}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {bookCount} {bookCount === 1 ? "book" : "books"}
          </p>
        </StatCard>

        {/* Avg Rating */}
        <StatCard isLoading={statsLoading}>
          <p className="text-sm font-medium text-muted-foreground">
            {t("stats.avgRating")}
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {avgRating.toFixed(1)}
          </p>
          <div className="mt-0.5">{renderStars(avgRating)}</div>
        </StatCard>

        {/* This Month */}
        <StatCard isLoading={statsLoading}>
          <p className="text-sm font-medium text-muted-foreground">
            {t("stats.thisMonth")}
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {thisMonth.toLocaleString()}
          </p>
          <div className="mt-0.5 flex items-center gap-1 text-xs">
            {thisMonthChangePct >= 0 ? (
              <ArrowUp className="h-3 w-3 text-green-600" />
            ) : (
              <ArrowDown className="h-3 w-3 text-red-600" />
            )}
            <span
              className={
                thisMonthChangePct >= 0 ? "text-green-600" : "text-red-600"
              }
            >
              {Math.abs(thisMonthChangePct).toFixed(1)}%
            </span>
            <span className="text-muted-foreground">
              {t("stats.vsLastMonth", { pct: Math.abs(thisMonthChangePct).toFixed(1) })}
            </span>
          </div>
        </StatCard>

        {/* Sentiment Score */}
        <StatCard isLoading={statsLoading}>
          <p className="text-sm font-medium text-muted-foreground">
            {t("stats.sentimentScore")}
          </p>
          <p
            className={cn(
              "mt-1 text-2xl font-bold",
              getSentimentColor(sentimentScore),
            )}
          >
            {sentimentScore}
          </p>
          <div className="mt-0.5 flex items-center gap-1">
            <div
              className={cn(
                "h-2 w-2 rounded-full",
                sentimentScore >= 70
                  ? "bg-green-500"
                  : sentimentScore >= 40
                    ? "bg-yellow-500"
                    : "bg-red-500",
              )}
            />
            <span
              className={cn("text-xs font-medium", getSentimentColor(sentimentScore))}
            >
              {sentimentScore >= 70
                ? t("stats.good")
                : sentimentScore >= 40
                  ? t("stats.fair")
                  : t("stats.poor")}
            </span>
          </div>
        </StatCard>

        {/* Review Velocity */}
        <StatCard isLoading={statsLoading}>
          <p className="text-sm font-medium text-muted-foreground">
            {t("stats.reviewVelocity")}
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {velocity.toFixed(1)}
          </p>
          <div className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
            {velocity >= genreAvgVelocity ? (
              <TrendingUp className="h-3 w-3 text-green-600" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-600" />
            )}
            <span>
              {t("stats.perWeek")} &middot;{" "}
              {t("stats.vsGenreAvg", { value: genreAvgVelocity.toFixed(1) })}
            </span>
          </div>
        </StatCard>

        {/* Needs Attention */}
        <StatCard isLoading={statsLoading}>
          <p className="text-sm font-medium text-muted-foreground">
            {t("stats.needsAttention")}
          </p>
          <p
            className={cn(
              "mt-1 text-2xl font-bold",
              needsAttention > 0 ? "text-red-600" : "text-foreground",
            )}
          >
            {needsAttention}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {t("stats.lowRatedReviews")}
          </p>
        </StatCard>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Row 2: Charts                                                       */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Sentiment Trend Chart - 60% (3 of 5 cols) */}
        <div className="lg:col-span-3">
          {trendLoading ? (
            <div className="rounded-lg border bg-card p-6 shadow-sm">
              <Skeleton className="h-5 w-40 mb-4" />
              <Skeleton className="h-[300px] w-full" />
            </div>
          ) : (
            <SentimentTrendChart
              data={sentimentTrend?.data}
              bookFilter={trendBookFilter}
              onBookFilterChange={setTrendBookFilter}
              period={trendPeriod}
              onPeriodChange={setTrendPeriod}
            />
          )}
        </div>

        {/* Rating Distribution - 40% (2 of 5 cols) */}
        <div className="lg:col-span-2">
          {statsLoading ? (
            <div className="rounded-lg border bg-card p-6 shadow-sm">
              <Skeleton className="h-5 w-40 mb-4" />
              <div className="space-y-3">
                {[5, 4, 3, 2, 1].map((i) => (
                  <Skeleton key={i} className="h-5 w-full" />
                ))}
              </div>
            </div>
          ) : (
            <RatingDistribution
              distribution={ratingDistribution}
              total={total}
            />
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Tab Bar                                                             */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex border-b gap-6">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              "pb-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === tab.key
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t(tab.labelKey)}
          </button>
        ))}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Tab Content                                                         */}
      {/* ------------------------------------------------------------------ */}
      <div>{renderTabContent()}</div>
    </div>
  );
}
