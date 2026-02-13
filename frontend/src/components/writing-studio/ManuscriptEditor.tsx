"use client";

import { useEffect, useMemo, useCallback } from "react";
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
}

const WORDS_PER_MINUTE = 250;

export function ManuscriptEditor({
  content,
  onChange,
  onSelectionChange,
  onSave,
  placeholder = "Start writing...",
  className,
  readOnly = false,
}: ManuscriptEditorProps) {
  const t = useTranslations("writing");

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
        class: "prose prose-lg max-w-none font-serif outline-none min-h-[300px] px-8 py-6",
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

  // Ctrl+S keyboard shortcut
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "s") {
        event.preventDefault();
        onSave?.();
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
    <div className={cn("flex flex-col rounded-md border bg-background", className)}>
      {/* Toolbar */}
      {!readOnly && <EditorToolbar editor={editor} />}

      {/* Editor content area */}
      <div className="flex-1 overflow-y-auto">
        <EditorContent editor={editor} />
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t px-4 py-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>
            {wordCount.toLocaleString()} {t("editor.words")}
          </span>
          <span>
            {characterCount.toLocaleString()} {t("editor.characters")}
          </span>
          <span>
            ~{readingTime} {t("editor.minRead")}
          </span>
        </div>
        <div>
          {readOnly ? (
            <span>{t("editor.readOnly")}</span>
          ) : (
            <span>{t("editor.editing")}</span>
          )}
        </div>
      </div>
    </div>
  );
}
