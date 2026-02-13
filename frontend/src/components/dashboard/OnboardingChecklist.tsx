"use client";

import * as React from "react";
import Link from "next/link";
import { Check, X } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const STORAGE_KEY = "spf-onboarding";

interface OnboardingChecklistProps {
  hasProjects: boolean;
  onDismiss: () => void;
}

interface OnboardingState {
  completedSteps: number[];
  dismissed: boolean;
}

interface Step {
  id: number;
  titleKey: string;
  descriptionKey: string;
  href: string | null;
  alwaysComplete: boolean;
}

const STEPS: Step[] = [
  {
    id: 1,
    titleKey: "onboarding.step1Title",
    descriptionKey: "onboarding.step1Description",
    href: null,
    alwaysComplete: true,
  },
  {
    id: 2,
    titleKey: "onboarding.step2Title",
    descriptionKey: "onboarding.step2Description",
    href: "/projects/new",
    alwaysComplete: false,
  },
  {
    id: 3,
    titleKey: "onboarding.step3Title",
    descriptionKey: "onboarding.step3Description",
    href: "/market",
    alwaysComplete: false,
  },
  {
    id: 4,
    titleKey: "onboarding.step4Title",
    descriptionKey: "onboarding.step4Description",
    href: "/writing",
    alwaysComplete: false,
  },
  {
    id: 5,
    titleKey: "onboarding.step5Title",
    descriptionKey: "onboarding.step5Description",
    href: "/settings",
    alwaysComplete: false,
  },
];

function loadState(): OnboardingState {
  if (typeof window === "undefined") {
    return { completedSteps: [1], dismissed: false };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as OnboardingState;
      // Ensure step 1 is always present
      if (!parsed.completedSteps.includes(1)) {
        parsed.completedSteps = [1, ...parsed.completedSteps];
      }
      return parsed;
    }
  } catch {
    // Corrupted storage — reset
  }
  return { completedSteps: [1], dismissed: false };
}

function saveState(state: OnboardingState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}

export function OnboardingChecklist({ hasProjects, onDismiss }: OnboardingChecklistProps) {
  const t = useTranslations("dashboard");
  const [state, setState] = React.useState<OnboardingState>(() => loadState());

  // Sync state to localStorage whenever it changes
  React.useEffect(() => {
    saveState(state);
  }, [state]);

  // If the user already has projects, mark step 2 as complete
  React.useEffect(() => {
    if (hasProjects && !state.completedSteps.includes(2)) {
      setState((prev) => ({
        ...prev,
        completedSteps: [...prev.completedSteps, 2],
      }));
    }
  }, [hasProjects, state.completedSteps]);

  const completedCount = state.completedSteps.length;
  const progressPercent = (completedCount / STEPS.length) * 100;

  const isStepComplete = (stepId: number): boolean => {
    return state.completedSteps.includes(stepId);
  };

  const handleDismiss = () => {
    setState((prev) => ({ ...prev, dismissed: true }));
    onDismiss();
  };

  // Don't render if dismissed
  if (state.dismissed) {
    return null;
  }

  return (
    <Card className="border bg-card">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div className="space-y-1">
          <CardTitle className="text-lg font-semibold">
            {t("onboarding.title")}
          </CardTitle>
          <CardDescription>
            {t("onboarding.subtitle")}
          </CardDescription>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          onClick={handleDismiss}
          aria-label="Dismiss onboarding checklist"
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Steps list */}
        <div className="space-y-3">
          {STEPS.map((step) => {
            const completed = isStepComplete(step.id);

            return (
              <div
                key={step.id}
                className="flex items-start gap-3"
              >
                {/* Step indicator */}
                <div className="mt-0.5 shrink-0">
                  {completed ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                      <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                    </div>
                  ) : (
                    <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
                  )}
                </div>

                {/* Step content */}
                <div className="flex flex-1 items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <p
                      className={
                        completed
                          ? "text-sm font-medium text-green-600 dark:text-green-400"
                          : "text-sm font-medium text-foreground"
                      }
                    >
                      {t(step.titleKey)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t(step.descriptionKey)}
                    </p>
                  </div>

                  {/* Action */}
                  <div className="shrink-0">
                    {completed ? (
                      <span className="text-xs font-medium text-green-600 dark:text-green-400">
                        {t("onboarding.complete")}
                      </span>
                    ) : step.href ? (
                      <Button variant="link" size="sm" className="h-auto p-0 text-xs" asChild>
                        <Link href={step.href}>
                          {t("onboarding.start")} &rarr;
                        </Link>
                      </Button>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="space-y-2 pt-2">
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {t("onboarding.progress", { completed: completedCount, total: STEPS.length })}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
