"use client";

import { useState, useCallback } from "react";
import {
  Grid3X3,
  Hash,
  Navigation,
  Binary,
  Shuffle,
  Lock,
  Search,
  Link2,
  Plus,
  RefreshCw,
  CheckCircle,
  Trash2,
  GripVertical,
  Eye,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Puzzle, PuzzleType } from "../hooks";

// ─── Constants ──────────────────────────────────────────────────────────────

const PUZZLE_TYPE_ICONS: Record<PuzzleType, typeof Grid3X3> = {
  word_search: Search,
  crossword: Hash,
  maze: Navigation,
  sudoku: Grid3X3,
  word_scramble: Shuffle,
  cryptogram: Lock,
  number_search: Binary,
  word_connect: Link2,
};

const PUZZLE_TYPE_LABELS: Record<PuzzleType, string> = {
  word_search: "Word Search",
  crossword: "Crossword",
  maze: "Maze",
  sudoku: "Sudoku",
  word_scramble: "Word Scramble",
  cryptogram: "Cryptogram",
  number_search: "Number Search",
  word_connect: "Word Connect",
};

const DIFFICULTY_STYLES: Record<string, string> = {
  easy: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  hard: "bg-red-100 text-red-800",
};

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  generating: "bg-blue-100 text-blue-700",
  generated: "bg-indigo-100 text-indigo-700",
  verified: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

// ─── Props ──────────────────────────────────────────────────────────────────

interface PuzzleEditorProps {
  bookId: string;
  puzzles: Puzzle[];
  onGenerate: (input: {
    puzzle_type: PuzzleType;
    difficulty: string;
    theme?: string;
    grid_size?: string;
  }) => void;
  onRegenerate: (puzzleId: string) => void;
  onVerify: (puzzleId: string) => void;
  onDelete: (puzzleId: string) => void;
  onReorder: (puzzleIds: string[]) => void;
  isGenerating?: boolean;
}

// ─── Component ──────────────────────────────────────────────────────────────

export function PuzzleEditor({
  bookId,
  puzzles,
  onGenerate,
  onRegenerate,
  onVerify,
  onDelete,
  onReorder,
  isGenerating,
}: PuzzleEditorProps) {
  const [selectedPuzzle, setSelectedPuzzle] = useState<Puzzle | null>(null);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // ── Generate form state ─────────────────────────────────────────────────
  const [genType, setGenType] = useState<PuzzleType>("word_search");
  const [genDifficulty, setGenDifficulty] = useState("easy");
  const [genTheme, setGenTheme] = useState("");
  const [genGridSize, setGenGridSize] = useState("15x15");

  const handleGenerate = useCallback(() => {
    onGenerate({
      puzzle_type: genType,
      difficulty: genDifficulty,
      theme: genTheme || undefined,
      grid_size: genGridSize || undefined,
    });
    setShowGenerateDialog(false);
    setGenTheme("");
  }, [genType, genDifficulty, genTheme, genGridSize, onGenerate]);

  // ── Drag and drop ───────────────────────────────────────────────────────
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Puzzle Editor</h2>
          <p className="text-sm text-muted-foreground">
            {puzzles.length} puzzle{puzzles.length !== 1 ? "s" : ""} in this
            book
          </p>
        </div>
        <Button onClick={() => setShowGenerateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Generate New Puzzle
        </Button>
      </div>

      {/* Puzzle Grid */}
      {puzzles.length === 0 ? (
        <div className="border-2 border-dashed rounded-lg p-12 text-center">
          <Grid3X3 className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
          <h3 className="font-medium text-lg mb-1">No puzzles yet</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Generate your first puzzle to get started.
          </p>
          <Button onClick={() => setShowGenerateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Generate New Puzzle
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {puzzles.map((puzzle, index) => {
            const Icon = PUZZLE_TYPE_ICONS[puzzle.puzzle_type] || Grid3X3;
            return (
              <div
                key={puzzle.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                className={`border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer group ${
                  draggedIndex === index ? "opacity-50" : ""
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <GripVertical className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 cursor-grab" />
                    <div className="p-2 rounded-md bg-muted">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">
                        #{puzzle.puzzle_number}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {PUZZLE_TYPE_LABELS[puzzle.puzzle_type]}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="secondary"
                    className={STATUS_STYLES[puzzle.status] || ""}
                  >
                    {puzzle.status}
                  </Badge>
                </div>

                {puzzle.theme && (
                  <p className="text-xs text-muted-foreground mb-2">
                    Theme: {puzzle.theme}
                  </p>
                )}

                <div className="flex items-center gap-2 mb-3">
                  <Badge
                    variant="outline"
                    className={DIFFICULTY_STYLES[puzzle.difficulty] || ""}
                  >
                    {puzzle.difficulty}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Score: {puzzle.difficulty_score}/100
                  </span>
                </div>

                {puzzle.quality_issues && puzzle.quality_issues.length > 0 && (
                  <div className="flex items-center gap-1 text-xs text-amber-600 mb-2">
                    <AlertTriangle className="h-3 w-3" />
                    {puzzle.quality_issues.length} issue
                    {puzzle.quality_issues.length !== 1 ? "s" : ""}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-1 pt-2 border-t">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedPuzzle(puzzle);
                    }}
                  >
                    <Eye className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRegenerate(puzzle.id);
                    }}
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onVerify(puzzle.id);
                    }}
                  >
                    <CheckCircle className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(puzzle.id);
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Puzzle Detail Dialog ───────────────────────────────────────────── */}
      <Dialog
        open={!!selectedPuzzle}
        onOpenChange={() => setSelectedPuzzle(null)}
      >
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          {selectedPuzzle && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {(() => {
                    const Icon =
                      PUZZLE_TYPE_ICONS[selectedPuzzle.puzzle_type] || Grid3X3;
                    return <Icon className="h-5 w-5" />;
                  })()}
                  Puzzle #{selectedPuzzle.puzzle_number} -{" "}
                  {PUZZLE_TYPE_LABELS[selectedPuzzle.puzzle_type]}
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 mt-4">
                {/* Metadata */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Difficulty
                    </Label>
                    <Badge
                      className={
                        DIFFICULTY_STYLES[selectedPuzzle.difficulty] || ""
                      }
                    >
                      {selectedPuzzle.difficulty}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Score
                    </Label>
                    <p className="font-medium">
                      {selectedPuzzle.difficulty_score}/100
                    </p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Grid Size
                    </Label>
                    <p className="font-medium">
                      {selectedPuzzle.grid_size || "N/A"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Status
                    </Label>
                    <Badge
                      className={
                        STATUS_STYLES[selectedPuzzle.status] || ""
                      }
                    >
                      {selectedPuzzle.status}
                    </Badge>
                  </div>
                </div>

                {selectedPuzzle.theme && (
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Theme
                    </Label>
                    <p className="font-medium">{selectedPuzzle.theme}</p>
                  </div>
                )}

                {/* Puzzle Preview */}
                <div className="border rounded-lg p-6 bg-muted/30">
                  <h4 className="text-sm font-medium mb-3">Puzzle Preview</h4>
                  {selectedPuzzle.grid_data ? (
                    <pre className="text-xs font-mono whitespace-pre overflow-x-auto">
                      {JSON.stringify(selectedPuzzle.grid_data, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-sm text-muted-foreground italic">
                      Preview not available - puzzle may not be generated yet.
                    </p>
                  )}
                </div>

                {/* Word List */}
                {selectedPuzzle.word_list &&
                  selectedPuzzle.word_list.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Word List</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedPuzzle.word_list.map((word, i) => (
                          <Badge key={i} variant="outline">
                            {word}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Clues */}
                {selectedPuzzle.clues && selectedPuzzle.clues.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Clues</h4>
                    <div className="space-y-1">
                      {selectedPuzzle.clues.map((clue, i) => (
                        <div key={i} className="flex gap-2 text-sm">
                          <span className="font-medium text-muted-foreground w-6">
                            {i + 1}.
                          </span>
                          <span>{clue.clue}</span>
                          <span className="text-muted-foreground ml-auto">
                            ({clue.answer})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quality Issues */}
                {selectedPuzzle.quality_issues &&
                  selectedPuzzle.quality_issues.length > 0 && (
                    <div className="border border-amber-200 rounded-lg p-3 bg-amber-50">
                      <h4 className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4" />
                        Quality Issues
                      </h4>
                      <ul className="space-y-1">
                        {selectedPuzzle.quality_issues.map((issue, i) => (
                          <li
                            key={i}
                            className="text-sm text-amber-700 flex items-start gap-2"
                          >
                            <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                            {issue}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t">
                  <Button
                    variant="outline"
                    onClick={() => {
                      onRegenerate(selectedPuzzle.id);
                      setSelectedPuzzle(null);
                    }}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Regenerate
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      onVerify(selectedPuzzle.id);
                      setSelectedPuzzle(null);
                    }}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Verify
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => {
                      onDelete(selectedPuzzle.id);
                      setSelectedPuzzle(null);
                    }}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Generate New Puzzle Dialog ─────────────────────────────────────── */}
      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate New Puzzle</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div>
              <Label>Puzzle Type</Label>
              <Select
                value={genType}
                onValueChange={(v) => setGenType(v as PuzzleType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PUZZLE_TYPE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Difficulty</Label>
              <Select value={genDifficulty} onValueChange={setGenDifficulty}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Theme (optional)</Label>
              <Input
                value={genTheme}
                onChange={(e) => setGenTheme(e.target.value)}
                placeholder="e.g., Animals, Space, Food..."
              />
            </div>

            <div>
              <Label>Grid Size</Label>
              <Select value={genGridSize} onValueChange={setGenGridSize}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10x10">10x10</SelectItem>
                  <SelectItem value="15x15">15x15</SelectItem>
                  <SelectItem value="20x20">20x20</SelectItem>
                  <SelectItem value="4x4">4x4 (Sudoku)</SelectItem>
                  <SelectItem value="6x6">6x6 (Sudoku)</SelectItem>
                  <SelectItem value="9x9">9x9 (Sudoku)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                onClick={() => setShowGenerateDialog(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleGenerate} disabled={isGenerating}>
                {isGenerating ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Generate
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
