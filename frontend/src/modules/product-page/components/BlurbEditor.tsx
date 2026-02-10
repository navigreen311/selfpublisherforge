"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useGenerateBlurb } from "../hooks";
import type { BlurbVariant } from "../hooks";

interface BlurbEditorProps {
  initialBlurb?: string;
  className?: string;
}

const GENRES = [
  { value: "romance", label: "Romance" },
  { value: "thriller", label: "Thriller" },
  { value: "mystery", label: "Mystery" },
  { value: "fantasy", label: "Fantasy" },
  { value: "science_fiction", label: "Sci-Fi" },
  { value: "literary_fiction", label: "Literary Fiction" },
  { value: "non_fiction", label: "Non-Fiction" },
  { value: "self_help", label: "Self-Help" },
  { value: "memoir", label: "Memoir" },
  { value: "horror", label: "Horror" },
  { value: "young_adult", label: "Young Adult" },
  { value: "children", label: "Children" },
  { value: "historical_fiction", label: "Historical Fiction" },
  { value: "other", label: "Other" },
];

function VariantCard({
  variant,
  onSelect,
}: {
  variant: BlurbVariant;
  onSelect: (content: string) => void;
}) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded">
            {variant.style.replace("_", " ")}
          </span>
          <span className="text-xs text-gray-500">{variant.hook_type.replace("_", " ")}</span>
        </div>
        <div
          className={cn(
            "text-sm font-bold px-2 py-0.5 rounded",
            variant.estimated_conversion_score >= 70
              ? "bg-green-100 text-green-700"
              : variant.estimated_conversion_score >= 50
                ? "bg-yellow-100 text-yellow-700"
                : "bg-red-100 text-red-700"
          )}
        >
          {Math.round(variant.estimated_conversion_score)}
        </div>
      </div>
      <div
        className="text-sm text-gray-700 whitespace-pre-wrap mb-3 max-h-48 overflow-y-auto"
        dangerouslySetInnerHTML={{ __html: variant.content }}
      />
      {variant.highlights.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {variant.highlights.map((h, i) => (
            <span
              key={i}
              className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full"
            >
              {h}
            </span>
          ))}
        </div>
      )}
      <button
        onClick={() => onSelect(variant.content)}
        className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
      >
        Use this variant
      </button>
    </div>
  );
}

export function BlurbEditor({ initialBlurb = "", className }: BlurbEditorProps) {
  const [blurb, setBlurb] = useState(initialBlurb);
  const [genre, setGenre] = useState("other");
  const [keywords, setKeywords] = useState("");
  const [numVariants, setNumVariants] = useState(3);
  const generateMutation = useGenerateBlurb();

  const handleGenerate = () => {
    if (blurb.length < 10) return;
    generateMutation.mutate({
      current_blurb: blurb,
      genre,
      keywords: keywords
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean),
      num_variants: numVariants,
    });
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Editor */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Blurb Editor</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Blurb
            </label>
            <textarea
              value={blurb}
              onChange={(e) => setBlurb(e.target.value)}
              rows={8}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-indigo-500"
              placeholder="Paste your current blurb here..."
            />
            <p className="text-xs text-gray-500 mt-1">
              {blurb.split(/\s+/).filter(Boolean).length} words
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Genre
              </label>
              <select
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {GENRES.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Keywords (comma-separated)
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                placeholder="romance, billionaire, love"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Variants
              </label>
              <select
                value={numVariants}
                onChange={(e) => setNumVariants(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={blurb.length < 10 || generateMutation.isPending}
            className={cn(
              "rounded-md px-4 py-2 text-sm font-medium text-white",
              blurb.length < 10 || generateMutation.isPending
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-700"
            )}
          >
            {generateMutation.isPending ? "Generating..." : "Generate Variants"}
          </button>
        </div>
      </div>

      {/* Results */}
      {generateMutation.data && (
        <div className="rounded-lg border bg-gray-50 p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-semibold">Generated Variants</h4>
            <span className="text-sm text-gray-500">
              Original score: {Math.round(generateMutation.data.original_score)}
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {generateMutation.data.variants.map((variant) => (
              <VariantCard
                key={variant.variant_id}
                variant={variant}
                onSelect={(content) => setBlurb(content)}
              />
            ))}
          </div>
        </div>
      )}

      {generateMutation.isError && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          Failed to generate variants. Please try again.
        </div>
      )}
    </div>
  );
}
