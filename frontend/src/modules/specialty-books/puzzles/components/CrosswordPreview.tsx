"use client";
import React from "react";
import { cn } from "@/lib/utils";
import type { Puzzle, PuzzleClue } from "../types";
export interface CrosswordPreviewProps { puzzle: Puzzle; showAnswer: boolean; className?: string; }
export function CrosswordPreview({ puzzle, showAnswer, className }: CrosswordPreviewProps) {
  const grid = (showAnswer ? puzzle.solution_data : puzzle.grid_data) ?? [];
  const clues = puzzle.clues ?? [];
  const [rows, cols] = (puzzle.grid_size ?? "15x15").split("x").map(Number);
  const cellSize = Math.max(22, Math.min(32, 420 / Math.max(rows, cols)));
  const acrossClues = clues.filter((c) => c.direction === "across");
  const downClues = clues.filter((c) => c.direction === "down");
  return (<div className={cn("flex flex-col gap-4", className)}><div className="flex justify-center"><svg width={cols * cellSize + 2} height={rows * cellSize + 2} viewBox={`0 0 ${cols * cellSize + 2} ${rows * cellSize + 2}`} className="border rounded">{grid.map((row, ri) => row.map((cell, ci) => { const isBlack = cell === "#" || cell === "."; return (<g key={`${ri}-${ci}`}><rect x={1 + ci * cellSize} y={1 + ri * cellSize} width={cellSize} height={cellSize} fill={isBlack ? "currentColor" : "transparent"} fillOpacity={isBlack ? 0.85 : 0} stroke="currentColor" strokeOpacity={0.3} strokeWidth={0.5} />{!isBlack && showAnswer && (<text x={1 + ci * cellSize + cellSize / 2} y={1 + ri * cellSize + cellSize / 2 + 1} textAnchor="middle" dominantBaseline="central" fontSize={cellSize * 0.5} fontFamily="monospace" fontWeight={600} fill="currentColor">{cell.toUpperCase()}</text>)}</g>); }))}</svg></div><div className="grid grid-cols-2 gap-4 text-xs"><div><h4 className="font-semibold text-muted-foreground mb-2">Across</h4><div className="space-y-1 max-h-48 overflow-y-auto pr-1">{acrossClues.length === 0 ? <p className="text-muted-foreground/60 italic">No clues</p> : acrossClues.map((clue) => (<div key={clue.id} className={cn("flex gap-2", clue.flagged && "text-destructive")}><span className="font-mono font-semibold shrink-0 w-6 text-right">{clue.number}.</span><span className="text-muted-foreground">{clue.clue_text}</span></div>))}</div></div><div><h4 className="font-semibold text-muted-foreground mb-2">Down</h4><div className="space-y-1 max-h-48 overflow-y-auto pr-1">{downClues.length === 0 ? <p className="text-muted-foreground/60 italic">No clues</p> : downClues.map((clue) => (<div key={clue.id} className={cn("flex gap-2", clue.flagged && "text-destructive")}><span className="font-mono font-semibold shrink-0 w-6 text-right">{clue.number}.</span><span className="text-muted-foreground">{clue.clue_text}</span></div>))}</div></div></div></div>);
}
