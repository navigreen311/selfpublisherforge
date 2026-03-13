"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import CharacterCount from "@tiptap/extension-character-count";
import Underline from "@tiptap/extension-underline";
import LinkExtension from "@tiptap/extension-link";
import ImageExtension from "@tiptap/extension-image";
import TextAlign from "@tiptap/extension-text-align";
import Highlight from "@tiptap/extension-highlight";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";
import { EditorToolbar } from "./EditorToolbar";

interface ManuscriptEditorProps {
  content: string;
  onChange: (html: string) => void;
  onSelectionChange?: (text: string) => void;
  onSave?: () => void;
  placeholder?: string;
  className?: string;
  readOnly?: boolean;
  theme?: "light" | "sepia" | "dark";
  fontFamily?: string;
  fontSize?: number;
  focusMode?: boolean;
}

const THEME_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  light: { bg: "bg-white", text: "text-gray-900", border: "border-gray-200" },
  sepia: { bg: "bg-amber-50", text: "text-amber-950", border: "border-amber-200" },
  dark: { bg: "bg-gray-900", text: "text-gray-100", border: "border-gray-700" },
};

const FONT_FAMILIES: Record<string, string> = {
  Georgia: "Georgia, 'Times New Roman', serif",
  Merriweather: "'Merriweather', serif",
  Lora: "'Lora', serif",
  "Source Serif Pro": "'Source Serif Pro', serif",
  "System Sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
};

const WORDS_PER_MINUTE = 250;

export function ManuscriptEditor({
  content,
  onChange,
  onSelectionChange,
  onSave,
  placeholder = "Start writing, or press / for AI commands...",
  className,
  readOnly = false,
  theme = "light",
  fontFamily = "Georgia",
  fontSize = 16,
  focusMode = false,
}: ManuscriptEditorProps) {
  const t = useTranslations("writing");

  // Find & Replace state
  const [showFind, setShowFind] = useState(false);
  const [showReplace, setShowReplace] = useState(false);
  const [findQuery, setFindQuery] = useState("");
  const [replaceQuery, setReplaceQuery] = useState("");
  const [caseSensitive, setCaseSensitive] = useState(false);

  const currentTheme = THEME_STYLES[theme] || THEME_STYLES.light;
  const currentFont = FONT_FAMILIES[fontFamily] || FONT_FAMILIES.Georgia;

  const extensions = useMemo(
    () => [
      StarterKit,
      Placeholder.configure({
        placeholder,
      }),
      CharacterCount,
      Underline,
      LinkExtension.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: "text-primary underline cursor-pointer",
        },
      }),
      ImageExtension.configure({
        inline: false,
        allowBase64: true,
      }),
      TextAlign.configure({
        types: ["heading", "paragraph"],
      }),
      Highlight.configure({
        multicolor: true,
      }),
    ],
    [placeholder]
  );

  const editor = useEditor({
    extensions,
    content,
    editable: !readOnly,
    autofocus: true,
    editorProps: {
      attributes: {
        class: cn(
          "prose prose-lg max-w-none outline-none min-h-[300px] px-8 py-6",
          "mx-auto",
          currentTheme.text,
        ),
        style: `font-family: ${currentFont}; font-size: ${fontSize}px; line-height: 1.8; max-width: 720px;`,
      },
    },
    onUpdate: ({ editor: currentEditor }) => {
      onChange(currentEditor.getHTML());
    },
    onSelectionUpdate: ({ editor: currentEditor }) => {
      if (onSelectionChange) {
        const { from, to } = currentEditor.state.selection;
        const selectedText = currentEditor.state.doc.textBetween(from, to, " ");
        onSelectionChange(selectedText);
      }
    },
  });

  // Sync readOnly prop changes
  useEffect(() => {
    if (editor) {
      editor.setEditable(!readOnly);
    }
  }, [editor, readOnly]);

  // Sync external content changes
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, { emitUpdate: false });
    }
  }, [editor, content]);

  // Keyboard shortcuts: Ctrl+S, Ctrl+F, Ctrl+H
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "s") {
        event.preventDefault();
        onSave?.();
      }
      if ((event.ctrlKey || event.metaKey) && event.key === "f") {
        event.preventDefault();
        setShowFind(true);
        setShowReplace(false);
      }
      if ((event.ctrlKey || event.metaKey) && event.key === "h") {
        event.preventDefault();
        setShowFind(true);
        setShowReplace(true);
      }
    },
    [onSave]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  // Computed statistics
  const wordCount = editor?.storage.characterCount?.words() ?? 0;
  const characterCount = editor?.storage.characterCount?.characters() ?? 0;
  const readingTime = Math.max(1, Math.ceil(wordCount / WORDS_PER_MINUTE));

  return (
    <div className={cn(
      "flex flex-col rounded-md border",
      currentTheme.bg,
      currentTheme.border,
      className
    )}>
      {/* Toolbar */}
      {!readOnly && (
        <div className={cn("transition-opacity duration-300", focusMode && "opacity-30 hover:opacity-100")}>
          <EditorToolbar editor={editor} />
        </div>
      )}

      {/* Find & Replace bar */}
      {showFind && (
        <div className="border-b px-4 py-2 flex items-center gap-2 bg-muted/30">
          <input
            type="text"
            value={findQuery}
            onChange={(e) => setFindQuery(e.target.value)}
            placeholder={t("editor.findReplace.find")}
            className="rounded border px-2 py-1 text-sm bg-background w-48 focus:outline-none focus:ring-1 focus:ring-primary"
            autoFocus
          />
          <button
            type="button"
            onClick={() => setCaseSensitive(prev => !prev)}
            className={cn(
              "text-xs px-2 py-1 rounded border transition-colors",
              caseSensitive ? "bg-primary text-primary-foreground" : "hover:bg-accent"
            )}
            title={t("editor.findReplace.caseSensitive")}
          >
            Aa
          </button>
          {showReplace && (
            <>
              <input
                type="text"
                value={replaceQuery}
                onChange={(e) => setReplaceQuery(e.target.value)}
                placeholder={t("editor.findReplace.replace")}
                className="rounded border px-2 py-1 text-sm bg-background w-48 focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button
                type="button"
                onClick={() => {
                  if (editor && findQuery) {
                    const html = editor.getHTML();
                    const flags = caseSensitive ? "g" : "gi";
                    const regex = new RegExp(findQuery.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), flags);
                    const updated = html.replace(regex, replaceQuery);
                    editor.commands.setContent(updated);
                    onChange(updated);
                    setFindQuery("");
                    setReplaceQuery("");
                  }
                }}
                className="text-xs px-2 py-1 rounded border hover:bg-accent transition-colors"
              >
                {t("editor.findReplace.replaceAll")}
              </button>
            </>
          )}
          <button
            type="button"
            onClick={() => {
              setShowFind(false);
              setShowReplace(false);
              setFindQuery("");
              setReplaceQuery("");
            }}
            className="text-xs px-2 py-1 rounded hover:bg-accent transition-colors ml-auto"
          >
            ✕
          </button>
        </div>
      )}

      {/* Editor content area */}
      <div className="flex-1 overflow-y-auto">
        <EditorContent editor={editor} />
      </div>

      {/* Minimal status bar */}
      <div className={cn(
        "flex items-center justify-end border-t px-4 py-1.5 text-xs text-muted-foreground transition-opacity duration-300",
        focusMode && "opacity-30 hover:opacity-100"
      )}>
        {readOnly ? <span>{t("editor.readOnly")}</span> : <span>{t("editor.editing")}</span>}
      </div>
    </div>
  );
}
