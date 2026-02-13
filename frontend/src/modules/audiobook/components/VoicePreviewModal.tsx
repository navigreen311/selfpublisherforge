"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  Play,
  Pause,
  Star,
  DollarSign,
  Loader2,
  X,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useVoices, useVoicePreview } from "../hooks";
import type { Voice } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface VoicePreviewModalProps {
  voiceId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (voiceId: string) => void;
}

interface CompareVoice {
  voice: Voice;
  audioUrl: string | null;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_PREVIEW_TEXT =
  "The quick brown fox jumps over the lazy dog. This sentence demonstrates voice clarity, natural cadence, and pronunciation quality.";

const MAX_COMPARE_VOICES = 3;

const COST_PER_MINUTE: Record<string, string> = {
  $: "$0.01",
  $$: "$0.05",
  $$$: "$0.15",
};

const providerBadgeStyles: Record<string, string> = {
  "self-hosted": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  premium: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function QualityStars({ score }: { score: number }) {
  const fullStars = Math.floor(score);
  const hasHalf = score - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

  return (
    <div className="flex items-center gap-0.5" aria-label={`Quality: ${score} out of 5 stars`}>
      {[...Array(fullStars)].map((_, i) => (
        <Star key={`full-${i}`} className="h-4 w-4 fill-amber-400 text-amber-400" />
      ))}
      {hasHalf && (
        <div className="relative">
          <Star className="h-4 w-4 text-muted-foreground/30" />
          <div className="absolute inset-0 overflow-hidden" style={{ width: "50%" }}>
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
          </div>
        </div>
      )}
      {[...Array(emptyStars)].map((_, i) => (
        <Star key={`empty-${i}`} className="h-4 w-4 text-muted-foreground/30" />
      ))}
      <span className="ml-1 text-xs text-muted-foreground">{score.toFixed(1)}</span>
    </div>
  );
}

function WaveformBars({
  isPlaying,
  progress,
}: {
  isPlaying: boolean;
  progress: number;
}) {
  const barCount = 32;
  return (
    <div className="flex items-end gap-[2px] h-10 w-full" aria-hidden="true">
      {[...Array(barCount)].map((_, i) => {
        const height = 20 + Math.sin(i * 0.8) * 15 + Math.cos(i * 1.3) * 10;
        const isFilled = i / barCount <= progress;
        return (
          <div
            key={i}
            className={cn(
              "flex-1 rounded-sm transition-all duration-150",
              isFilled
                ? "bg-primary"
                : "bg-muted-foreground/20",
              isPlaying && isFilled && "animate-pulse",
            )}
            style={{ height: `${height}%` }}
          />
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function VoicePreviewModal({
  voiceId,
  open,
  onOpenChange,
  onSelect,
}: VoicePreviewModalProps) {
  const { data: voices = [] } = useVoices();
  const previewMutation = useVoicePreview();

  const voice = voices.find((v) => v.id === voiceId);

  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationRef = useRef<number | null>(null);

  // Custom preview
  const [previewText, setPreviewText] = useState(DEFAULT_PREVIEW_TEXT);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState<string | null>(null);

  // Compare mode
  const [compareVoices, setCompareVoices] = useState<CompareVoice[]>([]);
  const [comparePlayingId, setComparePlayingId] = useState<string | null>(null);
  const compareAudioRef = useRef<HTMLAudioElement | null>(null);

  // Volume
  const [volume, setVolume] = useState(0.8);

  // Derived quality score (simulated from voice properties)
  const qualityScore = voice
    ? voice.provider === "premium" ? 4.5 : 3.8
    : 0;

  // Cleanup on close
  useEffect(() => {
    if (!open) {
      stopPlayback();
      stopComparePlayback();
      setGeneratedAudioUrl(null);
      setCompareVoices([]);
      setProgress(0);
    }
  }, [open]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      audioRef.current?.pause();
      compareAudioRef.current?.pause();
    };
  }, []);

  // Update volume on audio elements
  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
    if (compareAudioRef.current) compareAudioRef.current.volume = volume;
  }, [volume]);

  const updateProgress = useCallback(() => {
    if (audioRef.current) {
      const current = audioRef.current.currentTime;
      const total = audioRef.current.duration || 1;
      setProgress(current / total);
      setDuration(total);

      if (!audioRef.current.paused) {
        animationRef.current = requestAnimationFrame(updateProgress);
      }
    }
  }, []);

  const playAudio = useCallback(
    (url: string) => {
      stopPlayback();
      const audio = new Audio(url);
      audio.volume = volume;
      audioRef.current = audio;

      audio.addEventListener("loadedmetadata", () => {
        setDuration(audio.duration);
      });

      audio.addEventListener("ended", () => {
        setIsPlaying(false);
        setProgress(0);
        if (animationRef.current) cancelAnimationFrame(animationRef.current);
      });

      audio.play();
      setIsPlaying(true);
      animationRef.current = requestAnimationFrame(updateProgress);
    },
    [volume, updateProgress],
  );

  const stopPlayback = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    setIsPlaying(false);
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
  }, []);

  const togglePlayback = useCallback(() => {
    if (!audioRef.current) {
      // Try generated audio first, then sample
      const url = generatedAudioUrl ?? voice?.sample_url;
      if (url) playAudio(url);
      return;
    }

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
      animationRef.current = requestAnimationFrame(updateProgress);
    }
  }, [isPlaying, generatedAudioUrl, voice, playAudio, updateProgress]);

  const handleGeneratePreview = useCallback(() => {
    if (!voice || !previewText.trim()) return;

    stopPlayback();
    previewMutation.mutate(
      { voice_id: voice.id, text: previewText.trim() },
      {
        onSuccess: (data) => {
          setGeneratedAudioUrl(data.audio_url);
          playAudio(data.audio_url);
        },
      },
    );
  }, [voice, previewText, previewMutation, stopPlayback, playAudio]);

  // Compare voice management
  const addCompareVoice = useCallback(
    (v: Voice) => {
      if (compareVoices.length >= MAX_COMPARE_VOICES) return;
      if (compareVoices.some((cv) => cv.voice.id === v.id)) return;
      setCompareVoices((prev) => [...prev, { voice: v, audioUrl: v.sample_url ?? null }]);
    },
    [compareVoices],
  );

  const removeCompareVoice = useCallback((id: string) => {
    if (comparePlayingId === id) stopComparePlayback();
    setCompareVoices((prev) => prev.filter((cv) => cv.voice.id !== id));
  }, [comparePlayingId]);

  const stopComparePlayback = useCallback(() => {
    compareAudioRef.current?.pause();
    compareAudioRef.current = null;
    setComparePlayingId(null);
  }, []);

  const playCompareVoice = useCallback(
    (cv: CompareVoice) => {
      if (comparePlayingId === cv.voice.id) {
        stopComparePlayback();
        return;
      }

      stopComparePlayback();
      stopPlayback();

      if (!cv.audioUrl) return;

      const audio = new Audio(cv.audioUrl);
      audio.volume = volume;
      audio.onended = () => setComparePlayingId(null);
      audio.play();
      compareAudioRef.current = audio;
      setComparePlayingId(cv.voice.id);
    },
    [comparePlayingId, volume, stopComparePlayback, stopPlayback],
  );

  const handleSelect = useCallback(() => {
    onSelect(voiceId);
    onOpenChange(false);
  }, [voiceId, onSelect, onOpenChange]);

  // Available voices for compare (excluding current voice and already-added)
  const availableForCompare = voices.filter(
    (v) =>
      v.id !== voiceId &&
      !compareVoices.some((cv) => cv.voice.id === v.id),
  );

  if (!voice) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Voice Not Found</DialogTitle>
            <DialogDescription>
              The requested voice could not be loaded.
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
  }

  const hasAudio = !!(generatedAudioUrl ?? voice.sample_url);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span>{voice.name}</span>
            <Badge
              className={cn(
                "text-[10px] font-medium",
                providerBadgeStyles[voice.provider],
              )}
            >
              {voice.provider === "self-hosted" ? "Self-Hosted" : "Premium"}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Preview and compare this voice before selecting it for your audiobook.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-2">
          {/* Voice Info */}
          <div className="flex flex-wrap gap-3 items-center">
            <Badge variant="outline" className="text-xs">
              {voice.gender.charAt(0).toUpperCase() + voice.gender.slice(1)}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {voice.accent}
            </Badge>
            <Badge variant="outline" className="text-xs">
              English
            </Badge>
          </div>

          {/* Quality & Cost Row */}
          <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Quality</p>
              <QualityStars score={qualityScore} />
            </div>
            <div className="space-y-1 text-right">
              <p className="text-xs font-medium text-muted-foreground">Cost</p>
              <div className="flex items-center gap-1">
                <DollarSign className="h-3.5 w-3.5 text-green-600" />
                <span className="text-sm font-semibold">
                  {(voice.cost_tier && COST_PER_MINUTE[voice.cost_tier]) ?? voice.cost_tier ?? "N/A"}
                </span>
                <span className="text-xs text-muted-foreground">/min</span>
              </div>
            </div>
          </div>

          {/* Audio Player */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Audio Preview</h4>
              {duration > 0 && (
                <span className="text-xs text-muted-foreground tabular-nums">
                  {Math.floor(progress * duration)}s / {Math.floor(duration)}s
                </span>
              )}
            </div>

            {/* Waveform Visualization */}
            <div className="rounded-lg border bg-slate-50 p-3 dark:bg-slate-900">
              <WaveformBars isPlaying={isPlaying} progress={progress} />
            </div>

            {/* Play Controls + Volume */}
            <div className="flex items-center gap-3">
              <Button
                variant="default"
                size="icon"
                onClick={togglePlayback}
                disabled={!hasAudio}
                aria-label={isPlaying ? "Pause preview" : "Play preview"}
              >
                {isPlaying ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </Button>
              <Slider
                value={[volume]}
                onValueChange={(val) => setVolume(val[0])}
                min={0}
                max={1}
                step={0.05}
                className="w-24"
                aria-label="Volume"
              />
              <span className="text-xs text-muted-foreground">
                {Math.round(volume * 100)}%
              </span>
            </div>
          </div>

          {/* Custom Text Preview */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Custom Text Preview</h4>
            <div className="flex gap-2">
              <Input
                value={previewText}
                onChange={(e) => setPreviewText(e.target.value)}
                placeholder="Enter text to preview with this voice..."
                className="flex-1"
                aria-label="Custom preview text"
              />
              <Button
                onClick={handleGeneratePreview}
                disabled={
                  previewMutation.isPending || !previewText.trim()
                }
                className="gap-1.5 shrink-0"
              >
                {previewMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Generate Preview
              </Button>
            </div>
          </div>

          {/* Compare Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Compare Voices</h4>
              <span className="text-xs text-muted-foreground">
                {compareVoices.length}/{MAX_COMPARE_VOICES} slots used
              </span>
            </div>

            {/* Compare voice cards */}
            {compareVoices.length > 0 && (
              <div className="space-y-2">
                {compareVoices.map((cv) => (
                  <div
                    key={cv.voice.id}
                    className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2"
                  >
                    <button
                      onClick={() => playCompareVoice(cv)}
                      disabled={!cv.audioUrl}
                      className={cn(
                        "flex items-center justify-center h-8 w-8 rounded-full transition-colors shrink-0",
                        cv.audioUrl
                          ? "bg-primary text-primary-foreground hover:bg-primary/90"
                          : "bg-muted text-muted-foreground cursor-not-allowed",
                      )}
                      aria-label={
                        comparePlayingId === cv.voice.id
                          ? `Pause ${cv.voice.name}`
                          : `Play ${cv.voice.name}`
                      }
                    >
                      {comparePlayingId === cv.voice.id ? (
                        <Pause className="h-3.5 w-3.5" />
                      ) : (
                        <Play className="h-3.5 w-3.5" />
                      )}
                    </button>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{cv.voice.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {cv.voice.accent} &middot; {cv.voice.cost_tier}
                      </p>
                    </div>
                    <button
                      onClick={() => removeCompareVoice(cv.voice.id)}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      aria-label={`Remove ${cv.voice.name} from comparison`}
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add compare voice */}
            {compareVoices.length < MAX_COMPARE_VOICES &&
              availableForCompare.length > 0 && (
                <div className="space-y-2">
                  <select
                    onChange={(e) => {
                      const v = voices.find((v) => v.id === e.target.value);
                      if (v) addCompareVoice(v);
                      e.target.value = "";
                    }}
                    defaultValue=""
                    className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                    aria-label="Add voice to compare"
                  >
                    <option value="" disabled>
                      + Add a voice to compare...
                    </option>
                    {availableForCompare.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.accent}, {v.cost_tier})
                      </option>
                    ))}
                  </select>
                </div>
              )}

            {compareVoices.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-2">
                Add voices above to compare them side by side.
              </p>
            )}
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSelect}>Select Voice</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
