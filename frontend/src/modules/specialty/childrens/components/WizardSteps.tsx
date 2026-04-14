"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { StyleClonePicker } from "@/modules/specialty/style-clone/components/StyleClonePicker";
import { PenNameSelect } from "@/modules/pen-names/components/PenNameSelect";
import { usePenNames } from "@/modules/pen-names/hooks";
import {
  Select as FallbackSelect,
  SelectContent as FallbackSelectContent,
  SelectItem as FallbackSelectItem,
  SelectTrigger as FallbackSelectTrigger,
  SelectValue as FallbackSelectValue,
} from "@/components/ui/select";

function ChildrensAuthorField({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const { data: penNames = [] } = usePenNames();
  if (penNames.length === 0) {
    return (
      <FallbackSelect value={value} onValueChange={onChange}>
        <FallbackSelectTrigger id="author">
          <FallbackSelectValue placeholder="Select author or pen name" />
        </FallbackSelectTrigger>
        <FallbackSelectContent>
          <FallbackSelectItem value="self">My Name</FallbackSelectItem>
          <FallbackSelectItem value="pen-name">Pen Name</FallbackSelectItem>
        </FallbackSelectContent>
      </FallbackSelect>
    );
  }
  const selected = penNames.find((p) => p.display_name === value);
  return (
    <PenNameSelect
      value={selected?.id ?? null}
      onChange={(id) => {
        const match = penNames.find((p) => p.id === id);
        if (match) onChange(match.display_name);
      }}
    />
  );
}
import {
  Droplets,
  Smile,
  Layers,
  BookOpen,
  Paintbrush,
  Camera,
  Pencil,
  Scissors,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Wizard Data Type
// ---------------------------------------------------------------------------

export interface WizardData {
  // Step 1
  title: string;
  subtitle: string;
  author: string;
  age_range: string;
  is_bilingual: boolean;
  bilingual_language: string;
  bilingual_layout: string;
  // Step 2
  page_count: string;
  trim_size: string;
  illustration_style: string;
  color_palette: string;
  style_clone_id: string;
  // Step 3
  creation_mode: string;
  story_prompt: string;
  theme_moral: string;
  main_character: string;
  setting: string;
  tone: string;
  story_mode: string;
  // Step 4
  fear_intensity: string;
  safety_no_weapons: boolean;
  safety_no_scary: boolean;
  safety_no_trademarks: boolean;
  safety_no_stereotypes: boolean;
  safety_age_vocabulary: boolean;
  safety_trademark_enforcement: boolean;
  safety_content_precheck: boolean;
  safety_provenance_logging: boolean;
}

export const DEFAULT_WIZARD_DATA: WizardData = {
  title: "",
  subtitle: "",
  author: "",
  age_range: "",
  is_bilingual: false,
  bilingual_language: "",
  bilingual_layout: "side-by-side",
  page_count: "",
  trim_size: "",
  illustration_style: "",
  color_palette: "",
  style_clone_id: "",
  creation_mode: "ai-generate",
  story_prompt: "",
  theme_moral: "",
  main_character: "",
  setting: "",
  tone: "",
  story_mode: "prose",
  fear_intensity: "none",
  safety_no_weapons: true,
  safety_no_scary: true,
  safety_no_trademarks: true,
  safety_no_stereotypes: true,
  safety_age_vocabulary: true,
  safety_trademark_enforcement: true,
  safety_content_precheck: true,
  safety_provenance_logging: true,
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AGE_RANGES = [
  {
    value: "board",
    label: "Board Book",
    ages: "0-3",
    pages: "10-16 pages",
    icon: BookOpen,
  },
  {
    value: "picture",
    label: "Picture Book",
    ages: "3-5",
    pages: "24-32 pages",
    icon: Paintbrush,
  },
  {
    value: "early_reader",
    label: "Early Reader",
    ages: "5-8",
    pages: "32-48 pages",
    icon: Sparkles,
  },
  {
    value: "chapter",
    label: "Chapter Book",
    ages: "8-12",
    pages: "48-80 pages",
    icon: Layers,
  },
];

const PAGE_COUNT_OPTIONS: Record<string, string[]> = {
  board: ["10", "12", "14", "16"],
  picture: ["24", "28", "32"],
  early_reader: ["32", "36", "40", "48"],
  chapter: ["48", "56", "64", "72", "80"],
};

const TRIM_SIZES = [
  { value: "8.5x8.5", label: '8.5" x 8.5" (Square)' },
  { value: "8.5x11", label: '8.5" x 11" (Portrait)' },
  { value: "10x8", label: '10" x 8" (Landscape)' },
  { value: "6x9", label: '6" x 9" (Chapter)' },
];

const ILLUSTRATION_STYLES = [
  { value: "watercolor", label: "Watercolor", icon: Droplets },
  { value: "cartoon", label: "Cartoon", icon: Smile },
  { value: "flat", label: "Flat Vector", icon: Layers },
  { value: "storybook", label: "Storybook", icon: BookOpen },
  { value: "realistic", label: "Realistic", icon: Camera },
  { value: "crayon-pencil", label: "Crayon/Pencil", icon: Pencil },
  { value: "collage", label: "Collage", icon: Scissors },
  { value: "anime-manga", label: "Anime/Manga", icon: Sparkles },
];

const COLOR_PALETTES = [
  "Bright & Vibrant",
  "Soft & Pastel",
  "Warm & Earthy",
  "Cool & Dreamy",
  "Monochrome + Accent",
];

const TONES = [
  "Warm & reassuring",
  "Exciting",
  "Humorous",
  "Educational",
];

const BILINGUAL_LANGUAGES = [
  "Spanish",
  "French",
  "German",
  "Portuguese",
  "Chinese Simplified",
  "Chinese Traditional",
  "Japanese",
  "Korean",
  "Italian",
  "Hindi",
  "Arabic",
  "Russian",
  "Other",
];

// ---------------------------------------------------------------------------
// Step 1: Book Details
// ---------------------------------------------------------------------------

interface StepProps {
  data: WizardData;
  onChange: (updates: Partial<WizardData>) => void;
}

export function Step1BookDetails({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Book Details</h2>
        <p className="text-sm text-muted-foreground">
          Define the basics of your children&apos;s book.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="space-y-2">
          <Label htmlFor="title">
            Title <span className="text-destructive">*</span>
          </Label>
          <Input
            id="title"
            placeholder="Enter book title"
            value={data.title}
            onChange={(e) => onChange({ title: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="subtitle">Subtitle</Label>
          <Input
            id="subtitle"
            placeholder="Optional subtitle"
            value={data.subtitle}
            onChange={(e) => onChange({ subtitle: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="author">Author</Label>
          {/*
           * Stream 1 (Final Gaps) — use the reusable PenNameSelect so the
           * children's wizard pulls from the real pen_names API. Falls back
           * to the legacy two-option dropdown if no pen names exist yet.
           */}
          <ChildrensAuthorField
            value={data.author}
            onChange={(v) => onChange({ author: v })}
          />
        </div>
      </div>

      {/* Age Range Card Selector */}
      <div className="space-y-3">
        <Label>
          Age Range <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 gap-3">
          {AGE_RANGES.map((range) => {
            const Icon = range.icon;
            const isSelected = data.age_range === range.value;
            return (
              <Card
                key={range.value}
                className={cn(
                  "p-4 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                  isSelected && "ring-2 ring-primary bg-primary/5",
                )}
                onClick={() =>
                  onChange({ age_range: range.value, page_count: "" })
                }
              >
                <div className="flex items-start gap-3">
                  <Icon className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-sm">{range.label}</p>
                    <p className="text-xs text-muted-foreground">
                      Ages {range.ages}
                    </p>
                    <Badge variant="outline" className="mt-1 text-[10px]">
                      {range.pages}
                    </Badge>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Bilingual Toggle */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Bilingual Edition</Label>
            <p className="text-xs text-muted-foreground">
              Create a dual-language book
            </p>
          </div>
          <Switch
            checked={data.is_bilingual}
            onCheckedChange={(v) => onChange({ is_bilingual: v })}
          />
        </div>

        {data.is_bilingual && (
          <div className="grid gap-4 pl-4 border-l-2 border-primary/20">
            <div className="space-y-2">
              <Label>Second Language</Label>
              <Select
                value={data.bilingual_language}
                onValueChange={(v) => onChange({ bilingual_language: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  {BILINGUAL_LANGUAGES.map((lang) => (
                    <SelectItem key={lang} value={lang.toLowerCase()}>
                      {lang}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Layout</Label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: "side-by-side", label: "Side-by-side" },
                  { value: "alternating", label: "Alternating" },
                  { value: "back-section", label: "Back section" },
                ].map((opt) => (
                  <Card
                    key={opt.value}
                    className={cn(
                      "p-2 text-center text-xs cursor-pointer transition-all hover:ring-1 hover:ring-primary/50",
                      data.bilingual_layout === opt.value &&
                        "ring-2 ring-primary bg-primary/5",
                    )}
                    onClick={() => onChange({ bilingual_layout: opt.value })}
                  >
                    {opt.label}
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2: Format & Style
// ---------------------------------------------------------------------------

export function Step2FormatStyle({ data, onChange }: StepProps) {
  const pageOptions = data.age_range
    ? PAGE_COUNT_OPTIONS[data.age_range] ?? []
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Format & Style</h2>
        <p className="text-sm text-muted-foreground">
          Choose the physical format and visual style for your book.
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
              {pageOptions.map((p) => (
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

      {/* Illustration Style Card Selector */}
      <div className="space-y-3">
        <Label>Illustration Style</Label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {ILLUSTRATION_STYLES.map((style) => {
            const Icon = style.icon;
            const isSelected = data.illustration_style === style.value;
            return (
              <Card
                key={style.value}
                className={cn(
                  "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50 text-center",
                  isSelected && "ring-2 ring-primary bg-primary/5",
                )}
                onClick={() => onChange({ illustration_style: style.value })}
              >
                <Icon className="h-6 w-6 mx-auto mb-1.5 text-primary" />
                <p className="text-xs font-medium">{style.label}</p>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Color Palette */}
      <div className="space-y-2">
        <Label>Color Palette</Label>
        <Select
          value={data.color_palette}
          onValueChange={(v) => onChange({ color_palette: v })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select color palette" />
          </SelectTrigger>
          <SelectContent>
            {COLOR_PALETTES.map((p) => (
              <SelectItem key={p} value={p.toLowerCase().replace(/\s+/g, "-")}>
                {p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Style Clone */}
      <div className="space-y-2">
        <Label>Style Clone (Optional)</Label>
        <p className="text-xs text-muted-foreground">
          Apply a saved illustration style profile to keep art consistent.
        </p>
        <StyleClonePicker
          value={data.style_clone_id || undefined}
          onChange={(id: string | undefined) => onChange({ style_clone_id: id ?? "" })}
          bookType="childrens"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3: Story Setup
// ---------------------------------------------------------------------------

export function Step3StorySetup({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Story Setup</h2>
        <p className="text-sm text-muted-foreground">
          Define the story content and generation mode.
        </p>
      </div>

      {/* Creation Mode */}
      <div className="space-y-3">
        <Label>Creation Mode</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              value: "ai-generate",
              label: "AI Generate Full Story",
              desc: "AI writes the complete story",
            },
            {
              value: "write-own",
              label: "Write My Own",
              desc: "Write your own text",
            },
            {
              value: "import",
              label: "Import Text",
              desc: "Paste or upload text",
            },
          ].map((mode) => (
            <Card
              key={mode.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.creation_mode === mode.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ creation_mode: mode.value })}
            >
              <p className="text-sm font-medium">{mode.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {mode.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Story Prompt (AI mode) */}
      {data.creation_mode === "ai-generate" && (
        <div className="space-y-2">
          <Label htmlFor="story-prompt">Story Prompt</Label>
          <Textarea
            id="story-prompt"
            placeholder="Describe the story you want AI to generate..."
            value={data.story_prompt}
            onChange={(e) => onChange({ story_prompt: e.target.value })}
            rows={4}
          />
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="theme-moral">Theme / Moral</Label>
          <Input
            id="theme-moral"
            placeholder="e.g., Courage / Overcoming fears"
            value={data.theme_moral}
            onChange={(e) => onChange({ theme_moral: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="main-character">Main Character</Label>
          <Input
            id="main-character"
            placeholder="e.g., Luna - a small orange tabby kitten"
            value={data.main_character}
            onChange={(e) => onChange({ main_character: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="setting">Setting</Label>
          <Input
            id="setting"
            placeholder="e.g., A cozy village with gardens and woods"
            value={data.setting}
            onChange={(e) => onChange({ setting: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label>Tone</Label>
          <Select
            value={data.tone}
            onValueChange={(v) => onChange({ tone: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select tone" />
            </SelectTrigger>
            <SelectContent>
              {TONES.map((t) => (
                <SelectItem
                  key={t}
                  value={t.toLowerCase().replace(/\s+&\s+/g, "-")}
                >
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Story Mode */}
      <div className="space-y-3">
        <Label>Story Mode</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: "prose", label: "Prose", desc: "Standard narrative" },
            {
              value: "rhyming",
              label: "Rhyming",
              desc: "AABB or ABAB patterns",
            },
            {
              value: "repetitive",
              label: "Repetitive-Cumulative",
              desc: 'Build-up pattern (e.g., "Brown Bear")',
            },
          ].map((mode) => (
            <Card
              key={mode.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.story_mode === mode.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ story_mode: mode.value })}
            >
              <p className="text-sm font-medium">{mode.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {mode.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 4: Content Safety
// ---------------------------------------------------------------------------

export function Step4ContentSafety({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Content Safety</h2>
        <p className="text-sm text-muted-foreground">
          Configure content safety settings for your book.
        </p>
      </div>

      {/* Fear Intensity */}
      <div className="space-y-3">
        <Label>Fear Intensity Level</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: "none", label: "None", desc: "No fear elements" },
            {
              value: "mild",
              label: "Mild",
              desc: "Light tension, quickly resolved",
            },
            {
              value: "moderate",
              label: "Moderate",
              desc: "Age-appropriate suspense",
            },
          ].map((level) => (
            <Card
              key={level.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.fear_intensity === level.value &&
                  "ring-2 ring-primary bg-primary/5",
              )}
              onClick={() => onChange({ fear_intensity: level.value })}
            >
              <p className="text-sm font-medium">{level.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {level.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Content Exclusion Checkboxes */}
      <div className="space-y-1">
        <Label className="text-sm font-medium">
          Content Exclusions
        </Label>
        <p className="text-xs text-muted-foreground mb-3">
          These content rules are enforced to ensure child-safe material.
        </p>

        <div className="space-y-3">
          {([
            {
              key: "safety_no_weapons" as const,
              label: "No weapons or violence",
            },
            {
              key: "safety_no_scary" as const,
              label: "No scary / dark imagery",
            },
            {
              key: "safety_no_trademarks" as const,
              label: "No trademarked characters",
            },
            {
              key: "safety_no_stereotypes" as const,
              label: "No stereotypical depictions",
            },
            {
              key: "safety_age_vocabulary" as const,
              label: "Age-appropriate vocabulary",
            },
          ] as const).map((item) => (
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

      {/* Illustration Safety Checkboxes */}
      <div className="space-y-1">
        <Label className="text-sm font-medium">
          Illustration Safety
        </Label>
        <p className="text-xs text-muted-foreground mb-3">
          Additional safety checks for generated illustrations.
        </p>

        <div className="space-y-3">
          {([
            {
              key: "safety_trademark_enforcement" as const,
              label: "Trademark-safe prompt enforcement",
            },
            {
              key: "safety_content_precheck" as const,
              label: "Content sensitivity pre-check",
            },
            {
              key: "safety_provenance_logging" as const,
              label: "Model/style provenance logging",
            },
          ] as const).map((item) => (
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
