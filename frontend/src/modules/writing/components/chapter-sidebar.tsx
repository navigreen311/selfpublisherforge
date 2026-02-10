"use client";

import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import type { ChapterContent } from "../hooks";

interface ChapterSidebarProps {
  chapters: ChapterContent[];
  activeChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
  onReorderChapters: (chapters: { chapter_id: string; order: number }[]) => void;
  className?: string;
}

/**
 * Chapter sidebar with drag-and-drop reorder support.
 *
 * Displays a list of chapters with selection state, word counts,
 * and the ability to create new chapters or reorder existing ones.
 */
export function ChapterSidebar({
  chapters,
  activeChapterId,
  onSelectChapter,
  onCreateChapter,
  onReorderChapters,
  className,
}: ChapterSidebarProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

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

      // Compute new order
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

  const sortedChapters = [...chapters].sort((a, b) => a.order - b.order);

  return (
    <div
      className={cn(
        "flex flex-col h-full border-r bg-card",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground">Chapters</h3>
        <button
          onClick={onCreateChapter}
          className="text-xs px-2 py-1 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          + New
        </button>
      </div>

      {/* Chapter list */}
      <div className="flex-1 overflow-y-auto">
        {sortedChapters.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No chapters yet. Create your first chapter to begin writing.
          </div>
        ) : (
          <ul className="py-1">
            {sortedChapters.map((chapter) => (
              <li
                key={chapter.id}
                draggable
                onDragStart={(e) => handleDragStart(e, chapter.id)}
                onDragOver={(e) => handleDragOver(e, chapter.id)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, chapter.id)}
                onDragEnd={handleDragEnd}
                onClick={() => onSelectChapter(chapter.id)}
                className={cn(
                  "px-4 py-2.5 cursor-pointer border-l-2 transition-colors",
                  "hover:bg-accent/50",
                  chapter.id === activeChapterId
                    ? "border-l-primary bg-accent"
                    : "border-l-transparent",
                  draggedId === chapter.id && "opacity-50",
                  dragOverId === chapter.id &&
                    draggedId !== chapter.id &&
                    "bg-blue-50 border-l-blue-400"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground font-mono">
                    {chapter.order}.
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {chapter.word_count.toLocaleString()} words
                  </span>
                </div>
                <p className="text-sm font-medium text-foreground truncate mt-0.5">
                  {chapter.title}
                </p>
                {chapter.synopsis && (
                  <p className="text-xs text-muted-foreground truncate mt-0.5">
                    {chapter.synopsis}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Summary footer */}
      <div className="border-t px-4 py-2 bg-muted/30">
        <p className="text-xs text-muted-foreground">
          {chapters.length} chapter{chapters.length !== 1 ? "s" : ""} |{" "}
          {chapters
            .reduce((sum, ch) => sum + ch.word_count, 0)
            .toLocaleString()}{" "}
          total words
        </p>
      </div>
    </div>
  );
}

export default ChapterSidebar;
