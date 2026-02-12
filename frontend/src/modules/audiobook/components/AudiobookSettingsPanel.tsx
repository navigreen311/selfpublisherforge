"use client";

import { useState, useCallback } from "react";
import { toast } from "sonner";
import { Settings, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { useUpdateAudiobookProject } from "../hooks";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AudiobookSettingsPanelProps {
  projectId: string;
  currentSettings: {
    output_format: string;
    sample_rate: number;
    bit_rate: number;
    channels: number;
    target_platform: string;
    narration_style: Record<string, unknown> | null;
  };
  onSave: () => void;
}

type OutputFormat = "mp3" | "m4b" | "flac" | "wav";
type TargetPlatform = "acx" | "findaway" | "generic";
type EmphasisLevel = "subtle" | "moderate" | "dramatic";

interface NarrationStyle {
  pacing: number;
  paragraph_pause: number;
  chapter_pause: number;
  emphasis: EmphasisLevel;
}

// ---------------------------------------------------------------------------
// Platform presets
// ---------------------------------------------------------------------------

const PLATFORM_PRESETS: Record<
  TargetPlatform,
  { format: OutputFormat; sample_rate: number; bit_rate: number; channels: number }
> = {
  acx: { format: "mp3", sample_rate: 44100, bit_rate: 192, channels: 1 },
  findaway: { format: "mp3", sample_rate: 44100, bit_rate: 192, channels: 1 },
  generic: { format: "mp3", sample_rate: 48000, bit_rate: 256, channels: 2 },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AudiobookSettingsPanel({
  projectId,
  currentSettings,
  onSave,
}: AudiobookSettingsPanelProps) {
  const updateProject = useUpdateAudiobookProject(projectId);

  // Audio output state
  const [outputFormat, setOutputFormat] = useState<OutputFormat>(
    (currentSettings.output_format as OutputFormat) || "mp3",
  );
  const [sampleRate, setSampleRate] = useState(currentSettings.sample_rate || 44100);
  const [bitRate, setBitRate] = useState(currentSettings.bit_rate || 192);
  const [channels, setChannels] = useState(currentSettings.channels || 1);

  // Platform state
  const [platform, setPlatform] = useState<TargetPlatform>(
    (currentSettings.target_platform as TargetPlatform) || "acx",
  );

  // Narration style state
  const existingStyle = currentSettings.narration_style as NarrationStyle | null;
  const [pacing, setPacing] = useState(existingStyle?.pacing ?? 1.0);
  const [paragraphPause, setParagraphPause] = useState(existingStyle?.paragraph_pause ?? 1.5);
  const [chapterPause, setChapterPause] = useState(existingStyle?.chapter_pause ?? 3.0);
  const [emphasis, setEmphasis] = useState<EmphasisLevel>(existingStyle?.emphasis ?? "moderate");

  const handlePlatformChange = useCallback(
    (value: string) => {
      const p = value as TargetPlatform;
      setPlatform(p);
      const preset = PLATFORM_PRESETS[p];
      setOutputFormat(preset.format);
      setSampleRate(preset.sample_rate);
      setBitRate(preset.bit_rate);
      setChannels(preset.channels);
    },
    [],
  );

  const handleSave = useCallback(() => {
    updateProject.mutate(
      {
        output_format: outputFormat,
        sample_rate: sampleRate,
        bit_rate: bitRate,
        channels,
        target_platform: platform,
        narration_style: {
          pacing,
          paragraph_pause: paragraphPause,
          chapter_pause: chapterPause,
          emphasis,
        },
      },
      {
        onSuccess: () => {
          toast.success("Settings saved");
          onSave();
        },
      },
    );
  }, [
    updateProject,
    outputFormat,
    sampleRate,
    bitRate,
    channels,
    platform,
    pacing,
    paragraphPause,
    chapterPause,
    emphasis,
    onSave,
  ]);

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Settings className="h-5 w-5" />
          Project Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ---- Target Platform ---- */}
        <section className="space-y-3">
          <Label className="text-sm font-semibold">Target Platform</Label>
          <Select value={platform} onValueChange={handlePlatformChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select platform..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="acx">ACX / Audible</SelectItem>
              <SelectItem value="findaway">Findaway Voices</SelectItem>
              <SelectItem value="generic">Generic</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Selecting a platform auto-configures recommended audio settings.
          </p>
        </section>

        <Separator />

        {/* ---- Audio Output Settings ---- */}
        <section className="space-y-4">
          <Label className="text-sm font-semibold">Audio Output Settings</Label>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Output Format</Label>
            <Select value={outputFormat} onValueChange={(v) => setOutputFormat(v as OutputFormat)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="mp3">MP3</SelectItem>
                <SelectItem value="m4b">M4B (Audiobook)</SelectItem>
                <SelectItem value="flac">FLAC</SelectItem>
                <SelectItem value="wav">WAV</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Sample Rate</Label>
            <Select
              value={String(sampleRate)}
              onValueChange={(v) => setSampleRate(Number(v))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="44100">44,100 Hz</SelectItem>
                <SelectItem value="48000">48,000 Hz</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Bit Rate</Label>
            <Select value={String(bitRate)} onValueChange={(v) => setBitRate(Number(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="128">128 kbps</SelectItem>
                <SelectItem value="192">192 kbps</SelectItem>
                <SelectItem value="256">256 kbps</SelectItem>
                <SelectItem value="320">320 kbps</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Channels</Label>
            <Select value={String(channels)} onValueChange={(v) => setChannels(Number(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Mono (recommended for ACX)</SelectItem>
                <SelectItem value="2">Stereo</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </section>

        <Separator />

        {/* ---- Narration Style ---- */}
        <section className="space-y-4">
          <Label className="text-sm font-semibold">Narration Style</Label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs text-muted-foreground">Pacing</Label>
              <span className="text-xs font-mono text-muted-foreground">
                {pacing.toFixed(1)}x
              </span>
            </div>
            <Slider
              value={[pacing]}
              min={0.8}
              max={1.2}
              step={0.05}
              onValueChange={([v]) => setPacing(v)}
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>0.8x</span>
              <span>1.0x</span>
              <span>1.2x</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs text-muted-foreground">Pause Between Paragraphs</Label>
              <span className="text-xs font-mono text-muted-foreground">
                {paragraphPause.toFixed(1)}s
              </span>
            </div>
            <Slider
              value={[paragraphPause]}
              min={0.5}
              max={3}
              step={0.1}
              onValueChange={([v]) => setParagraphPause(v)}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs text-muted-foreground">Pause Between Chapters</Label>
              <span className="text-xs font-mono text-muted-foreground">
                {chapterPause.toFixed(1)}s
              </span>
            </div>
            <Slider
              value={[chapterPause]}
              min={1}
              max={5}
              step={0.5}
              onValueChange={([v]) => setChapterPause(v)}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Emphasis Level</Label>
            <Select value={emphasis} onValueChange={(v) => setEmphasis(v as EmphasisLevel)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="subtle">Subtle</SelectItem>
                <SelectItem value="moderate">Moderate</SelectItem>
                <SelectItem value="dramatic">Dramatic</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </section>

        <Separator />

        {/* ---- Save ---- */}
        <Button
          className="w-full"
          onClick={handleSave}
          disabled={updateProject.isPending}
        >
          {updateProject.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Save Settings
        </Button>
      </CardContent>
    </Card>
  );
}
