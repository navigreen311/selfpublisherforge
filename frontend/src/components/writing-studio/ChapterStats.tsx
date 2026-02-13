"use client";

import { useEffect, useState, useCallback } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

interface ReadabilityData {
  grade_level: number;
  flesch_ease: number;
  flesch_label: string;
  passive_voice_pct: number;
  avg_sentence_length: number;
  word_count: number;
  suggestions: string[];
}

interface ChapterStatsProps {
  wordCount: number;
  targetWordCount?: number;
  content?: string; // Raw text content for readability analysis
  className?: string;
}

function getGradeColor(grade: number): { text: string; bg: string; emoji: string } {
  if (grade <= 9) return { text: "text-green-600", bg: "bg-green-500", emoji: "\u{1F7E2}" };
  if (grade <= 12) return { text: "text-yellow-600", bg: "bg-yellow-500", emoji: "\u{1F7E1}" };
  return { text: "text-red-600", bg: "bg-red-500", emoji: "\u{1F534}" };
}

function getPassiveColor(pct: number): { text: string; bg: string; emoji: string } {
  if (pct < 10) return { text: "text-green-600", bg: "bg-green-500", emoji: "\u{1F7E2}" };
  if (pct <= 15) return { text: "text-yellow-600", bg: "bg-yellow-500", emoji: "\u{1F7E1}" };
  return { text: "text-red-600", bg: "bg-red-500", emoji: "\u{1F534}" };
}

export function ChapterStats({
  wordCount,
  targetWordCount = 0,
  content,
  className,
}: ChapterStatsProps) {
  const t = useTranslations("writing");
  const [readability, setReadability] = useState<ReadabilityData | null>(null);
  const [tooltipMetric, setTooltipMetric] = useState<string | null>(null);

  // Debounced readability analysis
  const analyzeReadability = useCallback(async (text: string) => {
    if (!text || text.trim().length < 50) {
      setReadability(null);
      return;
    }
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${baseURL}/api/v1/writing/readability`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ text }),
      });
      if (res.ok) {
        const data = await res.json();
        setReadability(data);
      }
    } catch {
      // Silently fail
    }
  }, []);

  // Debounce the readability analysis (every 5 seconds)
  useEffect(() => {
    if (!content) return;
    const timer = setTimeout(() => {
      // Strip HTML tags to get plain text
      const plainText = content.replace(/<[^>]*>/g, " ").trim();
      analyzeReadability(plainText);
    }, 5000);
    return () => clearTimeout(timer);
  }, [content, analyzeReadability]);

  const wordProgress = targetWordCount > 0
    ? Math.min(Math.round((wordCount / targetWordCount) * 100), 100)
    : 0;

  const gradeStyle = readability ? getGradeColor(readability.grade_level) : null;
  const passiveStyle = readability ? getPassiveColor(readability.passive_voice_pct) : null;

  const tooltips: Record<string, string> = {
    grade: "Flesch-Kincaid Grade Level measures text complexity. Grade 6-9 is ideal for most books.",
    flesch: "Flesch Reading Ease: 90-100 (Very Easy), 60-70 (Standard), 0-30 (Very Difficult).",
    passive: "Passive voice percentage. Under 10% is ideal. Over 15% can make writing feel flat.",
    avgSentence: "Average words per sentence. 15-20 is ideal for readability.",
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Word count progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-foreground">
            {t("ai.chapterStatsSection.wordCount")}
          </span>
          <span className="text-muted-foreground">
            {wordCount.toLocaleString()}
            {targetWordCount > 0 && (
              <span> / {targetWordCount.toLocaleString()} ({wordProgress}%)</span>
            )}
          </span>
        </div>
        {targetWordCount > 0 && (
          <Progress value={wordProgress} className="h-2" />
        )}
      </div>

      {/* Readability metrics */}
      {readability ? (
        <div className="space-y-2.5">
          {/* Grade level */}
          <div
            className="flex items-center justify-between text-xs cursor-help relative"
            onMouseEnter={() => setTooltipMetric("grade")}
            onMouseLeave={() => setTooltipMetric(null)}
          >
            <span className="text-muted-foreground">Readability</span>
            <span className={cn("flex items-center gap-1.5 font-medium", gradeStyle?.text)}>
              {gradeStyle?.emoji} Grade {readability.grade_level.toFixed(1)}
            </span>
            {tooltipMetric === "grade" && (
              <div className="absolute right-0 top-5 z-10 w-52 rounded-md border bg-popover p-2 text-xs text-popover-foreground shadow-md">
                {tooltips.grade}
              </div>
            )}
          </div>

          {/* Flesch ease */}
          <div
            className="flex items-center justify-between text-xs cursor-help relative"
            onMouseEnter={() => setTooltipMetric("flesch")}
            onMouseLeave={() => setTooltipMetric(null)}
          >
            <span className="text-muted-foreground">Flesch</span>
            <span className="font-medium">
              {readability.flesch_ease.toFixed(0)} ({readability.flesch_label})
            </span>
            {tooltipMetric === "flesch" && (
              <div className="absolute right-0 top-5 z-10 w-52 rounded-md border bg-popover p-2 text-xs text-popover-foreground shadow-md">
                {tooltips.flesch}
              </div>
            )}
          </div>

          {/* Passive voice */}
          <div
            className="flex items-center justify-between text-xs cursor-help relative"
            onMouseEnter={() => setTooltipMetric("passive")}
            onMouseLeave={() => setTooltipMetric(null)}
          >
            <span className="text-muted-foreground">Passive voice</span>
            <span className={cn("flex items-center gap-1.5 font-medium", passiveStyle?.text)}>
              {passiveStyle?.emoji} {readability.passive_voice_pct.toFixed(1)}%
            </span>
            {tooltipMetric === "passive" && (
              <div className="absolute right-0 top-5 z-10 w-52 rounded-md border bg-popover p-2 text-xs text-popover-foreground shadow-md">
                {tooltips.passive}
              </div>
            )}
          </div>

          {/* Average sentence length */}
          <div
            className="flex items-center justify-between text-xs cursor-help relative"
            onMouseEnter={() => setTooltipMetric("avgSentence")}
            onMouseLeave={() => setTooltipMetric(null)}
          >
            <span className="text-muted-foreground">Avg sentence</span>
            <span className="font-medium">{readability.avg_sentence_length.toFixed(0)} words</span>
            {tooltipMetric === "avgSentence" && (
              <div className="absolute right-0 top-5 z-10 w-52 rounded-md border bg-popover p-2 text-xs text-popover-foreground shadow-md">
                {tooltips.avgSentence}
              </div>
            )}
          </div>

          {/* Suggestions */}
          {readability.suggestions.length > 0 && (
            <div className="mt-2 space-y-1">
              {readability.suggestions.map((suggestion, i) => (
                <p key={i} className="text-[10px] text-amber-600">
                  {"\u{1F4A1}"} {suggestion}
                </p>
              ))}
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          {content && content.length > 0 ? t("ai.chapterStatsSection.loading") : t("ai.stats.noData")}
        </p>
      )}
    </div>
  );
}

export default ChapterStats;
