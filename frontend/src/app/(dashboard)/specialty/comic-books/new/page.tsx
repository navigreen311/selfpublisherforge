"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { useCreateComic } from "@/modules/specialty/comic/hooks";
import {
  Step1BookDetails,
  Step2ArtStyle,
  Step3StoryCharacters,
  Step4ContentSettings,
  DEFAULT_WIZARD_DATA,
  type WizardData,
} from "@/modules/specialty/comic/components/WizardSteps";

// ---------------------------------------------------------------------------
// Step metadata
// ---------------------------------------------------------------------------

const STEPS = [
  { label: "Details", number: 1 },
  { label: "Art Style", number: 2 },
  { label: "Story & Characters", number: 3 },
  { label: "Content Settings", number: 4 },
];

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateStep(step: number, data: WizardData): string | null {
  switch (step) {
    case 1:
      if (!data.title.trim()) return "Title is required";
      if (!data.target_audience) return "Please select a target audience";
      return null;
    case 2:
      if (!data.page_count) return "Please select a page count";
      if (!data.trim_size) return "Please select a trim size";
      if (!data.art_style) return "Please select an art style";
      return null;
    case 3:
      return null;
    case 4:
      return null;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Template presets from URL query params
// ---------------------------------------------------------------------------

function applyTemplate(
  base: WizardData,
  template: string | null,
): WizardData {
  if (!template) return base;
  switch (template) {
    case "superhero":
      return {
        ...base,
        format: "single_issue",
        art_style: "american_classic",
        color_mode: "full_color",
        genre: "Superhero",
        pacing: "action",
      };
    case "manga":
      return {
        ...base,
        format: "manga",
        art_style: "manga",
        color_mode: "black_white",
        trim_size: "5.5x8.5",
        genre: "Manga",
        pacing: "balanced",
      };
    case "indie":
      return {
        ...base,
        format: "graphic_novel",
        art_style: "indie",
        color_mode: "limited_palette",
        genre: "Slice-of-Life",
        pacing: "decompressed",
      };
    default:
      return base;
  }
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function CreateComicBookPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const template = searchParams.get("template");

  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState<WizardData>(() =>
    applyTemplate(DEFAULT_WIZARD_DATA, template),
  );
  const [error, setError] = useState<string | null>(null);

  const createComic = useCreateComic();

  const progress = (currentStep / STEPS.length) * 100;

  const handleChange = (updates: Partial<WizardData>) => {
    setData((prev) => ({ ...prev, ...updates }));
    setError(null);
  };

  const handleNext = () => {
    const validationError = validateStep(currentStep, data);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setCurrentStep((s) => Math.min(s + 1, STEPS.length));
  };

  const handleBack = () => {
    setError(null);
    setCurrentStep((s) => Math.max(s - 1, 1));
  };

  const handleCreate = () => {
    const validationError = validateStep(currentStep, data);
    if (validationError) {
      setError(validationError);
      return;
    }

    createComic.mutate(
      {
        title: data.title,
        subtitle: data.subtitle || undefined,
        author: data.author || undefined,
        artist: data.artist || undefined,
        format: data.format,
        target_audience: data.target_audience,
        page_count: parseInt(data.page_count, 10),
        trim_size: data.trim_size,
        art_style: data.art_style,
        color_mode: data.color_mode,
        ink_style: data.ink_style,
        border_style: data.border_style,
        gutter_style: data.gutter_style,
        genre: data.genre || undefined,
        premise: data.premise || undefined,
        pacing: data.pacing,
        characters: data.characters,
        content_rating: data.content_rating,
        violence_level: data.violence_level,
        language_level: data.language_level,
        safety_settings: {
          no_gore: data.safety_no_gore,
          no_explicit: data.safety_no_explicit,
          no_hate: data.safety_no_hate,
          age_appropriate: data.safety_age_appropriate,
        },
      },
      {
        onSuccess: (comic) => {
          router.push(`/specialty/comic-books/${comic.id}`);
        },
      },
    );
  };

  return (
    <div className="container mx-auto py-6 max-w-3xl space-y-6">
      <Breadcrumb items={[
        { label: "Specialty", href: "/specialty" },
        { label: "Comic Books", href: "/specialty/comic-books" },
        { label: "New" },
      ]} />
      {/* Back link */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5">
        <Link href="/specialty/comic-books">
          <ChevronLeft className="h-4 w-4" />
          Back to Comic Books
        </Link>
      </Button>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold">Create Comic Book</h1>
        <p className="text-muted-foreground">
          Set up your new comic book in 4 steps.
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          {STEPS.map((step) => (
            <button
              key={step.number}
              onClick={() => {
                if (step.number < currentStep) {
                  setCurrentStep(step.number);
                  setError(null);
                }
              }}
              className={cn(
                "flex items-center gap-2 text-sm transition-colors",
                step.number === currentStep
                  ? "text-primary font-medium"
                  : step.number < currentStep
                    ? "text-foreground cursor-pointer hover:text-primary"
                    : "text-muted-foreground",
              )}
            >
              <span
                className={cn(
                  "h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold border-2 transition-colors",
                  step.number === currentStep
                    ? "border-primary bg-primary text-primary-foreground"
                    : step.number < currentStep
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-muted-foreground/30",
                )}
              >
                {step.number < currentStep ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  step.number
                )}
              </span>
              <span className="hidden sm:inline">{step.label}</span>
            </button>
          ))}
        </div>
        <Progress value={progress} className="h-1.5" />
      </div>

      <Separator />

      {/* Step Content */}
      <div className="min-h-[400px]">
        {currentStep === 1 && (
          <Step1BookDetails data={data} onChange={handleChange} />
        )}
        {currentStep === 2 && (
          <Step2ArtStyle data={data} onChange={handleChange} />
        )}
        {currentStep === 3 && (
          <Step3StoryCharacters data={data} onChange={handleChange} />
        )}
        {currentStep === 4 && (
          <Step4ContentSettings data={data} onChange={handleChange} />
        )}
      </div>

      {/* Error message */}
      {error && (
        <p className="text-sm text-destructive font-medium">{error}</p>
      )}

      {/* Navigation Buttons */}
      <Separator />
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={currentStep === 1}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        {currentStep < STEPS.length ? (
          <Button onClick={handleNext}>
            Next
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={handleCreate}
            disabled={createComic.isPending}
          >
            {createComic.isPending ? "Creating..." : "Create Book"}
            <Check className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  );
}
