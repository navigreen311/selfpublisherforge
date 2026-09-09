"use client";

import { useMemo, useState } from "react";
import { Star } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { usePenNames } from "../hooks";
import type { PenName } from "../types";
import { PenNameFormDialog } from "./PenNameFormDialog";

const CREATE_SENTINEL = "__create__";

interface Props {
  value: string | null | undefined;
  onChange: (value: string | null) => void;
  /** Optional genre hint -- pen names tagged with this genre float to the top. */
  preferredGenre?: string | null;
  placeholder?: string;
  disabled?: boolean;
  /** Pass an id for label association. */
  id?: string;
}

/**
 * Author / pen-name dropdown helper shared by every book-creation wizard.
 * Default pen name is highlighted with a star and "Create New Pen Name" opens
 * the add-dialog inline without leaving the wizard.
 */
export function PenNameSelect({
  value,
  onChange,
  preferredGenre,
  placeholder = "Select author or pen name",
  disabled,
  id,
}: Props) {
  const { data, isLoading } = usePenNames();
  const [dialogOpen, setDialogOpen] = useState(false);

  const ordered = useMemo(() => {
    const list: PenName[] = Array.isArray(data) ? [...data] : [];
    return list.sort((a, b) => {
      if (a.is_default !== b.is_default) return a.is_default ? -1 : 1;
      if (preferredGenre) {
        const aHas = a.genres.includes(preferredGenre);
        const bHas = b.genres.includes(preferredGenre);
        if (aHas !== bHas) return aHas ? -1 : 1;
      }
      return a.display_name.localeCompare(b.display_name);
    });
  }, [data, preferredGenre]);

  const handleChange = (next: string) => {
    if (next === CREATE_SENTINEL) {
      setDialogOpen(true);
      return;
    }
    onChange(next || null);
  };

  return (
    <>
      <Select
        value={value ?? undefined}
        onValueChange={handleChange}
        disabled={disabled || isLoading}
      >
        <SelectTrigger id={id} aria-label={placeholder}>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {ordered.map((pen) => (
            <SelectItem key={pen.id} value={pen.id}>
              <span className="flex items-center gap-2">
                {pen.is_default && (
                  <Star className="h-3 w-3 text-yellow-500" aria-hidden />
                )}
                <span>{pen.display_name}</span>
                {pen.is_default && (
                  <span className="text-xs text-muted-foreground">
                    (default)
                  </span>
                )}
              </span>
            </SelectItem>
          ))}
          {ordered.length > 0 && (
            <div
              role="separator"
              aria-hidden
              className="my-1 h-px bg-border"
            />
          )}
          <SelectItem value={CREATE_SENTINEL}>+ Create new pen name</SelectItem>
        </SelectContent>
      </Select>

      <PenNameFormDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </>
  );
}
