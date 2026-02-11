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
import { useTranslations } from "@/hooks/use-translations";

// ---------------------------------------------------------------------------
// Constants & Validation helpers
// ---------------------------------------------------------------------------

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const STATUS_FILTERS: { label: string; value: PipelineStatus | undefined }[] = [
  { label: "filterAll", value: undefined },
  { label: "filterDraft", value: "draft" },
  { label: "filterActive", value: "active" },
  { label: "filterPaused", value: "paused" },
  { label: "filterCompleted", value: "completed" },
];

function getPipelineNameError(name: string, touched: boolean, t: (key: string) => string): string | undefined {
  if (!touched) return undefined;
  const trimmed = name.trim();
  if (!trimmed) return t("pipelineNameRequired");
  if (trimmed.length < 3) return t("pipelineNameMinLength");
  if (trimmed.length > 100) return t("pipelineNameMaxLength");
  return undefined;
}

function getBookIdError(bookId: string, touched: boolean, t: (key: string) => string): string | undefined {
  if (!touched) return undefined;
  const trimmed = bookId.trim();
  if (!trimmed) return t("bookRequired");
  if (!UUID_REGEX.test(trimmed)) return t("bookIdInvalid");
  return undefined;
}

export default function PipelineDashboardPage() {
  const t = useTranslations("pipeline");
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

  const nameError = getPipelineNameError(newName, touchedName, t);
  const bookIdError = getBookIdError(newBookId, touchedBookId, t);

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
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <button
          onClick={handleToggleCreate}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          {t("newPipeline")}
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
                {t("pipelineName")}
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
                placeholder={t("pipelineNamePlaceholder")}
              />
              {nameError && (
                <p className="mt-1 text-sm text-red-600">{nameError}</p>
              )}
            </div>
            <div>
              <label htmlFor="pl-book" className="block text-sm font-medium mb-1">
                {t("book")}
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
                    <option value="">{t("selectBook")}</option>
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
                    {t("enterBookIdManually")}
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
                    placeholder={t("bookIdPlaceholder")}
                  />
                  {booksLoading && (
                    <p className="mt-1 text-xs text-muted-foreground">{t("loadingBooks")}</p>
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
                      {t("selectFromBooks")}
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
              {t("cancel")}
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !isFormValid}
              className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending ? t("creating") : t("create")}
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
          {t("failedToLoad")}
        </p>
      )}
      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-muted-foreground">
            {t("noPipelines")}
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
                {t("previous")}
              </button>
              <span className="text-sm text-muted-foreground">
                {t("page", { page: data.page, pages: data.pages })}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
                className="px-3 py-1 text-sm border rounded-md disabled:opacity-50"
              >
                {t("next")}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
