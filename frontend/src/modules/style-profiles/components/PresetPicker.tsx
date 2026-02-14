"use client";

const PRESETS = [
  {
    id: "conversational-nonfiction",
    name: "Conversational Nonfiction",
    description: "Warm, accessible, second person",
  },
  {
    id: "academic-formal",
    name: "Academic/Formal",
    description: "Structured, evidence-based, third person",
  },
  {
    id: "storyteller-fiction",
    name: "Storyteller Fiction",
    description: "Vivid, sensory, past tense narrative",
  },
  {
    id: "journalistic",
    name: "Journalistic",
    description: "Clear, punchy, inverted pyramid",
  },
  {
    id: "technical",
    name: "Technical",
    description: "Precise, step-by-step, imperative mood",
  },
] as const;

interface PresetPickerProps {
  selectedPreset: string | null;
  onSelect: (preset: string | null) => void;
}

export function PresetPicker({ selectedPreset, onSelect }: PresetPickerProps) {
  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
      role="radiogroup"
      aria-label="Style presets"
    >
      {PRESETS.map((preset) => {
        const isSelected = selectedPreset === preset.id;
        return (
          <button
            key={preset.id}
            type="button"
            onClick={() => onSelect(isSelected ? null : preset.id)}
            className={`text-left border rounded-lg p-4 bg-card transition-all hover:shadow-md ${
              isSelected
                ? "ring-2 ring-primary border-primary"
                : "hover:border-muted-foreground/30"
            }`}
            aria-pressed={isSelected}
          >
            <h3 className="font-semibold text-sm">{preset.name}</h3>
            <p className="text-xs text-muted-foreground mt-1">
              {preset.description}
            </p>
          </button>
        );
      })}
    </div>
  );
}
