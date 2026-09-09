"use client";

import { useState } from "react";
import {
  ZoomIn,
  ArrowRight,
  Info,
  Columns2,
  RefreshCw,
  Grid3X3,
  Type,
  List,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ─── Types ──────────────────────────────────────────────────────────────────

type ScaleFactor = "125" | "150" | "175";

interface AdjustmentNote {
  icon: typeof Grid3X3;
  label: string;
  original: string;
  adjusted: string;
}

interface LargePrintGeneratorProps {
  bookId: string;
  bookTitle: string;
  totalPuzzles: number;
  onGenerate: (scale: number) => void;
  isGenerating?: boolean;
  generatedEditionId?: string | null;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const SCALE_OPTIONS: { value: ScaleFactor; label: string; description: string }[] = [
  {
    value: "125",
    label: "125%",
    description: "Slightly enlarged - good for general readability",
  },
  {
    value: "150",
    label: "150%",
    description: "Standard large print - recommended for seniors",
  },
  {
    value: "175",
    label: "175%",
    description: "Extra large print - maximum accessibility",
  },
];

function getAdjustments(scale: ScaleFactor): AdjustmentNote[] {
  switch (scale) {
    case "125":
      return [
        {
          icon: Grid3X3,
          label: "Grid Size",
          original: "15x15",
          adjusted: "12x12 (may reduce to fit)",
        },
        {
          icon: List,
          label: "Words per Puzzle",
          original: "15 words",
          adjusted: "12 words (reduced to fit)",
        },
        {
          icon: Type,
          label: "Letter Spacing",
          original: "Normal",
          adjusted: "+15% increased",
        },
      ];
    case "150":
      return [
        {
          icon: Grid3X3,
          label: "Grid Size",
          original: "15x15",
          adjusted: "10x10 (reduced to fit)",
        },
        {
          icon: List,
          label: "Words per Puzzle",
          original: "15 words",
          adjusted: "10 words (reduced to fit)",
        },
        {
          icon: Type,
          label: "Letter Spacing",
          original: "Normal",
          adjusted: "+25% increased",
        },
      ];
    case "175":
      return [
        {
          icon: Grid3X3,
          label: "Grid Size",
          original: "15x15",
          adjusted: "8x8 (significantly reduced)",
        },
        {
          icon: List,
          label: "Words per Puzzle",
          original: "15 words",
          adjusted: "8 words (significantly reduced)",
        },
        {
          icon: Type,
          label: "Letter Spacing",
          original: "Normal",
          adjusted: "+35% increased",
        },
      ];
  }
}

// ─── Component ──────────────────────────────────────────────────────────────

export function LargePrintGenerator({
  bookId,
  bookTitle,
  totalPuzzles,
  onGenerate,
  isGenerating,
  generatedEditionId,
}: LargePrintGeneratorProps) {
  const [scale, setScale] = useState<ScaleFactor>("150");

  const adjustments = getAdjustments(scale);
  const selectedOption = SCALE_OPTIONS.find((o) => o.value === scale)!;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">Large Print Edition</h2>
        <p className="text-sm text-muted-foreground">
          Generate a large print variant of &quot;{bookTitle}&quot; with{" "}
          {totalPuzzles} puzzles. Massive market, especially for seniors.
        </p>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <Info className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">Original book is unchanged</p>
          <p>
            This creates a new book copy with enlarged text and grids. Your
            original puzzle book will not be modified.
          </p>
        </div>
      </div>

      {/* ── Scale Selector ─────────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <Label className="font-medium">Scale Factor</Label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {SCALE_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setScale(option.value)}
              className={`border-2 rounded-lg p-4 text-left transition-colors ${
                scale === option.value
                  ? "border-primary bg-primary/5"
                  : "border-muted hover:border-muted-foreground/30"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <ZoomIn className="h-4 w-4" />
                <span className="font-semibold text-lg">{option.label}</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {option.description}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* ── Before/After Preview ────────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <h3 className="font-medium flex items-center gap-2">
          <Columns2 className="h-4 w-4" />
          Preview Comparison
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Original */}
          <div className="border rounded-lg p-4 space-y-3">
            <Badge variant="outline">Original</Badge>
            <div className="bg-white border rounded p-4 font-mono text-center space-y-2">
              <div className="grid grid-cols-5 gap-1 max-w-[160px] mx-auto">
                {Array.from({ length: 25 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-7 h-7 border flex items-center justify-center text-[10px]"
                  >
                    {String.fromCharCode(65 + (i % 26))}
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Standard size grid with normal letter spacing
              </p>
            </div>
          </div>

          {/* Large Print */}
          <div className="border rounded-lg p-4 space-y-3 bg-primary/5">
            <Badge>Large Print ({selectedOption.label})</Badge>
            <div className="bg-white border rounded p-4 font-mono text-center space-y-2">
              <div
                className="grid gap-1.5 max-w-[200px] mx-auto"
                style={{
                  gridTemplateColumns: `repeat(${
                    scale === "175" ? 3 : scale === "150" ? 4 : 4
                  }, 1fr)`,
                }}
              >
                {Array.from({
                  length: scale === "175" ? 9 : scale === "150" ? 16 : 16,
                }).map((_, i) => (
                  <div
                    key={i}
                    className={`border flex items-center justify-center font-bold ${
                      scale === "175"
                        ? "w-12 h-12 text-lg"
                        : scale === "150"
                        ? "w-10 h-10 text-base"
                        : "w-9 h-9 text-sm"
                    }`}
                    style={{
                      letterSpacing:
                        scale === "175"
                          ? "0.1em"
                          : scale === "150"
                          ? "0.06em"
                          : "0.04em",
                    }}
                  >
                    {String.fromCharCode(65 + (i % 26))}
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Enlarged grid with increased letter spacing
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Auto-Adjustment Notes ──────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-3">
        <h3 className="font-medium">Auto-Adjustments at {selectedOption.label}</h3>
        <div className="space-y-2">
          {adjustments.map((adj, i) => {
            const Icon = adj.icon;
            return (
              <div
                key={i}
                className="flex items-center gap-3 py-2 px-3 rounded-md bg-muted/30"
              >
                <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                <span className="text-sm font-medium w-36">{adj.label}</span>
                <span className="text-sm text-muted-foreground">
                  {adj.original}
                </span>
                <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                <span className="text-sm font-medium">{adj.adjusted}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Generate Button ────────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-t pt-4">
        {generatedEditionId && (
          <p className="text-sm text-green-700">
            Large print edition generated successfully.
          </p>
        )}
        <div className="ml-auto">
          <Button
            size="lg"
            onClick={() => onGenerate(Number(scale))}
            disabled={isGenerating || totalPuzzles === 0}
          >
            {isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Generating Large Print Edition...
              </>
            ) : (
              <>
                <ZoomIn className="h-4 w-4 mr-2" />
                Generate Large Print Edition
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
