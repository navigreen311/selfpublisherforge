"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { Editor } from "@tiptap/react";
import {
  Bold,
  Italic,
  Underline,
  Strikethrough,
  Heading1,
  Heading2,
  Heading3,
  Quote,
  Minus,
  List,
  ListOrdered,
  Link,
  Image,
  Undo,
  Redo,
  Upload,
  ExternalLink,
  X,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EditorToolbarProps {
  editor: Editor | null;
  className?: string;
}

interface ToolbarButtonProps {
  onClick: () => void;
  isActive?: boolean;
  disabled?: boolean;
  tooltip: string;
  children: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Small reusable primitives
// ---------------------------------------------------------------------------

function ToolbarButton({
  onClick,
  isActive = false,
  disabled = false,
  tooltip,
  children,
}: ToolbarButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={onClick}
          disabled={disabled}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1.5 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            "disabled:pointer-events-none disabled:opacity-40",
            isActive && "bg-accent text-accent-foreground",
          )}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="text-xs">
        {tooltip}
      </TooltipContent>
    </Tooltip>
  );
}

function ToolbarSeparator() {
  return <div className="mx-1 h-6 w-px shrink-0 bg-border" />;
}

// ---------------------------------------------------------------------------
// Link popover
// ---------------------------------------------------------------------------

interface LinkPopoverProps {
  editor: Editor;
  onClose: () => void;
}

function LinkPopover({ editor, onClose }: LinkPopoverProps) {
  const previousUrl = editor.getAttributes("link").href ?? "";
  const [url, setUrl] = useState<string>(previousUrl);
  const [openInNewTab, setOpenInNewTab] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const apply = useCallback(() => {
    if (!url) {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
    } else {
      editor
        .chain()
        .focus()
        .extendMarkRange("link")
        .setLink({
          href: url,
          target: openInNewTab ? "_blank" : null,
        })
        .run();
    }
    onClose();
  }, [editor, url, openInNewTab, onClose]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        apply();
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    },
    [apply, onClose],
  );

  return (
    <div
      ref={popoverRef}
      className="absolute left-0 top-full z-50 mt-1 w-80 rounded-lg border bg-popover p-3 shadow-md"
    >
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-muted-foreground">URL</label>
        <input
          ref={inputRef}
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="https://example.com"
          className="w-full rounded-md border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={openInNewTab}
            onChange={(e) => setOpenInNewTab(e.target.checked)}
            className="rounded"
          />
          <ExternalLink className="h-3 w-3" />
          Open in new tab
        </label>
        <div className="flex items-center justify-end gap-1.5 pt-1">
          {previousUrl && (
            <button
              type="button"
              onClick={() => {
                editor.chain().focus().extendMarkRange("link").unsetLink().run();
                onClose();
              }}
              className="rounded-md px-2.5 py-1 text-xs text-destructive hover:bg-destructive/10 transition-colors"
            >
              Remove
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs hover:bg-accent transition-colors"
          >
            <X className="h-3 w-3" />
            Cancel
          </button>
          <button
            type="button"
            onClick={apply}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Check className="h-3 w-3" />
            Apply
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Image popover
// ---------------------------------------------------------------------------

interface ImagePopoverProps {
  editor: Editor;
  onClose: () => void;
}

function ImagePopover({ editor, onClose }: ImagePopoverProps) {
  const [tab, setTab] = useState<"url" | "upload">("url");
  const [url, setUrl] = useState("");
  const [alt, setAlt] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const insertFromUrl = useCallback(() => {
    if (url) {
      editor.chain().focus().setImage({ src: url, alt: alt || undefined }).run();
    }
    onClose();
  }, [editor, url, alt, onClose]);

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result as string;
        editor
          .chain()
          .focus()
          .setImage({ src: dataUrl, alt: file.name })
          .run();
        onClose();
      };
      reader.readAsDataURL(file);
    },
    [editor, onClose],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        insertFromUrl();
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    },
    [insertFromUrl, onClose],
  );

  return (
    <div
      ref={popoverRef}
      className="absolute left-0 top-full z-50 mt-1 w-80 rounded-lg border bg-popover p-3 shadow-md"
    >
      <div className="mb-3 flex gap-1 rounded-md bg-muted p-0.5">
        <button
          type="button"
          onClick={() => setTab("url")}
          className={cn(
            "flex-1 rounded-sm px-2.5 py-1 text-xs font-medium transition-colors",
            tab === "url"
              ? "bg-background shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          URL
        </button>
        <button
          type="button"
          onClick={() => setTab("upload")}
          className={cn(
            "flex-1 rounded-sm px-2.5 py-1 text-xs font-medium transition-colors",
            tab === "upload"
              ? "bg-background shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          Upload
        </button>
      </div>

      {tab === "url" ? (
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-muted-foreground">
            Image URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="https://example.com/image.png"
            className="w-full rounded-md border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            autoFocus
          />
          <label className="text-xs font-medium text-muted-foreground">
            Alt text (optional)
          </label>
          <input
            type="text"
            value={alt}
            onChange={(e) => setAlt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the image"
            className="w-full rounded-md border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <div className="flex items-center justify-end gap-1.5 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs hover:bg-accent transition-colors"
            >
              <X className="h-3 w-3" />
              Cancel
            </button>
            <button
              type="button"
              onClick={insertFromUrl}
              disabled={!url}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:pointer-events-none"
            >
              <Check className="h-3 w-3" />
              Insert
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 py-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center gap-2 rounded-lg border-2 border-dashed px-6 py-4 text-muted-foreground transition-colors hover:border-primary hover:text-primary"
          >
            <Upload className="h-6 w-6" />
            <span className="text-xs font-medium">
              Click to upload an image
            </span>
          </button>
          <p className="text-[10px] text-muted-foreground">
            Supports JPG, PNG, GIF, SVG, WebP
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main toolbar
// ---------------------------------------------------------------------------

export function EditorToolbar({ editor, className }: EditorToolbarProps) {
  const [showLinkPopover, setShowLinkPopover] = useState(false);
  const [showImagePopover, setShowImagePopover] = useState(false);

  const isDisabled = !editor;

  return (
    <TooltipProvider delayDuration={300}>
      <div
        className={cn(
          "sticky top-0 z-40 flex items-center gap-0.5 border-b bg-background/95 px-2 py-1 backdrop-blur supports-[backdrop-filter]:bg-background/60",
          className,
        )}
      >
        {/* Text formatting */}
        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleBold().run()}
          isActive={editor?.isActive("bold") ?? false}
          disabled={isDisabled}
          tooltip="Bold (Ctrl+B)"
        >
          <Bold className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleItalic().run()}
          isActive={editor?.isActive("italic") ?? false}
          disabled={isDisabled}
          tooltip="Italic (Ctrl+I)"
        >
          <Italic className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleUnderline().run()}
          isActive={editor?.isActive("underline") ?? false}
          disabled={isDisabled}
          tooltip="Underline (Ctrl+U)"
        >
          <Underline className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleStrike().run()}
          isActive={editor?.isActive("strike") ?? false}
          disabled={isDisabled}
          tooltip="Strikethrough (Ctrl+Shift+X)"
        >
          <Strikethrough className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarSeparator />

        {/* Headings */}
        <ToolbarButton
          onClick={() =>
            editor?.chain().focus().toggleHeading({ level: 1 }).run()
          }
          isActive={editor?.isActive("heading", { level: 1 }) ?? false}
          disabled={isDisabled}
          tooltip="Heading 1"
        >
          <Heading1 className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() =>
            editor?.chain().focus().toggleHeading({ level: 2 }).run()
          }
          isActive={editor?.isActive("heading", { level: 2 }) ?? false}
          disabled={isDisabled}
          tooltip="Heading 2"
        >
          <Heading2 className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() =>
            editor?.chain().focus().toggleHeading({ level: 3 }).run()
          }
          isActive={editor?.isActive("heading", { level: 3 }) ?? false}
          disabled={isDisabled}
          tooltip="Heading 3"
        >
          <Heading3 className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarSeparator />

        {/* Block elements */}
        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleBlockquote().run()}
          isActive={editor?.isActive("blockquote") ?? false}
          disabled={isDisabled}
          tooltip="Blockquote (Ctrl+Shift+B)"
        >
          <Quote className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() => editor?.chain().focus().setHorizontalRule().run()}
          disabled={isDisabled}
          tooltip="Horizontal Rule"
        >
          <Minus className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarSeparator />

        {/* Lists */}
        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleBulletList().run()}
          isActive={editor?.isActive("bulletList") ?? false}
          disabled={isDisabled}
          tooltip="Bullet List (Ctrl+Shift+8)"
        >
          <List className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() => editor?.chain().focus().toggleOrderedList().run()}
          isActive={editor?.isActive("orderedList") ?? false}
          disabled={isDisabled}
          tooltip="Numbered List (Ctrl+Shift+9)"
        >
          <ListOrdered className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarSeparator />

        {/* Insert: Link */}
        <div className="relative">
          <ToolbarButton
            onClick={() => {
              setShowImagePopover(false);
              setShowLinkPopover((prev) => !prev);
            }}
            isActive={editor?.isActive("link") ?? false}
            disabled={isDisabled}
            tooltip="Link (Ctrl+K)"
          >
            <Link className="h-4 w-4" />
          </ToolbarButton>

          {showLinkPopover && editor && (
            <LinkPopover
              editor={editor}
              onClose={() => setShowLinkPopover(false)}
            />
          )}
        </div>

        {/* Insert: Image */}
        <div className="relative">
          <ToolbarButton
            onClick={() => {
              setShowLinkPopover(false);
              setShowImagePopover((prev) => !prev);
            }}
            disabled={isDisabled}
            tooltip="Image"
          >
            <Image className="h-4 w-4" />
          </ToolbarButton>

          {showImagePopover && editor && (
            <ImagePopover
              editor={editor}
              onClose={() => setShowImagePopover(false)}
            />
          )}
        </div>

        <ToolbarSeparator />

        {/* History */}
        <ToolbarButton
          onClick={() => editor?.chain().focus().undo().run()}
          disabled={isDisabled || !(editor?.can().undo() ?? false)}
          tooltip="Undo (Ctrl+Z)"
        >
          <Undo className="h-4 w-4" />
        </ToolbarButton>

        <ToolbarButton
          onClick={() => editor?.chain().focus().redo().run()}
          disabled={isDisabled || !(editor?.can().redo() ?? false)}
          tooltip="Redo (Ctrl+Shift+Z)"
        >
          <Redo className="h-4 w-4" />
        </ToolbarButton>
      </div>
    </TooltipProvider>
  );
}
