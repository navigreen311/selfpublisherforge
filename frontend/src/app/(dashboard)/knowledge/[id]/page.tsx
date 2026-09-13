"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Trash2,
  Loader2,
  MoreVertical,
  Paperclip,
  X,
  Calendar,
  FileText,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import {
  useKnowledgeEntry,
  useUpdateEntry,
  useDeleteEntry,
  useSummarizeEntry,
} from "@/modules/knowledge/hooks";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { SummarizeResult } from "@/modules/knowledge/types";
import { useTranslations } from "@/hooks/use-translations";
import { toast } from "sonner";

// ── Attachment type helper ─────────────────────────────────────────
interface Attachment {
  name: string;
  size: number;
  type: string;
  data: string; // base64
}

// ── Main component ─────────────────────────────────────────────────
export default function KnowledgeEntryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations("knowledge");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const rawId = params.id;
  const entryId =
    typeof rawId === "string"
      ? rawId
      : Array.isArray(rawId)
        ? rawId[0]
        : "";

  const { data: entry, isLoading } = useKnowledgeEntry(entryId);
  const updateMutation = useUpdateEntry(entryId);
  const deleteMutation = useDeleteEntry();
  // POST /knowledge/{id}/summarize had no caller after the detail view became
  // an editor; the endpoint, the hook and the strings were all still here.
  const summarizeMutation = useSummarizeEntry(entryId);
  const [summary, setSummary] = useState<SummarizeResult | null>(null);

  const handleSummarize = useCallback(async () => {
    setSummary(await summarizeMutation.mutateAsync());
  }, [summarizeMutation]);

  // ── Form state ───────────────────────────────────────────────────
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("");
  const [tags, setTags] = useState("");
  const [linkedProject, setLinkedProject] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [tagInput, setTagInput] = useState("");

  // ── UI state ─────────────────────────────────────────────────────
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [initialized, setInitialized] = useState(false);

  // ── Populate form when entry loads ───────────────────────────────
  useEffect(() => {
    if (entry && !initialized) {
      setTitle(entry.title);
      setContent(entry.content);
      setCategory(
        (entry.metadata?.category as string) ?? ""
      );
      setTags(
        entry.tags?.join(", ") ?? ""
      );
      setLinkedProject(
        (entry.metadata?.linked_project as string) ?? ""
      );
      setAttachments(
        (entry.metadata?.attachments as Attachment[]) ?? []
      );
      setInitialized(true);
    }
  }, [entry, initialized]);

  // ── Handlers ─────────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!title.trim()) {
      toast.error(t("detail.editor.titleRequired"));
      return;
    }

    setIsSaving(true);
    try {
      const parsedTags = tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);

      await updateMutation.mutateAsync({
        title: title.trim(),
        content,
        tags: parsedTags,
        metadata: {
          ...entry?.metadata,
          category: category.trim() || undefined,
          linked_project: linkedProject.trim() || undefined,
          attachments: attachments.length > 0 ? attachments : undefined,
        },
      });
      toast.success(t("detail.editor.saveSuccess"));
    } catch {
      toast.error(t("detail.editor.saveError"));
    } finally {
      setIsSaving(false);
    }
  }, [title, content, tags, category, linkedProject, attachments, entry?.metadata, updateMutation, t]);

  const handleDelete = useCallback(async () => {
    await deleteMutation.mutateAsync(entryId);
    toast.success(t("detail.editor.deleteSuccess"));
    router.push("/knowledge");
  }, [deleteMutation, entryId, router, t]);

  const addTag = useCallback(
    (newTag: string) => {
      const trimmed = newTag.trim();
      if (!trimmed) return;
      const current = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      if (!current.includes(trimmed)) {
        setTags([...current, trimmed].join(", "));
      }
    },
    [tags]
  );

  const handleAddTag = useCallback(() => {
    addTag(tagInput);
    setTagInput("");
  }, [addTag, tagInput]);

  const handleRemoveTag = useCallback(
    (tagToRemove: string) => {
      const current = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      setTags(current.filter((t) => t !== tagToRemove).join(", "));
    },
    [tags]
  );

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      Array.from(files).forEach((file) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = (reader.result as string).split(",")[1];
          setAttachments((prev) => [
            ...prev,
            {
              name: file.name,
              size: file.size,
              type: file.type,
              data: base64,
            },
          ]);
        };
        reader.readAsDataURL(file);
      });

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    []
  );

  const handleRemoveAttachment = useCallback((index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // ── Error / loading states ───────────────────────────────────────
  if (!entryId) {
    return (
      <div className="text-center py-24">
        <h2 className="text-lg font-medium">{t("detail.invalidId")}</h2>
        <button
          onClick={() => router.push("/knowledge")}
          className="mt-4 text-sm text-primary hover:underline"
        >
          {t("detail.backToVault")}
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-6 w-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!entry) {
    return (
      <div className="text-center py-24">
        <h2 className="text-lg font-medium">{t("detail.notFound")}</h2>
        <button
          onClick={() => router.push("/knowledge")}
          className="mt-4 text-sm text-primary hover:underline"
        >
          {t("detail.backToVault")}
        </button>
      </div>
    );
  }

  const parsedTags = tags
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // ── Render ───────────────────────────────────────────────────────
  return (
    <div className="max-w-4xl mx-auto space-y-6 px-4 sm:px-6 lg:px-0">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => router.push("/knowledge")}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> {t("detail.backToVault")}
        </button>

        <div className="flex items-center gap-2">
          {/* Save button */}
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {isSaving ? t("detail.editor.saving") : t("detail.editor.save")}
          </button>

          {/* More menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-2 border rounded-lg hover:bg-accent transition-colors"
                aria-label={t("detail.editor.moreActions")}
              >
                <MoreVertical className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="cursor-pointer"
                disabled={summarizeMutation.isPending}
                onClick={handleSummarize}
              >
                <Sparkles className="mr-2 h-4 w-4" />
                {t("detail.aiSummary")}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive cursor-pointer"
                onClick={() => setShowDeleteConfirm(true)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t("detail.delete")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Provenance: where this entry came from and how much to trust it.
          The editor dropped all three when it replaced the read-only view,
          even though the entry still carries them. */}
      {(entry.source_url || entry.credibility_score != null) && (
        <div className="flex flex-wrap items-center gap-4 text-sm">
          {entry.source_url && (
            <a
              href={entry.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-primary hover:underline"
            >
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
              {entry.source_url}
            </a>
          )}
          {entry.credibility_score != null && (
            <span className="text-muted-foreground">
              {t("detail.credibility", {
                score: Math.round(entry.credibility_score * 100),
              })}
            </span>
          )}
        </div>
      )}

      {/* AI summary */}
      {summary && (
        <section
          aria-label={t("detail.aiSummary")}
          className="rounded-lg border bg-muted/40 p-4 space-y-3"
        >
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {t("detail.aiSummary")}
          </h2>
          <p className="text-sm text-muted-foreground">
            {summary.summary}
          </p>
          {summary.key_points?.length > 0 && (
            <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
              {summary.key_points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          )}
          {summary.suggested_tags?.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              {summary.suggested_tags.map((suggested) => (
                <button
                  key={suggested}
                  type="button"
                  onClick={() => addTag(suggested)}
                  className="rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                >
                  {suggested}
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Created / Updated dates */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        {entry.created_at && (
          <span className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            {t("detail.editor.createdAt")}: {formatDate(entry.created_at)}
          </span>
        )}
        {entry.updated_at && (
          <span className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            {t("detail.editor.updatedAt")}: {formatDate(entry.updated_at)}
          </span>
        )}
      </div>

      {/* Editor form */}
      <div className="space-y-5">
        {/* Title */}
        <div>
          <label
            htmlFor="entry-title"
            className="block text-sm font-medium mb-1.5"
          >
            {t("detail.editor.titleLabel")}
          </label>
          <input
            id="entry-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t("detail.editor.titlePlaceholder")}
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        {/* Category & Linked Project row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="entry-category"
              className="block text-sm font-medium mb-1.5"
            >
              {t("detail.editor.categoryLabel")}
            </label>
            <input
              id="entry-category"
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder={t("detail.editor.categoryPlaceholder")}
              className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <div>
            <label
              htmlFor="entry-linked-project"
              className="block text-sm font-medium mb-1.5"
            >
              {t("detail.editor.linkedProjectLabel")}
            </label>
            <input
              id="entry-linked-project"
              type="text"
              value={linkedProject}
              onChange={(e) => setLinkedProject(e.target.value)}
              placeholder={t("detail.editor.linkedProjectPlaceholder")}
              className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium mb-1.5">
            {t("detail.editor.tagsLabel")}
          </label>
          <div className="flex flex-wrap gap-2 mb-2">
            {parsedTags.map((tag) => (
              <span
                key={tag}
                className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-destructive transition-colors"
                  aria-label={`Remove tag ${tag}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddTag();
                }
              }}
              placeholder={t("detail.editor.tagPlaceholder")}
              className="flex-1 border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              type="button"
              onClick={handleAddTag}
              className="px-3 py-2 text-sm border rounded-lg hover:bg-accent transition-colors"
            >
              {t("detail.editor.addTag")}
            </button>
          </div>
        </div>

        {/* Content */}
        <div>
          <label
            htmlFor="entry-content"
            className="block text-sm font-medium mb-1.5"
          >
            {t("detail.editor.contentLabel")}
          </label>
          <textarea
            id="entry-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={16}
            placeholder={t("detail.editor.contentPlaceholder")}
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y min-h-[200px]"
          />
        </div>

        {/* Attachments */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Paperclip className="h-4 w-4" />
              {t("detail.editor.attachments")}
            </h3>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded-lg hover:bg-accent transition-colors"
            >
              <Paperclip className="h-3.5 w-3.5" />
              {t("detail.editor.addAttachment")}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileUpload}
              className="hidden"
              aria-label={t("detail.editor.addAttachment")}
            />
          </div>

          {attachments.length === 0 ? (
            <p className="text-xs text-muted-foreground py-4 text-center">
              {t("detail.editor.noAttachments")}
            </p>
          ) : (
            <div className="space-y-2">
              {attachments.map((attachment, index) => (
                <div
                  key={`${attachment.name}-${index}`}
                  className="flex items-center justify-between gap-3 p-2.5 rounded-lg border bg-card"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {attachment.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(attachment.size)}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveAttachment(index)}
                    className="shrink-0 p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                    aria-label={`Remove ${attachment.name}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Metadata */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <section aria-label={t("detail.metadata")} className="space-y-2">
          <h2 className="text-sm font-semibold">{t("detail.metadata")}</h2>
          <pre className="overflow-x-auto rounded-lg border bg-muted/40 p-3 text-xs text-muted-foreground">
            {JSON.stringify(entry.metadata, null, 2)}
          </pre>
        </section>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title={t("detail.deleteConfirmTitle")}
        description={t("detail.deleteConfirmMessage")}
        confirmText={t("detail.delete")}
        variant="destructive"
        loading={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
