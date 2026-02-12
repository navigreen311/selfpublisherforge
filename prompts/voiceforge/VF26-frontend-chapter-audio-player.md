# VF26: Frontend — ChapterAudioPlayer with Waveform

## Task
Create the ChapterAudioPlayer component with wavesurfer.js waveform visualization and sentence-level navigation.

## Dependencies
- wavesurfer.js v7 (added by VF06)

## Files to Create

### `frontend/src/modules/audiobook/components/ChapterAudioPlayer.tsx`

Advanced audio player for reviewing chapter narration:

**Features:**
- Waveform visualization using wavesurfer.js
- Sentence-level navigation: click sentence in text → jump to audio position
- Synchronized text highlighting: currently spoken sentence highlighted
- Speed control: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 2.0x
- Volume control slider
- Play/Pause/Skip controls
- Current time / total duration display
- Segment selection tool: select a sentence to regenerate just that segment
- Approve / Request Changes buttons
- Keyboard shortcuts: Space=play/pause, ←→=skip 5s, Shift+←→=prev/next sentence

```tsx
"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";
// import WaveSurfer from "wavesurfer.js";
import type { AudiobookChapter } from "../types";

interface ChapterAudioPlayerProps {
  chapter: AudiobookChapter;
  onApprove: (approved: boolean, notes?: string) => void;
  onRegenerateSegment: (segmentIndex: number) => void;
}

export function ChapterAudioPlayer({ chapter, onApprove, onRegenerateSegment }: ChapterAudioPlayerProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<any>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1.0);
  const [volume, setVolume] = useState(0.8);
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null);

  // Initialize wavesurfer.js
  useEffect(() => {
    if (!waveformRef.current || !chapter.audio_url) return;

    const loadWaveSurfer = async () => {
      const WaveSurfer = (await import("wavesurfer.js")).default;
      const ws = WaveSurfer.create({
        container: waveformRef.current!,
        waveColor: "#94a3b8",       // slate-400
        progressColor: "#6366f1",    // indigo-500
        cursorColor: "#4f46e5",      // indigo-600
        barWidth: 2,
        barRadius: 2,
        barGap: 1,
        height: 128,
        normalize: true,
        backend: "WebAudio",
      });

      ws.load(chapter.audio_url);

      ws.on("ready", () => {
        setDuration(ws.getDuration());
        wavesurferRef.current = ws;
      });

      ws.on("audioprocess", () => {
        setCurrentTime(ws.getCurrentTime());
      });

      ws.on("play", () => setIsPlaying(true));
      ws.on("pause", () => setIsPlaying(false));
      ws.on("finish", () => setIsPlaying(false));

      return () => ws.destroy();
    };

    loadWaveSurfer();
  }, [chapter.audio_url]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const ws = wavesurferRef.current;
      if (!ws) return;

      switch (e.code) {
        case "Space":
          e.preventDefault();
          ws.playPause();
          break;
        case "ArrowLeft":
          e.preventDefault();
          ws.skip(e.shiftKey ? -30 : -5);
          break;
        case "ArrowRight":
          e.preventDefault();
          ws.skip(e.shiftKey ? 30 : 5);
          break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const togglePlay = () => wavesurferRef.current?.playPause();
  const setPlaybackSpeed = (s: number) => {
    setSpeed(s);
    wavesurferRef.current?.setPlaybackRate(s);
  };
  const setVolumeLevel = (v: number) => {
    setVolume(v);
    wavesurferRef.current?.setVolume(v);
  };
  const skipTo = (seconds: number) => {
    wavesurferRef.current?.seekTo(seconds / duration);
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Waveform */}
      <div ref={waveformRef} className="w-full bg-slate-50 rounded-lg" />

      {/* Controls */}
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          {/* Play/Pause button */}
          {/* Skip buttons */}
          {/* Time display */}
          <span className="text-sm text-slate-500">{formatTime(currentTime)} / {formatTime(duration)}</span>
        </div>
        <div className="flex items-center gap-4">
          {/* Speed selector */}
          {/* Volume slider */}
          {/* Approve/Reject buttons */}
        </div>
      </div>
    </div>
  );
}
```

Build the complete component with all UI elements using shadcn/ui Button, Select, Slider, etc.

### `frontend/src/modules/audiobook/components/SentenceHighlighter.tsx`

Component that displays chapter text with sentence-level click-to-navigate and real-time highlighting:
- Split text into sentences
- Highlight currently playing sentence based on currentTime and word timings
- Click a sentence → jump audio to that position
- Right-click a sentence → "Regenerate this segment" context menu
