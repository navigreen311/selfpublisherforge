"use client";

import type { VoiceFingerprint } from "../types";

interface StyleMetricsProps {
  fingerprint: VoiceFingerprint | null | undefined;
  loading?: boolean;
}

function MetricRow({ label, value, format = "number" }: { label: string; value: number; format?: "number" | "percent" | "ratio" }) {
  const formatted =
    format === "percent"
      ? `${(value * 100).toFixed(1)}%`
      : format === "ratio"
        ? value.toFixed(3)
        : typeof value === "number"
          ? value.toFixed(1)
          : String(value);

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium tabular-nums">{formatted}</span>
    </div>
  );
}

function MetricSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border rounded-lg bg-card p-4">
      <h4 className="text-sm font-semibold mb-3">{title}</h4>
      <div>{children}</div>
    </div>
  );
}

export function StyleMetrics({ fingerprint, loading = false }: StyleMetricsProps) {
  if (loading) {
    return (
      <div className="border rounded-lg bg-card p-6">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent mb-3" />
          <p className="text-sm text-muted-foreground">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (!fingerprint) {
    return (
      <div className="border rounded-lg bg-card p-6">
        <p className="text-sm text-muted-foreground text-center py-4">
          No fingerprint data available. Analyze sample texts first.
        </p>
      </div>
    );
  }

  const { vocabulary, sentence, paragraph, rhetorical, dialogue } = fingerprint;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Detailed Style Metrics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricSection title="Vocabulary">
          <MetricRow label="Unique Words" value={vocabulary.unique_word_count} />
          <MetricRow label="Total Words" value={vocabulary.total_word_count} />
          <MetricRow label="Lexical Density" value={vocabulary.lexical_density} format="percent" />
          <MetricRow label="Type-Token Ratio" value={vocabulary.type_token_ratio} format="ratio" />
          <MetricRow label="Rare Word Frequency" value={vocabulary.rare_word_frequency} format="percent" />
          <MetricRow label="Reading Level" value={vocabulary.reading_level} />
          <MetricRow label="Avg Word Length" value={vocabulary.avg_word_length} />
        </MetricSection>

        <MetricSection title="Sentence Structure">
          <MetricRow label="Avg Length" value={sentence.avg_length} />
          <MetricRow label="Length Variance" value={sentence.length_variance} />
          <MetricRow label="Min Length" value={sentence.min_length} />
          <MetricRow label="Max Length" value={sentence.max_length} />
          <MetricRow label="Simple Ratio" value={sentence.simple_ratio} format="percent" />
          <MetricRow label="Compound Ratio" value={sentence.compound_ratio} format="percent" />
          <MetricRow label="Complex Ratio" value={sentence.complex_ratio} format="percent" />
        </MetricSection>

        <MetricSection title="Paragraph Structure">
          <MetricRow label="Avg Length" value={paragraph.avg_length} />
          <MetricRow label="Avg Word Count" value={paragraph.avg_word_count} />
          <MetricRow label="Transition Density" value={paragraph.transition_word_density} format="percent" />
          <MetricRow label="Short Para Ratio" value={paragraph.short_paragraph_ratio} format="percent" />
          <MetricRow label="Long Para Ratio" value={paragraph.long_paragraph_ratio} format="percent" />
        </MetricSection>

        <MetricSection title="Rhetorical Devices">
          <MetricRow label="Metaphor Density" value={rhetorical.metaphor_density} format="percent" />
          <MetricRow label="Simile Density" value={rhetorical.simile_density} format="percent" />
          <MetricRow label="Humor Markers" value={rhetorical.humor_marker_density} format="percent" />
          <MetricRow label="Emotional Intensity" value={rhetorical.emotional_intensity} format="percent" />
          <MetricRow label="Alliteration" value={rhetorical.alliteration_density} format="percent" />
          <MetricRow label="Rhetorical Questions" value={rhetorical.rhetorical_question_density} format="percent" />
        </MetricSection>

        <MetricSection title="Dialogue Patterns">
          <MetricRow label="Dialogue Ratio" value={dialogue.dialogue_ratio} format="percent" />
          <MetricRow label="Avg Dialogue Length" value={dialogue.avg_dialogue_length} />
          <MetricRow label="Said Tag Ratio" value={dialogue.said_tag_ratio} format="percent" />
          <MetricRow label="Action Beat Ratio" value={dialogue.action_beat_ratio} format="percent" />
          <MetricRow label="Dialogue-to-Narrative" value={dialogue.dialogue_to_narrative_ratio} format="ratio" />
        </MetricSection>
      </div>

      {/* Top Words */}
      {vocabulary.top_words && vocabulary.top_words.length > 0 && (
        <div className="border rounded-lg bg-card p-4">
          <h4 className="text-sm font-semibold mb-3">Top Words</h4>
          <div className="flex flex-wrap gap-2">
            {vocabulary.top_words.map(([word, count]) => (
              <span
                key={word}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-muted text-sm"
              >
                {word}
                <span className="text-xs text-muted-foreground">({count})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
