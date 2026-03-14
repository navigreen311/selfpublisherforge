"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  Plus,
  RefreshCw,
  Download,
  Search,
  Grid3X3,
  Route,
  Hash,
  Shuffle,
  Lock,
  Binary,
  Link2,
  Eye,
  MessageSquareWarning,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  usePuzzleBook,
  usePuzzles,
  useGeneratePuzzle,
  useExport,
  type PuzzleType,
  type Puzzle,
} from "@/modules/specialty/puzzles/hooks";
import { ReviewFeedbackPanel } from "@/modules/specialty/shared/components/ReviewFeedbackPanel";

// ─── Constants ────────────────────────────────────────────────────────────────

const PUZZLE_TYPE_ICONS: Record<PuzzleType, LucideIcon> = {
  word_search: Search,
  crossword: Grid3X3,
  maze: Route,
  sudoku: Hash,
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

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-muted text-muted-foreground",
  generating: "bg-yellow-500/10 text-yellow-600",
  generated: "bg-blue-500/10 text-blue-600",
  verified: "bg-green-500/10 text-green-600",
  failed: "bg-red-500/10 text-red-600",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "bg-green-500/10 text-green-600",
  medium: "bg-yellow-500/10 text-yellow-600",
  hard: "bg-red-500/10 text-red-600",
};

const GRID_SIZE_OPTIONS = [
  { value: "10x10", label: "10\u00d710" },
  { value: "15x15", label: "15\u00d715" },
  { value: "20x20", label: "20\u00d720" },
  { value: "4x4", label: "4\u00d74 (Sudoku)" },
  { value: "6x6", label: "6\u00d76 (Sudoku)" },
  { value: "9x9", label: "9\u00d79 (Sudoku)" },
];

// ─── Page Component ───────────────────────────────────────────────────────────

export default function PuzzleBookEditorPage() {
  const params = useParams();
  const bookId = params.id as string;

  const { data: book, isLoading: bookLoading } = usePuzzleBook(bookId);
  const { data: puzzles, isLoading: puzzlesLoading } = usePuzzles(bookId);
  const generatePuzzle = useGeneratePuzzle(bookId);
  const exportBook = useExport(bookId);

  const [selectedPuzzleId, setSelectedPuzzleId] = useState<string | null>(null);
  const [showAnswerKey, setShowAnswerKey] = useState(false);
  const [showReviews, setShowReviews] = useState(false);

  // Right panel editable state
  const [editTheme, setEditTheme] = useState("");
  const [editGridSize, setEditGridSize] = useState("15x15");
  const [editDifficulty, setEditDifficulty] = useState("medium");
  const [editPuzzleType, setEditPuzzleType] = useState<PuzzleType>("word_search");
  const [editWordList, setEditWordList] = useState("");
  const [allowDiagonal, setAllowDiagonal] = useState(true);
  const [allowBackwards, setAllowBackwards] = useState(false);

  const allPuzzles = puzzles ?? [];
  const selectedPuzzle = allPuzzles.find((p) => p.id === selectedPuzzleId) ?? null;

  const handleSelectPuzzle = useCallback((puzzle: Puzzle) => {
    setSelectedPuzzleId(puzzle.id);
    setEditTheme(puzzle.theme ?? "");
    setEditGridSize(puzzle.grid_size ?? "15x15");
    setEditDifficulty(puzzle.difficulty);
    setEditPuzzleType(puzzle.puzzle_type);
    setEditWordList(puzzle.word_list?.join("\n") ?? "");
    setShowAnswerKey(false);
  }, []);

  const handleGenerate = useCallback(() => {
    const wordList = editWordList
      .split("\n")
      .map((w) => w.trim())
      .filter(Boolean);

    generatePuzzle.mutate({
      puzzle_type: editPuzzleType,
      difficulty: editDifficulty,
      grid_size: editGridSize || undefined,
      theme: editTheme || undefined,
      word_list: wordList.length > 0 ? wordList : undefined,
    });
  }, [editPuzzleType, editDifficulty, editGridSize, editTheme, editWordList, generatePuzzle]);

  const handleRegenerate = useCallback(() => {
    if (!selectedPuzzle) return;
    const wordList = editWordList
      .split("\n")
      .map((w) => w.trim())
      .filter(Boolean);

    generatePuzzle.mutate({
      puzzle_type: editPuzzleType,
      difficulty: editDifficulty,
      grid_size: editGridSize || undefined,
      theme: editTheme || undefined,
      word_list: wordList.length > 0 ? wordList : undefined,
    });
  }, [selectedPuzzle, editPuzzleType, editDifficulty, editGridSize, editTheme, editWordList, generatePuzzle]);

  if (bookLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-6 w-96 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="container mx-auto py-6">
        <p className="text-muted-foreground">Book not found.</p>
        <Button variant="outline" asChild className="mt-4">
          <Link href="/specialty/puzzle-books">
            <ChevronLeft className="h-4 w-4 mr-2" />
            Back to Puzzle Books
          </Link>
        </Button>
      </div>
    );
  }

  if (showReviews) {
    return (
      <div className="container mx-auto py-6 space-y-4">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => setShowReviews(false)}
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Editor
        </Button>
        <ReviewFeedbackPanel bookType="puzzle-books" bookId={bookId} />
      </div>
    );
  }

  const statusLabel = book.status.replace("_", " ");

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* ─── Top Bar ──────────────────────────────────────────────────────── */}
      <div className="border-b px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" asChild className="gap-1.5">
            <Link href="/specialty/puzzle-books">
              <ChevronLeft className="h-4 w-4" />
              Back
            </Link>
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold">{book.title}</h1>
              <Badge className={cn("capitalize text-[10px]", STATUS_COLORS[book.status] ?? "")}>
                {statusLabel}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              {book.puzzles_created}/{book.total_puzzles} puzzles
              {" \u00b7 "}
              <span className="capitalize">{book.difficulty_mode}</span>
              {" \u00b7 "}
              <span className="capitalize">{book.audience.replace("_", " ")}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowReviews(true)}
            className="gap-1.5"
          >
            <MessageSquareWarning className="h-4 w-4" />
            Reviews
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportBook.mutate({ format: "pdf", include_answers: true })}
            disabled={exportBook.isPending}
          >
            <Download className="h-4 w-4 mr-2" />
            {exportBook.isPending ? "Exporting..." : "Export PDF"}
          </Button>
        </div>
      </div>

      {/* ─── Three-Panel Layout ──────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── LEFT PANEL: Page Thumbnails ─────────────────────────────── */}
        <div className="w-56 border-r flex flex-col shrink-0">
          <div className="p-3 border-b flex items-center justify-between">
            <span className="text-sm font-medium">Pages</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => {
                setSelectedPuzzleId(null);
                setEditTheme("");
                setEditGridSize("15x15");
                setEditDifficulty("medium");
                setEditPuzzleType(
                  (book.puzzle_config[0]?.type as PuzzleType) ?? "word_search"
                );
                setEditWordList("");
              }}
              title="New puzzle"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {puzzlesLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-16 bg-muted animate-pulse rounded-md"
                />
              ))
            ) : allPuzzles.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-6 px-2">
                No puzzles yet. Click + to generate one.
              </p>
            ) : (
              allPuzzles.map((puzzle) => {
                const Icon = PUZZLE_TYPE_ICONS[puzzle.puzzle_type] ?? Search;
                const isSelected = puzzle.id === selectedPuzzleId;
                return (
                  <button
                    key={puzzle.id}
                    onClick={() => handleSelectPuzzle(puzzle)}
                    className={cn(
                      "w-full text-left rounded-md border p-2 transition-colors",
                      isSelected
                        ? "border-primary bg-primary/5 ring-1 ring-primary"
                        : "hover:bg-muted/50"
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="h-3.5 w-3.5 text-primary shrink-0" />
                      <span className="text-xs font-medium truncate">
                        #{puzzle.puzzle_number}{" "}
                        {PUZZLE_TYPE_LABELS[puzzle.puzzle_type] ?? puzzle.puzzle_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[9px] capitalize px-1 py-0",
                          DIFFICULTY_COLORS[puzzle.difficulty] ?? ""
                        )}
                      >
                        {puzzle.difficulty}
                      </Badge>
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-[9px] capitalize px-1 py-0",
                          STATUS_COLORS[puzzle.status] ?? ""
                        )}
                      >
                        {puzzle.status}
                      </Badge>
                    </div>
                    {puzzle.theme && (
                      <p className="text-[10px] text-muted-foreground mt-1 truncate">
                        {puzzle.theme}
                      </p>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ─── CENTER PANEL: Puzzle Preview ─────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-3 border-b flex items-center justify-between">
            <span className="text-sm font-medium">
              {selectedPuzzle
                ? `Preview \u2014 #${selectedPuzzle.puzzle_number} ${
                    PUZZLE_TYPE_LABELS[selectedPuzzle.puzzle_type]
                  }`
                : "Puzzle Preview"}
            </span>
            {selectedPuzzle && (
              <div className="flex items-center gap-1.5">
                <Label htmlFor="answer-key-center" className="text-xs">
                  Answer Key
                </Label>
                <Switch
                  id="answer-key-center"
                  checked={showAnswerKey}
                  onCheckedChange={setShowAnswerKey}
                />
              </div>
            )}
          </div>
          <div className="flex-1 overflow-auto p-6">
            {selectedPuzzle ? (
              <div className="max-w-2xl mx-auto space-y-4">
                <Card>
                  <CardContent className="p-6">
                    {showAnswerKey && selectedPuzzle.solution_data ? (
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <Eye className="h-4 w-4 text-green-600" />
                          <span className="text-sm font-medium text-green-600">
                            Answer Key
                          </span>
                        </div>
                        <pre className="text-xs font-mono whitespace-pre overflow-x-auto bg-green-50 rounded-md p-4">
                          {JSON.stringify(selectedPuzzle.solution_data, null, 2)}
                        </pre>
                      </div>
                    ) : selectedPuzzle.grid_data ? (
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <Grid3X3 className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">Puzzle Grid</span>
                          {selectedPuzzle.grid_size && (
                            <Badge variant="outline" className="text-[10px]">
                              {selectedPuzzle.grid_size}
                            </Badge>
                          )}
                        </div>
                        <pre className="text-xs font-mono whitespace-pre overflow-x-auto bg-muted/30 rounded-md p-4">
                          {JSON.stringify(selectedPuzzle.grid_data, null, 2)}
                        </pre>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <Grid3X3 className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                        <p className="text-sm text-muted-foreground">
                          {selectedPuzzle.status === "generating"
                            ? "Generating puzzle..."
                            : selectedPuzzle.status === "failed"
                              ? "Puzzle generation failed. Try regenerating."
                              : "Preview not available yet."}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {selectedPuzzle.word_list && selectedPuzzle.word_list.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <span className="text-sm font-medium mb-2 block">
                        Word List ({selectedPuzzle.word_list.length} words)
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedPuzzle.word_list.map((word, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {word}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {selectedPuzzle.clues && selectedPuzzle.clues.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <span className="text-sm font-medium mb-2 block">
                        Clues ({selectedPuzzle.clues.length})
                      </span>
                      <div className="space-y-1">
                        {selectedPuzzle.clues.map((clue, idx) => (
                          <div key={idx} className="flex items-baseline gap-2 text-xs">
                            <span className="text-muted-foreground font-mono w-5">
                              {idx + 1}.
                            </span>
                            <span>{clue.clue}</span>
                            {showAnswerKey && (
                              <span className="text-muted-foreground ml-auto font-mono">
                                ({clue.answer})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {selectedPuzzle.quality_issues &&
                  selectedPuzzle.quality_issues.length > 0 && (
                    <Card className="border-yellow-200">
                      <CardContent className="p-4">
                        <span className="text-sm font-medium text-yellow-700 mb-2 block">
                          Quality Issues ({selectedPuzzle.quality_issues.length})
                        </span>
                        <ul className="space-y-1">
                          {selectedPuzzle.quality_issues.map((issue, idx) => (
                            <li
                              key={idx}
                              className="text-xs text-yellow-700 flex items-start gap-1.5"
                            >
                              <span className="text-yellow-500 mt-0.5">&bull;</span>
                              {issue}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Grid3X3 className="h-12 w-12 text-muted-foreground mb-3" />
                <p className="text-muted-foreground text-sm mb-1">
                  {allPuzzles.length === 0
                    ? "No puzzles generated yet"
                    : "Select a puzzle from the left panel"}
                </p>
                <p className="text-muted-foreground text-xs">
                  Use the right panel to configure and generate new puzzles.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ─── RIGHT PANEL: Settings & Controls ────────────────────────── */}
        <div className="w-72 border-l flex flex-col shrink-0 overflow-y-auto">
          <div className="p-3 border-b">
            <span className="text-sm font-medium">
              {selectedPuzzle ? "Puzzle Settings" : "New Puzzle"}
            </span>
          </div>
          <div className="p-3 space-y-4">
            {/* Puzzle Type */}
            <div className="space-y-1.5">
              <Label className="text-xs">Puzzle Type</Label>
              <Select
                value={editPuzzleType}
                onValueChange={(v) => setEditPuzzleType(v as PuzzleType)}
              >
                <SelectTrigger className="h-8 text-xs">
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

            {/* Theme */}
            <div className="space-y-1.5">
              <Label className="text-xs">Theme</Label>
              <Input
                value={editTheme}
                onChange={(e) => setEditTheme(e.target.value)}
                placeholder="e.g., Animals, Space..."
                className="h-8 text-xs"
              />
            </div>

            {/* Grid Size */}
            <div className="space-y-1.5">
              <Label className="text-xs">Grid Size</Label>
              <Select value={editGridSize} onValueChange={setEditGridSize}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GRID_SIZE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Difficulty */}
            <div className="space-y-1.5">
              <Label className="text-xs">Difficulty</Label>
              <Select value={editDifficulty} onValueChange={setEditDifficulty}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Separator />

            {/* Direction Toggles */}
            <div className="space-y-3">
              <Label className="text-xs font-medium">Direction Options</Label>
              <div className="flex items-center justify-between">
                <Label htmlFor="diagonal-toggle" className="text-xs text-muted-foreground">
                  Allow diagonal
                </Label>
                <Switch
                  id="diagonal-toggle"
                  checked={allowDiagonal}
                  onCheckedChange={setAllowDiagonal}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="backwards-toggle" className="text-xs text-muted-foreground">
                  Allow backwards
                </Label>
                <Switch
                  id="backwards-toggle"
                  checked={allowBackwards}
                  onCheckedChange={setAllowBackwards}
                />
              </div>
            </div>

            <Separator />

            {/* Word List Editor */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Word List</Label>
              <Textarea
                value={editWordList}
                onChange={(e) => setEditWordList(e.target.value)}
                rows={6}
                placeholder={"One word per line\ne.g.:\nDOLPHIN\nWHALE\nOCTOPUS"}
                className="text-xs font-mono resize-none"
              />
              <p className="text-[10px] text-muted-foreground">
                {editWordList.split("\n").filter((w) => w.trim()).length} words
              </p>
            </div>

            <Separator />

            {/* Answer Key Toggle */}
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium">Show Answer Key</Label>
              <Switch
                checked={showAnswerKey}
                onCheckedChange={setShowAnswerKey}
                disabled={!selectedPuzzle}
              />
            </div>

            <Separator />

            {/* Action Buttons */}
            <div className="space-y-2">
              {selectedPuzzle ? (
                <Button
                  size="sm"
                  className="w-full"
                  onClick={handleRegenerate}
                  disabled={generatePuzzle.isPending}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      generatePuzzle.isPending && "animate-spin"
                    )}
                  />
                  {generatePuzzle.isPending ? "Regenerating..." : "Regenerate"}
                </Button>
              ) : (
                <Button
                  size="sm"
                  className="w-full"
                  onClick={handleGenerate}
                  disabled={generatePuzzle.isPending}
                >
                  <Plus
                    className={cn(
                      "h-4 w-4 mr-2",
                      generatePuzzle.isPending && "animate-spin"
                    )}
                  />
                  {generatePuzzle.isPending ? "Generating..." : "Generate Puzzle"}
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
