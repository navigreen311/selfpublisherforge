"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
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

function formatRelativeDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
  return date.toLocaleDateString();
}

function formatSessionDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

// ---------------------------------------------------------------------------
// StatusBadge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
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
      {status.charAt(0).toUpperCase() + status.slice(1)}
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

function SessionsTableSkeleton() {
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/30">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Book
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Words Written
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Duration
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Date
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

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <p className="font-medium">Something went wrong</p>
      <p className="mt-1 text-red-600">{message}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyBooksState() {
  return (
    <div className="text-center py-12 rounded-lg border border-dashed bg-card">
      <h3 className="font-medium text-foreground">No manuscripts yet</h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
        Start your first book to begin writing. You can create a new manuscript
        from scratch or use the AI Outline Generator.
      </p>
      <Link
        href="/writing/new"
        className="inline-block mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        Start your first book
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
    return <ErrorBanner message={error.message} />;
  }

  if (isLoading) {
    return <SessionsTableSkeleton />;
  }

  if (!sessions || sessions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No writing sessions recorded yet. Open a manuscript and start writing!
      </p>
    );
  }

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/30">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Book
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Words Written
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Duration
            </th>
            <th className="text-left px-4 py-2 font-medium text-muted-foreground">
              Date
            </th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr key={session.id} className="border-t">
              <td className="px-4 py-2">
                {session.book_title ||
                  bookTitleMap[session.book_id] ||
                  "Unknown Book"}
              </td>
              <td className="px-4 py-2">
                {session.words_written.toLocaleString()}
              </td>
              <td className="px-4 py-2">{session.duration_minutes} min</td>
              <td className="px-4 py-2 text-muted-foreground">
                {formatSessionDate(session.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function WritingStudioPage() {
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
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Writing Studio</h1>
        <p className="text-muted-foreground mt-1">
          Write, edit, and polish your manuscripts with AI-powered assistance.
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          href="/writing/new"
          className="rounded-lg border bg-card p-4 hover:border-primary/50 transition-colors"
        >
          <h3 className="font-medium text-sm">New Manuscript</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Start a new book from scratch or with an AI-generated outline.
          </p>
        </Link>
        <Link href="/writing/outline" className="rounded-lg border bg-card p-4 hover:border-primary/50 transition-colors">
          <h3 className="font-medium text-sm">AI Outline Generator</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Generate a complete book outline with chapter summaries.
          </p>
        </Link>
        <div className="rounded-lg border bg-card p-4 hover:border-primary/50 transition-colors">
          <h3 className="font-medium text-sm">Writing Analytics</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Track your writing sessions, word counts, and productivity.
          </p>
        </div>
      </div>

      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Search manuscripts..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-md rounded-md border px-3 py-2 text-sm bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      {/* Book list */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-3">
          Your Manuscripts
        </h2>

        {/* Error state */}
        {booksError && (
          <ErrorBanner
            message={
              booksError instanceof Error
                ? booksError.message
                : "Failed to load manuscripts."
            }
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
          <EmptyBooksState />
        )}

        {/* Loaded with results */}
        {!booksLoading && !booksError && books && books.length > 0 && (
          <>
            <div className="space-y-3">
              {filteredBooks.map((book) => (
                <Link
                  key={book.id}
                  href={`/writing/${book.id}`}
                  className="block rounded-lg border bg-card p-4 hover:border-primary/50 hover:shadow-sm transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-foreground">
                        {book.title}
                      </h3>
                      <div className="flex items-center gap-3 mt-1">
                        <StatusBadge status={book.status} />
                        {book.chapter_count !== undefined && (
                          <span className="text-xs text-muted-foreground">
                            {book.chapter_count} chapters
                          </span>
                        )}
                        {book.word_count !== undefined && (
                          <span className="text-xs text-muted-foreground">
                            {book.word_count.toLocaleString()} words
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeDate(book.updated_at)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>

            {filteredBooks.length === 0 && searchQuery && (
              <p className="text-sm text-muted-foreground text-center py-8">
                No manuscripts found matching &quot;{searchQuery}&quot;.
              </p>
            )}
          </>
        )}
      </div>

      {/* Recent sessions */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-3">
          Recent Writing Sessions
        </h2>
        <WritingSessionsSection
          sessions={sessions}
          isLoading={sessionsLoading}
          error={sessionsError as Error | null}
          books={books}
        />
      </div>
    </div>
  );
}
