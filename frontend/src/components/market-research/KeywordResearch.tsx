"use client";

import * as React from "react";
import { Search, ChevronLeft, ChevronRight, ArrowUpDown, Copy, Check, Download, FolderPlus, Sparkles } from "lucide-react";
import { useKeywordResearch } from "@/modules/market/hooks";
import type { KeywordData } from "@/modules/market/hooks";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

type SortField = "keyword" | "search_volume" | "competition" | "opportunity_score" | "cpc";
type SortDirection = "asc" | "desc";

interface KeywordResearchProps {
  onAnalyzeNiche?: (keyword: string) => void;
}

function CompetitionBadge({
  level,
  t,
}: {
  level: "low" | "medium" | "high" | undefined;
  t: (key: string) => string;
}) {
  const config = {
    high: { label: t("keywords.competitionHigh"), className: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
    medium: { label: t("keywords.competitionMedium"), className: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" },
    low: { label: t("keywords.competitionLow"), className: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
  };
  const resolved = level ?? "medium";
  const { label, className } = config[resolved];
  return (
    <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap", className)}>
      {label}
    </span>
  );
}

function OpportunityScore({ score }: { score: number | undefined }) {
  const value = score ?? 0;
  const color =
    value >= 70 ? "text-green-600 dark:text-green-400" :
    value >= 40 ? "text-yellow-600 dark:text-yellow-400" :
    "text-red-600 dark:text-red-400";
  return <span className={cn("font-semibold tabular-nums", color)}>{value}</span>;
}

export function KeywordResearch({ onAnalyzeNiche }: KeywordResearchProps) {
  const t = useTranslations("market");
  const mutation = useKeywordResearch();

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const [seedInput, setSeedInput] = React.useState("");
  const [sortField, setSortField] = React.useState<SortField>("search_volume");
  const [sortDirection, setSortDirection] = React.useState<SortDirection>("desc");
  const [selectedKeywords, setSelectedKeywords] = React.useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = React.useState(0);
  const [copied, setCopied] = React.useState(false);

  // ---------------------------------------------------------------------------
  // Derived data
  // ---------------------------------------------------------------------------
  const keywords: KeywordData[] = mutation.data?.keywords ?? [];
  const suggestedKdpKeywords: string[] = mutation.data?.suggested_kdp_keywords ?? [];
  const totalResults: number = mutation.data?.total_results ?? keywords.length;

  const sortedKeywords = React.useMemo(() => {
    const sorted = [...keywords].sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;

      switch (sortField) {
        case "keyword":
          aVal = a.keyword.toLowerCase();
          bVal = b.keyword.toLowerCase();
          break;
        case "search_volume":
          aVal = a.search_volume;
          bVal = b.search_volume;
          break;
        case "competition":
          aVal = a.competition;
          bVal = b.competition;
          break;
        case "opportunity_score":
          aVal = a.opportunity_score ?? 0;
          bVal = b.opportunity_score ?? 0;
          break;
        case "cpc":
          aVal = a.cpc;
          bVal = b.cpc;
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [keywords, sortField, sortDirection]);

  const totalPages = Math.ceil(sortedKeywords.length / PAGE_SIZE);
  const paginatedKeywords = sortedKeywords.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  );
  const rangeStart = sortedKeywords.length > 0 ? currentPage * PAGE_SIZE + 1 : 0;
  const rangeEnd = Math.min((currentPage + 1) * PAGE_SIZE, sortedKeywords.length);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  function handleResearch() {
    const trimmed = seedInput.trim();
    if (!trimmed) return;
    const keywordsList = trimmed.split(",").map((k) => k.trim()).filter(Boolean);
    setCurrentPage(0);
    setSelectedKeywords(new Set());
    mutation.mutate({ keywords: keywordsList });
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      handleResearch();
    }
  }

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  }

  function toggleKeyword(keyword: string) {
    setSelectedKeywords((prev) => {
      const next = new Set(prev);
      if (next.has(keyword)) {
        next.delete(keyword);
      } else {
        next.add(keyword);
      }
      return next;
    });
  }

  function toggleAll() {
    if (selectedKeywords.size === paginatedKeywords.length) {
      setSelectedKeywords(new Set());
    } else {
      setSelectedKeywords(new Set(paginatedKeywords.map((kw) => kw.keyword)));
    }
  }

  function handleExportCsv() {
    const selected = keywords.filter((kw) => selectedKeywords.has(kw.keyword));
    const header = "Keyword,Search Volume,Competition,Opportunity Score,CPC";
    const rows = selected.map(
      (kw) =>
        `"${kw.keyword}",${kw.search_volume},${kw.competition_level ?? ""},${kw.opportunity_score ?? ""},${kw.cpc.toFixed(2)}`,
    );
    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "keyword-research.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleCopyKdpKeywords() {
    const text = suggestedKdpKeywords.join(", ");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  // ---------------------------------------------------------------------------
  // Sort header helper
  // ---------------------------------------------------------------------------
  function SortHeader({ field, children, className }: { field: SortField; children: React.ReactNode; className?: string }) {
    return (
      <button
        type="button"
        className={cn("flex items-center gap-1 hover:text-foreground", className)}
        onClick={() => handleSort(field)}
      >
        {children}
        <ArrowUpDown
          className={cn(
            "h-3.5 w-3.5",
            sortField === field ? "text-foreground" : "text-muted-foreground/50",
          )}
        />
      </button>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="space-y-6">
      {/* Title */}
      <h2 className="text-xl font-semibold">{t("keywords.title")}</h2>

      {/* Search bar */}
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Input
            placeholder={t("keywords.seedPlaceholder")}
            value={seedInput}
            onChange={(e) => setSeedInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
        <Button
          onClick={handleResearch}
          disabled={!seedInput.trim() || mutation.isPending}
        >
          <Search className="h-4 w-4 mr-2" aria-hidden="true" />
          {mutation.isPending ? t("keywords.researching") : t("keywords.research")}
        </Button>
      </div>

      {/* Bulk actions */}
      {selectedKeywords.size > 0 && (
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {selectedKeywords.size} selected
          </span>
          <Button variant="outline" size="sm" onClick={handleExportCsv}>
            <Download className="h-4 w-4 mr-2" aria-hidden="true" />
            {t("keywords.exportCsv")}
          </Button>
          <Button variant="outline" size="sm">
            <FolderPlus className="h-4 w-4 mr-2" aria-hidden="true" />
            {t("keywords.addToProject")}
          </Button>
        </div>
      )}

      {/* Results table */}
      {mutation.isPending && (
        <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
          {t("keywords.researching")}...
        </div>
      )}

      {!mutation.isPending && keywords.length === 0 && mutation.isSuccess && (
        <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
          {t("keywords.noResults")}
        </div>
      )}

      {!mutation.isPending && keywords.length > 0 && (
        <>
          <div className="border rounded-lg bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 w-10">
                      <input
                        type="checkbox"
                        checked={
                          paginatedKeywords.length > 0 &&
                          selectedKeywords.size === paginatedKeywords.length
                        }
                        onChange={toggleAll}
                        className="rounded border-input"
                        aria-label="Select all keywords"
                      />
                    </th>
                    <th className="text-left px-4 py-3 font-medium">
                      <SortHeader field="keyword">Keyword</SortHeader>
                    </th>
                    <th className="text-right px-4 py-3 font-medium">
                      <SortHeader field="search_volume" className="justify-end">
                        {t("keywords.searchVolume")}
                      </SortHeader>
                    </th>
                    <th className="text-left px-4 py-3 font-medium">
                      <SortHeader field="competition">
                        {t("keywords.competition")}
                      </SortHeader>
                    </th>
                    <th className="text-right px-4 py-3 font-medium">
                      <SortHeader field="opportunity_score" className="justify-end">
                        {t("keywords.opportunityScore")}
                      </SortHeader>
                    </th>
                    <th className="text-right px-4 py-3 font-medium">
                      <SortHeader field="cpc" className="justify-end">
                        {t("keywords.cpc")}
                      </SortHeader>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedKeywords.map((kw) => (
                    <tr
                      key={kw.keyword}
                      className="border-b last:border-b-0 hover:bg-muted/30"
                    >
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedKeywords.has(kw.keyword)}
                          onChange={() => toggleKeyword(kw.keyword)}
                          className="rounded border-input"
                          aria-label={`Select ${kw.keyword}`}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          className="font-medium text-primary hover:underline text-left"
                          onClick={() => onAnalyzeNiche?.(kw.keyword)}
                        >
                          {kw.keyword}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {kw.search_volume.toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <CompetitionBadge level={kw.competition_level} t={t} />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <OpportunityScore score={kw.opportunity_score} />
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        ${kw.cpc.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {t("keywords.showing")} {rangeStart}-{rangeEnd} / {totalResults}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage >= totalPages - 1}
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}

      {/* KDP Keyword Suggester */}
      {suggestedKdpKeywords.length > 0 && (
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
            <h3 className="text-lg font-semibold">{t("keywords.kdpSuggestion")}</h3>
          </div>
          <p className="text-sm text-muted-foreground">
            Suggested 7-keyword combo for KDP backend:
          </p>
          <div className="flex flex-wrap gap-2">
            {suggestedKdpKeywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center rounded-md bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary"
              >
                {kw}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={handleCopyKdpKeywords}>
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" aria-hidden="true" />
                  {t("keywords.copied")}
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" aria-hidden="true" />
                  {t("keywords.copyToClipboard")}
                </>
              )}
            </Button>
            <Button variant="outline" size="sm">
              <FolderPlus className="h-4 w-4 mr-2" aria-hidden="true" />
              {t("keywords.saveToProject")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
