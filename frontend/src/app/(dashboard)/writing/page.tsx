"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { formatDistanceToNow, differenceInDays, format } from "date-fns";
import { useTranslations } from "@/hooks/use-translations";
import { useBooks, useWritingSessions } from "@/modules/writing/hooks";
import type { BookEntry, WritingSessionEntry } from "@/modules/writing/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { WritingAnalytics } from "@/components/writing-studio/WritingAnalytics";
import { NewManuscriptModal } from "@/components/writing-studio/NewManuscriptModal";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";

/**
 * Writing Studio landing page.
 *
 * Displays quick-action cards, a searchable/sortable manuscript list with
 * progress bars, status badges, and row-level action menus, plus a recent
 * writing sessions table and an analytics dialog.
 */

// ---------------------------------------------------------------------------
// Sort options
// ---------------------------------------------------------------------------

type SortOption = "recent" | "title" | "progress";

// ---------------------------------------------------------------------------
// Helper: format a date string into a human-friendly relative label
// ---------------------------------------------------------------------------

function formatRelativeDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const daysDiff = differenceInDays(new Date(), date);
  if (daysDiff >= 7) return format(date, "MMM d, yyyy");
  return formatDistanceToNow(date, { addSuffix: true });
}

function formatSessionDate(dateStr: string): string {
  const date = new Date(dateStr);
  const daysDiff = differenceInDays(new Date(), date);
  if (daysDiff === 0) return "Today";
  if (daysDiff === 1) return "Yesterday";
  if (daysDiff < 7) return `${daysDiff} days ago`;
  return format(date, "MMM d, yyyy");
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

function BookRowSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-5 rounded" />
            <Skeleton className="h-5 w-48" />
          </div>
          <div className="flex items-center gap-3">
            <Skeleton className="h-4 w-16 rounded-full" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-2 w-full max-w-xs rounded-full" />
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Skeleton className="h-8 w-24 rounded-md" />
          <Skeleton className="h-8 w-8 rounded-md" />
        </div>
      </div>
    </div>
  );
}

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
              {t("sessions.table.chapter")}
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
                <Skeleton className="h-4 w-24" />
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
  return (
    <div className="text-center py-12 rounded-lg border border-dashed bg-card">
      <div className="text-4xl mb-3">&#128214;</div>
      <h3 className="font-medium text-foreground">{t("manuscripts.empty.title")}</h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
        {t("manuscripts.empty.description")}
      </p>
      <div className="flex items-center justify-center gap-3 mt-5">
        <Link
          href="/writing/new"
          className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {t("manuscripts.empty.action")}
        </Link>
        <Link
          href="/writing/outline"
          className="inline-block rounded-md border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
        >
          {t("manuscripts.empty.generateOutline")}
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Manuscript row action menu
// ---------------------------------------------------------------------------

function ManuscriptActionMenu({ book, t }: { book: BookEntry; t: (key: string) => string }) {
  const handleAction = (action: string) => {
    // Placeholder actions -- show alert for now
    switch (action) {
      case "rename":
        alert(`${t("manuscripts.menu.rename")}: ${book.title}`);
        break;
      case "duplicate":
        alert(`${t("manuscripts.menu.duplicate")}: ${book.title}`);
        break;
      case "export-docx":
        alert(`${t("manuscripts.menu.exportDocx")}: ${book.title}`);
        break;
      case "export-epub":
        alert(`${t("manuscripts.menu.exportEpub")}: ${book.title}`);
        break;
      case "export-pdf":
        alert(`${t("manuscripts.menu.exportPdf")}: ${book.title}`);
        break;
      case "export-txt":
        alert(`${t("manuscripts.menu.exportTxt")}: ${book.title}`);
        break;
      case "export-md":
        alert(`${t("manuscripts.menu.exportMarkdown")}: ${book.title}`);
        break;
      case "analytics":
        alert(`${t("manuscripts.menu.viewAnalytics")}: ${book.title}`);
        break;
      case "move-to-project":
        alert(`${t("manuscripts.menu.moveToProject")}: ${book.title}`);
        break;
      case "archive":
        alert(`${t("manuscripts.menu.archive")}: ${book.title}`);
        break;
      case "delete":
        alert(`${t("manuscripts.menu.delete")}: ${book.title}`);
        break;
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="h-8 w-8 flex items-center justify-center rounded-md border text-muted-foreground hover:bg-muted transition-colors"
          aria-label={t("manuscripts.menu.rename")}
        >
          &#8230;
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onSelect={() => handleAction("rename")}>
          {t("manuscripts.menu.rename")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleAction("duplicate")}>
          {t("manuscripts.menu.duplicate")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => handleAction("analytics")}>
          {t("manuscripts.menu.viewAnalytics")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleAction("move-to-project")}>
          {t("manuscripts.menu.moveToProject")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          {t("editor.export")}
        </DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => handleAction("export-docx")}>
          {t("manuscripts.menu.exportDocx")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleAction("export-epub")}>
          {t("manuscripts.menu.exportEpub")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleAction("export-pdf")}>
          {t("manuscripts.menu.exportPdf")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleAction("export-txt")}>
          {t("manuscripts.menu.exportTxt")}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleAction("export-md")}>
          {t("manuscripts.menu.exportMarkdown")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => handleAction("archive")}>
          {t("manuscripts.menu.archive")}
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-600 focus:text-red-600"
          onSelect={() => handleAction("delete")}
        >
          {t("manuscripts.menu.delete")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// ---------------------------------------------------------------------------
// Progress bar for manuscript
// ---------------------------------------------------------------------------

function ManuscriptProgress({ book, t }: { book: BookEntry; t: (key: string) => string }) {
  const wordCount = book.word_count ?? 0;
  const target = book.target_word_count;

  if (!target) {
    return (
      <span className="text-[10px] sm:text-xs text-muted-foreground">
        {wordCount.toLocaleString()} {t("stats.words")}
      </span>
    );
  }

  const pct = Math.min(Math.round((wordCount / target) * 100), 100);

  return (
    <div className="flex items-center gap-2 w-full max-w-xs">
      <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] sm:text-xs text-muted-foreground flex-shrink-0">
        {pct}%
      </span>
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
  t,
}: {
  sessions: WritingSessionEntry[] | undefined;
  isLoading: boolean;
  error: Error | null;
  books: BookEntry[] | undefined;
  t: (key: string, vars?: Record<string, string | number>) => string;
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
                {t("sessions.table.chapter")}
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
                <td className="px-2 sm:px-4 py-2 text-muted-foreground">
                  {session.chapter_title || "\u2014"}
                </td>
                <td className="px-2 sm:px-4 py-2">
                  {session.words_written.toLocaleString()}
                </td>
                <td className="px-2 sm:px-4 py-2">{session.duration_minutes} {t("sessions.minutes")}</td>
                <td className="px-2 sm:px-4 py-2 text-muted-foreground">
                  {formatSessionDate(session.created_at)}
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
  const [sortBy, setSortBy] = useState<SortOption>("recent");
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [newManuscriptOpen, setNewManuscriptOpen] = useState(false);

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

  // Filter and sort manuscripts
  const filteredBooks = useMemo(() => {
    if (!books) return [];

    let result = [...books];

    // Filter by search
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter((book) =>
        book.title.toLowerCase().includes(q)
      );
    }

    // Filter by status
    if (statusFilter !== "all") {
      if (statusFilter === "complete") {
        result = result.filter(b => b.status === "published" || b.status === "formatting");
      } else {
        result = result.filter(b => b.status === statusFilter);
      }
    }

    // Sort
    switch (sortBy) {
      case "recent":
        result.sort((a, b) => {
          const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
          const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
          return dateB - dateA;
        });
        break;
      case "title":
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "progress":
        result.sort((a, b) => {
          const pctA = a.target_word_count ? (a.word_count ?? 0) / a.target_word_count : 0;
          const pctB = b.target_word_count ? (b.word_count ?? 0) / b.target_word_count : 0;
          return pctB - pctA;
        });
        break;
    }

    return result;
  }, [books, searchQuery, sortBy, statusFilter]);

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
        <button
          type="button"
          onClick={() => setNewManuscriptOpen(true)}
          className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 transition-colors text-left w-full"
        >
          <h3 className="font-medium text-xs sm:text-sm">{t("quickActions.newManuscript.title")}</h3>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {t("quickActions.newManuscript.description")}
          </p>
        </button>
        <Link
          href="/writing/outline"
          className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 transition-colors"
        >
          <h3 className="font-medium text-xs sm:text-sm">{t("quickActions.aiOutline.title")}</h3>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {t("quickActions.aiOutline.description")}
          </p>
        </Link>
        <button
          type="button"
          onClick={() => setAnalyticsOpen(true)}
          className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 transition-colors text-left"
        >
          <h3 className="font-medium text-xs sm:text-sm">{t("quickActions.analytics.title")}</h3>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {t("quickActions.analytics.description")}
          </p>
        </button>
      </div>

      {/* Analytics dialog */}
      <Dialog open={analyticsOpen} onOpenChange={setAnalyticsOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t("quickActions.analytics.title")}</DialogTitle>
            <DialogDescription>
              {t("quickActions.analytics.description")}
            </DialogDescription>
          </DialogHeader>
          <WritingAnalytics />
        </DialogContent>
      </Dialog>

      {/* Search + Sort */}
      <div role="search" className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <input
          type="text"
          placeholder={t("search.placeholder")}
          aria-label={t("search.placeholder")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full sm:max-w-md rounded-md border px-3 py-2 text-sm bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortOption)}
          aria-label={t("sort.label")}
          className="rounded-md border px-3 py-2 text-sm bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="recent">{t("sort.recent")}</option>
          <option value="title">{t("sort.title")}</option>
          <option value="progress">{t("sort.progress")}</option>
        </select>
      </div>

      {/* Status filter pills */}
      {books && books.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {["all", "writing", "draft", "editing", "complete"].map((status) => {
            const count = status === "all"
              ? books.length
              : books.filter(b => {
                  if (status === "complete") return b.status === "published" || b.status === "formatting";
                  return b.status === status;
                }).length;
            return (
              <button
                key={status}
                type="button"
                onClick={() => setStatusFilter(status)}
                className={cn(
                  "px-3 py-1 text-xs font-medium rounded-full border transition-colors",
                  statusFilter === status
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-card text-muted-foreground border-border hover:bg-accent"
                )}
              >
                {t(`manuscripts.statusFilter.${status}`)} ({count})
              </button>
            );
          })}
        </div>
      )}

      {/* Manuscript list */}
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
            <BookRowSkeleton />
            <BookRowSkeleton />
            <BookRowSkeleton />
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
                <div
                  key={book.id}
                  className="rounded-lg border bg-card p-3 sm:p-4 hover:border-primary/50 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start sm:items-center justify-between gap-3">
                    {/* Left side: info */}
                    <div className="min-w-0 flex-1 space-y-1.5">
                      {/* Title row */}
                      <div className="flex items-center gap-2">
                        <span className="text-base flex-shrink-0" aria-hidden="true">
                          &#128214;
                        </span>
                        <h3 className="font-medium text-sm sm:text-base text-foreground truncate">
                          {book.title}
                        </h3>
                      </div>

                      {/* Meta row */}
                      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
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
                        <span className="text-[10px] sm:text-xs text-muted-foreground">
                          {formatRelativeDate(book.updated_at)}
                        </span>
                      </div>

                      {/* Progress bar */}
                      <ManuscriptProgress book={book} t={t} />
                    </div>

                    {/* Right side: actions */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Link
                        href={`/writing/${book.id}`}
                        className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs sm:text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                      >
                        {t("manuscripts.openEditor")}
                      </Link>
                      <ManuscriptActionMenu book={book} t={t} />
                    </div>
                  </div>
                </div>
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

      {/* Recent writing sessions */}
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
        <div className="mt-2 text-right">
          <button
            type="button"
            onClick={() => setAnalyticsOpen(true)}
            className="text-sm text-primary hover:text-primary/80 font-medium transition-colors"
          >
            {t("sessions.viewAll")}
          </button>
        </div>
      </div>

      {/* New manuscript modal */}
      <NewManuscriptModal open={newManuscriptOpen} onOpenChange={setNewManuscriptOpen} />
    </div>
  );
}
