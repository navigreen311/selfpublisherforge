"use client";

import type { VoiceFingerprint } from "../types";

interface VoiceCharacteristicsProps {
  fingerprint: VoiceFingerprint;
}

interface CharacteristicItem {
  label: string;
  value: number;
  description: string;
}

function intensityLabel(value: number): string {
  if (value >= 0.7) return "High";
  if (value >= 0.4) return "Moderate";
  if (value >= 0.1) return "Low";
  return "Minimal";
}

function intensityColor(value: number): string {
  if (value >= 0.7) return "bg-green-500";
  if (value >= 0.4) return "bg-yellow-500";
  if (value >= 0.1) return "bg-orange-500";
  return "bg-muted-foreground";
}

function CharacteristicRow({ label, value, description }: CharacteristicItem) {
  return (
    <div className="flex items-center justify-between py-2 border-b last:border-b-0">
      <div className="flex-1">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-2 ml-4">
        <div className={`h-2 w-2 rounded-full ${intensityColor(value)}`} />
        <span className="text-sm font-medium w-20 text-right">
          {intensityLabel(value)}
        </span>
      </div>
    </div>
  );
}

export function VoiceCharacteristics({ fingerprint }: VoiceCharacteristicsProps) {
  const { rhetorical, dialogue } = fingerprint;

  const characteristics: CharacteristicItem[] = [
    {
      label: "Metaphor Usage",
      value: rhetorical.metaphor_density,
      description: "Frequency of metaphorical language",
    },
    {
      label: "Simile Usage",
      value: rhetorical.simile_density,
      description: "Frequency of explicit comparisons",
    },
    {
      label: "Humor Markers",
      value: rhetorical.humor_marker_density,
      description: "Presence of humor and wit",
    },
    {
      label: "Emotional Intensity",
      value: rhetorical.emotional_intensity,
      description: "Strength of emotional expression",
    },
    {
      label: "Alliteration",
      value: rhetorical.alliteration_density,
      description: "Use of repeated initial sounds",
    },
    {
      label: "Rhetorical Questions",
      value: rhetorical.rhetorical_question_density,
      description: "Questions used for effect",
    },
    {
      label: "Dialogue Presence",
      value: dialogue.dialogue_ratio,
      description: "Proportion of text that is dialogue",
    },
    {
      label: "Dialogue-to-Narrative",
      value: dialogue.dialogue_to_narrative_ratio,
      description: "Balance between speech and narration",
    },
  ];

  return (
    <div className="space-y-1">
      {characteristics.map((item) => (
        <CharacteristicRow key={item.label} {...item} />
      ))}
    </div>
  );
}
