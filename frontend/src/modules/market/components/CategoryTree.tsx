"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { CategoryNode } from "../hooks";

interface CategoryTreeProps {
  categories: CategoryNode[];
  onSelect: (category: CategoryNode) => void;
  selectedId?: string;
}

export function CategoryTree({ categories, onSelect, selectedId }: CategoryTreeProps) {
  return (
    <div className="border rounded-lg bg-card">
      <div className="p-4 border-b">
        <h3 className="font-semibold text-sm">Amazon Categories</h3>
      </div>
      <div className="p-2 max-h-[500px] overflow-y-auto">
        {categories.map((cat) => (
          <CategoryTreeNode
            key={cat.id}
            node={cat}
            depth={0}
            onSelect={onSelect}
            selectedId={selectedId}
          />
        ))}
      </div>
    </div>
  );
}

function CategoryTreeNode({
  node,
  depth,
  onSelect,
  selectedId,
}: {
  node: CategoryNode;
  depth: number;
  onSelect: (cat: CategoryNode) => void;
  selectedId?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = node.children.length > 0;
  const isSelected = node.id === selectedId;

  return (
    <div>
      <button
        onClick={() => {
          onSelect(node);
          if (hasChildren) setExpanded(!expanded);
        }}
        className={cn(
          "w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors text-left",
          isSelected
            ? "bg-primary/10 text-primary font-medium"
            : "hover:bg-accent text-foreground"
        )}
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
      >
        {hasChildren && (
          <span className="text-xs text-muted-foreground w-4 flex-shrink-0">
            {expanded ? "\u25BC" : "\u25B6"}
          </span>
        )}
        {!hasChildren && <span className="w-4 flex-shrink-0" />}
        <span className="flex-1 truncate">{node.name}</span>
        {node.book_count != null && (
          <span className="text-xs text-muted-foreground flex-shrink-0">
            {node.book_count.toLocaleString()}
          </span>
        )}
      </button>
      {expanded &&
        hasChildren &&
        node.children.map((child) => (
          <CategoryTreeNode
            key={child.id}
            node={child}
            depth={depth + 1}
            onSelect={onSelect}
            selectedId={selectedId}
          />
        ))}
    </div>
  );
}
