"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { TextIngestion } from "@/modules/style-profiles/components/TextIngestion";
import { PresetPicker } from "@/modules/style-profiles/components/PresetPicker";
import { StyleAnalysis } from "@/modules/style-profiles/components/StyleAnalysis";
import { useCreateProfile } from "@/modules/style-profiles/hooks";
import type { ProfileResponse } from "@/modules/style-profiles/types";
import { useTranslations } from "@/hooks/use-translations";

const STEP_LABELS = ["new.stepBasicInfo", "new.stepSamples", "new.stepAnalysis"] as const;

export default function NewStyleProfilePage() {
  const router = useRouter();
  const t = useTranslations("style-profiles");
  const createMutation = useCreateProfile();

  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState("");
  const [preset, setPreset] = useState<string | null>(null);
  const [voiceDescription, setVoiceDescription] = useState("");
  const [createdProfile, setCreatedProfile] = useState<ProfileResponse | null>(null);

  const handleBasicInfoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      setStep(2);
    }
  };

  const handleTextSubmit = async (texts: string[]) => {
    try {
      const profile = await createMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        genre: genre.trim() || undefined,
        sample_texts: texts,
      });
      setCreatedProfile(profile);
      setStep(3);
    } catch (error) {
      console.error("Failed to create profile:", error);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/style-profiles"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t("new.backToProfiles")}
        </Link>
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-primary" aria-hidden="true" />
          <h1 className="text-2xl font-bold">{t("new.title")}</h1>
        </div>
      </div>

      {/* Progress indicator — 3 steps */}
      <div className="flex items-center gap-2">
        {STEP_LABELS.map((labelKey, idx) => {
          const stepNum = idx + 1;
          return (
            <div key={labelKey} className="flex items-center gap-2 flex-1 last:flex-none">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium shrink-0 ${
                  step >= stepNum
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {stepNum}
              </div>
              <span
                className={`text-xs hidden sm:inline ${
                  step >= stepNum ? "text-foreground font-medium" : "text-muted-foreground"
                }`}
              >
                {t(labelKey)}
              </span>
              {idx < STEP_LABELS.length - 1 && (
                <div
                  className={`flex-1 h-1 ${
                    step > stepNum ? "bg-primary" : "bg-muted"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Step 1: Basic Information + Quick Start */}
      {step === 1 && (
        <div className="border rounded-lg bg-card p-6">
          <h2 className="text-lg font-semibold mb-4">{t("new.basicInfo")}</h2>
          <form onSubmit={handleBasicInfoSubmit} className="space-y-4">
            <div>
              <label htmlFor="profile-name" className="block text-sm font-medium mb-2">
                {t("new.profileName")} <span className="text-destructive">*</span>
              </label>
              <input
                id="profile-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("new.profileNamePlaceholder")}
                className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                required
              />
            </div>

            <div>
              <label htmlFor="profile-description" className="block text-sm font-medium mb-2">
                {t("new.description")}
              </label>
              <textarea
                id="profile-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t("new.descriptionPlaceholder")}
                rows={3}
                className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div>
              <label htmlFor="profile-genre" className="block text-sm font-medium mb-2">
                {t("new.genre")}
              </label>
              <input
                id="profile-genre"
                type="text"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                placeholder={t("new.genrePlaceholder")}
                className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            {/* Quick Start: Preset Picker */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-semibold mb-3">{t("new.quickStart")}</h3>
              <PresetPicker selectedPreset={preset} onSelect={setPreset} />
            </div>

            {/* Voice Description textarea */}
            <div>
              <label htmlFor="voice-description" className="block text-sm font-medium mb-2">
                {t("new.voiceDescriptionLabel")}
              </label>
              <textarea
                id="voice-description"
                value={voiceDescription}
                onChange={(e) => setVoiceDescription(e.target.value)}
                placeholder={t("new.voiceDescriptionPlaceholder")}
                rows={3}
                className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={!name.trim()}
                className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t("new.nextAddSamples")}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Step 2: Add Sample Texts */}
      {step === 2 && (
        <div className="border rounded-lg bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">{t("new.addSampleTexts")}</h2>
            <button
              onClick={() => setStep(1)}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {t("new.editInfo")}
            </button>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            {t("new.samplesDescription")}
          </p>
          <TextIngestion
            onSubmit={handleTextSubmit}
            isSubmitting={createMutation.isPending}
          />
        </div>
      )}

      {/* Step 3: Analysis Results */}
      {step === 3 && createdProfile && (
        <div className="space-y-6">
          <div className="border rounded-lg bg-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{t("new.stepAnalysis")}</h2>
              <button
                onClick={() => router.push(`/style-profiles/${createdProfile.id}`)}
                className="px-4 py-2 text-sm border rounded-lg hover:bg-accent"
              >
                {t("new.editInfo")}
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              {t("new.analysisDescription")}
            </p>
          </div>

          <StyleAnalysis
            styleCard={createdProfile.style_card}
            loading={createdProfile.status === "analyzing"}
          />

          <div className="flex justify-end">
            <button
              onClick={() => router.push(`/style-profiles/${createdProfile.id}`)}
              className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {t("detail.backToProfiles")}
            </button>
          </div>
        </div>
      )}

      {/* Error message */}
      {createMutation.isError && (
        <div className="border border-destructive rounded-lg p-4 bg-destructive/10">
          <p className="text-sm text-destructive">
            {t("new.errorMessage")}
          </p>
        </div>
      )}
    </div>
  );
}
