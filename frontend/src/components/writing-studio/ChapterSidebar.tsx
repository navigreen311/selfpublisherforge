"use client";

import { useCallback, useState, useRef, useEffect } from "react";
import {
  BookOpen,
  Check,
  Pencil,
  Circle,
  MoreHorizontal,
  Plus,
  GripVertical,
  ChevronUp,
  ChevronDown,
  ChevronRight,
  Copy,
  Trash2,
  Type,
  PanelLeftClose,
  PanelLeft,
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

/** Well-known IDs for front/back matter virtual sections */
const FRONT_MATTER_ITEMS = [
  { key: "titlePage", id: "front:titlePage" },
  { key: "copyright", id: "front:copyright" },
  { key: "dedication", id: "front:dedication" },
] as const;

const BACK_MATTER_ITEMS = [
  { key: "aboutAuthor", id: "back:aboutAuthor" },
  { key: "alsoBy", id: "back:alsoBy" },
  { key: "reviewRequest", id: "back:reviewRequest" },
] as const;

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
  /** Duplicate an existing chapter by its ID */
  onDuplicateChapter?: (chapterId: string) => void;
  /** Insert a new chapter below a given chapter ID */
  onInsertChapterBelow?: (afterChapterId: string) => void;
  /** Toggle between complete and draft status for a chapter */
  onToggleChapterStatus?: (chapterId: string, newStatus: ChapterStatus) => void;
  totalWordCount?: number;
  manuscriptTitle?: string;
  targetWordCount?: number;
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Called when the user toggles the collapse state */
  onToggleCollapse?: () => void;
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
  status: ChapterStatus;
  onRename: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onInsertBelow: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onToggleStatus: () => void;
  t: ReturnType<typeof useTranslations>;
}

function ChapterMenu({
  isFirst,
  isLast,
  status,
  onRename,
  onDelete,
  onDuplicate,
  onInsertBelow,
  onMoveUp,
  onMoveDown,
  onToggleStatus,
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
            onToggleStatus();
          }}
        >
          <Check className="mr-2 h-4 w-4" />
          {status === "complete"
            ? t("editor.chapterSidebar.markDraft")
            : t("editor.chapterSidebar.markComplete")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onDuplicate();
          }}
        >
          <Copy className="mr-2 h-4 w-4" />
          {t("editor.chapterMenu.duplicate")}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onInsertBelow();
          }}
        >
          <Plus className="mr-2 h-4 w-4" />
          {t("editor.chapterSidebar.insertBelow")}
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
  activeChapterId: string | null;
  onRename: (id: string) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  onInsertBelow: (id: string) => void;
  onMoveUp: (id: string) => void;
  onMoveDown: (id: string) => void;
  onToggleStatus: (id: string) => void;
  onClose: () => void;
  t: ReturnType<typeof useTranslations>;
}

function FloatingContextMenu({
  menu,
  sortedChapters,
  activeChapterId,
  onRename,
  onDelete,
  onDuplicate,
  onInsertBelow,
  onMoveUp,
  onMoveDown,
  onToggleStatus,
  onClose,
  t,
}: FloatingContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);
  const idx = sortedChapters.findIndex((c) => c.id === menu.chapterId);
  const isFirst = idx === 0;
  const isLast = idx === sortedChapters.length - 1;
  const chapter = sortedChapters[idx];
  const status = chapter
    ? getChapterStatus(chapter, activeChapterId)
    : "not_started";

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
          onToggleStatus(menu.chapterId);
          onClose();
        }}
        className={itemClass}
      >
        <Check className="mr-2 h-4 w-4" />
        {status === "complete"
          ? t("editor.chapterSidebar.markDraft")
          : t("editor.chapterSidebar.markComplete")}
      </button>
      <div className="-mx-1 my-1 h-px bg-muted" />
      <button
        type="button"
        onClick={() => {
          onDuplicate(menu.chapterId);
          onClose();
        }}
        className={itemClass}
      >
        <Copy className="mr-2 h-4 w-4" />
        {t("editor.chapterMenu.duplicate")}
      </button>
      <button
        type="button"
        onClick={() => {
          onInsertBelow(menu.chapterId);
          onClose();
        }}
        className={itemClass}
      >
        <Plus className="mr-2 h-4 w-4" />
        {t("editor.chapterSidebar.insertBelow")}
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
// Collapsible section header
// ---------------------------------------------------------------------------

interface SectionHeaderProps {
  label: string;
  isOpen: boolean;
  onToggle: () => void;
}

function SectionHeader({ label, isOpen, onToggle }: SectionHeaderProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="w-full flex items-center gap-1.5 px-4 pt-3 pb-1 text-left group/section"
    >
      <ChevronRight
        className={cn(
          "h-3 w-3 text-muted-foreground/70 transition-transform duration-200",
          isOpen && "rotate-90"
        )}
      />
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70 group-hover/section:text-muted-foreground transition-colors">
        {label}
      </span>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Matter item (front/back matter clickable entry with tree connector)
// ---------------------------------------------------------------------------

interface MatterItemProps {
  label: string;
  itemId: string;
  isActive: boolean;
  isLast: boolean;
  onClick: (id: string) => void;
}

function MatterItem({ label, itemId, isActive, isLast, onClick }: MatterItemProps) {
  return (
    <li className="relative pl-4 ml-2">
      {/* Vertical connector line */}
      <span
        className={cn(
          "absolute left-0 top-0 w-px bg-border",
          isLast ? "h-[50%]" : "h-full"
        )}
        aria-hidden="true"
      />
      {/* Horizontal connector branch */}
      <span
        className="absolute left-0 top-[50%] h-px w-3 bg-border"
        aria-hidden="true"
      />
      <button
        type="button"
        onClick={() => onClick(itemId)}
        className={cn(
          "w-full text-left px-2 py-1 text-xs rounded transition-colors",
          isActive
            ? "bg-accent text-accent-foreground font-medium"
            : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
        )}
      >
        {label}
      </button>
    </li>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * Enhanced chapter sidebar with drag-and-drop reorder, status icons,
 * section labels (Front / Back Matter), inline rename, three-dot menu,
 * right-click context menu, collapse toggle, and total word count progress.
 *
 * Fixed at 240px width. Scrollable chapter list with sticky header/footer.
 */
export function ChapterSidebar({
  chapters,
  activeChapterId,
  onSelectChapter,
  onCreateChapter,
  onReorderChapters,
  onDeleteChapter,
  onRenameChapter,
  onDuplicateChapter,
  onInsertChapterBelow,
  onToggleChapterStatus,
  totalWordCount,
  manuscriptTitle,
  targetWordCount,
  collapsed = false,
  onToggleCollapse,
  className,
}: ChapterSidebarProps) {
  const t = useTranslations("writing");

  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(
    null
  );
  const [frontMatterOpen, setFrontMatterOpen] = useState(true);
  const [backMatterOpen, setBackMatterOpen] = useState(true);

  // ---- Collapsed state ----
  // When collapsed, render only a thin rail with an expand button
  if (collapsed) {
    return (
      <div
        className={cn(
          "flex flex-col items-center border-r bg-card py-3",
          "w-10 flex-shrink-0",
          className
        )}
      >
        <button
          type="button"
          onClick={onToggleCollapse}
          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          aria-label={t("editor.chapterSidebar.expand")}
          title={t("editor.chapterSidebar.expand")}
        >
          <PanelLeft className="h-4 w-4" />
        </button>
      </div>
    );
  }

  // ---- Drag and drop handlers ----

  const handleDragStart = (e: React.DragEvent, chapterId: string) => {
    setDraggedId(chapterId);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", chapterId);
  };

  const handleDragOver = (e: React.DragEvent, chapterId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverId(chapterId);
  };

  const handleDragLeave = () => {
    setDragOverId(null);
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
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
  };

  const handleDragEnd = () => {
    setDraggedId(null);
    setDragOverId(null);
  };

  // ---- Move up / down helpers ----

  const handleMoveUp = (chapterId: string) => {
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
  };

  const handleMoveDown = (chapterId: string) => {
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
  };

  // ---- Rename handler ----

  const handleRenameConfirm = (chapterId: string, title: string) => {
    onRenameChapter?.(chapterId, title);
    setRenamingId(null);
  };

  // ---- Delete handler (with confirmation) ----

  const handleDelete = (chapterId: string) => {
    const confirmed = window.confirm(t("editor.deleteConfirm"));
    if (confirmed) {
      onDeleteChapter?.(chapterId);
    }
  };

  // ---- Duplicate handler ----

  const handleDuplicate = (chapterId: string) => {
    if (onDuplicateChapter) {
      onDuplicateChapter(chapterId);
    } else {
      // Fallback: just create a new chapter
      onCreateChapter();
    }
  };

  // ---- Insert below handler ----

  const handleInsertBelow = (chapterId: string) => {
    if (onInsertChapterBelow) {
      onInsertChapterBelow(chapterId);
    } else {
      // Fallback: just create a new chapter
      onCreateChapter();
    }
  };

  // ---- Toggle status handler ----

  const handleToggleStatus = (chapterId: string) => {
    const chapter = chapters.find((c) => c.id === chapterId);
    if (!chapter) return;
    const currentStatus = getChapterStatus(chapter, activeChapterId);
    const newStatus: ChapterStatus =
      currentStatus === "complete" ? "not_started" : "complete";
    onToggleChapterStatus?.(chapterId, newStatus);
  };

  // ---- Right-click context menu ----

  const handleContextMenu = (e: React.MouseEvent, chapterId: string) => {
    e.preventDefault();
    setContextMenu({ chapterId, x: e.clientX, y: e.clientY });
  };

  const closeContextMenu = () => {
    setContextMenu(null);
  };

  // ---- Computed values ----

  const sortedChapters = [...chapters].sort((a, b) => a.order - b.order);

  const computedTotalWords =
    totalWordCount ??
    chapters.reduce((sum, ch) => sum + ch.word_count, 0);

  const effectiveTarget = targetWordCount || 60000;
  const progressPct = Math.min(
    Math.round((computedTotalWords / effectiveTarget) * 100),
    100
  );

  return (
    <div
      className={cn(
        "flex flex-col h-full border-r bg-card w-60 flex-shrink-0",
        className
      )}
    >
      {/* ------------------------------------------------------------------ */}
      {/* Header: manuscript title + collapse button                         */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex items-center justify-between px-3 py-3 border-b gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <BookOpen className="h-4 w-4 text-primary flex-shrink-0" />
          <div className="min-w-0">
            <p
              className="text-xs font-medium text-foreground truncate leading-tight"
              title={manuscriptTitle || t("editor.chapterSidebar.manuscriptTitle")}
            >
              {manuscriptTitle || t("editor.chapterSidebar.manuscriptTitle")}
            </p>
            <p className="text-[10px] text-muted-foreground leading-tight">
              {t("editor.chapters")}
            </p>
          </div>
        </div>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
            aria-label={t("editor.chapterSidebar.collapse")}
            title={t("editor.chapterSidebar.collapse")}
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Scrollable content                                                 */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex-1 overflow-y-auto">
        {sortedChapters.length === 0 && chapters.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            {t("editor.noChapters")}
          </div>
        ) : (
          <>
            {/* -------------------------------------------------------------- */}
            {/* Front Matter section (collapsible)                              */}
            {/* -------------------------------------------------------------- */}
            <SectionHeader
              label={t("editor.chapterSidebar.frontMatter")}
              isOpen={frontMatterOpen}
              onToggle={() => setFrontMatterOpen((prev) => !prev)}
            />
            {frontMatterOpen && (
              <ul className="py-1 pl-5 pr-2">
                {FRONT_MATTER_ITEMS.map((item, i) => (
                  <MatterItem
                    key={item.key}
                    label={t(`editor.chapterSidebar.${item.key}`)}
                    itemId={item.id}
                    isActive={activeChapterId === item.id}
                    isLast={i === FRONT_MATTER_ITEMS.length - 1}
                    onClick={onSelectChapter}
                  />
                ))}
              </ul>
            )}

            <div className="mx-3 my-1 h-px bg-border" />

            {/* -------------------------------------------------------------- */}
            {/* Chapter list                                                    */}
            {/* -------------------------------------------------------------- */}
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
                      "group relative px-2 py-1.5 cursor-pointer border-l-2 transition-colors",
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
                    <div className="flex items-center gap-1.5">
                      {/* Drag handle */}
                      <GripVertical className="h-3 w-3 text-muted-foreground/40 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 cursor-grab" />

                      {/* Status icon */}
                      <StatusIcon status={status} />

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
                          <p
                            className={cn(
                              "text-xs font-medium truncate",
                              isActive
                                ? "text-foreground"
                                : "text-foreground/80"
                            )}
                            title={`Ch ${chapter.order}: ${chapter.title}`}
                          >
                            Ch {chapter.order}: {chapter.title}
                          </p>
                        )}
                      </div>

                      {/* Word count badge */}
                      <span className="text-[9px] text-muted-foreground tabular-nums flex-shrink-0">
                        {chapter.word_count.toLocaleString()}
                      </span>

                      {/* Three-dot menu */}
                      <ChapterMenu
                        isFirst={isFirst}
                        isLast={isLast}
                        status={status}
                        onRename={() => setRenamingId(chapter.id)}
                        onDelete={() => handleDelete(chapter.id)}
                        onDuplicate={() => handleDuplicate(chapter.id)}
                        onInsertBelow={() => handleInsertBelow(chapter.id)}
                        onMoveUp={() => handleMoveUp(chapter.id)}
                        onMoveDown={() => handleMoveDown(chapter.id)}
                        onToggleStatus={() => handleToggleStatus(chapter.id)}
                        t={t}
                      />
                    </div>
                  </li>
                );
              })}
            </ul>

            <div className="mx-3 my-1 h-px bg-border" />

            {/* -------------------------------------------------------------- */}
            {/* Back Matter section (collapsible)                               */}
            {/* -------------------------------------------------------------- */}
            <SectionHeader
              label={t("editor.chapterSidebar.backMatter")}
              isOpen={backMatterOpen}
              onToggle={() => setBackMatterOpen((prev) => !prev)}
            />
            {backMatterOpen && (
              <ul className="py-1 pl-5 pr-2">
                {BACK_MATTER_ITEMS.map((item, i) => (
                  <MatterItem
                    key={item.key}
                    label={t(`editor.chapterSidebar.${item.key}`)}
                    itemId={item.id}
                    isActive={activeChapterId === item.id}
                    isLast={i === BACK_MATTER_ITEMS.length - 1}
                    onClick={onSelectChapter}
                  />
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Footer: + Add Chapter button and total word count progress         */}
      {/* ------------------------------------------------------------------ */}
      <div className="border-t flex-shrink-0">
        <button
          type="button"
          onClick={onCreateChapter}
          className={cn(
            "flex w-full items-center gap-2 px-4 py-2 text-sm font-medium",
            "text-primary hover:bg-accent/50 transition-colors"
          )}
        >
          <Plus className="h-4 w-4" />
          {t("editor.addChapter")}
        </button>

        <div className="px-3 py-2.5 bg-muted/30 border-t space-y-1.5">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-muted-foreground">
              {computedTotalWords.toLocaleString()} /{" "}
              {effectiveTarget.toLocaleString()} {t("stats.words")}
            </span>
            <span className="text-muted-foreground font-medium">
              {progressPct}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                progressPct >= 100
                  ? "bg-green-500"
                  : progressPct >= 75
                    ? "bg-primary"
                    : progressPct >= 50
                      ? "bg-amber-500"
                      : "bg-primary/60"
              )}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Floating right-click context menu                                  */}
      {/* ------------------------------------------------------------------ */}
      {contextMenu && (
        <FloatingContextMenu
          menu={contextMenu}
          sortedChapters={sortedChapters}
          activeChapterId={activeChapterId}
          onRename={(id) => setRenamingId(id)}
          onDelete={handleDelete}
          onDuplicate={handleDuplicate}
          onInsertBelow={handleInsertBelow}
          onMoveUp={handleMoveUp}
          onMoveDown={handleMoveDown}
          onToggleStatus={handleToggleStatus}
          onClose={closeContextMenu}
          t={t}
        />
      )}
    </div>
  );
}

export default ChapterSidebar;
