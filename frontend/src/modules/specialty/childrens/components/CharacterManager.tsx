"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Plus,
  Trash2,
  Save,
  ImagePlus,
  Loader2,
  User,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ReferenceView = "front" | "side" | "happy" | "scared";

interface ReferenceImage {
  view: ReferenceView;
  url: string | null;
  generating: boolean;
}

interface Character {
  id: string;
  name: string;
  species: string;
  description: string;
  referenceImages: ReferenceImage[];
  clothingRules: string;
  scaleRules: string;
  settingContinuityRules: string;
  timeofdayRules: string;
  autoAppend: boolean;
}

const REFERENCE_VIEWS: { key: ReferenceView; label: string }[] = [
  { key: "front", label: "Front View" },
  { key: "side", label: "Side View" },
  { key: "happy", label: "Happy Face" },
  { key: "scared", label: "Scared Face" },
];

function createBlankCharacter(): Character {
  return {
    id: crypto.randomUUID(),
    name: "",
    species: "",
    description: "",
    referenceImages: REFERENCE_VIEWS.map((v) => ({
      view: v.key,
      url: null,
      generating: false,
    })),
    clothingRules: "",
    scaleRules: "",
    settingContinuityRules: "",
    timeofdayRules: "",
    autoAppend: true,
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CharacterManager() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const selected = characters.find((c) => c.id === selectedId) ?? null;

  // ---- helpers ----------------------------------------------------------

  const addCharacter = () => {
    const c = createBlankCharacter();
    setCharacters((prev) => [...prev, c]);
    setSelectedId(c.id);
  };

  const updateCharacter = (id: string, patch: Partial<Character>) => {
    setCharacters((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...patch } : c))
    );
  };

  const deleteCharacter = (id: string) => {
    setCharacters((prev) => prev.filter((c) => c.id !== id));
    if (selectedId === id) {
      setSelectedId(characters.find((c) => c.id !== id)?.id ?? null);
    }
  };

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    // TODO: persist via API  POST /api/v1/specialty/childrens-books/{bookId}/characters
    await new Promise((r) => setTimeout(r, 600));
    setSaving(false);
  };

  const generateReferenceImage = async (
    characterId: string,
    view: ReferenceView
  ) => {
    setCharacters((prev) =>
      prev.map((c) => {
        if (c.id !== characterId) return c;
        return {
          ...c,
          referenceImages: c.referenceImages.map((ri) =>
            ri.view === view ? { ...ri, generating: true } : ri
          ),
        };
      })
    );

    // TODO: call API  POST /api/v1/specialty/childrens-books/{bookId}/characters/{charId}/generate-references
    await new Promise((r) => setTimeout(r, 1500));

    setCharacters((prev) =>
      prev.map((c) => {
        if (c.id !== characterId) return c;
        return {
          ...c,
          referenceImages: c.referenceImages.map((ri) =>
            ri.view === view
              ? { ...ri, generating: false, url: `/placeholder-${view}.png` }
              : ri
          ),
        };
      })
    );
  };

  // ---- render -----------------------------------------------------------

  return (
    <div className="flex h-full gap-4">
      {/* ---- Sidebar: Character list ---- */}
      <Card className="w-64 flex-shrink-0">
        <CardContent className="p-3 flex flex-col h-full">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Characters</h3>
            <Button size="icon" variant="ghost" onClick={addCharacter}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <Separator className="mb-3" />

          <ScrollArea className="flex-1">
            <div className="space-y-1">
              {characters.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-6">
                  No characters yet. Click + to add one.
                </p>
              )}

              {characters.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full flex items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors ${
                    selectedId === c.id
                      ? "bg-primary/10 text-primary font-medium"
                      : "hover:bg-muted"
                  }`}
                >
                  <User className="h-4 w-4 flex-shrink-0" />
                  <span className="truncate">
                    {c.name || "Unnamed Character"}
                  </span>
                </button>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* ---- Detail panel ---- */}
      <Card className="flex-1 overflow-auto">
        <CardContent className="p-6">
          {!selected ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <User className="h-12 w-12 mb-3 opacity-40" />
              <p className="text-sm">
                Select or add a character to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Name + Species */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="char-name">Name</Label>
                  <Input
                    id="char-name"
                    value={selected.name}
                    onChange={(e) =>
                      updateCharacter(selected.id, { name: e.target.value })
                    }
                    placeholder="e.g. Luna"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-species">Species / Type</Label>
                  <Input
                    id="char-species"
                    value={selected.species}
                    onChange={(e) =>
                      updateCharacter(selected.id, { species: e.target.value })
                    }
                    placeholder="e.g. orange tabby kitten"
                  />
                </div>
              </div>

              {/* Description */}
              <div className="space-y-1.5">
                <Label htmlFor="char-desc">Description</Label>
                <Textarea
                  id="char-desc"
                  rows={4}
                  value={selected.description}
                  onChange={(e) =>
                    updateCharacter(selected.id, {
                      description: e.target.value,
                    })
                  }
                  placeholder="Detailed visual description appended to all illustration prompts..."
                />
              </div>

              {/* Reference Images (4 slots) */}
              <div className="space-y-2">
                <Label>Reference Images</Label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {selected.referenceImages.map((ri) => {
                    const viewLabel =
                      REFERENCE_VIEWS.find((v) => v.key === ri.view)?.label ??
                      ri.view;
                    return (
                      <div
                        key={ri.view}
                        className="border rounded-lg overflow-hidden"
                      >
                        <div className="aspect-square bg-muted flex items-center justify-center relative">
                          {ri.generating ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                          ) : ri.url ? (
                            <img
                              src={ri.url}
                              alt={viewLabel}
                              className="object-cover w-full h-full"
                            />
                          ) : (
                            <ImagePlus className="h-8 w-8 text-muted-foreground/40" />
                          )}
                        </div>
                        <div className="p-2 flex flex-col items-center gap-1">
                          <span className="text-xs text-muted-foreground">
                            {viewLabel}
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs w-full"
                            disabled={ri.generating}
                            onClick={() =>
                              generateReferenceImage(selected.id, ri.view)
                            }
                          >
                            {ri.generating ? "Generating..." : "Generate"}
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Rules textareas */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="char-clothing">
                    Clothing / Accessory Rules
                  </Label>
                  <Textarea
                    id="char-clothing"
                    rows={3}
                    value={selected.clothingRules}
                    onChange={(e) =>
                      updateCharacter(selected.id, {
                        clothingRules: e.target.value,
                      })
                    }
                    placeholder="e.g. Always wears a red collar with a gold bell..."
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-scale">Scale Rules</Label>
                  <Textarea
                    id="char-scale"
                    rows={3}
                    value={selected.scaleRules}
                    onChange={(e) =>
                      updateCharacter(selected.id, {
                        scaleRules: e.target.value,
                      })
                    }
                    placeholder="e.g. Half the height of the main human character..."
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-setting">
                    Setting Continuity Rules
                  </Label>
                  <Textarea
                    id="char-setting"
                    rows={3}
                    value={selected.settingContinuityRules}
                    onChange={(e) =>
                      updateCharacter(selected.id, {
                        settingContinuityRules: e.target.value,
                      })
                    }
                    placeholder="e.g. Blue garden gate, stone path, red mailbox..."
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-tod">Time-of-Day Rules</Label>
                  <Textarea
                    id="char-tod"
                    rows={3}
                    value={selected.timeofdayRules}
                    onChange={(e) =>
                      updateCharacter(selected.id, {
                        timeofdayRules: e.target.value,
                      })
                    }
                    placeholder="e.g. Pages 1-8: morning light, Pages 9-16: golden hour..."
                  />
                </div>
              </div>

              {/* Auto-Append toggle */}
              <div className="flex items-center gap-3">
                <Switch
                  id="char-autoappend"
                  checked={selected.autoAppend}
                  onCheckedChange={(v) =>
                    updateCharacter(selected.id, { autoAppend: v })
                  }
                />
                <Label htmlFor="char-autoappend" className="cursor-pointer">
                  Auto-append description to all illustration prompts
                </Label>
              </div>

              <Separator />

              {/* Save / Delete */}
              <div className="flex items-center gap-3">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  {saving ? "Saving..." : "Save Character"}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => deleteCharacter(selected.id)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
