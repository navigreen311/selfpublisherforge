"use client";

import * as React from "react";
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
}

interface OnboardingWizardProps {
  steps: WizardStep[];
  onComplete: () => void;
  onSkip?: () => void;
  className?: string;
}

export function OnboardingWizard({
  steps,
  onComplete,
  onSkip,
  className,
}: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = React.useState(0);
  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;
  const isLast = currentStep === steps.length - 1;

  const handleNext = () => {
    if (isLast) {
      onComplete();
    } else {
      setCurrentStep((s) => s + 1);
    }
  };

  const handleBack = () => {
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
            <Button variant="ghost" size="sm" onClick={onSkip}>
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
            disabled={currentStep === 0}
          >
            Back
          </Button>
          <div className="flex gap-2">
            {step.isOptional && !isLast && (
              <Button variant="ghost" onClick={handleNext}>
                Skip
              </Button>
            )}
            <Button onClick={handleNext}>
              {isLast ? "Complete" : "Continue"}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
