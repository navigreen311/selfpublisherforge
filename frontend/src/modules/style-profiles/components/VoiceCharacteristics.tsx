"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { StyleCard } from "../types";

interface VoiceCharacteristicsProps {
  styleCard: StyleCard | null | undefined;
  loading?: boolean;
}

const STYLE_ATTRIBUTES = [
  { key: "tone", label: "Tone" },
  { key: "pacing", label: "Pacing" },
  { key: "vocabulary_level", label: "Vocabulary Level" },
  { key: "sentence_style", label: "Sentence Style" },
  { key: "paragraph_style", label: "Paragraph Style" },
  { key: "rhetorical_style", label: "Rhetorical Style" },
  { key: "dialogue_style", label: "Dialogue Style" },
] as const;

export function VoiceCharacteristics({ styleCard, loading = false }: VoiceCharacteristicsProps) {
  if (loading) {
    return (
      <div className="border rounded-lg bg-card p-6">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent mb-3" />
          <p className="text-sm text-muted-foreground">Analyzing voice...</p>
        </div>
      </div>
    );
  }

  if (!styleCard) {
    return (
      <div className="border rounded-lg bg-card p-6">
        <p className="text-sm text-muted-foreground text-center py-4">
          Voice characteristics not yet available. Add sample texts to generate an analysis.
        </p>
      </div>
    );
  }

  const radarData = Object.entries(styleCard.key_metrics || {}).map(([key, value]) => ({
    metric: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    value: value * 100,
    fullMark: 100,
  }));

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Voice Characteristics</h3>

      {/* Summary */}
      {styleCard.summary && (
        <div className="border rounded-lg bg-card p-4">
          <h4 className="text-sm font-medium mb-2">Summary</h4>
          <p className="text-sm text-muted-foreground">{styleCard.summary}</p>
        </div>
      )}

      {/* Radar Chart */}
      {radarData.length > 0 && (
        <div className="border rounded-lg bg-card p-4">
          <h4 className="text-sm font-medium mb-3">Style Dimensions</h4>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar
                name="Style Score"
                dataKey="value"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.3}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Style Attributes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {STYLE_ATTRIBUTES.map(({ key, label }) => {
          const value = styleCard[key];
          if (!value) return null;
          return (
            <div key={key} className="border rounded-lg bg-card p-4">
              <h5 className="text-xs font-medium text-muted-foreground mb-1">{label}</h5>
              <p className="text-sm">{value}</p>
            </div>
          );
        })}
      </div>

      {/* Example Prompts */}
      {styleCard.example_prompts && styleCard.example_prompts.length > 0 && (
        <div className="border rounded-lg bg-card p-4">
          <h4 className="text-sm font-medium mb-2">Example Prompts</h4>
          <ul className="space-y-1">
            {styleCard.example_prompts.map((prompt, idx) => (
              <li key={idx} className="text-sm text-muted-foreground">
                • {prompt}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
