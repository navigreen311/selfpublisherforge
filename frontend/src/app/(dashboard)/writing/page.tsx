"use client";

import Link from "next/link";
import { useState } from "react";

/**
 * Writing Studio landing page.
 *
 * Displays project selector, book list, and recent writing sessions.
 * Users select a book to enter the manuscript editor.
 */

interface BookEntry {
  id: string;
  title: string;
  status: string;
  chapterCount: number;
  wordCount: number;
  lastEdited: string;
}

// Placeholder data -- in production this comes from the API
const SAMPLE_BOOKS: BookEntry[] = [
  {
    id: "book-1",
    title: "The Forgotten Kingdom",
    status: "writing",
    chapterCount: 12,
    wordCount: 34500,
    lastEdited: "2 hours ago",
  },
  {
    id: "book-2",
    title: "Digital Horizons",
    status: "draft",
    chapterCount: 3,
    wordCount: 8200,
    lastEdited: "1 day ago",
  },
  {
    id: "book-3",
    title: "Cooking with Fire",
    status: "editing",
    chapterCount: 20,
    wordCount: 62000,
    lastEdited: "3 days ago",
  },
];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    writing: "bg-blue-100 text-blue-700",
    editing: "bg-yellow-100 text-yellow-700",
    formatting: "bg-purple-100 text-purple-700",
    published: "bg-green-100 text-green-700",
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

export default function WritingStudioPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredBooks = SAMPLE_BOOKS.filter((book) =>
    book.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
        <div className="rounded-lg border bg-card p-4 hover:border-primary/50 transition-colors">
          <h3 className="font-medium text-sm">New Manuscript</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Start a new book from scratch or with an AI-generated outline.
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4 hover:border-primary/50 transition-colors">
          <h3 className="font-medium text-sm">AI Outline Generator</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Generate a complete book outline with chapter summaries.
          </p>
        </div>
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
        <div className="space-y-3">
          {filteredBooks.map((book) => (
            <Link
              key={book.id}
              href={`/writing/${book.id}`}
              className="block rounded-lg border bg-card p-4 hover:border-primary/50 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-foreground">{book.title}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <StatusBadge status={book.status} />
                    <span className="text-xs text-muted-foreground">
                      {book.chapterCount} chapters
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {book.wordCount.toLocaleString()} words
                    </span>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">
                  {book.lastEdited}
                </span>
              </div>
            </Link>
          ))}
        </div>

        {filteredBooks.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-8">
            No manuscripts found matching your search.
          </p>
        )}
      </div>

      {/* Recent sessions */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-3">
          Recent Writing Sessions
        </h2>
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
              <tr className="border-t">
                <td className="px-4 py-2">The Forgotten Kingdom</td>
                <td className="px-4 py-2">1,250</td>
                <td className="px-4 py-2">45 min</td>
                <td className="px-4 py-2 text-muted-foreground">Today</td>
              </tr>
              <tr className="border-t">
                <td className="px-4 py-2">Digital Horizons</td>
                <td className="px-4 py-2">800</td>
                <td className="px-4 py-2">30 min</td>
                <td className="px-4 py-2 text-muted-foreground">Yesterday</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
