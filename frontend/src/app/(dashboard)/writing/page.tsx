import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";

export const metadata: Metadata = createMetadata({
  title: "Writing Studio",
  description: "Manage your manuscripts, track writing sessions, and organize your books with AI-powered writing tools.",
  noindex: true,
});

"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { useBooks, useWritingSessions } from "@/modules/writing/hooks";
import type { BookEntry, WritingSessionEntry } from "@/modules/writing/hooks";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Writing Studio landing page.
 *
 * Displays project selector, book list, and recent writing sessions.
 * Users select a book to enter the manuscript editor.
 * Data is fetched from the API via React Query hooks.
 */

// ---------------------------------------------------------------------------
// Helper: format a date string into a human-friendly relative label
// ---------------------------------------------------------------------------

function formatRelativeDate(dateStr: string | undefined, t: (key: string, vars?: Record<string, string | number>) => string): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return t("timeAgo.justNow");
  if (diffMins < 60) return t("timeAgo.minutesAgo", { count: diffMins });
  if (diffHours < 24) return diffHours === 1 ? t("timeAgo.hoursAgo", { count: diffHours }) : t("timeAgo.hoursAgoPlural", { count: diffHours });
  if (diffDays < 7) return diffDays === 1 ? t("timeAgo.daysAgo", { count: diffDays }) : t("timeAgo.daysAgoPlural", { count: diffDays });
  return date.toLocaleDateString();
}

function formatSessionDate(dateStr: string, t: (key: string, vars?: Record<string, string | number>) => string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays === 0) return t("timeAgo.today");
  if (diffDays === 1) return t("timeAgo.yesterday");
  if (diffDays < 7) return t("timeAgo.daysAgoPlural", { count: diffDays });
  return date.toLocaleDateString();
}

// ---------------------------------------------------------------------------
// StatusBadge
// ---------------------------------------------------------------------------

function StatusBadge({ status, t }: { status: string; t: (key: string) => string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    writing: "bg-blue-100 text-blue-700",
    editing: "bg-yellow-100 text-yellow-700",
    formatting: "bg-purple-100 text-purple-700",
    published: "bg-green-100 text-green-700",
    archived: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${
        colors[status] || colors.draft
      }`}
    >
      {t(`status.${status}`)}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Skeleton loaders
// ---------------------------------------------------------------------------

function BookCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-3 w-20" />
      </div>
    </div>
  );
}

  const t = useTranslations("writing");
function SessionsTableSkeleton({ t }: { t: (key: string) => string }) {
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/30">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              {t("sessions.table.book")}
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              {t("sessions.table.wordsWritten")}
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              {t("sessions.table.duration")}
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              {t("sessions.table.date")}
            </th>
          </tr>
        </thead>
        <tbody>
          {[1, 2, 3].map((i) => (
            <tr key={i} className="border-t">
              <td className="px-4 py-2">
                <Skeleton className="h-4 w-36" />
              </td>
              <td className="px-4 py-2">
                <Skeleton className="h-4 w-16" />
              </td>
              <td className="px-4 py-2">
                <Skeleton className="h-4 w-16" />
              </td>
              <td className="px-4 py-2">
                <Skeleton className="h-4 w-20" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error display
// ---------------------------------------------------------------------------

  const t = useTranslations("writing");
function ErrorBanner({ message, t }: { message: string; t: (key: string) => string }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <p className="font-medium">{t("error.title")}</p>
      <p className="mt-1 text-red-600">{message}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyBooksState({ t }: { t: (key: string) => string }) {
  const t = useTranslations("writing");

  return (
    <div className="text-center py-12 rounded-lg border border-dashed bg-card">
      <h3 className="font-medium text-foreground">{t("manuscripts.empty.title")}</h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
        {t("manuscripts.empty.description")}
      </p>
      <Link
        href="/writing/new"
        className="inline-block mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        {t("manuscripts.empty.action")}
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sessions section
// ---------------------------------------------------------------------------

function WritingSessionsSection({
  sessions,
  isLoading,
  error,
  books,
}: {
  sessions: WritingSessionEntry[] | undefined;
  isLoading: boolean;
  error: Error | null;
  books: BookEntry[] | undefined;
}) {
  // Build a book title lookup map
  const bookTitleMap = useMemo(() => {
    const map: Record<string, string> = {};
    if (books) {
      for (const b of books) {
        map[b.id] = b.title;
      }
    }
    return map;
  }, [books]);

  if (error) {
    return <ErrorBanner message={error.message} t={t} />;
  }

  if (isLoading) {
    return <SessionsTableSkeleton t={t} />;
  }

  if (!sessions || sessions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        {t("sessions.empty")}
      </p>
    );
  }

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs sm:text-sm min-w-[600px]">
          <thead className="bg-muted/30">
            <tr>
              <th className="text-left px-2 sm:px-4 py-2 font-medium text-muted-foreground">
                {t("sessions.table.book")}
              </th>
              <th className="text-left px-2 sm:px-4 py-2 font-medium text-muted-foreground">
                {t("sessions.table.wordsWritten")}
              </th>
              <th className="text-left px-2 sm:px-4 py-2 font-medium text-muted-foreground">
                {t("sessions.table.duration")}
              </th>
              <th className="text-left px-2 sm:px-4 py-2 font-medium text-muted-foreground">
                {t("sessions.table.date")}
              </th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr key={session.id} className="border-t">
                <td className="px-2 sm:px-4 py-2">
                  {session.book_title ||
                    bookTitleMap[session.book_id] ||
                    t("stats.unknownBook")}
                </td>
                <td className="px-2 sm:px-4 py-2">
                  {session.words_written.toLocaleString()}
                </td>
                <td className="px-2 sm:px-4 py-2">{session.duration_minutes} {t("sessions.minutes")}</td>
                <td className="px-2 sm:px-4 py-2 text-muted-foreground">
                  {formatSessionDate(session.created_at, t)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function WritingStudioPage() {
  const t = useTranslations("writing");
  const [searchQuery, setSearchQuery] = useState("");

  const {
    data: books,
    isLoading: booksLoading,
    error: booksError,
  } = useBooks();

  const {
    data: sessions,
    isLoading: sessionsLoading,
    error: sessionsError,
  } = useWritingSessions();

  const filteredBooks = useMemo(() => {
    if (!books) return [];
    if (!searchQuery) return books;
    return books.filter((book) =>
      book.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [books, searchQuery]);

  return (
    <div className="max-w-5xl mx-auto space-y-6 sm:space-y-8 px-4 sm:px-6 lg:px-0">
      {/* Page header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-foreground">{t("title")}</h1>
        <p className="text-sm sm:text-base text-muted-foreground mt-1">
          {t("subtitle")}
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <Link
          href="/writing/new"
          className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 transition-colors"
        >
          <h3 className="font-medium text-xs sm:text-sm">{t("quickActions.newManuscript.title")}</h3>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {t("quickActions.newManuscript.description")}
          </p>
        </Link>
        <Link href="/writing/outline" className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 transition-colors">
          <h3 className="font-medium text-xs sm:text-sm">{t("quickActions.aiOutline.title")}</h3>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {t("quickActions.aiOutline.description")}
          </p>
        </Link>
        <div className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 transition-colors">
          <h3 className="font-medium text-xs sm:text-sm">{t("quickActions.analytics.title")}</h3>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {t("quickActions.analytics.description")}
          </p>
        </div>
      </div>

      {/* Search */}
      <div role="search">
        <input
          type="text"
          placeholder={t("search.placeholder")}
          aria-label={t("search.placeholder")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-md rounded-md border px-3 py-2 text-sm bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      {/* Book list */}
      <div>
        <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3">
          {t("manuscripts.title")}
        </h2>

        {/* Error state */}
        {booksError && (
          <ErrorBanner
            message={
              booksError instanceof Error
                ? booksError.message
                : "Failed to load manuscripts."
            }
            t={t}
          />
        )}

        {/* Loading state */}
        {booksLoading && (
          <div className="space-y-3">
            <BookCardSkeleton />
            <BookCardSkeleton />
            <BookCardSkeleton />
          </div>
        )}

        {/* Empty state -- no books at all */}
        {!booksLoading && !booksError && books && books.length === 0 && (
          <EmptyBooksState t={t} />
        )}

        {/* Loaded with results */}
        {!booksLoading && !booksError && books && books.length > 0 && (
          <>
            <div className="space-y-2 sm:space-y-3">
              {filteredBooks.map((book) => (
                <Link
                  key={book.id}
                  href={`/writing/${book.id}`}
                  className="block rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 hover:shadow-sm transition-all"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium text-sm sm:text-base text-foreground truncate">
                        {book.title}
                      </h3>
                      <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-1">
                        <StatusBadge status={book.status} t={t} />
                        {book.chapter_count !== undefined && (
                          <span className="text-[10px] sm:text-xs text-muted-foreground">
                            {book.chapter_count} {t("stats.chapters")}
                          </span>
                        )}
                        {book.word_count !== undefined && (
                          <span className="text-[10px] sm:text-xs text-muted-foreground">
                            {book.word_count.toLocaleString()} {t("stats.words")}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] sm:text-xs text-muted-foreground flex-shrink-0">
                      {formatRelativeDate(book.updated_at, t)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>

            {filteredBooks.length === 0 && searchQuery && (
              <p className="text-sm text-muted-foreground text-center py-8">
                {t("search.noResults", { query: searchQuery })}
              </p>
            )}
          </>
        )}
      </div>

      {/* Recent sessions */}
      <div>
        <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3">
          {t("sessions.title")}
        </h2>
        <div className="overflow-x-auto -mx-4 sm:mx-0">
          <WritingSessionsSection
            sessions={sessions}
            isLoading={sessionsLoading}
            error={sessionsError as Error | null}
            books={books}
            t={t}
          />
        </div>
      </div>
    </div>
  );
}
