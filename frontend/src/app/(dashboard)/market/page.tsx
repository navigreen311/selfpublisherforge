"use client";

import { useState } from "react";
import {
  useCategories,
  useCategoryAnalysis,
  useNicheAnalysis,
  useMarketTrends,
  useMarketSnapshots,
  type CategoryNode,
} from "@/modules/market/hooks";
import { CategoryTree, NicheScoreCard, TrendChart } from "@/modules/market/components";
import { Skeleton } from "@/components/ui/skeleton";

export default function MarketDashboardPage() {
  const [selectedCategory, setSelectedCategory] = useState<CategoryNode | null>(null);
  const [nicheQuery, setNicheQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data: categories = [], isLoading: catsLoading } = useCategories();
  const { data: categoryAnalysis } = useCategoryAnalysis(selectedCategory?.id ?? "");
  const nicheAnalysis = useNicheAnalysis();
  const { data: trends } = useMarketTrends(
    selectedCategory?.id,
    undefined,
    30
  );
  const { data: snapshots = [], isLoading: snapshotsLoading } = useMarketSnapshots(selectedCategory?.id);

  const handleAnalyzeNiche = () => {
    if (!searchInput.trim()) return;
    setNicheQuery(searchInput.trim());
    nicheAnalysis.mutate({
      niche: searchInput.trim(),
      category_id: selectedCategory?.id,
    });
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div role="region" aria-label="Page header">
        <h1 className="text-2xl font-bold">Market Intelligence</h1>
        <p className="text-muted-foreground mt-1">
          Analyze niches, explore categories, and discover market opportunities
        </p>
      </div>

      {/* Search bar */}
      <div role="search" aria-label="Niche analysis search" className="flex gap-3">
        <label htmlFor="niche-search" className="sr-only">
          Enter a niche to analyze
        </label>
        <input
          id="niche-search"
          type="text"
          placeholder="Enter a niche to analyze (e.g., 'self-help for millennials')..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAnalyzeNiche()}
          className="flex-1 px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          aria-describedby="niche-search-hint"
        />
        <span id="niche-search-hint" className="sr-only">
          Type a niche keyword and press Enter or click Analyze Niche to get market analysis
        </span>
        <button
          onClick={handleAnalyzeNiche}
          disabled={nicheAnalysis.isPending || !searchInput.trim()}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={nicheAnalysis.isPending ? "Analyzing niche, please wait" : "Analyze niche"}
        >
          {nicheAnalysis.isPending ? "Analyzing..." : "Analyze Niche"}
        </button>
      </div>

      {/* Niche analysis results */}
      <div aria-live="polite" aria-atomic="true" role="region" aria-label="Niche analysis results">
        {nicheAnalysis.data && <NicheScoreCard analysis={nicheAnalysis.data} />}

        {nicheAnalysis.isError && (
          <div role="alert" className="border border-red-200 rounded-lg bg-red-50 p-4 text-sm text-red-700">
            Failed to analyze niche. Please try again.
          </div>
        )}
      </div>

      {/* Main grid: category tree + analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category tree */}
        <div className="lg:col-span-1" role="region" aria-label="Category browser">
          {catsLoading ? (
            <div className="border rounded-lg bg-card p-4 space-y-3" aria-busy="true" aria-label="Loading categories">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-8" />
              ))}
            </div>
          ) : (
            <CategoryTree
              categories={categories}
              onSelect={setSelectedCategory}
              selectedId={selectedCategory?.id}
            />
          )}
        </div>

        {/* Category analysis */}
        <div className="lg:col-span-2 space-y-4" role="region" aria-label="Category analysis details">
          {categoryAnalysis ? (
            <>
              <div className="border rounded-lg bg-card p-6">
                <h3 className="font-semibold text-lg mb-4">
                  {categoryAnalysis.category_name}
                </h3>
                <div
                  className="grid grid-cols-2 sm:grid-cols-4 gap-4"
                  role="group"
                  aria-label="Category statistics"
                >
                  <StatCard label="Books" value={categoryAnalysis.book_count.toLocaleString()} />
                  <StatCard label="Avg BSR" value={Math.round(categoryAnalysis.avg_bsr).toLocaleString()} />
                  <StatCard label="Avg Price" value={`$${categoryAnalysis.avg_price.toFixed(2)}`} />
                  <StatCard label="Competition" value={`${categoryAnalysis.competition_score.toFixed(0)}/100`} />
                  <StatCard label="Avg Reviews" value={Math.round(categoryAnalysis.avg_reviews).toLocaleString()} />
                  <StatCard label="Avg Rating" value={`${categoryAnalysis.avg_rating.toFixed(1)} stars`} />
                  <StatCard label="Median BSR" value={Math.round(categoryAnalysis.median_bsr).toLocaleString()} />
                </div>

                {/* BSR Distribution */}
                <div className="mt-6" role="region" aria-label="BSR distribution chart">
                  <h4 className="text-sm font-medium mb-3">BSR Distribution</h4>
                  <div
                    className="flex gap-2"
                    role="img"
                    aria-describedby="bsr-distribution-desc"
                  >
                    {Object.entries(categoryAnalysis.bsr_distribution).map(([range, count]) => (
                      <div key={range} className="flex-1 text-center">
                        <div
                          className="bg-primary/20 rounded-t-md mx-auto"
                          style={{
                            height: `${Math.max(8, (count / categoryAnalysis.book_count) * 200)}px`,
                            width: "100%",
                          }}
                        />
                        <div className="text-xs text-muted-foreground mt-1">{range}</div>
                        <div className="text-xs font-medium">{count}</div>
                      </div>
                    ))}
                  </div>
                  <p id="bsr-distribution-desc" className="sr-only">
                    Bar chart showing the distribution of Best Sellers Rank across different ranges for this category
                  </p>
                </div>

                {/* Top books */}
                {categoryAnalysis.top_books.length > 0 && (
                  <div className="mt-6" role="region" aria-label="Top books in category">
                    <h4 className="text-sm font-medium mb-3">Top Books</h4>
                    <div
                      className="space-y-2"
                      role="list"
                      aria-describedby="top-books-desc"
                    >
                      <span id="top-books-desc" className="sr-only">
                        List of top-performing books showing title, BSR rank, and price
                      </span>
                      {categoryAnalysis.top_books.map((book) => (
                        <div
                          key={book.asin}
                          role="listitem"
                          className="flex items-center gap-3 p-2 rounded-md bg-muted/50 text-sm"
                        >
                          <span className="font-medium flex-1 truncate">{book.title}</span>
                          <span className="text-muted-foreground text-xs">
                            BSR: {book.bsr?.toLocaleString() ?? "N/A"}
                          </span>
                          <span className="text-muted-foreground text-xs">
                            ${book.price?.toFixed(2) ?? "N/A"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground">
              Select a category from the tree to view analysis
            </div>
          )}

          {/* Trends */}
          {trends && trends.trends.length > 0 && (
            <div className="space-y-4" role="region" aria-label="Market trends">
              <h3 className="font-semibold">Market Trends</h3>
              {trends.trends.map((t, i) => (
                <TrendChart key={i} trend={t} />
              ))}
            </div>
          )}

          {/* Snapshots summary */}
          <div role="region" aria-label="Market snapshots">
            {snapshotsLoading ? (
              <div className="border rounded-lg bg-card p-6 space-y-3" aria-busy="true" aria-label="Loading snapshots">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-64" />
              </div>
            ) : snapshots.length > 0 ? (
              <div className="border rounded-lg bg-card p-6">
                <h3 className="font-semibold mb-3">Recent Snapshots</h3>
                <div className="text-sm text-muted-foreground">
                  {snapshots.length} daily snapshots available for analysis.
                  Latest: {new Date(snapshots[0].snapshot_date).toLocaleDateString()}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-md bg-muted/50 text-center" role="group" aria-label={`${label}: ${value}`}>
      <div className="text-lg font-semibold" aria-hidden="true">{value}</div>
      <div className="text-xs text-muted-foreground" aria-hidden="true">{label}</div>
    </div>
  );
}
