"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Plus, Users, ImagePlus, Loader2, Save } from "lucide-react";
import { useCharacters, useCreateCharacter, useUpdateCharacter, useGenerateCharacterReferences } from "../hooks";
import type { Character } from "../types";

export interface CharacterPanelProps {
  bookId: string;
}

function CharacterCard({
  character,
  bookId,
  isSelected,
  onSelect,
}: {
  character: Character;
  bookId: string;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const { mutate: updateCharacter, isPending: isUpdating } = useUpdateCharacter(bookId);
  const { mutate: generateRefs, isPending: isGeneratingRefs } = useGenerateCharacterReferences(bookId);

  const [name, setName] = useState(character.name);
  const [species, setSpecies] = useState(character.species_type);
  const [description, setDescription] = useState(character.description);
  const [clothingRules, setClothingRules] = useState(character.clothing_rules);
  const [scaleRules, setScaleRules] = useState(character.scale_rules);

  const handleSave = () => {
    updateCharacter({
      characterId: character.id,
      updates: {
        name,
        species_type: species,
        description,
        clothing_rules: clothingRules,
        scale_rules: scaleRules,
      },
    });
  };

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all",
        isSelected ? "ring-2 ring-primary border-primary" : "hover:border-primary/40",
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <h4 className="font-semibold text-sm">{character.name}</h4>
          <span className="text-xs text-muted-foreground">{character.species_type}</span>
        </div>
      </CardHeader>
      {isSelected && (
        <CardContent className="space-y-3" onClick={(e) => e.stopPropagation()}>
          <div>
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} className="h-8 text-sm" />
          </div>
          <div>
            <Label className="text-xs">Species / Type</Label>
            <Input value={species} onChange={(e) => setSpecies(e.target.value)} className="h-8 text-sm" />
          </div>
          <div>
            <Label className="text-xs">Visual Description</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="text-sm" />
          </div>
          <div>
            <Label className="text-xs">Clothing / Accessory Rules</Label>
            <Input value={clothingRules} onChange={(e) => setClothingRules(e.target.value)} className="h-8 text-sm" />
          </div>
          <div>
            <Label className="text-xs">Scale Rules</Label>
            <Input value={scaleRules} onChange={(e) => setScaleRules(e.target.value)} className="h-8 text-sm" />
          </div>

          {/* Reference images */}
          <div>
            <Label className="text-xs">Reference Images</Label>
            <div className="grid grid-cols-4 gap-2 mt-1">
              {(["front", "side", "happy", "scared"] as const).map((view) => (
                <div key={view} className="aspect-square bg-muted rounded-md overflow-hidden flex items-center justify-center">
                  {character.reference_images[view] ? (
                    <img src={character.reference_images[view]} alt={view} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-[10px] text-muted-foreground">{view}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-1">
            <Button size="sm" className="text-xs flex-1" onClick={handleSave} disabled={isUpdating}>
              {isUpdating ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}
              Save
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-xs flex-1"
              onClick={() => generateRefs({ characterId: character.id })}
              disabled={isGeneratingRefs}
            >
              {isGeneratingRefs ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <ImagePlus className="h-3 w-3 mr-1" />}
              Gen Refs
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export function CharacterPanel({ bookId }: CharacterPanelProps) {
  const { data: characters = [], isLoading } = useCharacters(bookId);
  const { mutate: createCharacter, isPending: isCreating } = useCreateCharacter(bookId);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleCreate = () => {
    createCharacter(
      { name: "New Character", species_type: "", description: "", clothing_rules: "", scale_rules: "", setting_continuity: "", time_of_day_rules: "" },
      { onSuccess: (c) => setSelectedId(c.id) },
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Characters ({characters.length})</span>
        </div>
        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={handleCreate} disabled={isCreating}>
          {isCreating ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Plus className="h-3 w-3 mr-1" />}
          Add
        </Button>
      </div>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-3">
          {characters.length === 0 ? (
            <div className="text-center py-8">
              <Users className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No characters yet</p>
              <Button size="sm" variant="outline" className="mt-2 text-xs" onClick={handleCreate}>
                <Plus className="h-3 w-3 mr-1" />
                Add Character
              </Button>
            </div>
          ) : (
            characters.map((c) => (
              <CharacterCard
                key={c.id}
                character={c}
                bookId={bookId}
                isSelected={selectedId === c.id}
                onSelect={() => setSelectedId(selectedId === c.id ? null : c.id)}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
