"use client";

import Link from "next/link";
import { Clipboard, FileText, File, Globe } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { KnowledgeEntry } from "../hooks";

interface EntryCardProps {
  entry: KnowledgeEntry;
}

const sourceIcons: Record<string, React.ReactNode> = {
  manual: <FileText className="h-4 w-4" />,
  url: <Globe className="h-4 w-4" />,
  file: <File className="h-4 w-4" />,
  clip: <Clipboard className="h-4 w-4" />,
};

function resolveIcon(entry: KnowledgeEntry): React.ReactNode {
  // Prefer metadata.category if it maps to a known icon
  const category =
    typeof entry.metadata?.category === "string"
      ? entry.metadata.category.toLowerCase()
      : null;

  if (category && sourceIcons[category]) return sourceIcons[category];
  return sourceIcons[entry.source_type] ?? sourceIcons.manual;
}

function relativeDate(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diffMs = now - then;
  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return days === 1 ? "1 day ago" : `${days} days ago`;
  if (hours > 0) return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  if (minutes > 0)
    return minutes === 1 ? "1 minute ago" : `${minutes} minutes ago`;
  return "just now";
}

export function EntryCard({ entry }: EntryCardProps) {
  const dateSource = entry.updated_at || entry.created_at;
  const lastModified = dateSource ? relativeDate(dateSource) : "";

  const category =
    typeof entry.metadata?.category === "string"
      ? entry.metadata.category
      : null;

  const visibleTags = entry.tags.slice(0, 3);
  const extraCount = entry.tags.length - 3;

  return (
    <Link href={`/knowledge/${entry.id}`} className="block group">
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          {/* Header: icon + title + credibility */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-muted-foreground shrink-0">
                {resolveIcon(entry)}
              </span>
              <h3 className="font-semibold text-sm line-clamp-1">
                {entry.title}
              </h3>
            </div>

            {entry.credibility_score != null && (
              <Badge variant="secondary" className="shrink-0 text-[10px]">
                {Math.round(entry.credibility_score * 100)}% cred
              </Badge>
            )}
          </div>

          {/* Category badge */}
          {category && (
            <div className="mt-2">
              <Badge variant="outline" className="text-[10px]">
                {category}
              </Badge>
            </div>
          )}

          {/* Last modified */}
          {lastModified && (
            <p className="mt-2 text-[11px] text-muted-foreground">
              Last modified {lastModified}
            </p>
          )}

          {/* Tags */}
          {visibleTags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {visibleTags.map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="text-[10px] px-2 py-0"
                >
                  {tag}
                </Badge>
              ))}
              {extraCount > 0 && (
                <span className="text-[10px] text-muted-foreground self-center">
                  +{extraCount}
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
