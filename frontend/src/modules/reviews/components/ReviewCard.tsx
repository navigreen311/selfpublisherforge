"use client";

import { Badge } from "@/components/ui/badge";
import { SentimentLabel, type Review } from "../types";

interface ReviewCardProps {
  review: Review;
}

export function ReviewCard({ review }: ReviewCardProps) {
  const sentimentColor = getSentimentColor(review.sentiment);
  const sentimentText = getSentimentText(review.sentiment);

  const formattedDate = review.review_date
    ? new Date(review.review_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "Unknown date";

  const renderStars = (rating: number) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    return (
      <div className="flex items-center gap-0.5" aria-label={`${rating} out of 5 stars`}>
        {[...Array(fullStars)].map((_, i) => (
          <span key={`full-${i}`} className="text-yellow-500">
            ★
          </span>
        ))}
        {hasHalfStar && <span className="text-yellow-500">☆</span>}
        {[...Array(emptyStars)].map((_, i) => (
          <span key={`empty-${i}`} className="text-gray-300">
            ★
          </span>
        ))}
        <span className="ml-1 text-sm text-gray-600">{rating.toFixed(1)}</span>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {renderStars(review.star_rating)}
            {review.verified_purchase && (
              <Badge variant="secondary" className="text-xs">
                Verified
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="font-medium text-gray-700">
              {review.reviewer_name || "Anonymous"}
            </span>
            <span>•</span>
            <span>{formattedDate}</span>
            <span>•</span>
            <span className="capitalize">{review.source.replace("_", " ")}</span>
          </div>
        </div>
        {review.sentiment && (
          <Badge className={sentimentColor}>{sentimentText}</Badge>
        )}
      </div>

      {review.title && (
        <h4 className="font-semibold text-gray-900 mb-1">{review.title}</h4>
      )}

      {review.body && (
        <p className="text-gray-700 text-sm leading-relaxed line-clamp-3">{review.body}</p>
      )}

      {review.helpful_count > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          {review.helpful_count} {review.helpful_count === 1 ? "person" : "people"} found this
          helpful
        </div>
      )}
    </div>
  );
}

function getSentimentColor(sentiment: SentimentLabel | null): string {
  switch (sentiment) {
    case SentimentLabel.POSITIVE:
      return "bg-green-100 text-green-800 border-green-300";
    case SentimentLabel.NEGATIVE:
      return "bg-red-100 text-red-800 border-red-300";
    case SentimentLabel.NEUTRAL:
      return "bg-gray-100 text-gray-800 border-gray-300";
    case SentimentLabel.MIXED:
      return "bg-yellow-100 text-yellow-800 border-yellow-300";
    default:
      return "bg-gray-100 text-gray-600 border-gray-300";
  }
}

function getSentimentText(sentiment: SentimentLabel | null): string {
  if (!sentiment) return "Unknown";
  return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
}
