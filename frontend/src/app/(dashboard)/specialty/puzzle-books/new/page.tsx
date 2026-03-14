"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { useCreatePuzzleBook } from "@/modules/specialty/puzzles/hooks";
import {
  Step1BookDetails,
  Step2PuzzleSelection,
  Step3ThemesWords,
  Step4LayoutExtras,
  DEFAULT_WIZARD_DATA,
  type WizardData,
} from "@/modules/specialty/puzzles/components/WizardSteps";

// ---------------------------------------------------------------------------
// Step metadata
// ---------------------------------------------------------------------------

const STEPS = [
  { label: "Book Details", number: 1 },
  { label: "Puzzle Selection", number: 2 },
  { label: "Themes & Words", number: 3 },
  { label: "Layout & Extras", number: 4 },
];

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateStep(step: number, data: WizardData): string | null {
  switch (step) {
    case 1:
      if (!data.title.trim()) return "Title is required";
      if (!data.audience) return "Please select an audience";
      if (data.series_enabled && !data.series_name.trim())
        return "Please enter a series name";
      return null;
    case 2:
      if (data.selected_puzzle_types.length === 0)
        return "Please select at least one puzzle type";
      return null;
    case 3:
      if (
        (data.theme_input_method === "ai_generate" ||
          data.theme_input_method === "mix") &&
        data.themes.length === 0
      )
        return "Please select at least one theme category";
      if (
        (data.theme_input_method === "custom" ||
          data.theme_input_method === "mix") &&
        !data.custom_word_list.trim()
      )
        return "Please enter custom words";
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

export default function CreatePuzzleBookPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState<WizardData>(DEFAULT_WIZARD_DATA);
  const [error, setError] = useState<string | null>(null);

  const createBook = useCreatePuzzleBook();

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

    const extras: string[] = [];
    if (data.extras_toc) extras.push("toc");
    if (data.extras_instructions) extras.push("instructions");
    if (data.extras_difficulty_badges) extras.push("difficulty_badges");
    if (data.extras_section_dividers) extras.push("section_dividers");

    createBook.mutate(
      {
        title: data.title,
        subtitle: data.subtitle || undefined,
        audience: data.audience as "kids" | "teens" | "adults" | "large_print",
        puzzle_config: data.selected_puzzle_types,
        difficulty_mode: data.difficulty_mode as
          | "progressive"
          | "fixed"
          | "mixed",
        themes: data.themes,
        seasonal_theme: data.seasonal_enabled
          ? data.seasonal_theme
          : undefined,
        word_difficulty: data.word_difficulty as
          | "simple"
          | "standard"
          | "advanced",
        clue_style: data.clue_style as
          | "standard"
          | "kid_friendly"
          | "trivia"
          | "themed",
        answer_key_position: data.answer_key_position as
          | "back"
          | "reverse"
          | "none",
        layout: data.layout as "one_per_page" | "two_per_page",
        extras,
        hint_config:
          Object.keys(data.hint_config).length > 0
            ? data.hint_config
            : undefined,
        puzzle_mix_template:
          data.selected_puzzle_types.length > 1
            ? (data.puzzle_mix_template as
                | "balanced"
                | "word_heavy"
                | "custom")
            : undefined,
        custom_percentages:
          data.puzzle_mix_template === "custom"
            ? data.custom_percentages
            : undefined,
        theme_input_method: data.theme_input_method,
        series_name: data.series_enabled ? data.series_name : undefined,
        volume_number: data.series_enabled
          ? parseInt(data.volume_number, 10) || undefined
          : undefined,
      },
      {
        onSuccess: (book) => {
          router.push(`/specialty/puzzle-books/${book.id}`);
        },
      }
    );
  };

  return (
    <div className="container mx-auto py-6 max-w-3xl space-y-6">
      {/* Back link */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5">
        <Link href="/specialty/puzzle-books">
          <ChevronLeft className="h-4 w-4" />
          Back to Puzzle Books
        </Link>
      </Button>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold">Create Puzzle Book</h1>
        <p className="text-muted-foreground">
          Set up your new puzzle book in 4 steps.
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
                    : "text-muted-foreground"
              )}
            >
              <span
                className={cn(
                  "h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold border-2 transition-colors",
                  step.number === currentStep
                    ? "border-primary bg-primary text-primary-foreground"
                    : step.number < currentStep
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-muted-foreground/30"
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
          <Step2PuzzleSelection data={data} onChange={handleChange} />
        )}
        {currentStep === 3 && (
          <Step3ThemesWords data={data} onChange={handleChange} />
        )}
        {currentStep === 4 && (
          <Step4LayoutExtras data={data} onChange={handleChange} />
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
