"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ChevronRight, Mic, X } from "lucide-react";
import { useSSEGeneration, useStyleProfiles } from "@/modules/writing/hooks";
import type { GenerateRequest, AIAction } from "@/modules/writing/hooks";
import { AIOutputDisplay } from "./AIOutputDisplay";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AIAssistantPanelProps {
  bookId: string;
  chapterId: string;
  /** TipTap editor instance for inserting/replacing text */
  editor: any;
  selectedText?: string;
  contextBefore?: string;
  onCollapse?: () => void;
  /** Legacy: project ID for generation requests */
  projectId?: string;
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

interface QuickActionDef {
  action: AIAction;
  labelKey: string;
  icon: string;
  /** Whether action requires text to be selected in the editor */
  requiresSelection: boolean;
  /** Tooltip text when selection is missing */
  selectionHint?: string;
  /** Keyboard shortcut label */
  shortcut?: string;
}

const QUICK_ACTIONS: QuickActionDef[] = [
  {
    action: "write",
    labelKey: "ai.write",
    icon: "\u270d\ufe0f",
    requiresSelection: false,
  },
  {
    action: "rewrite",
    labelKey: "ai.rewrite",
    icon: "\ud83d\udd04",
    requiresSelection: true,
    selectionHint: "Select text first",
  },
  {
    action: "expand",
    labelKey: "ai.expand",
    icon: "\ud83d\udcdd",
    requiresSelection: false,
  },
  {
    action: "shorten",
    labelKey: "ai.shorten",
    icon: "\u2702\ufe0f",
    requiresSelection: true,
    selectionHint: "Select text first",
  },
  {
    action: "continue",
    labelKey: "ai.continue",
    icon: "\u27a1\ufe0f",
    requiresSelection: false,
    shortcut: "Ctrl+Enter",
  },
  {
    action: "brainstorm",
    labelKey: "ai.brainstorm",
    icon: "\ud83d\udca1",
    requiresSelection: false,
  },
];

// ---------------------------------------------------------------------------
// Tone and length options
// ---------------------------------------------------------------------------

const TONE_OPTIONS = [
  { value: "match_profile", labelKey: "ai.toneMatchProfile" },
  { value: "more_formal", labelKey: "ai.toneFormal" },
  { value: "more_casual", labelKey: "ai.toneCasual" },
  { value: "more_authoritative", labelKey: "ai.toneAuthoritative" },
  { value: "more_conversational", labelKey: "ai.toneConversational" },
  { value: "humorous", labelKey: "ai.toneHumorous" },
  { value: "academic", labelKey: "ai.toneAcademic" },
];

const LENGTH_OPTIONS = [
  { value: "short", labelKey: "ai.lengthShort", description: "~1 paragraph" },
  {
    value: "medium",
    labelKey: "ai.lengthMedium",
    description: "~2-3 paragraphs",
  },
  { value: "long", labelKey: "ai.lengthLong", description: "~4-6 paragraphs" },
  {
    value: "custom",
    labelKey: "ai.lengthCustom",
    description: "Custom word count",
  },
];

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_INSTRUCTION_HISTORY = 10;
const TEXTAREA_MAX_ROWS = 4;
const TEXTAREA_LINE_HEIGHT = 20; // px per line

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AIAssistantPanel({
  bookId,
  chapterId,
  editor,
  selectedText,
  contextBefore,
  onCollapse,
  projectId,
  onInsertText,
  onReplaceSelection,
  readabilityScore,
  wordCount = 0,
  targetWordCount = 0,
  className,
}: AIAssistantPanelProps) {
  const t = useTranslations("writing");

  // -- State ---------------------------------------------------------------
  const [customInstruction, setCustomInstruction] = useState("");
  const [activeAction, setActiveAction] = useState<AIAction | null>(null);
  const [tone, setTone] = useState("match_profile");
  const [lengthOption, setLengthOption] = useState<string>("medium");
  const [customWordCount, setCustomWordCount] = useState<string>("500");
  const [styleProfile, setStyleProfile] = useState("default");
  const [selectionWarning, setSelectionWarning] = useState("");
  const [instructionHistory, setInstructionHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [brainstormSuggestions, setBrainstormSuggestions] = useState<string[]>(
    []
  );
  const [insertConfirmation, setInsertConfirmation] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // -- Hooks ---------------------------------------------------------------
  const {
    content: generatedContent,
    isStreaming,
    error,
    startGeneration,
    stopGeneration,
  } = useSSEGeneration();

  const { data: styleProfiles } = useStyleProfiles();

  // -- Derived values ------------------------------------------------------
  const effectiveProjectId = projectId || "";
  const effectiveLength =
    lengthOption === "custom"
      ? "medium"
      : (lengthOption as "short" | "medium" | "long");
  const hasSelection = !!selectedText;

  // -- Auto-resize textarea ------------------------------------------------
  const autoResizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = TEXTAREA_MAX_ROWS * TEXTAREA_LINE_HEIGHT + 16;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
    el.style.overflowY = el.scrollHeight > maxHeight ? "auto" : "hidden";
  }, []);

  useEffect(() => {
    autoResizeTextarea();
  }, [customInstruction, autoResizeTextarea]);

  // -- Parse brainstorm suggestions from generated content -----------------
  useEffect(() => {
    if (activeAction === "brainstorm" && generatedContent && !isStreaming) {
      const lines = generatedContent
        .replace(/<[^>]*>/g, "")
        .split(/\n/)
        .map((line) => line.replace(/^[\s\-\*\u2022\d.]+/, "").trim())
        .filter((line) => line.length > 5);
      if (lines.length > 0) {
        setBrainstormSuggestions(lines.slice(0, 5));
      }
    }
  }, [activeAction, generatedContent, isStreaming]);

  // -- Build generation request -------------------------------------------
  const buildRequest = useCallback(
    (action: AIAction, instruction: string): GenerateRequest => {
      const contextPayload: Record<string, unknown> = {
        book_id: bookId,
        chapter_id: chapterId,
        selected_text: selectedText || "",
        tone,
        length: effectiveLength,
      };

      if (action === "continue" && contextBefore) {
        const words = contextBefore.split(/\s+/);
        contextPayload.context_before = words.slice(-500).join(" ");
      }

      if (lengthOption === "custom" && customWordCount) {
        contextPayload.target_word_count = parseInt(customWordCount, 10);
      }

      return {
        generation_type: action,
        project_id: effectiveProjectId,
        style_profile_id:
          styleProfile !== "default" ? styleProfile : undefined,
        instructions: instruction,
        context: contextPayload,
        model_preference: "auto",
        stream: true,
        quality_checks: ["readability"],
      };
    },
    [
      bookId,
      chapterId,
      contextBefore,
      customWordCount,
      effectiveLength,
      effectiveProjectId,
      lengthOption,
      selectedText,
      styleProfile,
      tone,
    ]
  );

  // -- Handlers ------------------------------------------------------------

  const handleQuickAction = useCallback(
    (action: AIAction) => {
      if ((action === "rewrite" || action === "shorten") && !selectedText) {
        setSelectionWarning("Select text in the editor first");
        setTimeout(() => setSelectionWarning(""), 3000);
        return;
      }

      setActiveAction(action);
      setBrainstormSuggestions([]);

      if (action === "write") {
        setTimeout(() => textareaRef.current?.focus(), 50);
        return;
      }

      let instruction = customInstruction;
      if (!instruction) {
        switch (action) {
          case "rewrite":
            instruction =
              "Rewrite the selected text, improving clarity and flow.";
            break;
          case "expand":
            instruction = selectedText
              ? "Expand on the selected text with more detail."
              : "Expand the current paragraph with more detail and depth.";
            break;
          case "shorten":
            instruction =
              "Condense the selected text while preserving key meaning.";
            break;
          case "continue":
            instruction =
              "Continue writing from where the text left off, matching the existing style and tone.";
            break;
          case "brainstorm":
            instruction =
              "Generate 3-5 creative ideas as bullet points for what to write next.";
            break;
          default:
            instruction = `Perform ${action} on the selected text.`;
        }
      }

      const request = buildRequest(action, instruction);
      startGeneration(request);
    },
    [buildRequest, customInstruction, selectedText, startGeneration]
  );

  const handleCustomGenerate = useCallback(() => {
    if (!customInstruction.trim()) return;

    setInstructionHistory((prev) => {
      const filtered = prev.filter(
        (item) => item !== customInstruction.trim()
      );
      return [customInstruction.trim(), ...filtered].slice(
        0,
        MAX_INSTRUCTION_HISTORY
      );
    });
    setHistoryIndex(-1);

    const action = activeAction || "write";
    const request = buildRequest(action, customInstruction);
    startGeneration(request);
  }, [activeAction, buildRequest, customInstruction, startGeneration]);

  const handleBrainstormSelect = useCallback(
    (suggestion: string) => {
      setCustomInstruction(suggestion);
      setActiveAction("write");
      setBrainstormSuggestions([]);
      const request = buildRequest("write", suggestion);
      startGeneration(request);
    },
    [buildRequest, startGeneration]
  );

  const handleInsert = useCallback(() => {
    if (!generatedContent) return;

    if (editor) {
      editor.chain().focus().insertContent(generatedContent).run();
    } else {
      onInsertText?.(generatedContent);
    }

    setInsertConfirmation("Inserted!");
    setTimeout(() => setInsertConfirmation(""), 2000);
  }, [editor, generatedContent, onInsertText]);

  const handleReplace = useCallback(() => {
    if (!generatedContent) return;

    if (editor && selectedText) {
      editor
        .chain()
        .focus()
        .deleteSelection()
        .insertContent(generatedContent)
        .run();
    } else {
      onReplaceSelection?.(generatedContent);
    }

    setInsertConfirmation("Replaced!");
    setTimeout(() => setInsertConfirmation(""), 2000);
  }, [editor, generatedContent, onReplaceSelection, selectedText]);

  const handleRegenerate = useCallback(() => {
    if (activeAction) {
      const instruction =
        customInstruction ||
        `Perform ${activeAction} on the selected text.`;
      const request = buildRequest(activeAction, instruction);
      startGeneration(request);
    }
  }, [activeAction, buildRequest, customInstruction, startGeneration]);

  const handleEditRetry = useCallback(() => {
    if (instructionHistory.length > 0) {
      setCustomInstruction(instructionHistory[0]);
    }
    setTimeout(() => textareaRef.current?.focus(), 50);
  }, [instructionHistory]);

  // -- Keyboard shortcut: Ctrl+Enter for Continue -------------------------
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        handleQuickAction("continue");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleQuickAction]);

  // -- Textarea key handlers -----------------------------------------------
  const handleTextareaKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleCustomGenerate();
        return;
      }

      if (e.key === "ArrowUp" && instructionHistory.length > 0) {
        const cursorAtStart =
          textareaRef.current?.selectionStart === 0 &&
          textareaRef.current?.selectionEnd === 0;
        const isEmpty = customInstruction.trim() === "";
        if (cursorAtStart || isEmpty) {
          e.preventDefault();
          const newIdx = Math.min(
            historyIndex + 1,
            instructionHistory.length - 1
          );
          setHistoryIndex(newIdx);
          setCustomInstruction(instructionHistory[newIdx]);
        }
      }

      if (e.key === "ArrowDown" && historyIndex >= 0) {
        e.preventDefault();
        const newIdx = historyIndex - 1;
        if (newIdx < 0) {
          setHistoryIndex(-1);
          setCustomInstruction("");
        } else {
          setHistoryIndex(newIdx);
          setCustomInstruction(instructionHistory[newIdx]);
        }
      }
    },
    [customInstruction, handleCustomGenerate, historyIndex, instructionHistory]
  );

  // -- Readability helpers -------------------------------------------------
  const gradeLevel = readabilityScore?.flesch_kincaid_grade ?? 0;
  const gradeColor =
    gradeLevel <= 9
      ? "text-green-600"
      : gradeLevel <= 12
        ? "text-yellow-600"
        : "text-red-600";
  const gradeBg =
    gradeLevel <= 9
      ? "bg-green-500"
      : gradeLevel <= 12
        ? "bg-yellow-500"
        : "bg-red-500";

  const passivePct = readabilityScore?.passive_voice_pct ?? 0;
  const passiveColor =
    passivePct < 10
      ? "text-green-600"
      : passivePct <= 15
        ? "text-yellow-600"
        : "text-red-600";
  const passiveBg =
    passivePct < 10
      ? "bg-green-500"
      : passivePct <= 15
        ? "bg-yellow-500"
        : "bg-red-500";

  const wordProgress =
    targetWordCount > 0
      ? Math.min(Math.round((wordCount / targetWordCount) * 100), 100)
      : 0;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <TooltipProvider delayDuration={300}>
      <div
        className={cn(
          "flex flex-col h-full border-l bg-card w-80 overflow-y-auto",
          className
        )}
      >
        {/* ---- Header with collapse button ---- */}
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">
            {t("ai.title")}
          </h3>
          {onCollapse && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={onCollapse}
                  aria-label="Collapse AI panel"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>{t("ai.collapse")}</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* ---- Quick Actions (3x2 grid) ---- */}
        <div className="px-4 py-3 border-b space-y-2">
          <p className="text-xs font-medium text-foreground">
            {t("ai.quickActions")}
          </p>
          <div className="grid grid-cols-3 gap-2">
            {QUICK_ACTIONS.map(
              ({
                action,
                labelKey,
                icon,
                requiresSelection,
                selectionHint,
                shortcut,
              }) => {
                const needsWarning = requiresSelection && !hasSelection;
                const tooltipText = needsWarning
                  ? selectionHint || "Select text first"
                  : shortcut
                    ? `${t(labelKey)} (${shortcut})`
                    : t(labelKey);

                return (
                  <Tooltip key={action}>
                    <TooltipTrigger asChild>
                      <Button
                        variant={
                          activeAction === action ? "default" : "outline"
                        }
                        size="sm"
                        disabled={isStreaming}
                        onClick={() => handleQuickAction(action)}
                        className={cn(
                          "text-xs gap-1",
                          needsWarning && "opacity-60"
                        )}
                      >
                        <span>{icon}</span>
                        {t(labelKey)}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p>{tooltipText}</p>
                    </TooltipContent>
                  </Tooltip>
                );
              }
            )}
          </div>

          {selectionWarning && (
            <p className="text-xs text-amber-600 mt-1 animate-in fade-in">
              {selectionWarning}
            </p>
          )}

          {isStreaming && (
            <Button
              variant="destructive"
              size="sm"
              className="w-full text-xs mt-1"
              onClick={stopGeneration}
            >
              {t("ai.stopGeneration")}
            </Button>
          )}
        </div>

        {/* ---- Instruction Input ---- */}
        <div className="px-4 py-3 border-b space-y-2">
          <p className="text-xs font-medium text-foreground">
            {t("ai.instruction")}
          </p>
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={customInstruction}
              onChange={(e) => {
                setCustomInstruction(e.target.value);
                setHistoryIndex(-1);
              }}
              onKeyDown={handleTextareaKeyDown}
              placeholder={t("ai.instructionPlaceholder")}
              rows={1}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
                "ring-offset-background placeholder:text-muted-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                "min-h-[40px] resize-none pr-8"
              )}
              style={{ overflow: "hidden" }}
            />
            {customInstruction && (
              <button
                type="button"
                onClick={() => {
                  setCustomInstruction("");
                  textareaRef.current?.focus();
                }}
                className="absolute top-2 right-2 text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Clear instruction"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              className="flex-1 text-xs"
              disabled={isStreaming || !customInstruction.trim()}
              onClick={handleCustomGenerate}
            >
              {t("ai.generate")} {"\u2192"}
            </Button>
            {instructionHistory.length > 0 && (
              <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                {"\u2191"} history ({instructionHistory.length})
              </span>
            )}
          </div>
        </div>

        {/* ---- AI Output ---- */}
        <div className="px-4 py-3 border-b">
          <AIOutputDisplay
            content={generatedContent}
            isStreaming={isStreaming}
            error={error}
            hasSelection={hasSelection}
            onInsert={handleInsert}
            onReplace={handleReplace}
            onRegenerate={handleRegenerate}
            onEditRetry={handleEditRetry}
          />

          {/* Insert / Replace confirmation message */}
          {insertConfirmation && (
            <div className="mt-2 text-xs text-green-600 font-medium flex items-center gap-1 animate-in fade-in">
              <span>{"\u2705"}</span> {insertConfirmation}
            </div>
          )}

          {/* Brainstorm suggestions (clickable ideas) */}
          {brainstormSuggestions.length > 0 && !isStreaming && (
            <div className="mt-3 space-y-1.5">
              <p className="text-xs font-medium text-muted-foreground">
                Click an idea to start writing:
              </p>
              {brainstormSuggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleBrainstormSelect(suggestion)}
                  className={cn(
                    "w-full text-left text-xs px-3 py-2 rounded-md border",
                    "bg-muted/30 hover:bg-muted/60 hover:border-primary/30",
                    "transition-colors cursor-pointer"
                  )}
                >
                  <span className="text-muted-foreground mr-1.5">
                    {"\ud83d\udca1"}
                  </span>
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ---- Style Settings ---- */}
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
                <SelectValue
                  placeholder={t("ai.styleProfilePlaceholder")}
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">
                  {t("ai.styleProfileDefault")}
                </SelectItem>
                {styleProfiles?.map((profile) => (
                  <SelectItem key={profile.id} value={profile.id}>
                    {profile.name}
                  </SelectItem>
                ))}
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
              value={lengthOption}
              onValueChange={(v) => setLengthOption(v)}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LENGTH_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {t(opt.labelKey)}{" "}
                    <span className="text-muted-foreground">
                      ({opt.description})
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Custom word count input */}
            {lengthOption === "custom" && (
              <div className="flex items-center gap-2 mt-1.5">
                <Input
                  type="number"
                  min={50}
                  max={10000}
                  step={50}
                  value={customWordCount}
                  onChange={(e) => setCustomWordCount(e.target.value)}
                  className="h-7 text-xs w-24"
                  placeholder="500"
                />
                <span className="text-xs text-muted-foreground">words</span>
              </div>
            )}
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
                <span
                  className={cn(
                    "flex items-center gap-1.5 font-medium",
                    gradeColor
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-2 w-2 rounded-full",
                      gradeBg
                    )}
                  />
                  Grade{" "}
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
                  <span
                    className={cn(
                      "flex items-center gap-1.5 font-medium",
                      passiveColor
                    )}
                  >
                    <span
                      className={cn(
                        "inline-block h-2 w-2 rounded-full",
                        passiveBg
                      )}
                    />
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
                    {readabilityScore.avg_words_per_sentence.toFixed(1)}{" "}
                    {t("ai.stats.words")}
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
          <Button
            variant="outline"
            size="sm"
            className="w-full text-xs gap-2"
          >
            <Mic className="h-3.5 w-3.5" />
            {t("ai.startDictation")}
          </Button>
        </div>
      </div>
    </TooltipProvider>
  );
}
