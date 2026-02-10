"use client";

import { cn } from "@/lib/utils";
import type { KeywordData } from "../hooks";

interface KeywordTableProps {
  keywords: KeywordData[];
  isLoading?: boolean;
}

function TrendBadge({ trend }: { trend: "up" | "down" | "stable" }) {
  const config = {
    up: { label: "Rising", className: "bg-green-100 text-green-700" },
    down: { label: "Declining", className: "bg-red-100 text-red-700" },
    stable: { label: "Stable", className: "bg-gray-100 text-gray-700" },
  };
  const { label, className } = config[trend];
  return (
    <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", className)}>
      {label}
    </span>
  );
}

function CompetitionBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "bg-red-500" : pct >= 40 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 rounded-full bg-muted overflow-hidden">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

export function KeywordTable({ keywords, isLoading }: KeywordTableProps) {
  if (isLoading) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        Analyzing keywords...
      </div>
    );
  }

  if (!keywords.length) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
        No keyword data yet. Enter keywords to research above.
      </div>
    );
  }

  return (
    <div className="border rounded-lg bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="text-left px-4 py-3 font-medium">Keyword</th>
              <th className="text-right px-4 py-3 font-medium">Search Vol</th>
              <th className="text-left px-4 py-3 font-medium">Competition</th>
              <th className="text-right px-4 py-3 font-medium">CPC</th>
              <th className="text-left px-4 py-3 font-medium">Trend</th>
              <th className="text-right px-4 py-3 font-medium">Relevance</th>
            </tr>
          </thead>
          <tbody>
            {keywords.map((kw) => (
              <tr key={kw.keyword} className="border-b last:border-b-0 hover:bg-muted/30">
                <td className="px-4 py-3 font-medium">{kw.keyword}</td>
                <td className="px-4 py-3 text-right">
                  {kw.search_volume.toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <CompetitionBar value={kw.competition} />
                </td>
                <td className="px-4 py-3 text-right">${kw.cpc.toFixed(2)}</td>
                <td className="px-4 py-3">
                  <TrendBadge trend={kw.trend} />
                </td>
                <td className="px-4 py-3 text-right">{kw.relevance_score.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
