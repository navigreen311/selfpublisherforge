"use client";

import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import { Eye, Maximize, Minimize } from "lucide-react";
import type { SaveStatus } from "@/modules/writing/types";

interface StatusBarProps {
  wordCount: number;
  readingTime: number;
  saveStatus: SaveStatus;
  sessionWords: number;
  sessionMinutes: number;
  totalWordCount: number;
  targetWordCount: number;
  showAIPanel: boolean;
  distractionFree: boolean;
  onToggleAIPanel: () => void;
  onToggleDistractionFree: () => void;
}

export function StatusBar({
  wordCount,
  readingTime,
  saveStatus,
  sessionWords,
  sessionMinutes,
  totalWordCount,
  targetWordCount,
  showAIPanel,
  distractionFree,
  onToggleAIPanel,
  onToggleDistractionFree,
}: StatusBarProps) {
  const t = useTranslations("writing");

  const wpm = sessionMinutes > 0 ? Math.round(sessionWords / sessionMinutes) : 0;

  const saveStatusColor: Record<SaveStatus, string> = {
    idle: "text-muted-foreground",
    saving: "text-yellow-600",
    saved: "text-green-600",
    error: "text-red-600",
  };

  return (
    <div className="flex items-center justify-between border-t bg-card px-4 py-1.5 flex-shrink-0 text-xs text-muted-foreground">
      {/* Left: word count + reading time */}
      <div className="flex items-center gap-3">
        <span>{wordCount.toLocaleString()} {t("stats.words")}</span>
        <span className="text-border">|</span>
        <span>~{readingTime} {t("editor.minRead")}</span>
        {targetWordCount > 0 && (
          <>
            <span className="text-border">|</span>
            <span>{wordCount.toLocaleString()} / {targetWordCount.toLocaleString()}</span>
          </>
        )}
      </div>

      {/* Center: save status + session */}
      <div className="flex items-center gap-3">
        <span className={cn("inline-flex items-center gap-1", saveStatusColor[saveStatus])}>
          {saveStatus === "saving" && (
            <>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-yellow-500 animate-pulse" />
              {t("editor.saveStatus.saving")}
            </>
          )}
          {saveStatus === "saved" && (
            <>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
              {t("editor.saveStatus.saved")}
            </>
          )}
          {saveStatus === "error" && (
            <>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500" />
              {t("editor.saveStatus.error")}
            </>
          )}
        </span>
        <span className="text-border">|</span>
        <span>
          {sessionWords.toLocaleString()} {t("stats.words")} / {sessionMinutes} {t("stats.minutes")}
          {wpm > 0 && ` (${wpm} wpm)`}
        </span>
      </div>

      {/* Right: panel toggles */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleAIPanel}
          className={cn(
            "inline-flex items-center gap-1 px-2 py-0.5 rounded transition-colors hover:bg-accent",
            showAIPanel && "text-primary"
          )}
          title={`${showAIPanel ? t("editor.hideAI") : t("editor.showAI")} (Ctrl+Shift+A)`}
        >
          <Eye className="h-3 w-3" />
          {t("editor.aiPanel")}
        </button>
        <button
          onClick={onToggleDistractionFree}
          className={cn(
            "inline-flex items-center gap-1 px-2 py-0.5 rounded transition-colors hover:bg-accent",
            distractionFree && "text-primary"
          )}
          title={`${t("editor.focusMode")} (F11)`}
        >
          {distractionFree ? <Minimize className="h-3 w-3" /> : <Maximize className="h-3 w-3" />}
          {t("editor.focusMode")}
        </button>
      </div>
    </div>
  );
}
