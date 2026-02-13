"use client";

import { create } from "zustand";

interface GenerationProgress {
  percent: number;
  stage: string;
}

interface AudiobookStudioStore {
  // State
  selectedChapterId: string | null;
  isPlaying: boolean;
  playbackSpeed: number;
  currentTime: number;
  generationProgress: Record<string, GenerationProgress>;

  // Actions
  selectChapter: (id: string) => void;
  setPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  setCurrentTime: (time: number) => void;
  updateGenerationProgress: (
    chapterId: string,
    percent: number,
    stage: string,
  ) => void;
}

export const useAudiobookStudioStore = create<AudiobookStudioStore>()(
  (set) => ({
    // Initial state
    selectedChapterId: null,
    isPlaying: false,
    playbackSpeed: 1,
    currentTime: 0,
    generationProgress: {},

    // Actions
    selectChapter: (id) => set({ selectedChapterId: id }),

    setPlaying: (playing) => set({ isPlaying: playing }),

    setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),

    setCurrentTime: (time) => set({ currentTime: time }),

    updateGenerationProgress: (chapterId, percent, stage) =>
      set((state) => ({
        generationProgress: {
          ...state.generationProgress,
          [chapterId]: { percent, stage },
        },
      })),
  }),
);
