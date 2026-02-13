"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslations } from "@/hooks/use-translations";
import type { Review } from "@/modules/reviews/hooks";

/* -------------------------------------------------------------------------- */
/*  Props                                                                     */
/* -------------------------------------------------------------------------- */

interface ReviewFeedProps {
  reviews: Review[];
  total: number;
  hasMore: boolean;
  onLoadMore: () => void;
  onMarkRead: (reviewId: string, read: boolean) => void;
  onFlag: (reviewId: string, flagged: boolean) => void;
  bookFilter: string;
  onBookFilterChange: (id: string) => void;
  ratingFilter: number | null;
  onRatingFilterChange: (r: number | null) => void;
  sentimentFilter: string | null;
  onSentimentFilterChange: (s: string | null) => void;
  sortBy: string;
  onSortChange: (sort: string) => void;
  isLoading?: boolean;
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                   */
/* -------------------------------------------------------------------------- */

function renderStars(rating: number): string {
  const filled = Math.round(rating);
  return (
    Array.from({ length: 5 })
      .map((_, i) => (i < filled ? "\u2605" : "\u2606"))
      .join("")
  );
}

function relativeDate(
  dateStr: string | null,
  t: any,
): string {
  if (!dateStr) return "";
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return t("feed.justNow");
  if (diffHours < 24) return t("feed.hoursAgo", { count: diffHours });
  return t("feed.daysAgo", { count: diffDays });
}

function sentimentColor(sentiment: string | null): string {
  switch (sentiment) {
    case "positive":
      return "text-green-600";
    case "negative":
      return "text-red-600";
    case "neutral":
      return "text-gray-500";
    case "mixed":
      return "text-yellow-600";
    default:
      return "text-gray-400";
  }
}

function sentimentDotColor(sentiment: string | null): string {
  switch (sentiment) {
    case "positive":
      return "bg-green-500";
    case "negative":
      return "bg-red-500";
    case "neutral":
      return "bg-gray-400";
    case "mixed":
      return "bg-yellow-500";
    default:
      return "bg-gray-300";
  }
}

function sentimentLabel(sentiment: string | null): string {
  if (!sentiment) return "Unknown";
  return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
}

const THEME_COLORS = [
  "bg-blue-100 text-blue-800",
  "bg-purple-100 text-purple-800",
  "bg-teal-100 text-teal-800",
  "bg-indigo-100 text-indigo-800",
  "bg-pink-100 text-pink-800",
  "bg-cyan-100 text-cyan-800",
  "bg-emerald-100 text-emerald-800",
  "bg-amber-100 text-amber-800",
];

/* -------------------------------------------------------------------------- */
/*  Skeleton card                                                             */
/* -------------------------------------------------------------------------- */

function ReviewCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-16 ml-auto" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-5 w-28" />
        </div>
        <Skeleton className="h-14 w-full" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-20" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-8 w-36" />
          <Skeleton className="h-8 w-32" />
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/*  Single review card                                                        */
/* -------------------------------------------------------------------------- */

function ReviewFeedCard({
  review,
  t,
  onMarkRead,
  onFlag,
}: {
  review: Review;
  t: any;
  onMarkRead: (reviewId: string, read: boolean) => void;
  onFlag: (reviewId: string, flagged: boolean) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const stars = renderStars(review.star_rating);
  const date = relativeDate(review.review_date, t);
  const scorePct =
    review.sentiment_score != null
      ? `${Math.round(Math.abs(review.sentiment_score) * 100)}%`
      : null;

  const bodyIsTruncatable =
    review.body != null && review.body.length > 200;

  return (
    <Card
      className={
        review.read === false
          ? "border-l-4 border-l-blue-400"
          : undefined
      }
    >
      <CardContent className="p-4 space-y-3">
        {/* Row 1: Stars, title, date */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span
            className="text-yellow-500 text-base tracking-wider"
            aria-label={`${review.star_rating} out of 5 stars`}
          >
            {stars}
          </span>
          {review.title && (
            <span className="font-semibold text-sm text-foreground">
              {review.title}
            </span>
          )}
          {date && (
            <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
              {date}
            </span>
          )}
        </div>

        {/* Row 2: Book name + reviewer + verified badge */}
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          {review.book_title && (
            <span className="font-medium text-foreground">
              {review.book_title}
            </span>
          )}
          {review.reviewer_name && (
            <>
              <span>&middot;</span>
              <span>{review.reviewer_name}</span>
            </>
          )}
          {review.verified_purchase && (
            <Badge
              variant="secondary"
              className="text-[10px] px-1.5 py-0"
            >
              {t("feed.verifiedPurchase")}
            </Badge>
          )}
        </div>

        {/* Row 3: Body text (truncated to 3 lines with expand) */}
        {review.body && (
          <div>
            <p
              className={`text-sm leading-relaxed text-foreground ${
                !expanded ? "line-clamp-3" : ""
              }`}
            >
              {review.body}
            </p>
            {bodyIsTruncatable && (
              <button
                type="button"
                onClick={() => setExpanded((prev) => !prev)}
                className="mt-1 text-xs font-medium text-primary hover:underline"
              >
                {expanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>
        )}

        {/* Row 4: Sentiment indicator */}
        {review.sentiment && (
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${sentimentDotColor(review.sentiment)}`}
            />
            <span
              className={`text-xs font-medium ${sentimentColor(review.sentiment)}`}
            >
              {sentimentLabel(review.sentiment)}
              {scorePct && ` (${scorePct})`}
            </span>
          </div>
        )}

        {/* Row 5: Extracted themes */}
        {review.extracted_themes && review.extracted_themes.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {review.extracted_themes.map((theme, idx) => (
              <span
                key={theme}
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  THEME_COLORS[idx % THEME_COLORS.length]
                }`}
              >
                {theme}
              </span>
            ))}
          </div>
        )}

        {/* Row 6: Actionable suggestion for negative reviews */}
        {review.actionable_suggestion &&
          (review.sentiment === "negative" || review.sentiment === "mixed") && (
            <div className="rounded-md bg-yellow-50 border border-yellow-200 px-3 py-2">
              <p className="text-xs font-medium text-yellow-800">
                {t("feed.actionable")}
              </p>
              <p className="text-xs text-yellow-700 mt-0.5">
                {review.actionable_suggestion}
              </p>
            </div>
          )}

        {/* Row 7: Action buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs"
            onClick={() => onMarkRead(review.id, !review.read)}
          >
            {review.read ? t("feed.markUnread") : t("feed.markRead")}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={`h-7 text-xs ${
              review.flagged
                ? "text-orange-600 hover:text-orange-700"
                : ""
            }`}
            onClick={() => onFlag(review.id, !review.flagged)}
          >
            {review.flagged ? t("feed.unflag") : t("feed.flag")}
          </Button>
          {review.reviewer_profile_url && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              asChild
            >
              <a
                href={review.reviewer_profile_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {t("feed.viewOnAmazon")}
                <span className="ml-1" aria-hidden="true">
                  &#8599;
                </span>
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main component                                                            */
/* -------------------------------------------------------------------------- */

export function ReviewFeed({
  reviews,
  total,
  hasMore,
  onLoadMore,
  onMarkRead,
  onFlag,
  bookFilter,
  onBookFilterChange,
  ratingFilter,
  onRatingFilterChange,
  sentimentFilter,
  onSentimentFilterChange,
  sortBy,
  onSortChange,
  isLoading = false,
}: ReviewFeedProps) {
  const t = useTranslations("reviews");

  /* Showing X-Y of Z */
  const showingFrom = reviews.length > 0 ? 1 : 0;
  const showingTo = reviews.length;

  /* ----- Loading state ----- */
  if (isLoading && reviews.length === 0) {
    return (
      <div className="space-y-4">
        {/* Filter bar skeleton */}
        <div className="flex flex-wrap items-center gap-2">
          <Skeleton className="h-8 w-[140px]" />
          <Skeleton className="h-8 w-[140px]" />
          <Skeleton className="h-8 w-[140px]" />
          <Skeleton className="h-8 w-[140px]" />
        </div>
        {/* Skeleton cards */}
        {Array.from({ length: 5 }).map((_, i) => (
          <ReviewCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  /* ----- Empty state ----- */
  if (!isLoading && reviews.length === 0) {
    return (
      <div className="space-y-4">
        <FilterBar
          t={t}
          bookFilter={bookFilter}
          onBookFilterChange={onBookFilterChange}
          ratingFilter={ratingFilter}
          onRatingFilterChange={onRatingFilterChange}
          sentimentFilter={sentimentFilter}
          onSentimentFilterChange={onSentimentFilterChange}
          sortBy={sortBy}
          onSortChange={onSortChange}
        />
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <p className="text-sm text-muted-foreground text-center">
              {t("feed.noReviews")}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  /* ----- Normal state ----- */
  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <FilterBar
        t={t}
        bookFilter={bookFilter}
        onBookFilterChange={onBookFilterChange}
        ratingFilter={ratingFilter}
        onRatingFilterChange={onRatingFilterChange}
        sentimentFilter={sentimentFilter}
        onSentimentFilterChange={onSentimentFilterChange}
        sortBy={sortBy}
        onSortChange={onSortChange}
      />

      {/* Showing counter */}
      <p className="text-xs text-muted-foreground">
        {t("feed.showing", {
          from: showingFrom,
          to: showingTo,
          total,
        })}
      </p>

      {/* Review cards */}
      <div className="space-y-3">
        {reviews.map((review) => (
          <ReviewFeedCard
            key={review.id}
            review={review}
            t={t}
            onMarkRead={onMarkRead}
            onFlag={onFlag}
          />
        ))}
      </div>

      {/* Loading more indicator */}
      {isLoading && (
        <div className="space-y-3">
          <ReviewCardSkeleton />
          <ReviewCardSkeleton />
        </div>
      )}

      {/* Load More button */}
      {hasMore && (
        <div className="flex justify-center pt-2">
          <Button
            variant="outline"
            onClick={onLoadMore}
            disabled={isLoading}
          >
            {isLoading ? "..." : t("feed.loadMore")}
          </Button>
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Filter bar                                                                */
/* -------------------------------------------------------------------------- */

function FilterBar({
  t,
  bookFilter,
  onBookFilterChange,
  ratingFilter,
  onRatingFilterChange,
  sentimentFilter,
  onSentimentFilterChange,
  sortBy,
  onSortChange,
}: {
  t: any;
  bookFilter: string;
  onBookFilterChange: (id: string) => void;
  ratingFilter: number | null;
  onRatingFilterChange: (r: number | null) => void;
  sentimentFilter: string | null;
  onSentimentFilterChange: (s: string | null) => void;
  sortBy: string;
  onSortChange: (sort: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Book filter */}
      <Select value={bookFilter} onValueChange={onBookFilterChange}>
        <SelectTrigger className="h-8 w-[160px] text-xs">
          <SelectValue placeholder={t("feed.filterBook")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t("feed.filterBook")}</SelectItem>
        </SelectContent>
      </Select>

      {/* Rating filter */}
      <Select
        value={ratingFilter != null ? String(ratingFilter) : "all"}
        onValueChange={(v) =>
          onRatingFilterChange(v === "all" ? null : Number(v))
        }
      >
        <SelectTrigger className="h-8 w-[140px] text-xs">
          <SelectValue placeholder={t("feed.filterRating")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t("feed.filterRating")}</SelectItem>
          {[5, 4, 3, 2, 1].map((star) => (
            <SelectItem key={star} value={String(star)}>
              {star} {star === 1 ? "Star" : "Stars"}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Sentiment filter */}
      <Select
        value={sentimentFilter ?? "all"}
        onValueChange={(v) =>
          onSentimentFilterChange(v === "all" ? null : v)
        }
      >
        <SelectTrigger className="h-8 w-[160px] text-xs">
          <SelectValue placeholder={t("feed.filterSentiment")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t("feed.filterSentiment")}</SelectItem>
          <SelectItem value="positive">Positive</SelectItem>
          <SelectItem value="negative">Negative</SelectItem>
          <SelectItem value="neutral">Neutral</SelectItem>
        </SelectContent>
      </Select>

      {/* Sort */}
      <Select value={sortBy} onValueChange={onSortChange}>
        <SelectTrigger className="h-8 w-[150px] text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="newest">{t("feed.sortNewest")}</SelectItem>
          <SelectItem value="oldest">{t("feed.sortOldest")}</SelectItem>
          <SelectItem value="highest">{t("feed.sortRatingHigh")}</SelectItem>
          <SelectItem value="lowest">{t("feed.sortRatingLow")}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
