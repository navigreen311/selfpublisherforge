"use client";

import { useState } from "react";
import { ImageIcon } from "lucide-react";
import { useCoverTemplates } from "../hooks";
import { Skeleton } from "@/components/ui/skeleton";
import type { CoverGenre, CoverTemplate } from "../types";

interface TemplateGalleryProps {
  selectedGenre?: CoverGenre;
  onSelectTemplate?: (template: CoverTemplate) => void;
}

export function TemplateGallery({
  selectedGenre,
  onSelectTemplate,
}: TemplateGalleryProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: templates, isPending } = useCoverTemplates(selectedGenre);

  const handleSelect = (template: CoverTemplate) => {
    setSelectedId(template.id);
    if (onSelectTemplate) {
      onSelectTemplate(template);
    }
  };

  if (isPending) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="aspect-[2/3] w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!templates || templates.length === 0) {
    return (
      <div className="text-center py-12">
        <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
        <p className="text-muted-foreground">
          No templates available{selectedGenre ? ` for ${selectedGenre}` : ""}.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        {templates.length} template{templates.length !== 1 ? "s" : ""} available
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {templates.map((template) => {
          const isSelected = selectedId === template.id;
          return (
            <button
              key={template.id}
              onClick={() => handleSelect(template)}
              className={`text-left border rounded-lg overflow-hidden transition-all ${
                isSelected
                  ? "ring-2 ring-primary shadow-lg"
                  : "hover:shadow-md hover:border-primary/50"
              }`}
            >
              {/* Template thumbnail */}
              <div className="aspect-[2/3] bg-muted relative overflow-hidden">
                {template.thumbnail_url ? (
                  <img
                    src={template.thumbnail_url}
                    alt={template.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                    <ImageIcon className="h-10 w-10" />
                  </div>
                )}
              </div>

              {/* Template info */}
              <div className="p-3 space-y-1">
                <h3 className="font-semibold text-sm truncate">
                  {template.name}
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {template.description}
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {template.tags.slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
