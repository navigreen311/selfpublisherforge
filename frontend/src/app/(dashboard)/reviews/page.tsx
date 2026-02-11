"use client";

import { useState } from "react";
import { useAlerts, useReviews } from "@/modules/reviews/hooks";
import { AlertsPanel } from "@/modules/reviews/components/AlertsPanel";
import { ReviewList } from "@/modules/reviews/components/ReviewList";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SentimentLabel } from "@/modules/reviews/types";
import Link from "next/link";

export default function ReviewsPage() {
  const [selectedSentiment, setSelectedSentiment] = useState<SentimentLabel | "all">("all");

  const {
    data: alertsData,
    isLoading: alertsLoading,
  } = useAlerts({ is_acknowledged: false });

  const {
    data: reviewsData,
    isLoading: reviewsLoading,
    error: reviewsError,
  } = useReviews({
    sentiment: selectedSentiment === "all" ? undefined : selectedSentiment,
    limit: 20,
  });

  if (reviewsError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Review Intelligence</h1>
        <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
          <p className="text-red-800">Failed to load review data. Please try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Review Intelligence</h1>
        <div className="flex gap-2">
          <Link
            href="/reviews/analytics"
            className="px-4 py-2 text-sm font-medium text-foreground bg-card border rounded-md hover:bg-muted"
          >
            Analytics
          </Link>
        </div>
      </div>

      {/* Overview KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Total Reviews</p>
          {reviewsLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {reviewsData?.total_count?.toLocaleString() || "0"}
              </p>
              <p className="mt-1 text-xs text-gray-500">Across all books</p>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Active Alerts</p>
          {alertsLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {alertsData?.items.length || "0"}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {alertsData?.items.filter((a) => a.severity === "critical" || a.severity === "high")
                  .length || 0}{" "}
                critical/high
              </p>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Positive Reviews</p>
          {reviewsLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-green-600">
                {reviewsData?.items.filter((r) => r.sentiment === SentimentLabel.POSITIVE).length ||
                  "0"}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {reviewsData?.total_count
                  ? (
                      (reviewsData.items.filter((r) => r.sentiment === SentimentLabel.POSITIVE)
                        .length /
                        reviewsData.total_count) *
                      100
                    ).toFixed(0)
                  : "0"}
                % of total
              </p>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Negative Reviews</p>
          {reviewsLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-red-600">
                {reviewsData?.items.filter((r) => r.sentiment === SentimentLabel.NEGATIVE).length ||
                  "0"}
              </p>
              <p className="mt-1 text-xs text-gray-500">Requires attention</p>
            </>
          )}
        </div>
      </div>

      {/* Alerts Panel */}
      {!alertsLoading && alertsData && alertsData.items.length > 0 && (
        <AlertsPanel alerts={alertsData.items} />
      )}

      {/* Quick Book Links */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Review by Book</h3>
        <p className="text-sm text-gray-500 mb-4">
          Select a book to view detailed review analytics, sentiment trends, and alerts.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {/* In production, this would be a list of books from an API */}
          <Link
            href="/reviews/book-id-1"
            className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
          >
            <p className="font-medium text-gray-900">Book Title 1</p>
            <p className="text-xs text-gray-500 mt-1">Click to view details</p>
          </Link>
          <Link
            href="/reviews/book-id-2"
            className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
          >
            <p className="font-medium text-gray-900">Book Title 2</p>
            <p className="text-xs text-gray-500 mt-1">Click to view details</p>
          </Link>
        </div>
      </div>

      {/* Recent Reviews */}
      {!reviewsLoading && reviewsData && (
        <ReviewList
          reviews={reviewsData.items}
          hasMore={reviewsData.has_more}
          nextCursor={reviewsData.next_cursor}
          onLoadMore={() => {
            console.log("Load more reviews");
          }}
          onSentimentFilter={setSelectedSentiment}
          selectedSentiment={selectedSentiment}
        />
      )}

      {reviewsLoading && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}
    </div>
  );
}
