"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useMobileCheck } from "../hooks";
import type { MobileCheckResult, Recommendation } from "../hooks";

interface MobilePreviewProps {
  className?: string;
}

function MobileFrame({
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
  return (
    <div className="mx-auto w-[280px] rounded-[24px] border-4 border-gray-800 bg-white p-3 shadow-lg">
      {/* Status bar */}
      <div className="flex justify-between text-[10px] text-gray-500 mb-2 px-1">
        <span>9:41</span>
        <span>Amazon</span>
      </div>

      {/* Cover placeholder */}
      <div
        role="img"
        aria-label="Book cover preview placeholder"
        className="mx-auto w-32 h-48 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-400 mb-3"
      >
        Book Cover
      </div>

      {/* Title */}
      <h4 className="text-xs font-bold text-gray-900 mb-0.5 line-clamp-2">
        {title}
        {isTruncated && <span className="text-gray-400">...</span>}
      </h4>

      {/* Author */}
      <p className="text-[10px] text-blue-600 mb-2">by {author}</p>

      {/* Price */}
      {price !== undefined && (
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-bold text-gray-900">${price.toFixed(2)}</span>
          <span className="text-[10px] text-gray-500">Kindle Edition</span>
        </div>
      )}

      {/* Buy button */}
      <button className="w-full bg-yellow-400 rounded-full py-1.5 text-xs font-medium text-gray-900 mb-2">
        Buy now with 1-Click
      </button>

      {/* Blurb (above fold) */}
      <div className="text-[10px] text-gray-700 leading-relaxed">
        {blurbAboveFold}
        {blurbAboveFold.length > 150 && (
          <span className="text-blue-600 ml-1">Read more</span>
        )}
      </div>
    </div>
  );
}

function MobileRecommendations({ recommendations }: { recommendations: Recommendation[] }) {
  if (recommendations.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold">Mobile Optimization Tips</h4>
      {recommendations.map((rec, i) => (
        <div
          key={i}
          className={cn(
            "rounded-md border-l-4 p-3 text-xs",
            rec.severity === "critical"
              ? "border-red-400 bg-red-50"
              : rec.severity === "warning"
                ? "border-yellow-400 bg-yellow-50"
                : "border-blue-400 bg-blue-50"
          )}
        >
          <p className="font-medium">{rec.message}</p>
          <p className="mt-1 text-gray-600">{rec.suggestion}</p>
        </div>
      ))}
    </div>
  );
}

export function MobilePreview({ className }: MobilePreviewProps) {
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [blurb, setBlurb] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [price, setPrice] = useState<string>("");

  const mobileMutation = useMobileCheck();

  const handleCheck = () => {
    if (!title || !blurb || !authorName) return;
    mobileMutation.mutate({
      title,
      subtitle: subtitle || undefined,
      blurb,
      author_name: authorName,
      price: price ? parseFloat(price) : undefined,
    });
  };

  const result = mobileMutation.data;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Input form */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Mobile Conversion Checker</h3>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="mobile-preview-title" className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                id="mobile-preview-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Book title"
              />
            </div>
            <div>
              <label htmlFor="mobile-preview-author" className="block text-sm font-medium text-gray-700 mb-1">Author</label>
              <input
                id="mobile-preview-author"
                type="text"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Author name"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="mobile-preview-subtitle" className="block text-sm font-medium text-gray-700 mb-1">
                Subtitle (optional)
              </label>
              <input
                id="mobile-preview-subtitle"
                type="text"
                value={subtitle}
                onChange={(e) => setSubtitle(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Subtitle"
              />
            </div>
            <div>
              <label htmlFor="mobile-preview-price" className="block text-sm font-medium text-gray-700 mb-1">
                Price (optional)
              </label>
              <input
                id="mobile-preview-price"
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="3.99"
              />
            </div>
          </div>
          <div>
            <label htmlFor="mobile-preview-blurb" className="block text-sm font-medium text-gray-700 mb-1">Blurb</label>
            <textarea
              id="mobile-preview-blurb"
              value={blurb}
              onChange={(e) => setBlurb(e.target.value)}
              rows={4}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Book description / blurb"
            />
          </div>
          <button
            onClick={handleCheck}
            disabled={!title || !blurb || !authorName || mobileMutation.isPending}
            className={cn(
              "rounded-md px-4 py-2 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2",
              !title || !blurb || !authorName
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-700"
            )}
          >
            {mobileMutation.isPending ? "Checking..." : "Check Mobile Display"}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Mobile preview */}
          <div className="flex justify-center">
            <MobileFrame
              title={result.title_display.visible_text}
              author={authorName}
              blurbAboveFold={result.blurb_above_fold}
              price={price ? parseFloat(price) : undefined}
              isTruncated={result.title_display.is_truncated}
            />
          </div>

          {/* Scores and recommendations */}
          <div className="space-y-4">
            <div className="rounded-lg border bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold">Mobile Score</h4>
                <div
                  className={cn(
                    "text-xl font-bold px-3 py-1 rounded-full",
                    result.overall_score >= 80
                      ? "bg-green-100 text-green-700"
                      : result.overall_score >= 60
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-red-100 text-red-700"
                  )}
                >
                  {Math.round(result.overall_score)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Title truncated:</span>{" "}
                  <span className="font-medium">
                    {result.title_display.is_truncated ? "Yes" : "No"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Blurb fold:</span>{" "}
                  <span className="font-medium">{result.blurb_fold_point} chars</span>
                </div>
                <div>
                  <span className="text-gray-500">Above fold words:</span>{" "}
                  <span className="font-medium">{result.blurb_above_fold_word_count}</span>
                </div>
                <div>
                  <span className="text-gray-500">Price visibility:</span>{" "}
                  <span className="font-medium">{result.price_visibility}</span>
                </div>
              </div>
            </div>

            <MobileRecommendations recommendations={result.recommendations} />

            {/* Device breakdown */}
            {Object.keys(result.device_previews).length > 0 && (
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <h4 className="text-sm font-semibold mb-2">Device Breakdown</h4>
                <div className="space-y-1">
                  {Object.entries(result.device_previews).map(([id, preview]) => (
                    <div key={id} className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">
                        {preview.device_name as string}
                      </span>
                      <span
                        className={cn(
                          "font-medium",
                          preview.title_truncated ? "text-red-600" : "text-green-600"
                        )}
                      >
                        {preview.title_truncated ? "Title truncated" : "OK"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {mobileMutation.isError && (
        <div role="alert" className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          Failed to check mobile display. Please try again.
        </div>
      )}
    </div>
  );
}
