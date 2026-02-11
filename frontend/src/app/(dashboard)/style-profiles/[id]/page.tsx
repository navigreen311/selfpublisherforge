"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, Plus, FileText, Sparkles } from "lucide-react";
import { StyleAnalysis } from "@/modules/style-profiles/components/StyleAnalysis";
import { ConformityChecker } from "@/modules/style-profiles/components/ConformityChecker";
import { TextIngestion } from "@/modules/style-profiles/components/TextIngestion";
import {
  useStyleProfile,
  useAnalyzeProfile,
  useConformityCheck,
  useGenerateSample,
} from "@/modules/style-profiles/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { useState } from "react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StyleProfileDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { data: profile, isPending } = useStyleProfile(id);
  const analyzeMutation = useAnalyzeProfile(id);
  const conformityMutation = useConformityCheck(id);
  const generateMutation = useGenerateSample(id);

  const [showAddSamples, setShowAddSamples] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generatedText, setGeneratedText] = useState("");

  const handleAnalyze = async (texts: string[]) => {
    await analyzeMutation.mutateAsync({ sample_texts: texts });
    setShowAddSamples(false);
  };

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

  if (isPending) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
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

  const statusColors = {
    pending: "bg-gray-100 text-gray-700",
    analyzing: "bg-blue-100 text-blue-700",
    ready: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Link
            href="/style-profiles"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-2"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to profiles
          </Link>
          <div className="flex items-start gap-3 mt-2">
            <Sparkles className="h-6 w-6 text-primary mt-1" aria-hidden="true" />
            <div>
              <h1 className="text-2xl font-bold">{profile.name}</h1>
              {profile.description && (
                <p className="text-sm text-muted-foreground mt-1">{profile.description}</p>
              )}
            </div>
          </div>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full shrink-0 ${statusColors[profile.status]}`}>
          {profile.status}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">Samples</div>
          <div className="text-2xl font-bold">{profile.sample_count}</div>
        </div>
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">Total Words</div>
          <div className="text-2xl font-bold">{profile.word_count.toLocaleString()}</div>
        </div>
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">Confidence</div>
          <div className="text-2xl font-bold">{Math.round(profile.confidence * 100)}%</div>
        </div>
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">Genre</div>
          <div className="text-lg font-semibold">{profile.genre || "—"}</div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => setShowAddSamples(!showAddSamples)}
          className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent transition-colors"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add Samples
        </button>
        <button
          onClick={() => setShowGenerate(!showGenerate)}
          disabled={profile.status !== "ready"}
          className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          Generate Sample
        </button>
      </div>

      {/* Add samples section */}
      {showAddSamples && (
        <div className="border rounded-lg bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Add Sample Texts</h3>
          <TextIngestion
            onSubmit={handleAnalyze}
            isSubmitting={analyzeMutation.isPending}
          />
        </div>
      )}

      {/* Generate sample section */}
      {showGenerate && (
        <div className="border rounded-lg bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Generate Sample Text</h3>
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
            <button
              onClick={handleGenerate}
              disabled={!generatePrompt.trim() || generateMutation.isPending}
              className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generateMutation.isPending ? "Generating..." : "Generate"}
            </button>
            {generatedText && (
              <div className="border rounded-lg p-4 bg-muted/30">
                <h4 className="text-sm font-medium mb-2">Generated Text</h4>
                <p className="text-sm whitespace-pre-wrap">{generatedText}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Style Analysis */}
      <StyleAnalysis
        styleCard={profile.style_card}
        loading={profile.status === "analyzing"}
      />

      {/* Conformity Checker */}
      {profile.status === "ready" && (
        <ConformityChecker
          onCheck={handleConformityCheck}
          isChecking={conformityMutation.isPending}
        />
      )}
    </div>
  );
}
