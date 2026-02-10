"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Globe,
  FileText,
  PenLine,
  Paperclip,
  Sparkles,
  Trash2,
  Loader2,
} from "lucide-react";
import {
  useKnowledgeEntry,
  useDeleteEntry,
  useSummarizeEntry,
} from "@/modules/knowledge/hooks";

const sourceLabels: Record<string, string> = {
  manual: "Manual entry",
  url: "Imported from URL",
  file: "Imported from file",
  clip: "Web clip",
};

const sourceIcons: Record<string, React.ReactNode> = {
  manual: <PenLine className="h-4 w-4" />,
  url: <Globe className="h-4 w-4" />,
  file: <FileText className="h-4 w-4" />,
  clip: <Paperclip className="h-4 w-4" />,
};

export default function KnowledgeEntryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const entryId = params.id as string;
  const { data: entry, isLoading } = useKnowledgeEntry(entryId);
  const deleteMutation = useDeleteEntry();
  const summarizeMutation = useSummarizeEntry(entryId);
  const [summary, setSummary] = useState<{
    summary: string;
    key_points: string[];
    suggested_tags: string[];
  } | null>(null);

  const handleDelete = useCallback(async () => {
    if (!confirm("Are you sure you want to delete this entry?")) return;
    await deleteMutation.mutateAsync(entryId);
    router.push("/knowledge");
  }, [deleteMutation, entryId, router]);

  const handleSummarize = useCallback(async () => {
    const result = await summarizeMutation.mutateAsync();
    setSummary({
      summary: result.summary,
      key_points: result.key_points,
      suggested_tags: result.suggested_tags,
    });
  }, [summarizeMutation]);

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
        <h2 className="text-lg font-medium">Entry not found</h2>
        <button
          onClick={() => router.push("/knowledge")}
          className="mt-4 text-sm text-primary hover:underline"
        >
          Back to Knowledge Vault
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <button
        onClick={() => router.push("/knowledge")}
        className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Knowledge Vault
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{entry.title}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              {sourceIcons[entry.source_type]}
              {sourceLabels[entry.source_type] || entry.source_type}
            </span>
            {entry.created_at && (
              <span>Created {new Date(entry.created_at).toLocaleDateString()}</span>
            )}
            {entry.credibility_score != null && (
              <span className="px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground text-xs">
                {Math.round(entry.credibility_score * 100)}% credibility
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSummarize}
            disabled={summarizeMutation.isPending}
            className="flex items-center gap-2 px-3 py-2 text-sm border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
          >
            {summarizeMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            AI Summary
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" /> Delete
          </button>
        </div>
      </div>

      {/* Source URL */}
      {entry.source_url && (
        <a
          href={entry.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary hover:underline break-all"
        >
          {entry.source_url}
        </a>
      )}

      {/* Tags */}
      {entry.tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {entry.tags.map((tag) => (
            <span
              key={tag}
              className="px-3 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* AI Summary section */}
      {summary && (
        <div className="border rounded-lg p-4 bg-primary/5">
          <h3 className="flex items-center gap-2 font-semibold text-sm mb-2">
            <Sparkles className="h-4 w-4 text-primary" /> AI Summary
          </h3>
          <p className="text-sm">{summary.summary}</p>
          {summary.key_points.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-muted-foreground mb-1">
                Key Points
              </h4>
              <ul className="list-disc list-inside text-sm space-y-1">
                {summary.key_points.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {summary.suggested_tags.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-muted-foreground mb-1">
                Suggested Tags
              </h4>
              <div className="flex flex-wrap gap-1">
                {summary.suggested_tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Content */}
      <div className="border rounded-lg p-6 bg-card">
        <div className="prose prose-sm max-w-none whitespace-pre-wrap">
          {entry.content}
        </div>
      </div>

      {/* Metadata */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <div className="border rounded-lg p-4">
          <h3 className="text-sm font-semibold mb-2">Metadata</h3>
          <pre className="text-xs text-muted-foreground overflow-auto">
            {JSON.stringify(entry.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
