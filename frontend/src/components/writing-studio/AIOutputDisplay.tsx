"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AIOutputDisplayProps {
  content: string;
  isStreaming: boolean;
  action: string;
  originalWordCount?: number; // for shorten comparison
  error?: string | null;
  onInsert: () => void;
  onReplace: () => void;
  onRegenerate: () => void;
  onEditPrompt: () => void;
  onSelectIdea?: (idea: string) => void; // for ideas action
  hasSelection: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Count words in a plain-text or HTML string (strips tags first). */
function countWords(text: string): number {
  const plain = text.replace(/<[^>]*>/g, " ").trim();
  if (!plain) return 0;
  return plain.split(/\s+/).filter(Boolean).length;
}

/** Extract bullet-point ideas from generated content (strips leading markers). */
function extractIdeas(html: string): string[] {
  // Try to find <li> elements first (markdown rendered as HTML list)
  const liMatches = html.match(/<li[^>]*>([\s\S]*?)<\/li>/gi);
  if (liMatches && liMatches.length > 0) {
    return liMatches
      .map((li) => li.replace(/<[^>]*>/g, "").trim())
      .filter(Boolean);
  }

  // Fall back to splitting on newlines and looking for bullet-like prefixes
  const plain = html.replace(/<[^>]*>/g, "\n");
  return plain
    .split("\n")
    .map((line) => line.replace(/^[\s\-*\u2022\d.]+/, "").trim())
    .filter((line) => line.length > 3);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AIOutputDisplay({
  content,
  isStreaming,
  action,
  originalWordCount,
  error = null,
  onInsert,
  onReplace,
  onRegenerate,
  onEditPrompt,
  onSelectIdea,
  hasSelection,
}: AIOutputDisplayProps) {
  const t = useTranslations("writing");
  const [insertedMsg, setInsertedMsg] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom during streaming
  useEffect(() => {
    if (isStreaming && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content, isStreaming]);

  // Word counts
  const generatedWordCount = useMemo(() => countWords(content), [content]);

  const shortenStats = useMemo(() => {
    if (action !== "shorten" || !originalWordCount || !generatedWordCount) {
      return null;
    }
    const diff = originalWordCount - generatedWordCount;
    const pct =
      originalWordCount > 0
        ? Math.round((diff / originalWordCount) * 100)
        : 0;
    return { from: originalWordCount, to: generatedWordCount, pct };
  }, [action, originalWordCount, generatedWordCount]);

  // Ideas extraction for brainstorm/ideas action
  const ideas = useMemo(() => {
    if (
      (action === "brainstorm" || action === "ideas") &&
      content &&
      !isStreaming
    ) {
      return extractIdeas(content);
    }
    return [];
  }, [action, content, isStreaming]);

  const isIdeasAction = action === "brainstorm" || action === "ideas";

  // -------------------------------------------------------------------------
  // Action handlers
  // -------------------------------------------------------------------------

  const handleInsertWithConfirm = () => {
    onInsert();
    setInsertedMsg(true);
    setTimeout(() => setInsertedMsg(false), 2000);
  };

  const handleReplaceWithConfirm = () => {
    onReplace();
    setInsertedMsg(true);
    setTimeout(() => setInsertedMsg(false), 2000);
  };

  // -------------------------------------------------------------------------
  // Error state
  // -------------------------------------------------------------------------

  if (error) {
    return (
      <div className="rounded-md border border-red-300 bg-red-50 p-3">
        <p className="text-xs font-medium text-red-700">
          {t("ai.output.error")}
        </p>
        <p className="mt-1 text-xs text-red-600">{error}</p>
        <div className="mt-2 flex gap-2">
          <Button variant="outline" size="sm" onClick={onRegenerate}>
            Retry
          </Button>
          <Button variant="ghost" size="sm" onClick={onEditPrompt}>
            {t("ai.output.editRetry")}
          </Button>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Empty state
  // -------------------------------------------------------------------------

  if (!content && !isStreaming) {
    return (
      <div className="rounded-md border border-dashed border-muted-foreground/30 bg-muted/10 p-4 text-center">
        <p className="text-xs text-muted-foreground italic">
          AI output will appear here
        </p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Streaming / Complete state
  // -------------------------------------------------------------------------

  return (
    <div className="space-y-2">
      {/* Streaming indicator */}
      {isStreaming && (
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-muted-foreground">
            {t("ai.output.generating")}
          </span>
        </div>
      )}

      {/* Generated content */}
      <div
        ref={scrollRef}
        className={cn(
          "rounded-md border bg-muted/30 p-3 text-sm font-serif overflow-y-auto",
          "prose prose-sm dark:prose-invert max-w-none",
          "max-h-[300px]",
          isStreaming && "border-green-300"
        )}
      >
        {content ? (
          <>
            {/* For ideas/brainstorm: render as clickable bullets */}
            {isIdeasAction && !isStreaming && ideas.length > 0 ? (
              <ul className="space-y-1.5 list-none p-0 m-0">
                {ideas.map((idea, idx) => (
                  <li key={idx}>
                    <button
                      type="button"
                      onClick={() => onSelectIdea?.(idea)}
                      className={cn(
                        "w-full text-left px-2 py-1.5 rounded-md text-xs",
                        "bg-muted/50 hover:bg-primary/10 hover:text-primary",
                        "transition-colors cursor-pointer border border-transparent",
                        "hover:border-primary/20"
                      )}
                    >
                      <span className="mr-1.5 text-muted-foreground">
                        {"\u2022"}
                      </span>
                      {idea}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div dangerouslySetInnerHTML={{ __html: content }} />
            )}

            {/* Blinking cursor while streaming */}
            {isStreaming && (
              <span
                className="inline-block w-[2px] h-4 bg-foreground ml-0.5 align-text-bottom animate-blink"
                aria-hidden="true"
              />
            )}
          </>
        ) : (
          isStreaming && (
            <div className="flex items-center gap-1">
              <span className="text-muted-foreground text-xs">
                {t("ai.output.waiting")}
              </span>
              <span
                className="inline-block w-[2px] h-4 bg-foreground animate-blink"
                aria-hidden="true"
              />
            </div>
          )
        )}
      </div>

      {/* Word count footer */}
      <div className="flex items-center justify-between">
        {generatedWordCount > 0 && (
          <p className="text-[11px] text-muted-foreground">
            Generated: {generatedWordCount} words
          </p>
        )}

        {/* Shorten comparison stats */}
        {shortenStats && !isStreaming && (
          <p className="text-[11px] text-muted-foreground font-medium">
            Shortened from {shortenStats.from} to {shortenStats.to} words (-
            {shortenStats.pct}%)
          </p>
        )}
      </div>

      {/* Ideas hint */}
      {isIdeasAction && !isStreaming && ideas.length > 0 && (
        <p className="text-[11px] text-muted-foreground italic">
          Click an idea to use it as a writing prompt
        </p>
      )}

      {/* Toast message */}
      {insertedMsg && (
        <div className="text-xs text-green-600 font-medium flex items-center gap-1 justify-center py-1">
          <span>{"\u2705"}</span> Inserted!
        </div>
      )}

      {/* Action buttons (shown when generation is complete) */}
      {!isStreaming && content && !insertedMsg && (
        <div className="flex flex-wrap gap-2 items-center">
          <Button
            variant="default"
            size="sm"
            className="text-xs gap-1"
            onClick={handleInsertWithConfirm}
          >
            <span>{"\uD83D\uDCCB"}</span>
            Insert at Cursor
          </Button>

          <Button
            variant="secondary"
            size="sm"
            className="text-xs gap-1"
            disabled={!hasSelection}
            onClick={handleReplaceWithConfirm}
            title={
              !hasSelection ? "Select text in the editor first" : undefined
            }
          >
            <span>{"\uD83D\uDD04"}</span>
            Replace Selection
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="text-xs gap-1"
            onClick={onRegenerate}
          >
            <span>{"\uD83D\uDD03"}</span>
            Regenerate
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="text-xs gap-1"
            onClick={onEditPrompt}
          >
            <span>{"\u270F\uFE0F"}</span>
            Edit Prompt
          </Button>
        </div>
      )}
    </div>
  );
}
