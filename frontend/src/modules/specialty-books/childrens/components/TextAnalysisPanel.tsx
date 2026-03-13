"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { BarChart3, Loader2, AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";
import { useTextAnalysis } from "../hooks";
import type { TextAnalysisResult } from "../types";

export interface TextAnalysisPanelProps {
  bookId: string;
  ageRange: string;
}

const AGE_LIMITS: Record<string, { maxSentence: number; maxWordLength: number; totalWords: string }> = {
  board: { maxSentence: 5, maxWordLength: 5, totalWords: "50-150" },
  picture: { maxSentence: 8, maxWordLength: 7, totalWords: "300-500" },
  early_reader: { maxSentence: 12, maxWordLength: 9, totalWords: "500-2000" },
  chapter: { maxSentence: 15, maxWordLength: 99, totalWords: "3000-10000" },
};

export function TextAnalysisPanel({ bookId, ageRange }: TextAnalysisPanelProps) {
  const { mutate: analyze, isPending } = useTextAnalysis(bookId);
  const [result, setResult] = useState<TextAnalysisResult | null>(null);

  const limits = AGE_LIMITS[ageRange] ?? AGE_LIMITS.picture;

  const handleAnalyze = () => {
    analyze(undefined, {
      onSuccess: (data) => setResult(data),
    });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Text Analysis</span>
        </div>
        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={handleAnalyze} disabled={isPending}>
          {isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1" />}
          Analyze
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4">
        {!result ? (
          <div className="text-center py-8">
            <BarChart3 className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Run analysis to check readability</p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Max sentence: {limits.maxSentence} words | Target: {limits.totalWords} total words
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Score cards */}
            <div className="grid grid-cols-2 gap-3">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{result.readability_score}</div>
                    <div className="text-xs text-muted-foreground">Readability</div>
                  </div>
                  <Progress value={result.readability_score} className="h-1.5 mt-2" />
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{result.read_aloud_rhythm}</div>
                    <div className="text-xs text-muted-foreground">Read-Aloud</div>
                  </div>
                  <Progress value={result.read_aloud_rhythm} className="h-1.5 mt-2" />
                </CardContent>
              </Card>
            </div>

            {/* Stats */}
            <Card>
              <CardContent className="pt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Words</span>
                  <span className="font-medium">{result.total_words}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Avg Sentence Length</span>
                  <span className={cn("font-medium", result.avg_sentence_length > limits.maxSentence && "text-destructive")}>
                    {result.avg_sentence_length.toFixed(1)} words
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Max Word Length</span>
                  <span className={cn("font-medium", result.max_word_length > limits.maxWordLength && "text-destructive")}>
                    {result.max_word_length} letters
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Vocabulary Level</span>
                  <span className="font-medium">{result.vocabulary_level}</span>
                </div>
              </CardContent>
            </Card>

            {/* Issues */}
            {result.issues.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-1">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                  Issues ({result.issues.length})
                </h4>
                {result.issues.map((issue, i) => (
                  <Card key={i}>
                    <CardContent className="pt-3 pb-3">
                      <div className="flex items-start gap-2">
                        <Badge variant="outline" className="shrink-0 text-[10px]">
                          p.{issue.page}
                        </Badge>
                        <div>
                          <p className="text-xs">{issue.issue}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{issue.suggestion}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {result.issues.length === 0 && (
              <div className="text-center py-4">
                <CheckCircle2 className="h-6 w-6 text-green-500 mx-auto mb-1" />
                <p className="text-sm text-muted-foreground">All checks passed</p>
              </div>
            )}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
