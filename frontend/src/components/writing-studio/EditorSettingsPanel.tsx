"use client";

import { cn } from "@/lib/utils";
import { X, Sun, BookOpen, Moon } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ---------------------------------------------------------------------------
// Re-export hook and types for convenience
// ---------------------------------------------------------------------------

export { useEditorSettings, DEFAULT_EDITOR_SETTINGS } from "@/hooks/use-editor-settings";
export type {
  EditorSettings,
  EditorTheme,
  EditorFont,
  EditorFontSize,
} from "@/hooks/use-editor-settings";

// Import for local use
import type { EditorSettings, EditorTheme, EditorFont, EditorFontSize } from "@/hooks/use-editor-settings";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const THEME_OPTIONS: {
  value: EditorTheme;
  label: string;
  icon: typeof Sun;
}[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "sepia", label: "Sepia", icon: BookOpen },
  { value: "dark", label: "Dark", icon: Moon },
];

const FONT_OPTIONS: {
  value: EditorFont;
  label: string;
  family: string;
}[] = [
  { value: "Georgia", label: "Georgia", family: "Georgia, serif" },
  {
    value: "Merriweather",
    label: "Merriweather",
    family: "'Merriweather', serif",
  },
  { value: "Lora", label: "Lora", family: "'Lora', serif" },
  {
    value: "Source Serif Pro",
    label: "Source Serif Pro",
    family: "'Source Serif Pro', serif",
  },
  {
    value: "System Sans",
    label: "System Sans",
    family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
];

const FONT_SIZE_OPTIONS: EditorFontSize[] = [14, 16, 18, 20];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface EditorSettingsPanelProps {
  /** Current editor settings */
  settings: EditorSettings;
  /** Callback when a setting changes — receives partial update */
  onSettingsChange: (partial: Partial<EditorSettings>) => void;
  /** Whether the panel is open */
  isOpen: boolean;
  /** Callback to close the panel */
  onClose: () => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Editor Settings Panel
 *
 * Slides in from the right side and provides live-preview controls for:
 * - **Theme**: Light / Sepia / Dark (icon buttons)
 * - **Font family**: dropdown with preview text
 * - **Font size**: 14 / 16 / 18 / 20 (toggle buttons)
 *
 * All changes apply immediately.
 * Settings are persisted via the `useEditorSettings` hook (localStorage).
 *
 * @example
 * ```tsx
 * const { settings, updateSettings } = useEditorSettings();
 * const [showSettings, setShowSettings] = useState(false);
 *
 * <EditorSettingsPanel
 *   settings={settings}
 *   onSettingsChange={updateSettings}
 *   isOpen={showSettings}
 *   onClose={() => setShowSettings(false)}
 * />
 * ```
 */
export function EditorSettingsPanel({
  settings,
  onSettingsChange,
  isOpen,
  onClose,
  className,
}: EditorSettingsPanelProps) {
  if (!isOpen) return null;

  return (
    <div
      className={cn(
        "absolute right-0 top-0 z-40 h-full w-72 border-l bg-card shadow-lg",
        "animate-in slide-in-from-right-full duration-300",
        className
      )}
      role="dialog"
      aria-label="Editor settings"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold">Editor Settings</h3>
        <button
          type="button"
          onClick={onClose}
          className={cn(
            "inline-flex items-center justify-center rounded-md p-1 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground"
          )}
          aria-label="Close settings"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Settings body */}
      <div className="space-y-6 p-4">
        {/* ---- Theme selection ---- */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Theme
          </label>
          <div className="grid grid-cols-3 gap-2">
            {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => onSettingsChange({ theme: value })}
                className={cn(
                  "flex flex-col items-center gap-1.5 rounded-lg border p-3 text-xs transition-all",
                  "hover:border-primary/50 hover:bg-accent/50",
                  settings.theme === value
                    ? "border-primary bg-accent text-accent-foreground ring-1 ring-primary"
                    : "border-border"
                )}
                aria-pressed={settings.theme === value}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ---- Font selection ---- */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Font
          </label>
          <Select
            value={settings.font}
            onValueChange={(value: string) =>
              onSettingsChange({ font: value as EditorFont })
            }
          >
            <SelectTrigger className="w-full h-9 text-sm">
              <SelectValue placeholder="Select font" />
            </SelectTrigger>
            <SelectContent>
              {FONT_OPTIONS.map(({ value, label, family }) => (
                <SelectItem key={value} value={value}>
                  <span style={{ fontFamily: family }}>{label}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Font preview */}
          <div
            className={cn(
              "rounded-md border p-3 text-sm leading-relaxed",
              settings.theme === "sepia" &&
                "bg-amber-50 text-amber-950 border-amber-200",
              settings.theme === "dark" &&
                "bg-gray-900 text-gray-100 border-gray-700",
              settings.theme === "light" &&
                "bg-white text-gray-900 border-gray-200"
            )}
            style={{
              fontFamily:
                FONT_OPTIONS.find((f) => f.value === settings.font)?.family ||
                "Georgia, serif",
              fontSize: `${settings.fontSize}px`,
              lineHeight: 1.8,
            }}
          >
            The quick brown fox jumps over the lazy dog.
          </div>
        </div>

        {/* ---- Font size ---- */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Size
          </label>
          <div className="flex items-center gap-1">
            {FONT_SIZE_OPTIONS.map((size) => (
              <button
                key={size}
                type="button"
                onClick={() => onSettingsChange({ fontSize: size })}
                className={cn(
                  "flex-1 rounded-md border py-1.5 text-center text-sm font-medium transition-all",
                  "hover:border-primary/50 hover:bg-accent/50",
                  settings.fontSize === size
                    ? "border-primary bg-accent text-accent-foreground ring-1 ring-primary"
                    : "border-border"
                )}
                aria-pressed={settings.fontSize === size}
              >
                {size}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer hint */}
      <div className="absolute bottom-0 left-0 right-0 border-t px-4 py-2">
        <p className="text-[10px] text-muted-foreground text-center">
          Changes are applied immediately and saved automatically
        </p>
      </div>
    </div>
  );
}
