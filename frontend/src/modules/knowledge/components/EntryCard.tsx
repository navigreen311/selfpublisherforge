"use client";

import Link from "next/link";
import { FileText, Globe, Paperclip, PenLine } from "lucide-react";
import type { KnowledgeEntry } from "../hooks";

interface EntryCardProps {
  entry: KnowledgeEntry;
}

const sourceIcons: Record<string, React.ReactNode> = {
  manual: <PenLine className="h-4 w-4" />,
  url: <Globe className="h-4 w-4" />,
  file: <FileText className="h-4 w-4" />,
  clip: <Paperclip className="h-4 w-4" />,
};

export function EntryCard({ entry }: EntryCardProps) {
  const preview =
    entry.content.length > 180
      ? entry.content.slice(0, 180) + "..."
      : entry.content;

  const formattedDate = entry.created_at
    ? new Date(entry.created_at).toLocaleDateString()
    : "";

  return (
    <Link
      href={`/knowledge/${entry.id}`}
      className="block border rounded-lg p-4 hover:shadow-md transition-shadow bg-card"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-muted-foreground">
            {sourceIcons[entry.source_type] || sourceIcons.manual}
          </span>
          <h3 className="font-semibold text-sm truncate">{entry.title}</h3>
        </div>
        {entry.credibility_score != null && (
          <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
            {Math.round(entry.credibility_score * 100)}% cred
          </span>
        )}
      </div>

      <p className="mt-2 text-xs text-muted-foreground line-clamp-3">{preview}</p>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {entry.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground"
            >
              {tag}
            </span>
          ))}
          {entry.tags.length > 4 && (
            <span className="text-[10px] text-muted-foreground">
              +{entry.tags.length - 4}
            </span>
          )}
        </div>
        <span className="text-[10px] text-muted-foreground">{formattedDate}</span>
      </div>
    </Link>
  );
}
