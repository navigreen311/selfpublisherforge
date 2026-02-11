"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ReviewCard } from "./ReviewCard";
import { SentimentLabel, type Review } from "../types";

interface ReviewListProps {
  reviews: Review[];
  hasMore: boolean;
  nextCursor: string | null;
  onLoadMore: () => void;
  isLoading?: boolean;
  onSentimentFilter?: (sentiment: SentimentLabel | "all") => void;
  selectedSentiment?: SentimentLabel | "all";
}

export function ReviewList({
  reviews,
  hasMore,
  nextCursor,
  onLoadMore,
  isLoading = false,
  onSentimentFilter,
  selectedSentiment = "all",
}: ReviewListProps) {
  const [sortBy, setSortBy] = useState<"date" | "rating">("date");

  const handleSentimentChange = (value: string) => {
    if (onSentimentFilter) {
      onSentimentFilter(value as SentimentLabel | "all");
    }
  };

  const sortedReviews = [...reviews].sort((a, b) => {
    if (sortBy === "date") {
      const dateA = a.review_date ? new Date(a.review_date).getTime() : 0;
      const dateB = b.review_date ? new Date(b.review_date).getTime() : 0;
      return dateB - dateA;
    } else {
      return b.star_rating - a.star_rating;
    }
  });

  if (reviews.length === 0 && !isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
        <p className="text-gray-500 text-center">No reviews found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Reviews ({reviews.length})
        </h3>
        <div className="flex gap-2">
          {onSentimentFilter && (
            <Select value={selectedSentiment} onValueChange={handleSentimentChange}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Filter sentiment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sentiment</SelectItem>
                <SelectItem value={SentimentLabel.POSITIVE}>Positive</SelectItem>
                <SelectItem value={SentimentLabel.NEUTRAL}>Neutral</SelectItem>
                <SelectItem value={SentimentLabel.NEGATIVE}>Negative</SelectItem>
                <SelectItem value={SentimentLabel.MIXED}>Mixed</SelectItem>
              </SelectContent>
            </Select>
          )}
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as "date" | "rating")}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="date">Sort by Date</SelectItem>
              <SelectItem value="rating">Sort by Rating</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-3">
        {sortedReviews.map((review) => (
          <ReviewCard key={review.id} review={review} />
        ))}
      </div>

      {hasMore && nextCursor && (
        <div className="flex justify-center pt-4">
          <Button
            onClick={onLoadMore}
            disabled={isLoading}
            variant="outline"
          >
            {isLoading ? "Loading..." : "Load More Reviews"}
          </Button>
        </div>
      )}
    </div>
  );
}
