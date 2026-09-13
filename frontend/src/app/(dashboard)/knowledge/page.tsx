"use client";

import { useState, useCallback, useMemo } from "react";
import { Plus, BookOpen, Trash2, Upload } from "lucide-react";
import { SearchBar } from "@/modules/knowledge/components/SearchBar";
import { CategoryFilter } from "@/modules/knowledge/components/CategoryFilter";
import type { CategoryItem } from "@/modules/knowledge/components/CategoryFilter";
import { EntryCard } from "@/modules/knowledge/components/EntryCard";
import { ImportModal } from "@/modules/knowledge/components/ImportModal";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useKnowledgeEntries,
  useKnowledgeSearch,
  useCreateEntry,
  useDeleteEntry,
} from "@/modules/knowledge/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import type { KnowledgeEntry, SearchHit } from "@/modules/knowledge/hooks";
import { useTranslations } from "@/hooks/use-translations";

export default function KnowledgeVaultPage() {
  const t = useTranslations("knowledge");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchHit[] | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeEntry | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const { data: entries, isPending: entriesPending } = useKnowledgeEntries();
  const searchMutation = useKnowledgeSearch();
  const createMutation = useCreateEntry();
  const deleteMutation = useDeleteEntry();

  // Derive categories from entries by metadata.category or source_type
  const categories: CategoryItem[] = useMemo(() => {
    if (!entries?.items) return [];
    const counts: Record<string, number> = {};
    for (const entry of entries.items) {
      const category =
        (typeof entry.metadata?.category === "string" && entry.metadata.category) ||
        entry.source_type;
      counts[category] = (counts[category] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [entries]);

  // Filter entries by selected category
  const filteredEntries = useMemo(() => {
    if (!entries?.items) return [];
    if (!selectedCategory) return entries.items;
    return entries.items.filter((entry) => {
      const category =
        (typeof entry.metadata?.category === "string" && entry.metadata.category) ||
        entry.source_type;
      return category === selectedCategory;
    });
  }, [entries, selectedCategory]);

  const handleSearch = useCallback(
    async (query: string) => {
      const result = await searchMutation.mutateAsync({ query });
      setSearchResults(result.hits);
    },
    [searchMutation]
  );

  const handleSelectCategory = useCallback((category: string | null) => {
    setSelectedCategory(category);
    setSearchResults(null);
  }, []);

  const handleCreate = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!newTitle.trim()) return;
      await createMutation.mutateAsync({
        title: newTitle.trim(),
        content: newContent,
        source_type: "manual",
      });
      setNewTitle("");
      setNewContent("");
      setCreateOpen(false);
    },
    [newTitle, newContent, createMutation]
  );

  const handleDeleteRequest = useCallback((entry: KnowledgeEntry) => {
    setDeleteTarget(entry);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  }, [deleteTarget, deleteMutation]);

  const handleCancelDelete = useCallback(() => {
    setDeleteTarget(null);
  }, []);

  return (
    <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <BookOpen className="h-5 w-5 sm:h-6 sm:w-6 text-primary" aria-hidden="true" />
          <h1 className="text-xl sm:text-2xl font-bold">{t("title")}</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setImportOpen(true)}
            aria-label={t("importLabel")}
            className="flex-1 sm:flex-none px-3 sm:px-4 py-2 text-xs sm:text-sm border rounded-lg hover:bg-accent transition-colors"
          >
            {t("import")}
          </button>
          <button
            onClick={() => setCreateOpen(true)}
            aria-label={t("newEntryLabel")}
            className="flex-1 sm:flex-none flex items-center justify-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-xs sm:text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-3.5 w-3.5 sm:h-4 sm:w-4" aria-hidden="true" /> {t("newEntry")}
          </button>
        </div>
      </div>

      {/* Search */}
      <SearchBar onSearch={handleSearch} isLoading={searchMutation.isPending} />

      {/* Category filters */}
      {categories.length > 0 && (
        <CategoryFilter
          categories={categories}
          selectedCategory={selectedCategory}
          onSelect={handleSelectCategory}
        />
      )}

      {/* Search results */}
      {searchResults && (
        <div className="space-y-2 sm:space-y-3">
          <div className="flex items-center justify-between">
            <h2 id="search-results-heading" className="text-xs sm:text-sm font-medium text-muted-foreground">
              {t("searchResults", { count: searchResults.length })}
            </h2>
            <button
              onClick={() => setSearchResults(null)}
              aria-label={t("clearSearchLabel")}
              className="text-[10px] sm:text-xs text-primary hover:underline"
            >
              {t("clearSearch")}
            </button>
          </div>
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
            role="list"
            aria-describedby="search-results-heading"
            aria-label="Search results"
          >
            {searchResults.map((hit) => (
              <div key={hit.id} className="border rounded-lg p-3 sm:p-4 bg-card" role="listitem">
                <div className="flex items-start justify-between gap-2">
                  <a
                    href={`/knowledge/${hit.id}`}
                    className="font-semibold text-xs sm:text-sm hover:text-primary transition-colors truncate"
                    aria-label={t("viewEntry", { title: hit.title })}
                  >
                    {hit.title}
                  </a>
                  <button
                    onClick={() =>
                      handleDeleteRequest({
                        id: hit.id,
                        title: hit.title,
                        content: hit.content_snippet,
                        source_type: hit.source_type as KnowledgeEntry["source_type"],
                        tags: hit.tags,
                        credibility_score: hit.credibility_score,
                        created_at: hit.created_at,
                        org_id: "",
                        source_url: null,
                        metadata: {},
                        updated_at: null,
                        deleted_at: null,
                      })
                    }
                    aria-label={t("deleteEntry", { title: hit.title })}
                    className="shrink-0 p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="h-3 w-3 sm:h-3.5 sm:w-3.5" aria-hidden="true" />
                  </button>
                </div>
                <p className="mt-1 text-[10px] sm:text-xs text-muted-foreground line-clamp-3">
                  {hit.content_snippet}
                </p>
                <div className="mt-1.5 sm:mt-2 flex flex-wrap gap-1">
                  {hit.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="text-[9px] sm:text-[10px] px-1.5 sm:px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="mt-1 text-[9px] sm:text-[10px] text-muted-foreground">
                  {t("relevance", { score: hit.score.toFixed(2) })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Entry list */}
      {!searchResults && (
        <div>
          {entriesPending ? (
            <div
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
              aria-label="Loading knowledge entries"
            >
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-28 sm:h-32" />
              ))}
            </div>
          ) : filteredEntries.length > 0 ? (
            <>
              <p id="entries-count" className="text-xs sm:text-sm text-muted-foreground mb-2 sm:mb-3">
                {filteredEntries.length} {t("entries")}
              </p>
              <div
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
                role="list"
                aria-describedby="entries-count"
                aria-label="Knowledge entries"
              >
                {filteredEntries.map((entry) => (
                  <div key={entry.id} className="relative group" role="listitem">
                    <EntryCard entry={entry} />
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDeleteRequest(entry);
                      }}
                      aria-label={t("deleteEntry", { title: entry.title })}
                      className="absolute top-2 right-2 p-1 sm:p-1.5 rounded-md bg-background/80 border opacity-0 group-hover:opacity-100 focus:opacity-100 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                    >
                      <Trash2 className="h-3 w-3 sm:h-3.5 sm:w-3.5" aria-hidden="true" />
                    </button>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12 sm:py-16">
              <BookOpen className="mx-auto h-12 w-12 sm:h-14 sm:w-14 text-muted-foreground/30" aria-hidden="true" />
              <h3 className="mt-4 sm:mt-5 text-base sm:text-lg font-semibold">
                Your Knowledge Vault is empty
              </h3>
              <p className="mt-1.5 text-xs sm:text-sm text-muted-foreground max-w-sm mx-auto">
                Start building your research library.
              </p>
              <div className="mt-5 sm:mt-6 flex items-center justify-center gap-3">
                <button
                  onClick={() => setCreateOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs sm:text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <Plus className="h-4 w-4" aria-hidden="true" />
                  Create First Entry
                </button>
                <button
                  onClick={() => setImportOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs sm:text-sm border rounded-lg hover:bg-accent transition-colors"
                >
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  Import Files
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create entry dialog (inline) */}
      {createOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-dialog-title"
        >
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setCreateOpen(false)}
            aria-label="Close create entry dialog"
          />
          <div className="relative bg-background border rounded-xl shadow-xl w-full max-w-lg p-4 sm:p-6">
            <h2 id="create-dialog-title" className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">{t("newKnowledgeEntry")}</h2>
            <form onSubmit={handleCreate} className="space-y-3 sm:space-y-4" aria-label="Create knowledge entry form">
              <div>
                <label htmlFor="new-entry-title" className="block text-xs sm:text-sm font-medium mb-1">{t("titleLabel")}</label>
                <input
                  id="new-entry-title"
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-xs sm:text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                  required
                />
              </div>
              <div>
                <label htmlFor="new-entry-content" className="block text-xs sm:text-sm font-medium mb-1">{t("content")}</label>
                <textarea
                  id="new-entry-content"
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  rows={6}
                  className="w-full border rounded-lg px-3 py-2 text-xs sm:text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  aria-label={t("cancelLabel")}
                  className="px-3 sm:px-4 py-2 text-xs sm:text-sm border rounded-lg hover:bg-accent"
                >
                  {t("cancel")}
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  aria-label={createMutation.isPending ? t("creatingLabel") : t("createLabel")}
                  className="px-3 sm:px-4 py-2 text-xs sm:text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {createMutation.isPending ? t("creating") : t("create")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title={t("deleteConfirmTitle")}
        description={
          deleteTarget
            ? t("deleteConfirmMessage", { title: deleteTarget.title })
            : ""
        }
        confirmLabel={t("deleteButton")}
        cancelLabel={t("cancelButton")}
        variant="destructive"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        loading={isDeleting}
      />

      {/* Import modal */}
      <ImportModal open={importOpen} onClose={() => setImportOpen(false)} />
    </div>
  );
}
