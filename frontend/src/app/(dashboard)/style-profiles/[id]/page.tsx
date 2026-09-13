"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Sparkles } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { StyleMetrics } from "@/modules/style-profiles/components/StyleMetrics";
import { VoiceCharacteristics } from "@/modules/style-profiles/components/VoiceCharacteristics";
import { SampleComparison } from "@/modules/style-profiles/components/SampleComparison";
import { TestRefine } from "@/modules/style-profiles/components/TestRefine";
import {
  useStyleProfile,
  useStyleFingerprint,
  useAnalyzeProfile,
  useConformityCheck,
  useGenerateSample,
} from "@/modules/style-profiles/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslations } from "@/hooks/use-translations";

export default function StyleProfileDetailPage() {
  const { id } = useParams<{ id: string }>();
  const t = useTranslations("style-profiles");
  const { data: profile, isPending } = useStyleProfile(id);
  const { data: fingerprintData, isPending: fingerprintPending } = useStyleFingerprint(id);
  const analyzeMutation = useAnalyzeProfile(id);
  const conformityMutation = useConformityCheck(id);
  const generateMutation = useGenerateSample(id);

  const [activeTab, setActiveTab] = useState("overview");

  const handleAnalyze = async (texts: string[]) => {
    await analyzeMutation.mutateAsync({ sample_texts: texts });
  };

  const handleConformityCheck = async (text: string) => {
    return await conformityMutation.mutateAsync({ text });
  };

  const handleGenerate = async (prompt: string, maxWords?: number) => {
    return await generateMutation.mutateAsync({
      prompt,
      max_words: maxWords,
    });
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
        <p className="text-lg text-muted-foreground">{t("detail.notFound")}</p>
        <Link href="/style-profiles" className="mt-4 text-primary hover:underline">
          {t("detail.backToProfiles")}
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
            {t("detail.backToProfiles")}
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
          <div className="text-xs text-muted-foreground mb-1">{t("detail.stats.samples")}</div>
          <div className="text-2xl font-bold">{profile.sample_count}</div>
        </div>
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">{t("detail.stats.totalWords")}</div>
          <div className="text-2xl font-bold">{profile.word_count.toLocaleString()}</div>
        </div>
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">{t("detail.stats.confidence")}</div>
          <div className="text-2xl font-bold">{Math.round(profile.confidence * 100)}%</div>
        </div>
        <div className="border rounded-lg p-4 bg-card">
          <div className="text-xs text-muted-foreground mb-1">{t("detail.stats.genre")}</div>
          <div className="text-lg font-semibold">{profile.genre || "—"}</div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="test">Test</TabsTrigger>
          <TabsTrigger value="samples">Samples</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-4">
          {profile.style_card && (
            <VoiceCharacteristics
              styleCard={profile.style_card}
            />
          )}
          {fingerprintData?.fingerprint && (
            <StyleMetrics
              fingerprint={fingerprintData.fingerprint}
            />
          )}
        </TabsContent>

        {/* Test Tab */}
        <TabsContent value="test" className="mt-4">
          <TestRefine profileId={id} />
        </TabsContent>

        {/* Samples Tab */}
        <TabsContent value="samples" className="mt-4">
          <SampleComparison profileId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
