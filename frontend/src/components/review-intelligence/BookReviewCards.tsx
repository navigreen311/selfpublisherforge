"use client";

import { useTranslations } from "@/hooks/use-translations";
import type { BookReviewSummary } from "@/modules/reviews/hooks";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BookOpen,
  Star,
  TrendingUp,
  CalendarDays,
  Eye,
  Brain,
  MessageSquarePlus,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function getSentimentColor(score: number): string {
  if (score >= 70) return "text-green-600";
  if (score >= 40) return "text-yellow-600";
  return "text-red-600";
}

function getSentimentBg(score: number): string {
  if (score >= 70) return "bg-green-100";
  if (score >= 40) return "bg-yellow-100";
  return "bg-red-100";
}

function renderStars(rating: number) {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className="flex items-center gap-0.5" aria-label={`${rating} out of 5 stars`}>
      {[...Array(fullStars)].map((_, i) => (
        <span key={`full-${i}`} className="text-yellow-500">
          <Star className="h-3.5 w-3.5 fill-current" />
        </span>
      ))}
      {hasHalfStar && (
        <span className="text-yellow-500">
          <Star className="h-3.5 w-3.5" />
        </span>
      )}
      {[...Array(emptyStars)].map((_, i) => (
        <span key={`empty-${i}`} className="text-gray-300">
          <Star className="h-3.5 w-3.5" />
        </span>
      ))}
      <span className="ml-1 text-sm text-muted-foreground">{rating.toFixed(1)}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton Card
// ---------------------------------------------------------------------------

function BookReviewCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4 space-y-4">
        {/* Header: cover + title */}
        <div className="flex gap-3">
          <Skeleton className="h-20 w-14 rounded flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        </div>
        {/* Stats row */}
        <div className="flex gap-4">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
        {/* Themes */}
        <div className="flex gap-2">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-14 rounded-full" />
        </div>
        {/* Sentiment bar */}
        <Skeleton className="h-2.5 w-full rounded-full" />
        {/* Actions */}
        <div className="flex gap-2">
          <Skeleton className="h-9 flex-1" />
          <Skeleton className="h-9 flex-1" />
          <Skeleton className="h-9 flex-1" />
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Single Book Review Card
// ---------------------------------------------------------------------------

function BookReviewCard({
  book,
  onViewReviews,
  onRunAnalysis,
  onAcquisition,
  t,
}: {
  book: BookReviewSummary;
  onViewReviews: (bookId: string) => void;
  onRunAnalysis: (bookId: string) => void;
  onAcquisition: (bookId: string) => void;
  t: ReturnType<typeof useTranslations>;
}) {
  const negativePct = 100 - book.positive_pct;

  return (
    <Card className="flex flex-col overflow-hidden">
      <CardContent className="p-4 space-y-3 flex-1">
        {/* Header: Cover + Title + Rating + Count + Date */}
        <div className="flex gap-3">
          {/* Cover thumbnail placeholder */}
          {book.cover_url ? (
            <img
              src={book.cover_url}
              alt={book.title}
              className="h-20 w-14 flex-shrink-0 rounded object-cover"
            />
          ) : (
            <div className="flex h-20 w-14 flex-shrink-0 items-center justify-center rounded bg-primary/10">
              <BookOpen className="h-6 w-6 text-primary" />
            </div>
          )}

          <div className="flex flex-1 flex-col gap-1 min-w-0">
            <h3 className="text-sm font-semibold leading-snug line-clamp-2">
              {book.title}
            </h3>
            <div className="flex items-center gap-1.5">
              {renderStars(book.rating)}
              <span className="text-xs text-muted-foreground">
                ({book.review_count.toLocaleString()})
              </span>
            </div>
            {book.publish_date && (
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <CalendarDays className="h-3 w-3" />
                {formatDate(book.publish_date)}
              </p>
            )}
          </div>
        </div>

        {/* Stats Row: Sentiment Score + Velocity + This Month */}
        <div className="flex items-center gap-3 text-xs">
          {/* Sentiment Score */}
          <div
            className={`flex items-center gap-1.5 rounded-md px-2 py-1 font-medium ${getSentimentBg(book.sentiment_score)} ${getSentimentColor(book.sentiment_score)}`}
          >
            <span>{t("stats.sentimentScore")}</span>
            <span className="font-bold">{book.sentiment_score}</span>
          </div>

          {/* Review Velocity */}
          <div className="flex items-center gap-1 text-muted-foreground">
            <TrendingUp className="h-3.5 w-3.5" />
            <span>
              {book.velocity.toFixed(1)} {t("stats.perWeek")}
            </span>
          </div>

          {/* This Month */}
          <div className="flex items-center gap-1 text-muted-foreground">
            <CalendarDays className="h-3.5 w-3.5" />
            <span>
              {book.this_month} {t("books.thisMonthLabel")}
            </span>
          </div>
        </div>

        {/* Theme Tags */}
        <div className="space-y-1.5">
          {/* Positive Themes */}
          {book.positive_themes.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <ThumbsUp className="h-3 w-3 text-green-600 flex-shrink-0" />
              {book.positive_themes.slice(0, 2).map((theme) => (
                <span
                  key={theme}
                  className="inline-flex items-center rounded-full bg-green-50 px-2 py-0.5 text-[11px] font-medium text-green-700 border border-green-200"
                >
                  {theme}
                </span>
              ))}
            </div>
          )}

          {/* Negative Themes */}
          {book.negative_themes.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <ThumbsDown className="h-3 w-3 text-red-600 flex-shrink-0" />
              {book.negative_themes.slice(0, 2).map((theme) => (
                <span
                  key={theme}
                  className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-700 border border-red-200"
                >
                  {theme}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Sentiment Bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>{t("books.positive")} {book.positive_pct}%</span>
            <span>{t("books.negativeThemes")} {negativePct}%</span>
          </div>
          <div className="flex h-2 w-full overflow-hidden rounded-full bg-red-200">
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${book.positive_pct}%` }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 pt-1">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-xs"
            onClick={() => onViewReviews(book.book_id)}
          >
            <Eye className="mr-1 h-3.5 w-3.5" />
            {t("books.viewAllReviews")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-xs"
            onClick={() => onRunAnalysis(book.book_id)}
          >
            <Brain className="mr-1 h-3.5 w-3.5" />
            {t("books.runAIAnalysis")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-xs"
            onClick={() => onAcquisition(book.book_id)}
          >
            <MessageSquarePlus className="mr-1 h-3.5 w-3.5" />
            {t("books.reviewAcquisition")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface BookReviewCardsProps {
  books: BookReviewSummary[];
  onViewReviews: (bookId: string) => void;
  onRunAnalysis: (bookId: string) => void;
  onAcquisition: (bookId: string) => void;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function BookReviewCards({
  books,
  onViewReviews,
  onRunAnalysis,
  onAcquisition,
  isLoading,
}: BookReviewCardsProps) {
  const t = useTranslations("reviews");

  // Loading state: 3 skeleton cards
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <BookReviewCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Empty state
  if (books.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 px-6">
        <BookOpen className="h-10 w-10 text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground text-center max-w-md">
          {t("books.noBooks")}
        </p>
      </div>
    );
  }

  // Book cards grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {books.map((book) => (
        <BookReviewCard
          key={book.book_id}
          book={book}
          onViewReviews={onViewReviews}
          onRunAnalysis={onRunAnalysis}
          onAcquisition={onAcquisition}
          t={t}
        />
      ))}
    </div>
  );
}
