"use client";

import { useState } from "react";
import { Search, Loader2, ImageIcon } from "lucide-react";
import { useAnalyzeCompetitors } from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { CoverGenre } from "../types";

interface CompetitorCoversProps {
  genre?: CoverGenre;
}

export function CompetitorCovers({ genre }: CompetitorCoversProps) {
  const [keywords, setKeywords] = useState("");
  const [selectedGenre, setSelectedGenre] = useState<CoverGenre | undefined>(genre);
  const { mutate: analyzeCompetitors, data: analysis, isPending } = useAnalyzeCompetitors();

  const handleAnalyze = () => {
    if (!keywords.trim()) return;

    analyzeCompetitors({
      niche_keywords: keywords.split(",").map(k => k.trim()).filter(Boolean),
      genre: selectedGenre!,
      max_results: 12,
    });
  };

  return (
    <div className="space-y-6">
      {/* Search form */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            placeholder="Enter keywords (e.g., romantic suspense, dark fantasy)..."
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            className="flex-1 border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <Button
            onClick={handleAnalyze}
            disabled={isPending || !keywords.trim()}
            className="gap-2"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                Analyze
              </>
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Analyze competitor covers to discover trending styles, colors, and design patterns in your genre.
        </p>
      </div>

      {/* Loading state */}
      {isPending && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="aspect-[2/3] w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {!isPending && analysis && (
        <div className="space-y-6">
          {/* Summary insights */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="p-4 border rounded-lg bg-muted/50">
              <h3 className="font-semibold mb-2">Key Insights</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Competitor covers grid */}
          {analysis.analyses && analysis.analyses.length > 0 ? (
            <>
              <p className="text-sm text-muted-foreground">
                {analysis.analyses.length} competitor cover{analysis.analyses.length !== 1 ? "s" : ""} analyzed
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {analysis.analyses.map((cover, index) => (
                  <div key={index} className="border rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                    {/* Cover image */}
                    <div className="aspect-[2/3] bg-muted relative overflow-hidden">
                      {cover.image_url ? (
                        <img
                          src={cover.image_url}
                          alt={`Competitor cover ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                          <ImageIcon className="h-10 w-10" />
                        </div>
                      )}
                    </div>

                    {/* Cover analysis */}
                    <div className="p-3 space-y-2">
                      {cover.overall_mood && (
                        <div>
                          <p className="text-xs font-semibold">Mood</p>
                          <p className="text-xs text-muted-foreground">{cover.overall_mood}</p>
                        </div>
                      )}
                      {cover.dominant_colors && cover.dominant_colors.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold mb-1">Colors</p>
                          <div className="flex gap-1">
                            {cover.dominant_colors.slice(0, 5).map((color, i) => (
                              <div
                                key={i}
                                className="w-6 h-6 rounded border"
                                style={{ backgroundColor: color.hex_code }}
                                title={color.name || color.hex_code}
                              />
                            ))}
                          </div>
                        </div>
                      )}
                      {cover.effectiveness_score !== null && cover.effectiveness_score !== undefined && (
                        <div>
                          <p className="text-xs font-semibold">Score</p>
                          <p className="text-xs text-muted-foreground">
                            {Math.round(cover.effectiveness_score * 100)}%
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No competitor covers found.</p>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!isPending && !analysis && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">
            Enter keywords to analyze competitor covers in your niche.
          </p>
        </div>
      )}
    </div>
  );
}
