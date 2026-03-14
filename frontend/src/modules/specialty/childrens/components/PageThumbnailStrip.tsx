"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GripVertical, Plus, Trash2 } from "lucide-react";
import type { LayoutType } from "./LayoutSelector";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface PageData {
  id: string;
  pageNumber: number;
  layout: LayoutType;
  textContent?: string;
  illustrationUrl?: string;
}

interface PageThumbnailStripProps {
  pages: PageData[];
  selectedIndex: number;
  onSelectPage: (index: number) => void;
  onReorderPages: (pages: PageData[]) => void;
  onAddPage: () => void;
  onDeletePage: (index: number) => void;
}

// ─── Mini layout thumbnail ──────────────────────────────────────────────────

function MiniLayoutPreview({ layout }: { layout: LayoutType }) {
  const img = "bg-indigo-200/60";
  const txt = "bg-amber-200/60";

  switch (layout) {
    case "full-bleed":
      return (
        <div className="relative h-full w-full">
          <div className={cn(img, "absolute inset-0 rounded-[1px]")} />
          <div
            className={cn(
              txt,
              "absolute bottom-0.5 left-0.5 right-0.5 h-[30%] rounded-[1px]"
            )}
          />
        </div>
      );
    case "top-image-bottom-text":
      return (
        <div className="flex h-full w-full flex-col gap-px">
          <div className={cn(img, "flex-[6] rounded-[1px]")} />
          <div className={cn(txt, "flex-[4] rounded-[1px]")} />
        </div>
      );
    case "bottom-image-top-text":
      return (
        <div className="flex h-full w-full flex-col gap-px">
          <div className={cn(txt, "flex-[4] rounded-[1px]")} />
          <div className={cn(img, "flex-[6] rounded-[1px]")} />
        </div>
      );
    case "left-image-right-text":
      return (
        <div className="flex h-full w-full flex-row gap-px">
          <div className={cn(img, "flex-1 rounded-[1px]")} />
          <div className={cn(txt, "flex-1 rounded-[1px]")} />
        </div>
      );
    case "right-image-left-text":
      return (
        <div className="flex h-full w-full flex-row gap-px">
          <div className={cn(txt, "flex-1 rounded-[1px]")} />
          <div className={cn(img, "flex-1 rounded-[1px]")} />
        </div>
      );
    case "text-only":
      return (
        <div className="flex h-full w-full items-center justify-center">
          <div className="flex flex-col gap-px p-1">
            <div className={cn(txt, "h-px w-8")} />
            <div className={cn(txt, "h-px w-6")} />
            <div className={cn(txt, "h-px w-7")} />
          </div>
        </div>
      );
    case "full-bleed-no-text":
      return <div className={cn(img, "h-full w-full rounded-[1px]")} />;
    default:
      return null;
  }
}

// ─── Component ──────────────────────────────────────────────────────────────

export function PageThumbnailStrip({
  pages,
  selectedIndex,
  onSelectPage,
  onReorderPages,
  onAddPage,
  onDeletePage,
}: PageThumbnailStripProps) {
  const [dragIndex, setDragIndex] = React.useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = React.useState<number | null>(null);

  const handleDragStart = React.useCallback(
    (e: React.DragEvent<HTMLDivElement>, index: number) => {
      setDragIndex(index);
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", String(index));
    },
    []
  );

  const handleDragOver = React.useCallback(
    (e: React.DragEvent<HTMLDivElement>, index: number) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverIndex(index);
    },
    []
  );

  const handleDragLeave = React.useCallback(() => {
    setDragOverIndex(null);
  }, []);

  const handleDrop = React.useCallback(
    (e: React.DragEvent<HTMLDivElement>, dropIndex: number) => {
      e.preventDefault();
      const fromIndex = dragIndex;
      setDragIndex(null);
      setDragOverIndex(null);

      if (fromIndex === null || fromIndex === dropIndex) return;

      const reordered = [...pages];
      const [moved] = reordered.splice(fromIndex, 1);
      reordered.splice(dropIndex, 0, moved);

      // Re-number pages
      const renumbered = reordered.map((page, i) => ({
        ...page,
        pageNumber: i + 1,
      }));

      onReorderPages(renumbered);

      // Update selection to follow the moved page
      if (selectedIndex === fromIndex) {
        onSelectPage(dropIndex);
      } else if (
        fromIndex < selectedIndex &&
        dropIndex >= selectedIndex
      ) {
        onSelectPage(selectedIndex - 1);
      } else if (
        fromIndex > selectedIndex &&
        dropIndex <= selectedIndex
      ) {
        onSelectPage(selectedIndex + 1);
      }
    },
    [dragIndex, pages, selectedIndex, onReorderPages, onSelectPage]
  );

  const handleDragEnd = React.useCallback(() => {
    setDragIndex(null);
    setDragOverIndex(null);
  }, []);

  return (
    <div className="flex h-full flex-col border-r bg-muted/30">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-3 py-2">
        <h3 className="text-sm font-semibold text-foreground">Pages</h3>
        <span className="text-xs text-muted-foreground">
          {pages.length} pages
        </span>
      </div>

      {/* Scrollable thumbnail list */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-2" role="listbox" aria-label="Page thumbnails">
          {pages.map((page, index) => {
            const isSelected = index === selectedIndex;
            const isDragging = index === dragIndex;
            const isDragOver = index === dragOverIndex && dragIndex !== null;

            return (
              <div
                key={page.id}
                role="option"
                aria-selected={isSelected}
                tabIndex={isSelected ? 0 : -1}
                draggable
                onDragStart={(e) => handleDragStart(e, index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, index)}
                onDragEnd={handleDragEnd}
                onClick={() => onSelectPage(index)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelectPage(index);
                  } else if (e.key === "ArrowDown" && index < pages.length - 1) {
                    e.preventDefault();
                    onSelectPage(index + 1);
                  } else if (e.key === "ArrowUp" && index > 0) {
                    e.preventDefault();
                    onSelectPage(index - 1);
                  }
                }}
                className={cn(
                  "group relative flex cursor-pointer items-center gap-2 rounded-md border p-1.5 transition-all duration-150",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                  isSelected
                    ? "border-primary bg-primary/5 ring-2 ring-primary/30"
                    : "border-transparent hover:border-muted-foreground/20 hover:bg-muted/50",
                  isDragging && "opacity-40",
                  isDragOver && "border-primary border-dashed bg-primary/10"
                )}
              >
                {/* Drag handle */}
                <div
                  className="flex cursor-grab items-center text-muted-foreground/50 transition-colors group-hover:text-muted-foreground active:cursor-grabbing"
                  aria-label="Drag to reorder"
                >
                  <GripVertical className="h-3.5 w-3.5" />
                </div>

                {/* Mini preview */}
                <div
                  className={cn(
                    "h-16 w-12 shrink-0 overflow-hidden rounded border bg-white p-0.5",
                    isSelected ? "border-primary/40" : "border-muted"
                  )}
                >
                  <MiniLayoutPreview layout={page.layout} />
                </div>

                {/* Page number */}
                <span
                  className={cn(
                    "text-xs font-medium",
                    isSelected
                      ? "text-primary"
                      : "text-muted-foreground"
                  )}
                >
                  {page.pageNumber}
                </span>
              </div>
            );
          })}
        </div>
      </ScrollArea>

      {/* Bottom actions */}
      <div className="flex gap-1 border-t p-2">
        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={onAddPage}
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                Add
              </Button>
            </TooltipTrigger>
            <TooltipContent>Add a new page</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 text-destructive hover:bg-destructive/10 hover:text-destructive"
                onClick={() => onDeletePage(selectedIndex)}
                disabled={pages.length <= 1}
              >
                <Trash2 className="mr-1 h-3.5 w-3.5" />
                Delete
              </Button>
            </TooltipTrigger>
            <TooltipContent>Delete selected page</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
}
