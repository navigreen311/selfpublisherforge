"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { CheckCircle2, Plus, Trash2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Wizard Data
// ---------------------------------------------------------------------------

export interface WizardData {
  // Step 1: Details
  title: string;
  subtitle: string;
  author: string;
  artist: string;
  format: string;
  target_audience: string;

  // Step 2: Art Style
  page_count: string;
  trim_size: string;
  art_style: string;
  color_mode: string;
  ink_style: string;
  border_style: string;
  gutter_style: string;

  // Step 3: Story & Characters
  genre: string;
  premise: string;
  pacing: string;
  characters: Array<{ name: string; role: string; description: string }>;

  // Step 4: Content Settings
  content_rating: string;
  violence_level: string;
  language_level: string;
  safety_no_gore: boolean;
  safety_no_explicit: boolean;
  safety_no_hate: boolean;
  safety_age_appropriate: boolean;
}

export const DEFAULT_WIZARD_DATA: WizardData = {
  title: "",
  subtitle: "",
  author: "",
  artist: "",
  format: "graphic_novel",
  target_audience: "all_ages",

  page_count: "24",
  trim_size: "6.625x10.25",
  art_style: "american_classic",
  color_mode: "full_color",
  ink_style: "clean",
  border_style: "solid",
  gutter_style: "standard",

  genre: "",
  premise: "",
  pacing: "balanced",
  characters: [],

  content_rating: "everyone",
  violence_level: "none",
  language_level: "clean",
  safety_no_gore: true,
  safety_no_explicit: true,
  safety_no_hate: true,
  safety_age_appropriate: true,
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const FORMATS = [
  { value: "single_issue", label: "Single Issue", desc: "22-32 pages, serialized" },
  { value: "graphic_novel", label: "Graphic Novel", desc: "Long-form, self-contained" },
  { value: "manga", label: "Manga", desc: "Japanese-style, right-to-left" },
  { value: "webcomic", label: "Webcomic", desc: "Digital-first, scroll format" },
  { value: "mini_series", label: "Mini Series", desc: "Limited run, 4-12 issues" },
  { value: "one_shot", label: "One-Shot", desc: "Single standalone issue" },
  { value: "trade_paperback", label: "Trade Paperback", desc: "Collected edition" },
];

const TARGET_AUDIENCES = [
  { value: "all_ages", label: "All Ages", desc: "Suitable for everyone" },
  { value: "kids", label: "Kids (6-12)", desc: "Child-friendly content" },
  { value: "teen", label: "Teen (13-17)", desc: "Mild action & themes" },
  { value: "young_adult", label: "Young Adult (16-25)", desc: "Complex themes" },
  { value: "mature", label: "Mature (18+)", desc: "Adult content" },
];

const PAGE_COUNTS = ["8", "12", "16", "22", "24", "32", "48", "64", "100", "150", "200"];

const TRIM_SIZES = [
  { value: "6.625x10.25", label: '6.625" x 10.25" (Standard Comic)' },
  { value: "6x9", label: '6" x 9" (Digest)' },
  { value: "7x10.5", label: '7" x 10.5" (Magazine)' },
  { value: "5.5x8.5", label: '5.5" x 8.5" (Manga)' },
  { value: "8.5x11", label: '8.5" x 11" (Full Size)' },
];

const ART_STYLES = [
  { value: "american_classic", label: "American Classic", desc: "Bold lines, dynamic poses" },
  { value: "manga", label: "Manga", desc: "Japanese comic art style" },
  { value: "franco_belgian", label: "Franco-Belgian", desc: "European album style" },
  { value: "indie", label: "Indie", desc: "Alternative, experimental" },
  { value: "cartoon", label: "Cartoon", desc: "Fun, exaggerated proportions" },
  { value: "realistic", label: "Realistic", desc: "Photo-realistic rendering" },
  { value: "noir", label: "Noir", desc: "High contrast, shadow-heavy" },
  { value: "watercolor", label: "Watercolor", desc: "Painted, fluid aesthetic" },
  { value: "pixel_art", label: "Pixel Art", desc: "Retro digital style" },
  { value: "minimalist", label: "Minimalist", desc: "Clean, sparse design" },
];

const COLOR_MODES = [
  { value: "full_color", label: "Full Color", desc: "Complete color palette" },
  { value: "grayscale", label: "Grayscale", desc: "Shades of gray" },
  { value: "black_white", label: "Black & White", desc: "Pure ink, no tones" },
  { value: "duotone", label: "Duotone", desc: "Two-color scheme" },
  { value: "limited_palette", label: "Limited Palette", desc: "3-5 colors only" },
  { value: "spot_color", label: "Spot Color", desc: "B&W with color accents" },
];

const INK_STYLES = [
  { value: "clean", label: "Clean" },
  { value: "hatching", label: "Hatching" },
  { value: "cross_hatching", label: "Cross-Hatching" },
  { value: "brush", label: "Brush" },
  { value: "digital", label: "Digital" },
  { value: "woodcut", label: "Woodcut" },
  { value: "stipple", label: "Stipple" },
];

const BORDER_STYLES = [
  { value: "solid", label: "Solid" },
  { value: "dashed", label: "Dashed" },
  { value: "wavy", label: "Wavy" },
  { value: "jagged", label: "Jagged" },
  { value: "none", label: "None" },
  { value: "double", label: "Double" },
  { value: "rough", label: "Rough" },
];

const GUTTER_STYLES = [
  { value: "standard", label: "Standard" },
  { value: "narrow", label: "Narrow" },
  { value: "wide", label: "Wide" },
  { value: "none", label: "None" },
  { value: "bleeding", label: "Bleeding" },
];

const PACING_OPTIONS = [
  { value: "action", label: "Action", desc: "Fast-paced, fight sequences" },
  { value: "dialogue_heavy", label: "Dialogue Heavy", desc: "Character-driven conversations" },
  { value: "balanced", label: "Balanced", desc: "Mix of action and dialogue" },
  { value: "cinematic", label: "Cinematic", desc: "Wide panels, atmosphere" },
  { value: "decompressed", label: "Decompressed", desc: "Slow-burn, detailed moments" },
  { value: "compressed", label: "Compressed", desc: "Dense, many panels per page" },
];

const CHARACTER_ROLES = [
  { value: "hero", label: "Hero" },
  { value: "villain", label: "Villain" },
  { value: "supporting", label: "Supporting" },
  { value: "narrator", label: "Narrator" },
];

const CONTENT_RATINGS = [
  { value: "everyone", label: "Everyone", desc: "Suitable for all readers" },
  { value: "teen", label: "Teen", desc: "Some action, mild themes" },
  { value: "mature", label: "Mature", desc: "Adult themes and content" },
];

const VIOLENCE_LEVELS = [
  { value: "none", label: "None" },
  { value: "mild", label: "Mild (cartoon)" },
  { value: "moderate", label: "Moderate (action)" },
  { value: "intense", label: "Intense" },
];

const LANGUAGE_LEVELS = [
  { value: "clean", label: "Clean" },
  { value: "mild", label: "Mild" },
  { value: "moderate", label: "Moderate" },
  { value: "strong", label: "Strong" },
];

// ---------------------------------------------------------------------------
// Shared Props
// ---------------------------------------------------------------------------

interface StepProps {
  data: WizardData;
  onChange: (updates: Partial<WizardData>) => void;
}

// ---------------------------------------------------------------------------
// Step 1: Book Details
// ---------------------------------------------------------------------------

export function Step1BookDetails({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Book Details</h2>
        <p className="text-sm text-muted-foreground">
          Define the basics of your comic book.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="space-y-2">
          <Label htmlFor="title">
            Title <span className="text-destructive">*</span>
          </Label>
          <Input
            id="title"
            placeholder="Enter comic book title"
            value={data.title}
            onChange={(e) => onChange({ title: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="subtitle">Subtitle</Label>
          <Input
            id="subtitle"
            placeholder="Optional subtitle or issue tagline"
            value={data.subtitle}
            onChange={(e) => onChange({ subtitle: e.target.value })}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="author">Author / Writer</Label>
            <Input
              id="author"
              placeholder="Writer name"
              value={data.author}
              onChange={(e) => onChange({ author: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="artist">Artist / Illustrator</Label>
            <Input
              id="artist"
              placeholder="Artist name"
              value={data.artist}
              onChange={(e) => onChange({ artist: e.target.value })}
            />
          </div>
        </div>
      </div>

      {/* Format */}
      <div className="space-y-3">
        <Label>Format</Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {FORMATS.map((fmt) => (
            <Card
              key={fmt.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.format === fmt.value && "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ format: fmt.value })}
            >
              <p className="text-sm font-medium">{fmt.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {fmt.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Target Audience */}
      <div className="space-y-3">
        <Label>
          Target Audience <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {TARGET_AUDIENCES.map((aud) => (
            <Card
              key={aud.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.target_audience === aud.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ target_audience: aud.value })}
            >
              <p className="text-sm font-medium">{aud.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {aud.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2: Art Style
// ---------------------------------------------------------------------------

export function Step2ArtStyle({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Art Style</h2>
        <p className="text-sm text-muted-foreground">
          Choose the visual style and format for your comic.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Page Count</Label>
          <Select
            value={data.page_count}
            onValueChange={(v) => onChange({ page_count: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select page count" />
            </SelectTrigger>
            <SelectContent>
              {PAGE_COUNTS.map((p) => (
                <SelectItem key={p} value={p}>
                  {p} pages
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Trim Size</Label>
          <Select
            value={data.trim_size}
            onValueChange={(v) => onChange({ trim_size: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select trim size" />
            </SelectTrigger>
            <SelectContent>
              {TRIM_SIZES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Art Style */}
      <div className="space-y-3">
        <Label>Art Style</Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {ART_STYLES.map((style) => (
            <Card
              key={style.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.art_style === style.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ art_style: style.value })}
            >
              <p className="text-sm font-medium">{style.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {style.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Color Mode */}
      <div className="space-y-3">
        <Label>Color Mode</Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {COLOR_MODES.map((mode) => (
            <Card
              key={mode.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.color_mode === mode.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ color_mode: mode.value })}
            >
              <p className="text-sm font-medium">{mode.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {mode.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label>Ink Style</Label>
          <Select
            value={data.ink_style}
            onValueChange={(v) => onChange({ ink_style: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select ink style" />
            </SelectTrigger>
            <SelectContent>
              {INK_STYLES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Border Style</Label>
          <Select
            value={data.border_style}
            onValueChange={(v) => onChange({ border_style: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select border style" />
            </SelectTrigger>
            <SelectContent>
              {BORDER_STYLES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Gutter Style</Label>
          <Select
            value={data.gutter_style}
            onValueChange={(v) => onChange({ gutter_style: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select gutter style" />
            </SelectTrigger>
            <SelectContent>
              {GUTTER_STYLES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3: Story & Characters
// ---------------------------------------------------------------------------

export function Step3StoryCharacters({ data, onChange }: StepProps) {
  const addCharacter = () => {
    onChange({
      characters: [
        ...data.characters,
        { name: "", role: "hero", description: "" },
      ],
    });
  };

  const removeCharacter = (index: number) => {
    onChange({
      characters: data.characters.filter((_, i) => i !== index),
    });
  };

  const updateCharacter = (
    index: number,
    field: keyof (typeof data.characters)[0],
    value: string,
  ) => {
    const updated = data.characters.map((c, i) =>
      i === index ? { ...c, [field]: value } : c,
    );
    onChange({ characters: updated });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Story & Characters</h2>
        <p className="text-sm text-muted-foreground">
          Define your story premise and cast of characters.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="space-y-2">
          <Label htmlFor="genre">Genre</Label>
          <Input
            id="genre"
            placeholder='e.g., Superhero, Sci-Fi, Fantasy, Horror, Slice-of-Life'
            value={data.genre}
            onChange={(e) => onChange({ genre: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="premise">Premise</Label>
          <Textarea
            id="premise"
            placeholder="Brief story premise or synopsis..."
            value={data.premise}
            onChange={(e) => onChange({ premise: e.target.value })}
            rows={4}
          />
        </div>
      </div>

      {/* Pacing */}
      <div className="space-y-3">
        <Label>Pacing</Label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {PACING_OPTIONS.map((opt) => (
            <Card
              key={opt.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.pacing === opt.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ pacing: opt.value })}
            >
              <p className="text-sm font-medium">{opt.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {opt.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Characters */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Characters</Label>
          <Button variant="outline" size="sm" onClick={addCharacter}>
            <Plus className="h-4 w-4 mr-1" />
            Add Character
          </Button>
        </div>

        {data.characters.length === 0 && (
          <p className="text-sm text-muted-foreground italic">
            No characters added yet. Click &quot;Add Character&quot; to get
            started.
          </p>
        )}

        <div className="space-y-3">
          {data.characters.map((char, index) => (
            <Card key={index} className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">
                  Character {index + 1}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeCharacter(index)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Remove
                </Button>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input
                    placeholder="Character name"
                    value={char.name}
                    onChange={(e) =>
                      updateCharacter(index, "name", e.target.value)
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select
                    value={char.role}
                    onValueChange={(v) => updateCharacter(index, "role", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      {CHARACTER_ROLES.map((r) => (
                        <SelectItem key={r.value} value={r.value}>
                          {r.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  placeholder="Visual description, personality, powers..."
                  value={char.description}
                  onChange={(e) =>
                    updateCharacter(index, "description", e.target.value)
                  }
                  rows={2}
                />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 4: Content Settings
// ---------------------------------------------------------------------------

export function Step4ContentSettings({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Content Settings</h2>
        <p className="text-sm text-muted-foreground">
          Configure content rating and safety settings for your comic.
        </p>
      </div>

      {/* Content Rating */}
      <div className="space-y-3">
        <Label>Content Rating</Label>
        <div className="grid grid-cols-3 gap-3">
          {CONTENT_RATINGS.map((rating) => (
            <Card
              key={rating.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.content_rating === rating.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ content_rating: rating.value })}
            >
              <p className="text-sm font-medium">{rating.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {rating.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Violence Level</Label>
          <Select
            value={data.violence_level}
            onValueChange={(v) => onChange({ violence_level: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select violence level" />
            </SelectTrigger>
            <SelectContent>
              {VIOLENCE_LEVELS.map((v) => (
                <SelectItem key={v.value} value={v.value}>
                  {v.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Language Level</Label>
          <Select
            value={data.language_level}
            onValueChange={(v) => onChange({ language_level: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select language level" />
            </SelectTrigger>
            <SelectContent>
              {LANGUAGE_LEVELS.map((l) => (
                <SelectItem key={l.value} value={l.value}>
                  {l.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Safety Toggles */}
      <div className="space-y-1">
        <Label className="text-sm font-medium">Safety Rules</Label>
        <p className="text-xs text-muted-foreground mb-3">
          Enable safety guardrails for content generation.
        </p>

        <div className="space-y-3">
          {[
            {
              key: "safety_no_gore" as const,
              label: "No graphic gore",
            },
            {
              key: "safety_no_explicit" as const,
              label: "No explicit content",
            },
            {
              key: "safety_no_hate" as const,
              label: "No hate speech / discrimination",
            },
            {
              key: "safety_age_appropriate" as const,
              label: "Age-appropriate content enforcement",
            },
          ].map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between rounded-md border p-3"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2
                  className={cn(
                    "h-4 w-4",
                    data[item.key]
                      ? "text-green-500"
                      : "text-muted-foreground",
                  )}
                />
                <span className="text-sm">{item.label}</span>
              </div>
              <Switch
                checked={data[item.key]}
                onCheckedChange={(v) => onChange({ [item.key]: v })}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
