"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  BookOpen,
  GripVertical,
  Plus,
  Download,
  CheckCircle2,
  Lock,
  Unlock,
  Layers,
  Palette,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type VolumeStatus = "draft" | "generating" | "qa-review" | "ready" | "exported";

export interface Volume {
  id: string;
  volumeNumber: number;
  title: string;
  theme: string;
  pageCount: number;
  status: VolumeStatus;
  qaScore: number; // 0-100
}

export type BadgeStyle = "circle" | "ribbon" | "banner" | "badge" | "minimal";

export interface BrandingTemplate {
  titleFontLocked: boolean;
  titlePositionLocked: boolean;
  authorPositionLocked: boolean;
  badgeStyle: BadgeStyle;
}

export interface VolumeFactoryProps {
  seriesName: string;
  volumes: Volume[];
  branding: BrandingTemplate;
  onBrandingChange: (branding: BrandingTemplate) => void;
  onAutoGenerateNext: (theme: string) => void;
  onBatchExportAll: () => void;
  onReorderVolumes: (volumes: Volume[]) => void;
  isGenerating: boolean;
  isExporting: boolean;
}

// ---------------------------------------------------------------------------
// Status config
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  VolumeStatus,
  { label: string; className: string }
> = {
  draft: { label: "Draft", className: "bg-muted text-muted-foreground" },
  generating: {
    label: "Generating",
    className: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  },
  "qa-review": {
    label: "QA Review",
    className:
      "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  },
  ready: {
    label: "Ready",
    className:
      "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  },
  exported: {
    label: "Exported",
    className:
      "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  },
};

const BADGE_STYLES: { value: BadgeStyle; label: string }[] = [
  { value: "circle", label: "Circle" },
  { value: "ribbon", label: "Ribbon" },
  { value: "banner", label: "Banner" },
  { value: "badge", label: "Badge" },
  { value: "minimal", label: "Minimal" },
];

// ---------------------------------------------------------------------------
// QA Score Ring (small)
// ---------------------------------------------------------------------------

function QAScoreRing({ score }: { score: number }) {
  const radius = 14;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 80
      ? "text-green-500"
      : score >= 60
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="relative h-8 w-8 shrink-0">
      <svg className="h-8 w-8 -rotate-90" viewBox="0 0 32 32">
        <circle
          cx="16"
          cy="16"
          r={radius}
          fill="none"
          className="stroke-muted"
          strokeWidth="2.5"
        />
        <circle
          cx="16"
          cy="16"
          r={radius}
          fill="none"
          className={cn("stroke-current", color)}
          strokeWidth="2.5"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[9px] font-semibold">
        {score}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Volume Card
// ---------------------------------------------------------------------------

interface VolumeCardProps {
  volume: Volume;
  onDragStart: (e: React.DragEvent, index: number) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, index: number) => void;
  index: number;
}

function VolumeCard({
  volume,
  onDragStart,
  onDragOver,
  onDrop,
  index,
}: VolumeCardProps) {
  const statusCfg = STATUS_CONFIG[volume.status];

  return (
    <Card
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, index)}
      className="p-4 cursor-grab active:cursor-grabbing hover:ring-2 hover:ring-primary/30 transition-all"
    >
      <div className="flex items-start gap-3">
        <GripVertical className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />

        <div className="flex-1 min-w-0 space-y-2">
          {/* Top row: volume number + title */}
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] shrink-0">
              Vol. {volume.volumeNumber}
            </Badge>
            <h4 className="text-sm font-semibold truncate">{volume.title}</h4>
          </div>

          {/* Meta row */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Palette className="h-3 w-3" />
              {volume.theme}
            </span>
            <span className="flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              {volume.pageCount}p
            </span>
          </div>

          {/* Status + QA */}
          <div className="flex items-center justify-between">
            <Badge
              variant="secondary"
              className={cn("text-[10px]", statusCfg.className)}
            >
              {statusCfg.label}
            </Badge>
            <QAScoreRing score={volume.qaScore} />
          </div>
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Spine Layout Preview
// ---------------------------------------------------------------------------

function SpinePreview({ badgeStyle }: { badgeStyle: BadgeStyle }) {
  return (
    <div className="flex items-center justify-center p-3">
      <div className="w-8 h-40 bg-muted rounded border flex flex-col items-center justify-between py-2">
        {/* Title area */}
        <div className="w-5 h-1 bg-foreground/30 rounded" />
        <div className="w-5 h-1 bg-foreground/30 rounded" />

        {/* Volume badge */}
        <div
          className={cn(
            "flex items-center justify-center text-[7px] font-bold",
            badgeStyle === "circle" &&
              "h-5 w-5 rounded-full border-2 border-foreground/40",
            badgeStyle === "ribbon" &&
              "h-4 w-6 bg-foreground/20 rounded-sm",
            badgeStyle === "banner" &&
              "h-5 w-7 bg-foreground/20 rounded",
            badgeStyle === "badge" &&
              "h-5 w-5 rounded border border-foreground/40 bg-foreground/10",
            badgeStyle === "minimal" && "h-4 w-4"
          )}
        >
          1
        </div>

        {/* Author area */}
        <div className="w-4 h-1 bg-foreground/20 rounded" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// VolumeFactory
// ---------------------------------------------------------------------------

export function VolumeFactory({
  seriesName,
  volumes,
  branding,
  onBrandingChange,
  onAutoGenerateNext,
  onBatchExportAll,
  onReorderVolumes,
  isGenerating,
  isExporting,
}: VolumeFactoryProps) {
  const [newTheme, setNewTheme] = React.useState("");
  const dragIndexRef = React.useRef<number | null>(null);

  // --- Drag & drop ---
  const handleDragStart = (_e: React.DragEvent, index: number) => {
    dragIndexRef.current = index;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (_e: React.DragEvent, dropIndex: number) => {
    const dragIndex = dragIndexRef.current;
    if (dragIndex === null || dragIndex === dropIndex) return;

    const updated = [...volumes];
    const [dragged] = updated.splice(dragIndex, 1);
    updated.splice(dropIndex, 0, dragged);

    onReorderVolumes(
      updated.map((v, i) => ({ ...v, volumeNumber: i + 1 }))
    );
    dragIndexRef.current = null;
  };

  const handleAutoGenerate = () => {
    if (newTheme.trim()) {
      onAutoGenerateNext(newTheme.trim());
      setNewTheme("");
    }
  };

  // --- Branding helpers ---
  const updateBranding = (patch: Partial<BrandingTemplate>) => {
    onBrandingChange({ ...branding, ...patch });
  };

  const brandingLocked =
    branding.titleFontLocked &&
    branding.titlePositionLocked &&
    branding.authorPositionLocked;

  return (
    <div className="space-y-6">
      {/* Series header */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">{seriesName}</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              {volumes.length} volume{volumes.length !== 1 && "s"}
              <span className="mx-2">|</span>
              Branding:{" "}
              <Badge
                variant={brandingLocked ? "default" : "outline"}
                className="text-[10px] ml-1"
              >
                {brandingLocked ? (
                  <span className="flex items-center gap-1">
                    <Lock className="h-3 w-3" /> Locked
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <Unlock className="h-3 w-3" /> Unlocked
                  </span>
                )}
              </Badge>
            </p>
          </div>
        </div>
      </Card>

      {/* Two-column layout: volumes + branding */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Volume cards grid (2/3) */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold">Volumes</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {volumes.map((volume, index) => (
              <VolumeCard
                key={volume.id}
                volume={volume}
                index={index}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              />
            ))}
          </div>

          {volumes.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-sm text-muted-foreground border rounded-lg border-dashed">
              <BookOpen className="h-8 w-8 mb-2" />
              <p>No volumes yet. Generate your first volume below.</p>
            </div>
          )}

          {/* Auto-generate next volume */}
          <Card className="p-4">
            <h4 className="text-sm font-semibold mb-3">
              Auto-Generate Next Volume
            </h4>
            <div className="flex items-end gap-3">
              <div className="flex-1 space-y-1.5">
                <Label htmlFor="new-theme" className="text-xs">
                  Theme for Volume {volumes.length + 1}
                </Label>
                <Input
                  id="new-theme"
                  value={newTheme}
                  onChange={(e) => setNewTheme(e.target.value)}
                  placeholder="e.g., Ocean Animals, Tropical Flowers..."
                  disabled={isGenerating}
                />
              </div>
              <Button
                onClick={handleAutoGenerate}
                disabled={!newTheme.trim() || isGenerating}
              >
                <Plus className="h-4 w-4 mr-1.5" />
                {isGenerating ? "Generating..." : "Generate"}
              </Button>
            </div>
          </Card>

          {/* Batch export */}
          <Button
            variant="outline"
            className="w-full"
            onClick={onBatchExportAll}
            disabled={volumes.length === 0 || isExporting}
          >
            <Download className="h-4 w-4 mr-1.5" />
            {isExporting
              ? "Exporting..."
              : `Batch Export All Volumes (${volumes.length})`}
          </Button>
        </div>

        {/* Branding template panel (1/3) */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold">Branding Template</h3>

          <Card className="p-4 space-y-4">
            {/* Title font lock */}
            <div className="flex items-center justify-between">
              <Label htmlFor="title-font-lock" className="text-sm">
                Title Font
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground">
                  {branding.titleFontLocked ? "Locked" : "Unlocked"}
                </span>
                <Switch
                  id="title-font-lock"
                  checked={branding.titleFontLocked}
                  onCheckedChange={(v) =>
                    updateBranding({ titleFontLocked: v })
                  }
                />
              </div>
            </div>

            {/* Title position lock */}
            <div className="flex items-center justify-between">
              <Label htmlFor="title-pos-lock" className="text-sm">
                Title Position
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground">
                  {branding.titlePositionLocked ? "Locked" : "Unlocked"}
                </span>
                <Switch
                  id="title-pos-lock"
                  checked={branding.titlePositionLocked}
                  onCheckedChange={(v) =>
                    updateBranding({ titlePositionLocked: v })
                  }
                />
              </div>
            </div>

            {/* Author position lock */}
            <div className="flex items-center justify-between">
              <Label htmlFor="author-pos-lock" className="text-sm">
                Author Position
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground">
                  {branding.authorPositionLocked ? "Locked" : "Unlocked"}
                </span>
                <Switch
                  id="author-pos-lock"
                  checked={branding.authorPositionLocked}
                  onCheckedChange={(v) =>
                    updateBranding({ authorPositionLocked: v })
                  }
                />
              </div>
            </div>

            <Separator />

            {/* Volume badge style */}
            <div className="space-y-1.5">
              <Label className="text-sm">Volume Badge Style</Label>
              <Select
                value={branding.badgeStyle}
                onValueChange={(v) =>
                  updateBranding({ badgeStyle: v as BadgeStyle })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {BADGE_STYLES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator />

            {/* Spine layout preview */}
            <div className="space-y-1.5">
              <Label className="text-sm">Spine Layout Preview</Label>
              <div className="border rounded-lg bg-muted/30">
                <SpinePreview badgeStyle={branding.badgeStyle} />
              </div>
            </div>
          </Card>

          {/* Lock all status */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
            {brandingLocked ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                All branding settings are locked. New volumes will use this
                template.
              </>
            ) : (
              <>
                <Unlock className="h-4 w-4" />
                Some branding settings are unlocked. New volumes may have
                inconsistent styling.
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
