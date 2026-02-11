"use client";

import { useState, useCallback } from "react";
import { CoverCard } from "./CoverCard";
import { Skeleton } from "@/components/ui/skeleton";
import type { Cover, CoverGenre } from "../types";

interface CoverGalleryProps {
  covers: Cover[];
  isLoading?: boolean;
  emptyMessage?: string;
}

const GENRE_OPTIONS: { value: CoverGenre | "all"; label: string }[] = [
  { value: "all", label: "All Genres" },
  { value: "romance", label: "Romance" },
  { value: "thriller", label: "Thriller" },
  { value: "mystery", label: "Mystery" },
  { value: "sci-fi", label: "Sci-Fi" },
  { value: "fantasy", label: "Fantasy" },
  { value: "horror", label: "Horror" },
  { value: "literary-fiction", label: "Literary Fiction" },
  { value: "nonfiction", label: "Non-Fiction" },
  { value: "self-help", label: "Self-Help" },
  { value: "business", label: "Business" },
  { value: "childrens", label: "Children's" },
  { value: "young-adult", label: "Young Adult" },
  { value: "memoir", label: "Memoir" },
  { value: "cookbook", label: "Cookbook" },
  { value: "other", label: "Other" },
];

export function CoverGallery({
  covers,
  isLoading = false,
  emptyMessage = "No covers yet",
}: CoverGalleryProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGenre, setSelectedGenre] = useState<CoverGenre | "all">("all");

  const filteredCovers = useCallback(() => {
    let filtered = covers;

    if (selectedGenre !== "all") {
      filtered = filtered.filter((cover) => cover.genre === selectedGenre);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (cover) =>
          cover.title.toLowerCase().includes(query) ||
          cover.author_name.toLowerCase().includes(query) ||
          cover.subtitle?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [covers, selectedGenre, searchQuery]);

  const displayedCovers = filteredCovers();

  if (isLoading) {
    return (
      <div
        className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"
        aria-label="Loading covers"
      >
        {[...Array(8)].map((_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="aspect-[2/3] w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Search covers by title or author..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <select
          value={selectedGenre}
          onChange={(e) => setSelectedGenre(e.target.value as CoverGenre | "all")}
          className="border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {GENRE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Gallery */}
      {displayedCovers.length > 0 ? (
        <>
          <p className="text-sm text-muted-foreground">
            {displayedCovers.length} cover{displayedCovers.length !== 1 ? "s" : ""}
          </p>
          <div
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"
            role="list"
            aria-label="Cover designs"
          >
            {displayedCovers.map((cover) => (
              <div key={cover.id} role="listitem">
                <CoverCard cover={cover} />
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-muted-foreground">{emptyMessage}</p>
        </div>
      )}
    </div>
  );
}
