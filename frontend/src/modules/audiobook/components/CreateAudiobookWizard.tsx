"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Check,
  Mic2,
  Settings2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useBooks } from "@/modules/writing/hooks";
import { useVoices, useCreateAudiobookProject } from "../hooks";
import { VoicePicker } from "./VoicePicker";
import { CostEstimator } from "./CostEstimator";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CreateAudiobookWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type WizardStep = 1 | 2 | 3;

const STEPS: { step: WizardStep; label: string; icon: React.ElementType }[] = [
  { step: 1, label: "Select Book", icon: BookOpen },
  { step: 2, label: "Choose Voice", icon: Mic2 },
  { step: 3, label: "Configure", icon: Settings2 },
];

// ---------------------------------------------------------------------------
// Step indicator
// ---------------------------------------------------------------------------

function StepIndicator({ current }: { current: WizardStep }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map(({ step, label, icon: Icon }, idx) => {
        const isActive = step === current;
        const isComplete = step < current;
        return (
          <div key={step} className="flex items-center gap-2">
            {idx > 0 && (
              <div
                className={cn(
                  "h-px w-8",
                  isComplete ? "bg-primary" : "bg-border"
                )}
              />
            )}
            <div
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive && "bg-primary text-primary-foreground",
                isComplete && "bg-primary/10 text-primary",
                !isActive && !isComplete && "bg-muted text-muted-foreground"
              )}
            >
              {isComplete ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Icon className="h-3.5 w-3.5" />
              )}
              <span className="hidden sm:inline">{label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 1: Book Selection
// ---------------------------------------------------------------------------

function StepSelectBook({
  selectedBookId,
  onSelect,
}: {
  selectedBookId: string;
  onSelect: (bookId: string) => void;
}) {
  const { data: books, isLoading } = useBooks();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">
          Loading books...
        </span>
      </div>
    );
  }

  if (!books || books.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <BookOpen className="h-10 w-10 text-muted-foreground/40 mb-3" />
        <p className="font-medium text-muted-foreground">No books found</p>
        <p className="text-sm text-muted-foreground/70 mt-1">
          Create a book in the Writing module first, then come back to create an
          audiobook.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Select the book you want to convert into an audiobook.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto pr-1">
        {books.map((book) => {
          const isSelected = selectedBookId === book.id;
          return (
            <button
              key={book.id}
              onClick={() => onSelect(book.id)}
              className={cn(
                "text-left border rounded-lg p-4 transition-all space-y-2",
                isSelected
                  ? "ring-2 ring-primary border-primary shadow-sm"
                  : "hover:shadow-md hover:border-primary/30"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <h4 className="font-semibold text-sm line-clamp-2">
                  {book.title}
                </h4>
                {isSelected && (
                  <Check className="h-4 w-4 text-primary shrink-0" />
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                {book.word_count != null && (
                  <span>{book.word_count.toLocaleString()} words</span>
                )}
                {book.chapter_count != null && (
                  <span>{book.chapter_count} chapters</span>
                )}
                {book.status && (
                  <Badge variant="outline" className="text-[10px]">
                    {book.status}
                  </Badge>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3: Configure & Review
// ---------------------------------------------------------------------------

function StepConfigure({
  selectedBookId,
  selectedVoiceId,
  books,
  voices,
}: {
  selectedBookId: string;
  selectedVoiceId: string;
  books: { id: string; title: string; word_count?: number; chapter_count?: number }[];
  voices: { id: string; name: string; cost_tier?: string }[];
}) {
  const book = books.find((b) => b.id === selectedBookId);
  const voice = voices.find((v) => v.id === selectedVoiceId);
  const wordCount = book?.word_count ?? 0;
  const chapterCount = book?.chapter_count ?? 0;

  const chapters = Array.from({ length: chapterCount }, (_, i) => ({
    chapter_number: i + 1,
    word_count: chapterCount > 0 ? Math.round(wordCount / chapterCount) : 0,
    cost_usd: 0,
  }));

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <h3 className="font-semibold text-sm">Project Summary</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="border rounded-lg p-3 space-y-1">
            <span className="text-xs text-muted-foreground">Book</span>
            <p className="font-medium truncate">{book?.title ?? "Unknown"}</p>
          </div>
          <div className="border rounded-lg p-3 space-y-1">
            <span className="text-xs text-muted-foreground">Voice</span>
            <p className="font-medium truncate">{voice?.name ?? "Unknown"}</p>
          </div>
        </div>
      </div>

      <CostEstimator
        projectId=""
        totalWordCount={wordCount}
        chapters={chapters}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Wizard
// ---------------------------------------------------------------------------

export function CreateAudiobookWizard({
  open,
  onOpenChange,
}: CreateAudiobookWizardProps) {
  const router = useRouter();
  const [step, setStep] = useState<WizardStep>(1);
  const [selectedBookId, setSelectedBookId] = useState("");
  const [selectedVoiceId, setSelectedVoiceId] = useState("");

  const { data: books } = useBooks();
  const { data: voices, isLoading: voicesLoading } = useVoices();
  const { mutate: createProject, isPending } = useCreateAudiobookProject();

  const reset = () => {
    setStep(1);
    setSelectedBookId("");
    setSelectedVoiceId("");
  };

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen && !isPending) {
      reset();
    }
    onOpenChange(nextOpen);
  };

  const canProceed = (): boolean => {
    if (step === 1) return !!selectedBookId;
    if (step === 2) return !!selectedVoiceId;
    return true;
  };

  const handleNext = () => {
    if (step < 3) {
      setStep((s) => (s + 1) as WizardStep);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((s) => (s - 1) as WizardStep);
    }
  };

  const handleCreate = () => {
    const book = books?.find((b) => b.id === selectedBookId);

    createProject(
      {
        book_id: selectedBookId,
        voice_id: selectedVoiceId,
        title: book?.title || undefined,
        target_platform: "acx",
        output_format: "mp3",
        sample_rate: 44100,
        bit_rate: 192,
        channels: 1,
      },
      {
        onSuccess: (project) => {
          toast.success("Audiobook project created!");
          reset();
          onOpenChange(false);
          router.push(`/audiobook-studio/${project.id}`);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Audiobook</DialogTitle>
          <DialogDescription>
            Follow the steps to set up your new audiobook project.
          </DialogDescription>
        </DialogHeader>

        <StepIndicator current={step} />

        {/* Step content */}
        {step === 1 && (
          <StepSelectBook
            selectedBookId={selectedBookId}
            onSelect={setSelectedBookId}
          />
        )}

        {step === 2 && (
          <VoicePicker
            selectedVoiceId={selectedVoiceId}
            onSelect={setSelectedVoiceId}
            voices={(voices ?? []).map((v) => ({
              id: v.id,
              name: v.name,
              gender: (v.gender as "male" | "female" | "neutral") || "neutral",
              accent: v.accent ?? "American",
              provider:
                (v.provider as "self-hosted" | "premium") || "self-hosted",
              cost_tier: (v.cost_tier as "$" | "$$" | "$$$") || "$",
              sample_url: v.sample_url ?? null,
            }))}
            isLoading={voicesLoading}
          />
        )}

        {step === 3 && (
          <StepConfigure
            selectedBookId={selectedBookId}
            selectedVoiceId={selectedVoiceId}
            books={books ?? []}
            voices={voices ?? []}
          />
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={step === 1 || isPending}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>

          {step < 3 ? (
            <Button onClick={handleNext} disabled={!canProceed()}>
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={handleCreate}
              disabled={isPending || !canProceed()}
            >
              {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isPending ? "Creating..." : "Create Audiobook"}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
