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
  Plus,
  Lock,
  Unlock,
  CheckCircle2,
  AlertTriangle,
  Info,
  Layers,
  Type,
  User,
  Hash,
  AlignVerticalJustifyCenter,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BrandingConfig {
  titleFont: string | null;
  titlePosition: string;
  authorPosition: string;
  volumeBadge: {
    enabled: boolean;
    position: string;
    style: string;
  };
  spineLayout: {
    titleOrientation: string;
    authorOrientation: string;
    volumeNumber: boolean;
  };
  colorScheme: string | null;
}

export interface SeriesVolume {
  id: string;
  title: string;
  volumeNumber: number;
  pageCount: number;
  status: string;
}

export interface Series {
  id: string;
  name: string;
  bookType: string;
  namingFormat: string;
  brandingConfig: BrandingConfig;
  brandingLocked: boolean;
  volumeCount: number;
  volumes: SeriesVolume[];
}

export interface CoherenceIssue {
  field: string;
  severity: "error" | "warning" | "info";
  message: string;
}

export interface CoherenceResult {
  score: number;
  issues: CoherenceIssue[];
}

export interface SeriesManagerProps {
  seriesList: Series[];
  selectedSeriesId: string | null;
  onSelectSeries: (id: string) => void;
  onCreateSeries: (name: string, bookType: string, namingFormat: string) => void;
  onLockBranding: (seriesId: string) => void;
  onUnlockBranding: (seriesId: string) => void;
  onUpdateBranding: (seriesId: string, config: BrandingConfig) => void;
  onCheckCoherence: (seriesId: string) => void;
  onAddVolume: (seriesId: string) => void;
  coherenceResult: CoherenceResult | null;
  isCheckingCoherence: boolean;
}

// ---------------------------------------------------------------------------
// Severity icon helper
// ---------------------------------------------------------------------------

function SeverityIcon({ severity }: { severity: string }) {
  if (severity === "error") {
    return <AlertTriangle className="h-4 w-4 text-red-500" />;
  }
  if (severity === "warning") {
    return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
  }
  return <Info className="h-4 w-4 text-blue-500" />;
}

// ---------------------------------------------------------------------------
// Coherence score ring
// ---------------------------------------------------------------------------

function CoherenceRing({ score }: { score: number }) {
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score >= 80
      ? "text-green-500"
      : score >= 50
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="relative h-14 w-14 shrink-0">
      <svg className="h-14 w-14 -rotate-90" viewBox="0 0 44 44">
        <circle cx="22" cy="22" r={radius} fill="none" className="stroke-muted" strokeWidth="3" />
        <circle
          cx="22"
          cy="22"
          r={radius}
          fill="none"
          className={cn("stroke-current", color)}
          strokeWidth="3"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">
        {Math.round(score)}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Spine preview (simplified visual)
// ---------------------------------------------------------------------------

function SpinePreview({ series }: { series: Series }) {
  const spine = series.brandingConfig.spineLayout;

  return (
    <Card className="p-3">
      <Label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Spine Preview
      </Label>
      <div className="mx-auto flex h-48 w-8 flex-col items-center justify-between rounded border bg-muted/50 py-2">
        <span
          className="text-[7px] font-bold"
          style={{
            writingMode:
              spine.titleOrientation === "vertical" ? "vertical-rl" : undefined,
          }}
        >
          {series.name}
        </span>
        {spine.volumeNumber && (
          <span className="rounded-full bg-primary/20 px-1 text-[6px] font-bold">
            V{series.volumeCount || 1}
          </span>
        )}
        <span
          className="text-[6px] text-muted-foreground"
          style={{
            writingMode:
              spine.authorOrientation === "vertical" ? "vertical-rl" : undefined,
          }}
        >
          Author
        </span>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Create series form
// ---------------------------------------------------------------------------

function CreateSeriesForm({
  onSubmit,
}: {
  onSubmit: (name: string, bookType: string, namingFormat: string) => void;
}) {
  const [name, setName] = React.useState("");
  const [bookType, setBookType] = React.useState("coloring");
  const [namingFormat, setNamingFormat] = React.useState("{series_name} Vol. {volume}");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit(name.trim(), bookType, namingFormat);
    setName("");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
      <div className="space-y-1">
        <Label htmlFor="series-name">Series Name</Label>
        <Input
          id="series-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Animal Adventures"
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="book-type">Book Type</Label>
        <Select value={bookType} onValueChange={setBookType}>
          <SelectTrigger id="book-type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="childrens">Children&apos;s Books</SelectItem>
            <SelectItem value="coloring">Coloring Books</SelectItem>
            <SelectItem value="puzzle">Puzzle Books</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1">
        <Label htmlFor="naming-format">Naming Format</Label>
        <Input
          id="naming-format"
          value={namingFormat}
          onChange={(e) => setNamingFormat(e.target.value)}
          placeholder="{series_name} Vol. {volume} - {theme}"
        />
        <p className="text-xs text-muted-foreground">
          Placeholders: {"{series_name}"}, {"{volume}"}, {"{theme}"}
        </p>
      </div>
      <Button type="submit" size="sm" disabled={!name.trim()}>
        <Plus className="mr-1 h-4 w-4" />
        Create Series
      </Button>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function SeriesManager({
  seriesList,
  selectedSeriesId,
  onSelectSeries,
  onCreateSeries,
  onLockBranding,
  onUnlockBranding,
  onUpdateBranding,
  onCheckCoherence,
  onAddVolume,
  coherenceResult,
  isCheckingCoherence,
}: SeriesManagerProps) {
  const [showCreateForm, setShowCreateForm] = React.useState(false);

  const selected = seriesList.find((s) => s.id === selectedSeriesId) ?? null;

  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------------- */}
      {/* Series list                                                       */}
      {/* ----------------------------------------------------------------- */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Series</h3>
          <Button variant="outline" size="sm" onClick={() => setShowCreateForm((v) => !v)}>
            <Plus className="mr-1 h-4 w-4" />
            New Series
          </Button>
        </div>

        {showCreateForm && (
          <CreateSeriesForm
            onSubmit={(name, bookType, fmt) => {
              onCreateSeries(name, bookType, fmt);
              setShowCreateForm(false);
            }}
          />
        )}

        <div className="space-y-2">
          {seriesList.map((series) => (
            <Card
              key={series.id}
              className={cn(
                "flex cursor-pointer items-center gap-3 p-3 transition-colors hover:bg-muted/50",
                series.id === selectedSeriesId && "border-primary bg-muted/30",
              )}
              onClick={() => onSelectSeries(series.id)}
            >
              <BookOpen className="h-5 w-5 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{series.name}</p>
                <p className="text-xs text-muted-foreground">
                  {series.volumeCount} volume{series.volumeCount !== 1 ? "s" : ""} &middot;{" "}
                  {series.bookType}
                </p>
              </div>
              {series.brandingLocked ? (
                <Lock className="h-4 w-4 text-green-500" />
              ) : (
                <Unlock className="h-4 w-4 text-muted-foreground" />
              )}
            </Card>
          ))}

          {seriesList.length === 0 && !showCreateForm && (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No series yet. Create one to start managing volumes.
            </p>
          )}
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Series detail                                                     */}
      {/* ----------------------------------------------------------------- */}
      {selected && (
        <>
          <Separator />
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">{selected.name}</h3>

            {/* Naming format */}
            <div className="space-y-1">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Naming Format
              </Label>
              <p className="text-sm">{selected.namingFormat || "Not set"}</p>
            </div>

            {/* Branding lock toggles */}
            <Card className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">Branding Configuration</Label>
                <Button
                  variant={selected.brandingLocked ? "default" : "outline"}
                  size="sm"
                  onClick={() =>
                    selected.brandingLocked
                      ? onUnlockBranding(selected.id)
                      : onLockBranding(selected.id)
                  }
                >
                  {selected.brandingLocked ? (
                    <>
                      <Lock className="mr-1 h-3 w-3" />
                      Locked
                    </>
                  ) : (
                    <>
                      <Unlock className="mr-1 h-3 w-3" />
                      Lock Branding
                    </>
                  )}
                </Button>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {/* Title font */}
                <div className="flex items-center gap-2 rounded border p-2">
                  <Type className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="text-xs font-medium">Title Font</p>
                    <p className="text-xs text-muted-foreground">
                      {selected.brandingConfig.titleFont || "Default"}
                    </p>
                  </div>
                  {selected.brandingLocked && <Lock className="h-3 w-3 text-green-500" />}
                </div>

                {/* Title position */}
                <div className="flex items-center gap-2 rounded border p-2">
                  <AlignVerticalJustifyCenter className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="text-xs font-medium">Title Position</p>
                    <p className="text-xs text-muted-foreground">
                      {selected.brandingConfig.titlePosition}
                    </p>
                  </div>
                  {selected.brandingLocked && <Lock className="h-3 w-3 text-green-500" />}
                </div>

                {/* Author position */}
                <div className="flex items-center gap-2 rounded border p-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="text-xs font-medium">Author Position</p>
                    <p className="text-xs text-muted-foreground">
                      {selected.brandingConfig.authorPosition}
                    </p>
                  </div>
                  {selected.brandingLocked && <Lock className="h-3 w-3 text-green-500" />}
                </div>

                {/* Volume badge */}
                <div className="flex items-center gap-2 rounded border p-2">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="text-xs font-medium">Volume Badge</p>
                    <p className="text-xs text-muted-foreground">
                      {selected.brandingConfig.volumeBadge.enabled
                        ? `${selected.brandingConfig.volumeBadge.style} - ${selected.brandingConfig.volumeBadge.position}`
                        : "Disabled"}
                    </p>
                  </div>
                  {selected.brandingLocked && <Lock className="h-3 w-3 text-green-500" />}
                </div>
              </div>
            </Card>

            {/* Spine preview */}
            <SpinePreview series={selected} />

            {/* Coherence check */}
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">Theme Coherence</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onCheckCoherence(selected.id)}
                  disabled={isCheckingCoherence}
                >
                  {isCheckingCoherence ? (
                    <>
                      <span className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Checking...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Check Coherence
                    </>
                  )}
                </Button>
              </div>

              {coherenceResult && (
                <div className="mt-3 space-y-3">
                  <div className="flex items-center gap-4">
                    <CoherenceRing score={coherenceResult.score} />
                    <div>
                      <p className="font-medium">
                        {coherenceResult.score >= 80
                          ? "Strong coherence"
                          : coherenceResult.score >= 50
                            ? "Moderate coherence"
                            : "Low coherence"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {coherenceResult.issues.length} issue
                        {coherenceResult.issues.length !== 1 ? "s" : ""} found
                      </p>
                    </div>
                  </div>

                  {coherenceResult.issues.length > 0 && (
                    <div className="space-y-2">
                      {coherenceResult.issues.map((issue, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 rounded border p-2 text-sm"
                        >
                          <SeverityIcon severity={issue.severity} />
                          <p className="flex-1">{issue.message}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* Volume list */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">
                  Volumes ({selected.volumes.length})
                </Label>
                <Button variant="outline" size="sm" onClick={() => onAddVolume(selected.id)}>
                  <Plus className="mr-1 h-3 w-3" />
                  Add Volume
                </Button>
              </div>

              {selected.volumes.map((vol) => (
                <Card key={vol.id} className="flex items-center gap-3 p-3">
                  <Layers className="h-4 w-4 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{vol.title}</p>
                    <p className="text-xs text-muted-foreground">
                      Vol. {vol.volumeNumber} &middot; {vol.pageCount} pages
                    </p>
                  </div>
                  <Badge variant={vol.status === "published" ? "default" : "secondary"}>
                    {vol.status}
                  </Badge>
                </Card>
              ))}

              {selected.volumes.length === 0 && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No volumes in this series yet.
                </p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
