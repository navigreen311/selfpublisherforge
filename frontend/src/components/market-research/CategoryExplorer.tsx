"use client";

import { useState, useMemo, useCallback } from "react";
import { ChevronRight, ChevronDown, Search, FolderTree, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import { useCategories, useCategoryMetrics } from "@/modules/market/hooks";
import type { CategoryNode } from "@/modules/market/hooks";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CategoryExplorerProps {
  onAnalyzeCategory?: (categoryId: string) => void;
  onViewTopBooks?: (categoryId: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface BreadcrumbEntry {
  id: string;
  name: string;
}

/** Return Tailwind classes for a 0-100 score badge. */
function scoreBadgeClasses(score: number): string {
  if (score >= 70) return "bg-green-100 text-green-700 border-green-200";
  if (score >= 40) return "bg-yellow-100 text-yellow-700 border-yellow-200";
  return "bg-red-100 text-red-700 border-red-200";
}

/** Format a number with locale-aware separators. */
function fmt(value: number | undefined | null): string {
  if (value == null) return "--";
  return value.toLocaleString();
}

/** Format a currency value. */
function fmtCurrency(value: number | undefined | null): string {
  if (value == null) return "--";
  return `$${value.toFixed(2)}`;
}

/** Recursively filter categories by search term. */
function filterCategories(
  categories: CategoryNode[],
  search: string,
): CategoryNode[] {
  if (!search.trim()) return categories;
  const lower = search.toLowerCase();

  return categories.reduce<CategoryNode[]>((acc, cat) => {
    const nameMatch = cat.name.toLowerCase().includes(lower);
    const filteredChildren = filterCategories(cat.children, search);

    if (nameMatch || filteredChildren.length > 0) {
      acc.push({
        ...cat,
        children: filteredChildren,
      });
    }

    return acc;
  }, []);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** A single metric cell in the metrics grid. */
function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-card p-3 text-center">
      <p className="text-xs font-medium text-muted-foreground mb-1">{label}</p>
      <p className="text-lg font-semibold text-foreground">{value}</p>
    </div>
  );
}

/** Score badge with color coding. */
function ScoreBadge({ label, score }: { label: string; score: number }) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge
        className={cn(
          "border text-xs font-bold tabular-nums",
          scoreBadgeClasses(score),
        )}
      >
        {Math.round(score)}
      </Badge>
    </div>
  );
}

/** A single node in the category tree. */
function TreeNode({
  node,
  depth,
  selectedId,
  expandedNodes,
  onSelect,
  onToggle,
}: {
  node: CategoryNode;
  depth: number;
  selectedId: string | null;
  expandedNodes: Set<string>;
  onSelect: (node: CategoryNode) => void;
  onToggle: (nodeId: string) => void;
}) {
  const isExpanded = expandedNodes.has(node.id);
  const isSelected = node.id === selectedId;
  const hasChildren =
    node.children.length > 0 || (node.children_count != null && node.children_count > 0);

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors cursor-pointer",
          isSelected
            ? "bg-primary/10 text-primary font-medium"
            : "hover:bg-accent text-foreground",
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {/* Expand/collapse chevron */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggle(node.id);
            }}
            className="flex-shrink-0 p-0.5 rounded hover:bg-muted"
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
            )}
          </button>
        ) : (
          <span className="w-[18px] flex-shrink-0" />
        )}

        {/* Category name - click to select */}
        <button
          onClick={() => onSelect(node)}
          className="flex-1 text-left truncate"
        >
          {node.name}
        </button>

        {/* Book count */}
        {node.book_count != null && (
          <span className="text-xs text-muted-foreground flex-shrink-0 tabular-nums">
            {node.book_count.toLocaleString()}
          </span>
        )}
      </div>

      {/* Lazy-loaded children */}
      {isExpanded && hasChildren && (
        <LazyChildren
          parentId={node.id}
          inlineChildren={node.children}
          depth={depth + 1}
          selectedId={selectedId}
          expandedNodes={expandedNodes}
          onSelect={onSelect}
          onToggle={onToggle}
        />
      )}
    </div>
  );
}

/** Lazy-loaded children: uses inline children if available, otherwise fetches. */
function LazyChildren({
  parentId,
  inlineChildren,
  depth,
  selectedId,
  expandedNodes,
  onSelect,
  onToggle,
}: {
  parentId: string;
  inlineChildren: CategoryNode[];
  depth: number;
  selectedId: string | null;
  expandedNodes: Set<string>;
  onSelect: (node: CategoryNode) => void;
  onToggle: (nodeId: string) => void;
}) {
  // If inline children are already present, render them directly.
  // Otherwise, lazy-load using the hook with rootId.
  const needsFetch = inlineChildren.length === 0;
  const { data: fetchedChildren, isLoading } = useCategories(
    needsFetch ? parentId : undefined,
  );

  const children = needsFetch ? fetchedChildren ?? [] : inlineChildren;

  if (isLoading && needsFetch) {
    return (
      <div className="space-y-1 py-1" style={{ paddingLeft: `${depth * 16 + 8}px` }}>
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-6 w-1/2" />
      </div>
    );
  }

  return (
    <>
      {children.map((child) => (
        <TreeNode
          key={child.id}
          node={child}
          depth={depth}
          selectedId={selectedId}
          expandedNodes={expandedNodes}
          onSelect={onSelect}
          onToggle={onToggle}
        />
      ))}
    </>
  );
}

/** Category metrics panel shown when a category is selected. */
function MetricsPanel({
  categoryId,
  categoryName,
  onAnalyze,
  onViewTopBooks,
}: {
  categoryId: string;
  categoryName: string;
  onAnalyze?: (id: string) => void;
  onViewTopBooks?: (id: string) => void;
}) {
  const t = useTranslations("market");
  const { data: metrics, isLoading } = useCategoryMetrics(categoryId);

  if (isLoading) {
    return (
      <div className="space-y-4 p-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <p className="text-sm text-muted-foreground">
          {t("categories.noSelection")}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Category title */}
      <h3 className="text-xl font-semibold text-foreground">{categoryName}</h3>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        <MetricItem
          label={t("categories.totalBooks")}
          value={fmt(metrics.total_books)}
        />
        <MetricItem
          label={t("categories.avgBsr")}
          value={fmt(metrics.avg_bsr)}
        />
        <MetricItem
          label={t("categories.avgPrice")}
          value={fmtCurrency(metrics.avg_price)}
        />
        <MetricItem
          label={t("categories.avgReviews")}
          value={fmt(metrics.avg_reviews)}
        />
        <MetricItem
          label={t("categories.topBsr")}
          value={fmt(metrics.top_bsr)}
        />
        <MetricItem
          label={t("categories.newBooks30d")}
          value={fmt(metrics.new_books_30d)}
        />
        <MetricItem
          label={t("categories.avgPubDate")}
          value={metrics.avg_pub_date ?? "--"}
        />
      </div>

      {/* Score badges */}
      <div className="space-y-2">
        <ScoreBadge
          label={t("categories.competition")}
          score={metrics.competition_score}
        />
        <ScoreBadge
          label={t("categories.saturation")}
          score={metrics.saturation_score}
        />
        <ScoreBadge
          label={t("categories.opportunity")}
          score={metrics.opportunity_score}
        />
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-2">
        <Button
          onClick={() => onAnalyze?.(categoryId)}
          className="flex-1"
        >
          <BarChart3 className="mr-2 h-4 w-4" />
          {t("categories.analyzeCategory")}
        </Button>
        <Button
          variant="outline"
          onClick={() => onViewTopBooks?.(categoryId)}
          className="flex-1"
        >
          {t("categories.viewTopBooks")}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function CategoryExplorer({
  onAnalyzeCategory,
  onViewTopBooks,
}: CategoryExplorerProps) {
  const t = useTranslations("market");

  // ---- State ----
  const [selectedCategory, setSelectedCategory] = useState<CategoryNode | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [searchFilter, setSearchFilter] = useState("");
  const [breadcrumbPath, setBreadcrumbPath] = useState<BreadcrumbEntry[]>([]);

  // ---- Data ----
  const { data: rootCategories, isLoading: isLoadingRoot } = useCategories();

  // ---- Derived ----
  const filteredCategories = useMemo(() => {
    if (!rootCategories) return [];
    return filterCategories(rootCategories, searchFilter);
  }, [rootCategories, searchFilter]);

  // ---- Handlers ----
  const handleToggle = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  const handleSelect = useCallback((node: CategoryNode) => {
    setSelectedCategory(node);

    // Build breadcrumb path by walking up from the selected node.
    // Since we don't have a parent map, we build it from the name
    // by finding the node path in the tree.
    setBreadcrumbPath((prev) => {
      // If the node is already in the breadcrumb path, truncate to it.
      const existingIndex = prev.findIndex((entry) => entry.id === node.id);
      if (existingIndex >= 0) {
        return prev.slice(0, existingIndex + 1);
      }

      // If the node's parent_id matches the last breadcrumb entry, append.
      if (
        node.parent_id &&
        prev.length > 0 &&
        prev[prev.length - 1].id === node.parent_id
      ) {
        return [...prev, { id: node.id, name: node.name }];
      }

      // Otherwise, start a new breadcrumb path with just this node.
      return [{ id: node.id, name: node.name }];
    });
  }, []);

  const handleBreadcrumbClick = useCallback(
    (entry: BreadcrumbEntry, index: number) => {
      // Truncate breadcrumb to the clicked entry and find the node in tree.
      setBreadcrumbPath((prev) => prev.slice(0, index + 1));

      // We need to locate the node to set it as selected.
      // For breadcrumb navigation, we create a minimal node reference.
      setSelectedCategory((prev) => {
        if (prev && prev.id === entry.id) return prev;
        return {
          id: entry.id,
          name: entry.name,
          parent_id: null,
          children: [],
          book_count: null,
        };
      });
    },
    [],
  );

  // ---- Render ----
  return (
    <div className="space-y-4">
      {/* Title */}
      <h2 className="text-lg font-semibold text-foreground">
        {t("categories.title")}
      </h2>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(280px,1fr)_minmax(320px,1.5fr)] gap-6">
        {/* Left Panel - Category Tree */}
        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FolderTree className="h-4 w-4" aria-hidden="true" />
              Amazon Categories
            </CardTitle>
          </CardHeader>

          <CardContent className="flex flex-col flex-1 gap-3 pt-0">
            {/* Breadcrumb navigation */}
            {breadcrumbPath.length > 0 && (
              <nav
                aria-label="Category breadcrumb"
                className="flex items-center gap-1 text-xs flex-wrap"
              >
                {breadcrumbPath.map((entry, idx) => (
                  <span key={entry.id} className="flex items-center gap-1">
                    {idx > 0 && (
                      <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    )}
                    {idx < breadcrumbPath.length - 1 ? (
                      <button
                        onClick={() => handleBreadcrumbClick(entry, idx)}
                        className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[120px]"
                        title={entry.name}
                      >
                        {entry.name}
                      </button>
                    ) : (
                      <span
                        className="font-medium text-foreground truncate max-w-[140px]"
                        title={entry.name}
                      >
                        {entry.name}
                      </span>
                    )}
                  </span>
                ))}
              </nav>
            )}

            {/* Search/filter input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t("categories.searchPlaceholder")}
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Tree view */}
            <div className="flex-1 overflow-y-auto max-h-[500px] -mx-2">
              {isLoadingRoot ? (
                <div className="space-y-2 px-2 py-1">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-7 w-full" />
                  ))}
                </div>
              ) : filteredCategories.length === 0 ? (
                <p className="px-2 py-4 text-sm text-muted-foreground text-center">
                  No categories found.
                </p>
              ) : (
                filteredCategories.map((cat) => (
                  <TreeNode
                    key={cat.id}
                    node={cat}
                    depth={0}
                    selectedId={selectedCategory?.id ?? null}
                    expandedNodes={expandedNodes}
                    onSelect={handleSelect}
                    onToggle={handleToggle}
                  />
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Right Panel - Category Metrics */}
        <Card>
          <CardContent className="p-6">
            {selectedCategory ? (
              <MetricsPanel
                categoryId={selectedCategory.id}
                categoryName={selectedCategory.name}
                onAnalyze={onAnalyzeCategory}
                onViewTopBooks={onViewTopBooks}
              />
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <BarChart3 className="h-10 w-10 text-muted-foreground/40 mb-4" />
                <p className="text-sm text-muted-foreground">
                  {t("categories.noSelection")}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
