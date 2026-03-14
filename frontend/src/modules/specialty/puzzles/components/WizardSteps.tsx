"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  Search,
  Grid3X3,
  Route,
  Hash,
  Shuffle,
  Lock,
  Binary,
  Link2,
  Baby,
  Users,
  User,
  ZoomIn,
  Sparkles,
  Trash2,
  Plus,
} from "lucide-react";
import type { PuzzleType } from "../hooks";

// ─── Wizard Data Type ─────────────────────────────────────────────────────────

export interface PuzzleTypeConfig {
  type: PuzzleType;
  quantity: number;
  difficulty: string;
  grid_size: string;
}

export interface WizardData {
  // Step 1
  title: string;
  subtitle: string;
  audience: string;
  series_enabled: boolean;
  series_name: string;
  volume_number: string;
  // Step 2
  selected_puzzle_types: PuzzleTypeConfig[];
  difficulty_mode: string;
  puzzle_mix_template: string;
  custom_percentages: Record<string, number>;
  // Step 3
  theme_input_method: string;
  themes: string[];
  seasonal_enabled: boolean;
  seasonal_theme: string;
  word_difficulty: string;
  custom_word_list: string;
  // Step 4
  answer_key_position: string;
  extras_toc: boolean;
  extras_instructions: boolean;
  extras_difficulty_badges: boolean;
  extras_section_dividers: boolean;
  hint_config: Record<string, string>;
  clue_style: string;
  layout: string;
}

export const DEFAULT_WIZARD_DATA: WizardData = {
  title: "",
  subtitle: "",
  audience: "",
  series_enabled: false,
  series_name: "",
  volume_number: "",
  selected_puzzle_types: [],
  difficulty_mode: "progressive",
  puzzle_mix_template: "balanced",
  custom_percentages: {},
  theme_input_method: "ai_generate",
  themes: [],
  seasonal_enabled: false,
  seasonal_theme: "",
  word_difficulty: "standard",
  custom_word_list: "",
  answer_key_position: "back",
  extras_toc: true,
  extras_instructions: true,
  extras_difficulty_badges: false,
  extras_section_dividers: false,
  hint_config: {},
  clue_style: "standard",
  layout: "one_per_page",
};

// ─── Constants ────────────────────────────────────────────────────────────────

const AUDIENCES = [
  {
    value: "kids",
    label: "Kids",
    desc: "Ages 5-10, simple & fun",
    icon: Baby,
  },
  {
    value: "teens",
    label: "Teens",
    desc: "Ages 9-14, moderate challenge",
    icon: Users,
  },
  {
    value: "adults",
    label: "Adults",
    desc: "Ages 15+, full complexity",
    icon: User,
  },
  {
    value: "large_print",
    label: "Large Print",
    desc: "150% scale, seniors",
    icon: ZoomIn,
  },
];

const PUZZLE_TYPES_LIST: {
  type: PuzzleType;
  label: string;
  icon: typeof Search;
  defaultGridSize: string;
  gridSizes: string[];
}[] = [
  {
    type: "word_search",
    label: "Word Search",
    icon: Search,
    defaultGridSize: "15x15",
    gridSizes: ["10x10", "12x12", "15x15", "18x18", "20x20"],
  },
  {
    type: "crossword",
    label: "Crossword",
    icon: Grid3X3,
    defaultGridSize: "15x15",
    gridSizes: ["11x11", "13x13", "15x15", "17x17", "21x21"],
  },
  {
    type: "maze",
    label: "Maze",
    icon: Route,
    defaultGridSize: "20x20",
    gridSizes: ["10x10", "15x15", "20x20", "30x30", "40x40"],
  },
  {
    type: "sudoku",
    label: "Sudoku",
    icon: Hash,
    defaultGridSize: "9x9",
    gridSizes: ["4x4", "6x6", "9x9"],
  },
  {
    type: "word_scramble",
    label: "Word Scramble",
    icon: Shuffle,
    defaultGridSize: "n/a",
    gridSizes: ["n/a"],
  },
  {
    type: "cryptogram",
    label: "Cryptogram",
    icon: Lock,
    defaultGridSize: "n/a",
    gridSizes: ["n/a"],
  },
  {
    type: "number_search",
    label: "Number Search",
    icon: Binary,
    defaultGridSize: "15x15",
    gridSizes: ["10x10", "12x12", "15x15", "18x18", "20x20"],
  },
  {
    type: "word_connect",
    label: "Word Connect",
    icon: Link2,
    defaultGridSize: "variable",
    gridSizes: ["variable"],
  },
];

const DIFFICULTY_OPTIONS = ["easy", "medium", "hard"];

const THEME_CATEGORIES = [
  "Animals",
  "Nature",
  "Food",
  "Sports",
  "Science",
  "History",
  "Geography",
  "Music",
  "Movies",
  "Space",
  "Ocean",
  "Technology",
];

const SEASONAL_THEMES = [
  "Christmas",
  "Halloween",
  "Easter",
  "Thanksgiving",
  "Valentine's Day",
  "St. Patrick's Day",
  "Fourth of July",
  "Back to School",
  "Summer",
  "Winter",
  "Spring",
  "Fall",
];

// ─── Step Props ───────────────────────────────────────────────────────────────

interface StepProps {
  data: WizardData;
  onChange: (updates: Partial<WizardData>) => void;
}

// ─── Step 1: Book Details ─────────────────────────────────────────────────────

export function Step1BookDetails({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Book Details</h2>
        <p className="text-sm text-muted-foreground">
          Define the basics of your puzzle book.
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
          <div className="flex gap-2">
            <Input
              id="subtitle"
              placeholder="Optional subtitle"
              value={data.subtitle}
              onChange={(e) => onChange({ subtitle: e.target.value })}
              className="flex-1"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="shrink-0 gap-1.5"
              onClick={() => {
                const types = data.selected_puzzle_types
                  .map((c) => {
                    const pt = PUZZLE_TYPES_LIST.find(
                      (p) => p.type === c.type
                    );
                    return pt?.label;
                  })
                  .filter(Boolean);
                const typesStr =
                  types.length > 0 ? types.join(", ") : "Puzzles";
                onChange({
                  subtitle: `${typesStr} with Answers`,
                });
              }}
            >
              <Sparkles className="h-3.5 w-3.5" />
              AI Suggest
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            AI suggests including puzzle types + &ldquo;with answers&rdquo;
          </p>
        </div>
      </div>

      {/* Audience Card Selector */}
      <div className="space-y-3">
        <Label>
          Audience <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 gap-3">
          {AUDIENCES.map((aud) => {
            const Icon = aud.icon;
            const isSelected = data.audience === aud.value;
            return (
              <Card
                key={aud.value}
                className={cn(
                  "p-4 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                  isSelected && "ring-2 ring-primary bg-primary/5"
                )}
                onClick={() => onChange({ audience: aud.value })}
              >
                <div className="flex items-start gap-3">
                  <Icon className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-sm">{aud.label}</p>
                    <p className="text-xs text-muted-foreground">{aud.desc}</p>
                    {aud.value === "large_print" && (
                      <Badge variant="outline" className="mt-1 text-[10px]">
                        150% scale
                      </Badge>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Series Planning */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Series Planning</Label>
            <p className="text-xs text-muted-foreground">
              Plan this book as part of a series
            </p>
          </div>
          <Switch
            checked={data.series_enabled}
            onCheckedChange={(v) => onChange({ series_enabled: v })}
          />
        </div>

        {data.series_enabled && (
          <div className="grid gap-4 pl-4 border-l-2 border-primary/20 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Series Name</Label>
              <Input
                placeholder="e.g., Ultimate Puzzle Series"
                value={data.series_name}
                onChange={(e) => onChange({ series_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Volume Number</Label>
              <Input
                type="number"
                placeholder="1"
                min={1}
                value={data.volume_number}
                onChange={(e) => onChange({ volume_number: e.target.value })}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Step 2: Puzzle Selection ─────────────────────────────────────────────────

export function Step2PuzzleSelection({ data, onChange }: StepProps) {
  const togglePuzzleType = (type: PuzzleType) => {
    const existing = data.selected_puzzle_types.find((c) => c.type === type);
    if (existing) {
      onChange({
        selected_puzzle_types: data.selected_puzzle_types.filter(
          (c) => c.type !== type
        ),
      });
    } else {
      const ptDef = PUZZLE_TYPES_LIST.find((p) => p.type === type);
      onChange({
        selected_puzzle_types: [
          ...data.selected_puzzle_types,
          {
            type,
            quantity: 10,
            difficulty: "medium",
            grid_size: ptDef?.defaultGridSize ?? "15x15",
          },
        ],
      });
    }
  };

  const updatePuzzleConfig = (
    type: PuzzleType,
    field: keyof PuzzleTypeConfig,
    value: string | number
  ) => {
    onChange({
      selected_puzzle_types: data.selected_puzzle_types.map((c) =>
        c.type === type ? { ...c, [field]: value } : c
      ),
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Puzzle Selection</h2>
        <p className="text-sm text-muted-foreground">
          Choose puzzle types and configure each independently.
        </p>
      </div>

      {/* Puzzle Type Multi-Select */}
      <div className="space-y-3">
        <Label>
          Puzzle Types <span className="text-destructive">*</span>
        </Label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {PUZZLE_TYPES_LIST.map((pt) => {
            const Icon = pt.icon;
            const isSelected = data.selected_puzzle_types.some(
              (c) => c.type === pt.type
            );
            return (
              <Card
                key={pt.type}
                className={cn(
                  "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50 text-center",
                  isSelected && "ring-2 ring-primary bg-primary/5"
                )}
                onClick={() => togglePuzzleType(pt.type)}
              >
                <Icon className="h-5 w-5 mx-auto mb-1 text-primary" />
                <p className="text-xs font-medium">{pt.label}</p>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Per-Type Configuration */}
      {data.selected_puzzle_types.length > 0 && (
        <div className="space-y-3">
          <Label>Configuration Per Type</Label>
          <div className="space-y-3">
            {data.selected_puzzle_types.map((config) => {
              const ptDef = PUZZLE_TYPES_LIST.find(
                (p) => p.type === config.type
              );
              if (!ptDef) return null;
              const Icon = ptDef.icon;
              return (
                <div
                  key={config.type}
                  className="rounded-lg border p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">
                        {ptDef.label}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => togglePuzzleType(config.type)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    {/* Quantity */}
                    <div className="space-y-1">
                      <Label className="text-xs">Quantity</Label>
                      <Input
                        type="number"
                        min={1}
                        max={100}
                        value={config.quantity}
                        onChange={(e) =>
                          updatePuzzleConfig(
                            config.type,
                            "quantity",
                            parseInt(e.target.value, 10) || 1
                          )
                        }
                        className="h-8 text-sm"
                      />
                    </div>

                    {/* Difficulty */}
                    <div className="space-y-1">
                      <Label className="text-xs">Difficulty</Label>
                      <Select
                        value={config.difficulty}
                        onValueChange={(v) =>
                          updatePuzzleConfig(config.type, "difficulty", v)
                        }
                      >
                        <SelectTrigger className="h-8 text-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {DIFFICULTY_OPTIONS.map((d) => (
                            <SelectItem key={d} value={d}>
                              {d.charAt(0).toUpperCase() + d.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Grid Size */}
                    <div className="space-y-1">
                      <Label className="text-xs">Grid Size</Label>
                      <Select
                        value={config.grid_size}
                        onValueChange={(v) =>
                          updatePuzzleConfig(config.type, "grid_size", v)
                        }
                      >
                        <SelectTrigger className="h-8 text-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ptDef.gridSizes.map((s) => (
                            <SelectItem key={s} value={s}>
                              {s}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Difficulty Calibration Mode */}
      <div className="space-y-3">
        <Label>Difficulty Calibration Mode</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              value: "progressive",
              label: "Progressive",
              desc: "Easy to hard ramp",
            },
            {
              value: "fixed",
              label: "Fixed",
              desc: "Same difficulty throughout",
            },
            {
              value: "mixed",
              label: "Mixed Random",
              desc: "Random difficulty order",
            },
          ].map((mode) => (
            <Card
              key={mode.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.difficulty_mode === mode.value &&
                  "ring-2 ring-primary bg-primary/5"
              )}
              onClick={() => onChange({ difficulty_mode: mode.value })}
            >
              <p className="text-sm font-medium">{mode.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {mode.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Puzzle Mix Template (for mixed books) */}
      {data.selected_puzzle_types.length > 1 && (
        <div className="space-y-3">
          <Label>Puzzle Mix Template</Label>
          <div className="grid grid-cols-3 gap-3">
            {[
              {
                value: "balanced",
                label: "Balanced",
                desc: "Equal distribution",
              },
              {
                value: "word_heavy",
                label: "Word-Heavy",
                desc: "More word puzzles",
              },
              {
                value: "custom",
                label: "Custom",
                desc: "Set percentages",
              },
            ].map((tmpl) => (
              <Card
                key={tmpl.value}
                className={cn(
                  "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                  data.puzzle_mix_template === tmpl.value &&
                    "ring-2 ring-primary bg-primary/5"
                )}
                onClick={() => onChange({ puzzle_mix_template: tmpl.value })}
              >
                <p className="text-sm font-medium">{tmpl.label}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {tmpl.desc}
                </p>
              </Card>
            ))}
          </div>

          {/* Custom Percentages */}
          {data.puzzle_mix_template === "custom" && (
            <div className="pl-4 border-l-2 border-primary/20 space-y-2">
              {data.selected_puzzle_types.map((config) => {
                const ptDef = PUZZLE_TYPES_LIST.find(
                  (p) => p.type === config.type
                );
                return (
                  <div
                    key={config.type}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm">{ptDef?.label}</span>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        className="h-8 w-20 text-sm"
                        value={data.custom_percentages[config.type] ?? 0}
                        onChange={(e) =>
                          onChange({
                            custom_percentages: {
                              ...data.custom_percentages,
                              [config.type]:
                                parseInt(e.target.value, 10) || 0,
                            },
                          })
                        }
                      />
                      <span className="text-xs text-muted-foreground">%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Step 3: Themes & Words ───────────────────────────────────────────────────

export function Step3ThemesWords({ data, onChange }: StepProps) {
  const addTheme = (theme: string) => {
    if (!data.themes.includes(theme)) {
      onChange({ themes: [...data.themes, theme] });
    }
  };

  const removeTheme = (theme: string) => {
    onChange({ themes: data.themes.filter((t) => t !== theme) });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Themes & Words</h2>
        <p className="text-sm text-muted-foreground">
          Define themed content and word lists for your puzzles.
        </p>
      </div>

      {/* Theme Input Method */}
      <div className="space-y-3">
        <Label>Theme Input Method</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              value: "ai_generate",
              label: "AI Generate by Theme",
              desc: "AI creates word lists from themes",
            },
            {
              value: "custom",
              label: "Custom Word Lists",
              desc: "Provide your own words",
            },
            {
              value: "mix",
              label: "Mix",
              desc: "Combine AI + custom words",
            },
          ].map((method) => (
            <Card
              key={method.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.theme_input_method === method.value &&
                  "ring-2 ring-primary bg-primary/5"
              )}
              onClick={() => onChange({ theme_input_method: method.value })}
            >
              <p className="text-sm font-medium">{method.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {method.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Theme Categories Multi-Select */}
      {(data.theme_input_method === "ai_generate" ||
        data.theme_input_method === "mix") && (
        <div className="space-y-3">
          <Label>Theme Categories</Label>
          <div className="flex flex-wrap gap-2">
            {THEME_CATEGORIES.map((theme) => {
              const isSelected = data.themes.includes(theme);
              return (
                <Badge
                  key={theme}
                  variant={isSelected ? "default" : "outline"}
                  className={cn(
                    "cursor-pointer transition-colors",
                    isSelected
                      ? ""
                      : "hover:bg-primary/10 hover:text-primary hover:border-primary"
                  )}
                  onClick={() =>
                    isSelected ? removeTheme(theme) : addTheme(theme)
                  }
                >
                  {theme}
                </Badge>
              );
            })}
          </div>
          {data.themes.length === 0 && (
            <p className="text-xs text-muted-foreground">
              Select at least one theme category
            </p>
          )}
        </div>
      )}

      {/* Custom Word List Input */}
      {(data.theme_input_method === "custom" ||
        data.theme_input_method === "mix") && (
        <div className="space-y-2">
          <Label htmlFor="custom-words">Custom Word List</Label>
          <textarea
            id="custom-words"
            className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            placeholder="Enter words separated by commas or new lines..."
            value={data.custom_word_list}
            onChange={(e) => onChange({ custom_word_list: e.target.value })}
          />
          <div className="flex items-center gap-2">
            <p className="text-xs text-muted-foreground flex-1">
              Words will be sanitized for offensive terms, trademarks, and
              abbreviations
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!data.custom_word_list.trim() || sanitize.isPending}
              onClick={handleSanitize}
            >
              {sanitize.isPending ? "Sanitizing\u2026" : "Sanitize Words"}
            </Button>
          </div>
        </div>
      )}

      {/* Seasonal / Holiday Auto-Theming */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Seasonal / Holiday Auto-Theming</Label>
            <p className="text-xs text-muted-foreground">
              Apply seasonal themes across all puzzle types
            </p>
          </div>
          <Switch
            checked={data.seasonal_enabled}
            onCheckedChange={(v) => onChange({ seasonal_enabled: v })}
          />
        </div>

        {data.seasonal_enabled && (
          <div className="pl-4 border-l-2 border-primary/20">
            <Select
              value={data.seasonal_theme}
              onValueChange={(v) => onChange({ seasonal_theme: v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select seasonal theme" />
              </SelectTrigger>
              <SelectContent>
                {SEASONAL_THEMES.map((theme) => (
                  <SelectItem
                    key={theme}
                    value={theme.toLowerCase().replace(/['\s]/g, "_")}
                  >
                    {theme}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Word Difficulty */}
      <div className="space-y-3">
        <Label>Word Difficulty</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              value: "simple",
              label: "Simple",
              desc: "3-6 letters",
            },
            {
              value: "standard",
              label: "Standard",
              desc: "4-10 letters",
            },
            {
              value: "advanced",
              label: "Advanced",
              desc: "6-15 letters",
            },
          ].map((wd) => (
            <Card
              key={wd.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.word_difficulty === wd.value &&
                  "ring-2 ring-primary bg-primary/5"
              )}
              onClick={() => onChange({ word_difficulty: wd.value })}
            >
              <p className="text-sm font-medium">{wd.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {wd.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Step 4: Layout & Extras ──────────────────────────────────────────────────

export function Step4LayoutExtras({ data, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Layout & Extras</h2>
        <p className="text-sm text-muted-foreground">
          Configure answer keys, extras, and layout options.
        </p>
      </div>

      {/* Answer Key Position */}
      <div className="space-y-3">
        <Label>Answer Key Position</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              value: "back",
              label: "Back of Book",
              desc: "Standard, all answers at end",
            },
            {
              value: "reverse",
              label: "Reverse of Page",
              desc: "Answer on back of puzzle page",
            },
            {
              value: "none",
              label: "No Answers",
              desc: "No answer key included",
            },
          ].map((pos) => (
            <Card
              key={pos.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.answer_key_position === pos.value &&
                  "ring-2 ring-primary bg-primary/5"
              )}
              onClick={() => onChange({ answer_key_position: pos.value })}
            >
              <p className="text-sm font-medium">{pos.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {pos.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* Extras Checkboxes */}
      <div className="space-y-3">
        <Label>Extras</Label>
        <div className="space-y-2">
          {[
            {
              key: "extras_toc" as const,
              label: "Table of Contents",
            },
            {
              key: "extras_instructions" as const,
              label: "Instructions per puzzle type",
            },
            {
              key: "extras_difficulty_badges" as const,
              label: "Difficulty badges on puzzles",
            },
            {
              key: "extras_section_dividers" as const,
              label: "Section dividers between types",
            },
          ].map((extra) => (
            <div
              key={extra.key}
              className="flex items-center space-x-2 rounded-md border p-3"
            >
              <Checkbox
                id={extra.key}
                checked={data[extra.key]}
                onCheckedChange={(v) =>
                  onChange({ [extra.key]: v === true })
                }
              />
              <Label htmlFor={extra.key} className="text-sm cursor-pointer">
                {extra.label}
              </Label>
            </div>
          ))}
        </div>
      </div>

      {/* Hint System Config */}
      {data.selected_puzzle_types.length > 0 && (
        <div className="space-y-3">
          <Label>Hint System (per puzzle type)</Label>
          <div className="space-y-2">
            {data.selected_puzzle_types.map((config) => {
              const ptDef = PUZZLE_TYPES_LIST.find(
                (p) => p.type === config.type
              );
              if (!ptDef) return null;
              return (
                <div
                  key={config.type}
                  className="flex items-center justify-between rounded-md border p-3"
                >
                  <span className="text-sm">{ptDef.label}</span>
                  <Select
                    value={data.hint_config[config.type] ?? "none"}
                    onValueChange={(v) =>
                      onChange({
                        hint_config: {
                          ...data.hint_config,
                          [config.type]: v,
                        },
                      })
                    }
                  >
                    <SelectTrigger className="w-[180px] h-8 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No hints</SelectItem>
                      <SelectItem value="first_letter">
                        First letter revealed
                      </SelectItem>
                      <SelectItem value="theme_hint">Theme hints</SelectItem>
                      <SelectItem value="partial">
                        Partial solution
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Clue Style */}
      <div className="space-y-3">
        <Label>Clue Style</Label>
        <Select
          value={data.clue_style}
          onValueChange={(v) => onChange({ clue_style: v })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="standard">Standard</SelectItem>
            <SelectItem value="kid_friendly">Kid-Friendly</SelectItem>
            <SelectItem value="trivia">Trivia</SelectItem>
            <SelectItem value="themed">Themed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Layout */}
      <div className="space-y-3">
        <Label>Puzzle Layout</Label>
        <div className="grid grid-cols-2 gap-3">
          {[
            {
              value: "one_per_page",
              label: "One Puzzle Per Page",
              desc: "Full-page puzzles, easier to read",
            },
            {
              value: "two_per_page",
              label: "Two Per Page",
              desc: "Compact layout, more puzzles per book",
            },
          ].map((opt) => (
            <Card
              key={opt.value}
              className={cn(
                "p-3 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50",
                data.layout === opt.value &&
                  "ring-2 ring-primary bg-primary/5"
              )}
              onClick={() => onChange({ layout: opt.value })}
            >
              <p className="text-sm font-medium">{opt.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {opt.desc}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
