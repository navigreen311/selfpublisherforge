"use client";

import { useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { SentimentChart } from "./SentimentChart";
import { VelocityTracker } from "./VelocityTracker";
import { AlertsPanel } from "./AlertsPanel";
import { ReviewList } from "./ReviewList";
import {
  useBookReviews,
  useSentimentBreakdown,
  useVelocity,
  useAlerts,
  useAcknowledgeAlert,
} from "../hooks";
import { VelocityPeriod, SentimentLabel } from "../types";

interface ReviewDashboardProps {
  bookId: string;
  bookTitle?: string;
}

export function ReviewDashboard({ bookId, bookTitle }: ReviewDashboardProps) {
  const [selectedSentiment, setSelectedSentiment] = useState<SentimentLabel | "all">("all");
  const [velocityPeriod, setVelocityPeriod] = useState<VelocityPeriod>(VelocityPeriod.WEEKLY);

  const {
    data: reviewsData,
    isLoading: reviewsLoading,
    error: reviewsError,
  } = useBookReviews(bookId, {
    sentiment: selectedSentiment === "all" ? undefined : selectedSentiment,
    limit: 20,
  });

  const {
    data: sentimentData,
    isLoading: sentimentLoading,
  } = useSentimentBreakdown(bookId);

  const {
    data: velocityData,
    isLoading: velocityLoading,
  } = useVelocity(bookId, velocityPeriod);

  const {
    data: alertsData,
    isLoading: alertsLoading,
  } = useAlerts({ book_id: bookId, is_acknowledged: false });

  const acknowledgeAlert = useAcknowledgeAlert();

  const handleAcknowledgeAlert = (alertId: string) => {
    acknowledgeAlert.mutate({ alertId });
  };

  if (reviewsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
        <p className="text-red-800">Failed to load review data. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Book Title */}
      {bookTitle && (
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">{bookTitle}</h2>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Average Sentiment</p>
          {sentimentLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {sentimentData?.avg_sentiment_score.toFixed(2) || "N/A"}
              </p>
              <p className="mt-1 text-xs text-gray-500">-1 (negative) to +1 (positive)</p>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Total Reviews</p>
          {sentimentLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {sentimentData?.total_count.toLocaleString() || "0"}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {sentimentData?.positive_pct.toFixed(0)}% positive
              </p>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-600">Review Velocity</p>
          {velocityLoading ? (
            <Skeleton className="h-8 w-24 mt-2" />
          ) : (
            <>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {velocityData?.current_rate.toFixed(1) || "0"}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                per {velocityData?.period || "week"}
              </p>
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
      </div>

      {/* Alerts Panel */}
      {!alertsLoading && alertsData && (
        <AlertsPanel
          alerts={alertsData.items}
          onAcknowledge={handleAcknowledgeAlert}
          isAcknowledging={acknowledgeAlert.isPending}
        />
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Chart */}
        {!velocityLoading && velocityData && (
          <SentimentChart data={velocityData.data_points} />
        )}

        {/* Velocity Tracker */}
        {!velocityLoading && velocityData && (
          <div>
            <div className="mb-2 flex justify-end">
              <Select
                value={velocityPeriod}
                onValueChange={(v) => setVelocityPeriod(v as VelocityPeriod)}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={VelocityPeriod.DAILY}>Daily</SelectItem>
                  <SelectItem value={VelocityPeriod.WEEKLY}>Weekly</SelectItem>
                  <SelectItem value={VelocityPeriod.MONTHLY}>Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <VelocityTracker velocityReport={velocityData} />
          </div>
        )}
      </div>

      {/* Reviews List */}
      {!reviewsLoading && reviewsData && (
        <ReviewList
          reviews={reviewsData.items}
          hasMore={reviewsData.has_more}
          nextCursor={reviewsData.next_cursor}
          onLoadMore={() => {
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
