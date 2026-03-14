"use client";

import Link from "next/link";
import {
  Search,
  Grid3X3,
  Route,
  Hash,
  Shuffle,
  Lock,
  Binary,
  Link2,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { PuzzleBook, PuzzleType } from "../hooks";

// ─── Puzzle type icon map ─────────────────────────────────────────────────────

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
  draft: "bg-muted text-muted-foreground",
  in_progress: "bg-yellow-500/10 text-yellow-600",
  published: "bg-green-500/10 text-green-600",
};

// ─── Component ────────────────────────────────────────────────────────────────

export interface PuzzleCardProps {
  book: PuzzleBook;
}

export function PuzzleCard({ book }: PuzzleCardProps) {
  const primaryType = book.puzzle_config[0]?.type ?? "word_search";
  const Icon = PUZZLE_TYPE_ICONS[primaryType] ?? Search;

  const puzzleTypeLabels = book.puzzle_config
    .map((c) => PUZZLE_TYPE_LABELS[c.type])
    .filter(Boolean);

  const statusLabel = book.status.replace("_", " ");

  return (
    <Link href={`/specialty/puzzle-books/${book.id}`}>
      <Card className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer group">
        {/* Icon header */}
        <div className="aspect-[4/3] bg-muted/50 flex items-center justify-center relative">
          <Icon className="h-12 w-12 text-muted-foreground/40 group-hover:text-primary/60 transition-colors" />
          <Badge
            className={cn(
              "absolute top-2 right-2 text-[10px] capitalize",
              STATUS_COLORS[book.status]
            )}
            variant="secondary"
          >
            {statusLabel}
          </Badge>
        </div>

        <CardContent className="p-3 space-y-1.5">
          <p className="font-medium text-sm truncate">{book.title}</p>

          {/* Puzzle types */}
          <div className="flex flex-wrap gap-1">
            {puzzleTypeLabels.slice(0, 3).map((label) => (
              <span
                key={label}
                className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full"
              >
                {label}
              </span>
            ))}
            {puzzleTypeLabels.length > 3 && (
              <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded-full text-muted-foreground">
                +{puzzleTypeLabels.length - 3}
              </span>
            )}
          </div>

          {/* Puzzle count & difficulty */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {book.puzzles_created}/{book.total_puzzles} puzzles
            </span>
            <Badge variant="outline" className="text-[10px] capitalize">
              {book.difficulty_mode}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
