"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  GripVertical,
  Plus,
  X,
  BookOpen,
  Layers,
  FileText,
  Hash,
  ArrowUp,
  ArrowDown,
  Package,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BundleVolume {
  id: string;
  title: string;
  volumeNumber: number;
  pageCount: number;
  status: string;
}

export interface BundleSection {
  type: "divider" | "content";
  volumeIndex: number;
  volumeId: string;
  title: string;
  startPage: number;
  pageCount?: number;
}

export interface BundleTocEntry {
  volumeIndex: number;
  volumeId: string;
  title: string;
  startPage: number;
  endPage: number;
}

export interface BundlePreview {
  toc: BundleTocEntry[];
  sections: BundleSection[];
  totalPages: number;
}

export interface BundleCreatorProps {
  availableVolumes: BundleVolume[];
  selectedVolumeIds: string[];
  bundleTitle: string;
  seriesId: string | null;
  onTitleChange: (title: string) => void;
  onAddVolume: (volumeId: string) => void;
  onRemoveVolume: (volumeId: string) => void;
  onReorderVolumes: (volumeIds: string[]) => void;
  onCreateBundle: () => void;
  bundlePreview: BundlePreview | null;
  isCreating: boolean;
}

// ---------------------------------------------------------------------------
// Volume selector
// ---------------------------------------------------------------------------

function VolumeSelector({
  available,
  selected,
  onAdd,
}: {
  available: BundleVolume[];
  selected: string[];
  onAdd: (id: string) => void;
}) {
  const unselected = available.filter((v) => !selected.includes(v.id));

  if (unselected.length === 0) {
    return (
      <p className="py-2 text-center text-xs text-muted-foreground">
        All available volumes have been added.
      </p>
    );
  }

  return (
    <div className="space-y-1">
      {unselected.map((vol) => (
        <div
          key={vol.id}
          className="flex items-center gap-2 rounded border p-2 text-sm hover:bg-muted/30"
        >
          <BookOpen className="h-4 w-4 text-muted-foreground" />
          <span className="flex-1 truncate">{vol.title}</span>
          <span className="text-xs text-muted-foreground">{vol.pageCount}p</span>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => onAdd(vol.id)}>
            <Plus className="h-3 w-3" />
          </Button>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Selected volumes list (reorderable)
// ---------------------------------------------------------------------------

function SelectedVolumesList({
  volumes,
  selectedIds,
  onRemove,
  onMoveUp,
  onMoveDown,
}: {
  volumes: BundleVolume[];
  selectedIds: string[];
  onRemove: (id: string) => void;
  onMoveUp: (index: number) => void;
  onMoveDown: (index: number) => void;
}) {
  const orderedVolumes = selectedIds
    .map((id) => volumes.find((v) => v.id === id))
    .filter(Boolean) as BundleVolume[];

  if (orderedVolumes.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No volumes selected. Add volumes from the list above.
      </p>
    );
  }

  return (
    <div className="space-y-1">
      {orderedVolumes.map((vol, idx) => (
        <div
          key={vol.id}
          className="flex items-center gap-2 rounded border bg-muted/20 p-2 text-sm"
        >
          <GripVertical className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Hash className="h-3 w-3 text-muted-foreground" />
          <span className="w-4 text-xs font-bold">{idx + 1}</span>
          <span className="flex-1 truncate font-medium">{vol.title}</span>
          <span className="text-xs text-muted-foreground">{vol.pageCount}p</span>
          <div className="flex gap-0.5">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => onMoveUp(idx)}
              disabled={idx === 0}
            >
              <ArrowUp className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => onMoveDown(idx)}
              disabled={idx === orderedVolumes.length - 1}
            >
              <ArrowDown className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-red-500 hover:text-red-600"
              onClick={() => onRemove(vol.id)}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bundle preview
// ---------------------------------------------------------------------------

function BundlePreviewPanel({ preview }: { preview: BundlePreview }) {
  return (
    <Card className="space-y-3 p-4">
      <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Bundle Preview
      </Label>

      {/* Combined TOC */}
      <div className="space-y-1">
        <p className="text-xs font-semibold">Table of Contents</p>
        {preview.toc.map((entry) => (
          <div key={entry.volumeIndex} className="flex items-center gap-2 text-xs">
            <span className="w-8 text-right text-muted-foreground">p.{entry.startPage}</span>
            <span className="flex-1 truncate">{entry.title}</span>
            <span className="text-muted-foreground">
              {entry.endPage - entry.startPage + 1} pages
            </span>
          </div>
        ))}
      </div>

      <Separator />

      {/* Sections */}
      <div className="space-y-1">
        <p className="text-xs font-semibold">Sections</p>
        {preview.sections.map((section, idx) => (
          <div
            key={idx}
            className={cn(
              "flex items-center gap-2 rounded px-2 py-1 text-xs",
              section.type === "divider" ? "bg-muted/50 font-medium" : "",
            )}
          >
            {section.type === "divider" ? (
              <FileText className="h-3 w-3 text-muted-foreground" />
            ) : (
              <Layers className="h-3 w-3 text-muted-foreground" />
            )}
            <span className="flex-1 truncate">
              {section.type === "divider" ? `--- ${section.title} ---` : section.title}
            </span>
            {section.pageCount && (
              <span className="text-muted-foreground">{section.pageCount}p</span>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function BundleCreator({
  availableVolumes,
  selectedVolumeIds,
  bundleTitle,
  seriesId,
  onTitleChange,
  onAddVolume,
  onRemoveVolume,
  onReorderVolumes,
  onCreateBundle,
  bundlePreview,
  isCreating,
}: BundleCreatorProps) {
  const totalPages = bundlePreview?.totalPages ?? 0;

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newOrder = [...selectedVolumeIds];
    [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
    onReorderVolumes(newOrder);
  };

  const handleMoveDown = (index: number) => {
    if (index >= selectedVolumeIds.length - 1) return;
    const newOrder = [...selectedVolumeIds];
    [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
    onReorderVolumes(newOrder);
  };

  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------------- */}
      {/* Bundle title                                                      */}
      {/* ----------------------------------------------------------------- */}
      <div className="space-y-1">
        <Label htmlFor="bundle-title">Bundle Title</Label>
        <Input
          id="bundle-title"
          value={bundleTitle}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="e.g. Animal Adventures: Complete Collection"
        />
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Available volumes                                                 */}
      {/* ----------------------------------------------------------------- */}
      <div className="space-y-2">
        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Available Volumes
        </Label>
        <VolumeSelector
          available={availableVolumes}
          selected={selectedVolumeIds}
          onAdd={onAddVolume}
        />
      </div>

      <Separator />

      {/* ----------------------------------------------------------------- */}
      {/* Selected volumes (reorderable)                                    */}
      {/* ----------------------------------------------------------------- */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Bundle Contents ({selectedVolumeIds.length} volumes)
          </Label>
          {totalPages > 0 && (
            <Badge variant="secondary" className="text-xs">
              {totalPages} total pages
            </Badge>
          )}
        </div>
        <SelectedVolumesList
          volumes={availableVolumes}
          selectedIds={selectedVolumeIds}
          onRemove={onRemoveVolume}
          onMoveUp={handleMoveUp}
          onMoveDown={handleMoveDown}
        />
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Bundle preview                                                    */}
      {/* ----------------------------------------------------------------- */}
      {bundlePreview && (
        <>
          <Separator />
          <BundlePreviewPanel preview={bundlePreview} />
        </>
      )}

      {/* ----------------------------------------------------------------- */}
      {/* Total page count + Create button                                  */}
      {/* ----------------------------------------------------------------- */}
      <div className="flex items-center justify-between rounded-lg border p-4">
        <div>
          <p className="text-sm font-medium">Total Page Count</p>
          <p className="text-2xl font-bold">{totalPages || "--"}</p>
        </div>
        <Button
          onClick={onCreateBundle}
          disabled={selectedVolumeIds.length < 2 || !bundleTitle.trim() || isCreating}
        >
          {isCreating ? (
            <>
              <span className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              Creating...
            </>
          ) : (
            <>
              <Package className="mr-1 h-4 w-4" />
              Create Bundle
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
