"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { BlurbEditor } from "@/modules/product-page/components/BlurbEditor";
import { ABTestPanel } from "@/modules/product-page/components/ABTestPanel";
import { useProjects } from "@/modules/projects/hooks";

function BlurbOptimizationContent() {
  const searchParams = useSearchParams();
  const bookIdFromUrl = searchParams.get("bookId");

  const { data: projects, isLoading: isLoadingProjects } = useProjects();

  const [selectedBookId, setSelectedBookId] = useState<string | undefined>(
    undefined
  );
  const [activeTab, setActiveTab] = useState<"editor" | "ab-test">("editor");

  // Derive the effective bookId: URL param takes priority, then user selection
  const bookId = bookIdFromUrl || selectedBookId;

  // Collect all books across all projects
  const allBooks =
    projects?.flatMap((project) =>
      (project.books ?? []).map((book) => ({
        ...book,
        projectTitle: project.title,
      }))
    ) ?? [];

  const tabs = [
    { key: "editor" as const, label: "Blurb Editor" },
    { key: "ab-test" as const, label: "A/B Testing" },
  ];

  // Loading state while fetching projects
  if (isLoadingProjects) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Blurb Optimization</h1>
          <p className="text-gray-500 mt-1">Loading your books...</p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      </div>
    );
  }

  // No books exist yet
  if (!isLoadingProjects && allBooks.length === 0 && !bookIdFromUrl) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Blurb Optimization</h1>
          <p className="text-gray-500 mt-1">
            Generate, test, and optimize your book blurb for maximum conversion.
          </p>
        </div>
        <div className="rounded-lg border bg-white p-8 shadow-sm text-center">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            No books found
          </h3>
          <p className="text-gray-500 text-sm">
            Create a project first to start optimizing your blurbs.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Blurb Optimization</h1>
        <p className="text-gray-500 mt-1">
          Generate, test, and optimize your book blurb for maximum conversion.
        </p>
      </div>

      {/* Book selector (shown when no bookId in URL) */}
      {!bookIdFromUrl && allBooks.length > 0 && (
        <div className="rounded-lg border bg-white p-4 shadow-sm">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select a Book
          </label>
          <select
            value={selectedBookId ?? ""}
            onChange={(e) => setSelectedBookId(e.target.value || undefined)}
            className="w-full max-w-md rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">-- Choose a book --</option>
            {allBooks.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title} ({book.projectTitle})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Tab navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "pb-2 text-sm font-medium border-b-2 -mb-px",
                activeTab === tab.key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Blurb editor tab */}
      {activeTab === "editor" && <BlurbEditor />}

      {/* A/B testing tab */}
      {activeTab === "ab-test" && <ABTestPanel bookId={bookId ?? undefined} />}
    </div>
  );
}

export default function BlurbOptimizationPage() {
  return (
    <React.Suspense
      fallback={
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold">Blurb Optimization</h1>
            <p className="text-gray-500 mt-1">Loading...</p>
          </div>
        </div>
      }
    >
      <BlurbOptimizationContent />
    </React.Suspense>
  );
}
