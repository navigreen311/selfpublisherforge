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
  { value: "10x10", label: "10 x 10" },
  { value: "15x15", label: "15 x 15" },
  { value: "20x20", label: "20 x 20" },
  { value: "4x4", label: "4 x 4" },
  { value: "6x6", label: "6 x 6" },
  { value: "9x9", label: "9 x 9" },
];

// ─── Page Component ───────────────────────────────────────────────────────────

export default function PuzzleBookEditorPage() {
  const params = useParams();
  const bookId = params.id as string;

  const { data: book, isLoading: bookLoading } = usePuzzleBook(bookId);
  const { data: puzzles } = usePuzzles(bookId);
  const generatePuzzle = useGeneratePuzzle(bookId);
  const exportBook = useExport(bookId);

  // ─── State ──────────────────────────────────────────────────────────────────
  const [selectedPuzzleId, setSelectedPuzzleId] = useState<string | null>(null);
  const [showAnswerKey, setShowAnswerKey] = useState(false);
  const [showReviews, setShowReviews] = useState(false);

  // Right-panel form state
  const [editPuzzleType, setEditPuzzleType] = useState<PuzzleType>("word_search");
  const [editTheme, setEditTheme] = useState("");
  const [editGridSize, setEditGridSize] = useState("10x10");
  const [editDifficulty, setEditDifficulty] = useState("medium");
  const [editWordList, setEditWordList] = useState("");
  const [allowDiagonal, setAllowDiagonal] = useState(false);
  const [allowBackwards, setAllowBackwards] = useState(false);

  // ─── Derived ────────────────────────────────────────────────────────────────
  const puzzleList = puzzles ?? [];
  const selectedPuzzle = puzzleList.find((p) => p.id === selectedPuzzleId) ?? null;

  // ─── Handlers ───────────────────────────────────────────────────────────────
  const handleSelectPuzzle = useCallback(
    (puzzle: Puzzle) => {
      setSelectedPuzzleId(puzzle.id);
      setEditPuzzleType(puzzle.puzzle_type);
      setEditTheme(puzzle.theme ?? "");
      setEditGridSize(puzzle.grid_size ?? "10x10");
      setEditDifficulty(puzzle.difficulty);
      setEditWordList(puzzle.word_list?.join("\n") ?? "");
      setShowAnswerKey(false);
    },
    [],
  );

  const handleNewPuzzle = () => {
    setSelectedPuzzleId(null);
    setEditPuzzleType("word_search");
    setEditTheme("");
    setEditGridSize("10x10");
    setEditDifficulty("medium");
    setEditWordList("");
    setAllowDiagonal(false);
    setAllowBackwards(false);
    setShowAnswerKey(false);
  };

  const handleGenerate = () => {
    const wordListArray = editWordList
      .split("\n")
      .map((w) => w.trim())
      .filter(Boolean);

    generatePuzzle.mutate({
      puzzle_type: editPuzzleType,
      difficulty: editDifficulty,
      grid_size: editGridSize,
      theme: editTheme || undefined,
      word_list: wordListArray.length > 0 ? wordListArray : undefined,
    });
  };

  // ─── Loading state ──────────────────────────────────────────────────────────
  if (bookLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="space-y-3 text-center">
          <div className="h-8 w-48 bg-muted animate-pulse rounded mx-auto" />
          <div className="h-4 w-64 bg-muted animate-pulse rounded mx-auto" />
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-muted-foreground">Book not found.</p>
          <Button variant="outline" asChild>
            <Link href="/specialty/puzzle-books">
              <ChevronLeft className="h-4 w-4 mr-2" />
              Back to Puzzle Books
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  // ─── Reviews fullscreen view ────────────────────────────────────────────────
  if (showReviews) {
    return (
      <div className="flex h-screen flex-col">
        <div className="flex items-center gap-3 border-b px-4 py-3">
          <Button variant="ghost" size="sm" onClick={() => setShowReviews(false)}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to Editor
          </Button>
          <h2 className="text-lg font-semibold">Reviews &amp; Feedback</h2>
        </div>
        <div className="flex-1 overflow-auto p-6">
          <ReviewFeedbackPanel bookType="puzzle-books" bookId={bookId} />
        </div>
      </div>
    );
  }

  const statusLabel = book.status.replace("_", " ");
  const wordListLines = editWordList.split("\n").filter((w) => w.trim().length > 0);

  // ─── Main three-panel layout ────────────────────────────────────────────────
  return (
    <div className="flex h-screen flex-col">
      {/* ─── Top Bar ───────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/specialty/puzzle-books">
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back
            </Link>
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold">{book.title}</h1>
            <Badge className={cn("capitalize text-[10px]", STATUS_COLORS[book.status] ?? "")}>
              {statusLabel}
            </Badge>
          </div>
          <span className="text-sm text-muted-foreground">
            {book.puzzles_created}/{book.total_puzzles} puzzles
          </span>
          <span className="text-sm text-muted-foreground capitalize">
            {book.difficulty_mode}
          </span>
          <span className="text-sm text-muted-foreground capitalize">
            {book.audience.replace("_", " ")}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowReviews(true)}>
            <MessageSquareWarning className="h-4 w-4 mr-1" />
            Reviews
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportBook.mutate({ format: "pdf", include_answers: true })}
            disabled={exportBook.isPending}
          >
            <Download className="h-4 w-4 mr-1" />
            {exportBook.isPending ? "Exporting..." : "Export PDF"}
          </Button>
        </div>
      </div>

      {/* ─── Three-Panel Layout ────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── LEFT PANEL: Page Thumbnails ─────────────────────────────────── */}
        <div className="w-56 flex-shrink-0 border-r flex flex-col">
          <div className="flex items-center justify-between px-3 py-2 border-b">
            <span className="text-sm font-medium">Pages</span>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleNewPuzzle}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {puzzleList.map((puzzle) => {
              const Icon = PUZZLE_TYPE_ICONS[puzzle.puzzle_type] ?? Search;
              const isSelected = selectedPuzzleId === puzzle.id;
              return (
                <button
                  key={puzzle.id}
                  onClick={() => handleSelectPuzzle(puzzle)}
                  className={cn(
                    "w-full rounded-md border p-2 text-left transition-colors",
                    "hover:bg-accent",
                    isSelected && "ring-2 ring-primary bg-accent",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                    <span className="text-xs font-medium">#{puzzle.puzzle_number}</span>
                    <Badge
                      variant="secondary"
                      className={cn(
                        "text-[9px] capitalize ml-auto",
                        DIFFICULTY_COLORS[puzzle.difficulty] ?? "",
                      )}
                    >
                      {puzzle.difficulty}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1 mt-1">
                    <Badge
                      variant="outline"
                      className={cn("text-[9px] capitalize", STATUS_COLORS[puzzle.status] ?? "")}
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
            })}
          </div>
        </div>

        {/* ─── CENTER PANEL: Preview ───────────────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-b">
            <span className="text-sm font-medium">Preview</span>
            {selectedPuzzle && (
              <div className="flex items-center gap-2">
                <Label htmlFor="answer-key-toggle-center" className="text-xs">
                  Answer Key
                </Label>
                <Switch
                  id="answer-key-toggle-center"
                  checked={showAnswerKey}
                  onCheckedChange={setShowAnswerKey}
                />
              </div>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {selectedPuzzle ? (
              <div className="space-y-4">
                {/* Grid data / Solution data */}
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Eye className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {showAnswerKey ? "Solution Data" : "Grid Data"}
                      </span>
                    </div>
                    <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-80 whitespace-pre-wrap">
                      {JSON.stringify(
                        showAnswerKey
                          ? selectedPuzzle.solution_data ?? {}
                          : selectedPuzzle.grid_data ?? {},
                        null,
                        2,
                      )}
                    </pre>
                  </CardContent>
                </Card>

                {/* Word list badges */}
                {selectedPuzzle.word_list && selectedPuzzle.word_list.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-sm font-medium">
                      Word List ({selectedPuzzle.word_list.length})
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {selectedPuzzle.word_list.map((word) => (
                        <Badge key={word} variant="secondary" className="text-xs">
                          {word}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Clues */}
                {selectedPuzzle.clues && selectedPuzzle.clues.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-sm font-medium">
                      Clues ({selectedPuzzle.clues.length})
                    </span>
                    <div className="space-y-1">
                      {selectedPuzzle.clues.map((clue, idx) => (
                        <div key={idx} className="flex items-baseline gap-2 text-xs">
                          <span className="text-muted-foreground font-mono w-5">
                            {idx + 1}.
                          </span>
                          <span>{clue.clue}</span>
                          <span className="text-muted-foreground ml-auto font-mono">
                            ({clue.answer})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quality issues */}
                {selectedPuzzle.quality_issues &&
                  selectedPuzzle.quality_issues.length > 0 && (
                    <Card className="border-yellow-500/30">
                      <CardContent className="p-4">
                        <span className="text-sm font-medium text-yellow-600">
                          Quality Issues
                        </span>
                        <ul className="mt-2 space-y-1">
                          {selectedPuzzle.quality_issues.map((issue, idx) => (
                            <li
                              key={idx}
                              className="text-xs text-muted-foreground flex items-start gap-1.5"
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
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  Select a puzzle from the left panel or create a new one.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ─── RIGHT PANEL: Settings ───────────────────────────────────────── */}
        <div className="w-72 flex-shrink-0 border-l flex flex-col">
          <div className="px-4 py-2 border-b">
            <span className="text-sm font-medium">
              {selectedPuzzle ? "Puzzle Settings" : "New Puzzle"}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Puzzle Type */}
            <div className="space-y-1.5">
              <Label className="text-xs">Puzzle Type</Label>
              <Select
                value={editPuzzleType}
                onValueChange={(v) => setEditPuzzleType(v as PuzzleType)}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(PUZZLE_TYPE_LABELS) as PuzzleType[]).map((type) => (
                    <SelectItem key={type} value={type}>
                      {PUZZLE_TYPE_LABELS[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Theme */}
            <div className="space-y-1.5">
              <Label className="text-xs">Theme</Label>
              <Input
                className="h-8 text-xs"
                placeholder="e.g. Animals, Space..."
                value={editTheme}
                onChange={(e) => setEditTheme(e.target.value)}
              />
            </div>

            {/* Grid Size */}
            <div className="space-y-1.5">
              <Label className="text-xs">Grid Size</Label>
              <Select value={editGridSize} onValueChange={setEditGridSize}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Select size" />
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
                  <SelectValue placeholder="Select difficulty" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Separator />

            {/* Direction Options */}
            <div className="space-y-3">
              <span className="text-xs font-medium">Direction Options</span>
              <div className="flex items-center justify-between">
                <Label htmlFor="allow-diagonal" className="text-xs">
                  Allow diagonal
                </Label>
                <Switch
                  id="allow-diagonal"
                  checked={allowDiagonal}
                  onCheckedChange={setAllowDiagonal}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="allow-backwards" className="text-xs">
                  Allow backwards
                </Label>
                <Switch
                  id="allow-backwards"
                  checked={allowBackwards}
                  onCheckedChange={setAllowBackwards}
                />
              </div>
            </div>

            <Separator />

            {/* Word List */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-xs">Word List</Label>
                <span className="text-[10px] text-muted-foreground">
                  {wordListLines.length} word{wordListLines.length !== 1 ? "s" : ""}
                </span>
              </div>
              <Textarea
                className="text-xs min-h-[100px] resize-y"
                placeholder={"One word per line\napple\nbanana\ncherry"}
                value={editWordList}
                onChange={(e) => setEditWordList(e.target.value)}
              />
            </div>

            <Separator />

            {/* Show Answer Key */}
            <div className="flex items-center justify-between">
              <Label htmlFor="answer-key-right" className="text-xs">
                Show Answer Key
              </Label>
              <Switch
                id="answer-key-right"
                checked={showAnswerKey}
                onCheckedChange={setShowAnswerKey}
              />
            </div>

            <Separator />

            {/* Generate / Regenerate */}
            <Button
              className="w-full"
              size="sm"
              onClick={handleGenerate}
              disabled={generatePuzzle.isPending}
            >
              {generatePuzzle.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : selectedPuzzle ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Regenerate
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
      </div>
    </div>
  );
}
