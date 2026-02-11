"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { TextIngestion } from "@/modules/style-profiles/components/TextIngestion";
import { useCreateProfile } from "@/modules/style-profiles/hooks";
import { useTranslations } from "@/hooks/use-translations";

export default function NewStyleProfilePage() {
  const router = useRouter();
  const t = useTranslations("style-profiles");
  const createMutation = useCreateProfile();

  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState("");

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
      router.push(`/style-profiles/${profile.id}`);
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

      {/* Progress indicator */}
      <div className="flex items-center gap-2">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${step >= 1 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
          1
        </div>
        <div className={`flex-1 h-1 ${step >= 2 ? "bg-primary" : "bg-muted"}`} />
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${step >= 2 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
          2
        </div>
      </div>

      {/* Step 1: Basic Information */}
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
