"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreatePenName, useUpdatePenName } from "../hooks";
import type { PenName, PenNameInput } from "../types";

const GENRE_OPTIONS = [
  "Children's Books",
  "Coloring Books",
  "Puzzle Books",
  "Comic Books",
  "Cookbooks",
  "Nonfiction",
  "Fiction",
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  penName?: PenName | null;
  onSaved?: (pn: PenName) => void;
}

export function PenNameModal({ open, onOpenChange, penName, onSaved }: Props) {
  const isEdit = !!penName;
  const [form, setForm] = useState<PenNameInput>({
    display_name: "",
    amazon_author_url: "",
    bio: "",
    photo_url: "",
    genres: [],
    is_default: false,
  });
  const create = useCreatePenName();
  const update = useUpdatePenName(penName?.id ?? "");
  const busy = create.isPending || update.isPending;

  useEffect(() => {
    if (penName) {
      setForm({
        display_name: penName.display_name,
        amazon_author_url: penName.amazon_author_url ?? "",
        bio: penName.bio ?? "",
        photo_url: penName.photo_url ?? "",
        genres: penName.genres ?? [],
        is_default: penName.is_default,
      });
    } else {
      setForm({
        display_name: "",
        amazon_author_url: "",
        bio: "",
        photo_url: "",
        genres: [],
        is_default: false,
      });
    }
  }, [penName, open]);

  const toggleGenre = (g: string) => {
    setForm((f) => {
      const set = new Set(f.genres ?? []);
      if (set.has(g)) set.delete(g);
      else set.add(g);
      return { ...f, genres: Array.from(set) };
    });
  };

  const submit = async () => {
    if (!form.display_name.trim()) return;
    const payload: PenNameInput = {
      display_name: form.display_name.trim(),
      amazon_author_url: form.amazon_author_url || null,
      bio: form.bio || null,
      photo_url: form.photo_url || null,
      genres: form.genres,
      is_default: form.is_default,
    };
    const result = isEdit
      ? await update.mutateAsync(payload)
      : await create.mutateAsync(payload);
    onSaved?.(result);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Pen Name" : "Add Pen Name"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="pn-display-name">Display Name *</Label>
            <Input
              id="pn-display-name"
              value={form.display_name}
              onChange={(e) =>
                setForm((f) => ({ ...f, display_name: e.target.value }))
              }
              required
              maxLength={255}
            />
          </div>
          <div>
            <Label htmlFor="pn-amz">Amazon Author Page URL</Label>
            <Input
              id="pn-amz"
              placeholder="https://amazon.com/author/..."
              value={form.amazon_author_url ?? ""}
              onChange={(e) =>
                setForm((f) => ({ ...f, amazon_author_url: e.target.value }))
              }
            />
          </div>
          <div>
            <Label htmlFor="pn-bio">Author Bio</Label>
            <Textarea
              id="pn-bio"
              rows={4}
              maxLength={2000}
              value={form.bio ?? ""}
              onChange={(e) =>
                setForm((f) => ({ ...f, bio: e.target.value }))
              }
            />
            <div className="text-xs text-muted-foreground mt-1">
              {(form.bio ?? "").length}/2000
            </div>
          </div>
          <div>
            <Label>Primary Genres</Label>
            <div className="flex flex-wrap gap-2 mt-1">
              {GENRE_OPTIONS.map((g) => {
                const checked = (form.genres ?? []).includes(g);
                return (
                  <label
                    key={g}
                    className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs cursor-pointer"
                  >
                    <Checkbox
                      checked={checked}
                      onCheckedChange={() => toggleGenre(g)}
                      aria-label={g}
                    />
                    {g}
                  </label>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="pn-default"
              checked={!!form.is_default}
              onCheckedChange={(v) =>
                setForm((f) => ({ ...f, is_default: !!v }))
              }
            />
            <Label htmlFor="pn-default">Set as default pen name</Label>
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={busy}
          >
            Cancel
          </Button>
          <Button onClick={submit} disabled={busy || !form.display_name.trim()}>
            {busy && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            Save Pen Name
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
