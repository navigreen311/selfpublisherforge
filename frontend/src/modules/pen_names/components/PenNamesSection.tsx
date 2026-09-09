"use client";

import { useState } from "react";
import { Star } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

import {
  useDeletePenName,
  usePenNames,
  useSetDefaultPenName,
} from "../hooks";
import { PEN_NAME_GENRES, type PenName } from "../types";
import { PenNameFormDialog } from "./PenNameFormDialog";

function genreLabel(value: string): string {
  return PEN_NAME_GENRES.find((g) => g.value === value)?.label ?? value;
}

export function PenNamesSection() {
  const { data, isLoading, isError } = usePenNames();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<PenName | null>(null);
  const setDefaultMut = useSetDefaultPenName();
  const deleteMut = useDeletePenName();

  const openAdd = () => {
    setEditing(null);
    setFormOpen(true);
  };

  const openEdit = (pen: PenName) => {
    setEditing(pen);
    setFormOpen(true);
  };

  const handleDelete = async (pen: PenName) => {
    if (!window.confirm(`Delete pen name "${pen.display_name}"?`)) return;
    try {
      await deleteMut.mutateAsync(pen.id);
      toast.success("Pen name deleted");
    } catch (err) {
      toast.error((err as Error)?.message ?? "Failed to delete pen name");
    }
  };

  const handleSetDefault = async (pen: PenName) => {
    try {
      await setDefaultMut.mutateAsync(pen.id);
      toast.success(`"${pen.display_name}" is now the default pen name`);
    } catch (err) {
      toast.error((err as Error)?.message ?? "Failed to set default");
    }
  };

  const pens = data ?? [];

  return (
    <section aria-labelledby="pen-names-heading" className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 id="pen-names-heading" className="text-base font-semibold">
            Pen Names
          </h3>
          <p className="text-sm text-muted-foreground">
            Manage your author identities. Each pen name can have its own Amazon
            author page, bio, and be assigned to specific books.
          </p>
        </div>
        <Button onClick={openAdd}>+ Add</Button>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {isError && (
        <p className="text-sm text-destructive">
          Could not load pen names. Please retry.
        </p>
      )}

      {!isLoading && !isError && pens.length === 0 && (
        <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
          No pen names yet. Add one to assign author identities to your books.
        </div>
      )}

      <ul className="space-y-3">
        {pens.map((pen) => (
          <li
            key={pen.id}
            className="rounded-lg border bg-card p-4"
            data-testid={`pen-name-card-${pen.id}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold">{pen.display_name}</h4>
                  {pen.is_default && (
                    <Badge variant="secondary" className="gap-1">
                      <Star className="h-3 w-3" /> Default
                    </Badge>
                  )}
                </div>
                {pen.amazon_url && (
                  <p className="text-xs text-muted-foreground break-all">
                    Amazon: {pen.amazon_url}
                  </p>
                )}
                {pen.bio && (
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {pen.bio}
                  </p>
                )}
                {pen.genres.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    Genres: {pen.genres.map(genreLabel).join(", ")}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  Books using this name: {pen.book_count}
                </p>
              </div>
              <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEdit(pen)}
                >
                  Edit
                </Button>
                {!pen.is_default && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSetDefault(pen)}
                      disabled={setDefaultMut.isPending}
                    >
                      Set default
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(pen)}
                      disabled={deleteMut.isPending}
                    >
                      Delete
                    </Button>
                  </>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>

      <PenNameFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        initial={editing}
      />
    </section>
  );
}
