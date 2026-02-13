"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import { Eye, Maximize, Minimize } from "lucide-react";
import type { SaveStatus } from "@/modules/writing/types";

interface StatusBarProps {
  wordCount: number;
  readingTime: number;
  saveStatus: SaveStatus;
  savedAt?: Date;
  sessionWords: number;
  sessionMinutes: number;
  totalWordCount: number;
  targetWordCount: number;
  showAIPanel: boolean;
  distractionFree: boolean;
  onToggleFocusMode?: () => void;
  onToggleAIPanel: () => void;
  onToggleDistractionFree: () => void;
}

/**
 * Format a Date to a locale time string like "10:32 AM".
 */
function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

/**
 * Format a duration in seconds into mm:ss or h:mm format.
 */
function formatDuration(totalSeconds: number): string {
  if (totalSeconds < 0) totalSeconds = 0;
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}`;
  }
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function StatusBar({
  wordCount,
  readingTime,
  saveStatus,
  savedAt: savedAtProp,
  sessionWords,
  sessionMinutes,
  totalWordCount,
  targetWordCount,
  showAIPanel,
  distractionFree,
  onToggleFocusMode,
  onToggleAIPanel,
  onToggleDistractionFree,
}: StatusBarProps) {
  const t = useTranslations("writing");

  // ---- Internal session tracking -------------------------------------------
  const sessionStartTimeRef = useRef<number>(Date.now());
  const sessionStartWordCountRef = useRef<number>(wordCount);
  const [tick, setTick] = useState(0);

  // Initialize session start word count on first mount
  useEffect(() => {
    sessionStartWordCountRef.current = wordCount;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update every 10 seconds for live session stats
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((prev) => prev + 1);
    }, 10_000);
    return () => clearInterval(interval);
  }, []);

  // Calculate session stats from internal tracking
  const elapsedSeconds = Math.floor(
    (Date.now() - sessionStartTimeRef.current) / 1000
  );
  const wordsThisSession = Math.max(
    0,
    wordCount - sessionStartWordCountRef.current
  );
  const elapsedMinutes = elapsedSeconds / 60;
  const wpm =
    elapsedMinutes > 0.5
      ? Math.round(wordsThisSession / elapsedMinutes)
      : 0;
  const displaySessionWords = Math.max(wordsThisSession, sessionWords);
  const displayWpm =
    sessionMinutes > 0
      ? Math.max(wpm, Math.round(sessionWords / sessionMinutes))
      : wpm;

  // ---- Save status tracking ------------------------------------------------
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(
    savedAtProp ?? null
  );
  const prevSaveStatusRef = useRef<SaveStatus>(saveStatus);

  useEffect(() => {
    if (savedAtProp) {
      setLastSavedAt(savedAtProp);
    }
  }, [savedAtProp]);

  // Detect transition from "saving" to "saved" to record timestamp
  useEffect(() => {
    if (
      prevSaveStatusRef.current === "saving" &&
      saveStatus === "saved"
    ) {
      setLastSavedAt(new Date());
    }
    prevSaveStatusRef.current = saveStatus;
  }, [saveStatus]);

  // ---- Save status display -------------------------------------------------
  const getSaveStatusDisplay = useCallback(() => {
    switch (saveStatus) {
      case "saving":
        return {
          text: "Saving...",
          colorClass: "text-muted-foreground",
        };
      case "saved":
        return {
          text: lastSavedAt
            ? `Saved at ${formatTime(lastSavedAt)}`
            : "Saved",
          colorClass: "text-green-500",
        };
      case "error":
        return {
          text: "Save error",
          colorClass: "text-red-500",
        };
      case "idle":
      default:
        return {
          text: "Unsaved changes",
          colorClass: "text-orange-400",
        };
    }
  }, [saveStatus, lastSavedAt]);

  const status = getSaveStatusDisplay();

  // ---- Toggle handler for focus mode ---------------------------------------
  const handleToggleFocusMode = useCallback(() => {
    if (onToggleFocusMode) {
      onToggleFocusMode();
    } else {
      onToggleDistractionFree();
    }
  }, [onToggleFocusMode, onToggleDistractionFree]);

  // Suppress unused var lint: tick forces re-render on interval
  void tick;

  return (
    <div
      className={cn(
        "flex items-center border-t bg-card/95 backdrop-blur-sm px-4 flex-shrink-0 text-xs text-muted-foreground",
        "h-10 min-h-[40px] max-h-[40px]"
      )}
    >
      {/* Left section: word count, reading time, save status, session */}
      <div className="flex items-center gap-0 overflow-hidden">
        {/* Word count */}
        <div className="flex items-center gap-1.5 px-3 border-r border-border/50">
          <span aria-hidden="true" className="text-sm leading-none">
            {"✏️"}
          </span>
          <span className="font-medium tabular-nums whitespace-nowrap">
            {wordCount.toLocaleString()} words
          </span>
        </div>

        {/* Reading time */}
        <div className="flex items-center gap-1.5 px-3 border-r border-border/50">
          <span aria-hidden="true" className="text-sm leading-none">
            {"📖"}
          </span>
          <span className="whitespace-nowrap">
            {readingTime} min read
          </span>
        </div>

        {/* Save status */}
        <div
          className={cn(
            "flex items-center gap-1.5 px-3 border-r border-border/50 transition-colors duration-300",
            status.colorClass
          )}
        >
          <span aria-hidden="true" className="text-sm leading-none">
            {"💾"}
          </span>
          <span
            className={cn(
              "whitespace-nowrap",
              saveStatus === "saving" && "animate-pulse"
            )}
          >
            {status.text}
          </span>
        </div>

        {/* Session stats - hidden on small screens */}
        <div className="hidden md:flex items-center gap-1.5 px-3 border-r border-border/50">
          <span aria-hidden="true" className="text-sm leading-none">
            {"⏱️"}
          </span>
          <span className="whitespace-nowrap tabular-nums">
            Session: {displaySessionWords.toLocaleString()} words /{" "}
            {formatDuration(elapsedSeconds)}
            {displayWpm > 0 && (
              <span className="text-muted-foreground/70">
                {" "}({displayWpm} wpm)
              </span>
            )}
          </span>
        </div>

        {/* Target word count progress - hidden on smaller screens */}
        {targetWordCount > 0 && (
          <div className="hidden lg:flex items-center gap-1.5 px-3 border-r border-border/50">
            <span aria-hidden="true" className="text-sm leading-none">
              {"🎯"}
            </span>
            <span className="whitespace-nowrap tabular-nums">
              {totalWordCount.toLocaleString()} /{" "}
              {targetWordCount.toLocaleString()}
            </span>
            <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden ml-1">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{
                  width: `${Math.min(
                    100,
                    (totalWordCount / targetWordCount) * 100
                  )}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Right section: panel toggles */}
      <div className="flex items-center gap-1 ml-auto flex-shrink-0">
        {/* AI Panel toggle */}
        <button
          onClick={onToggleAIPanel}
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors",
            "hover:bg-accent/80",
            showAIPanel
              ? "text-primary bg-accent/50"
              : "text-muted-foreground"
          )}
          title={`${
            showAIPanel ? "Hide" : "Show"
          } AI Panel (Ctrl+Shift+A)`}
        >
          <Eye className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">
            {t("editor.aiPanel")}
          </span>
        </button>

        {/* Focus Mode toggle */}
        <button
          onClick={handleToggleFocusMode}
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors",
            "hover:bg-accent/80",
            distractionFree
              ? "text-primary bg-accent/50"
              : "text-muted-foreground"
          )}
          title={`${t("editor.focusMode")} (F11)`}
        >
          {distractionFree ? (
            <Minimize className="h-3.5 w-3.5" />
          ) : (
            <Maximize className="h-3.5 w-3.5" />
          )}
          <span className="hidden sm:inline">
            {"🖥️"} {t("editor.focusMode")}
          </span>
        </button>
      </div>
    </div>
  );
}
