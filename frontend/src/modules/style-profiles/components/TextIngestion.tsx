"use client";

import { useCallback, useRef, useState } from "react";
import {
  Upload,
  FileText,
  ClipboardPaste,
  BookOpen,
  Eye,
  EyeOff,
  X,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useBooks, useChapters } from "@/modules/writing/hooks";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SampleEntry {
  label: string;
  text: string;
  wordCount: number;
}

interface TextIngestionProps {
  onSubmit: (texts: string[]) => void;
  isSubmitting?: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function countWords(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length;
}

const MIN_WORDS = 1_000;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TextIngestion({
  onSubmit,
  isSubmitting = false,
}: TextIngestionProps) {
  const [samples, setSamples] = useState<SampleEntry[]>([]);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  // Paste modal state
  const [pasteOpen, setPasteOpen] = useState(false);
  const [pasteText, setPasteText] = useState("");

  // Manuscript modal state
  const [manuscriptOpen, setManuscriptOpen] = useState(false);
  const [selectedBookId, setSelectedBookId] = useState<string>("");
  const [selectedChapterIds, setSelectedChapterIds] = useState<Set<string>>(
    new Set()
  );

  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Data hooks
  const { data: books, isLoading: booksLoading } = useBooks();
  const { data: chapters, isLoading: chaptersLoading } =
    useChapters(selectedBookId);

  // -------------------------------------------------------------------------
  // Totals
  // -------------------------------------------------------------------------

  const totalWords = samples.reduce((sum, s) => sum + s.wordCount, 0);
  const meetsMinimum = totalWords >= MIN_WORDS;

  // -------------------------------------------------------------------------
  // Add / remove helpers
  // -------------------------------------------------------------------------

  const addSample = useCallback((label: string, text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setSamples((prev) => [
      ...prev,
      { label, text: trimmed, wordCount: countWords(trimmed) },
    ]);
  }, []);

  const removeSample = useCallback(
    (index: number) => {
      setSamples((prev) => prev.filter((_, i) => i !== index));
      if (expandedIdx === index) setExpandedIdx(null);
      else if (expandedIdx !== null && expandedIdx > index)
        setExpandedIdx(expandedIdx - 1);
    },
    [expandedIdx]
  );

  // -------------------------------------------------------------------------
  // Upload Files
  // -------------------------------------------------------------------------

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      for (const file of Array.from(files)) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const text = event.target?.result as string;
          if (text?.trim()) {
            addSample(file.name, text);
          }
        };
        reader.readAsText(file);
      }

      // Reset the input so the same file(s) can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    [addSample]
  );

  // -------------------------------------------------------------------------
  // Paste Text submit
  // -------------------------------------------------------------------------

  const handlePasteSubmit = useCallback(() => {
    if (pasteText.trim()) {
      addSample("Pasted text", pasteText);
      setPasteText("");
      setPasteOpen(false);
    }
  }, [pasteText, addSample]);

  // -------------------------------------------------------------------------
  // Manuscript chapter confirm
  // -------------------------------------------------------------------------

  const handleManuscriptConfirm = useCallback(() => {
    if (!chapters || selectedChapterIds.size === 0) return;
    const book = books?.find((b) => b.id === selectedBookId);
    const bookTitle = book?.title ?? "Manuscript";

    for (const ch of chapters) {
      if (selectedChapterIds.has(ch.id) && ch.content?.trim()) {
        addSample(`${bookTitle} - ${ch.title}`, ch.content);
      }
    }

    setSelectedBookId("");
    setSelectedChapterIds(new Set());
    setManuscriptOpen(false);
  }, [chapters, selectedChapterIds, books, selectedBookId, addSample]);

  // -------------------------------------------------------------------------
  // Toggle chapter selection
  // -------------------------------------------------------------------------

  const toggleChapter = useCallback((chapterId: string) => {
    setSelectedChapterIds((prev) => {
      const next = new Set(prev);
      if (next.has(chapterId)) next.delete(chapterId);
      else next.add(chapterId);
      return next;
    });
  }, []);

  const toggleAllChapters = useCallback(() => {
    if (!chapters) return;
    setSelectedChapterIds((prev) => {
      if (prev.size === chapters.length) return new Set();
      return new Set(chapters.map((c) => c.id));
    });
  }, [chapters]);

  // -------------------------------------------------------------------------
  // Submit
  // -------------------------------------------------------------------------

  const handleSubmit = useCallback(() => {
    if (samples.length > 0) {
      onSubmit(samples.map((s) => s.text));
    }
  }, [samples, onSubmit]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="space-y-5">
      {/* -------- Input mode buttons -------- */}
      <div>
        <p className="text-sm font-medium mb-3">Add Writing Samples</p>
        <div className="flex flex-wrap gap-2">
          {/* Upload Files */}
          <label className="inline-flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent cursor-pointer transition-colors">
            <Upload className="h-4 w-4" aria-hidden="true" />
            Upload Files
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx,.txt,.md,.epub"
              multiple
              onChange={handleFileUpload}
              className="hidden"
              aria-label="Upload text files"
            />
          </label>

          {/* Paste Text */}
          <button
            type="button"
            onClick={() => setPasteOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent transition-colors"
          >
            <ClipboardPaste className="h-4 w-4" aria-hidden="true" />
            Paste Text
          </button>

          {/* From Manuscript */}
          <button
            type="button"
            onClick={() => setManuscriptOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent transition-colors"
          >
            <BookOpen className="h-4 w-4" aria-hidden="true" />
            From Manuscript
          </button>
        </div>
      </div>

      {/* -------- Sample cards -------- */}
      {samples.length > 0 && (
        <div className="space-y-2">
          {samples.map((sample, idx) => (
            <div
              key={idx}
              className="border rounded-lg bg-card p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileText
                    className="h-4 w-4 text-muted-foreground shrink-0"
                    aria-hidden="true"
                  />
                  <span className="text-sm font-medium truncate">
                    {sample.label}
                  </span>
                  <span className="text-xs text-muted-foreground shrink-0">
                    {sample.wordCount.toLocaleString()} words
                  </span>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() =>
                      setExpandedIdx(expandedIdx === idx ? null : idx)
                    }
                    aria-label={
                      expandedIdx === idx
                        ? `Collapse sample ${idx + 1}`
                        : `Preview sample ${idx + 1}`
                    }
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded hover:bg-accent transition-colors"
                  >
                    {expandedIdx === idx ? (
                      <>
                        <EyeOff className="h-3 w-3" aria-hidden="true" />
                        Hide
                      </>
                    ) : (
                      <>
                        <Eye className="h-3 w-3" aria-hidden="true" />
                        Preview
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeSample(idx)}
                    aria-label={`Remove sample ${idx + 1}`}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs text-destructive rounded hover:bg-destructive/10 transition-colors"
                  >
                    <X className="h-3 w-3" aria-hidden="true" />
                    Remove
                  </button>
                </div>
              </div>

              {/* Expanded preview */}
              {expandedIdx === idx && (
                <div className="mt-2 p-3 rounded bg-muted/50 text-sm text-muted-foreground max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {sample.text}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* -------- Totals -------- */}
      <div className="flex items-center gap-2 text-sm">
        {meetsMinimum ? (
          <CheckCircle2
            className="h-4 w-4 text-green-600 shrink-0"
            aria-hidden="true"
          />
        ) : (
          <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/40 shrink-0" />
        )}
        <span className={meetsMinimum ? "text-green-600" : "text-muted-foreground"}>
          {samples.length} sample{samples.length !== 1 ? "s" : ""},{" "}
          {totalWords.toLocaleString()} words (minimum: 1,000 words)
        </span>
      </div>

      {/* -------- Submit -------- */}
      <div className="flex justify-end pt-4 border-t">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={samples.length === 0 || isSubmitting}
          className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Processing..." : "Analyze Samples"}
        </button>
      </div>

      {/* ================================================================== */}
      {/*  Paste Text Modal                                                  */}
      {/* ================================================================== */}
      <Dialog open={pasteOpen} onOpenChange={setPasteOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Paste Writing Sample</DialogTitle>
            <DialogDescription>
              Paste or type your writing sample below. A few paragraphs or more
              will give the best results.
            </DialogDescription>
          </DialogHeader>

          <textarea
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste your writing sample here..."
            rows={10}
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
          />

          {pasteText.trim() && (
            <p className="text-xs text-muted-foreground">
              {countWords(pasteText).toLocaleString()} words
            </p>
          )}

          <DialogFooter>
            <button
              type="button"
              onClick={() => setPasteOpen(false)}
              className="px-4 py-2 text-sm border rounded-lg hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handlePasteSubmit}
              disabled={!pasteText.trim()}
              className="px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add Sample
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ================================================================== */}
      {/*  From Manuscript Modal                                             */}
      {/* ================================================================== */}
      <Dialog
        open={manuscriptOpen}
        onOpenChange={(open) => {
          setManuscriptOpen(open);
          if (!open) {
            setSelectedBookId("");
            setSelectedChapterIds(new Set());
          }
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Import from Manuscript</DialogTitle>
            <DialogDescription>
              Select a book and choose chapters to use as writing samples.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Book selector */}
            <div>
              <label className="block text-sm font-medium mb-1.5">Book</label>
              {booksLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Loading books...
                </div>
              ) : books && books.length > 0 ? (
                <Select
                  value={selectedBookId}
                  onValueChange={(val) => {
                    setSelectedBookId(val);
                    setSelectedChapterIds(new Set());
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a book..." />
                  </SelectTrigger>
                  <SelectContent>
                    {books.map((book) => (
                      <SelectItem key={book.id} value={book.id}>
                        {book.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-muted-foreground py-2">
                  No manuscripts found. Create a book first.
                </p>
              )}
            </div>

            {/* Chapter list */}
            {selectedBookId && (
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-medium">Chapters</label>
                  {chapters && chapters.length > 0 && (
                    <button
                      type="button"
                      onClick={toggleAllChapters}
                      className="text-xs text-primary hover:underline"
                    >
                      {selectedChapterIds.size === chapters.length
                        ? "Deselect all"
                        : "Select all"}
                    </button>
                  )}
                </div>

                {chaptersLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                    <Loader2
                      className="h-4 w-4 animate-spin"
                      aria-hidden="true"
                    />
                    Loading chapters...
                  </div>
                ) : chapters && chapters.length > 0 ? (
                  <div className="max-h-56 overflow-y-auto space-y-1 border rounded-lg p-2">
                    {chapters.map((ch) => (
                      <label
                        key={ch.id}
                        className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-accent cursor-pointer text-sm"
                      >
                        <input
                          type="checkbox"
                          checked={selectedChapterIds.has(ch.id)}
                          onChange={() => toggleChapter(ch.id)}
                          className="rounded border-input"
                        />
                        <span className="flex-1 truncate">{ch.title}</span>
                        <span className="text-xs text-muted-foreground shrink-0">
                          {(ch.word_count ?? 0).toLocaleString()} words
                        </span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-2">
                    No chapters found in this book.
                  </p>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <button
              type="button"
              onClick={() => setManuscriptOpen(false)}
              className="px-4 py-2 text-sm border rounded-lg hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleManuscriptConfirm}
              disabled={selectedChapterIds.size === 0}
              className="px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add {selectedChapterIds.size} Chapter
              {selectedChapterIds.size !== 1 ? "s" : ""}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
