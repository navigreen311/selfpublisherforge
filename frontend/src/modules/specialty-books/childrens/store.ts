"use client";

import { create } from "zustand";
import type { PreviewDevice } from "./types";

interface ChildrensBookEditorStore {
  selectedPageId: string | null;
  zoomLevel: number;
  previewMode: boolean;
  previewDevice: PreviewDevice;

  selectPage: (id: string, pageNumber: number) => void;
  setZoomLevel: (level: number) => void;
  setPreviewMode: (on: boolean) => void;
  setPreviewDevice: (device: PreviewDevice) => void;
}

export const useChildrensBookEditorStore = create<ChildrensBookEditorStore>()(
  (set) => ({
    selectedPageId: null,
    zoomLevel: 100,
    previewMode: false,
    previewDevice: "desktop",

    selectPage: (id, _pageNumber) => set({ selectedPageId: id }),
    setZoomLevel: (level) => set({ zoomLevel: level }),
    setPreviewMode: (on) => set({ previewMode: on }),
    setPreviewDevice: (device) => set({ previewDevice: device }),
  }),
);
