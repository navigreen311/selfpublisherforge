"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { Editor } from "@tiptap/react";
import {
  X,
  ChevronUp,
  ChevronDown,
  CaseSensitive,
  Regex,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FindReplaceBarProps {
  editor: Editor | null;
  isOpen: boolean;
  showReplace: boolean;
  onClose: () => void;
}

interface SearchMatch {
  from: number;
  to: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Walk the TipTap document and collect all positions where `query` matches.
 * Returns an array of { from, to } positions in document coordinates.
 */
function findMatchesInDoc(
  editor: Editor,
  query: string,
  caseSensitive: boolean,
  useRegex: boolean
): SearchMatch[] {
  if (!query) return [];

  const matches: SearchMatch[] = [];
  const doc = editor.state.doc;

  try {
    const pattern = useRegex
      ? query
      : query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const flags = caseSensitive ? "g" : "gi";
    const regex = new RegExp(pattern, flags);

    doc.descendants((node, pos) => {
      if (!node.isText || !node.text) return;

      let match: RegExpExecArray | null;
      regex.lastIndex = 0;
      while ((match = regex.exec(node.text)) !== null) {
        const from = pos + match.index;
        const to = from + match[0].length;
        matches.push({ from, to });
      }
    });
  } catch {
    // Invalid regex — silently return no matches
  }

  return matches;
}

// ---------------------------------------------------------------------------
// Decoration helpers — apply highlight marks via editor commands
// ---------------------------------------------------------------------------

/**
 * Clear all search highlights from the editor by removing highlight marks.
 */
function clearHighlights(editor: Editor) {
  const markType = editor.schema.marks.highlight;
  if (!markType) return;

  const { tr } = editor.state;
  tr.removeMark(0, editor.state.doc.content.size, markType);
  editor.view.dispatch(tr);
}

/**
 * Apply visual search highlights. All matches get a yellow highlight;
 * the current match gets an orange highlight.
 */
function applyHighlights(
  editor: Editor,
  matches: SearchMatch[],
  currentIndex: number
) {
  const markType = editor.schema.marks.highlight;
  if (!markType) return;

  const { tr } = editor.state;

  // First clear existing highlights
  tr.removeMark(0, editor.state.doc.content.size, markType);

  // Apply yellow for all matches, orange for current match
  matches.forEach((m, i) => {
    const color = i === currentIndex ? "#fb923c" : "#fde047"; // orange-400 : yellow-300
    tr.addMark(m.from, m.to, markType.create({ color }));
  });

  editor.view.dispatch(tr);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function FindReplaceBar({
  editor,
  isOpen,
  showReplace,
  onClose,
}: FindReplaceBarProps) {
  const [findQuery, setFindQuery] = useState("");
  const [replaceQuery, setReplaceQuery] = useState("");
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [useRegex, setUseRegex] = useState(false);
  const [matches, setMatches] = useState<SearchMatch[]>([]);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);

  const findInputRef = useRef<HTMLInputElement>(null);

  // ---------------------------------------------------------------------------
  // Focus the find input when bar opens
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (isOpen && findInputRef.current) {
      findInputRef.current.focus();
      findInputRef.current.select();
    }
  }, [isOpen]);

  // ---------------------------------------------------------------------------
  // Search logic — recalculate matches when query/options change
  // ---------------------------------------------------------------------------
  const performSearch = useCallback(() => {
    if (!editor || !findQuery) {
      setMatches([]);
      setCurrentMatchIndex(0);
      if (editor) clearHighlights(editor);
      return;
    }

    const found = findMatchesInDoc(editor, findQuery, caseSensitive, useRegex);
    setMatches(found);

    // Keep current index in bounds
    const idx =
      found.length > 0
        ? Math.min(currentMatchIndex, found.length - 1)
        : 0;
    setCurrentMatchIndex(idx);

    if (found.length > 0) {
      applyHighlights(editor, found, idx);
    } else {
      clearHighlights(editor);
    }
  }, [editor, findQuery, caseSensitive, useRegex, currentMatchIndex]);

  useEffect(() => {
    performSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [findQuery, caseSensitive, useRegex]);

  // Also refresh on editor content changes
  useEffect(() => {
    if (!editor) return;

    const handleUpdate = () => {
      if (findQuery) {
        const found = findMatchesInDoc(
          editor,
          findQuery,
          caseSensitive,
          useRegex
        );
        setMatches(found);
        if (found.length === 0) {
          setCurrentMatchIndex(0);
          clearHighlights(editor);
        }
      }
    };

    editor.on("update", handleUpdate);
    return () => {
      editor.off("update", handleUpdate);
    };
  }, [editor, findQuery, caseSensitive, useRegex]);

  // ---------------------------------------------------------------------------
  // Navigate matches
  // ---------------------------------------------------------------------------
  const goToMatch = useCallback(
    (index: number) => {
      if (!editor || matches.length === 0) return;

      const safeIndex =
        ((index % matches.length) + matches.length) % matches.length;
      setCurrentMatchIndex(safeIndex);
      applyHighlights(editor, matches, safeIndex);

      // Scroll the match into view
      const match = matches[safeIndex];
      editor.commands.setTextSelection({ from: match.from, to: match.to });
      editor.commands.scrollIntoView();
    },
    [editor, matches]
  );

  const goToNextMatch = useCallback(() => {
    goToMatch(currentMatchIndex + 1);
  }, [goToMatch, currentMatchIndex]);

  const goToPrevMatch = useCallback(() => {
    goToMatch(currentMatchIndex - 1);
  }, [goToMatch, currentMatchIndex]);

  // ---------------------------------------------------------------------------
  // Replace
  // ---------------------------------------------------------------------------
  const replaceCurrent = useCallback(() => {
    if (!editor || matches.length === 0) return;

    const match = matches[currentMatchIndex];
    if (!match) return;

    editor
      .chain()
      .focus()
      .setTextSelection({ from: match.from, to: match.to })
      .run();
    editor.chain().focus().insertContent(replaceQuery).run();

    // Re-search after replacement
    setTimeout(() => {
      const found = findMatchesInDoc(
        editor,
        findQuery,
        caseSensitive,
        useRegex
      );
      setMatches(found);
      const nextIndex =
        found.length > 0
          ? Math.min(currentMatchIndex, found.length - 1)
          : 0;
      setCurrentMatchIndex(nextIndex);
      if (found.length > 0) {
        applyHighlights(editor, found, nextIndex);
      } else {
        clearHighlights(editor);
      }
    }, 10);
  }, [
    editor,
    matches,
    currentMatchIndex,
    replaceQuery,
    findQuery,
    caseSensitive,
    useRegex,
  ]);

  const replaceAll = useCallback(() => {
    if (!editor || matches.length === 0) return;

    // Replace from end to start to preserve positions
    const sortedMatches = [...matches].sort((a, b) => b.from - a.from);

    editor.chain().focus().run();
    const { tr } = editor.state;

    sortedMatches.forEach((match) => {
      tr.replaceWith(
        match.from,
        match.to,
        editor.state.schema.text(replaceQuery)
      );
    });

    editor.view.dispatch(tr);

    // Clear all search state
    setMatches([]);
    setCurrentMatchIndex(0);
    clearHighlights(editor);
  }, [editor, matches, replaceQuery]);

  // ---------------------------------------------------------------------------
  // Close handler
  // ---------------------------------------------------------------------------
  const handleClose = useCallback(() => {
    if (editor) {
      clearHighlights(editor);
    }
    setFindQuery("");
    setReplaceQuery("");
    setMatches([]);
    setCurrentMatchIndex(0);
    onClose();
  }, [editor, onClose]);

  // ---------------------------------------------------------------------------
  // Keyboard: Escape to close, Enter to next, Shift+Enter to prev
  // ---------------------------------------------------------------------------
  const handleFindKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
      } else if (e.key === "Enter" && e.shiftKey) {
        e.preventDefault();
        goToPrevMatch();
      } else if (e.key === "Enter") {
        e.preventDefault();
        goToNextMatch();
      }
    },
    [handleClose, goToNextMatch, goToPrevMatch]
  );

  const handleReplaceKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
      } else if (e.key === "Enter") {
        e.preventDefault();
        replaceCurrent();
      }
    },
    [handleClose, replaceCurrent]
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (!isOpen) return null;

  return (
    <div
      className={cn(
        "border-b bg-card px-3 py-2 shadow-sm",
        "animate-in slide-in-from-top-2 duration-200"
      )}
      role="search"
      aria-label="Find and replace"
    >
      {/* Find row */}
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium text-muted-foreground w-14 shrink-0">
          Find:
        </label>
        <input
          ref={findInputRef}
          type="text"
          value={findQuery}
          onChange={(e) => setFindQuery(e.target.value)}
          onKeyDown={handleFindKeyDown}
          placeholder="Search..."
          className={cn(
            "flex-1 max-w-xs rounded-md border border-input bg-background px-2 py-1 text-sm",
            "focus:outline-none focus:ring-1 focus:ring-ring",
            "placeholder:text-muted-foreground",
            findQuery && matches.length === 0 && "border-destructive"
          )}
          aria-label="Search text"
        />

        {/* Case sensitive toggle */}
        <button
          type="button"
          onClick={() => setCaseSensitive((prev) => !prev)}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1.5 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            caseSensitive &&
              "bg-accent text-accent-foreground ring-1 ring-ring"
          )}
          title="Case sensitive (Aa)"
          aria-pressed={caseSensitive}
          aria-label="Toggle case sensitivity"
        >
          <CaseSensitive className="h-4 w-4" />
        </button>

        {/* Regex toggle */}
        <button
          type="button"
          onClick={() => setUseRegex((prev) => !prev)}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1.5 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            useRegex && "bg-accent text-accent-foreground ring-1 ring-ring"
          )}
          title="Regular expression (.*)"
          aria-pressed={useRegex}
          aria-label="Toggle regular expression"
        >
          <Regex className="h-4 w-4" />
        </button>

        {/* Match count + navigation */}
        <div className="flex items-center gap-1 text-xs text-muted-foreground min-w-[72px] justify-center">
          {findQuery ? (
            matches.length > 0 ? (
              <span>
                {currentMatchIndex + 1} of {matches.length}
              </span>
            ) : (
              <span className="text-destructive">No results</span>
            )
          ) : null}
        </div>

        <button
          type="button"
          onClick={goToPrevMatch}
          disabled={matches.length === 0}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            "disabled:pointer-events-none disabled:opacity-50"
          )}
          title="Previous match (Shift+Enter)"
          aria-label="Previous match"
        >
          <ChevronUp className="h-4 w-4" />
        </button>

        <button
          type="button"
          onClick={goToNextMatch}
          disabled={matches.length === 0}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            "disabled:pointer-events-none disabled:opacity-50"
          )}
          title="Next match (Enter)"
          aria-label="Next match"
        >
          <ChevronDown className="h-4 w-4" />
        </button>

        {/* Close button */}
        <button
          type="button"
          onClick={handleClose}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1 text-sm transition-colors ml-auto",
            "hover:bg-accent hover:text-accent-foreground"
          )}
          title="Close (Escape)"
          aria-label="Close find and replace"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Replace row */}
      {showReplace && (
        <div className="mt-2 flex items-center gap-2">
          <label className="text-xs font-medium text-muted-foreground w-14 shrink-0">
            Replace:
          </label>
          <input
            type="text"
            value={replaceQuery}
            onChange={(e) => setReplaceQuery(e.target.value)}
            onKeyDown={handleReplaceKeyDown}
            placeholder="Replace with..."
            className={cn(
              "flex-1 max-w-xs rounded-md border border-input bg-background px-2 py-1 text-sm",
              "focus:outline-none focus:ring-1 focus:ring-ring",
              "placeholder:text-muted-foreground"
            )}
            aria-label="Replace text"
          />

          <button
            type="button"
            onClick={replaceCurrent}
            disabled={matches.length === 0}
            className={cn(
              "inline-flex items-center justify-center rounded-md border border-input bg-background px-3 py-1 text-xs font-medium transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            Replace
          </button>

          <button
            type="button"
            onClick={replaceAll}
            disabled={matches.length === 0}
            className={cn(
              "inline-flex items-center justify-center rounded-md border border-input bg-background px-3 py-1 text-xs font-medium transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            Replace All
          </button>
        </div>
      )}
    </div>
  );
}
