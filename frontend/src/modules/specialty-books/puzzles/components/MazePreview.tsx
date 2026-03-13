"use client";
import React from "react";
import { cn } from "@/lib/utils";
import type { Puzzle } from "../types";
export interface MazePreviewProps { puzzle: Puzzle; showAnswer: boolean; className?: string; }
export function MazePreview({ puzzle, showAnswer, className }: MazePreviewProps) {
  const grid = puzzle.grid_data ?? []; const solution = puzzle.solution_data ?? [];
  const [rows, cols] = (puzzle.grid_size ?? "20x20").split("x").map(Number);
  const cellSize = Math.max(8, Math.min(20, 400 / Math.max(rows, cols)));
  return (<div className={cn("flex justify-center", className)}><svg width={cols * cellSize + 4} height={rows * cellSize + 4} viewBox={`0 0 ${cols * cellSize + 4} ${rows * cellSize + 4}`} className="border rounded">{grid.map((row, ri) => row.map((cell, ci) => { const isWall = cell === "#" || cell === "1"; const isStart = cell === "S"; const isEnd = cell === "E"; const isSolPath = showAnswer && solution[ri]?.[ci] === "*"; return (<rect key={`${ri}-${ci}`} x={2 + ci * cellSize} y={2 + ri * cellSize} width={cellSize} height={cellSize} fill={isWall ? "currentColor" : isStart ? "hsl(var(--primary))" : isEnd ? "hsl(142, 76%, 36%)" : isSolPath ? "hsl(var(--primary) / 0.3)" : "transparent"} fillOpacity={isWall ? 0.85 : 1} />); }))}{grid.map((row, ri) => row.map((cell, ci) => { if (cell !== "S" && cell !== "E") return null; return (<text key={`m-${ri}-${ci}`} x={2 + ci * cellSize + cellSize / 2} y={2 + ri * cellSize + cellSize / 2 + 1} textAnchor="middle" dominantBaseline="central" fontSize={cellSize * 0.7} fontWeight={700} fill="white">{cell}</text>); }))}</svg></div>);
}
