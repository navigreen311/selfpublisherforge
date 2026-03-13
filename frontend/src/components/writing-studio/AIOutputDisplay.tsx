"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AIOutputDisplayProps {
  content: string;
  isStreaming: boolean;
  error: string | null;
  hasSelection: boolean;
  onInsert: () => void;
  onReplace: () => void;
  onRegenerate: () => void;
  onEditRetry: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AIOutputDisplay({
  content,
  isStreaming,
  error,
  hasSelection,
  onInsert,
  onReplace,
  onRegenerate,
  onEditRetry,
}: AIOutputDisplayProps) {
  const t = useTranslations("writing");
  const [insertedMsg, setInsertedMsg] = useState(false);

  const handleInsertWithConfirm = () => {
    onInsert();
    setInsertedMsg(true);
    setTimeout(() => setInsertedMsg(false), 2000);
  };

  if (error) {
    return (
      <div className="rounded-md border border-red-300 bg-red-50 p-3">
        <p className="text-xs font-medium text-red-700">
          {t("ai.output.error")}
        </p>
        <p className="mt-1 text-xs text-red-600">{error}</p>
        <div className="mt-2 flex gap-2">
          <Button variant="outline" size="sm" onClick={onRegenerate}>
            {t("ai.output.regenerate")}
          </Button>
          <Button variant="outline" size="sm" onClick={onEditRetry}>
            {t("ai.output.editRetry")}
          </Button>
        </div>
      </div>
    );
  }

  if (!content && !isStreaming) {
    return null;
  }

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
      {content ? (
        <div
          className={cn(
            "rounded-md border bg-muted/30 p-3 text-sm font-serif max-h-64 overflow-y-auto prose prose-sm",
            isStreaming && "border-green-300"
          )}
          dangerouslySetInnerHTML={{ __html: content }}
        />
      ) : (
        isStreaming && (
          <div
            className={cn(
              "rounded-md border bg-muted/30 p-3 text-sm font-serif max-h-64 overflow-y-auto",
              "border-green-300"
            )}
          >
            <span className="text-muted-foreground">
              {t("ai.output.waiting")}
            </span>
          </div>
        )
      )}

      {/* Action buttons (shown when generation is complete) */}
      {!isStreaming && content && (
        <div className="flex flex-wrap gap-2 items-center">
          <Button variant="default" size="sm" onClick={handleInsertWithConfirm}>
            {t("ai.output.insertAtCursor")}
          </Button>
          {hasSelection && (
            <Button variant="secondary" size="sm" onClick={onReplace}>
              {t("ai.output.replaceSelection")}
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={onRegenerate}>
            {t("ai.output.regenerate")}
          </Button>
          <Button variant="ghost" size="sm" onClick={onEditRetry}>
            {t("ai.output.editRetry")}
          </Button>
          {insertedMsg && (
            <div className="text-xs text-green-600 font-medium flex items-center gap-1">
              <span>{"\u2713"}</span> Inserted!
            </div>
          )}
        </div>
      )}
    </div>
  );
}
