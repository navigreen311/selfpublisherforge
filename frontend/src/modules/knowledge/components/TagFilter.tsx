"use client";

import { cn } from "@/lib/utils";

interface TagFilterProps {
  tags: string[];
  counts: Record<string, number>;
  selectedTags: string[];
  onToggleTag: (tag: string) => void;
}

export function TagFilter({ tags, counts, selectedTags, onToggleTag }: TagFilterProps) {
  if (tags.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">No tags yet.</div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag) => {
        const isSelected = selectedTags.includes(tag);
        return (
          <button
            key={tag}
            onClick={() => onToggleTag(tag)}
            className={cn(
              "inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium transition-colors",
              isSelected
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            {tag}
            {counts[tag] != null && (
              <span
                className={cn(
                  "ml-1 text-xs",
                  isSelected ? "text-primary-foreground/70" : "text-muted-foreground"
                )}
              >
                ({counts[tag]})
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
