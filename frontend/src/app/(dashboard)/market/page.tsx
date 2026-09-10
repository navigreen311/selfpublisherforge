"use client";

import { useState, useCallback } from "react";
import { useNicheAnalysis, useTrackCompetitor } from "@/modules/market/hooks";
import { useTranslations } from "@/hooks/use-translations";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { NicheScorecard } from "@/components/market-research/NicheScorecard";
import { CompetitorBooksTable } from "@/components/market-research/CompetitorBooksTable";
import { MarketCharts } from "@/components/market-research/MarketCharts";
import { AIMarketSummary } from "@/components/market-research/AIMarketSummary";
import { KeywordResearch } from "@/components/market-research/KeywordResearch";
import { CategoryExplorer } from "@/components/market-research/CategoryExplorer";
import { TrendTracker } from "@/components/market-research/TrendTracker";

// ---------------------------------------------------------------------------
// Suggested searches (hardcoded examples)
// ---------------------------------------------------------------------------

const SUGGESTED_NICHES = [
  "Self-Help Journaling",
  "Cozy Mystery",
  "Low-Content Puzzle Books",
  "Dark Romance",
  "Children's STEM Activities",
  "Personal Finance for Millennials",
];

// ---------------------------------------------------------------------------
// Filter options
// ---------------------------------------------------------------------------

const MARKETPLACES = [
  { value: "US", label: "Amazon.com (US)" },
  { value: "UK", label: "Amazon.co.uk (UK)" },
  { value: "DE", label: "Amazon.de (DE)" },
  { value: "CA", label: "Amazon.ca (CA)" },
  { value: "AU", label: "Amazon.com.au (AU)" },
];

const FORMATS = [
  { value: "", labelKey: "filters.allFormats" },
  { value: "kindle", labelKey: "filters.kindle" },
  { value: "paperback", labelKey: "filters.paperback" },
  { value: "hardcover", labelKey: "filters.hardcover" },
  { value: "audiobook", labelKey: "filters.audiobook" },
];

const DATE_RANGES = [
  { value: "30d", labelKey: "filters.last30d" },
  { value: "90d", labelKey: "filters.last90d" },
  { value: "6m", labelKey: "filters.last180d" },
  { value: "1y", labelKey: "filters.last365d" },
  { value: "all", labelKey: "filters.allTime" },
];

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function MarketResearchPage() {
  const t = useTranslations("market");

  // ---- State ----
  const [activeTab, setActiveTab] = useState("niche");
  const [searchInput, setSearchInput] = useState("");
  const [marketplace, setMarketplace] = useState("US");
  const [format, setFormat] = useState("");
  const [dateRange, setDateRange] = useState("90d");
  const [nicheQuery, setNicheQuery] = useState("");

  // ---- Hooks ----
  const nicheAnalysis = useNicheAnalysis();
  const trackCompetitor = useTrackCompetitor();

  // ---- Handlers ----

  const handleAnalyzeNiche = useCallback(() => {
    const query = searchInput.trim();
    if (!query) return;

    setNicheQuery(query);
    nicheAnalysis.mutate({
      niche: query,
      marketplace,
      format: format || undefined,
      date_range: dateRange,
    });
  }, [searchInput, marketplace, format, dateRange, nicheAnalysis]);

  const handleSwitchToNiche = useCallback(
    (term: string) => {
      setActiveTab("niche");
      setSearchInput(term);
      setNicheQuery(term);
      nicheAnalysis.mutate({
        niche: term,
        marketplace,
        format: format || undefined,
        date_range: dateRange,
      });
    },
    [marketplace, format, dateRange, nicheAnalysis]
  );

  const handleAnalyzeCategory = useCallback(
    (categoryId: string) => {
      handleSwitchToNiche(categoryId);
    },
    [handleSwitchToNiche]
  );

  const handleViewTopBooks = useCallback(
    (categoryId: string) => {
      handleSwitchToNiche(categoryId);
    },
    [handleSwitchToNiche]
  );

  const handleSuggestedClick = useCallback(
    (niche: string) => {
      setSearchInput(niche);
      setNicheQuery(niche);
      nicheAnalysis.mutate({
        niche,
        marketplace,
        format: format || undefined,
        date_range: dateRange,
      });
    },
    [marketplace, format, dateRange, nicheAnalysis]
  );

  // ---- Render ----

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* Page Header                                                        */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-muted-foreground mt-1">{t("subtitle")}</p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Tabbed Interface                                                   */}
      {/* ------------------------------------------------------------------ */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4">
          <TabsTrigger value="niche">{t("tabs.nicheAnalyzer")}</TabsTrigger>
          <TabsTrigger value="keywords">
            {t("tabs.keywordResearch")}
          </TabsTrigger>
          <TabsTrigger value="categories">
            {t("tabs.categoryExplorer")}
          </TabsTrigger>
          <TabsTrigger value="trends">{t("tabs.trends")}</TabsTrigger>
        </TabsList>

        {/* ================================================================ */}
        {/* Tab 1 -- Niche Analyzer                                          */}
        {/* ================================================================ */}
        <TabsContent value="niche" className="space-y-6 mt-6">
          {/* Search Input */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                aria-label={t("nicheSearchLabel")}
                placeholder={t("nicheSearchPlaceholder")}
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAnalyzeNiche()}
                className="flex-1 px-4 py-3 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
              <button
                onClick={handleAnalyzeNiche}
                disabled={nicheAnalysis.isPending || !searchInput.trim()}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {nicheAnalysis.isPending
                  ? t("analyzing")
                  : t("analyzeNiche")}
              </button>
            </div>

            {/* Filters Row */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Marketplace */}
              <div className="flex items-center gap-2">
                <label
                  htmlFor="marketplace-filter"
                  className="text-xs font-medium text-muted-foreground"
                >
                  {t("filters.marketplace")}
                </label>
                <select
                  id="marketplace-filter"
                  value={marketplace}
                  onChange={(e) => setMarketplace(e.target.value)}
                  className="px-3 py-1.5 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {MARKETPLACES.map((mp) => (
                    <option key={mp.value} value={mp.value}>
                      {mp.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Format */}
              <div className="flex items-center gap-2">
                <label
                  htmlFor="format-filter"
                  className="text-xs font-medium text-muted-foreground"
                >
                  {t("filters.format")}
                </label>
                <select
                  id="format-filter"
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="px-3 py-1.5 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {FORMATS.map((f) => (
                    <option key={f.value} value={f.value}>
                      {t(f.labelKey)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Date Range */}
              <div className="flex items-center gap-2">
                <label
                  htmlFor="daterange-filter"
                  className="text-xs font-medium text-muted-foreground"
                >
                  {t("filters.dateRange")}
                </label>
                <select
                  id="daterange-filter"
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="px-3 py-1.5 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {DATE_RANGES.map((dr) => (
                    <option key={dr.value} value={dr.value}>
                      {t(dr.labelKey)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Suggested Searches */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {t("trySuggestions")}
              </span>
              {SUGGESTED_NICHES.map((niche) => (
                <button
                  key={niche}
                  onClick={() => handleSuggestedClick(niche)}
                  className="px-3 py-1 rounded-full border text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  {niche}
                </button>
              ))}
            </div>
          </div>

          {/* Error State */}
          {nicheAnalysis.isError && (
            <div
              role="alert"
              className="border border-red-200 rounded-lg bg-red-50 dark:bg-red-950/20 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-400"
            >
              {t("nicheAnalysisError")}
            </div>
          )}

          {/* Results */}
          {nicheAnalysis.data && (
            <div className="space-y-6">
              <NicheScorecard analysis={nicheAnalysis.data} />

              <CompetitorBooksTable
                books={nicheAnalysis.data.top_competitors}
                onTrack={(asin) =>
                  trackCompetitor.mutate({ asin, marketplace })
                }
              />

              <MarketCharts
                chartsData={nicheAnalysis.data.charts_data}
                books={nicheAnalysis.data.top_competitors}
              />

              <AIMarketSummary nicheData={nicheAnalysis.data} />
            </div>
          )}
        </TabsContent>

        {/* ================================================================ */}
        {/* Tab 2 -- Keyword Research                                        */}
        {/* ================================================================ */}
        <TabsContent value="keywords" className="mt-6">
          <KeywordResearch onAnalyzeNiche={handleSwitchToNiche} />
        </TabsContent>

        {/* ================================================================ */}
        {/* Tab 3 -- Category Explorer                                       */}
        {/* ================================================================ */}
        <TabsContent value="categories" className="mt-6">
          <CategoryExplorer
            onAnalyzeCategory={handleAnalyzeCategory}
            onViewTopBooks={handleViewTopBooks}
          />
        </TabsContent>

        {/* ================================================================ */}
        {/* Tab 4 -- Trends                                                  */}
        {/* ================================================================ */}
        <TabsContent value="trends" className="mt-6">
          <TrendTracker onAnalyzeTrend={handleSwitchToNiche} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
