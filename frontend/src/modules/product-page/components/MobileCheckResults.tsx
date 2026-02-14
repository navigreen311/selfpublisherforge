"use client";

import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Star,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MobileCheckResult, Recommendation } from "../types";

interface MobileCheckResultsProps {
  result: MobileCheckResult;
  title: string;
  author: string;
  price?: number;
  className?: string;
}

function PhoneFrame({
  title,
  author,
  blurbAboveFold,
  price,
  isTruncated,
}: {
  title: string;
  author: string;
  blurbAboveFold: string;
  price?: number;
  isTruncated: boolean;
}) {
  const displayTitle =
    title.length > 36 ? title.slice(0, 36) + "..." : title;

  return (
    <div className="mx-auto w-[280px] rounded-[28px] border-[3px] border-gray-800 bg-white p-3 shadow-xl">
      {/* Status bar */}
      <div className="flex justify-between text-[10px] text-gray-400 mb-2 px-1">
        <span>9:41</span>
        <span className="font-medium">amazon.com</span>
        <span>100%</span>
      </div>

      {/* Cover placeholder */}
      <div
        className="mx-auto w-28 h-40 bg-gradient-to-br from-gray-200 to-gray-300 rounded flex items-center justify-center text-[10px] text-gray-400 mb-3"
      >
        Book Cover
      </div>

      {/* Title */}
      <h4 className="text-xs font-bold text-gray-900 mb-0.5 leading-tight">
        {isTruncated ? displayTitle : title}
      </h4>

      {/* Author */}
      <p className="text-[10px] text-blue-600 mb-1.5">by {author}</p>

      {/* Rating placeholder */}
      <div className="flex items-center gap-1 mb-1.5">
        <div className="flex">
          {[1, 2, 3, 4].map((i) => (
            <Star
              key={i}
              className="h-2.5 w-2.5 fill-yellow-400 text-yellow-400"
            />
          ))}
          <Star className="h-2.5 w-2.5 fill-yellow-400/50 text-yellow-400" />
        </div>
        <span className="text-[9px] text-blue-600">1,234 ratings</span>
      </div>

      {/* Price */}
      {price !== undefined && (
        <div className="flex items-center gap-1.5 mb-2">
          <span className="text-sm font-bold text-gray-900">
            ${price.toFixed(2)}
          </span>
          <span className="text-[9px] text-gray-500">Kindle Edition</span>
        </div>
      )}

      {/* Buy button */}
      <button className="w-full bg-yellow-400 rounded-full py-1 text-[10px] font-medium text-gray-900 mb-2 shadow-sm">
        Buy now with 1-Click
      </button>

      {/* Blurb above fold */}
      <div className="text-[9px] text-gray-700 leading-relaxed line-clamp-3">
        {blurbAboveFold}
      </div>
      {blurbAboveFold.length > 0 && (
        <span className="text-[9px] text-blue-600 font-medium">Read more</span>
      )}
    </div>
  );
}

function CheckItem({
  pass,
  severity,
  label,
  detail,
}: {
  pass: boolean;
  severity?: "critical" | "warning" | "info";
  label: string;
  detail?: string;
}) {
  const Icon = pass ? CheckCircle2 : severity === "critical" ? XCircle : AlertTriangle;
  const iconColor = pass
    ? "text-green-600"
    : severity === "critical"
      ? "text-red-600"
      : "text-yellow-600";

  return (
    <div className="flex items-start gap-2 py-1">
      <Icon className={cn("h-4 w-4 shrink-0 mt-0.5", iconColor)} />
      <div>
        <p className="text-sm font-medium">{label}</p>
        {detail && <p className="text-xs text-muted-foreground">{detail}</p>}
      </div>
    </div>
  );
}

function SuggestionItem({ rec }: { rec: Recommendation }) {
  const severityStyles = {
    critical: "border-l-red-500 bg-red-50",
    warning: "border-l-yellow-500 bg-yellow-50",
    info: "border-l-blue-500 bg-blue-50",
  };

  return (
    <div
      className={cn(
        "border-l-4 rounded-r-md p-3",
        severityStyles[rec.severity]
      )}
    >
      <p className="text-sm font-medium">{rec.message}</p>
      <p className="text-xs text-muted-foreground mt-1">{rec.suggestion}</p>
    </div>
  );
}

export function MobileCheckResults({
  result,
  title,
  author,
  price,
  className,
}: MobileCheckResultsProps) {
  const scoreColor =
    result.overall_score >= 80
      ? "bg-green-100 text-green-700 border-green-300"
      : result.overall_score >= 60
        ? "bg-yellow-100 text-yellow-700 border-yellow-300"
        : "bg-red-100 text-red-700 border-red-300";

  return (
    <div className={cn("grid gap-6 lg:grid-cols-2", className)}>
      {/* Left: Phone mockup */}
      <div className="flex justify-center items-start pt-4">
        <PhoneFrame
          title={result.title_display.visible_text}
          author={author}
          blurbAboveFold={result.blurb_above_fold}
          price={price}
          isTruncated={result.title_display.is_truncated}
        />
      </div>

      {/* Right: Analysis panel */}
      <div className="space-y-4">
        {/* Mobile score */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Mobile Score</CardTitle>
              <div
                className={cn(
                  "text-2xl font-bold px-4 py-1 rounded-full border",
                  scoreColor
                )}
              >
                {Math.round(result.overall_score)}/100
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Checklist */}
            <div className="space-y-1 divide-y">
              <CheckItem
                pass={!result.title_display.is_truncated}
                severity="warning"
                label="Title visibility"
                detail={
                  result.title_display.is_truncated
                    ? `Truncated at ${result.title_display.visible_length} of ${result.title_display.original_length} chars`
                    : "Full title visible on mobile"
                }
              />
              <CheckItem
                pass={result.blurb_above_fold_word_count >= 30}
                severity="warning"
                label="Blurb above fold"
                detail={`${result.blurb_above_fold_word_count} words visible before "Read more"`}
              />
              <CheckItem
                pass={result.cover_aspect_ratio_ok}
                severity="critical"
                label="Cover aspect ratio"
                detail={
                  result.cover_aspect_ratio_ok
                    ? "Cover displays correctly on mobile"
                    : "Cover may appear distorted"
                }
              />
              <CheckItem
                pass={result.cover_readable_at_thumbnail}
                severity="warning"
                label="Cover thumbnail readability"
                detail={
                  result.cover_readable_at_thumbnail
                    ? "Title readable at thumbnail size"
                    : "Title may be hard to read at small sizes"
                }
              />
              <CheckItem
                pass={result.price_visibility === "good" || result.price_visibility === "visible"}
                severity="info"
                label="Price visibility"
                detail={`Price visibility: ${result.price_visibility}`}
              />
              <CheckItem
                pass={result.buy_button_proximity === "good" || result.buy_button_proximity === "close"}
                severity="info"
                label="Buy button proximity"
                detail={`Buy button: ${result.buy_button_proximity}`}
              />
            </div>
          </CardContent>
        </Card>

        {/* Suggestions */}
        {result.recommendations.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Suggestions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {result.recommendations.map((rec, i) => (
                <SuggestionItem key={i} rec={rec} />
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
