"use client";

import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import type { CompetitorAnalysisDetail } from "../types";
import { Badge } from "@/components/ui/badge";

interface CompetitorTableProps {
  analyses: CompetitorAnalysisDetail[];
  isLoading?: boolean;
  onSelectCompetitor?: (analysis: CompetitorAnalysisDetail) => void;
}

type SortField = "title" | "bsr" | "price" | "rating" | "reviews" | "weaknesses" | "score";
type SortDirection = "asc" | "desc";

export function CompetitorTable({ analyses, isLoading, onSelectCompetitor }: CompetitorTableProps) {
  const [sortField, setSortField] = useState<SortField>("bsr");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const sortedAnalyses = useMemo(() => {
    const sorted = [...analyses];
    sorted.sort((a, b) => {
      let aVal: number | string = 0;
      let bVal: number | string = 0;

      switch (sortField) {
        case "title":
          aVal = a.book?.title ?? "";
          bVal = b.book?.title ?? "";
          break;
        case "bsr":
          aVal = a.book?.bsr ?? 999999;
          bVal = b.book?.bsr ?? 999999;
          break;
        case "price":
          aVal = a.book?.price ?? 0;
          bVal = b.book?.price ?? 0;
          break;
        case "rating":
          aVal = a.book?.rating ?? 0;
          bVal = b.book?.rating ?? 0;
          break;
        case "reviews":
          aVal = a.book?.review_count ?? 0;
          bVal = b.book?.review_count ?? 0;
          break;
        case "weaknesses":
          aVal = a.weakness_count;
          bVal = b.weakness_count;
          break;
        case "score":
          aVal = a.overall_score ?? 0;
          bVal = b.overall_score ?? 0;
          break;
      }

      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sortDirection === "asc" ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });
    return sorted;
  }, [analyses, sortField, sortDirection]);

  if (isLoading) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        Loading competitor analyses...
      </div>
    );
  }

  if (!analyses.length) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        No competitor analyses yet. Start by analyzing a competitor book.
      </div>
    );
  }

  return (
    <div className="border rounded-lg bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <SortableHeader
                label="Book Title"
                field="title"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                label="BSR"
                field="bsr"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <SortableHeader
                label="Price"
                field="price"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <SortableHeader
                label="Rating"
                field="rating"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <SortableHeader
                label="Reviews"
                field="reviews"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <SortableHeader
                label="Weaknesses"
                field="weaknesses"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <SortableHeader
                label="Score"
                field="score"
                currentField={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <th className="text-left px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedAnalyses.map((analysis) => (
              <tr
                key={analysis.id}
                className="border-b last:border-b-0 hover:bg-muted/30 cursor-pointer"
                onClick={() => onSelectCompetitor?.(analysis)}
              >
                <td className="px-4 py-3">
                  <div className="font-medium max-w-xs truncate">
                    {analysis.book?.title ?? "Unknown"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {analysis.book?.author ?? ""}
                  </div>
                </td>
                <td className="px-4 py-3 text-right">
                  {analysis.book?.bsr?.toLocaleString() ?? "N/A"}
                </td>
                <td className="px-4 py-3 text-right">
                  {analysis.book?.price ? `$${analysis.book.price.toFixed(2)}` : "N/A"}
                </td>
                <td className="px-4 py-3 text-right">
                  {analysis.book?.rating ? (
                    <span className="inline-flex items-center gap-1">
                      <span>{analysis.book.rating.toFixed(1)}</span>
                      <span className="text-yellow-500">★</span>
                    </span>
                  ) : (
                    "N/A"
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {analysis.book?.review_count?.toLocaleString() ?? 0}
                </td>
                <td className="px-4 py-3 text-right">
                  <WeaknessCountBadge count={analysis.weakness_count} />
                </td>
                <td className="px-4 py-3 text-right">
                  {analysis.overall_score ? (
                    <ScoreBadge score={analysis.overall_score} />
                  ) : (
                    "N/A"
                  )}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={analysis.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

interface SortableHeaderProps {
  label: string;
  field: SortField;
  currentField: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  align?: "left" | "right";
}

function SortableHeader({
  label,
  field,
  currentField,
  direction,
  onSort,
  align = "left",
}: SortableHeaderProps) {
  const isActive = currentField === field;
  return (
    <th
      className={cn(
        "px-4 py-3 font-medium cursor-pointer select-none hover:bg-muted/70",
        align === "right" ? "text-right" : "text-left"
      )}
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {isActive && (
          <span className="text-xs">{direction === "asc" ? "↑" : "↓"}</span>
        )}
      </span>
    </th>
  );
}

function WeaknessCountBadge({ count }: { count: number }) {
  if (count === 0) return <span className="text-muted-foreground">0</span>;

  const color = count >= 10 ? "text-red-600" : count >= 5 ? "text-yellow-600" : "text-green-600";
  return <span className={cn("font-medium", color)}>{count}</span>;
}

function ScoreBadge({ score }: { score: number }) {
  const rounded = Math.round(score);
  const color =
    rounded >= 70 ? "bg-green-100 text-green-700" :
    rounded >= 40 ? "bg-yellow-100 text-yellow-700" :
    "bg-red-100 text-red-700";

  return (
    <Badge variant="outline" className={cn("font-medium", color)}>
      {rounded}
    </Badge>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: "Pending", className: "bg-gray-100 text-gray-700" },
    processing: { label: "Processing", className: "bg-blue-100 text-blue-700" },
    completed: { label: "Completed", className: "bg-green-100 text-green-700" },
    failed: { label: "Failed", className: "bg-red-100 text-red-700" },
  };

  const { label, className } = config[status] ?? config.pending;
  return <Badge variant="outline" className={className}>{label}</Badge>;
}
