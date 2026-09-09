"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { useCreatePenName, useUpdatePenName } from "../hooks";
import { PEN_NAME_GENRES, type PenName } from "../types";

const BIO_MAX = 2000;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initial?: PenName | null;
}

export function PenNameFormDialog({ open, onOpenChange, initial }: Props) {
  const isEdit = Boolean(initial);
  const [displayName, setDisplayName] = useState("");
  const [amazonUrl, setAmazonUrl] = useState("");
  const [bio, setBio] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [genres, setGenres] = useState<string[]>([]);
  const [isDefault, setIsDefault] = useState(false);

  useEffect(() => {
    if (open) {
      setDisplayName(initial?.display_name ?? "");
      setAmazonUrl(initial?.amazon_url ?? "");
      setBio(initial?.bio ?? "");
      setPhotoUrl(initial?.photo_url ?? "");
      setGenres(initial?.genres ?? []);
      setIsDefault(Boolean(initial?.is_default));
    }
  }, [open, initial]);

  const createMut = useCreatePenName();
  const updateMut = useUpdatePenName();
  const submitting = createMut.isPending || updateMut.isPending;

  const toggleGenre = (value: string) => {
    setGenres((cur) =>
      cur.includes(value) ? cur.filter((g) => g !== value) : [...cur, value]
    );
  };

  const handleSubmit = async () => {
    const trimmed = displayName.trim();
    if (!trimmed) {
      toast.error("Display name is required");
      return;
    }
    const payload = {
      display_name: trimmed,
      amazon_url: amazonUrl.trim() || null,
      bio: bio.trim() || null,
      photo_url: photoUrl.trim() || null,
      genres,
      is_default: isDefault,
    };
    try {
      if (isEdit && initial) {
        await updateMut.mutateAsync({ id: initial.id, data: payload });
        toast.success("Pen name updated");
      } else {
        await createMut.mutateAsync(payload);
        toast.success("Pen name created");
      }
      onOpenChange(false);
    } catch (err) {
      toast.error((err as Error)?.message ?? "Failed to save pen name");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Pen Name" : "Add Pen Name"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pn-display-name">Display name *</Label>
            <Input
              id="pn-display-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={255}
              placeholder="Jane Doe"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pn-amazon-url">Amazon author page URL</Label>
            <Input
              id="pn-amazon-url"
              value={amazonUrl}
              onChange={(e) => setAmazonUrl(e.target.value)}
              placeholder="https://amazon.com/author/janedoe"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pn-bio">Author bio</Label>
            <Textarea
              id="pn-bio"
              value={bio}
              onChange={(e) => setBio(e.target.value.slice(0, BIO_MAX))}
              rows={5}
              placeholder="Appears on Amazon and in book back matter..."
            />
            <p className="text-xs text-muted-foreground">
              Characters: {bio.length}/{BIO_MAX}
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="pn-photo-url">Author photo URL</Label>
            <Input
              id="pn-photo-url"
              value={photoUrl}
              onChange={(e) => setPhotoUrl(e.target.value)}
              placeholder="https://..."
            />
          </div>

          <div className="space-y-2">
            <Label>Primary genres</Label>
            <div className="flex flex-wrap gap-2">
              {PEN_NAME_GENRES.map((g) => {
                const active = genres.includes(g.value);
                return (
                  <button
                    key={g.value}
                    type="button"
                    onClick={() => toggleGenre(g.value)}
                    className={`rounded-full border px-3 py-1 text-sm transition ${
                      active
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-background text-muted-foreground hover:bg-muted"
                    }`}
                    aria-pressed={active}
                  >
                    {g.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="pn-default"
              checked={isDefault}
              onCheckedChange={(v) => setIsDefault(v === true)}
            />
            <Label htmlFor="pn-default" className="cursor-pointer">
              Set as default pen name
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Saving..." : "Save pen name"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
