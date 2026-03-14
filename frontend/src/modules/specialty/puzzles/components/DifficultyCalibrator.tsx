"use client";

import { useState, useCallback, useMemo } from "react";
import {
  BarChart3,
  RefreshCw,
  GripVertical,
  TrendingUp,
  Shuffle,
  Minus,
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
import type { DifficultyMode, Puzzle } from "../hooks";

// ─── Types ──────────────────────────────────────────────────────────────────

interface DiffficultyCalibratorProps {
  puzzles: Puzzle[];
  difficultyMode: DifficultyMode;
  onModeChange: (mode: DifficultyMode) => void;
  onRecalibrate: () => void;
  onReorder: (puzzleIds: string[]) => void;
  isRecalibrating?: boolean;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function getDifficultyColor(difficulty: string): string {
  switch (difficulty) {
    case "easy":
      return "bg-green-500";
    case "medium":
      return "bg-yellow-500";
    case "hard":
      return "bg-red-500";
    default:
      return "bg-gray-400";
  }
}

function getDifficultyTextColor(difficulty: string): string {
  switch (difficulty) {
    case "easy":
      return "text-green-700";
    case "medium":
      return "text-yellow-700";
    case "hard":
      return "text-red-700";
    default:
      return "text-gray-600";
  }
}

const MODE_ICONS: Record<DifficultyMode, typeof TrendingUp> = {
  progressive: TrendingUp,
  fixed: Minus,
  mixed: Shuffle,
};

const MODE_DESCRIPTIONS: Record<DifficultyMode, string> = {
  progressive:
    "Puzzles increase in difficulty: first 30% Easy, middle 40% Medium, last 30% Hard",
  fixed: "All puzzles at the same difficulty level throughout the book",
  mixed: "Random mix of difficulties throughout the book",
};

// ─── Component ──────────────────────────────────────────────────────────────

export function DifficultyCalibrator({
  puzzles,
  difficultyMode,
  onModeChange,
  onRecalibrate,
  onReorder,
  isRecalibrating,
}: DiffficultyCalibratorProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // ── Distribution stats ──────────────────────────────────────────────────
  const distribution = useMemo(() => {
    const counts = { easy: 0, medium: 0, hard: 0 };
    for (const p of puzzles) {
      const d = p.difficulty as keyof typeof counts;
      if (d in counts) counts[d]++;
    }
    const total = puzzles.length || 1;
    return {
      counts,
      percentages: {
        easy: Math.round((counts.easy / total) * 100),
        medium: Math.round((counts.medium / total) * 100),
        hard: Math.round((counts.hard / total) * 100),
      },
    };
  }, [puzzles]);

  // ── Drag reorder ────────────────────────────────────────────────────────
  const handleDragStart = useCallback((index: number) => {
    setDraggedIndex(index);
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent, targetIndex: number) => {
      e.preventDefault();
      if (draggedIndex === null || draggedIndex === targetIndex) return;
      const reordered = [...puzzles];
      const [moved] = reordered.splice(draggedIndex, 1);
      reordered.splice(targetIndex, 0, moved);
      onReorder(reordered.map((p) => p.id));
      setDraggedIndex(targetIndex);
    },
    [draggedIndex, puzzles, onReorder]
  );

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
  }, []);

  const ModeIcon = MODE_ICONS[difficultyMode];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Difficulty Calibrator</h2>
          <p className="text-sm text-muted-foreground">
            Configure difficulty distribution across your puzzle book
          </p>
        </div>
        <Button
          variant="outline"
          onClick={onRecalibrate}
          disabled={isRecalibrating || puzzles.length === 0}
        >
          {isRecalibrating ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Recalibrating...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Recalibrate
            </>
          )}
        </Button>
      </div>

      {/* ── Difficulty Mode Selector ───────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-3">
        <Label className="font-medium">Difficulty Mode</Label>
        <Select
          value={difficultyMode}
          onValueChange={(v) => onModeChange(v as DifficultyMode)}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="progressive">Progressive (Ramp)</SelectItem>
            <SelectItem value="fixed">Fixed (Uniform)</SelectItem>
            <SelectItem value="mixed">Mixed (Random)</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ModeIcon className="h-4 w-4" />
          {MODE_DESCRIPTIONS[difficultyMode]}
        </div>
      </div>

      {/* ── Distribution Visualization ─────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-4">
        <h3 className="font-medium flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Distribution
        </h3>

        {/* Stacked bar */}
        <div className="space-y-2">
          <div className="flex h-10 rounded-lg overflow-hidden">
            {distribution.percentages.easy > 0 && (
              <div
                className="bg-green-500 flex items-center justify-center text-white text-xs font-medium transition-all"
                style={{ width: `${distribution.percentages.easy}%` }}
              >
                {distribution.percentages.easy}%
              </div>
            )}
            {distribution.percentages.medium > 0 && (
              <div
                className="bg-yellow-500 flex items-center justify-center text-white text-xs font-medium transition-all"
                style={{ width: `${distribution.percentages.medium}%` }}
              >
                {distribution.percentages.medium}%
              </div>
            )}
            {distribution.percentages.hard > 0 && (
              <div
                className="bg-red-500 flex items-center justify-center text-white text-xs font-medium transition-all"
                style={{ width: `${distribution.percentages.hard}%` }}
              >
                {distribution.percentages.hard}%
              </div>
            )}
            {puzzles.length === 0 && (
              <div className="bg-gray-200 flex-1 flex items-center justify-center text-gray-500 text-xs">
                No puzzles
              </div>
            )}
          </div>

          <div className="flex gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-green-500" />
              Easy: {distribution.counts.easy}
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-yellow-500" />
              Medium: {distribution.counts.medium}
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-red-500" />
              Hard: {distribution.counts.hard}
            </div>
          </div>
        </div>

        {/* Progressive ramp visualization */}
        {difficultyMode === "progressive" && puzzles.length > 0 && (
          <div className="space-y-2 pt-2 border-t">
            <h4 className="text-sm font-medium">Progressive Ramp Target</h4>
            <div className="flex h-8 rounded-lg overflow-hidden">
              <div className="bg-green-200 border-r border-white flex items-center justify-center text-green-800 text-xs font-medium w-[30%]">
                Easy (30%)
              </div>
              <div className="bg-yellow-200 border-r border-white flex items-center justify-center text-yellow-800 text-xs font-medium w-[40%]">
                Medium (40%)
              </div>
              <div className="bg-red-200 flex items-center justify-center text-red-800 text-xs font-medium w-[30%]">
                Hard (30%)
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              First 30% of puzzles should be Easy, middle 40% Medium, last 30%
              Hard.
            </p>
          </div>
        )}
      </div>

      {/* ── Per-Puzzle Difficulty List ──────────────────────────────────── */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-muted px-4 py-2 border-b">
          <h3 className="font-medium text-sm">
            Per-Puzzle Difficulty Scores (drag to reorder)
          </h3>
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          {puzzles.length === 0 ? (
            <p className="text-sm text-muted-foreground p-4 text-center">
              No puzzles in this book yet.
            </p>
          ) : (
            <div className="divide-y">
              {puzzles.map((puzzle, index) => (
                <div
                  key={puzzle.id}
                  draggable
                  onDragStart={() => handleDragStart(index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  className={`flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50 transition-colors ${
                    draggedIndex === index ? "opacity-50" : ""
                  }`}
                >
                  <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab shrink-0" />
                  <span className="text-sm font-medium w-16">
                    #{puzzle.puzzle_number}
                  </span>
                  <span className="text-sm text-muted-foreground w-28">
                    {puzzle.puzzle_type.replace(/_/g, " ")}
                  </span>

                  {/* Score bar */}
                  <div className="flex-1 flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${getDifficultyColor(
                          puzzle.difficulty
                        )}`}
                        style={{ width: `${puzzle.difficulty_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono w-10 text-right">
                      {puzzle.difficulty_score}
                    </span>
                  </div>

                  <Badge
                    variant="outline"
                    className={`w-20 justify-center ${getDifficultyTextColor(
                      puzzle.difficulty
                    )}`}
                  >
                    {puzzle.difficulty}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
