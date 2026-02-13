"use client";

import { useCallback, useSyncExternalStore } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type EditorTheme = "light" | "sepia" | "dark";

export type EditorFont =
  | "Georgia"
  | "Merriweather"
  | "Lora"
  | "Source Serif Pro"
  | "System Sans";

export type EditorFontSize = 14 | 16 | 18 | 20;

export interface EditorSettings {
  theme: EditorTheme;
  font: EditorFont;
  fontSize: EditorFontSize;
}

export const DEFAULT_EDITOR_SETTINGS: EditorSettings = {
  theme: "light",
  font: "Georgia",
  fontSize: 16,
};

// ---------------------------------------------------------------------------
// Storage key
// ---------------------------------------------------------------------------

const STORAGE_KEY = "spf-editor-settings";

// ---------------------------------------------------------------------------
// External store for useSyncExternalStore
// ---------------------------------------------------------------------------

let listeners: Array<() => void> = [];
let cachedSettings: EditorSettings | null = null;

function getSettingsSnapshot(): EditorSettings {
  if (cachedSettings) return cachedSettings;

  if (typeof window === "undefined") return DEFAULT_EDITOR_SETTINGS;

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      cachedSettings = { ...DEFAULT_EDITOR_SETTINGS, ...JSON.parse(stored) };
      return cachedSettings;
    }
  } catch {
    // Ignore parse errors
  }

  cachedSettings = DEFAULT_EDITOR_SETTINGS;
  return cachedSettings;
}

function getServerSnapshot(): EditorSettings {
  return DEFAULT_EDITOR_SETTINGS;
}

function subscribe(listener: () => void) {
  listeners.push(listener);

  // Listen for storage events from other browser tabs
  const handleStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) {
      cachedSettings = null; // Invalidate cache
      listeners.forEach((l) => l());
    }
  };

  // Listen for our custom event (same-tab reactivity)
  const handleCustom = () => {
    cachedSettings = null;
    listeners.forEach((l) => l());
  };

  window.addEventListener("storage", handleStorage);
  window.addEventListener("editor-settings-change", handleCustom);

  return () => {
    listeners = listeners.filter((l) => l !== listener);
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener("editor-settings-change", handleCustom);
  };
}

function emitChange(nextSettings: EditorSettings) {
  cachedSettings = nextSettings;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSettings));
  } catch {
    // Ignore storage errors (e.g., QuotaExceededError)
  }
  // Notify all listeners (triggers re-render in all consuming components)
  listeners.forEach((l) => l());
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Reactive hook for editor settings persisted in localStorage.
 *
 * Uses `useSyncExternalStore` for proper React 18 concurrent-safe reactivity.
 * Settings sync across all components using this hook, and even across
 * browser tabs via the `storage` event.
 *
 * @returns `{ settings, updateSettings, resetSettings }`
 *
 * @example
 * ```tsx
 * const { settings, updateSettings, resetSettings } = useEditorSettings();
 *
 * // Update a single setting
 * updateSettings({ theme: "dark" });
 *
 * // Update multiple settings at once
 * updateSettings({ font: "Merriweather", fontSize: 18 });
 *
 * // Reset everything to defaults
 * resetSettings();
 * ```
 */
export function useEditorSettings() {
  const settings = useSyncExternalStore(
    subscribe,
    getSettingsSnapshot,
    getServerSnapshot
  );

  const updateSettings = useCallback((partial: Partial<EditorSettings>) => {
    const current = getSettingsSnapshot();
    const next = { ...current, ...partial };
    emitChange(next);
  }, []);

  const resetSettings = useCallback(() => {
    emitChange(DEFAULT_EDITOR_SETTINGS);
  }, []);

  return { settings, updateSettings, resetSettings };
}
