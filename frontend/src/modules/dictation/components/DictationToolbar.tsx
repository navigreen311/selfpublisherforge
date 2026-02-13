"use client";

import * as React from "react";
import {
  Mic,
  Pause,
  Play,
  Square,
  Settings,
  Sparkles,
  Timer,
  Gauge,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DictationSettings } from "../types";

interface DictationToolbarProps {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  wpm: number;
  audioLevel: number;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onRefine: () => void;
  settings: DictationSettings;
  onSettingsChange: (settings: Partial<DictationSettings>) => void;
}

const LANGUAGES = [
  { value: "en-US", label: "English (US)" },
  { value: "en-GB", label: "English (UK)" },
  { value: "es-ES", label: "Spanish" },
  { value: "fr-FR", label: "French" },
  { value: "de-DE", label: "German" },
  { value: "it-IT", label: "Italian" },
  { value: "pt-BR", label: "Portuguese (BR)" },
  { value: "ja-JP", label: "Japanese" },
  { value: "zh-CN", label: "Chinese (Simplified)" },
];

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function getStatusText(isRecording: boolean, isPaused: boolean): string {
  if (!isRecording) return "Ready";
  if (isPaused) return "Paused";
  return "Listening...";
}

function getStatusColor(isRecording: boolean, isPaused: boolean): string {
  if (!isRecording) return "text-muted-foreground";
  if (isPaused) return "text-yellow-600";
  return "text-green-600";
}

export function DictationToolbar({
  isRecording,
  isPaused,
  duration,
  wpm,
  audioLevel,
  onStart,
  onPause,
  onResume,
  onStop,
  onRefine,
  settings,
  onSettingsChange,
}: DictationToolbarProps) {
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const settingsRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        settingsRef.current &&
        !settingsRef.current.contains(event.target as Node)
      ) {
        setSettingsOpen(false);
      }
    }
    if (settingsOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [settingsOpen]);

  const clampedLevel = Math.max(0, Math.min(1, audioLevel));

  return (
    <div
      className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2"
      role="toolbar"
      aria-label="Dictation controls"
    >
      <div className="flex items-center gap-3 rounded-2xl border bg-background/95 px-4 py-3 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-background/80">
        {/* Microphone button */}
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            "h-12 w-12 rounded-full transition-colors",
            !isRecording && "bg-muted text-muted-foreground hover:bg-muted/80",
            isRecording &&
              !isPaused &&
              "bg-red-500 text-white hover:bg-red-600 animate-pulse",
            isRecording &&
              isPaused &&
              "bg-yellow-500 text-white hover:bg-yellow-600"
          )}
          onClick={isRecording ? (isPaused ? onResume : onPause) : onStart}
          aria-label={
            isRecording
              ? isPaused
                ? "Resume recording"
                : "Pause recording"
              : "Start recording"
          }
        >
          <Mic className="h-6 w-6" />
        </Button>

        {/* Audio level meter */}
        <div
          className="flex h-8 w-24 items-center gap-px"
          role="meter"
          aria-label="Audio level"
          aria-valuenow={Math.round(clampedLevel * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          {Array.from({ length: 12 }).map((_, i) => {
            const threshold = (i + 1) / 12;
            const isActive = isRecording && !isPaused && clampedLevel >= threshold;
            return (
              <div
                key={i}
                className={cn(
                  "h-full flex-1 rounded-sm transition-colors duration-75",
                  isActive
                    ? threshold > 0.75
                      ? "bg-red-500"
                      : threshold > 0.5
                        ? "bg-yellow-500"
                        : "bg-green-500"
                    : "bg-muted"
                )}
              />
            );
          })}
        </div>

        {/* Duration */}
        <div className="flex items-center gap-1.5 text-sm tabular-nums text-muted-foreground">
          <Timer className="h-3.5 w-3.5" />
          <span aria-label="Recording duration">{formatDuration(duration)}</span>
        </div>

        {/* WPM */}
        <div className="flex items-center gap-1.5 text-sm tabular-nums text-muted-foreground">
          <Gauge className="h-3.5 w-3.5" />
          <span aria-label="Words per minute">{wpm} wpm</span>
        </div>

        {/* Status */}
        <Badge
          variant="secondary"
          className={cn("text-xs", getStatusColor(isRecording, isPaused))}
        >
          {getStatusText(isRecording, isPaused)}
        </Badge>

        {/* Separator */}
        <div className="h-8 w-px bg-border" />

        {/* Pause / Resume */}
        {isRecording && (
          <Button
            variant="ghost"
            size="sm"
            onClick={isPaused ? onResume : onPause}
            aria-label={isPaused ? "Resume" : "Pause"}
          >
            {isPaused ? (
              <Play className="mr-1.5 h-4 w-4" />
            ) : (
              <Pause className="mr-1.5 h-4 w-4" />
            )}
            {isPaused ? "Resume" : "Pause"}
          </Button>
        )}

        {/* Stop */}
        {isRecording && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onStop}
            aria-label="Stop recording"
          >
            <Square className="mr-1.5 h-4 w-4" />
            Stop
          </Button>
        )}

        {/* Refine button (visible when auto-refine is off) */}
        {!settings.autoRefine && isRecording && (
          <Button variant="secondary" size="sm" onClick={onRefine}>
            <Sparkles className="mr-1.5 h-4 w-4" />
            Refine
          </Button>
        )}

        {/* Settings */}
        <div className="relative" ref={settingsRef}>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSettingsOpen((prev) => !prev)}
            aria-label="Dictation settings"
            aria-expanded={settingsOpen}
          >
            <Settings className="h-4 w-4" />
          </Button>

          {settingsOpen && (
            <div
              className="absolute bottom-full right-0 mb-2 w-72 rounded-lg border bg-background p-4 shadow-lg"
              role="dialog"
              aria-label="Dictation settings"
            >
              <h3 className="mb-3 text-sm font-semibold">
                Dictation Settings
              </h3>

              <div className="space-y-4">
                {/* Language selector */}
                <div className="space-y-1.5">
                  <Label htmlFor="dictation-language" className="text-xs">
                    Language
                  </Label>
                  <Select
                    value={settings.language}
                    onValueChange={(value) =>
                      onSettingsChange({ language: value })
                    }
                  >
                    <SelectTrigger id="dictation-language" className="h-8 text-xs">
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent>
                      {LANGUAGES.map((lang) => (
                        <SelectItem
                          key={lang.value}
                          value={lang.value}
                          className="text-xs"
                        >
                          {lang.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Microphone selector */}
                <div className="space-y-1.5">
                  <Label htmlFor="dictation-mic" className="text-xs">
                    Microphone
                  </Label>
                  <Select
                    value={settings.microphoneDeviceId}
                    onValueChange={(value) =>
                      onSettingsChange({ microphoneDeviceId: value })
                    }
                  >
                    <SelectTrigger id="dictation-mic" className="h-8 text-xs">
                      <SelectValue placeholder="Default microphone" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default" className="text-xs">
                        Default Microphone
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Auto-refine toggle */}
                <div className="flex items-center justify-between">
                  <Label htmlFor="auto-refine" className="text-xs">
                    Auto-refine
                  </Label>
                  <Switch
                    id="auto-refine"
                    checked={settings.autoRefine}
                    onCheckedChange={(checked) =>
                      onSettingsChange({ autoRefine: checked })
                    }
                  />
                </div>

                {/* Voice commands toggle */}
                <div className="flex items-center justify-between">
                  <Label htmlFor="voice-commands" className="text-xs">
                    Voice commands
                  </Label>
                  <Switch
                    id="voice-commands"
                    checked={settings.voiceCommandsEnabled}
                    onCheckedChange={(checked) =>
                      onSettingsChange({ voiceCommandsEnabled: checked })
                    }
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
