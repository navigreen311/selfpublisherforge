"use client";

import { Progress } from "@/components/ui/progress";
import type { VoiceFingerprint } from "../types";

interface StyleMetricsProps {
  fingerprint: VoiceFingerprint;
}

interface MetricBar {
  label: string;
  value: number;
  max: number;
  display: string;
  descriptor: string;
}

function getReadabilityDescriptor(grade: number): string {
  if (grade <= 5) return "Easy";
  if (grade <= 8) return "Simple";
  if (grade <= 10) return "Moderate";
  if (grade <= 12) return "Advanced";
  return "Complex";
}

function getFormalityDescriptor(pct: number): string {
  if (pct <= 20) return "Casual";
  if (pct <= 40) return "Relaxed";
  if (pct <= 60) return "Balanced";
  if (pct <= 80) return "Polished";
  return "Formal";
}

function getWarmthDescriptor(pct: number): string {
  if (pct <= 20) return "Detached";
  if (pct <= 40) return "Neutral";
  if (pct <= 60) return "Friendly";
  if (pct <= 80) return "Warm";
  return "Passionate";
}

function getComplexityDescriptor(pct: number): string {
  if (pct <= 20) return "Simple";
  if (pct <= 40) return "Light";
  if (pct <= 60) return "Moderate";
  if (pct <= 80) return "Dense";
  return "Complex";
}

function getActiveVoiceDescriptor(pct: number): string {
  if (pct <= 30) return "Passive";
  if (pct <= 50) return "Mixed";
  if (pct <= 70) return "Balanced";
  if (pct <= 85) return "Active";
  return "Direct";
}

function getDialogueDescriptor(pct: number): string {
  if (pct <= 10) return "Sparse";
  if (pct <= 25) return "Light";
  if (pct <= 45) return "Balanced";
  if (pct <= 65) return "Heavy";
  return "Dialogue-driven";
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function buildMetrics(fingerprint: VoiceFingerprint): MetricBar[] {
  const readability = clamp(Math.round(fingerprint.vocabulary.reading_level), 1, 16);
  const formality = clamp(Math.round(fingerprint.vocabulary.rare_word_frequency * 100), 0, 100);
  const warmth = clamp(Math.round(fingerprint.rhetorical.emotional_intensity * 100), 0, 100);
  const complexity = clamp(Math.round(fingerprint.vocabulary.lexical_density * 100), 0, 100);
  const sentenceLen = Math.round(fingerprint.sentence.avg_length * 10) / 10;
  const paragraphLen = Math.round(fingerprint.paragraph.avg_length * 10) / 10;
  const activeVoice = clamp(Math.round(100 - fingerprint.sentence.complex_ratio * 100), 0, 100);
  const dialogueUse = clamp(Math.round(fingerprint.dialogue.dialogue_ratio * 100), 0, 100);

  return [
    {
      label: "Readability",
      value: readability,
      max: 16,
      display: `Grade ${readability}`,
      descriptor: getReadabilityDescriptor(readability),
    },
    {
      label: "Formality",
      value: formality,
      max: 100,
      display: `${formality}%`,
      descriptor: getFormalityDescriptor(formality),
    },
    {
      label: "Warmth",
      value: warmth,
      max: 100,
      display: `${warmth}%`,
      descriptor: getWarmthDescriptor(warmth),
    },
    {
      label: "Complexity",
      value: complexity,
      max: 100,
      display: `${complexity}%`,
      descriptor: getComplexityDescriptor(complexity),
    },
    {
      label: "Sentence Length",
      value: sentenceLen,
      max: 50,
      display: `${sentenceLen} words`,
      descriptor: "",
    },
    {
      label: "Paragraph Length",
      value: paragraphLen,
      max: 20,
      display: `${paragraphLen} sentences`,
      descriptor: "",
    },
    {
      label: "Active Voice",
      value: activeVoice,
      max: 100,
      display: `${activeVoice}%`,
      descriptor: getActiveVoiceDescriptor(activeVoice),
    },
    {
      label: "Dialogue Use",
      value: dialogueUse,
      max: 100,
      display: `${dialogueUse}%`,
      descriptor: getDialogueDescriptor(dialogueUse),
    },
  ];
}

export function StyleMetrics({ fingerprint }: StyleMetricsProps) {
  const metrics = buildMetrics(fingerprint);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Style Metrics</h3>
      <div className="space-y-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{metric.label}</span>
              <span className="text-muted-foreground">
                {metric.display}
                {metric.descriptor ? ` · ${metric.descriptor}` : ""}
              </span>
            </div>
            <Progress value={metric.value} max={metric.max} className="h-2" />
          </div>
        ))}
      </div>
    </div>
  );
}
