"use client";

import React, { useRef, useEffect } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { SentenceTiming } from "../types";

interface SentenceHighlighterProps {
  sentences: SentenceTiming[];
  activeSentenceIndex: number;
  selectedSegment: number | null;
  onSentenceClick: (index: number) => void;
  onSegmentSelect: (index: number) => void;
}

export function SentenceHighlighter({
  sentences,
  activeSentenceIndex,
  selectedSegment,
  onSentenceClick,
  onSegmentSelect,
}: SentenceHighlighterProps) {
  const activeRef = useRef<HTMLSpanElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to keep the active sentence in view
  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      const container = containerRef.current;
      const active = activeRef.current;
      const containerRect = container.getBoundingClientRect();
      const activeRect = active.getBoundingClientRect();

      const isAbove = activeRect.top < containerRect.top;
      const isBelow = activeRect.bottom > containerRect.bottom;

      if (isAbove || isBelow) {
        active.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [activeSentenceIndex]);

  if (!sentences.length) return null;

  return (
    <div
      ref={containerRef}
      className="max-h-64 overflow-y-auto rounded-lg border bg-card p-4"
      role="region"
      aria-label="Chapter text with sentence navigation"
    >
      <p className="mb-2 text-xs font-medium text-muted-foreground">
        Click a sentence to jump to its position. Right-click to select for regeneration.
      </p>
      <div className="leading-relaxed">
        {sentences.map((sentence, index) => (
          <SentenceSpan
            key={index}
            ref={index === activeSentenceIndex ? activeRef : undefined}
            sentence={sentence}
            index={index}
            isActive={index === activeSentenceIndex}
            isSelected={index === selectedSegment}
            onClick={() => onSentenceClick(index)}
            onSelectForRegeneration={() => onSegmentSelect(index)}
          />
        ))}
      </div>
    </div>
  );
}

interface SentenceSpanProps {
  sentence: SentenceTiming;
  index: number;
  isActive: boolean;
  isSelected: boolean;
  onClick: () => void;
  onSelectForRegeneration: () => void;
}

const SentenceSpan = React.forwardRef<HTMLSpanElement, SentenceSpanProps>(
  function SentenceSpan(
    { sentence, index, isActive, isSelected, onClick, onSelectForRegeneration },
    ref
  ) {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <span
            ref={ref}
            role="button"
            tabIndex={0}
            onClick={(e) => {
              // Left-click navigates to sentence
              e.preventDefault();
              onClick();
            }}
            onContextMenu={(e) => {
              // Right-click opens the context menu via DropdownMenu
              // Prevent browser default context menu
              e.preventDefault();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }}
            className={cn(
              "cursor-pointer rounded-sm px-0.5 py-0.5 transition-colors",
              "hover:bg-indigo-100 dark:hover:bg-indigo-900/30",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              isActive &&
                "bg-indigo-100 font-medium text-indigo-900 dark:bg-indigo-900/40 dark:text-indigo-100",
              isSelected &&
                "ring-2 ring-amber-400 bg-amber-50 dark:bg-amber-900/30",
              !isActive && !isSelected && "text-foreground"
            )}
            aria-label={`Sentence ${index + 1}: ${sentence.text.slice(0, 50)}${sentence.text.length > 50 ? "..." : ""}`}
            aria-current={isActive ? "true" : undefined}
          >
            {sentence.text}{" "}
          </span>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={onClick}>
            Jump to this sentence
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onSelectForRegeneration}>
            Regenerate this segment
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }
);
