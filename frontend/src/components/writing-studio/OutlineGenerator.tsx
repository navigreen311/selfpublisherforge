"use client";

import { useState, useCallback } from "react";
import {
  Pencil,
  Check,
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  RotateCcw,
  BookOpen,
  Loader2,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/hooks/use-translations";
import {
  useGenerateEnhancedOutline,
  useCreateFromOutline,
} from "@/modules/writing/hooks";
import type {
  EnhancedOutlineRequest,
  EnhancedOutlineResponse,
  EnhancedOutlineChapter,
} from "@/modules/writing/hooks";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GENRES = [
  "Fiction",
  "Non-Fiction",
  "Self-Help",
  "How-To",
  "Romance",
  "Mystery",
  "Sci-Fi",
  "Fantasy",
  "Business",
  "Health",
] as const;

const BOOK_TYPES = [
  { value: "nonfiction", label: "Nonfiction" },
  { value: "fiction", label: "Fiction" },
  { value: "self-help", label: "Self-Help" },
  { value: "how-to", label: "How-To" },
] as const;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OutlineGeneratorProps {
  onCreateManuscript?: (outline: EnhancedOutlineResponse) => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OutlineGenerator({
  onCreateManuscript,
  className,
}: OutlineGeneratorProps) {
  const t = useTranslations("writing");

  // ---- Form state ----
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");
  const [bookType, setBookType] = useState<EnhancedOutlineRequest["type"]>("nonfiction");
  const [targetAudience, setTargetAudience] = useState("");
  const [uniqueAngle, setUniqueAngle] = useState("");
  const [chapterCount, setChapterCount] = useState(12);
  const [wordCountTarget, setWordCountTarget] = useState(50000);
  const [styleProfileId, setStyleProfileId] = useState("");

  // ---- Outline state ----
  const [outline, setOutline] = useState<EnhancedOutlineResponse | null>(null);
  const [editingChapterIdx, setEditingChapterIdx] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  // ---- Mutations ----
  const generateMutation = useGenerateEnhancedOutline();
  const createFromOutlineMutation = useCreateFromOutline();

  // ---- Handlers ----

  const handleGenerate = useCallback(() => {
    if (!title.trim()) return;

    const request: EnhancedOutlineRequest = {
      title: title.trim(),
      genre,
      type: bookType,
      target_audience: targetAudience.trim(),
      chapter_count: chapterCount,
      word_count_target: wordCountTarget,
      ...(uniqueAngle.trim() ? { unique_angle: uniqueAngle.trim() } : {}),
      ...(styleProfileId ? { style_profile_id: styleProfileId } : {}),
    };

    generateMutation.mutate(request, {
      onSuccess: (data) => {
        setOutline(data);
      },
    });
  }, [
    title,
    genre,
    bookType,
    targetAudience,
    uniqueAngle,
    chapterCount,
    wordCountTarget,
    styleProfileId,
    generateMutation,
  ]);

  const handleRegenerate = useCallback(() => {
    setOutline(null);
    setEditingChapterIdx(null);
    handleGenerate();
  }, [handleGenerate]);

  const handleCreateManuscript = useCallback(() => {
    if (!outline) return;

    if (onCreateManuscript) {
      onCreateManuscript(outline);
      return;
    }

    createFromOutlineMutation.mutate({
      outline,
      title: title.trim(),
    });
  }, [outline, title, onCreateManuscript, createFromOutlineMutation]);

  // ---- Chapter editing helpers ----

  const startEditingTitle = useCallback(
    (idx: number) => {
      if (!outline) return;
      setEditingChapterIdx(idx);
      setEditingTitle(outline.chapters[idx].title);
    },
    [outline]
  );

  const confirmEditTitle = useCallback(() => {
    if (editingChapterIdx === null || !outline) return;

    const updated = [...outline.chapters];
    updated[editingChapterIdx] = {
      ...updated[editingChapterIdx],
      title: editingTitle.trim() || updated[editingChapterIdx].title,
    };
    setOutline({ ...outline, chapters: updated });
    setEditingChapterIdx(null);
    setEditingTitle("");
  }, [editingChapterIdx, editingTitle, outline]);

  const cancelEditTitle = useCallback(() => {
    setEditingChapterIdx(null);
    setEditingTitle("");
  }, []);

  const addChapter = useCallback(() => {
    if (!outline) return;

    const newChapter: EnhancedOutlineChapter = {
      title: `Chapter ${outline.chapters.length + 1}`,
      summary: "",
      target_words: Math.round(wordCountTarget / (outline.chapters.length + 1)),
      key_points: [],
    };
    setOutline({ ...outline, chapters: [...outline.chapters, newChapter] });
  }, [outline, wordCountTarget]);

  const removeChapter = useCallback(
    (idx: number) => {
      if (!outline || outline.chapters.length <= 1) return;

      const updated = outline.chapters.filter((_, i) => i !== idx);
      setOutline({ ...outline, chapters: updated });

      if (editingChapterIdx === idx) {
        setEditingChapterIdx(null);
        setEditingTitle("");
      }
    },
    [outline, editingChapterIdx]
  );

  const moveChapter = useCallback(
    (idx: number, direction: "up" | "down") => {
      if (!outline) return;
      const target = direction === "up" ? idx - 1 : idx + 1;
      if (target < 0 || target >= outline.chapters.length) return;

      const updated = [...outline.chapters];
      [updated[idx], updated[target]] = [updated[target], updated[idx]];
      setOutline({ ...outline, chapters: updated });

      // Keep editing state consistent
      if (editingChapterIdx === idx) {
        setEditingChapterIdx(target);
      } else if (editingChapterIdx === target) {
        setEditingChapterIdx(idx);
      }
    },
    [outline, editingChapterIdx]
  );

  // ---- Render ----

  const isGenerating = generateMutation.isPending;
  const isCreating = createFromOutlineMutation.isPending;

  return (
    <div className={cn("flex min-h-full flex-col gap-8 p-6", className)}>
      {/* Page heading */}
      <div className="flex items-center gap-3">
        <Sparkles className="h-7 w-7 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {t("outline.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("outline.description")}
          </p>
        </div>
      </div>

      {/* ================================================================== */}
      {/* Input Form Section                                                 */}
      {/* ================================================================== */}

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">{t("outline.formTitle")}</h2>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 sm:grid-cols-2">
            {/* Book Title */}
            <div className="sm:col-span-2">
              <Input
                label={t("outline.bookTitle")}
                placeholder={t("outline.bookTitlePlaceholder")}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            {/* Genre */}
            <div className="space-y-1.5">
              <Label>{t("outline.genre")}</Label>
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger>
                  <SelectValue placeholder={t("outline.genrePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((g) => (
                    <SelectItem key={g} value={g}>
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Book Type (radio buttons) */}
            <div className="space-y-1.5">
              <Label>{t("outline.bookType")}</Label>
              <div className="flex flex-wrap gap-4 pt-1">
                {BOOK_TYPES.map(({ value, label }) => (
                  <label
                    key={value}
                    className="flex cursor-pointer items-center gap-2 text-sm"
                  >
                    <input
                      type="radio"
                      name="bookType"
                      value={value}
                      checked={bookType === value}
                      onChange={() =>
                        setBookType(value as EnhancedOutlineRequest["type"])
                      }
                      className="accent-primary h-4 w-4"
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            {/* Target Audience */}
            <div>
              <Input
                label={t("outline.targetAudience")}
                placeholder={t("outline.targetAudiencePlaceholder")}
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
              />
            </div>

            {/* Unique Angle */}
            <div>
              <Input
                label={t("outline.uniqueAngle")}
                placeholder={t("outline.uniqueAnglePlaceholder")}
                value={uniqueAngle}
                onChange={(e) => setUniqueAngle(e.target.value)}
              />
            </div>

            {/* Number of Chapters */}
            <div>
              <Input
                label={t("outline.chapterCount")}
                type="number"
                min={1}
                max={100}
                value={chapterCount}
                onChange={(e) => setChapterCount(Number(e.target.value))}
                helperText={t("outline.chapterCountHint")}
              />
            </div>

            {/* Word Count Target */}
            <div>
              <Input
                label={t("outline.wordCountTarget")}
                type="number"
                min={1000}
                step={1000}
                value={wordCountTarget}
                onChange={(e) => setWordCountTarget(Number(e.target.value))}
              />
            </div>

            {/* Style Profile (placeholder) */}
            <div className="space-y-1.5">
              <Label>{t("outline.styleProfile")}</Label>
              <Select value={styleProfileId} onValueChange={setStyleProfileId}>
                <SelectTrigger>
                  <SelectValue placeholder={t("outline.styleProfilePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none">{t("outline.styleProfileNone")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Generate button */}
          <div className="mt-8 flex items-center gap-4">
            <Button
              size="lg"
              onClick={handleGenerate}
              disabled={!title.trim() || isGenerating}
            >
              {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Sparkles className="mr-2 h-4 w-4" />
              {t("outline.generateButton")}
            </Button>

            {generateMutation.isError && (
              <p className="text-sm text-destructive">
                {generateMutation.error?.message || t("outline.generateError")}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* ================================================================== */}
      {/* Generated Outline Display                                          */}
      {/* ================================================================== */}

      {outline && (
        <div className="flex flex-col gap-6">
          {/* Section header */}
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">{t("outline.resultTitle")}</h2>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={addChapter}>
                <Plus className="mr-1.5 h-4 w-4" />
                {t("outline.addChapter")}
              </Button>
              <Button variant="outline" size="sm" onClick={handleRegenerate} disabled={isGenerating}>
                <RotateCcw className="mr-1.5 h-4 w-4" />
                {t("outline.regenerate")}
              </Button>
            </div>
          </div>

          {/* Chapter cards */}
          <div className="flex flex-col gap-4">
            {outline.chapters.map((chapter, idx) => (
              <Card key={idx}>
                <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
                  <div className="flex min-w-0 flex-1 items-start gap-3">
                    {/* Chapter number badge */}
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                      {idx + 1}
                    </span>

                    {/* Title: editable or static */}
                    {editingChapterIdx === idx ? (
                      <div className="flex min-w-0 flex-1 items-center gap-2">
                        <Input
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          className="h-8 text-lg font-semibold"
                          onKeyDown={(e) => {
                            if (e.key === "Enter") confirmEditTitle();
                            if (e.key === "Escape") cancelEditTitle();
                          }}
                          autoFocus
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 shrink-0"
                          onClick={confirmEditTitle}
                          title={t("outline.confirmEdit")}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <div className="flex min-w-0 flex-1 items-center gap-2">
                        <h3 className="truncate text-lg font-semibold">
                          {chapter.title}
                        </h3>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 shrink-0"
                          onClick={() => startEditingTitle(idx)}
                          title={t("outline.editTitle")}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Right side actions */}
                  <div className="flex items-center gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      onClick={() => moveChapter(idx, "up")}
                      disabled={idx === 0}
                      title={t("outline.moveUp")}
                    >
                      <ChevronUp className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      onClick={() => moveChapter(idx, "down")}
                      disabled={idx === outline.chapters.length - 1}
                      title={t("outline.moveDown")}
                    >
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => removeChapter(idx)}
                      disabled={outline.chapters.length <= 1}
                      title={t("outline.removeChapter")}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>

                <CardContent>
                  {/* Summary text */}
                  {chapter.summary && (
                    <p className="mb-4 text-sm text-muted-foreground leading-relaxed">
                      {chapter.summary}
                    </p>
                  )}

                  {/* Target word count */}
                  <div className="mb-3 text-xs text-muted-foreground">
                    {t("outline.targetWords")}: {chapter.target_words.toLocaleString()}
                  </div>

                  {/* Key points as tags */}
                  {chapter.key_points.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {chapter.key_points.map((point, pointIdx) => (
                        <Badge key={pointIdx} variant="secondary">
                          {point}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Bottom action bar */}
          <div className="flex items-center justify-between border-t pt-6">
            <p className="text-sm text-muted-foreground">
              {outline.chapters.length} {t("outline.chaptersTotal")} &middot;{" "}
              {outline.chapters
                .reduce((sum, ch) => sum + ch.target_words, 0)
                .toLocaleString()}{" "}
              {t("outline.wordsTotal")}
            </p>

            <Button
              size="lg"
              onClick={handleCreateManuscript}
              disabled={isCreating}
            >
              {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <BookOpen className="mr-2 h-4 w-4" />
              {t("outline.createManuscript")}
            </Button>
          </div>

          {createFromOutlineMutation.isError && (
            <p className="text-sm text-destructive">
              {createFromOutlineMutation.error?.message || t("outline.createError")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
