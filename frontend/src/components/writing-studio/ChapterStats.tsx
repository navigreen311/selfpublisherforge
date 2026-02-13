"use client";

import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import { Skeleton } from "@/components/ui/skeleton";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ReadabilityData {
  flesch_kincaid_grade: number;
  flesch_reading_ease: number;
  gunning_fog: number;
  smog_index: number;
  passive_voice_pct?: number;
  avg_words_per_sentence?: number;
  reading_level?: string;
  suggestions?: string[];
}

interface ChapterStatsProps {
  readability?: ReadabilityData;
  wordCount: number;
  targetWordCount?: number;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Return Tailwind color classes for grade level indicator. */
function gradeColor(grade: number): string {
  if (grade <= 9) return "text-green-600 dark:text-green-400";
  if (grade <= 12) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
}

/** Return Tailwind bg classes for grade level dot indicator. */
function gradeDotColor(grade: number): string {
  if (grade <= 9) return "bg-green-500";
  if (grade <= 12) return "bg-yellow-500";
  return "bg-red-500";
}

/** Return Tailwind color classes for passive voice percentage. */
function passiveVoiceColor(pct: number): string {
  if (pct < 15) return "text-green-600 dark:text-green-400";
  if (pct <= 25) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
}

/** Return Tailwind bg classes for passive voice dot indicator. */
function passiveVoiceDotColor(pct: number): string {
  if (pct < 15) return "bg-green-500";
  if (pct <= 25) return "bg-yellow-500";
  return "bg-red-500";
}

/** Calculate reading time in minutes (rounded up, minimum 1). */
function readingTime(wordCount: number): number {
  return Math.max(1, Math.ceil(wordCount / 250));
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{children}</span>
    </div>
  );
}

function ColoredStatRow({
  label,
  value,
  colorClass,
  dotColorClass,
}: {
  label: string;
  value: string;
  colorClass: string;
  dotColorClass: string;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn("flex items-center gap-1.5 font-medium", colorClass)}>
        <span
          className={cn("inline-block h-2 w-2 rounded-full", dotColorClass)}
          aria-hidden="true"
        />
        {value}
      </span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="flex items-center justify-between">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function ChapterStats({
  readability,
  wordCount,
  targetWordCount,
  isLoading = false,
}: ChapterStatsProps) {
  const t = useTranslations("writing");

  // ---- Loading state ----
  if (isLoading) {
    return (
      <div className="space-y-1" role="status" aria-busy="true">
        <h4 className="text-sm font-semibold mb-3">
          {t("ai.chapterStats.title")}
        </h4>
        <LoadingSkeleton />
        <span className="sr-only">{t("ai.chapterStats.loading")}</span>
      </div>
    );
  }

  const minutes = readingTime(wordCount);
  const wordProgress =
    targetWordCount && targetWordCount > 0
      ? Math.min(Math.round((wordCount / targetWordCount) * 100), 100)
      : null;

  return (
    <div className="space-y-1">
      <h4 className="text-sm font-semibold mb-3">
        {t("ai.chapterStats.title")}
      </h4>

      {/* Word Count */}
      <StatRow label={t("ai.chapterStats.wordCount")}>
        {wordCount.toLocaleString()}
      </StatRow>

      {/* Word count progress bar toward target */}
      {targetWordCount != null && targetWordCount > 0 && (
        <div className="pb-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>
              {t("ai.chapterStats.target")}: {targetWordCount.toLocaleString()}
            </span>
            <span>{wordProgress}%</span>
          </div>
          <div
            className="h-1.5 w-full rounded-full bg-muted"
            role="progressbar"
            aria-valuenow={wordCount}
            aria-valuemin={0}
            aria-valuemax={targetWordCount}
          >
            <div
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                wordProgress != null && wordProgress >= 100
                  ? "bg-green-500"
                  : "bg-primary"
              )}
              style={{ width: `${wordProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Reading Time */}
      <StatRow label={t("ai.chapterStats.readingTime")}>
        {t("ai.chapterStats.minutes", { count: minutes })}
      </StatRow>

      {/* Divider before readability stats */}
      {readability && (
        <>
          <div className="my-2 h-px bg-border" />

          {/* Readability Grade Level */}
          <ColoredStatRow
            label={t("editor.readability.gradeLevel")}
            value={readability.flesch_kincaid_grade.toFixed(1)}
            colorClass={gradeColor(readability.flesch_kincaid_grade)}
            dotColorClass={gradeDotColor(readability.flesch_kincaid_grade)}
          />

          {/* Reading Level label (if provided) */}
          {readability.reading_level && (
            <StatRow label={t("editor.readability.readingLevel")}>
              {readability.reading_level}
            </StatRow>
          )}

          {/* Flesch Reading Ease */}
          <StatRow label={t("editor.readability.fleschEase")}>
            {readability.flesch_reading_ease.toFixed(1)}
          </StatRow>

          {/* Gunning Fog Index */}
          <StatRow label={t("editor.readability.gunningFog")}>
            {readability.gunning_fog.toFixed(1)}
          </StatRow>

          {/* SMOG Index */}
          <StatRow label={t("editor.readability.smogIndex")}>
            {readability.smog_index.toFixed(1)}
          </StatRow>

          {/* Passive Voice Percentage */}
          {readability.passive_voice_pct != null && (
            <ColoredStatRow
              label={t("editor.readability.passiveVoice")}
              value={`${readability.passive_voice_pct.toFixed(1)}%`}
              colorClass={passiveVoiceColor(readability.passive_voice_pct)}
              dotColorClass={passiveVoiceDotColor(readability.passive_voice_pct)}
            />
          )}

          {/* Average Sentence Length */}
          {readability.avg_words_per_sentence != null && (
            <StatRow label={t("editor.readability.avgSentenceLength")}>
              {readability.avg_words_per_sentence.toFixed(1)} {t("ai.chapterStats.words")}
            </StatRow>
          )}

          {/* Suggestions */}
          {readability.suggestions && readability.suggestions.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-muted-foreground mb-1.5">
                {t("ai.chapterStats.suggestions")}
              </p>
              <ul className="space-y-1">
                {readability.suggestions.map((suggestion, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-1.5 text-xs text-muted-foreground"
                  >
                    <span
                      className="mt-1 inline-block h-1 w-1 shrink-0 rounded-full bg-muted-foreground"
                      aria-hidden="true"
                    />
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
