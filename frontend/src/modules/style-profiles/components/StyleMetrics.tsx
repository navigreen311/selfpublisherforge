"use client";

import type { VoiceFingerprint } from "../types";

interface StyleMetricsProps {
  fingerprint: VoiceFingerprint;
}

interface MetricItem {
  label: string;
  value: number;
  format: "percent" | "number" | "decimal";
}

function formatMetric(value: number, format: MetricItem["format"]): string {
  switch (format) {
    case "percent":
      return `${(value * 100).toFixed(1)}%`;
    case "number":
      return value.toLocaleString();
    case "decimal":
      return value.toFixed(2);
  }
}

function MetricBar({ label, value, format }: MetricItem) {
  const displayValue = formatMetric(value, format);
  const barWidth = format === "percent" ? value * 100 : Math.min(value / 10, 100);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{displayValue}</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${Math.max(barWidth, 2)}%` }}
        />
      </div>
    </div>
  );
}

export function StyleMetrics({ fingerprint }: StyleMetricsProps) {
  const { vocabulary, sentence, paragraph } = fingerprint;

  const sections: { title: string; metrics: MetricItem[] }[] = [
    {
      title: "Vocabulary",
      metrics: [
        { label: "Lexical Density", value: vocabulary.lexical_density, format: "decimal" },
        { label: "Type-Token Ratio", value: vocabulary.type_token_ratio, format: "decimal" },
        { label: "Rare Word Frequency", value: vocabulary.rare_word_frequency, format: "percent" },
        { label: "Reading Level", value: vocabulary.reading_level, format: "decimal" },
        { label: "Avg Word Length", value: vocabulary.avg_word_length, format: "decimal" },
      ],
    },
    {
      title: "Sentences",
      metrics: [
        { label: "Avg Length", value: sentence.avg_length, format: "decimal" },
        { label: "Simple", value: sentence.simple_ratio, format: "percent" },
        { label: "Compound", value: sentence.compound_ratio, format: "percent" },
        { label: "Complex", value: sentence.complex_ratio, format: "percent" },
        { label: "Questions", value: sentence.question_ratio, format: "percent" },
      ],
    },
    {
      title: "Paragraphs",
      metrics: [
        { label: "Avg Length (words)", value: paragraph.avg_word_count, format: "number" },
        { label: "Transition Word Density", value: paragraph.transition_word_density, format: "percent" },
        { label: "Short Paragraph Ratio", value: paragraph.short_paragraph_ratio, format: "percent" },
        { label: "Long Paragraph Ratio", value: paragraph.long_paragraph_ratio, format: "percent" },
      ],
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {sections.map((section) => (
        <div key={section.title}>
          <h4 className="text-sm font-medium mb-3">{section.title}</h4>
          <div className="space-y-3">
            {section.metrics.map((metric) => (
              <MetricBar key={metric.label} {...metric} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
