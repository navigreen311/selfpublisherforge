"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { useCreateChildrensBook } from "@/modules/specialty/childrens/hooks";
import {
  Step1BookDetails,
  Step2FormatStyle,
  Step3StorySetup,
  Step4ContentSafety,
  DEFAULT_WIZARD_DATA,
  type WizardData,
} from "@/modules/specialty/childrens/components/WizardSteps";

// ---------------------------------------------------------------------------
// Step metadata
// ---------------------------------------------------------------------------

const STEPS = [
  { label: "Book Details", number: 1 },
  { label: "Format & Style", number: 2 },
  { label: "Story Setup", number: 3 },
  { label: "Content Safety", number: 4 },
];

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateStep(step: number, data: WizardData): string | null {
  switch (step) {
    case 1:
      if (!data.title.trim()) return "Title is required";
      if (!data.age_range) return "Please select an age range";
      if (data.is_bilingual && !data.bilingual_language)
        return "Please select a second language";
      return null;
    case 2:
      if (!data.page_count) return "Please select a page count";
      if (!data.trim_size) return "Please select a trim size";
      if (!data.illustration_style) return "Please select an illustration style";
      if (!data.color_palette) return "Please select a color palette";
      return null;
    case 3:
      if (data.creation_mode === "ai-generate" && !data.story_prompt.trim())
        return "Please provide a story prompt for AI generation";
      return null;
    case 4:
      return null;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function CreateChildrensBookPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState<WizardData>(DEFAULT_WIZARD_DATA);
  const [error, setError] = useState<string | null>(null);

  const createBook = useCreateChildrensBook();

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

    createBook.mutate(
      {
        title: data.title,
        subtitle: data.subtitle || undefined,
        author: data.author || "self",
        age_range: data.age_range,
        page_count: parseInt(data.page_count, 10),
        trim_size: data.trim_size,
        illustration_style: data.illustration_style,
        color_palette: data.color_palette,
        story_mode: data.story_mode,
        creation_mode: data.creation_mode,
        is_bilingual: data.is_bilingual,
        bilingual_language: data.is_bilingual
          ? data.bilingual_language
          : undefined,
        bilingual_layout: data.is_bilingual
          ? data.bilingual_layout
          : undefined,
        fear_intensity: data.fear_intensity,
        tone: data.tone,
        theme_moral: data.theme_moral || undefined,
        main_character: data.main_character || undefined,
        setting: data.setting || undefined,
        story_prompt:
          data.creation_mode === "ai-generate"
            ? data.story_prompt
            : undefined,
        safety_settings: {
          no_weapons: data.safety_no_weapons,
          no_scary: data.safety_no_scary,
          no_trademarks: data.safety_no_trademarks,
          no_stereotypes: data.safety_no_stereotypes,
          age_vocabulary: data.safety_age_vocabulary,
          trademark_enforcement: data.safety_trademark_enforcement,
          content_precheck: data.safety_content_precheck,
          provenance_logging: data.safety_provenance_logging,
        },
      },
      {
        onSuccess: (book) => {
          router.push(`/specialty/childrens-books/${book.id}`);
        },
      },
    );
  };

  return (
    <div className="container mx-auto py-6 max-w-3xl space-y-6">
      {/* Back link */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5">
        <Link href="/specialty/childrens-books">
          <ChevronLeft className="h-4 w-4" />
          Back to Children&apos;s Books
        </Link>
      </Button>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold">Create Children&apos;s Book</h1>
        <p className="text-muted-foreground">
          Set up your new illustrated children&apos;s book in 4 steps.
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
          <Step2FormatStyle data={data} onChange={handleChange} />
        )}
        {currentStep === 3 && (
          <Step3StorySetup data={data} onChange={handleChange} />
        )}
        {currentStep === 4 && (
          <Step4ContentSafety data={data} onChange={handleChange} />
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
            disabled={createBook.isPending}
          >
            {createBook.isPending ? "Creating..." : "Create Book"}
            <Check className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  );
}
