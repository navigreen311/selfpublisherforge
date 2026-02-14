"use client";

import { useTranslations } from "@/hooks/use-translations";

export interface StylePreset {
  id: string;
  label: string;
  description: string;
  icon: string;
}

const PRESETS: StylePreset[] = [
  {
    id: "literary-fiction",
    label: "Literary Fiction",
    description: "Rich prose, character-driven narratives, lyrical language",
    icon: "\uD83D\uDCDA",
  },
  {
    id: "thriller",
    label: "Thriller / Suspense",
    description: "Fast-paced, short sentences, high tension",
    icon: "\uD83D\uDD2A",
  },
  {
    id: "romance",
    label: "Romance",
    description: "Emotional depth, sensory detail, dialogue-heavy",
    icon: "\u2764\uFE0F",
  },
  {
    id: "scifi-fantasy",
    label: "Sci-Fi / Fantasy",
    description: "World-building, descriptive, speculative tone",
    icon: "\uD83D\uDE80",
  },
  {
    id: "nonfiction",
    label: "Non-Fiction",
    description: "Clear, authoritative, evidence-based writing",
    icon: "\uD83D\uDCDD",
  },
  {
    id: "business",
    label: "Business / Marketing",
    description: "Persuasive, concise, action-oriented copy",
    icon: "\uD83D\uDCBC",
  },
];

interface PresetPickerProps {
  selected: string | null;
  onSelect: (presetId: string | null) => void;
}

export function PresetPicker({ selected, onSelect }: PresetPickerProps) {
  const t = useTranslations("style-profiles");

  return (
    <div>
      <p className="text-sm text-muted-foreground mb-3">
        {t("new.quickStartDescription")}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            onClick={() =>
              onSelect(selected === preset.id ? null : preset.id)
            }
            className={`flex flex-col items-start gap-1 rounded-lg border p-3 text-left transition-colors hover:bg-accent ${
              selected === preset.id
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border"
            }`}
          >
            <span className="text-lg" aria-hidden="true">
              {preset.icon}
            </span>
            <span className="text-sm font-medium">{preset.label}</span>
            <span className="text-xs text-muted-foreground line-clamp-2">
              {preset.description}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
