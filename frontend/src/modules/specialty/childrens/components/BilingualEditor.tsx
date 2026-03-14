"use client";

import * as React from "react";
import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  Globe,
  Languages,
  Loader2,
  RefreshCcw,
} from "lucide-react";
import type { ChildrensBookPage } from "../hooks";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE = "/api/v1/specialty/childrens-books";

const SUPPORTED_LANGUAGES: Record<string, string> = {
  es: "Spanish",
  fr: "French",
  de: "German",
  pt: "Portuguese",
  it: "Italian",
  zh: "Chinese (Simplified)",
  ja: "Japanese",
  ko: "Korean",
};

type LayoutMode = "side_by_side" | "alternating" | "back_section";

const LAYOUT_MODES: { value: LayoutMode; label: string; description: string }[] = [
  {
    value: "side_by_side",
    label: "Side-by-side",
    description: "Both languages on the same page",
  },
  {
    value: "alternating",
    label: "Alternating",
    description: "L1 page then L2 page",
  },
  {
    value: "back_section",
    label: "Back Section",
    description: "Full L2 story after L1",
  },
];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BilingualPage {
  page_number: number;
  text_content: string;
  translated_text: string;
  needs_retranslation?: boolean;
}

interface TranslationResult {
  target_language: string;
  language_name: string;
  pages: BilingualPage[];
}

interface ValidationResult {
  valid: boolean;
  original_readability: number;
  translated_readability: number;
  page_count_match: boolean;
  issues: { type: string; page?: number; message: string }[];
}

interface SyncResult {
  changed_pages: number[];
  total_changed: number;
  pages: BilingualPage[];
}

interface BilingualEditorProps {
  bookId: string;
  pages: ChildrensBookPage[];
  targetLanguage?: string;
  ageRange: string;
}

// ---------------------------------------------------------------------------
// API hooks
// ---------------------------------------------------------------------------

function useTranslateAll(bookId: string) {
  const qc = useQueryClient();
  return useMutation<TranslationResult, Error, { language: string; age_range: string }>({
    mutationFn: async ({ language, age_range }) => {
      const { data } = await api.post(`${API_BASE}/${bookId}/translate`, {
        target_language: language,
        age_range,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["childrens-books", "pages", bookId] });
      toast.success("Translation complete");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

function useSyncChanges(bookId: string) {
  const qc = useQueryClient();
  return useMutation<SyncResult, Error>({
    mutationFn: async () => {
      const { data } = await api.post(
        `${API_BASE}/${bookId}/sync-translations`
      );
      return data;
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["childrens-books", "pages", bookId] });
      toast.success(
        result.total_changed > 0
          ? `Re-translated ${result.total_changed} modified page(s)`
          : "All pages are up to date"
      );
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });
}

function useValidation(bookId: string) {
  return useQuery<ValidationResult>({
    queryKey: ["childrens-books", "bilingual-validation", bookId],
    queryFn: async () => {
      const { data } = await api.get(
        `${API_BASE}/${bookId}/validate-translation`
      );
      return data;
    },
    enabled: !!bookId,
  });
}

// ---------------------------------------------------------------------------
// Layout mode mini-preview
// ---------------------------------------------------------------------------

function LayoutModePreview({ mode }: { mode: LayoutMode }) {
  const l1 = "bg-blue-200 dark:bg-blue-800";
  const l2 = "bg-amber-200 dark:bg-amber-800";

  switch (mode) {
    case "side_by_side":
      return (
        <div className="flex h-10 w-16 gap-0.5 rounded border p-0.5">
          <div className={cn(l1, "flex-1 rounded-sm")} />
          <div className={cn(l2, "flex-1 rounded-sm")} />
        </div>
      );
    case "alternating":
      return (
        <div className="flex h-10 w-16 gap-0.5 rounded border p-0.5">
          <div className={cn(l1, "flex-1 rounded-sm")} />
          <div className={cn(l2, "flex-1 rounded-sm")} />
          <div className={cn(l1, "flex-1 rounded-sm")} />
          <div className={cn(l2, "flex-1 rounded-sm")} />
        </div>
      );
    case "back_section":
      return (
        <div className="flex h-10 w-16 gap-0.5 rounded border p-0.5">
          <div className={cn(l1, "flex-[3] rounded-sm")} />
          <div className={cn(l2, "flex-[3] rounded-sm")} />
        </div>
      );
  }
}

// ---------------------------------------------------------------------------
// Readability badge
// ---------------------------------------------------------------------------

function ReadabilityBadge({
  score,
  label,
}: {
  score: number;
  label: string;
}) {
  const variant =
    score >= 80 ? "default" : score >= 50 ? "secondary" : "destructive";
  return (
    <Badge variant={variant} className="gap-1 text-xs">
      {label}: {Math.round(score)}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function BilingualEditor({
  bookId,
  pages,
  targetLanguage: initialLang,
  ageRange,
}: BilingualEditorProps) {
  const [selectedLang, setSelectedLang] = useState(initialLang ?? "es");
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("side_by_side");
  const [currentPage, setCurrentPage] = useState(0);

  const translateAll = useTranslateAll(bookId);
  const syncChanges = useSyncChanges(bookId);
  const { data: validation } = useValidation(bookId);

  const langName = SUPPORTED_LANGUAGES[selectedLang] ?? selectedLang;

  // Map pages for display
  const bilingualPages: BilingualPage[] = pages.map((p) => ({
    page_number: p.page_number,
    text_content: p.text_content ?? "",
    translated_text: p.translated_text ?? "",
  }));

  const activePage = bilingualPages[currentPage];

  const handleTranslateAll = useCallback(() => {
    translateAll.mutate({
      language: selectedLang,
      age_range: ageRange,
    });
  }, [translateAll, selectedLang, ageRange]);

  const handleSyncChanges = useCallback(() => {
    syncChanges.mutate();
  }, [syncChanges]);

  const goToPrev = useCallback(() => {
    setCurrentPage((p) => Math.max(0, p - 1));
  }, []);

  const goToNext = useCallback(() => {
    setCurrentPage((p) => Math.min(bilingualPages.length - 1, p + 1));
  }, [bilingualPages.length]);

  return (
    <div className="space-y-4">
      {/* ── Header: language pair + controls ──────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-3">
        {/* Language pair display */}
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">English</span>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <Select value={selectedLang} onValueChange={setSelectedLang}>
            <SelectTrigger className="h-8 w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => (
                <SelectItem key={code} value={code}>
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={handleTranslateAll}
            disabled={translateAll.isPending}
            className="gap-1.5"
          >
            {translateAll.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Languages className="h-3.5 w-3.5" />
            )}
            {translateAll.isPending ? "Translating..." : "AI Translate All"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleSyncChanges}
            disabled={syncChanges.isPending}
            className="gap-1.5"
          >
            {syncChanges.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCcw className="h-3.5 w-3.5" />
            )}
            Sync Changes
          </Button>
        </div>
      </div>

      {/* ── Layout mode selector ─────────────────────────────── */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-muted-foreground">
          Layout:
        </span>
        {LAYOUT_MODES.map((mode) => (
          <button
            key={mode.value}
            type="button"
            onClick={() => setLayoutMode(mode.value)}
            className={cn(
              "flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs transition-all",
              "hover:border-primary/50",
              layoutMode === mode.value
                ? "border-primary bg-primary/5 font-medium"
                : "border-muted"
            )}
          >
            <LayoutModePreview mode={mode.value} />
            <div className="text-left">
              <p className="font-medium">{mode.label}</p>
              <p className="text-[10px] text-muted-foreground">
                {mode.description}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* ── Readability score badges ─────────────────────────── */}
      {validation && (
        <div className="flex items-center gap-2">
          <ReadabilityBadge
            score={validation.original_readability}
            label="English"
          />
          <ReadabilityBadge
            score={validation.translated_readability}
            label={langName}
          />
          {validation.valid && (
            <Badge
              variant="outline"
              className="gap-1 text-xs text-green-600"
            >
              <Check className="h-3 w-3" /> Valid
            </Badge>
          )}
        </div>
      )}

      {/* ── Page navigation ──────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <Button
          size="sm"
          variant="ghost"
          onClick={goToPrev}
          disabled={currentPage === 0}
          className="gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>
        <span className="text-sm font-medium text-muted-foreground">
          Page {currentPage + 1} of {bilingualPages.length}
        </span>
        <Button
          size="sm"
          variant="ghost"
          onClick={goToNext}
          disabled={currentPage >= bilingualPages.length - 1}
          className="gap-1"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* ── Split-pane editor ────────────────────────────────── */}
      {activePage && (
        <div className="grid grid-cols-2 gap-4">
          {/* Left: Original */}
          <Card className="space-y-2 p-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                English (Original)
              </h4>
              <Badge variant="outline" className="text-[10px]">
                Page {activePage.page_number}
              </Badge>
            </div>
            <Textarea
              value={activePage.text_content}
              readOnly
              className="min-h-[200px] resize-none bg-muted/30 text-sm"
              placeholder="No text on this page"
            />
          </Card>

          {/* Right: Translated */}
          <Card className="space-y-2 p-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {langName} (Translation)
              </h4>
              <Badge variant="outline" className="text-[10px]">
                Page {activePage.page_number}
              </Badge>
            </div>
            <Textarea
              value={activePage.translated_text}
              readOnly
              className={cn(
                "min-h-[200px] resize-none text-sm",
                activePage.translated_text
                  ? "bg-muted/30"
                  : "bg-amber-50/50 dark:bg-amber-950/20"
              )}
              placeholder="Not yet translated"
            />
          </Card>
        </div>
      )}

      {/* ── Translation progress indicator ───────────────────── */}
      {translateAll.isPending && (
        <div className="flex items-center gap-3 rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-950">
          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Translating to {langName}...
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-300">
              AI is translating {bilingualPages.length} pages with cultural
              adaptation and age-appropriate language constraints.
            </p>
          </div>
        </div>
      )}

      {/* ── Quick page list ──────────────────────────────────── */}
      <div className="flex flex-wrap gap-1">
        {bilingualPages.map((p, idx) => {
          const hasTranslation = !!p.translated_text;
          return (
            <button
              key={p.page_number}
              type="button"
              onClick={() => setCurrentPage(idx)}
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded text-xs font-medium transition-all",
                "border hover:ring-2 hover:ring-primary/50",
                idx === currentPage
                  ? "border-primary bg-primary text-primary-foreground"
                  : hasTranslation
                    ? "border-green-300 bg-green-50 text-green-700 dark:border-green-700 dark:bg-green-950 dark:text-green-300"
                    : "border-muted bg-background text-muted-foreground"
              )}
            >
              {p.page_number}
            </button>
          );
        })}
      </div>
    </div>
  );
}
