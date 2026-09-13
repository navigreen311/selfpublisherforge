"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";
import { ExportWizard } from "@/modules/publishing/components/ExportWizard";
import { useBooks, useChapters } from "@/modules/writing/hooks";
import { Skeleton } from "@/components/ui/skeleton";

export default function ExportPage() {
  const t = useTranslations("publishing");
  const [selectedBookId, setSelectedBookId] = useState<string>("");

  const {
    data: books,
    isLoading: booksLoading,
    error: booksError,
  } = useBooks();

  const {
    data: chapters,
    isLoading: chaptersLoading,
    error: chaptersError,
  } = useChapters(selectedBookId);

  // Map ChapterContent[] to the shape ExportWizard expects
  const exportChapters = (chapters ?? []).map((ch) => ({
    title: ch.title,
    content: ch.content,
    order: ch.order,
  }));

  const selectedBook = books?.find((b) => b.id === selectedBookId);

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav
        aria-label="Breadcrumb"
        className="flex items-center space-x-2 text-sm text-muted-foreground"
      >
        <Link href="/publishing" className="hover:text-foreground">
          {t("export.breadcrumb.publishing")}
        </Link>
        <span>/</span>
        <span className="text-foreground">{t("export.breadcrumb.export")}</span>
      </nav>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">{t("export.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("export.subtitle")}
        </p>
      </div>

      {/* Book Selector */}
      <div>
        <label
          htmlFor="book-selector"
          className="block text-sm font-medium text-foreground mb-1"
        >
          {t("export.selectBook")}
        </label>

        {booksLoading && (
          <Skeleton className="h-10 w-full max-w-md rounded-md" />
        )}

        {booksError && (
          <div
            role="alert"
            className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
          >
            <p className="font-medium">{t("export.error.failedToLoad")}</p>
            <p className="mt-1 text-red-600">
              {booksError instanceof Error
                ? booksError.message
                : t("export.error.unexpectedError")}
            </p>
          </div>
        )}

        {!booksLoading && !booksError && books && books.length === 0 && (
          <div
            className="rounded-lg border border-dashed border bg-muted p-8 text-center"
            role="status"
          >
            <h3 className="font-medium text-foreground">{t("export.empty.noBooksTitle")}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("export.empty.noBooksDescription")}
            </p>
            <Link
              href="/writing/new"
              className="mt-4 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              {t("export.empty.noBooksAction")}
            </Link>
          </div>
        )}

        {!booksLoading && !booksError && books && books.length > 0 && (
          <select
            id="book-selector"
            aria-label={t("export.selectBook")}
            value={selectedBookId}
            onChange={(e) => setSelectedBookId(e.target.value)}
            className="w-full max-w-md rounded-md border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">{t("export.bookSelector.choose")}</option>
            {books.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Chapters loading state */}
      {selectedBookId && chaptersLoading && (
        <div
          className="rounded-lg border bg-card p-6 shadow-sm"
          role="status"
          aria-label={t("export.chaptersLoading")}
        >
          <div className="space-y-4">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-full max-w-lg" />
            <Skeleton className="h-4 w-full max-w-sm" />
          </div>
        </div>
      )}

      {/* Chapters error state */}
      {selectedBookId && chaptersError && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          <p className="font-medium">{t("export.error.failedToLoadChapters")}</p>
          <p className="mt-1 text-red-600">
            {chaptersError instanceof Error
              ? chaptersError.message
              : t("export.error.unexpectedError")}
          </p>
        </div>
      )}

      {/* Empty chapters state */}
      {selectedBookId &&
        !chaptersLoading &&
        !chaptersError &&
        chapters &&
        chapters.length === 0 && (
          <div
            className="rounded-lg border border-dashed border bg-muted p-8 text-center"
            role="status"
          >
            <h3 className="font-medium text-foreground">{t("export.empty.noChaptersTitle")}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("export.empty.noChaptersDescription")}
            </p>
            <Link
              href={`/writing/${selectedBookId}`}
              className="mt-4 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              {t("export.empty.noChaptersAction")}
            </Link>
          </div>
        )}

      {/* Export Wizard -- only shown when a book is selected and chapters are loaded */}
      {selectedBookId &&
        !chaptersLoading &&
        !chaptersError &&
        chapters &&
        chapters.length > 0 && (
          <div className="rounded-lg border bg-card p-6 shadow-sm">
            <p className="mb-4 text-sm text-muted-foreground">
              {exportChapters.length === 1
                ? t("export.exporting", { title: selectedBook?.title, count: exportChapters.length })
                : t("export.exportingPlural", { title: selectedBook?.title, count: exportChapters.length })}
            </p>
            <ExportWizard bookId={selectedBookId} chapters={exportChapters} />
          </div>
        )}
    </div>
  );
}
