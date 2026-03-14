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
import {
  useBookCharacters,
  useCreateCharacter,
  useUpdateCharacter,
  useDeleteCharacter,
  useGenerateReferences,
  type ChildrensBookCharacter,
} from "../hooks";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ReferenceView = "front" | "side" | "happy" | "scared";

const REFERENCE_VIEWS: { key: ReferenceView; label: string }[] = [
  { key: "front", label: "Front View" },
  { key: "side", label: "Side View" },
  { key: "happy", label: "Happy Face" },
  { key: "scared", label: "Scared Face" },
];

/** Local draft state for a character being edited in the form. */
interface CharacterDraft {
  name: string;
  species: string;
  description: string;
  clothingRules: string;
  scaleRules: string;
  settingContinuityRules: string;
  timeofdayRules: string;
  autoAppend: boolean;
}

function draftFromApi(c: ChildrensBookCharacter): CharacterDraft {
  return {
    name: c.name,
    species: c.species ?? "",
    description: c.description,
    clothingRules:
      c.clothing_rules && Object.keys(c.clothing_rules).length > 0
        ? JSON.stringify(c.clothing_rules)
        : "",
    scaleRules:
      c.scale_rules && Object.keys(c.scale_rules).length > 0
        ? JSON.stringify(c.scale_rules)
        : "",
    settingContinuityRules: "",
    timeofdayRules: "",
    autoAppend: c.auto_append,
  };
}

function blankDraft(): CharacterDraft {
  return {
    name: "",
    species: "",
    description: "",
    clothingRules: "",
    scaleRules: "",
    settingContinuityRules: "",
    timeofdayRules: "",
    autoAppend: true,
  };
}

/** Helper to find the reference image URL for a given view from the API array. */
function getReferenceUrl(
  images: string[],
  view: ReferenceView,
): string | null {
  // Convention: images are stored as URLs containing the view name
  const match = images.find((url) => url.includes(view));
  return match ?? null;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CharacterManagerProps {
  bookId: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CharacterManager({ bookId }: CharacterManagerProps) {
  const { data: characters = [], isLoading } = useBookCharacters(bookId);
  const createMutation = useCreateCharacter(bookId);
  const updateMutation = useUpdateCharacter(bookId);
  const deleteMutation = useDeleteCharacter(bookId);
  const generateRefMutation = useGenerateReferences(bookId);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<CharacterDraft>(blankDraft());
  /** Tracks whether the currently selected character is a new unsaved draft */
  const [isNewDraft, setIsNewDraft] = useState(false);
  /** Track which views are currently generating */
  const [generatingViews, setGeneratingViews] = useState<
    Record<string, boolean>
  >({});

  const selected = characters.find((c) => c.id === selectedId) ?? null;

  // ---- helpers ----------------------------------------------------------

  const selectCharacter = (c: ChildrensBookCharacter) => {
    setSelectedId(c.id);
    setDraft(draftFromApi(c));
    setIsNewDraft(false);
  };

  const addCharacter = () => {
    setDraft(blankDraft());
    setSelectedId(null);
    setIsNewDraft(true);
  };

  const updateDraft = (patch: Partial<CharacterDraft>) => {
    setDraft((prev) => ({ ...prev, ...patch }));
  };

  const handleSave = async () => {
    const payload = {
      name: draft.name,
      species: draft.species || undefined,
      description: draft.description,
      auto_append: draft.autoAppend,
      clothing_rules: draft.clothingRules
        ? tryParseJson(draft.clothingRules)
        : undefined,
      scale_rules: draft.scaleRules
        ? tryParseJson(draft.scaleRules)
        : undefined,
    };

    if (isNewDraft || !selected) {
      // Create new character
      const created = await createMutation.mutateAsync(payload);
      setSelectedId(created.id);
      setIsNewDraft(false);
      setDraft(draftFromApi(created));
    } else {
      // Update existing character
      const updated = await updateMutation.mutateAsync({
        characterId: selected.id,
        payload,
      });
      setDraft(draftFromApi(updated));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
    if (selectedId === id) {
      const remaining = characters.filter((c) => c.id !== id);
      if (remaining.length > 0) {
        selectCharacter(remaining[0]);
      } else {
        setSelectedId(null);
        setDraft(blankDraft());
        setIsNewDraft(false);
      }
    }
  };

  const generateReferenceImage = async (
    characterId: string,
    view: ReferenceView,
  ) => {
    const viewKey = `${characterId}-${view}`;
    setGeneratingViews((prev) => ({ ...prev, [viewKey]: true }));
    try {
      await generateRefMutation.mutateAsync({ characterId, view });
    } finally {
      setGeneratingViews((prev) => ({ ...prev, [viewKey]: false }));
    }
  };

  const saving = createMutation.isPending || updateMutation.isPending;
  const showDraftForm = isNewDraft || selected !== null;

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
              {isLoading && (
                <div className="flex justify-center py-6">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              )}

              {!isLoading && characters.length === 0 && !isNewDraft && (
                <p className="text-xs text-muted-foreground text-center py-6">
                  No characters yet. Click + to add one.
                </p>
              )}

              {isNewDraft && (
                <button
                  className="w-full flex items-center gap-2 rounded-md px-2 py-2 text-left text-sm bg-primary/10 text-primary font-medium"
                >
                  <User className="h-4 w-4 flex-shrink-0" />
                  <span className="truncate">
                    {draft.name || "New Character"}
                  </span>
                </button>
              )}

              {characters.map((c) => (
                <button
                  key={c.id}
                  onClick={() => selectCharacter(c)}
                  className={`w-full flex items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors ${
                    !isNewDraft && selectedId === c.id
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
          {!showDraftForm ? (
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
                    value={draft.name}
                    onChange={(e) => updateDraft({ name: e.target.value })}
                    placeholder="e.g. Luna"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-species">Species / Type</Label>
                  <Input
                    id="char-species"
                    value={draft.species}
                    onChange={(e) => updateDraft({ species: e.target.value })}
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
                  value={draft.description}
                  onChange={(e) =>
                    updateDraft({ description: e.target.value })
                  }
                  placeholder="Detailed visual description appended to all illustration prompts..."
                />
              </div>

              {/* Reference Images (4 slots) — only for saved characters */}
              {selected && !isNewDraft && (
                <div className="space-y-2">
                  <Label>Reference Images</Label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {REFERENCE_VIEWS.map((rv) => {
                      const viewKey = `${selected.id}-${rv.key}`;
                      const isGenerating = generatingViews[viewKey] ?? false;
                      const url = getReferenceUrl(
                        selected.reference_images,
                        rv.key,
                      );
                      return (
                        <div
                          key={rv.key}
                          className="border rounded-lg overflow-hidden"
                        >
                          <div className="aspect-square bg-muted flex items-center justify-center relative">
                            {isGenerating ? (
                              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            ) : url ? (
                              <img
                                src={url}
                                alt={rv.label}
                                className="object-cover w-full h-full"
                              />
                            ) : (
                              <ImagePlus className="h-8 w-8 text-muted-foreground/40" />
                            )}
                          </div>
                          <div className="p-2 flex flex-col items-center gap-1">
                            <span className="text-xs text-muted-foreground">
                              {rv.label}
                            </span>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs w-full"
                              disabled={isGenerating}
                              onClick={() =>
                                generateReferenceImage(selected.id, rv.key)
                              }
                            >
                              {isGenerating ? "Generating..." : "Generate"}
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Rules textareas */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="char-clothing">
                    Clothing / Accessory Rules
                  </Label>
                  <Textarea
                    id="char-clothing"
                    rows={3}
                    value={draft.clothingRules}
                    onChange={(e) =>
                      updateDraft({ clothingRules: e.target.value })
                    }
                    placeholder="e.g. Always wears a red collar with a gold bell..."
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-scale">Scale Rules</Label>
                  <Textarea
                    id="char-scale"
                    rows={3}
                    value={draft.scaleRules}
                    onChange={(e) =>
                      updateDraft({ scaleRules: e.target.value })
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
                    value={draft.settingContinuityRules}
                    onChange={(e) =>
                      updateDraft({ settingContinuityRules: e.target.value })
                    }
                    placeholder="e.g. Blue garden gate, stone path, red mailbox..."
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="char-tod">Time-of-Day Rules</Label>
                  <Textarea
                    id="char-tod"
                    rows={3}
                    value={draft.timeofdayRules}
                    onChange={(e) =>
                      updateDraft({ timeofdayRules: e.target.value })
                    }
                    placeholder="e.g. Pages 1-8: morning light, Pages 9-16: golden hour..."
                  />
                </div>
              </div>

              {/* Auto-Append toggle */}
              <div className="flex items-center gap-3">
                <Switch
                  id="char-autoappend"
                  checked={draft.autoAppend}
                  onCheckedChange={(v) => updateDraft({ autoAppend: v })}
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
                  {saving
                    ? "Saving..."
                    : isNewDraft
                      ? "Create Character"
                      : "Save Character"}
                </Button>
                {selected && !isNewDraft && (
                  <Button
                    variant="destructive"
                    disabled={deleteMutation.isPending}
                    onClick={() => handleDelete(selected.id)}
                  >
                    {deleteMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="mr-2 h-4 w-4" />
                    )}
                    Delete
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function tryParseJson(str: string): Record<string, unknown> {
  try {
    return JSON.parse(str);
  } catch {
    // If the user typed plain text, wrap it as a simple object
    return { value: str };
  }
}
