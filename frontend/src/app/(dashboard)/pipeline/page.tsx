import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Production Pipeline",
  description: "Manage book production workflows from draft to publication with automated AI-powered pipelines.",
  noindex: true,
});

"use client";

import { useState } from "react";
import { usePipelines, useCreatePipeline } from "@/modules/pipeline/hooks";
import { useBooks } from "@/modules/writing/hooks";
import { PipelineCard } from "@/modules/pipeline/components/PipelineCard";
import { Skeleton } from "@/components/ui/skeleton";
import type { PipelineStatus } from "@/modules/pipeline/hooks";

// ---------------------------------------------------------------------------
// Constants & Validation helpers
// ---------------------------------------------------------------------------

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const STATUS_FILTERS: { label: string; value: PipelineStatus | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Draft", value: "draft" },
  { label: "Active", value: "active" },
  { label: "Paused", value: "paused" },
  { label: "Completed", value: "completed" },
];

function getPipelineNameError(name: string, touched: boolean): string | undefined {
  if (!touched) return undefined;
  const trimmed = name.trim();
  if (!trimmed) return "Pipeline name is required.";
  if (trimmed.length < 3) return "Pipeline name must be at least 3 characters.";
  if (trimmed.length > 100) return "Pipeline name must be 100 characters or fewer.";
  return undefined;
}

function getBookIdError(bookId: string, touched: boolean): string | undefined {
  if (!touched) return undefined;
  const trimmed = bookId.trim();
  if (!trimmed) return "Please select or enter a book.";
  if (!UUID_REGEX.test(trimmed)) return "Book ID must be a valid UUID (e.g. 550e8400-e29b-41d4-a716-446655440000).";
  return undefined;
}

export default function PipelineDashboardPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<PipelineStatus | undefined>(
    undefined
  );
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newBookId, setNewBookId] = useState("");
  const [useManualBookId, setUseManualBookId] = useState(false);

  // -- Touched state for inline validation --
  const [touchedName, setTouchedName] = useState(false);
  const [touchedBookId, setTouchedBookId] = useState(false);

  const { data, isLoading, error } = usePipelines(page, 20, statusFilter);
  const createMutation = useCreatePipeline();
  const { data: books, isLoading: booksLoading } = useBooks();

  const nameError = getPipelineNameError(newName, touchedName);
  const bookIdError = getBookIdError(newBookId, touchedBookId);

  // Form is valid when there are no errors (checked ignoring touched state)
  const isFormValid =
    !getPipelineNameError(newName, true) && !getBookIdError(newBookId, true);

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();

    // Mark all fields as touched to reveal any remaining errors
    setTouchedName(true);
    setTouchedBookId(true);

    if (!isFormValid) return;

    createMutation.mutate(
      { name: newName.trim(), book_id: newBookId.trim() },
      {
        onSuccess: () => {
          setShowCreate(false);
          setNewName("");
          setNewBookId("");
          setTouchedName(false);
          setTouchedBookId(false);
          setUseManualBookId(false);
        },
      }
    );
  }

  // Reset form state when toggling the create panel
  function handleToggleCreate() {
    if (showCreate) {
      // Closing -- reset form
      setNewName("");
      setNewBookId("");
      setTouchedName(false);
      setTouchedBookId(false);
      setUseManualBookId(false);
    }
    setShowCreate(!showCreate);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Production Pipeline</h1>
        <button
          onClick={handleToggleCreate}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          New Pipeline
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 border rounded-lg p-4 space-y-3"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="pl-name" className="block text-sm font-medium mb-1">
                Pipeline Name
              </label>
              <input
                id="pl-name"
                type="text"
                className={`w-full border rounded-md px-3 py-2 text-sm ${
                  nameError ? "border-red-500 focus:ring-red-500" : ""
                }`}
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onBlur={() => setTouchedName(true)}
                placeholder="e.g. My Novel Production"
              />
              {nameError && (
                <p className="mt-1 text-sm text-red-600">{nameError}</p>
              )}
            </div>
            <div>
              <label htmlFor="pl-book" className="block text-sm font-medium mb-1">
                Book
              </label>
              {/* Show dropdown when books are available and user hasn't opted for manual entry */}
              {!useManualBookId && books && books.length > 0 ? (
                <>
                  <select
                    id="pl-book"
                    className={`w-full border rounded-md px-3 py-2 text-sm bg-card ${
                      bookIdError ? "border-red-500 focus:ring-red-500" : ""
                    }`}
                    value={newBookId}
                    onChange={(e) => {
                      setNewBookId(e.target.value);
                      setTouchedBookId(true);
                    }}
                    onBlur={() => setTouchedBookId(true)}
                  >
                    <option value="">Select a book...</option>
                    {books.map((book) => (
                      <option key={book.id} value={book.id}>
                        {book.title}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => {
                      setUseManualBookId(true);
                      setNewBookId("");
                      setTouchedBookId(false);
                    }}
                    className="mt-1 text-xs text-blue-600 hover:underline"
                  >
                    Enter Book ID manually instead
                  </button>
                </>
              ) : (
                <>
                  <input
                    id="pl-book"
                    type="text"
                    className={`w-full border rounded-md px-3 py-2 text-sm ${
                      bookIdError ? "border-red-500 focus:ring-red-500" : ""
                    }`}
                    value={newBookId}
                    onChange={(e) => setNewBookId(e.target.value)}
                    onBlur={() => setTouchedBookId(true)}
                    placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  />
                  {booksLoading && (
                    <p className="mt-1 text-xs text-muted-foreground">Loading books...</p>
                  )}
                  {useManualBookId && books && books.length > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setUseManualBookId(false);
                        setNewBookId("");
                        setTouchedBookId(false);
                      }}
                      className="mt-1 text-xs text-blue-600 hover:underline"
                    >
                      Select from your books instead
                    </button>
                  )}
                </>
              )}
              {bookIdError && (
                <p className="mt-1 text-sm text-red-600">{bookIdError}</p>
              )}
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={handleToggleCreate}
              className="px-4 py-2 text-sm border rounded-md hover:bg-muted"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !isFormValid}
              className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      )}

      {/* Status filters */}
      <div className="flex gap-2 mb-6">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => {
              setStatusFilter(f.value);
              setPage(1);
            }}
            className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
              statusFilter === f.value
                ? "bg-primary text-primary-foreground"
                : "bg-card hover:bg-muted"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Pipeline grid */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      )}
      {error && (
        <p className="text-red-600 text-sm">
          Failed to load pipelines. Please try again.
        </p>
      )}
      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-muted-foreground">
            No pipelines found. Create one to get started.
          </p>
        </div>
      )}
      {data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {data.items.map((pipeline) => (
              <PipelineCard key={pipeline.id} pipeline={pipeline} />
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 text-sm border rounded-md disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {data.page} of {data.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
                className="px-3 py-1 text-sm border rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
