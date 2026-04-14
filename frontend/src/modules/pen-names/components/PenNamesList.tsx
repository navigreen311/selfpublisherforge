"use client";

import { useState } from "react";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useDeletePenName, usePenNames } from "../hooks";
import { PenNameModal } from "./PenNameModal";
import type { PenName } from "../types";

export function PenNamesList() {
  const { data: penNames = [], isLoading, error } = usePenNames();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PenName | null>(null);
  const del = useDeletePenName();

  const openNew = () => {
    setEditing(null);
    setModalOpen(true);
  };
  const openEdit = (pn: PenName) => {
    setEditing(pn);
    setModalOpen(true);
  };
  const remove = async (pn: PenName) => {
    if (!confirm(`Delete pen name "${pn.display_name}"?`)) return;
    await del.mutateAsync(pn.id);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading pen names…
      </div>
    );
  }
  if (error) {
    return (
      <div className="text-destructive text-sm">
        Failed to load pen names.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-medium">Pen Names</h3>
          <p className="text-sm text-muted-foreground">
            Manage your author identities. Each pen name can have its own
            Amazon author page, bio, and be assigned to specific books.
          </p>
        </div>
        <Button onClick={openNew} size="sm">
          <Plus className="h-4 w-4 mr-1" /> Add
        </Button>
      </div>

      {penNames.length === 0 ? (
        <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
          No pen names yet. Click “Add” to create your first one.
        </div>
      ) : (
        <div className="space-y-3">
          {penNames.map((pn) => (
            <div
              key={pn.id}
              className="rounded-lg border bg-card p-4"
              data-testid="pen-name-card"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="font-medium truncate">{pn.display_name}</h4>
                    {pn.is_default && (
                      <Badge variant="secondary">Default</Badge>
                    )}
                  </div>
                  {pn.amazon_author_url && (
                    <a
                      href={pn.amazon_author_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-blue-600 hover:underline break-all"
                    >
                      {pn.amazon_author_url}
                    </a>
                  )}
                  {pn.bio && (
                    <p className="mt-2 text-sm text-muted-foreground line-clamp-3">
                      {pn.bio}
                    </p>
                  )}
                  {!!pn.genres?.length && (
                    <div className="mt-2 flex gap-1 flex-wrap">
                      {pn.genres.map((g) => (
                        <Badge key={g} variant="outline" className="text-xs">
                          {g}
                        </Badge>
                      ))}
                    </div>
                  )}
                  <div className="mt-2 text-xs text-muted-foreground">
                    Books using this name: {pn.book_count}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEdit(pn)}
                  >
                    <Pencil className="h-3.5 w-3.5 mr-1" /> Edit
                  </Button>
                  {!pn.is_default && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => remove(pn)}
                      disabled={del.isPending}
                    >
                      <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <PenNameModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        penName={editing}
      />
    </div>
  );
}
