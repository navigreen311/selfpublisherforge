"use client";

import { create } from "zustand";
import type { DictationStatus, DiffSegment } from "./types";

// ── Types ───────────────────────────────────────────────────────

interface DictationUIState {
  /** ID of the currently active dictation session */
  activeSessionId: string | null;
  /** Current session status */
  sessionStatus: DictationStatus | null;
  /** Whether the mic is actively recording */
  isRecording: boolean;
  /** Whether recording is paused */
  isPaused: boolean;
  /** Current audio input level (0–1) for visualisation */
  audioLevel: number;
  /** Elapsed duration in seconds */
  elapsedSeconds: number;
  /** Words per minute from latest metrics */
  wpm: number;
  /** Whether the refinement comparison panel is open */
  showRefinementDiff: boolean;
  /** Latest diff segments from refinement */
  refinementDiff: DiffSegment[];

  // ── Actions ─────────────────────────────────────────────────
  setActiveSession: (id: string | null) => void;
  setSessionStatus: (status: DictationStatus | null) => void;
  setRecording: (recording: boolean) => void;
  setPaused: (paused: boolean) => void;
  setAudioLevel: (level: number) => void;
  setElapsedSeconds: (seconds: number) => void;
  setWpm: (wpm: number) => void;
  setShowRefinementDiff: (show: boolean) => void;
  setRefinementDiff: (diff: DiffSegment[]) => void;
  reset: () => void;
}

// ── Initial State ───────────────────────────────────────────────

const initialState = {
  activeSessionId: null,
  sessionStatus: null,
  isRecording: false,
  isPaused: false,
  audioLevel: 0,
  elapsedSeconds: 0,
  wpm: 0,
  showRefinementDiff: false,
  refinementDiff: [] as DiffSegment[],
};

// ── Store ───────────────────────────────────────────────────────

export const useDictationStore = create<DictationUIState>()((set) => ({
  ...initialState,

  setActiveSession: (activeSessionId) =>
    set({ activeSessionId }),
  setSessionStatus: (sessionStatus) =>
    set({ sessionStatus }),
  setRecording: (isRecording) =>
    set({ isRecording }),
  setPaused: (isPaused) =>
    set({ isPaused }),
  setAudioLevel: (audioLevel) =>
    set({ audioLevel }),
  setElapsedSeconds: (elapsedSeconds) =>
    set({ elapsedSeconds }),
  setWpm: (wpm) =>
    set({ wpm }),
  setShowRefinementDiff: (showRefinementDiff) =>
    set({ showRefinementDiff }),
  setRefinementDiff: (refinementDiff) =>
    set({ refinementDiff }),
  reset: () =>
    set(initialState),
}));
