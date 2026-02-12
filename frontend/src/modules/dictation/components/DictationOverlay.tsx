"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import type { LowConfidenceWord, VoiceCommandEvent } from "../types";

interface DictationOverlayProps {
  partialText: string;
  finalTexts: string[];
  lowConfidenceWords: LowConfidenceWord[];
  lastCommand?: VoiceCommandEvent;
  wordCount: number;
}

function ConfidenceWord({
  word,
  confidence,
  onCorrect,
}: {
  word: string;
  confidence: number;
  onCorrect: (word: string) => void;
}) {
  const [showSuggestions, setShowSuggestions] = React.useState(false);

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={cn(
              "cursor-pointer border-b-2 border-dashed border-orange-400 font-inherit text-inherit",
              "hover:bg-orange-50 dark:hover:bg-orange-950/30",
              "rounded-sm px-0.5 transition-colors"
            )}
            onClick={() => setShowSuggestions(!showSuggestions)}
            aria-label={`Low confidence word: ${word}, ${Math.round(confidence * 100)}% confident. Click for corrections.`}
          >
            {word}
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          <p className="font-medium">
            Confidence: {Math.round(confidence * 100)}%
          </p>
          <p className="text-muted-foreground">Click to correct</p>
        </TooltipContent>
      </Tooltip>
      {showSuggestions && (
        <span className="relative inline-block">
          <span
            className="absolute -top-1 left-0 z-10 -translate-y-full rounded border bg-background p-1.5 shadow-md"
            role="listbox"
            aria-label="Correction suggestions"
          >
            <button
              type="button"
              className="block w-full rounded px-2 py-1 text-left text-xs hover:bg-accent"
              onClick={() => {
                onCorrect(word);
                setShowSuggestions(false);
              }}
              role="option"
              aria-selected={false}
            >
              Re-dictate
            </button>
          </span>
        </span>
      )}
    </TooltipProvider>
  );
}

function CommandToast({ command }: { command: VoiceCommandEvent }) {
  const [visible, setVisible] = React.useState(true);

  React.useEffect(() => {
    setVisible(true);
    const timer = setTimeout(() => setVisible(false), 2000);
    return () => clearTimeout(timer);
  }, [command]);

  if (!visible) return null;

  return (
    <div
      className="animate-in fade-in slide-in-from-bottom-2 duration-300"
      role="status"
      aria-live="polite"
    >
      <Badge variant="secondary" className="gap-1.5 px-3 py-1 text-xs">
        <span className="font-medium">{command.command}</span>
        <span className="text-muted-foreground">{command.action}</span>
      </Badge>
    </div>
  );
}

function AnimatedWordCount({
  count,
  prevCount,
}: {
  count: number;
  prevCount: number;
}) {
  const [animate, setAnimate] = React.useState(false);

  React.useEffect(() => {
    if (count !== prevCount) {
      setAnimate(true);
      const timer = setTimeout(() => setAnimate(false), 300);
      return () => clearTimeout(timer);
    }
  }, [count, prevCount]);

  return (
    <span
      className={cn(
        "inline-block tabular-nums transition-transform duration-300",
        animate && "scale-110 text-primary"
      )}
      aria-label={`Word count: ${count}`}
    >
      {count.toLocaleString()}
    </span>
  );
}

export function DictationOverlay({
  partialText,
  finalTexts,
  lowConfidenceWords,
  lastCommand,
  wordCount,
}: DictationOverlayProps) {
  const prevWordCount = React.useRef(wordCount);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const prev = prevWordCount.current;
    prevWordCount.current = wordCount;
    return () => {
      prevWordCount.current = prev;
    };
  }, [wordCount]);

  const lowConfidenceMap = React.useMemo(() => {
    const map = new Map<number, LowConfidenceWord>();
    for (const lcw of lowConfidenceWords) {
      map.set(lcw.index, lcw);
    }
    return map;
  }, [lowConfidenceWords]);

  const handleCorrect = React.useCallback((_word: string) => {
    // Correction handler — parent component would handle re-dictation
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative"
      role="region"
      aria-label="Dictation overlay"
      aria-live="polite"
    >
      {/* Final transcripts */}
      {finalTexts.map((text, textIndex) => {
        const words = text.split(/\s+/);
        return (
          <span key={textIndex} className="text-foreground">
            {words.map((word, wordIndex) => {
              const globalIndex = textIndex * 1000 + wordIndex;
              const lcw = lowConfidenceMap.get(globalIndex);
              if (lcw) {
                return (
                  <React.Fragment key={wordIndex}>
                    <ConfidenceWord
                      word={word}
                      confidence={lcw.confidence}
                      onCorrect={handleCorrect}
                    />{" "}
                  </React.Fragment>
                );
              }
              return (
                <React.Fragment key={wordIndex}>{word} </React.Fragment>
              );
            })}
          </span>
        );
      })}

      {/* Partial transcript (in-progress) */}
      {partialText && (
        <span className="italic text-muted-foreground" aria-label="Partial transcript">
          {partialText}
        </span>
      )}

      {/* Word count indicator */}
      <div className="mt-2 flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          <AnimatedWordCount
            count={wordCount}
            prevCount={prevWordCount.current}
          />{" "}
          words
        </div>

        {/* Voice command toast */}
        {lastCommand && <CommandToast command={lastCommand} />}
      </div>
    </div>
  );
}
