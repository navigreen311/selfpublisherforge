"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { BlurbEditor } from "@/modules/product-page/components/BlurbEditor";
import { ABTestPanel } from "@/modules/product-page/components/ABTestPanel";
import { useProjects } from "@/modules/projects/hooks";
import { useTranslations } from "@/hooks/use-translations";

function BlurbOptimizationContent() {
  const searchParams = useSearchParams();
  const bookIdFromUrl = searchParams.get("bookId");
  const t = useTranslations("product-page");

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
    { key: "editor" as const, label: t("blurb.editorTab") },
    { key: "ab-test" as const, label: t("blurb.abTestTab") },
  ];

  // Loading state while fetching projects
  if (isLoadingProjects) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t("blurb.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("blurb.loading")}</p>
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
          <h1 className="text-2xl font-bold">{t("blurb.title")}</h1>
          <p className="text-muted-foreground mt-1">
            {t("blurb.subtitle")}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-8 shadow-sm text-center">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            {t("blurb.noBooksTitle")}
          </h3>
          <p className="text-muted-foreground text-sm">
            {t("blurb.noBooksMessage")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("blurb.title")}</h1>
        <p className="text-muted-foreground mt-1">
          {t("blurb.subtitle")}
        </p>
      </div>

      {/* Book selector (shown when no bookId in URL) */}
      {!bookIdFromUrl && allBooks.length > 0 && (
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <label className="block text-sm font-medium text-foreground mb-1">
            {t("blurb.selectBook")}
          </label>
          <select
            value={selectedBookId ?? ""}
            onChange={(e) => setSelectedBookId(e.target.value || undefined)}
            className="w-full max-w-md rounded-md border px-3 py-2 text-sm"
          >
            <option value="">{t("blurb.chooseBook")}</option>
            {allBooks.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title} ({book.projectTitle})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Tab navigation */}
      <div className="border-b border">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "pb-2 text-sm font-medium border-b-2 -mb-px",
                activeTab === tab.key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-muted-foreground hover:text-foreground"
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

function BlurbFallback() {
  const t = useTranslations("product-page");
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("blurb.title")}</h1>
        <p className="text-muted-foreground mt-1">{t("blurb.loading")}</p>
      </div>
    </div>
  );
}

export default function BlurbOptimizationPage() {
  return (
    <React.Suspense fallback={<BlurbFallback />}>
      <BlurbOptimizationContent />
    </React.Suspense>
  );
}
