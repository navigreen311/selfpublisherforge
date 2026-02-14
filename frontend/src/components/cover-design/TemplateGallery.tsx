"use client";

import { useState, useMemo } from "react";
import { ImageIcon } from "lucide-react";
import { useCoverTemplates } from "@/modules/cover-design/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { CoverGenre } from "@/modules/cover-design/types";

interface TemplateGalleryProps {
  onSelectTemplate: (templateId: string) => void;
}

type StyleFilter =
  | "all"
  | "minimalist"
  | "illustrated"
  | "photographic"
  | "typographic"
  | "vintage"
  | "modern";

const GENRE_FILTERS: { value: CoverGenre | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "romance", label: "Romance" },
  { value: "thriller", label: "Thriller" },
  { value: "sci-fi", label: "Sci-Fi" },
  { value: "fantasy", label: "Fantasy" },
  { value: "nonfiction", label: "Nonfiction" },
  { value: "business", label: "Business" },
  { value: "self-help", label: "Self-Help" },
  { value: "memoir", label: "Memoir" },
  { value: "childrens", label: "Children's" },
  { value: "horror", label: "Horror" },
  { value: "literary-fiction", label: "Literary" },
  { value: "young-adult", label: "Historical" },
];

const STYLE_FILTERS: { value: StyleFilter; label: string }[] = [
  { value: "all", label: "All Styles" },
  { value: "minimalist", label: "Minimalist" },
  { value: "illustrated", label: "Illustrated" },
  { value: "photographic", label: "Photographic" },
  { value: "typographic", label: "Typographic" },
  { value: "vintage", label: "Vintage" },
  { value: "modern", label: "Modern" },
];

const ITEMS_PER_PAGE = 12;

export function TemplateGallery({ onSelectTemplate }: TemplateGalleryProps) {
  const [selectedGenre, setSelectedGenre] = useState<CoverGenre | "all">("all");
  const [selectedStyle, setSelectedStyle] = useState<StyleFilter>("all");
  const [currentPage, setCurrentPage] = useState(1);

  const { data: allTemplates, isPending } = useCoverTemplates(
    selectedGenre === "all" ? undefined : selectedGenre
  );

  const filteredTemplates = useMemo(() => {
    if (!allTemplates) return [];
    if (selectedStyle === "all") return allTemplates;

    return allTemplates.filter((template) =>
      template.tags.some((tag) =>
        tag.toLowerCase().includes(selectedStyle.toLowerCase())
      )
    );
  }, [allTemplates, selectedStyle]);

  const totalTemplates = filteredTemplates.length;
  const totalPages = Math.ceil(totalTemplates / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedTemplates = filteredTemplates.slice(startIndex, endIndex);

  const handleGenreChange = (genre: CoverGenre | "all") => {
    setSelectedGenre(genre);
    setCurrentPage(1);
  };

  const handleStyleChange = (style: StyleFilter) => {
    setSelectedStyle(style);
    setCurrentPage(1);
  };

  const handleLoadMore = () => {
    setCurrentPage((prev) => prev + 1);
  };

  const hasMore = currentPage < totalPages;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-muted-foreground">Genre</h3>
        <div className="flex flex-wrap gap-2">
          {GENRE_FILTERS.map((filter) => (
            <Badge
              key={filter.value}
              variant={selectedGenre === filter.value ? "default" : "outline"}
              className="cursor-pointer hover:bg-primary/90 transition-colors"
              onClick={() => handleGenreChange(filter.value)}
            >
              {filter.label}
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium text-muted-foreground">Style</h3>
        <div className="flex flex-wrap gap-2">
          {STYLE_FILTERS.map((filter) => (
            <Badge
              key={filter.value}
              variant={selectedStyle === filter.value ? "default" : "outline"}
              className="cursor-pointer hover:bg-primary/90 transition-colors"
              onClick={() => handleStyleChange(filter.value)}
            >
              {filter.label}
            </Badge>
          ))}
        </div>
      </div>

      {!isPending && (
        <p className="text-sm text-muted-foreground">
          Showing {Math.min(endIndex, totalTemplates)} of {totalTemplates}{" "}
          template{totalTemplates !== 1 ? "s" : ""}
        </p>
      )}

      {isPending && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="aspect-[2/3] w-full rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-9 w-full" />
            </div>
          ))}
        </div>
      )}

      {!isPending && filteredTemplates.length === 0 && (
        <div className="text-center py-12 border-2 border-dashed rounded-lg">
          <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No templates found</h3>
          <p className="text-muted-foreground">
            Try adjusting your filters to see more templates.
          </p>
        </div>
      )}

      {!isPending && paginatedTemplates.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {paginatedTemplates.map((template) => (
              <div
                key={template.id}
                className="group border rounded-lg overflow-hidden hover:shadow-lg transition-all duration-200"
              >
                <div className="aspect-[2/3] bg-muted relative overflow-hidden">
                  {template.thumbnail_url ? (
                    <img
                      src={template.thumbnail_url}
                      alt={template.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                      <ImageIcon className="h-16 w-16" />
                    </div>
                  )}
                </div>

                <div className="p-4 space-y-3">
                  <div>
                    <h3 className="font-semibold text-sm truncate">
                      {template.name}
                    </h3>
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {template.description}
                    </p>
                  </div>

                  <Button
                    onClick={() => onSelectTemplate(template.id)}
                    className="w-full"
                    size="sm"
                  >
                    Use This
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="flex justify-center pt-4">
              <Button
                onClick={handleLoadMore}
                variant="outline"
                size="lg"
                className="min-w-[200px]"
              >
                Load More
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
