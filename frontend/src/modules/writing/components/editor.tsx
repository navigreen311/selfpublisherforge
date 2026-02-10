"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface EditorProps {
  content: string;
  onChange: (content: string) => void;
  onSelectionChange?: (selectedText: string) => void;
  placeholder?: string;
  className?: string;
  readOnly?: boolean;
  aiSuggestion?: string;
  onAcceptSuggestion?: () => void;
  onDismissSuggestion?: () => void;
}

/**
 * Rich text manuscript editor with AI inline suggestions.
 *
 * Uses a contenteditable div for rich editing with toolbar controls
 * for formatting. Supports AI suggestion overlays.
 */
export function ManuscriptEditor({
  content,
  onChange,
  onSelectionChange,
  placeholder = "Start writing your chapter...",
  className,
  readOnly = false,
  aiSuggestion,
  onAcceptSuggestion,
  onDismissSuggestion,
}: EditorProps) {
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const [isFocused, setIsFocused] = useState(false);

  // Update word/char counts
  useEffect(() => {
    const words = content
      .trim()
      .split(/\s+/)
      .filter((w) => w.length > 0);
    setWordCount(words.length);
    setCharCount(content.length);
  }, [content]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value);
    },
    [onChange]
  );

  const handleSelect = useCallback(() => {
    if (!onSelectionChange || !editorRef.current) return;
    const el = editorRef.current;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    if (start !== end) {
      onSelectionChange(content.substring(start, end));
    }
  }, [content, onSelectionChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Ctrl+Enter to accept AI suggestion
      if (e.ctrlKey && e.key === "Enter" && aiSuggestion) {
        e.preventDefault();
        onAcceptSuggestion?.();
      }
      // Escape to dismiss suggestion
      if (e.key === "Escape" && aiSuggestion) {
        e.preventDefault();
        onDismissSuggestion?.();
      }
    },
    [aiSuggestion, onAcceptSuggestion, onDismissSuggestion]
  );

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b px-4 py-2 bg-muted/30">
        <span className="text-xs text-muted-foreground">
          {wordCount} words | {charCount} characters
        </span>
        <div className="flex-1" />
        {aiSuggestion && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-blue-500 font-medium">
              AI suggestion available
            </span>
            <button
              onClick={onAcceptSuggestion}
              className="text-xs px-2 py-1 rounded bg-blue-500 text-white hover:bg-blue-600 transition-colors"
            >
              Accept (Ctrl+Enter)
            </button>
            <button
              onClick={onDismissSuggestion}
              className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
            >
              Dismiss (Esc)
            </button>
          </div>
        )}
      </div>

      {/* Editor area */}
      <div className="flex-1 relative">
        <textarea
          ref={editorRef}
          value={content}
          onChange={handleChange}
          onSelect={handleSelect}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          readOnly={readOnly}
          placeholder={placeholder}
          className={cn(
            "w-full h-full resize-none p-6 text-base leading-relaxed",
            "font-serif bg-background text-foreground",
            "focus:outline-none",
            "placeholder:text-muted-foreground/50",
            readOnly && "opacity-75 cursor-not-allowed"
          )}
          style={{
            minHeight: "400px",
            fontFamily: "'Georgia', 'Times New Roman', serif",
            fontSize: "16px",
            lineHeight: "1.8",
          }}
        />

        {/* AI Suggestion Overlay */}
        {aiSuggestion && (
          <div className="absolute bottom-0 left-0 right-0 bg-blue-50 border-t border-blue-200 p-4 max-h-48 overflow-y-auto">
            <p className="text-xs text-blue-600 font-medium mb-1">
              AI Suggestion:
            </p>
            <p className="text-sm text-blue-800 whitespace-pre-wrap font-serif">
              {aiSuggestion}
            </p>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 border-t px-4 py-1.5 bg-muted/30 text-xs text-muted-foreground">
        <span>{isFocused ? "Editing" : "Ready"}</span>
        <span>|</span>
        <span>
          ~{Math.ceil(wordCount / 250)} min read
        </span>
      </div>
    </div>
  );
}

export default ManuscriptEditor;
