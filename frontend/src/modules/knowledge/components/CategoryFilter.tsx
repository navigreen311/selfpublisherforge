"use client";

import { cn } from "@/lib/utils";

export interface CategoryItem {
  name: string;
  count: number;
}

interface CategoryFilterProps {
  categories: CategoryItem[];
  selectedCategory: string | null;
  onSelect: (category: string | null) => void;
}

export function CategoryFilter({
  categories,
  selectedCategory,
  onSelect,
}: CategoryFilterProps) {
  const total = categories.reduce((sum, cat) => sum + cat.count, 0);

  return (
    <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
      <button
        onClick={() => onSelect(null)}
        className={cn(
          "inline-flex items-center gap-1 whitespace-nowrap px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0",
          selectedCategory === null
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
        )}
      >
        All
        <span
          className={cn(
            "ml-1 text-xs",
            selectedCategory === null
              ? "text-primary-foreground/70"
              : "text-muted-foreground"
          )}
        >
          ({total})
        </span>
      </button>

      {categories.map((category) => {
        const isSelected = selectedCategory === category.name;
        return (
          <button
            key={category.name}
            onClick={() => onSelect(category.name)}
            className={cn(
              "inline-flex items-center gap-1 whitespace-nowrap px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0",
              isSelected
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            {category.name}
            <span
              className={cn(
                "ml-1 text-xs",
                isSelected
                  ? "text-primary-foreground/70"
                  : "text-muted-foreground"
              )}
            >
              ({category.count})
            </span>
          </button>
        );
      })}
    </div>
  );
}
