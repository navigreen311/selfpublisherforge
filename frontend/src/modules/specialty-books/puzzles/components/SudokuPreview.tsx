"use client";
import React from "react";
import { cn } from "@/lib/utils";
import type { Puzzle } from "../types";
export interface SudokuPreviewProps { puzzle: Puzzle; showAnswer: boolean; className?: string; }
export function SudokuPreview({ puzzle, showAnswer, className }: SudokuPreviewProps) {
  const grid = (showAnswer ? puzzle.solution_data : puzzle.grid_data) ?? [];
  const size = parseInt((puzzle.grid_size ?? "9x9").split("x")[0]) || 9;
  const boxRows = size === 4 ? 2 : size === 6 ? 2 : 3; const boxCols = size === 4 ? 2 : size === 6 ? 3 : 3;
  const cellSize = Math.max(28, Math.min(44, 400 / size)); const totalSize = size * cellSize + 4;
  return (<div className={cn("flex justify-center", className)}><svg width={totalSize} height={totalSize} viewBox={`0 0 ${totalSize} ${totalSize}`} className="border rounded">{grid.map((row, ri) => row.map((cell, ci) => { const isEmpty = cell === "" || cell === "0" || cell === "."; const isGiven = !isEmpty && puzzle.grid_data?.[ri]?.[ci] !== "" && puzzle.grid_data?.[ri]?.[ci] !== "0" && puzzle.grid_data?.[ri]?.[ci] !== "."; return (<g key={`${ri}-${ci}`}><rect x={2 + ci * cellSize} y={2 + ri * cellSize} width={cellSize} height={cellSize} fill="transparent" stroke="currentColor" strokeOpacity={0.2} strokeWidth={0.5} />{!isEmpty && (<text x={2 + ci * cellSize + cellSize / 2} y={2 + ri * cellSize + cellSize / 2 + 1} textAnchor="middle" dominantBaseline="central" fontSize={cellSize * 0.5} fontFamily="monospace" fontWeight={isGiven ? 700 : 400} fill="currentColor" opacity={isGiven ? 1 : 0.6}>{cell}</text>)}</g>); }))}{Array.from({ length: Math.floor(size / boxCols) + 1 }, (_, i) => (<line key={`vb-${i}`} x1={2 + i * boxCols * cellSize} y1={2} x2={2 + i * boxCols * cellSize} y2={2 + size * cellSize} stroke="currentColor" strokeOpacity={0.7} strokeWidth={2} />))}{Array.from({ length: Math.floor(size / boxRows) + 1 }, (_, i) => (<line key={`hb-${i}`} x1={2} y1={2 + i * boxRows * cellSize} x2={2 + size * cellSize} y2={2 + i * boxRows * cellSize} stroke="currentColor" strokeOpacity={0.7} strokeWidth={2} />))}<rect x={2} y={2} width={size * cellSize} height={size * cellSize} fill="none" stroke="currentColor" strokeOpacity={0.8} strokeWidth={2.5} /></svg></div>);
}
