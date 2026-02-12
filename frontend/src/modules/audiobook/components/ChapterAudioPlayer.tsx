"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Check,
  X,
} from "lucide-react";
import type { AudiobookChapter } from "../types";
import { SentenceHighlighter } from "./SentenceHighlighter";

interface ChapterAudioPlayerProps {
  chapter: AudiobookChapter;
  onApprove: (approved: boolean, notes?: string) => void;
  onRegenerateSegment: (segmentIndex: number) => void;
}

const SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function ChapterAudioPlayer({
  chapter,
  onApprove,
  onRegenerateSegment,
}: ChapterAudioPlayerProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<any>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1.0);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [showReviewNotes, setShowReviewNotes] = useState(false);

  // Compute active sentence index from currentTime and sentence_timings
  const activeSentenceIndex = React.useMemo(() => {
    if (!chapter.sentence_timings?.length) return -1;
    for (let i = chapter.sentence_timings.length - 1; i >= 0; i--) {
      if (currentTime >= chapter.sentence_timings[i].start_time) {
        return i;
      }
    }
    return -1;
  }, [currentTime, chapter.sentence_timings]);

  // Initialize wavesurfer.js
  useEffect(() => {
    if (!waveformRef.current || !chapter.audio_url) return;

    let ws: any = null;
    let destroyed = false;

    const loadWaveSurfer = async () => {
      const WaveSurfer = (await import("wavesurfer.js")).default;

      if (destroyed) return;

      ws = WaveSurfer.create({
        container: waveformRef.current!,
        waveColor: "#94a3b8",
        progressColor: "#6366f1",
        cursorColor: "#4f46e5",
        barWidth: 2,
        barRadius: 2,
        barGap: 1,
        height: 128,
        normalize: true,
      });

      ws.load(chapter.audio_url!);

      ws.on("ready", () => {
        if (destroyed) return;
        setDuration(ws.getDuration());
        setIsReady(true);
        wavesurferRef.current = ws;
        ws.setVolume(volume);
      });

      ws.on("audioprocess", () => {
        if (!destroyed) setCurrentTime(ws.getCurrentTime());
      });

      ws.on("seeking", () => {
        if (!destroyed) setCurrentTime(ws.getCurrentTime());
      });

      ws.on("play", () => {
        if (!destroyed) setIsPlaying(true);
      });

      ws.on("pause", () => {
        if (!destroyed) setIsPlaying(false);
      });

      ws.on("finish", () => {
        if (!destroyed) setIsPlaying(false);
      });
    };

    loadWaveSurfer();

    return () => {
      destroyed = true;
      if (ws) {
        ws.destroy();
      }
      wavesurferRef.current = null;
      setIsReady(false);
    };
  }, [chapter.audio_url]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      const ws = wavesurferRef.current;
      if (!ws) return;

      switch (e.code) {
        case "Space":
          e.preventDefault();
          ws.playPause();
          break;
        case "ArrowLeft":
          e.preventDefault();
          if (e.shiftKey) {
            // Previous sentence
            navigateToSentence(activeSentenceIndex - 1);
          } else {
            ws.skip(-5);
          }
          break;
        case "ArrowRight":
          e.preventDefault();
          if (e.shiftKey) {
            // Next sentence
            navigateToSentence(activeSentenceIndex + 1);
          } else {
            ws.skip(5);
          }
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [activeSentenceIndex, duration]);

  const navigateToSentence = useCallback(
    (sentenceIndex: number) => {
      if (!chapter.sentence_timings?.length || !wavesurferRef.current || duration <= 0) return;
      const clamped = Math.max(0, Math.min(sentenceIndex, chapter.sentence_timings.length - 1));
      const timing = chapter.sentence_timings[clamped];
      wavesurferRef.current.seekTo(timing.start_time / duration);
    },
    [chapter.sentence_timings, duration]
  );

  const togglePlay = useCallback(() => {
    wavesurferRef.current?.playPause();
  }, []);

  const setPlaybackSpeed = useCallback((s: number) => {
    setSpeed(s);
    wavesurferRef.current?.setPlaybackRate(s);
  }, []);

  const setVolumeLevel = useCallback(
    (v: number) => {
      setVolume(v);
      setIsMuted(v === 0);
      wavesurferRef.current?.setVolume(v);
    },
    []
  );

  const toggleMute = useCallback(() => {
    if (isMuted) {
      const restored = volume > 0 ? volume : 0.8;
      setIsMuted(false);
      wavesurferRef.current?.setVolume(restored);
    } else {
      setIsMuted(true);
      wavesurferRef.current?.setVolume(0);
    }
  }, [isMuted, volume]);

  const handleSentenceClick = useCallback(
    (sentenceIndex: number) => {
      navigateToSentence(sentenceIndex);
    },
    [navigateToSentence]
  );

  const handleSegmentSelect = useCallback((segmentIndex: number) => {
    setSelectedSegment((prev) => (prev === segmentIndex ? null : segmentIndex));
  }, []);

  const handleRegenerateSelected = useCallback(() => {
    if (selectedSegment !== null) {
      onRegenerateSegment(selectedSegment);
      setSelectedSegment(null);
    }
  }, [selectedSegment, onRegenerateSegment]);

  const handleApprove = useCallback(() => {
    onApprove(true, reviewNotes || undefined);
    setReviewNotes("");
    setShowReviewNotes(false);
  }, [onApprove, reviewNotes]);

  const handleRequestChanges = useCallback(() => {
    setShowReviewNotes(true);
  }, []);

  const handleSubmitChanges = useCallback(() => {
    onApprove(false, reviewNotes);
    setReviewNotes("");
    setShowReviewNotes(false);
  }, [onApprove, reviewNotes]);

  return (
    <TooltipProvider>
      <div className="flex flex-col gap-4">
        {/* Chapter Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">
            {chapter.chapter_title
              ? `Chapter ${chapter.chapter_number}: ${chapter.chapter_title}`
              : `Chapter ${chapter.chapter_number}`}
          </h3>
          {chapter.status === "review" && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Pending Review
            </span>
          )}
        </div>

        {/* Waveform */}
        <div className="relative">
          <div
            ref={waveformRef}
            className={cn(
              "w-full rounded-lg bg-slate-50 dark:bg-slate-900",
              !chapter.audio_url && "flex h-32 items-center justify-center"
            )}
          />
          {!chapter.audio_url && (
            <p className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">
              No audio available
            </p>
          )}
          {chapter.audio_url && !isReady && (
            <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-slate-50/80 dark:bg-slate-900/80">
              <p className="text-sm text-muted-foreground">Loading audio...</p>
            </div>
          )}
        </div>

        {/* Transport Controls */}
        <div className="flex items-center justify-between gap-4 rounded-lg border bg-card px-4 py-3">
          {/* Left: Playback controls + time */}
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => wavesurferRef.current?.skip(-5)}
                  disabled={!isReady}
                  aria-label="Skip back 5 seconds"
                >
                  <SkipBack className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Skip back 5s</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="default"
                  size="icon"
                  onClick={togglePlay}
                  disabled={!isReady}
                  aria-label={isPlaying ? "Pause" : "Play"}
                >
                  {isPlaying ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{isPlaying ? "Pause" : "Play"} (Space)</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => wavesurferRef.current?.skip(5)}
                  disabled={!isReady}
                  aria-label="Skip forward 5 seconds"
                >
                  <SkipForward className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Skip forward 5s</TooltipContent>
            </Tooltip>

            <span className="ml-2 min-w-[5rem] text-sm tabular-nums text-muted-foreground">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          {/* Right: Speed, Volume, Actions */}
          <div className="flex items-center gap-4">
            {/* Speed Control */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Speed</span>
              <Select
                value={speed.toString()}
                onValueChange={(v) => setPlaybackSpeed(parseFloat(v))}
              >
                <SelectTrigger className="h-8 w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SPEED_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s.toString()}>
                      {s}x
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Volume Control */}
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={toggleMute}
                    aria-label={isMuted ? "Unmute" : "Mute"}
                  >
                    {isMuted ? (
                      <VolumeX className="h-4 w-4" />
                    ) : (
                      <Volume2 className="h-4 w-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{isMuted ? "Unmute" : "Mute"}</TooltipContent>
              </Tooltip>
              <Slider
                value={[isMuted ? 0 : volume]}
                onValueChange={(val) => setVolumeLevel(val[0])}
                min={0}
                max={1}
                step={0.05}
                className="w-24"
                aria-label="Volume"
              />
            </div>
          </div>
        </div>

        {/* Keyboard shortcut hint */}
        <p className="text-xs text-muted-foreground">
          Shortcuts: Space = play/pause, Left/Right = skip 5s, Shift+Left/Right = prev/next sentence
        </p>

        {/* Sentence Highlighter (synchronized text) */}
        {chapter.sentence_timings && chapter.sentence_timings.length > 0 && (
          <SentenceHighlighter
            sentences={chapter.sentence_timings}
            activeSentenceIndex={activeSentenceIndex}
            selectedSegment={selectedSegment}
            onSentenceClick={handleSentenceClick}
            onSegmentSelect={handleSegmentSelect}
          />
        )}

        {/* Segment Regeneration */}
        {selectedSegment !== null && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950">
            <span className="text-sm text-amber-800 dark:text-amber-200">
              Sentence {selectedSegment + 1} selected for regeneration
            </span>
            <div className="ml-auto flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedSegment(null)}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleRegenerateSelected}
              >
                Regenerate Segment
              </Button>
            </div>
          </div>
        )}

        {/* Review Notes Input */}
        {showReviewNotes && (
          <div className="flex flex-col gap-2 rounded-lg border px-4 py-3">
            <label
              htmlFor="review-notes"
              className="text-sm font-medium text-foreground"
            >
              Review Notes
            </label>
            <textarea
              id="review-notes"
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Describe what changes are needed..."
              className="min-h-[80px] w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowReviewNotes(false);
                  setReviewNotes("");
                }}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleSubmitChanges}
                disabled={!reviewNotes.trim()}
              >
                Submit Changes Requested
              </Button>
            </div>
          </div>
        )}

        {/* Approve / Request Changes Buttons */}
        {chapter.status === "review" && !showReviewNotes && (
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleRequestChanges}>
              <X className="mr-2 h-4 w-4" />
              Request Changes
            </Button>
            <Button variant="default" onClick={handleApprove}>
              <Check className="mr-2 h-4 w-4" />
              Approve Chapter
            </Button>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
