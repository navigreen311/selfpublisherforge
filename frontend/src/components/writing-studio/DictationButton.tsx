"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Mic, MicOff } from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface DictationButtonProps {
  /** Whether the dictation feature is available (backend connected) */
  enabled?: boolean;
  /** Callback when dictated text is captured */
  onDictationResult?: (text: string) => void;
  /** Callback when auto-refined text is returned */
  onRefinedResult?: (text: string) => void;
  /** Style profile ID for auto-refinement */
  styleProfileId?: string;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DictationButton({
  enabled = false,
  onDictationResult,
  onRefinedResult,
  styleProfileId,
  className,
}: DictationButtonProps) {
  const t = useTranslations("writing");

  const [isRecording, setIsRecording] = useState(false);
  const [autoRefine, setAutoRefine] = useState(true);

  // -----------------------------------------------------------------------
  // Dictation handlers (Web Speech API)
  // -----------------------------------------------------------------------

  const startDictation = useCallback(() => {
    if (!enabled) return;

    // Check for Web Speech API support
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("Web Speech API not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join(" ");

      if (autoRefine && onRefinedResult) {
        // When auto-refine is on, send through refinement pipeline
        onRefinedResult(transcript);
      } else if (onDictationResult) {
        onDictationResult(transcript);
      }
    };

    recognition.onerror = () => {
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
    setIsRecording(true);

    // Store recognition instance for stopping
    (window as any).__dictationRecognition = recognition;
  }, [enabled, autoRefine, onDictationResult, onRefinedResult]);

  const stopDictation = useCallback(() => {
    const recognition = (window as any).__dictationRecognition;
    if (recognition) {
      recognition.stop();
      (window as any).__dictationRecognition = null;
    }
    setIsRecording(false);
  }, []);

  const toggleDictation = useCallback(() => {
    if (isRecording) {
      stopDictation();
    } else {
      startDictation();
    }
  }, [isRecording, startDictation, stopDictation]);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  if (!enabled) {
    // Disabled state with tooltip
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={cn("space-y-2", className)}>
              <Button
                variant="outline"
                size="sm"
                className="w-full text-xs gap-2 opacity-60 cursor-not-allowed"
                disabled
              >
                <Mic className="h-3.5 w-3.5" />
                {t("ai.startDictation") || "Start Dictation"}
              </Button>
              <div className="flex items-center justify-between">
                <label className="text-xs text-muted-foreground">
                  {t("ai.autoRefine") || "Auto-refine"}
                </label>
                <Switch
                  checked={autoRefine}
                  onCheckedChange={setAutoRefine}
                  disabled
                  className="scale-75"
                />
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p className="text-xs">
              {t("ai.dictationComingSoon") ||
                "Coming soon \u2014 AI voice dictation"}
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Enabled/active state
  return (
    <div className={cn("space-y-2", className)}>
      <Button
        variant={isRecording ? "destructive" : "outline"}
        size="sm"
        className="w-full text-xs gap-2"
        onClick={toggleDictation}
      >
        {isRecording ? (
          <>
            <MicOff className="h-3.5 w-3.5" />
            {t("ai.stopDictation") || "Stop Dictation"}
          </>
        ) : (
          <>
            <Mic className="h-3.5 w-3.5" />
            {t("ai.startDictation") || "Start Dictation"}
          </>
        )}
      </Button>

      <div className="flex items-center justify-between">
        <label className="text-xs text-muted-foreground">
          {t("ai.autoRefine") || "Auto-refine"}
        </label>
        <Switch
          checked={autoRefine}
          onCheckedChange={setAutoRefine}
          className="scale-75"
        />
      </div>

      {isRecording && (
        <div className="flex items-center gap-2 text-xs text-red-500">
          <span className="inline-block h-2 w-2 rounded-full bg-red-500 animate-pulse" />
          {t("ai.recording") || "Recording..."}
        </div>
      )}
    </div>
  );
}
