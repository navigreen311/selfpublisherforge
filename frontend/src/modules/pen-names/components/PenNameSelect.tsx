"use client";

/**
 * Reusable author/pen-name dropdown for every book creation wizard.
 *
 * Usage:
 *   <PenNameSelect value={penNameId} onChange={setPenNameId} />
 *
 * Shows the default pen name first (with a star) and an inline option to
 * create a new pen name. The create action is emitted via the optional
 * ``onCreate`` callback — the host page decides whether to open the modal
 * in-place or navigate to Settings > Pen Names.
 */

import { useMemo } from "react";
import { Star } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { usePenNames } from "../hooks";

interface PenNameSelectProps {
  value: string | null | undefined;
  onChange: (id: string) => void;
  onCreate?: () => void;
  placeholder?: string;
  disabled?: boolean;
  /** Optional genre filter — prioritises matching pen names in the list. */
  genre?: string;
}

export const NEW_PEN_NAME_SENTINEL = "__new__";

export function PenNameSelect({
  value,
  onChange,
  onCreate,
  placeholder = "Select author or pen name",
  disabled,
  genre,
}: PenNameSelectProps) {
  const { data: penNames = [], isLoading } = usePenNames();

  const ordered = useMemo(() => {
    const copy = [...penNames];
    copy.sort((a, b) => {
      if (a.is_default !== b.is_default) return a.is_default ? -1 : 1;
      if (genre) {
        const ag = a.genres?.includes(genre) ? 0 : 1;
        const bg = b.genres?.includes(genre) ? 0 : 1;
        if (ag !== bg) return ag - bg;
      }
      return (a.display_name || "").localeCompare(b.display_name || "");
    });
    return copy;
  }, [penNames, genre]);

  const handleChange = (v: string) => {
    if (v === NEW_PEN_NAME_SENTINEL) {
      onCreate?.();
      return;
    }
    onChange(v);
  };

  return (
    <Select
      value={value ?? undefined}
      onValueChange={handleChange}
      disabled={disabled || isLoading}
    >
      <SelectTrigger aria-label="Select pen name" data-testid="pen-name-select">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {ordered.length === 0 && (
          <div className="px-2 py-1.5 text-sm text-muted-foreground">
            No pen names yet.
          </div>
        )}
        {ordered.map((pn) => (
          <SelectItem key={pn.id} value={pn.id}>
            <span className="inline-flex items-center gap-1.5">
              {pn.is_default && (
                <Star
                  className="h-3 w-3 fill-yellow-500 text-yellow-500"
                  aria-label="Default"
                />
              )}
              {pn.display_name}
            </span>
          </SelectItem>
        ))}
        {onCreate && (
          <>
            <SelectSeparator />
            <SelectItem value={NEW_PEN_NAME_SENTINEL}>
              + Create New Pen Name
            </SelectItem>
          </>
        )}
      </SelectContent>
    </Select>
  );
}
