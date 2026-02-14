"use client";

import { useState, useEffect } from "react";
import { RefreshCw, Loader2 } from "lucide-react";
import { useGenerateSample, useConformityCheck } from "../hooks";

interface SampleComparisonProps {
  profileId: string;
}

const COMPARISON_PROMPT = "Write a short passage demonstrating this style.";
const MAX_WORDS = 200;

export function SampleComparison({ profileId }: SampleComparisonProps) {
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [score, setScore] = useState<number | null>(null);

  const generateMutation = useGenerateSample(profileId);
  const conformityMutation = useConformityCheck(profileId);

  const isLoading = generateMutation.isPending || conformityMutation.isPending;

  const runComparison = async () => {
    setScore(null);
    setGeneratedText(null);

    const result = await generateMutation.mutateAsync({
      prompt: COMPARISON_PROMPT,
      max_words: MAX_WORDS,
    });

    setGeneratedText(result.generated_text);

    const check = await conformityMutation.mutateAsync({
      text: result.generated_text,
    });

    setScore(check.overall_score);
  };

  useEffect(() => {
    runComparison();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getScoreBadge = (value: number) => {
    if (value >= 80) {
      return { color: "bg-green-100 text-green-800", label: "Excellent" };
    }
    if (value >= 60) {
      return { color: "bg-yellow-100 text-yellow-800", label: "Good" };
    }
    return { color: "bg-red-100 text-red-800", label: "Needs Work" };
  };

  return (
    <div className="border rounded-lg bg-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Sample Comparison</h3>
        <button
          onClick={runComparison}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
          )}
          Generate Another Comparison
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin mr-3" aria-hidden="true" />
          <span className="text-sm">Generating comparison...</span>
        </div>
      )}

      {!isLoading && (
        <div className="space-y-6">
          {/* Original sample */}
          <div>
            <h4 className="text-sm font-medium mb-2">Original (your sample):</h4>
            <div className="border rounded-lg p-4 bg-muted/30">
              <p className="text-sm text-muted-foreground italic">
                Sample text from your uploaded writing...
              </p>
            </div>
          </div>

          {/* AI-generated text */}
          <div>
            <h4 className="text-sm font-medium mb-2">AI-generated in this style:</h4>
            <div className="border rounded-lg p-4 bg-muted/30">
              {generatedText ? (
                <p className="text-sm">{generatedText}</p>
              ) : (
                <p className="text-sm text-muted-foreground italic">
                  No generated text yet.
                </p>
              )}
            </div>
          </div>

          {/* Similarity Score */}
          {score !== null && (
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium">Similarity Score:</span>
              <span className="text-2xl font-bold">{Math.round(score)}/100</span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreBadge(score).color}`}
              >
                {getScoreBadge(score).label}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
