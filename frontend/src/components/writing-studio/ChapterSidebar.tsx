"use client";

import { useCallback, useState, useRef, useEffect } from "react";
import {
  Check,
  Pencil,
  Circle,
  MoreHorizontal,
  Plus,
  GripVertical,
  ChevronUp,
  ChevronDown,
  Copy,
  Trash2,
  Type,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import type { ChapterContent } from "@/modules/writing/hooks";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ChapterStatus = "complete" | "editing" | "not_started";

interface ChapterSidebarProps {
  chapters: ChapterContent[];
  activeChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
  onReorderChapters: (
    chapters: { chapter_id: string; order: number }[]
  ) => void;
  onDeleteChapter?: (chapterId: string) => void;
  onRenameChapter?: (chapterId: string, title: string) => void;
  totalWordCount?: number;
  className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getChapterStatus(
  chapter: ChapterContent,
  activeChapterId: string | null
): ChapterStatus {
  if (chapter.status) return chapter.status;
  if (chapter.id === activeChapterId) return "editing";
  if (chapter.content && chapter.word_count > 0) return "complete";
  return "not_started";
}

function StatusIcon({ status }: { status: ChapterStatus }) {
  switch (status) {
    case "complete":
      return <Check className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />;
    case "editing":
      return <Pencil className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />;
    case "not_started":
    default:
      return (
        <Circle className="h-3.5 w-3.5 text-muted-foreground/50 flex-shrink-0" />
      );
  }
}

// ---------------------------------------------------------------------------
// Chapter context menu (three-dot dropdown)
// ---------------------------------------------------------------------------

interface ChapterMenuProps {
  isFirst: boolean;
  isLast: boolean;
  onRename: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  t: ReturnType<typeof useTranslations>;
}

function ChapterMenu({
  isFirst,
  isLast,
  onRename,
  onDelete,
  onDuplicate,
  onMoveUp,
  onMoveDown,
  t,
}: ChapterMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          onClick={(e) => e.stopPropagation()}
          className={cn(
            "inline-flex items-center justify-center rounded p-0.5",
            "opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity",
            "hover:bg-accent/80 text-muted-foreground hover:text-foreground"
          )}
          aria-label="Chapter options"
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onRename();
          }}
        >
          <Type className="mr-2 h-4 w-4" />
          {t("editor.chapterMenu.rename")}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onDuplicate();
          }}
        >
          <Copy className="mr-2 h-4 w-4" />
          {t("editor.chapterMenu.duplicate")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          disabled={isFirst}
          onClick={(e) => {
            e.stopPropagation();
            onMoveUp();
          }}
        >
          <ChevronUp className="mr-2 h-4 w-4" />
          {t("editor.chapterMenu.moveUp")}
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={isLast}
          onClick={(e) => {
            e.stopPropagation();
            onMoveDown();
          }}
        >
          <ChevronDown className="mr-2 h-4 w-4" />
          {t("editor.chapterMenu.moveDown")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="text-destructive focus:text-destructive"
        >
          <Trash2 className="mr-2 h-4 w-4" />
          {t("editor.chapterMenu.delete")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// ---------------------------------------------------------------------------
// Inline rename input
// ---------------------------------------------------------------------------

interface InlineRenameProps {
  initialTitle: string;
  onConfirm: (title: string) => void;
  onCancel: () => void;
}

function InlineRename({
  initialTitle,
  onConfirm,
  onCancel,
}: InlineRenameProps) {
  const [value, setValue] = useState(initialTitle);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed && trimmed !== initialTitle) {
      onConfirm(trimmed);
    } else {
      onCancel();
    }
  };

  return (
    <input
      ref={inputRef}
      type="text"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={handleSubmit}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          handleSubmit();
        }
        if (e.key === "Escape") {
          onCancel();
        }
      }}
      onClick={(e) => e.stopPropagation()}
      className={cn(
        "w-full text-sm font-medium bg-background border border-ring rounded px-1.5 py-0.5",
        "focus:outline-none focus:ring-1 focus:ring-primary"
      )}
    />
  );
}

// ---------------------------------------------------------------------------
// Right-click context menu (native-style floating menu)
// ---------------------------------------------------------------------------

interface ContextMenuState {
  chapterId: string;
  x: number;
  y: number;
}

interface FloatingContextMenuProps {
  menu: ContextMenuState;
  sortedChapters: ChapterContent[];
  onRename: (id: string) => void;
  onDelete: (id: string) => void;
  onDuplicate: () => void;
  onMoveUp: (id: string) => void;
  onMoveDown: (id: string) => void;
  onClose: () => void;
  t: ReturnType<typeof useTranslations>;
}

function FloatingContextMenu({
  menu,
  sortedChapters,
  onRename,
  onDelete,
  onDuplicate,
  onMoveUp,
  onMoveDown,
  onClose,
  t,
}: FloatingContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);
  const idx = sortedChapters.findIndex((c) => c.id === menu.chapterId);
  const isFirst = idx === 0;
  const isLast = idx === sortedChapters.length - 1;

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [onClose]);

  const itemClass =
    "relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground";

  return (
    <div
      ref={ref}
      className="fixed z-50 min-w-[10rem] overflow-hidden rounded-md border bg-background p-1 text-foreground shadow-md animate-in fade-in-0 zoom-in-95"
      style={{ top: menu.y, left: menu.x }}
    >
      <button
        type="button"
        onClick={() => {
          onRename(menu.chapterId);
          onClose();
        }}
        className={itemClass}
      >
        <Type className="mr-2 h-4 w-4" />
        {t("editor.chapterMenu.rename")}
      </button>
      <button
        type="button"
        onClick={() => {
          onDuplicate();
          onClose();
        }}
        className={itemClass}
      >
        <Copy className="mr-2 h-4 w-4" />
        {t("editor.chapterMenu.duplicate")}
      </button>
      <div className="-mx-1 my-1 h-px bg-muted" />
      <button
        type="button"
        disabled={isFirst}
        onClick={() => {
          onMoveUp(menu.chapterId);
          onClose();
        }}
        className={cn(
          itemClass,
          "disabled:pointer-events-none disabled:opacity-50"
        )}
      >
        <ChevronUp className="mr-2 h-4 w-4" />
        {t("editor.chapterMenu.moveUp")}
      </button>
      <button
        type="button"
        disabled={isLast}
        onClick={() => {
          onMoveDown(menu.chapterId);
          onClose();
        }}
        className={cn(
          itemClass,
          "disabled:pointer-events-none disabled:opacity-50"
        )}
      >
        <ChevronDown className="mr-2 h-4 w-4" />
        {t("editor.chapterMenu.moveDown")}
      </button>
      <div className="-mx-1 my-1 h-px bg-muted" />
      <button
        type="button"
        onClick={() => {
          onDelete(menu.chapterId);
          onClose();
        }}
        className={cn(
          itemClass,
          "text-destructive hover:bg-destructive/10 hover:text-destructive"
        )}
      >
        <Trash2 className="mr-2 h-4 w-4" />
        {t("editor.chapterMenu.delete")}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * Enhanced chapter sidebar with drag-and-drop reorder, status icons,
 * section labels (Front / Back Matter), inline rename, three-dot menu,
 * right-click context menu, and total word count.
 */
export function ChapterSidebar({
  chapters,
  activeChapterId,
  onSelectChapter,
  onCreateChapter,
  onReorderChapters,
  onDeleteChapter,
  onRenameChapter,
  totalWordCount,
  className,
}: ChapterSidebarProps) {
  const t = useTranslations("writing");

  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(
    null
  );

  // ---- Drag and drop handlers ----

  const handleDragStart = useCallback(
    (e: React.DragEvent, chapterId: string) => {
      setDraggedId(chapterId);
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", chapterId);
    },
    []
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent, chapterId: string) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverId(chapterId);
    },
    []
  );

  const handleDragLeave = useCallback(() => {
    setDragOverId(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, targetId: string) => {
      e.preventDefault();
      setDraggedId(null);
      setDragOverId(null);

      const sourceId = e.dataTransfer.getData("text/plain");
      if (sourceId === targetId) return;

      const sorted = [...chapters].sort((a, b) => a.order - b.order);
      const sourceIdx = sorted.findIndex((c) => c.id === sourceId);
      const targetIdx = sorted.findIndex((c) => c.id === targetId);
      if (sourceIdx === -1 || targetIdx === -1) return;

      const reordered = [...sorted];
      const [moved] = reordered.splice(sourceIdx, 1);
      reordered.splice(targetIdx, 0, moved);

      const newOrder = reordered.map((ch, idx) => ({
        chapter_id: ch.id,
        order: idx + 1,
      }));

      onReorderChapters(newOrder);
    },
    [chapters, onReorderChapters]
  );

  const handleDragEnd = useCallback(() => {
    setDraggedId(null);
    setDragOverId(null);
  }, []);

  // ---- Move up / down helpers ----

  const handleMoveUp = useCallback(
    (chapterId: string) => {
      const sorted = [...chapters].sort((a, b) => a.order - b.order);
      const idx = sorted.findIndex((c) => c.id === chapterId);
      if (idx <= 0) return;

      const reordered = [...sorted];
      [reordered[idx - 1], reordered[idx]] = [
        reordered[idx],
        reordered[idx - 1],
      ];

      onReorderChapters(
        reordered.map((ch, i) => ({ chapter_id: ch.id, order: i + 1 }))
      );
    },
    [chapters, onReorderChapters]
  );

  const handleMoveDown = useCallback(
    (chapterId: string) => {
      const sorted = [...chapters].sort((a, b) => a.order - b.order);
      const idx = sorted.findIndex((c) => c.id === chapterId);
      if (idx === -1 || idx >= sorted.length - 1) return;

      const reordered = [...sorted];
      [reordered[idx], reordered[idx + 1]] = [
        reordered[idx + 1],
        reordered[idx],
      ];

      onReorderChapters(
        reordered.map((ch, i) => ({ chapter_id: ch.id, order: i + 1 }))
      );
    },
    [chapters, onReorderChapters]
  );

  // ---- Rename handler ----

  const handleRenameConfirm = useCallback(
    (chapterId: string, title: string) => {
      onRenameChapter?.(chapterId, title);
      setRenamingId(null);
    },
    [onRenameChapter]
  );

  // ---- Delete handler ----

  const handleDelete = useCallback(
    (chapterId: string) => {
      const confirmed = window.confirm(t("editor.deleteConfirm"));
      if (confirmed) {
        onDeleteChapter?.(chapterId);
      }
    },
    [onDeleteChapter, t]
  );

  // ---- Right-click context menu ----

  const handleContextMenu = useCallback(
    (e: React.MouseEvent, chapterId: string) => {
      e.preventDefault();
      setContextMenu({ chapterId, x: e.clientX, y: e.clientY });
    },
    []
  );

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  // ---- Computed values ----

  const sortedChapters = [...chapters].sort((a, b) => a.order - b.order);

  const computedTotalWords =
    totalWordCount ??
    chapters.reduce((sum, ch) => sum + ch.word_count, 0);

  return (
    <div className={cn("flex flex-col h-full border-r bg-card", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground">
          {t("editor.chapters")}
        </h3>
      </div>

      {/* Chapter list */}
      <div className="flex-1 overflow-y-auto">
        {sortedChapters.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            {t("editor.noChapters")}
          </div>
        ) : (
          <>
            {/* Front Matter section label */}
            <div className="px-4 pt-3 pb-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t("editor.frontMatter")}
              </span>
            </div>

            <ul className="py-1">
              {sortedChapters.map((chapter, idx) => {
                const status = getChapterStatus(chapter, activeChapterId);
                const isActive = chapter.id === activeChapterId;
                const isFirst = idx === 0;
                const isLast = idx === sortedChapters.length - 1;
                const isRenaming = renamingId === chapter.id;

                return (
                  <li
                    key={chapter.id}
                    draggable={!isRenaming}
                    onDragStart={(e) => handleDragStart(e, chapter.id)}
                    onDragOver={(e) => handleDragOver(e, chapter.id)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, chapter.id)}
                    onDragEnd={handleDragEnd}
                    onClick={() => {
                      if (!isRenaming) onSelectChapter(chapter.id);
                    }}
                    onContextMenu={(e) => handleContextMenu(e, chapter.id)}
                    className={cn(
                      "group relative px-3 py-2 cursor-pointer border-l-2 transition-colors",
                      "hover:bg-accent/50",
                      isActive
                        ? "border-l-primary bg-accent"
                        : "border-l-transparent",
                      draggedId === chapter.id && "opacity-50",
                      dragOverId === chapter.id &&
                        draggedId !== chapter.id &&
                        "bg-blue-50 dark:bg-blue-950/30 border-l-blue-400"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {/* Drag handle */}
                      <GripVertical className="h-3.5 w-3.5 text-muted-foreground/40 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 cursor-grab" />

                      {/* Status icon */}
                      <StatusIcon status={status} />

                      {/* Order number */}
                      <span className="text-xs text-muted-foreground font-mono flex-shrink-0">
                        {chapter.order}.
                      </span>

                      {/* Title or inline rename input */}
                      <div className="flex-1 min-w-0">
                        {isRenaming ? (
                          <InlineRename
                            initialTitle={chapter.title}
                            onConfirm={(title) =>
                              handleRenameConfirm(chapter.id, title)
                            }
                            onCancel={() => setRenamingId(null)}
                          />
                        ) : (
                          <p className="text-sm font-medium text-foreground truncate">
                            {chapter.title}
                          </p>
                        )}
                      </div>

                      {/* Word count */}
                      <span className="text-[10px] text-muted-foreground tabular-nums flex-shrink-0">
                        {chapter.word_count.toLocaleString()}
                      </span>

                      {/* Three-dot menu */}
                      <ChapterMenu
                        isFirst={isFirst}
                        isLast={isLast}
                        onRename={() => setRenamingId(chapter.id)}
                        onDelete={() => handleDelete(chapter.id)}
                        onDuplicate={() => onCreateChapter()}
                        onMoveUp={() => handleMoveUp(chapter.id)}
                        onMoveDown={() => handleMoveDown(chapter.id)}
                        t={t}
                      />
                    </div>
                  </li>
                );
              })}
            </ul>

            {/* Back Matter section label */}
            <div className="px-4 pt-3 pb-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t("editor.backMatter")}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Footer: + Chapter button and total word count */}
      <div className="border-t">
        <button
          type="button"
          onClick={onCreateChapter}
          className={cn(
            "flex w-full items-center gap-2 px-4 py-2.5 text-sm font-medium",
            "text-primary hover:bg-accent/50 transition-colors"
          )}
        >
          <Plus className="h-4 w-4" />
          {t("editor.addChapter")}
        </button>
        <div className="px-4 py-2 bg-muted/30 border-t">
          <p className="text-xs text-muted-foreground">
            {t("editor.totalWords", {
              count: computedTotalWords.toLocaleString(),
            })}
          </p>
        </div>
      </div>

      {/* Floating right-click context menu */}
      {contextMenu && (
        <FloatingContextMenu
          menu={contextMenu}
          sortedChapters={sortedChapters}
          onRename={(id) => setRenamingId(id)}
          onDelete={handleDelete}
          onDuplicate={onCreateChapter}
          onMoveUp={handleMoveUp}
          onMoveDown={handleMoveDown}
          onClose={closeContextMenu}
          t={t}
        />
      )}
    </div>
  );
}

export default ChapterSidebar;
