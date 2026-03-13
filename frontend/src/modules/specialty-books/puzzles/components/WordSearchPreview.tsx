"use client";
import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Puzzle } from "../types";
export interface WordSearchPreviewProps { puzzle: Puzzle; showAnswer: boolean; className?: string; }
export function WordSearchPreview({ puzzle, showAnswer, className }: WordSearchPreviewProps) {
  const grid = (showAnswer ? puzzle.solution_data : puzzle.grid_data) ?? [];
  const words = puzzle.word_list ?? [];
  const [rows, cols] = (puzzle.grid_size ?? "15x15").split("x").map(Number);
  const cellSize = Math.max(20, Math.min(32, 400 / Math.max(rows, cols)));
  return (<div className={cn("flex flex-col items-center gap-4", className)}><svg width={cols * cellSize + 2} height={rows * cellSize + 2} viewBox={`0 0 ${cols * cellSize + 2} ${rows * cellSize + 2}`} className="border rounded">{Array.from({ length: rows + 1 }, (_, i) => (<line key={`h-${i}`} x1={1} y1={1 + i * cellSize} x2={1 + cols * cellSize} y2={1 + i * cellSize} stroke="currentColor" strokeOpacity={0.2} strokeWidth={0.5} />))}{Array.from({ length: cols + 1 }, (_, i) => (<line key={`v-${i}`} x1={1 + i * cellSize} y1={1} x2={1 + i * cellSize} y2={1 + rows * cellSize} stroke="currentColor" strokeOpacity={0.2} strokeWidth={0.5} />))}{grid.map((row, ri) => row.map((letter, ci) => (<text key={`${ri}-${ci}`} x={1 + ci * cellSize + cellSize / 2} y={1 + ri * cellSize + cellSize / 2 + 1} textAnchor="middle" dominantBaseline="central" fontSize={cellSize * 0.55} fontFamily="monospace" fontWeight={showAnswer ? 700 : 400} fill="currentColor" opacity={showAnswer ? 1 : 0.8}>{letter.toUpperCase()}</text>)))}</svg><div className="w-full"><h4 className="text-xs font-semibold text-muted-foreground mb-2">Words to Find ({words.length})</h4><div className="flex flex-wrap gap-1.5">{words.map((word) => (<Badge key={word} variant="outline" className="text-[10px] font-mono">{word.toUpperCase()}</Badge>))}</div></div></div>);
}
