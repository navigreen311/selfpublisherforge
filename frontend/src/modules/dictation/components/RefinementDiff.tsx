"use client";

import * as React from "react";
import { Check, X, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { DiffSegment } from "../types";

interface RefinementDiffProps {
  rawText: string;
  refinedText: string;
  diff: DiffSegment[];
  styleMatchScore?: number;
  onAcceptAll: () => void;
  onAcceptParagraph: (index: number) => void;
  onReject: () => void;
  onRevertSentence: (sentenceIndex: number) => void;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
  if (score >= 60) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
  return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
}

function splitIntoParagraphs(text: string): string[] {
  return text.split(/\n\n+/).filter(Boolean);
}

function DiffHighlight({
  segment,
  side,
  sentenceIndex,
  onRevert,
}: {
  segment: DiffSegment;
  side: "raw" | "refined";
  sentenceIndex: number;
  onRevert: (index: number) => void;
}) {
  const text = side === "raw" ? segment.rawText : segment.refinedText;

  if (!text) return null;

  switch (segment.type) {
    case "unchanged":
      return <span>{text}</span>;

    case "added":
      if (side === "raw") return null;
      return (
        <button
          type="button"
          className="cursor-pointer rounded-sm bg-green-100 px-0.5 text-green-900 transition-colors hover:bg-green-200 dark:bg-green-900/40 dark:text-green-300 dark:hover:bg-green-900/60"
          onClick={() => onRevert(sentenceIndex)}
          aria-label={`Revert addition: ${text}`}
        >
          {text}
        </button>
      );

    case "removed":
      if (side === "refined") return null;
      return (
        <span className="rounded-sm bg-red-100 px-0.5 line-through text-red-900 dark:bg-red-900/40 dark:text-red-300">
          {text}
        </span>
      );

    case "changed":
      if (side === "raw") {
        return (
          <span className="rounded-sm bg-yellow-100 px-0.5 line-through text-yellow-900 dark:bg-yellow-900/40 dark:text-yellow-300">
            {text}
          </span>
        );
      }
      return (
        <button
          type="button"
          className="cursor-pointer rounded-sm bg-yellow-100 px-0.5 text-yellow-900 transition-colors hover:bg-yellow-200 dark:bg-yellow-900/40 dark:text-yellow-300 dark:hover:bg-yellow-900/60"
          onClick={() => onRevert(sentenceIndex)}
          aria-label={`Revert change: ${text}`}
        >
          {text}
        </button>
      );

    default:
      return <span>{text}</span>;
  }
}

export function RefinementDiff({
  rawText,
  refinedText,
  diff,
  styleMatchScore,
  onAcceptAll,
  onAcceptParagraph,
  onReject,
  onRevertSentence,
}: RefinementDiffProps) {
  const rawScrollRef = React.useRef<HTMLDivElement>(null);
  const refinedScrollRef = React.useRef<HTMLDivElement>(null);
  const isSyncing = React.useRef(false);

  const handleScroll = React.useCallback(
    (source: "raw" | "refined") => {
      if (isSyncing.current) return;
      isSyncing.current = true;

      const sourceEl =
        source === "raw" ? rawScrollRef.current : refinedScrollRef.current;
      const targetEl =
        source === "raw" ? refinedScrollRef.current : rawScrollRef.current;

      if (sourceEl && targetEl) {
        const ratio =
          sourceEl.scrollTop /
          (sourceEl.scrollHeight - sourceEl.clientHeight || 1);
        targetEl.scrollTop =
          ratio * (targetEl.scrollHeight - targetEl.clientHeight);
      }

      requestAnimationFrame(() => {
        isSyncing.current = false;
      });
    },
    []
  );

  const rawParagraphs = React.useMemo(
    () => splitIntoParagraphs(rawText),
    [rawText]
  );
  const refinedParagraphs = React.useMemo(
    () => splitIntoParagraphs(refinedText),
    [refinedText]
  );

  return (
    <div
      className="flex flex-col gap-3 rounded-lg border bg-background p-4"
      role="region"
      aria-label="Refinement diff view"
    >
      {/* Header with score and actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold">Style Refinement</h3>
          {styleMatchScore !== undefined && (
            <Badge
              className={cn(
                "text-xs font-medium",
                getScoreColor(styleMatchScore)
              )}
            >
              {styleMatchScore}% style match
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onReject}>
            <X className="mr-1.5 h-3.5 w-3.5" />
            Reject
          </Button>
          <Button size="sm" onClick={onAcceptAll}>
            <Check className="mr-1.5 h-3.5 w-3.5" />
            Accept All
          </Button>
        </div>
      </div>

      {/* Side-by-side diff panels */}
      <div className="grid grid-cols-2 gap-3">
        {/* Raw text panel */}
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">
            Original (Dictated)
          </span>
          <div
            ref={rawScrollRef}
            className="max-h-80 overflow-y-auto rounded-md border bg-muted/30 p-3 text-sm leading-relaxed"
            onScroll={() => handleScroll("raw")}
          >
            {diff.length > 0 ? (
              diff.map((segment, i) => (
                <DiffHighlight
                  key={i}
                  segment={segment}
                  side="raw"
                  sentenceIndex={i}
                  onRevert={onRevertSentence}
                />
              ))
            ) : (
              rawParagraphs.map((para, i) => (
                <p key={i} className="mb-2 last:mb-0">
                  {para}
                </p>
              ))
            )}
          </div>
        </div>

        {/* Refined text panel */}
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">
            Refined
          </span>
          <div
            ref={refinedScrollRef}
            className="max-h-80 overflow-y-auto rounded-md border bg-muted/30 p-3 text-sm leading-relaxed"
            onScroll={() => handleScroll("refined")}
          >
            {diff.length > 0 ? (
              diff.map((segment, i) => (
                <DiffHighlight
                  key={i}
                  segment={segment}
                  side="refined"
                  sentenceIndex={i}
                  onRevert={onRevertSentence}
                />
              ))
            ) : (
              refinedParagraphs.map((para, i) => (
                <p key={i} className="mb-2 last:mb-0">
                  {para}
                </p>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Per-paragraph accept buttons */}
      {refinedParagraphs.length > 1 && (
        <div className="flex flex-wrap gap-2 border-t pt-3">
          <span className="self-center text-xs text-muted-foreground">
            Accept by paragraph:
          </span>
          {refinedParagraphs.map((_, i) => (
            <Button
              key={i}
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onAcceptParagraph(i)}
            >
              <RotateCcw className="mr-1 h-3 w-3" />
              Paragraph {i + 1}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
