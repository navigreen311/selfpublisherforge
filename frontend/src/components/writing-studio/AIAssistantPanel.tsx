"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Mic } from "lucide-react";
import { useSSEGeneration } from "@/modules/writing/hooks";
import type { GenerateRequest, AIAction } from "@/modules/writing/hooks";
import { AIOutputDisplay } from "./AIOutputDisplay";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AIAssistantPanelProps {
  bookId: string;
  projectId: string;
  chapterId?: string;
  selectedText?: string;
  onInsertText?: (text: string) => void;
  onReplaceSelection?: (text: string) => void;
  readabilityScore?: {
    flesch_kincaid_grade: number;
    flesch_reading_ease: number;
    passive_voice_pct?: number;
    avg_words_per_sentence?: number;
  };
  wordCount?: number;
  targetWordCount?: number;
  className?: string;
}

// ---------------------------------------------------------------------------
// Quick action definitions
// ---------------------------------------------------------------------------

const QUICK_ACTIONS: { action: AIAction; labelKey: string }[] = [
  { action: "write", labelKey: "ai.actions.write" },
  { action: "rewrite", labelKey: "ai.actions.rewrite" },
  { action: "expand", labelKey: "ai.actions.expand" },
  { action: "shorten", labelKey: "ai.actions.shorten" },
  { action: "continue", labelKey: "ai.actions.continue" },
  { action: "brainstorm", labelKey: "ai.actions.brainstorm" },
];

// ---------------------------------------------------------------------------
// Tone and length options
// ---------------------------------------------------------------------------

const TONE_OPTIONS = [
  { value: "match_profile", labelKey: "ai.tone.matchProfile" },
  { value: "more_formal", labelKey: "ai.tone.moreFormal" },
  { value: "more_casual", labelKey: "ai.tone.moreCasual" },
  { value: "more_authoritative", labelKey: "ai.tone.moreAuthoritative" },
  { value: "more_conversational", labelKey: "ai.tone.moreConversational" },
];

const LENGTH_OPTIONS = [
  { value: "short", labelKey: "ai.length.short" },
  { value: "medium", labelKey: "ai.length.medium" },
  { value: "long", labelKey: "ai.length.long" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AIAssistantPanel({
  bookId,
  projectId,
  chapterId,
  selectedText,
  onInsertText,
  onReplaceSelection,
  readabilityScore,
  wordCount = 0,
  targetWordCount = 0,
  className,
}: AIAssistantPanelProps) {
  const t = useTranslations("writing");

  const [customInstruction, setCustomInstruction] = useState("");
  const [tone, setTone] = useState("match_profile");
  const [length, setLength] = useState<"short" | "medium" | "long">("medium");
  const [styleProfile, setStyleProfile] = useState("default");

  const {
    content: generatedContent,
    isStreaming,
    error,
    startGeneration,
    stopGeneration,
  } = useSSEGeneration();

  // -----------------------------------------------------------------------
  // Handlers
  // -----------------------------------------------------------------------

  const handleQuickAction = useCallback(
    (action: AIAction) => {
      const request: GenerateRequest = {
        generation_type: action,
        project_id: projectId,
        instructions:
          customInstruction || `Perform ${action} on the selected text`,
        context: {
          book_id: bookId,
          chapter_id: chapterId,
          selected_text: selectedText || "",
          tone,
          length,
        },
        model_preference: "auto",
        stream: true,
        quality_checks: ["readability"],
      };
      startGeneration(request);
    },
    [
      bookId,
      chapterId,
      customInstruction,
      length,
      projectId,
      selectedText,
      startGeneration,
      tone,
    ]
  );

  const handleCustomGenerate = useCallback(() => {
    if (!customInstruction.trim()) return;
    const request: GenerateRequest = {
      generation_type: "write",
      project_id: projectId,
      instructions: customInstruction,
      context: {
        book_id: bookId,
        chapter_id: chapterId,
        selected_text: selectedText || "",
        tone,
        length,
      },
      model_preference: "auto",
      stream: true,
      quality_checks: ["readability"],
    };
    startGeneration(request);
  }, [
    bookId,
    chapterId,
    customInstruction,
    length,
    projectId,
    selectedText,
    startGeneration,
    tone,
  ]);

  const handleInsert = useCallback(() => {
    if (generatedContent) {
      onInsertText?.(generatedContent);
    }
  }, [generatedContent, onInsertText]);

  const handleReplace = useCallback(() => {
    if (generatedContent) {
      onReplaceSelection?.(generatedContent);
    }
  }, [generatedContent, onReplaceSelection]);

  const handleRegenerate = useCallback(() => {
    handleQuickAction("write");
  }, [handleQuickAction]);

  const handleEditRetry = useCallback(() => {
    setCustomInstruction(generatedContent || customInstruction);
  }, [generatedContent, customInstruction]);

  // -----------------------------------------------------------------------
  // Readability helpers
  // -----------------------------------------------------------------------

  const gradeLevel = readabilityScore?.flesch_kincaid_grade ?? 0;
  const gradeIndicatorColor = gradeLevel <= 12 ? "text-green-600" : "text-yellow-600";
  const gradeIndicatorBg = gradeLevel <= 12 ? "bg-green-500" : "bg-yellow-500";

  const wordProgress =
    targetWordCount > 0 ? Math.min(Math.round((wordCount / targetWordCount) * 100), 100) : 0;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div
      className={cn(
        "flex flex-col h-full border-l bg-card w-80 overflow-y-auto",
        className
      )}
    >
      {/* ---- Header ---- */}
      <div className="px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground">
          {t("ai.title")}
        </h3>
      </div>

      {/* ---- Quick Actions (3x2 grid) ---- */}
      <div className="px-4 py-3 border-b space-y-2">
        <p className="text-xs font-medium text-foreground">
          {t("ai.quickActions")}
        </p>
        <div className="grid grid-cols-3 gap-2">
          {QUICK_ACTIONS.map(({ action, labelKey }) => (
            <Button
              key={action}
              variant="outline"
              size="sm"
              disabled={isStreaming}
              onClick={() => handleQuickAction(action)}
              className="text-xs"
            >
              {t(labelKey)}
            </Button>
          ))}
        </div>
        {isStreaming && (
          <Button
            variant="destructive"
            size="sm"
            className="w-full text-xs"
            onClick={stopGeneration}
          >
            {t("ai.stopGeneration")}
          </Button>
        )}
      </div>

      {/* ---- Custom Instruction ---- */}
      <div className="px-4 py-3 border-b space-y-2">
        <Textarea
          value={customInstruction}
          onChange={(e) => setCustomInstruction(e.target.value)}
          placeholder={t("ai.instructionPlaceholder")}
          className="min-h-[60px] text-sm resize-none"
        />
        <Button
          size="sm"
          className="w-full text-xs"
          disabled={isStreaming || !customInstruction.trim()}
          onClick={handleCustomGenerate}
        >
          {t("ai.generate")}
        </Button>
      </div>

      {/* ---- AI Output ---- */}
      <div className="px-4 py-3 border-b">
        <AIOutputDisplay
          content={generatedContent}
          isStreaming={isStreaming}
          error={error}
          hasSelection={!!selectedText}
          onInsert={handleInsert}
          onReplace={handleReplace}
          onRegenerate={handleRegenerate}
          onEditRetry={handleEditRetry}
        />
      </div>

      {/* ---- Settings ---- */}
      <div className="px-4 py-3 border-b space-y-3">
        <div className="flex items-center gap-2">
          <Separator className="flex-1" />
          <span className="text-xs font-medium text-muted-foreground">
            {t("ai.settings")}
          </span>
          <Separator className="flex-1" />
        </div>

        {/* Style Profile */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-foreground">
            {t("ai.styleProfile")}
          </label>
          <Select value={styleProfile} onValueChange={setStyleProfile}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder={t("ai.styleProfilePlaceholder")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="default">
                {t("ai.styleProfileDefault")}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Tone */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-foreground">
            {t("ai.toneLabel")}
          </label>
          <Select value={tone} onValueChange={setTone}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TONE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {t(opt.labelKey)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Length */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-foreground">
            {t("ai.lengthLabel")}
          </label>
          <Select
            value={length}
            onValueChange={(v) => setLength(v as "short" | "medium" | "long")}
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LENGTH_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {t(opt.labelKey)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* ---- Chapter Stats ---- */}
      <div className="px-4 py-3 border-b space-y-3">
        <div className="flex items-center gap-2">
          <Separator className="flex-1" />
          <span className="text-xs font-medium text-muted-foreground">
            {t("ai.chapterStats")}
          </span>
          <Separator className="flex-1" />
        </div>

        {readabilityScore ? (
          <div className="space-y-2">
            {/* Readability Grade */}
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                {t("ai.stats.gradeLevel")}
              </span>
              <span className={cn("flex items-center gap-1.5 font-medium", gradeIndicatorColor)}>
                <span
                  className={cn("inline-block h-2 w-2 rounded-full", gradeIndicatorBg)}
                />
                {readabilityScore.flesch_kincaid_grade.toFixed(1)}
              </span>
            </div>

            {/* Flesch Score */}
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                {t("ai.stats.fleschScore")}
              </span>
              <span className="font-medium">
                {readabilityScore.flesch_reading_ease.toFixed(1)}
              </span>
            </div>

            {/* Passive Voice */}
            {readabilityScore.passive_voice_pct !== undefined && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {t("ai.stats.passiveVoice")}
                </span>
                <span className="font-medium">
                  {readabilityScore.passive_voice_pct.toFixed(1)}%
                </span>
              </div>
            )}

            {/* Avg Sentence Length */}
            {readabilityScore.avg_words_per_sentence !== undefined && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {t("ai.stats.avgSentenceLength")}
                </span>
                <span className="font-medium">
                  {readabilityScore.avg_words_per_sentence.toFixed(1)} {t("ai.stats.words")}
                </span>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            {t("ai.stats.noData")}
          </p>
        )}

        {/* Word count progress */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {t("ai.stats.wordCount")}
            </span>
            <span className="font-medium">
              {wordCount.toLocaleString()}
              {targetWordCount > 0 && (
                <span className="text-muted-foreground">
                  {" "}
                  / {targetWordCount.toLocaleString()}
                </span>
              )}
            </span>
          </div>
          {targetWordCount > 0 && (
            <Progress value={wordProgress} className="h-2" />
          )}
        </div>
      </div>

      {/* ---- Dictation ---- */}
      <div className="px-4 py-3">
        <Button variant="outline" size="sm" className="w-full text-xs gap-2">
          <Mic className="h-3.5 w-3.5" />
          {t("ai.startDictation")}
        </Button>
      </div>
    </div>
  );
}
