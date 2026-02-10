"use client";

import { useState, useCallback } from "react";
import { Plus, BookOpen } from "lucide-react";
import { SearchBar } from "@/modules/knowledge/components/SearchBar";
import { TagFilter } from "@/modules/knowledge/components/TagFilter";
import { EntryCard } from "@/modules/knowledge/components/EntryCard";
import { ImportModal } from "@/modules/knowledge/components/ImportModal";
import {
  useKnowledgeEntries,
  useKnowledgeTags,
  useKnowledgeSearch,
  useCreateEntry,
} from "@/modules/knowledge/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import type { SearchHit } from "@/modules/knowledge/hooks";

export default function KnowledgeVaultPage() {
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [importOpen, setImportOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchHit[] | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");

  const { data: entries, isLoading: entriesLoading } = useKnowledgeEntries({
    tag: selectedTags.length > 0 ? selectedTags : undefined,
  });
  const { data: tagData } = useKnowledgeTags();
  const searchMutation = useKnowledgeSearch();
  const createMutation = useCreateEntry();

  const handleSearch = useCallback(
    async (query: string) => {
      const result = await searchMutation.mutateAsync({
        query,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
      });
      setSearchResults(result.hits);
    },
    [searchMutation, selectedTags]
  );

  const handleToggleTag = useCallback((tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">Knowledge Vault</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setImportOpen(true)}
            className="px-4 py-2 text-sm border rounded-lg hover:bg-accent transition-colors"
          >
            Import
          </button>
          <button
            onClick={() => setCreateOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> New Entry
          </button>
        </div>
      </div>

      {/* Search */}
      <SearchBar onSearch={handleSearch} isLoading={searchMutation.isPending} />

      {/* Tag filters */}
      {tagData && (
        <TagFilter
          tags={tagData.tags}
          counts={tagData.counts}
          selectedTags={selectedTags}
          onToggleTag={handleToggleTag}
        />
      )}

      {/* Search results */}
      {searchResults && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-muted-foreground">
              Search results ({searchResults.length})
            </h2>
            <button
              onClick={() => setSearchResults(null)}
              className="text-xs text-primary hover:underline"
            >
              Clear search
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {searchResults.map((hit) => (
              <div key={hit.id} className="border rounded-lg p-4 bg-card">
                <a
                  href={`/knowledge/${hit.id}`}
                  className="font-semibold text-sm hover:text-primary transition-colors"
                >
                  {hit.title}
                </a>
                <p className="mt-1 text-xs text-muted-foreground line-clamp-3">
                  {hit.content_snippet}
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {hit.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="mt-1 text-[10px] text-muted-foreground">
                  Relevance: {hit.score.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Entry list */}
      {!searchResults && (
        <div>
          {entriesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : entries && entries.items.length > 0 ? (
            <>
              <p className="text-sm text-muted-foreground mb-3">
                {entries.total_count} entries
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {entries.items.map((entry) => (
                  <EntryCard key={entry.id} entry={entry} />
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/30" />
              <h3 className="mt-4 text-lg font-medium">No entries yet</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Create your first research entry or import from a URL or file.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Create entry dialog (inline) */}
      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setCreateOpen(false)} />
          <div className="relative bg-background border rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
            <h2 className="text-lg font-semibold mb-4">New Knowledge Entry</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Content</label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  rows={6}
                  className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="px-4 py-2 text-sm border rounded-lg hover:bg-accent"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {createMutation.isPending ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import modal */}
      <ImportModal open={importOpen} onClose={() => setImportOpen(false)} />
    </div>
  );
}
