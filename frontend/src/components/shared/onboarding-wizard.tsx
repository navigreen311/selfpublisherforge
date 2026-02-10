"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export interface WizardStep {
  id: string;
  title: string;
  description?: string;
  content: React.ReactNode;
  isOptional?: boolean;
  /**
   * Async callback invoked before advancing to the next step.
   * If the promise rejects, the wizard stays on the current step.
   * Not called when the step is skipped.
   */
  onBeforeNext?: () => Promise<void>;
}

interface OnboardingWizardProps {
  steps: WizardStep[];
  onComplete: () => void;
  onSkip?: () => void;
  /** Controls whether the Continue/Complete button is disabled externally. */
  isNextDisabled?: boolean;
  /** Shows a loading spinner on the Continue/Complete button. */
  isLoading?: boolean;
  className?: string;
}

export function OnboardingWizard({
  steps,
  onComplete,
  onSkip,
  isNextDisabled = false,
  isLoading = false,
  className,
}: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = React.useState(0);
  const [transitioning, setTransitioning] = React.useState(false);
  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;
  const isLast = currentStep === steps.length - 1;

  const busy = isLoading || transitioning;

  const handleNext = async () => {
    if (busy) return;

    // Run the step's onBeforeNext hook if present
    if (step.onBeforeNext) {
      setTransitioning(true);
      try {
        await step.onBeforeNext();
      } catch {
        // onBeforeNext rejected -- stay on current step
        setTransitioning(false);
        return;
      }
      setTransitioning(false);
    }

    if (isLast) {
      onComplete();
    } else {
      setCurrentStep((s) => s + 1);
    }
  };

  const handleSkip = () => {
    if (busy) return;
    if (isLast) {
      onComplete();
    } else {
      setCurrentStep((s) => s + 1);
    }
  };

  const handleBack = () => {
    if (busy) return;
    setCurrentStep((s) => Math.max(0, s - 1));
  };

  return (
    <div className={cn("w-full max-w-2xl mx-auto", className)}>
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-muted-foreground">
            Step {currentStep + 1} of {steps.length}
          </span>
          {onSkip && (
            <Button variant="ghost" size="sm" onClick={onSkip} disabled={busy}>
              Skip setup
            </Button>
          )}
        </div>
        <Progress value={progress} className="h-2" />
        <div className="flex justify-between mt-2">
          {steps.map((s, i) => (
            <div
              key={s.id}
              className={cn(
                "text-xs",
                i <= currentStep ? "text-primary font-medium" : "text-muted-foreground"
              )}
            >
              {s.title}
            </div>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{step.title}</CardTitle>
          {step.description && (
            <CardDescription>{step.description}</CardDescription>
          )}
        </CardHeader>
        <CardContent>{step.content}</CardContent>
        <CardFooter className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 0 || busy}
          >
            Back
          </Button>
          <div className="flex gap-2">
            {step.isOptional && !isLast && (
              <Button variant="ghost" onClick={handleSkip} disabled={busy}>
                Skip
              </Button>
            )}
            <Button
              onClick={handleNext}
              disabled={isNextDisabled || busy}
            >
              {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isLast ? "Complete" : "Continue"}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
