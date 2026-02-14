"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { X, Plus } from "lucide-react";
import type { ChecklistItem } from "../types";

interface TaskChecklistProps {
  items: ChecklistItem[];
  onAdd: (label: string) => void;
  onToggle: (itemId: string, done: boolean) => void;
  onDelete?: (itemId: string) => void;
  isAdding?: boolean;
}

export function TaskChecklist({
  items,
  onAdd,
  onToggle,
  onDelete,
  isAdding,
}: TaskChecklistProps) {
  const [newLabel, setNewLabel] = useState("");

  const doneCount = items.filter((i) => i.done).length;
  const totalCount = items.length;
  const progressValue = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  function handleAdd() {
    const trimmed = newLabel.trim();
    if (!trimmed) return;
    onAdd(trimmed);
    setNewLabel("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  }

  return (
    <div className="space-y-3">
      {/* Progress summary */}
      {totalCount > 0 && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {doneCount} of {totalCount} complete
            </span>
            <span>{progressValue}%</span>
          </div>
          <Progress value={progressValue} className="h-2" />
        </div>
      )}

      {/* Checklist items */}
      <div className="space-y-1">
        {items.map((item) => (
          <div
            key={item.id}
            className="group flex items-center gap-2 py-1 px-1 rounded hover:bg-muted/50"
          >
            <input
              type="checkbox"
              checked={item.done}
              onChange={() => onToggle(item.id, !item.done)}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span
              className={cn(
                "flex-1 text-sm",
                item.done && "line-through text-muted-foreground"
              )}
            >
              {item.label}
            </span>
            {onDelete && (
              <button
                onClick={() => onDelete(item.id)}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                aria-label="Delete item"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Add item input */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={newLabel}
          onChange={(e) => setNewLabel(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add an item..."
          className="flex-1 text-sm border rounded-md px-2 py-1.5"
          disabled={isAdding}
        />
        <button
          onClick={handleAdd}
          disabled={!newLabel.trim() || isAdding}
          className="p-1.5 text-muted-foreground hover:text-foreground disabled:opacity-50"
          aria-label="Add checklist item"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
