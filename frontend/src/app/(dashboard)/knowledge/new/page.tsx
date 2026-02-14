"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, X, Save, Loader2 } from "lucide-react";
import Link from "next/link";
import { useCreateEntry } from "@/modules/knowledge/hooks";
import { useBooks } from "@/modules/writing/hooks";
import { useTranslations } from "@/hooks/use-translations";

const CATEGORIES = [
  "Notes",
  "Research",
  "Characters",
  "World-Building",
  "References",
  "Outlines",
  "Custom",
] as const;

type Category = (typeof CATEGORIES)[number];

export default function NewKnowledgeEntryPage() {
  const router = useRouter();
  const t = useTranslations("knowledge");
  const createMutation = useCreateEntry();
  const { data: books } = useBooks();

  // ── Form state ───────────────────────────────────────────────
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<Category>("Notes");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [linkedProjectId, setLinkedProjectId] = useState("");
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [entryId, setEntryId] = useState<string | null>(null);

  // ── Auto-save via debounce ───────────────────────────────────
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasContentRef = useRef(false);

  const doSave = useCallback(async () => {
    if (!title.trim() && !content.trim()) return;

    setIsSaving(true);
    try {
      const payload = {
        title: title.trim() || "Untitled Entry",
        content,
        source_type: "manual" as const,
        tags: [
          category.toLowerCase(),
          ...tags,
          ...(linkedProjectId ? [`project:${linkedProjectId}`] : []),
        ],
      };

      const result = await createMutation.mutateAsync(payload);
      setEntryId(result.id);
      setSavedAt(new Date());
    } catch {
      // Mutation error — silent for auto-save
    } finally {
      setIsSaving(false);
    }
  }, [title, content, category, tags, linkedProjectId, createMutation]);

  const scheduleAutoSave = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (hasContentRef.current && !entryId) {
        doSave();
      }
    }, 1500);
  }, [doSave, entryId]);

  // Track whether we have meaningful content
  useEffect(() => {
    hasContentRef.current = !!(title.trim() || content.trim());
  }, [title, content]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  // ── Tag management ───────────────────────────────────────────
  const handleTagKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const value = tagInput.trim().toLowerCase();
        if (value && !tags.includes(value)) {
          setTags((prev) => [...prev, value]);
          setTagInput("");
          scheduleAutoSave();
        }
      }
    },
    [tagInput, tags, scheduleAutoSave]
  );

  const removeTag = useCallback(
    (tag: string) => {
      setTags((prev) => prev.filter((t) => t !== tag));
      scheduleAutoSave();
    },
    [scheduleAutoSave]
  );

  // ── Manual save ──────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!title.trim() && !content.trim()) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);

    setIsSaving(true);
    try {
      const payload = {
        title: title.trim() || "Untitled Entry",
        content,
        source_type: "manual" as const,
        tags: [
          category.toLowerCase(),
          ...tags,
          ...(linkedProjectId ? [`project:${linkedProjectId}`] : []),
        ],
      };

      if (entryId) {
        // Already saved once — for now, create again since useUpdateEntry needs id at hook level
        // A future iteration will use useUpdateEntry properly
        const result = await createMutation.mutateAsync(payload);
        setEntryId(result.id);
      } else {
        const result = await createMutation.mutateAsync(payload);
        setEntryId(result.id);
      }
      setSavedAt(new Date());
    } catch {
      // Error handled by mutation
    } finally {
      setIsSaving(false);
    }
  }, [title, content, category, tags, linkedProjectId, entryId, createMutation]);

  // ── Field change handlers with auto-save ─────────────────────
  const handleTitleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setTitle(e.target.value);
      scheduleAutoSave();
    },
    [scheduleAutoSave]
  );

  const handleContentChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setContent(e.target.value);
      scheduleAutoSave();
    },
    [scheduleAutoSave]
  );

  const handleCategoryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setCategory(e.target.value as Category);
      scheduleAutoSave();
    },
    [scheduleAutoSave]
  );

  const handleLinkedProjectChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setLinkedProjectId(e.target.value);
      scheduleAutoSave();
    },
    [scheduleAutoSave]
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6 px-4 sm:px-6 lg:px-0">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <Link
          href="/knowledge"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t("title")}
        </Link>

        <div className="flex items-center gap-3">
          {savedAt && (
            <span className="text-xs text-muted-foreground">
              Saved {savedAt.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={isSaving || (!title.trim() && !content.trim())}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Save className="h-4 w-4" aria-hidden="true" />
            )}
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      {/* Title input */}
      <div>
        <input
          type="text"
          value={title}
          onChange={handleTitleChange}
          placeholder="Untitled Entry"
          className="w-full text-2xl sm:text-3xl font-bold bg-transparent border-none outline-none placeholder:text-muted-foreground/50 focus:ring-0"
          aria-label="Entry title"
        />
      </div>

      {/* Metadata row */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Category dropdown */}
        <div className="flex-1">
          <label
            htmlFor="entry-category"
            className="block text-xs font-medium text-muted-foreground mb-1.5"
          >
            Category
          </label>
          <select
            id="entry-category"
            value={category}
            onChange={handleCategoryChange}
            className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Linked project dropdown */}
        <div className="flex-1">
          <label
            htmlFor="linked-project"
            className="block text-xs font-medium text-muted-foreground mb-1.5"
          >
            Linked Project (optional)
          </label>
          <select
            id="linked-project"
            value={linkedProjectId}
            onChange={handleLinkedProjectChange}
            className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option value="">None</option>
            {books?.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tags chip input */}
      <div>
        <label
          htmlFor="tag-input"
          className="block text-xs font-medium text-muted-foreground mb-1.5"
        >
          Tags
        </label>
        <div className="flex flex-wrap items-center gap-2 p-2 rounded-md border border-input bg-background min-h-[42px]">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="inline-flex items-center justify-center h-3.5 w-3.5 rounded-full hover:bg-foreground/10 transition-colors"
                aria-label={`Remove tag ${tag}`}
              >
                <X className="h-2.5 w-2.5" aria-hidden="true" />
              </button>
            </span>
          ))}
          <input
            id="tag-input"
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            placeholder={tags.length === 0 ? "Add tags (press Enter)" : ""}
            className="flex-1 min-w-[120px] bg-transparent border-none outline-none text-sm placeholder:text-muted-foreground/50 focus:ring-0"
          />
        </div>
      </div>

      {/* Content textarea */}
      <div>
        <label
          htmlFor="entry-content"
          className="block text-xs font-medium text-muted-foreground mb-1.5"
        >
          {t("content")}
        </label>
        <textarea
          id="entry-content"
          value={content}
          onChange={handleContentChange}
          placeholder="Start writing your entry..."
          className="w-full min-h-[300px] rounded-md border border-input bg-background px-4 py-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y"
        />
      </div>

      {/* Status indicator */}
      {entryId && (
        <div className="text-xs text-muted-foreground">
          Entry created successfully.{" "}
          <Link
            href={`/knowledge/${entryId}`}
            className="text-primary hover:underline"
          >
            View entry
          </Link>
        </div>
      )}
    </div>
  );
}
