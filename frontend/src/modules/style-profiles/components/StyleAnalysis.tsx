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

interface StyleAnalysisProps {
  styleCard: StyleCard | null | undefined;
  loading?: boolean;
}

export function StyleAnalysis({ styleCard, loading = false }: StyleAnalysisProps) {
  if (loading) {
    return (
      <div className="border rounded-lg bg-card p-6">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent mb-3" />
          <p className="text-sm text-muted-foreground">Analyzing style...</p>
        </div>
      </div>
    );
  }

  if (!styleCard) {
    return (
      <div className="border rounded-lg bg-card p-6">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="rounded-full bg-muted p-3 mb-3">
            <svg
              className="h-6 w-6 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <p className="text-sm text-muted-foreground">
            Style analysis not yet available. Add sample texts to generate an analysis.
          </p>
        </div>
      </div>
    );
  }

  // Build radar chart data from key_metrics
  const radarData = Object.entries(styleCard.key_metrics || {}).map(([key, value]) => ({
    metric: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    value: value * 100, // Convert 0-1 scale to 0-100 for better visualization
    fullMark: 100,
  }));

  return (
    <div className="border rounded-lg bg-card p-6">
      <h3 className="text-lg font-semibold mb-4">Style Analysis</h3>

      {/* Summary */}
      <div className="mb-6">
        <h4 className="text-sm font-medium mb-2">Summary</h4>
        <p className="text-sm text-muted-foreground">{styleCard.summary}</p>
      </div>

      {/* Radar Chart */}
      {radarData.length > 0 && (
        <div className="mb-6">
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
        {styleCard.tone && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Tone</h5>
            <p className="text-sm">{styleCard.tone}</p>
          </div>
        )}
        {styleCard.pacing && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Pacing</h5>
            <p className="text-sm">{styleCard.pacing}</p>
          </div>
        )}
        {styleCard.vocabulary_level && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Vocabulary Level</h5>
            <p className="text-sm">{styleCard.vocabulary_level}</p>
          </div>
        )}
        {styleCard.sentence_style && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Sentence Style</h5>
            <p className="text-sm">{styleCard.sentence_style}</p>
          </div>
        )}
        {styleCard.paragraph_style && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Paragraph Style</h5>
            <p className="text-sm">{styleCard.paragraph_style}</p>
          </div>
        )}
        {styleCard.rhetorical_style && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Rhetorical Style</h5>
            <p className="text-sm">{styleCard.rhetorical_style}</p>
          </div>
        )}
        {styleCard.dialogue_style && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Dialogue Style</h5>
            <p className="text-sm">{styleCard.dialogue_style}</p>
          </div>
        )}
      </div>

      {/* Example Prompts */}
      {styleCard.example_prompts && styleCard.example_prompts.length > 0 && (
        <div className="mt-6">
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
