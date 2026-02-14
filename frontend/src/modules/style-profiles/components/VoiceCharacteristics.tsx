"use client";

import type { StyleCard } from "../types";

interface VoiceCharacteristicsProps {
  styleCard: StyleCard;
}

function extractFromSummary(summary: string, label: string): string | null {
  // Look for patterns like "first-person POV", "third-person", "past tense", "present tense"
  const lower = summary.toLowerCase();

  if (label === "POV") {
    const povMatch = summary.match(
      /\b(first[- ]person|second[- ]person|third[- ]person|omniscient|limited)\b/i
    );
    return povMatch ? povMatch[0] : null;
  }

  if (label === "Tense") {
    const tenseMatch = summary.match(
      /\b(past tense|present tense|future tense)\b/i
    );
    return tenseMatch ? tenseMatch[0] : null;
  }

  return null;
}

const rows = [
  { label: "POV", key: "pov" },
  { label: "Tense", key: "tense" },
  { label: "Tone", key: "tone" },
  { label: "Vocabulary", key: "vocabulary_level" },
  { label: "Sentence Style", key: "sentence_style" },
  { label: "Paragraph Style", key: "paragraph_style" },
  { label: "Rhetorical Style", key: "rhetorical_style" },
  { label: "Dialogue Style", key: "dialogue_style" },
] as const;

export function VoiceCharacteristics({
  styleCard,
}: VoiceCharacteristicsProps) {
  function getValue(row: (typeof rows)[number]): string {
    if (row.key === "pov") {
      return extractFromSummary(styleCard.summary, "POV") ?? "See summary";
    }
    if (row.key === "tense") {
      return extractFromSummary(styleCard.summary, "Tense") ?? "See summary";
    }
    return (styleCard as unknown as Record<string, unknown>)[row.key] as string;
  }

  return (
    <dl className="border rounded-lg overflow-hidden divide-y divide-border">
      {rows.map((row, index) => (
        <div
          key={row.key}
          className={`flex px-4 py-3 ${
            index % 2 === 0 ? "bg-muted/50" : "bg-background"
          }`}
        >
          <dt className="w-40 shrink-0 font-medium text-muted-foreground">
            {row.label}
          </dt>
          <dd className="text-foreground">{getValue(row)}</dd>
        </div>
      ))}
    </dl>
  );
}
