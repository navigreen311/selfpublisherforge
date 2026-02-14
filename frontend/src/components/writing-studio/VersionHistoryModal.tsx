"use client";

import { useState, useMemo, useCallback } from "react";
import { useTranslations } from "@/hooks/use-translations";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  useChapterVersions,
  useRestoreChapterVersion,
} from "@/modules/writing/hooks";
import type { ChapterVersion } from "@/modules/writing/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface VersionHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  bookId: string;
  chapterId: string;
  chapterTitle: string;
  onRestore: (content: any) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Format a timestamp into a human-readable string:
 *   - Today: "Today, 10:32 AM"
 *   - Yesterday: "Yesterday, 4:30 PM"
 *   - Older: "Feb 11, 2:00 PM"
 */
function formatTimestamp(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();

  const timeStr = date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  // Check if the date is today
  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (isToday) {
    return `Today, ${timeStr}`;
  }

  // Check if the date is yesterday
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const isYesterday =
    date.getFullYear() === yesterday.getFullYear() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getDate() === yesterday.getDate();

  if (isYesterday) {
    return `Yesterday, ${timeStr}`;
  }

  // Older dates: "Feb 11, 2:00 PM"
  const monthDay = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  return `${monthDay}, ${timeStr}`;
}

/**
 * Compute the word count difference string between the current version
 * and the previous version (the one after it in the chronologically
 * descending list).
 */
function wordCountDiff(
  currentWordCount: number,
  previousWordCount: number | null
): string | null {
  if (previousWordCount === null) return null;
  const diff = currentWordCount - previousWordCount;
  if (diff === 0) return null;
  if (diff > 0) return `+${diff} words`;
  return `${diff} words`;
}

/**
 * Attempt to render TipTap JSON content or plain HTML as formatted HTML.
 * If the content is valid TipTap JSON, we do a simple conversion.
 * Otherwise we render it as-is (assuming it is HTML).
 */
function renderContentPreview(content: string): string {
  if (!content) return "<p class='text-muted-foreground italic'>Empty version</p>";

  // Try to parse as TipTap JSON
  try {
    const parsed = JSON.parse(content);
    if (parsed && parsed.type === "doc" && Array.isArray(parsed.content)) {
      return tiptapToHtml(parsed);
    }
  } catch {
    // Not JSON, treat as HTML
  }

  return content;
}

/**
 * Minimal TipTap JSON-to-HTML converter for preview purposes.
 * Handles paragraphs, headings, blockquotes, bullet/ordered lists,
 * horizontal rules, and inline marks (bold, italic, underline, strike, code, link).
 */
function tiptapToHtml(doc: any): string {
  if (!doc || !doc.content) return "";

  return doc.content.map((node: any) => nodeToHtml(node)).join("");
}

function nodeToHtml(node: any): string {
  switch (node.type) {
    case "paragraph":
      return `<p>${inlineContent(node)}</p>`;
    case "heading": {
      const level = node.attrs?.level ?? 1;
      return `<h${level}>${inlineContent(node)}</h${level}>`;
    }
    case "blockquote":
      return `<blockquote>${(node.content || []).map(nodeToHtml).join("")}</blockquote>`;
    case "bulletList":
      return `<ul>${(node.content || []).map(nodeToHtml).join("")}</ul>`;
    case "orderedList":
      return `<ol>${(node.content || []).map(nodeToHtml).join("")}</ol>`;
    case "listItem":
      return `<li>${(node.content || []).map(nodeToHtml).join("")}</li>`;
    case "horizontalRule":
      return "<hr />";
    case "hardBreak":
      return "<br />";
    case "image":
      return `<img src="${node.attrs?.src || ""}" alt="${node.attrs?.alt || ""}" />`;
    case "codeBlock":
      return `<pre><code>${escapeHtml(textContent(node))}</code></pre>`;
    default:
      // Fallback for unknown node types
      if (node.content) {
        return (node.content as any[]).map(nodeToHtml).join("");
      }
      if (node.text) {
        return applyMarks(node.text, node.marks);
      }
      return "";
  }
}

function inlineContent(node: any): string {
  if (!node.content) return "";
  return (node.content as any[])
    .map((child: any) => {
      if (child.type === "text") {
        return applyMarks(child.text || "", child.marks);
      }
      if (child.type === "hardBreak") return "<br />";
      return nodeToHtml(child);
    })
    .join("");
}

function applyMarks(text: string, marks?: any[]): string {
  if (!marks || marks.length === 0) return escapeHtml(text);
  let result = escapeHtml(text);
  for (const mark of marks) {
    switch (mark.type) {
      case "bold":
        result = `<strong>${result}</strong>`;
        break;
      case "italic":
        result = `<em>${result}</em>`;
        break;
      case "underline":
        result = `<u>${result}</u>`;
        break;
      case "strike":
        result = `<s>${result}</s>`;
        break;
      case "code":
        result = `<code>${result}</code>`;
        break;
      case "link":
        result = `<a href="${mark.attrs?.href || "#"}" target="_blank" rel="noopener">${result}</a>`;
        break;
    }
  }
  return result;
}

function textContent(node: any): string {
  if (node.text) return node.text;
  if (!node.content) return "";
  return (node.content as any[]).map(textContent).join("");
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function VersionHistoryModal({
  isOpen,
  onClose,
  bookId,
  chapterId,
  chapterTitle,
  onRestore,
}: VersionHistoryModalProps) {
  const t = useTranslations("writing");

  const [selectedVersion, setSelectedVersion] =
    useState<ChapterVersion | null>(null);
  const [confirmRestore, setConfirmRestore] =
    useState<ChapterVersion | null>(null);
  const [restoring, setRestoring] = useState(false);

  const { data: versions = [], isLoading } = useChapterVersions(
    bookId,
    chapterId
  );
  const restoreMutation = useRestoreChapterVersion(bookId, chapterId);

  // Versions are assumed sorted descending by created_at (newest first).
  // The first entry is the current version.

  const previewHtml = useMemo(() => {
    if (!selectedVersion) return null;
    return renderContentPreview(selectedVersion.content);
  }, [selectedVersion]);

  const handleRestoreConfirm = useCallback(async () => {
    if (!confirmRestore) return;
    setRestoring(true);
    try {
      const result = await restoreMutation.mutateAsync(confirmRestore.id);
      onRestore(result.content);
      setConfirmRestore(null);
      setSelectedVersion(null);
      onClose();
    } catch {
      // Error handled by mutation -- could add toast here
    } finally {
      setRestoring(false);
    }
  }, [confirmRestore, restoreMutation, onRestore, onClose]);

  const handleOpenChange = useCallback(
    (open: boolean) => {
      if (!open) {
        setSelectedVersion(null);
        setConfirmRestore(null);
        onClose();
      }
    },
    [onClose]
  );

  return (
    <>
      <Dialog open={isOpen} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>{t("versionHistory.title")}</DialogTitle>
            {chapterTitle && (
              <p className="text-sm text-muted-foreground mt-1">
                {chapterTitle}
              </p>
            )}
          </DialogHeader>

          {/* Version list */}
          <div className="flex-1 overflow-y-auto min-h-0 space-y-0.5 py-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <span className="ml-2 text-sm text-muted-foreground">
                  Loading versions...
                </span>
              </div>
            ) : versions.length === 0 ? (
              <div className="text-center py-12 px-4">
                <p className="text-sm text-muted-foreground">
                  {t("versionHistory.emptyState")}
                </p>
              </div>
            ) : (
              versions.map((version, idx) => {
                const isCurrent = idx === 0;
                const isSelected = selectedVersion?.id === version.id;
                const prevVersion =
                  idx < versions.length - 1 ? versions[idx + 1] : null;
                const diff = wordCountDiff(
                  version.word_count,
                  prevVersion ? prevVersion.word_count : null
                );

                return (
                  <button
                    key={version.id}
                    type="button"
                    onClick={() => setSelectedVersion(version)}
                    className={cn(
                      "flex items-center justify-between w-full px-4 py-3 rounded-md cursor-pointer transition-colors text-left",
                      isSelected
                        ? "bg-accent ring-1 ring-accent-foreground/10"
                        : "hover:bg-accent/50"
                    )}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {/* Version indicator circle */}
                      <span
                        className={cn(
                          "inline-flex items-center justify-center h-3 w-3 rounded-full flex-shrink-0",
                          isCurrent
                            ? "bg-primary"
                            : "border-2 border-muted-foreground/40 bg-transparent"
                        )}
                        aria-hidden="true"
                      />

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate">
                            {formatTimestamp(version.created_at)}
                          </p>
                          {isCurrent && (
                            <span className="text-xs text-primary font-medium whitespace-nowrap">
                              ({t("versionHistory.current")})
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <p className="text-xs text-muted-foreground">
                            {version.word_count.toLocaleString()} words
                          </p>
                          {diff && (
                            <span
                              className={cn(
                                "text-xs font-medium",
                                diff.startsWith("+")
                                  ? "text-green-600 dark:text-green-400"
                                  : "text-red-600 dark:text-red-400"
                              )}
                            >
                              {diff}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Restore button (non-current versions only) */}
                    {!isCurrent && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs ml-2 flex-shrink-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmRestore(version);
                        }}
                        disabled={restoring}
                      >
                        {t("versionHistory.restore")}
                      </Button>
                    )}
                  </button>
                );
              })
            )}
          </div>

          {/* Preview pane */}
          {selectedVersion && previewHtml && (
            <div className="border-t pt-3 flex flex-col min-h-0">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-muted-foreground">
                  Preview &mdash; {formatTimestamp(selectedVersion.created_at)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {selectedVersion.word_count.toLocaleString()} words
                </p>
              </div>
              <div
                className="flex-1 overflow-y-auto max-h-48 rounded-md border bg-muted/30 p-4"
              >
                <div
                  className="text-sm prose prose-sm max-w-none dark:prose-invert"
                  dangerouslySetInnerHTML={{ __html: previewHtml }}
                />
              </div>
            </div>
          )}

          {/* Hint text */}
          {!selectedVersion && versions.length > 0 && (
            <p className="text-xs text-muted-foreground text-center pt-2">
              {t("versionHistory.preview")}
            </p>
          )}

          {/* Footer */}
          <DialogFooter className="mt-2 gap-2">
            <Button variant="outline" onClick={onClose}>
              {t("versionHistory.close")}
            </Button>
            {selectedVersion &&
              versions.length > 0 &&
              selectedVersion.id !== versions[0]?.id && (
                <Button
                  onClick={() => setConfirmRestore(selectedVersion)}
                  disabled={restoring}
                >
                  {restoring
                    ? t("versionHistory.restoring")
                    : t("versionHistory.restoreSelected")}
                </Button>
              )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Restore confirmation dialog */}
      <AlertDialog
        open={!!confirmRestore}
        onOpenChange={(open) => {
          if (!open) setConfirmRestore(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t("versionHistory.confirmTitle")}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t("versionHistory.confirmDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={restoring}>
              {t("versionHistory.cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRestoreConfirm}
              disabled={restoring}
            >
              {restoring
                ? t("versionHistory.restoring")
                : t("versionHistory.restore")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
