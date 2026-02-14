"use client";

import { cn } from "@/lib/utils";

export interface CategoryItem {
  name: string;
  count: number;
}

interface CategoryFilterProps {
  categories: CategoryItem[];
  selectedCategory: string | null;
  onSelectCategory: (category: string | null) => void;
}

export function CategoryFilter({
  categories,
  selectedCategory,
  onSelectCategory,
}: CategoryFilterProps) {
  if (categories.length === 0) return null;

  const total = categories.reduce((sum, c) => sum + c.count, 0);

  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
      <button
        onClick={() => onSelectCategory(null)}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
          selectedCategory === null
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
        )}
      >
        All
        <span
          className={cn(
            "text-[10px]",
            selectedCategory === null
              ? "text-primary-foreground/70"
              : "text-muted-foreground"
          )}
        >
          ({total})
        </span>
      </button>
      {categories.map((cat) => {
        const isSelected = selectedCategory === cat.name;
        return (
          <button
            key={cat.name}
            onClick={() => onSelectCategory(isSelected ? null : cat.name)}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors capitalize",
              isSelected
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            {cat.name}
            <span
              className={cn(
                "text-[10px]",
                isSelected
                  ? "text-primary-foreground/70"
                  : "text-muted-foreground"
              )}
            >
              ({cat.count})
            </span>
          </button>
        );
      })}
    </div>
  );
}
