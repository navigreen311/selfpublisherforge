"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Plus,
  Pencil,
  FlaskConical,
  MoreHorizontal,
  Trash2,
  RefreshCw,
  FileText,
  BookOpen,
} from "lucide-react";
import {
  useStyleProfile,
  useStyleFingerprint,
  useAnalyzeProfile,
  useConformityCheck,
  useGenerateSample,
  useDeleteProfile,
} from "@/modules/style-profiles/hooks";
import type { VoiceFingerprint } from "@/modules/style-profiles/types";
import { StyleAnalysis } from "@/modules/style-profiles/components/StyleAnalysis";
import { ConformityChecker } from "@/modules/style-profiles/components/ConformityChecker";
import { TextIngestion } from "@/modules/style-profiles/components/TextIngestion";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

// ── Tab types ───────────────────────────────────────────────────

type TabValue = "overview" | "samples" | "test" | "usage";

const TABS: { value: TabValue; label: string }[] = [
  { value: "overview", label: "Overview" },
  { value: "samples", label: "Samples" },
  { value: "test", label: "Test & Refine" },
  { value: "usage", label: "Usage" },
];

// ── Helper: format a metric value as a percentage bar row ──────

function MetricRow({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{pct}%</span>
      </div>
      <Progress value={pct} className="h-2" />
    </div>
  );
}

// ── Voice Characteristics (inline) ─────────────────────────────

function VoiceCharacteristics({ fingerprint }: { fingerprint: VoiceFingerprint }) {
  const { vocabulary, sentence, paragraph, rhetorical, dialogue } = fingerprint;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Vocabulary */}
      <div className="border rounded-lg p-4 bg-card space-y-3">
        <h4 className="text-sm font-semibold">Vocabulary</h4>
        <MetricRow label="Lexical Density" value={vocabulary.lexical_density} />
        <MetricRow label="Type-Token Ratio" value={vocabulary.type_token_ratio} />
        <MetricRow label="Rare Word Frequency" value={vocabulary.rare_word_frequency} />
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Avg Word Length</span>
          <span className="font-medium">{vocabulary.avg_word_length.toFixed(1)} chars</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Reading Level</span>
          <span className="font-medium">Grade {vocabulary.reading_level.toFixed(1)}</span>
        </div>
        {vocabulary.top_words.length > 0 && (
          <div>
            <span className="text-xs text-muted-foreground">Top Words</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {vocabulary.top_words.slice(0, 10).map(([word, count]) => (
                <Badge key={word} variant="secondary" className="text-xs">
                  {word} ({count})
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sentence */}
      <div className="border rounded-lg p-4 bg-card space-y-3">
        <h4 className="text-sm font-semibold">Sentence Structure</h4>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Avg Length</span>
          <span className="font-medium">{sentence.avg_length.toFixed(1)} words</span>
        </div>
        <MetricRow label="Simple Sentences" value={sentence.simple_ratio} />
        <MetricRow label="Compound Sentences" value={sentence.compound_ratio} />
        <MetricRow label="Complex Sentences" value={sentence.complex_ratio} />
        <MetricRow label="Questions" value={sentence.question_ratio} />
        <MetricRow label="Exclamations" value={sentence.exclamation_ratio} />
      </div>

      {/* Paragraph */}
      <div className="border rounded-lg p-4 bg-card space-y-3">
        <h4 className="text-sm font-semibold">Paragraph Style</h4>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Avg Length</span>
          <span className="font-medium">{paragraph.avg_length.toFixed(1)} sentences</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Avg Word Count</span>
          <span className="font-medium">{paragraph.avg_word_count.toFixed(0)} words</span>
        </div>
        <MetricRow label="Transition Word Density" value={paragraph.transition_word_density} />
        <MetricRow label="Short Paragraphs" value={paragraph.short_paragraph_ratio} />
        <MetricRow label="Long Paragraphs" value={paragraph.long_paragraph_ratio} />
      </div>

      {/* Rhetorical */}
      <div className="border rounded-lg p-4 bg-card space-y-3">
        <h4 className="text-sm font-semibold">Rhetorical Devices</h4>
        <MetricRow label="Metaphor Density" value={rhetorical.metaphor_density} />
        <MetricRow label="Simile Density" value={rhetorical.simile_density} />
        <MetricRow label="Alliteration" value={rhetorical.alliteration_density} />
        <MetricRow label="Emotional Intensity" value={rhetorical.emotional_intensity} />
        <MetricRow label="Humor Markers" value={rhetorical.humor_marker_density} />
      </div>

      {/* Dialogue */}
      <div className="border rounded-lg p-4 bg-card space-y-3 md:col-span-2">
        <h4 className="text-sm font-semibold">Dialogue</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricRow label="Dialogue Ratio" value={dialogue.dialogue_ratio} />
          <MetricRow label="Said Tags" value={dialogue.said_tag_ratio} />
          <MetricRow label="Action Beats" value={dialogue.action_beat_ratio} />
          <MetricRow label="Dialogue-to-Narrative" value={dialogue.dialogue_to_narrative_ratio} />
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Avg Dialogue Length</span>
          <span className="font-medium">{dialogue.avg_dialogue_length.toFixed(1)} words</span>
        </div>
      </div>
    </div>
  );
}

// ── Style Metrics summary cards ────────────────────────────────

function StyleMetrics({
  confidence,
  wordCount,
  sampleCount,
}: {
  confidence: number;
  wordCount: number;
  sampleCount: number;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="border rounded-lg p-4 bg-card">
        <div className="text-xs text-muted-foreground mb-1">Confidence</div>
        <div className="text-2xl font-bold">{Math.round(confidence * 100)}%</div>
        <Progress value={confidence * 100} className="h-1.5 mt-2" />
      </div>
      <div className="border rounded-lg p-4 bg-card">
        <div className="text-xs text-muted-foreground mb-1">Total Words</div>
        <div className="text-2xl font-bold">{wordCount.toLocaleString()}</div>
      </div>
      <div className="border rounded-lg p-4 bg-card">
        <div className="text-xs text-muted-foreground mb-1">Samples</div>
        <div className="text-2xl font-bold">{sampleCount}</div>
      </div>
    </div>
  );
}

// ── Test & Refine component ────────────────────────────────────

function TestRefine({
  profileId,
  profileReady,
}: {
  profileId: string;
  profileReady: boolean;
}) {
  const conformityMutation = useConformityCheck(profileId);
  const generateMutation = useGenerateSample(profileId);
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generatedText, setGeneratedText] = useState("");

  const handleConformityCheck = async (text: string) => {
    return await conformityMutation.mutateAsync({ text });
  };

  const handleGenerate = async () => {
    if (!generatePrompt.trim()) return;
    const result = await generateMutation.mutateAsync({
      prompt: generatePrompt,
      max_words: 300,
    });
    setGeneratedText(result.generated_text);
  };

  if (!profileReady) {
    return (
      <div className="border rounded-lg bg-card p-8 text-center">
        <FlaskConical className="h-8 w-8 text-muted-foreground mx-auto mb-3" aria-hidden="true" />
        <p className="text-muted-foreground">
          Profile must be in &quot;ready&quot; status to test and refine.
          Add samples and analyze first.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Generate sample */}
      <div className="border rounded-lg bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">Generate Sample Text</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Generate text in this style to preview how it sounds.
        </p>
        <div className="space-y-4">
          <div>
            <label htmlFor="generate-prompt" className="block text-sm font-medium mb-2">
              Prompt
            </label>
            <input
              id="generate-prompt"
              type="text"
              value={generatePrompt}
              onChange={(e) => setGeneratePrompt(e.target.value)}
              placeholder="E.g., Write a short passage about a rainy day"
              className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <Button
            onClick={handleGenerate}
            disabled={!generatePrompt.trim() || generateMutation.isPending}
          >
            {generateMutation.isPending ? "Generating..." : "Generate"}
          </Button>
          {generatedText && (
            <div className="border rounded-lg p-4 bg-muted/30">
              <h4 className="text-sm font-medium mb-2">Generated Text</h4>
              <p className="text-sm whitespace-pre-wrap">{generatedText}</p>
            </div>
          )}
        </div>
      </div>

      {/* Conformity checker */}
      <ConformityChecker
        onCheck={handleConformityCheck}
        isChecking={conformityMutation.isPending}
      />
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StyleProfileDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = (searchParams.get("tab") as TabValue) || "overview";

  const { data: profile, isPending } = useStyleProfile(id);
  const { data: fingerprintData, isPending: fingerprintLoading } = useStyleFingerprint(id);
  const analyzeMutation = useAnalyzeProfile(id);
  const deleteMutation = useDeleteProfile();

  const [showAddSamples, setShowAddSamples] = useState(false);

  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "overview") {
      params.delete("tab");
    } else {
      params.set("tab", value);
    }
    const qs = params.toString();
    router.replace(`/style-profiles/${id}${qs ? `?${qs}` : ""}`, { scroll: false });
  };

  const handleAnalyze = async (texts: string[]) => {
    await analyzeMutation.mutateAsync({ sample_texts: texts });
    setShowAddSamples(false);
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this profile? This cannot be undone.")) return;
    await deleteMutation.mutateAsync(id);
    router.push("/style-profiles");
  };

  // ── Loading state ──────────────────────────────────────────────

  if (isPending) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-lg text-muted-foreground">Profile not found</p>
        <Link href="/style-profiles" className="mt-4 text-primary hover:underline">
          Back to profiles
        </Link>
      </div>
    );
  }

  // ── Derived state ──────────────────────────────────────────────

  const statusColors: Record<string, string> = {
    pending: "bg-gray-100 text-gray-700",
    analyzing: "bg-blue-100 text-blue-700",
    ready: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  const isReady = profile.status === "ready";

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/style-profiles"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to Profiles
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold truncate">{profile.name}</h1>
            {profile.genre && (
              <Badge variant="secondary">{profile.genre}</Badge>
            )}
            <span className={`text-xs px-3 py-1 rounded-full ${statusColors[profile.status]}`}>
              {profile.status}
            </span>
            {isReady && (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                Active
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span>
              Created {new Date(profile.created_at).toLocaleDateString()}
            </span>
            <span>{profile.sample_count} sample{profile.sample_count !== 1 ? "s" : ""}</span>
          </div>
          {profile.description && (
            <p className="text-sm text-muted-foreground mt-1">{profile.description}</p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/style-profiles/${id}/edit`}>
              <Pencil className="h-4 w-4 mr-2" aria-hidden="true" />
              Edit Profile
            </Link>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleTabChange("test")}
          >
            <FlaskConical className="h-4 w-4 mr-2" aria-hidden="true" />
            Test Style
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="h-9 w-9">
                <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
                <span className="sr-only">More actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={handleDelete}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" aria-hidden="true" />
                Delete Profile
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          {TABS.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* ─── Overview Tab ──────────────────────────────────────── */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          <StyleMetrics
            confidence={profile.confidence}
            wordCount={profile.word_count}
            sampleCount={profile.sample_count}
          />

          {/* Voice Fingerprint — StyleAnalysis radar + attributes */}
          <StyleAnalysis
            styleCard={profile.style_card}
            loading={profile.status === "analyzing"}
          />

          {/* Detailed Voice Characteristics from fingerprint */}
          {fingerprintLoading && (
            <div className="space-y-4">
              <Skeleton className="h-6 w-48" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Skeleton className="h-64" />
                <Skeleton className="h-64" />
              </div>
            </div>
          )}
          {fingerprintData?.fingerprint && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Voice Characteristics</h3>
              <VoiceCharacteristics fingerprint={fingerprintData.fingerprint} />
            </div>
          )}
        </TabsContent>

        {/* ─── Samples Tab ───────────────────────────────────────── */}
        <TabsContent value="samples" className="space-y-6 mt-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              Samples ({profile.sample_count})
            </h3>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => analyzeMutation.mutateAsync({ sample_texts: [] })}
                disabled={analyzeMutation.isPending || profile.sample_count === 0}
              >
                <RefreshCw
                  className={`h-4 w-4 mr-2 ${analyzeMutation.isPending ? "animate-spin" : ""}`}
                  aria-hidden="true"
                />
                Re-Analyze
              </Button>
              <Button size="sm" onClick={() => setShowAddSamples(!showAddSamples)}>
                <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
                Add More Samples
              </Button>
            </div>
          </div>

          {showAddSamples && (
            <div className="border rounded-lg bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">Add Sample Texts</h3>
              <TextIngestion
                onSubmit={handleAnalyze}
                isSubmitting={analyzeMutation.isPending}
              />
            </div>
          )}

          {/* Sample list */}
          {profile.sample_count === 0 ? (
            <div className="border rounded-lg bg-card p-8 text-center">
              <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-3" aria-hidden="true" />
              <p className="text-muted-foreground mb-4">
                No samples added yet. Add writing samples to analyze your style.
              </p>
              <Button onClick={() => setShowAddSamples(true)}>
                <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
                Add Samples
              </Button>
            </div>
          ) : (
            <div className="border rounded-lg bg-card divide-y">
              <div className="px-4 py-3 text-xs font-medium text-muted-foreground flex items-center gap-4">
                <span className="flex-1">Preview</span>
                <span className="w-24 text-right">Word Count</span>
              </div>
              {/* Placeholder sample rows — real samples would come from an API listing endpoint */}
              {Array.from({ length: Math.min(profile.sample_count, 5) }).map((_, i) => (
                <div key={i} className="px-4 py-3 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate text-muted-foreground">
                      Sample {i + 1} — Preview text would appear here from the full samples endpoint...
                    </p>
                  </div>
                  <span className="w-24 text-right text-sm text-muted-foreground">
                    {Math.round(profile.word_count / profile.sample_count).toLocaleString()}
                  </span>
                </div>
              ))}
              {profile.sample_count > 5 && (
                <div className="px-4 py-3 text-center text-sm text-muted-foreground">
                  + {profile.sample_count - 5} more sample{profile.sample_count - 5 !== 1 ? "s" : ""}
                </div>
              )}
            </div>
          )}
        </TabsContent>

        {/* ─── Test & Refine Tab ─────────────────────────────────── */}
        <TabsContent value="test" className="mt-6">
          <TestRefine profileId={id} profileReady={isReady} />
        </TabsContent>

        {/* ─── Usage Tab ─────────────────────────────────────────── */}
        <TabsContent value="usage" className="mt-6">
          <div className="border rounded-lg bg-card p-8 text-center">
            <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-3" aria-hidden="true" />
            <p className="text-lg font-medium mb-1">Coming Soon</p>
            <p className="text-sm text-muted-foreground">
              Coming soon — will show which manuscripts use this profile
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
