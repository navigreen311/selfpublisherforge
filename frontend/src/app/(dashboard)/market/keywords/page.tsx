"use client";

import { useState } from "react";
import {
  useKeywordResearch,
  useKeywordSuggestions,
} from "@/modules/market/hooks";
import { KeywordTable } from "@/modules/market/components";

export default function KeywordsPage() {
  const [keywordInput, setKeywordInput] = useState("");
  const [genreInput, setGenreInput] = useState("");
  const [activeTab, setActiveTab] = useState<"research" | "suggestions">("research");

  const keywordResearch = useKeywordResearch();
  const { data: suggestions = [], isLoading: suggestionsLoading } =
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
      <div>
        <h1 className="text-2xl font-bold">Keyword Research</h1>
        <p className="text-muted-foreground mt-1">
          Discover high-value keywords and analyze search trends for your book niche
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        <button
          onClick={() => setActiveTab("research")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "research"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Keyword Research
        </button>
        <button
          onClick={() => setActiveTab("suggestions")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "suggestions"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          AI Suggestions
        </button>
      </div>

      {/* Research tab */}
      {activeTab === "research" && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter keywords separated by commas (e.g., 'self help, productivity, mindset')..."
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleResearch()}
              className="flex-1 px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={handleResearch}
              disabled={keywordResearch.isPending || !keywordInput.trim()}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {keywordResearch.isPending ? "Researching..." : "Research"}
            </button>
          </div>

          <KeywordTable
            keywords={keywordResearch.data?.keywords ?? []}
            isLoading={keywordResearch.isPending}
          />

          {keywordResearch.isError && (
            <div className="border border-red-200 rounded-lg bg-red-50 p-4 text-sm text-red-700">
              Failed to research keywords. Please try again.
            </div>
          )}
        </div>
      )}

      {/* Suggestions tab */}
      {activeTab === "suggestions" && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter a genre (e.g., 'science fiction', 'self-help')..."
              value={genreInput}
              onChange={(e) => setGenreInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSuggest()}
              className="flex-1 px-4 py-2 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={handleSuggest}
              disabled={!genreInput.trim()}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Get Suggestions
            </button>
          </div>

          <KeywordTable
            keywords={suggestions}
            isLoading={suggestionsLoading}
          />
        </div>
      )}
    </div>
  );
}
