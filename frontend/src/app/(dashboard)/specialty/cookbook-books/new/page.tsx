"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { useCreateCookbook } from "@/modules/specialty/cookbook/hooks";
import type {
  ChapterOrganization,
  CookbookInteriorType,
  CookbookType,
  IllustrationMethod,
  RecipeLayout,
} from "@/modules/specialty/types/cookbook";
import {
  Step1Details,
  Step2Format,
  Step3RecipeSettings,
  DEFAULT_WIZARD_DATA,
  type WizardData,
} from "@/modules/specialty/cookbook/components/WizardSteps";

// ---------------------------------------------------------------------------
// Step metadata
// ---------------------------------------------------------------------------

const STEPS = [
  { label: "Details", number: 1 },
  { label: "Format", number: 2 },
  { label: "Recipe Settings", number: 3 },
];

// ---------------------------------------------------------------------------
// Page count estimation based on chapters and layout
// ---------------------------------------------------------------------------

function estimatePageCount(data: WizardData): number {
  const chapterCount = Math.max(data.initial_chapters.length, 1);
  const recipesPerChapter = 8;

  const pagesPerRecipe: Record<string, number> = {
    classic: 1,
    magazine: 1,
    minimal: 0.5,
    full_photo: 2,
    step_by_step: 2,
    card: 0.5,
    two_column: 0.5,
  };

  const multiplier = pagesPerRecipe[data.recipe_layout] ?? 1;
  const recipePages = Math.ceil(
    chapterCount * recipesPerChapter * multiplier,
  );

  // Add front matter (~6 pages) + chapter dividers + back matter (~10 pages)
  const overhead = 6 + chapterCount + 10;

  return recipePages + overhead;
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateStep(step: number, data: WizardData): string | null {
  switch (step) {
    case 1:
      if (!data.title.trim()) return "Title is required";
      if (!data.cookbook_type) return "Please select a cookbook type";
      if (data.cookbook_type === "diet_lifestyle" && !data.cuisine_diet)
        return "Please select a cuisine or diet";
      return null;
    case 2:
      if (!data.trim_size) return "Please select a trim size";
      if (!data.chapter_organization)
        return "Please select a chapter organization";
      return null;
    case 3:
      if (!data.recipe_layout) return "Please select a recipe layout";
      return null;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function CreateCookbookPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState<WizardData>(DEFAULT_WIZARD_DATA);
  const [error, setError] = useState<string | null>(null);

  const createCookbook = useCreateCookbook();

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

    createCookbook.mutate(
      {
        title: data.title,
        subtitle: data.subtitle || undefined,
        author: data.author || "self",
        cookbook_type: data.cookbook_type as CookbookType,
        cuisine: data.cuisine || undefined,
        cuisine_diet: data.cuisine_diet || undefined,
        target_audience: data.target_audience || undefined,
        description: data.description || undefined,
        trim_size: data.trim_size,
        interior_type: data.interior_type as CookbookInteriorType,
        chapter_organization: data.chapter_organization as ChapterOrganization,
        page_count: estimatePageCount(data),
        recipe_layout: data.recipe_layout as RecipeLayout,
        illustration_method: data.illustration_method as IllustrationMethod,
        include_nutrition: data.include_nutrition,
        include_meal_plans: data.include_meal_plans,
        include_shopping_lists: data.include_shopping_lists,
        include_index: data.include_index,
        include_conversion_charts: data.include_conversion_charts,
        dietary_tags: data.dietary_tags,
      },
      {
        onSuccess: (cookbook) => {
          router.push(`/specialty/cookbook-books/${cookbook.id}`);
        },
      },
    );
  };

  return (
    <div className="container mx-auto py-6 max-w-3xl space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb items={[
        { label: "Specialty", href: "/specialty" },
        { label: "Cookbooks", href: "/specialty/cookbook-books" },
        { label: "New" },
      ]} />

      {/* Back link */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5">
        <Link href="/specialty/cookbook-books">
          <ChevronLeft className="h-4 w-4" />
          Back to Cookbooks
        </Link>
      </Button>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold">Create Cookbook</h1>
        <p className="text-muted-foreground">
          Set up your new cookbook in 3 steps.
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
          <Step1Details data={data} onChange={handleChange} />
        )}
        {currentStep === 2 && (
          <Step2Format data={data} onChange={handleChange} />
        )}
        {currentStep === 3 && (
          <Step3RecipeSettings data={data} onChange={handleChange} />
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
            disabled={createCookbook.isPending}
          >
            {createCookbook.isPending ? "Creating..." : "Create Cookbook"}
            <Check className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  );
}
