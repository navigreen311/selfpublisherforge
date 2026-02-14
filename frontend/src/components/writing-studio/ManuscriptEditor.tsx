"use client";

import {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import CharacterCount from "@tiptap/extension-character-count";
import Underline from "@tiptap/extension-underline";
import LinkExtension from "@tiptap/extension-link";
import ImageExtension from "@tiptap/extension-image";
import TextAlign from "@tiptap/extension-text-align";
import Highlight from "@tiptap/extension-highlight";
import Typography from "@tiptap/extension-typography";
import { cn } from "@/lib/utils";
import { EditorToolbar } from "./EditorToolbar";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ManuscriptEditorProps {
  /** TipTap JSON content */
  content: any;
  /** Chapter title displayed as editable H1 at top */
  chapterTitle: string;
  /** Callback when editor content changes (TipTap JSON) */
  onContentChange: (content: any) => void;
  /** Callback when the chapter title is edited */
  onTitleChange: (title: string) => void;
  /** Callback to report save status to parent */
  onSaveStatusChange: (status: "saved" | "saving" | "unsaved") => void;
  /** Callback to report live word count */
  onWordCountChange: (count: number) => void;
  /** Editor color theme */
  theme?: "light" | "sepia" | "dark";
  /** Font family for the writing area */
  fontFamily?: string;
  /** Font size in px for the writing area */
  fontSize?: number;
  /** Expose the TipTap editor instance for external tools (AI insert, find/replace) */
  editorRef?: React.MutableRefObject<any>;
  /** Additional selection change handler (for AI panel etc.) */
  onSelectionChange?: (text: string) => void;
  /** Manual save trigger */
  onSave?: () => void;
  /** Additional CSS class */
  className?: string;
  /** Read-only mode */
  readOnly?: boolean;
}

// ---------------------------------------------------------------------------
// Theme definitions
// ---------------------------------------------------------------------------

const THEME_STYLES = {
  light: {
    bg: "#ffffff",
    text: "#1a1a1a",
    titleText: "#111111",
    border: "border-gray-200",
  },
  sepia: {
    bg: "#f5f0e8",
    text: "#5b4636",
    titleText: "#3e2f23",
    border: "border-amber-200",
  },
  dark: {
    bg: "#1a1a2e",
    text: "#e0e0e0",
    titleText: "#f0f0f0",
    border: "border-gray-700",
  },
} as const;

const DEFAULT_FONT_FAMILY = "Georgia, 'Times New Roman', serif";

// Auto-save debounce delay (ms)
const AUTO_SAVE_DELAY = 2000;

// Focus mode idle timeout (ms)
const FOCUS_MODE_IDLE_TIMEOUT = 3000;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ManuscriptEditor({
  content,
  chapterTitle,
  onContentChange,
  onTitleChange,
  onSaveStatusChange,
  onWordCountChange,
  theme = "light",
  fontFamily = DEFAULT_FONT_FAMILY,
  fontSize = 16,
  editorRef,
  onSelectionChange,
  onSave,
  className,
  readOnly = false,
}: ManuscriptEditorProps) {
  // ---- Refs ----------------------------------------------------------------
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedJsonRef = useRef<string>("");
  const titleInputRef = useRef<HTMLHeadingElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // ---- Focus mode state ----------------------------------------------------
  const [toolbarDimmed, setToolbarDimmed] = useState(false);
  const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isTypingRef = useRef(false);

  // ---- Theme ---------------------------------------------------------------
  const currentTheme = THEME_STYLES[theme] || THEME_STYLES.light;

  // ---- Focus mode helpers (declared before editor so handleKeyDown works) --
  const startFocusModeTimer = useCallback(() => {
    setToolbarDimmed(true);

    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current);
    }

    idleTimerRef.current = setTimeout(() => {
      isTypingRef.current = false;
      // Toolbar stays dimmed until mouse movement
    }, FOCUS_MODE_IDLE_TIMEOUT);
  }, []);

  // ---- TipTap extensions ---------------------------------------------------
  const extensions = useMemo(
    () => [
      StarterKit.configure({
        dropcursor: {
          color: theme === "dark" ? "#6366f1" : "#3b82f6",
          width: 2,
        },
        
      }),
      Placeholder.configure({
        placeholder: "Start writing, or press / for AI commands...",
      }),
      CharacterCount,
      Underline,
      Highlight.configure({
        multicolor: true,
      }),
      LinkExtension.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: "text-blue-600 underline cursor-pointer hover:text-blue-800",
        },
      }),
      ImageExtension.configure({
        inline: false,
        allowBase64: true,
      }),
      TextAlign.configure({
        types: ["heading", "paragraph"],
      }),
      Typography,
    ],
    [theme]
  );

  // ---- Auto-save logic -----------------------------------------------------
  const scheduleAutoSave = useCallback(
    (json: any) => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }

      autoSaveTimerRef.current = setTimeout(() => {
        const jsonString = JSON.stringify(json);
        if (jsonString !== lastSavedJsonRef.current) {
          onSaveStatusChange("saving");
          lastSavedJsonRef.current = jsonString;
          // The parent is responsible for actual persistence via onContentChange.
          // We signal "saving" then "saved" after a tick to complete the cycle.
          requestAnimationFrame(() => {
            onSaveStatusChange("saved");
          });
        }
      }, AUTO_SAVE_DELAY);
    },
    [onSaveStatusChange]
  );

  // ---- TipTap editor -------------------------------------------------------
  const editor = useEditor({
    extensions,
    content,
    editable: !readOnly,
    autofocus: true,
    editorProps: {
      attributes: {
        class: cn(
          "prose prose-lg max-w-none outline-none min-h-[300px] px-8 py-6",
          "mx-auto focus:outline-none",
        ),
        style: [
          "font-family: " + fontFamily,
          "font-size: " + fontSize + "px",
          "line-height: 1.8",
          "max-width: 720px",
          "color: " + currentTheme.text,
        ].join("; "),
      },
      handleKeyDown: () => {
        // Mark typing activity for focus mode
        isTypingRef.current = true;
        startFocusModeTimer();
        return false; // Do not prevent default
      },
    },
    onUpdate: ({ editor: currentEditor }) => {
      const json = currentEditor.getJSON();
      onContentChange(json);

      // Report word count
      const words = currentEditor.storage.characterCount?.words() ?? 0;
      onWordCountChange(words);

      // Mark as unsaved and schedule auto-save
      onSaveStatusChange("unsaved");
      scheduleAutoSave(json);
    },
    onSelectionUpdate: ({ editor: currentEditor }) => {
      if (onSelectionChange) {
        const { from, to } = currentEditor.state.selection;
        const selectedText = currentEditor.state.doc.textBetween(from, to, " ");
        onSelectionChange(selectedText);
      }
    },
  });

  // ---- Expose editor instance via ref --------------------------------------
  useEffect(() => {
    if (editorRef && editor) {
      editorRef.current = editor;
    }
  }, [editor, editorRef]);

  // ---- Sync readOnly prop --------------------------------------------------
  useEffect(() => {
    if (editor) {
      editor.setEditable(!readOnly);
    }
  }, [editor, readOnly]);

  // ---- Sync external content changes ---------------------------------------
  useEffect(() => {
    if (!editor) return;

    const currentJson = JSON.stringify(editor.getJSON());
    const incomingJson = JSON.stringify(content);

    if (currentJson !== incomingJson && content) {
      editor.commands.setContent(content, { emitUpdate: false });
      // Update word count after content sync
      const words = editor.storage.characterCount?.words() ?? 0;
      onWordCountChange(words);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content]);

  // ---- Sync editor style when theme/font changes --------------------------
  useEffect(() => {
    if (!editor) return;

    editor.setOptions({
      editorProps: {
        attributes: {
          class: cn(
            "prose prose-lg max-w-none outline-none min-h-[300px] px-8 py-6",
            "mx-auto focus:outline-none",
          ),
          style: [
            "font-family: " + fontFamily,
            "font-size: " + fontSize + "px",
            "line-height: 1.8",
            "max-width: 720px",
            "color: " + currentTheme.text,
          ].join("; "),
        },
      },
    });
  }, [editor, fontFamily, fontSize, currentTheme.text]);

  // ---- Save on blur --------------------------------------------------------
  const handleBlur = useCallback(() => {
    if (!editor) return;
    const json = editor.getJSON();
    const jsonString = JSON.stringify(json);
    if (jsonString !== lastSavedJsonRef.current) {
      onSaveStatusChange("saving");
      onContentChange(json);
      lastSavedJsonRef.current = jsonString;
      requestAnimationFrame(() => {
        onSaveStatusChange("saved");
      });
    }
  }, [editor, onContentChange, onSaveStatusChange]);

  // ---- Save on navigating away (beforeunload) ------------------------------
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!editor) return;
      const json = editor.getJSON();
      const jsonString = JSON.stringify(json);
      if (jsonString !== lastSavedJsonRef.current) {
        onContentChange(json);
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [editor, onContentChange]);

  // ---- Clean up auto-save timer on unmount ---------------------------------
  useEffect(() => {
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, []);

  // ---- Focus mode: restore toolbar on mouse movement -----------------------
  const handleMouseMove = useCallback(() => {
    if (toolbarDimmed) {
      setToolbarDimmed(false);
    }
    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current);
      idleTimerRef.current = null;
    }
  }, [toolbarDimmed]);

  // Clean up idle timer on unmount
  useEffect(() => {
    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, []);

  // ---- Keyboard shortcuts: Ctrl+S ------------------------------------------
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "s") {
        event.preventDefault();
        if (editor) {
          const json = editor.getJSON();
          onContentChange(json);
          onSaveStatusChange("saving");
          lastSavedJsonRef.current = JSON.stringify(json);
          requestAnimationFrame(() => {
            onSaveStatusChange("saved");
          });
        }
        onSave?.();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [editor, onContentChange, onSave, onSaveStatusChange]);

  // ---- Title editing -------------------------------------------------------
  const handleTitleInput = useCallback(
    (e: React.FormEvent<HTMLHeadingElement>) => {
      const newTitle = (e.currentTarget.textContent || "").trim();
      onTitleChange(newTitle);
    },
    [onTitleChange]
  );

  const handleTitleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLHeadingElement>) => {
      // Enter in title should move focus to editor body
      if (e.key === "Enter") {
        e.preventDefault();
        editor?.commands.focus("start");
      }
    },
    [editor]
  );

  // ---- Word count (for status display) -------------------------------------
  const wordCount = editor?.storage.characterCount?.words() ?? 0;
  const characterCount = editor?.storage.characterCount?.characters() ?? 0;

  // ---- Render --------------------------------------------------------------
  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className={cn(
        "flex flex-col rounded-md border overflow-hidden",
        currentTheme.border,
        className
      )}
      style={{ backgroundColor: currentTheme.bg }}
    >
      {/* Toolbar: dims during active typing (focus mode) */}
      {!readOnly && (
        <div
          className={cn(
            "transition-opacity duration-500 ease-in-out",
            toolbarDimmed ? "opacity-50" : "opacity-100"
          )}
          onMouseEnter={() => setToolbarDimmed(false)}
        >
          <EditorToolbar editor={editor} />
        </div>
      )}

      {/* Editor content area */}
      <div
        className="flex-1 overflow-y-auto"
        style={{ backgroundColor: currentTheme.bg }}
        onBlur={handleBlur}
      >
        {/* Chapter title: editable H1 */}
        <div className="mx-auto" style={{ maxWidth: 720 }}>
          <h1
            ref={titleInputRef}
            contentEditable={!readOnly}
            suppressContentEditableWarning
            onInput={handleTitleInput}
            onKeyDown={handleTitleKeyDown}
            className={cn(
              "outline-none px-8 pt-8 pb-2 text-3xl font-bold leading-tight",
              "border-none focus:outline-none",
              !chapterTitle && "text-gray-400"
            )}
            style={{
              fontFamily: fontFamily,
              color: currentTheme.titleText,
              maxWidth: 720,
            }}
            data-placeholder="Chapter title..."
          >
            {chapterTitle}
          </h1>
        </div>

        {/* TipTap editor body */}
        <EditorContent editor={editor} />
      </div>

      {/* Minimal status bar */}
      <div
        className={cn(
          "flex items-center justify-between border-t px-4 py-1.5 text-xs transition-opacity duration-500",
          toolbarDimmed ? "opacity-50" : "opacity-100"
        )}
        style={{
          backgroundColor: currentTheme.bg,
          color: theme === "dark" ? "#888" : "#999",
          borderColor: theme === "dark" ? "#333" : undefined,
        }}
      >
        <span>
          {wordCount.toLocaleString()} words &middot;{" "}
          {characterCount.toLocaleString()} characters
        </span>
        <span>
          {readOnly ? "Read only" : "Editing"}
        </span>
      </div>

      {/* Paragraph spacing and theme styles for TipTap prose */}
      <style jsx global>{`
        .ProseMirror p {
          margin-bottom: 1.5em;
        }
        .ProseMirror p.is-editor-empty:first-child::before {
          color: ${theme === "dark" ? "#555" : "#adb5bd"};
          content: attr(data-placeholder);
          float: left;
          height: 0;
          pointer-events: none;
        }
        .ProseMirror:focus {
          outline: none;
        }
        .ProseMirror img {
          max-width: 100%;
          height: auto;
          border-radius: 4px;
        }
        .ProseMirror blockquote {
          border-left: 3px solid ${theme === "dark" ? "#444" : "#ddd"};
          padding-left: 1em;
          color: ${theme === "dark" ? "#aaa" : "#666"};
        }
        .ProseMirror mark {
          background-color: ${theme === "dark" ? "#4a4a00" : "#fff3cd"};
          color: inherit;
          padding: 0.1em 0.2em;
          border-radius: 2px;
        }
        .ProseMirror hr {
          border: none;
          border-top: 1px solid ${theme === "dark" ? "#444" : "#ddd"};
          margin: 2em 0;
        }
        h1[data-placeholder]:empty::before {
          content: attr(data-placeholder);
          color: ${theme === "dark" ? "#555" : "#ccc"};
          pointer-events: none;
        }
      `}</style>
    </div>
  );
}

export default ManuscriptEditor;
