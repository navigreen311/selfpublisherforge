"use client";

import { useState } from "react";
import {
  useKeywordResearch,
  useKeywordSuggestions,
} from "@/modules/market/hooks";
import { KeywordTable } from "@/modules/market/components";
import { useTranslations } from "@/hooks/use-translations";

export default function KeywordsPage() {
  const t = useTranslations("market");
  const [keywordInput, setKeywordInput] = useState("");
  const [genreInput, setGenreInput] = useState("");
  const [activeTab, setActiveTab] = useState<"research" | "suggestions">("research");

  const keywordResearch = useKeywordResearch();
  const { data: suggestions = [], isPending: suggestionsPending } =
    useKeywordSuggestions(activeTab === "suggestions" ? genreInput : "");

  const handleResearch = () => {
    if (!keywordInput.trim()) return;
    const keywords = keywordInput
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
    if (keywords.length > 0) {
      keywordResearch.mutate({ keywords });
    }
  };

  const handleSuggest = () => {
    if (!genreInput.trim()) return;
    setActiveTab("suggestions");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div role="region" aria-label="Page header">
        <h1 className="text-2xl font-bold">{t("keywordResearch")}</h1>
        <p className="text-muted-foreground mt-1">
          {t("keywordResearchSubtitle")}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b" role="tablist" aria-label="Keyword research tabs">
        <button
          onClick={() => setActiveTab("research")}
          role="tab"
          id="tab-research"
          aria-selected={activeTab === "research"}
          aria-controls="tabpanel-research"
          tabIndex={activeTab === "research" ? 0 : -1}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "research"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          {t("keywordResearchTab")}
        </button>
        <button
          onClick={() => setActiveTab("suggestions")}
          role="tab"
          id="tab-suggestions"
          aria-selected={activeTab === "suggestions"}
          aria-controls="tabpanel-suggestions"
          tabIndex={activeTab === "suggestions" ? 0 : -1}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "suggestions"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          {t("aiSuggestionsTab")}
        </button>
      </div>

      {/* Research tab */}
      {activeTab === "research" && (
        <div
          className="space-y-4"
          role="tabpanel"
          id="tabpanel-research"
          aria-labelledby="tab-research"
        >
          <div className="flex gap-3" role="region" aria-label="Keyword research input">
            <label htmlFor="keyword-input" className="sr-only">
              {t("keywordsToResearch")}
            </label>
            <input
              id="keyword-input"
              type="text"
              placeholder={t("keywordInputPlaceholder")}
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleResearch()}
              aria-label={t("keywordInputAriaLabel")}
              className="flex-1 px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={handleResearch}
              disabled={keywordResearch.isPending || !keywordInput.trim()}
              aria-label={keywordResearch.isPending ? t("researchInProgress") : t("researchKeywords")}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {keywordResearch.isPending ? t("researching") : t("research")}
            </button>
          </div>

          <div role="region" aria-label={t("keywordResearchResults")} aria-live="polite">
            <KeywordTable
              keywords={keywordResearch.data?.keywords ?? []}
              isLoading={keywordResearch.isPending}
            />
          </div>

          <div aria-live="polite" aria-atomic="true">
            {keywordResearch.isError && (
              <div role="alert" className="border border-red-200 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                {t("keywordResearchError")}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Suggestions tab */}
      {activeTab === "suggestions" && (
        <div
          className="space-y-4"
          role="tabpanel"
          id="tabpanel-suggestions"
          aria-labelledby="tab-suggestions"
        >
          <div className="flex gap-3" role="region" aria-label="Genre suggestion input">
            <label htmlFor="genre-input" className="sr-only">
              {t("genreForSuggestions")}
            </label>
            <input
              id="genre-input"
              type="text"
              placeholder={t("genreInputPlaceholder")}
              value={genreInput}
              onChange={(e) => setGenreInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSuggest()}
              aria-label={t("genreInputAriaLabel")}
              className="flex-1 px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={handleSuggest}
              disabled={!genreInput.trim()}
              aria-label={t("genreInputAriaLabel")}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t("getSuggestions")}
            </button>
          </div>

          <div role="region" aria-label={t("aiKeywordSuggestions")} aria-live="polite">
            <KeywordTable
              keywords={suggestions}
              isLoading={suggestionsPending}
            />
          </div>
        </div>
      )}
    </div>
  );
}
