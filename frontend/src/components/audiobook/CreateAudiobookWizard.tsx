"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface CreateAudiobookWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const STEPS = ["Select Book", "Choose Voice", "Configure"] as const;

export function CreateAudiobookWizard({ open, onOpenChange }: CreateAudiobookWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Audiobook</DialogTitle>
          <DialogDescription>
            Step {currentStep + 1} of {STEPS.length}: {STEPS[currentStep]}
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 mb-6">
          {STEPS.map((step, i) => (
            <div
              key={step}
              className={`flex-1 h-2 rounded-full ${
                i <= currentStep ? "bg-primary" : "bg-muted"
              }`}
            />
          ))}
        </div>

        <div className="min-h-[300px] flex items-center justify-center">
          <p className="text-muted-foreground">
            {STEPS[currentStep]} - Configuration coming soon
          </p>
        </div>

        <div className="flex justify-between mt-6">
          <Button variant="outline" onClick={handleBack} disabled={currentStep === 0}>
            Back
          </Button>
          <Button onClick={handleNext}>
            {currentStep === STEPS.length - 1 ? "Create" : "Next"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
