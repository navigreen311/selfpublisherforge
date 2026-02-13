"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  CircleDot,
  Mic,
  Wand2,
  Download,
  Shield,
  RefreshCw,
  Plus,
  GripVertical,
  BookOpen,
  Settings,
  Users,
  FileAudio,
  type LucideIcon,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types (local to this component — canonical types live in ../types.ts)
// ---------------------------------------------------------------------------

type ChapterStatus = "pending" | "generating" | "review" | "approved" | "failed";

type ProjectStatus = "draft" | "generating" | "reviewing" | "mastering" | "complete";

interface AudiobookChapter {
  id: string;
  number: number;
  title: string;
  status: ChapterStatus;
  duration: number; // seconds
  content: string;
  audioUrl?: string;
  sentences?: string[];
}

interface VoiceProfile {
  id: string;
  name: string;
  language: string;
  accent?: string;
  gender: "male" | "female" | "neutral";
  previewUrl?: string;
}

interface CharacterVoice {
  character: string;
  voiceId: string;
}

interface QualityMetrics {
  naturalness: number;
  clarity: number;
  pace: number;
}

interface AudiobookProject {
  id: string;
  title: string;
  status: ProjectStatus;
  chapters: AudiobookChapter[];
  narratorVoiceId: string;
  characterVoices: CharacterVoice[];
  totalDuration: number; // seconds
  estimatedCost: number;
  actualCost: number;
  outputFormat: string;
  sampleRate: number;
  platform: string;
  qualityMetrics: QualityMetrics;
}

// ---------------------------------------------------------------------------
// Mock data (for development / demo — will be replaced by hooks)
// ---------------------------------------------------------------------------

const MOCK_VOICES: VoiceProfile[] = [
  { id: "v1", name: "James Narrator", language: "English", accent: "American", gender: "male" },
  { id: "v2", name: "Sarah Reader", language: "English", accent: "British", gender: "female" },
  { id: "v3", name: "Alex Neutral", language: "English", accent: "American", gender: "neutral" },
];

const MOCK_PROJECT: AudiobookProject = {
  id: "proj-1",
  title: "The Art of Code",
  status: "reviewing",
  narratorVoiceId: "v1",
  characterVoices: [
    { character: "Professor Chen", voiceId: "v2" },
    { character: "Detective Voss", voiceId: "v3" },
  ],
  totalDuration: 18720,
  estimatedCost: 42.5,
  actualCost: 28.75,
  outputFormat: "mp3",
  sampleRate: 44100,
  platform: "acx",
  qualityMetrics: { naturalness: 87, clarity: 92, pace: 78 },
  chapters: [
    { id: "ch1", number: 1, title: "The Beginning", status: "approved", duration: 3420, content: "It was a dark and stormy night when the first line of code was written. The programmer sat hunched over a glowing terminal, fingers dancing across the keys with practiced precision.\n\nThe cursor blinked steadily, a metronome keeping time with the rain pattering against the window. Each keystroke brought new logic into existence — functions that would calculate, loops that would iterate, conditions that would branch the flow of execution into countless possibilities.\n\n\"Hello, World,\" the screen displayed, and with those two words, a new chapter in computing history had begun." },
    { id: "ch2", number: 2, title: "First Steps", status: "approved", duration: 2890, content: "Learning to code is like learning a new language — at first, every symbol seems foreign, every syntax rule arbitrary. But gradually, patterns emerge from the chaos." },
    { id: "ch3", number: 3, title: "The Challenge", status: "review", duration: 4100, content: "The bug had been lurking in the codebase for weeks, hiding in the shadows of deeply nested conditionals and legacy abstractions that nobody dared to touch." },
    { id: "ch4", number: 4, title: "Discovery", status: "generating", duration: 0, content: "Professor Chen leaned forward, her eyes widening as the algorithm produced results that defied every prediction. \"This changes everything,\" she whispered." },
    { id: "ch5", number: 5, title: "The Algorithm", status: "pending", duration: 0, content: "At its core, every algorithm is a recipe — a set of instructions that, when followed precisely, transforms input into output." },
    { id: "ch6", number: 6, title: "Resolution", status: "pending", duration: 0, content: "The final commit was pushed at 3:47 AM. The tests passed. The build succeeded. And for the first time in weeks, the team could breathe." },
    { id: "ch7", number: 7, title: "Epilogue", status: "failed", duration: 0, content: "Years later, that first program — clumsy, inefficient, beautiful — still ran on a server in a forgotten data center, faithfully executing its simple purpose." },
  ],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDuration(seconds: number): string {
  if (seconds <= 0) return "--:--";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`;
}

const STATUS_CONFIG: Record<ChapterStatus, { icon: LucideIcon; color: string; label: string }> = {
  pending: { icon: CircleDot, color: "text-muted-foreground", label: "Pending" },
  generating: { icon: Loader2, color: "text-blue-500", label: "Generating" },
  review: { icon: Clock, color: "text-yellow-500", label: "Review" },
  approved: { icon: CheckCircle2, color: "text-green-500", label: "Approved" },
  failed: { icon: AlertCircle, color: "text-red-500", label: "Failed" },
};

const PROJECT_STATUS_VARIANT: Record<ProjectStatus, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "secondary",
  generating: "default",
  reviewing: "outline",
  mastering: "default",
  complete: "secondary",
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface TopBarProps {
  project: AudiobookProject;
  editingTitle: boolean;
  titleDraft: string;
  onTitleClick: () => void;
  onTitleChange: (v: string) => void;
  onTitleBlur: () => void;
  onGenerateAll: () => void;
  onMaster: () => void;
  onValidate: () => void;
}

function TopBar({
  project,
  editingTitle,
  titleDraft,
  onTitleClick,
  onTitleChange,
  onTitleBlur,
  onGenerateAll,
  onMaster,
  onValidate,
}: TopBarProps) {
  const completedCount = project.chapters.filter((c) => c.status === "approved").length;
  const totalCount = project.chapters.length;
  const progressPct = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="h-16 border-b flex items-center gap-4 px-4 bg-background shrink-0">
      {/* Project title */}
      <div className="flex items-center gap-2 min-w-0">
        <BookOpen className="h-5 w-5 text-primary shrink-0" />
        {editingTitle ? (
          <input
            type="text"
            value={titleDraft}
            onChange={(e) => onTitleChange(e.target.value)}
            onBlur={onTitleBlur}
            onKeyDown={(e) => e.key === "Enter" && onTitleBlur()}
            autoFocus
            className="text-lg font-semibold bg-transparent border-b border-primary outline-none min-w-0"
          />
        ) : (
          <h1
            className="text-lg font-semibold truncate cursor-pointer hover:text-primary transition-colors"
            onClick={onTitleClick}
            title="Click to edit"
          >
            {project.title}
          </h1>
        )}
        <Badge variant={PROJECT_STATUS_VARIANT[project.status]}>
          {project.status}
        </Badge>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2 min-w-[200px]">
        <Progress value={progressPct} className="h-2 flex-1" />
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {completedCount}/{totalCount} chapters
        </span>
      </div>

      {/* Duration + Cost */}
      <div className="hidden lg:flex items-center gap-4 text-sm text-muted-foreground">
        <span className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          {formatDuration(project.totalDuration)}
        </span>
        <span className="flex items-center gap-1">
          Est. {formatCost(project.estimatedCost)} / Actual {formatCost(project.actualCost)}
        </span>
      </div>

      <div className="flex-1" />

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onGenerateAll}>
          <Wand2 className="h-4 w-4 mr-1" />
          Generate All
        </Button>
        <Button variant="outline" size="sm" onClick={onMaster}>
          <Download className="h-4 w-4 mr-1" />
          Master & Export
        </Button>
        <Button variant="outline" size="sm" onClick={onValidate}>
          <Shield className="h-4 w-4 mr-1" />
          Validate ACX
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

interface ChapterListProps {
  chapters: AudiobookChapter[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function ChapterList({ chapters, selectedId, onSelect }: ChapterListProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  const handleDragStart = useCallback((e: React.DragEvent, id: string) => {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", id);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, id: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverId(id);
  }, []);

  const handleDragLeave = useCallback(() => setDragOverId(null), []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDraggedId(null);
    setDragOverId(null);
    // Reorder logic would go here via store/hook mutation
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedId(null);
    setDragOverId(null);
  }, []);

  const sorted = useMemo(
    () => [...chapters].sort((a, b) => a.number - b.number),
    [chapters]
  );

  return (
    <div className="w-72 border-r flex flex-col bg-card shrink-0">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground">Chapters</h3>
        <span className="text-xs text-muted-foreground">{chapters.length} total</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {sorted.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No chapters found.
          </div>
        ) : (
          <ul className="py-1">
            {sorted.map((chapter) => {
              const cfg = STATUS_CONFIG[chapter.status];
              const Icon = cfg.icon;
              const isActive = chapter.id === selectedId;

              return (
                <li
                  key={chapter.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, chapter.id)}
                  onDragOver={(e) => handleDragOver(e, chapter.id)}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onDragEnd={handleDragEnd}
                  onClick={() => onSelect(chapter.id)}
                  className={cn(
                    "px-3 py-2.5 cursor-pointer border-l-2 transition-colors group",
                    "hover:bg-accent/50",
                    isActive
                      ? "border-l-primary bg-accent"
                      : "border-l-transparent",
                    draggedId === chapter.id && "opacity-50",
                    dragOverId === chapter.id &&
                      draggedId !== chapter.id &&
                      "bg-blue-50 border-l-blue-400"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <GripVertical className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                    <span className="text-xs text-muted-foreground font-mono shrink-0">
                      {chapter.number}.
                    </span>
                    <p className="text-sm font-medium text-foreground truncate flex-1">
                      {chapter.title}
                    </p>
                    <Icon
                      className={cn(
                        "h-4 w-4 shrink-0",
                        cfg.color,
                        chapter.status === "generating" && "animate-spin"
                      )}
                    />
                  </div>
                  <div className="flex items-center justify-between mt-1 pl-7">
                    <span className="text-xs text-muted-foreground">{cfg.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatDuration(chapter.duration)}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Summary footer */}
      <div className="border-t px-4 py-2 bg-muted/30">
        <p className="text-xs text-muted-foreground">
          {chapters.filter((c) => c.status === "approved").length} approved |{" "}
          {formatDuration(chapters.reduce((sum, ch) => sum + ch.duration, 0))} total
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

interface ChapterContentProps {
  chapter: AudiobookChapter | null;
  playingSentenceIdx: number;
  onGenerate: (id: string) => void;
  onRegenerate: (id: string) => void;
}

function ChapterContentPanel({
  chapter,
  playingSentenceIdx,
  onGenerate,
  onRegenerate,
}: ChapterContentProps) {
  const sentences = useMemo(() => {
    if (!chapter) return [];
    // Split content into sentences for highlighting
    return chapter.content.split(/(?<=[.!?])\s+/).filter((s) => s.trim().length > 0);
  }, [chapter]);

  if (!chapter) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
        <BookOpen className="h-12 w-12 mb-4 opacity-30" />
        <p className="text-sm">Select a chapter to view its content and audio.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Chapter header */}
      <div className="flex items-center justify-between px-6 py-3 border-b bg-muted/20">
        <div>
          <h2 className="text-base font-semibold">
            Chapter {chapter.number}: {chapter.title}
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {sentences.length} sentences | {formatDuration(chapter.duration)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {chapter.status === "pending" && (
            <Button size="sm" onClick={() => onGenerate(chapter.id)}>
              <Mic className="h-4 w-4 mr-1" />
              Generate Audio
            </Button>
          )}
          {(chapter.status === "approved" || chapter.status === "review" || chapter.status === "failed") && (
            <Button variant="outline" size="sm" onClick={() => onRegenerate(chapter.id)}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Regenerate
            </Button>
          )}
        </div>
      </div>

      {/* Manuscript text (read-only, with sentence highlighting) */}
      <div className="flex-1 overflow-y-auto p-6">
        <div
          className="max-w-prose mx-auto leading-relaxed"
          style={{
            fontFamily: "'Georgia', 'Times New Roman', serif",
            fontSize: "16px",
            lineHeight: "1.8",
          }}
        >
          {sentences.map((sentence, idx) => (
            <span
              key={idx}
              className={cn(
                "transition-colors",
                playingSentenceIdx === idx
                  ? "bg-primary/20 text-primary rounded px-0.5"
                  : "text-foreground"
              )}
            >
              {sentence}{" "}
            </span>
          ))}
        </div>
      </div>

      {/* Waveform placeholder (for wavesurfer.js integration from VF26) */}
      <div className="h-48 border-t bg-muted/10 flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 border-b">
          <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
            <FileAudio className="h-3.5 w-3.5" />
            Audio Waveform
          </span>
          {chapter.status === "generating" && (
            <span className="text-xs text-blue-500 flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Generating audio...
            </span>
          )}
        </div>
        <div className="flex-1 flex items-center justify-center">
          {chapter.audioUrl || chapter.status === "approved" || chapter.status === "review" ? (
            <div className="w-full h-full px-4 py-2 flex items-center">
              {/* Placeholder waveform bars */}
              <div className="w-full h-full flex items-end gap-px">
                {Array.from({ length: 100 }, (_, i) => (
                  <div
                    key={i}
                    className={cn(
                      "flex-1 rounded-t transition-colors",
                      playingSentenceIdx >= 0 && i < (playingSentenceIdx + 1) * (100 / Math.max(1, sentences.length))
                        ? "bg-primary"
                        : "bg-muted-foreground/20"
                    )}
                    style={{
                      height: `${20 + Math.random() * 80}%`,
                    }}
                  />
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {chapter.status === "generating"
                ? "Audio is being generated..."
                : "No audio available. Generate audio to see the waveform."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

interface SettingsPanelProps {
  project: AudiobookProject;
  voices: VoiceProfile[];
  onNarratorChange: (voiceId: string) => void;
  onCharacterVoiceChange: (character: string, voiceId: string) => void;
  onOutputFormatChange: (format: string) => void;
  onPlatformChange: (platform: string) => void;
  onSampleRateChange: (rate: number) => void;
}

function SettingsPanel({
  project,
  voices,
  onNarratorChange,
  onCharacterVoiceChange,
  onOutputFormatChange,
  onPlatformChange,
  onSampleRateChange,
}: SettingsPanelProps) {
  const [ssmlEnabled, setSsmlEnabled] = useState(false);
  const [pronunciationWord, setPronunciationWord] = useState("");

  return (
    <div className="w-80 border-l flex flex-col bg-card shrink-0">
      <div className="flex items-center gap-2 px-4 py-3 border-b">
        <Settings className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold text-foreground">Settings</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Narrator Voice */}
        <div className="space-y-2">
          <Label className="text-xs font-medium">Narrator Voice</Label>
          <Select value={project.narratorVoiceId} onValueChange={onNarratorChange}>
            <SelectTrigger className="h-9 text-sm">
              <SelectValue placeholder="Select narrator..." />
            </SelectTrigger>
            <SelectContent>
              {voices.map((voice) => (
                <SelectItem key={voice.id} value={voice.id}>
                  <span className="flex items-center gap-2">
                    <Mic className="h-3.5 w-3.5" />
                    {voice.name}
                    <span className="text-muted-foreground text-xs">
                      ({voice.gender})
                    </span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Character Voice Mapping */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs font-medium flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              Character Voices
            </Label>
          </div>
          {project.characterVoices.length === 0 ? (
            <p className="text-xs text-muted-foreground">No characters detected.</p>
          ) : (
            <div className="space-y-2">
              {project.characterVoices.map((cv) => (
                <Card key={cv.character} className="p-2">
                  <div className="space-y-1.5">
                    <span className="text-xs font-medium">{cv.character}</span>
                    <Select
                      value={cv.voiceId}
                      onValueChange={(v) => onCharacterVoiceChange(cv.character, v)}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {voices.map((voice) => (
                          <SelectItem key={voice.id} value={voice.id}>
                            {voice.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* SSML Editor Toggle */}
        <div className="flex items-center justify-between">
          <Label className="text-xs font-medium">SSML Editor</Label>
          <Switch checked={ssmlEnabled} onCheckedChange={setSsmlEnabled} />
        </div>
        {ssmlEnabled && (
          <div className="rounded-md border bg-muted/30 p-3">
            <textarea
              className="w-full h-24 text-xs font-mono bg-transparent resize-none outline-none"
              placeholder={'<speak>\n  <prosody rate="medium">\n    Your SSML here...\n  </prosody>\n</speak>'}
            />
          </div>
        )}

        {/* Quality Metrics */}
        <div className="space-y-3">
          <Label className="text-xs font-medium">Quality Metrics</Label>
          <div className="space-y-2">
            {(
              [
                { label: "Naturalness", value: project.qualityMetrics.naturalness },
                { label: "Clarity", value: project.qualityMetrics.clarity },
                { label: "Pace", value: project.qualityMetrics.pace },
              ] as const
            ).map(({ label, value }) => (
              <div key={label} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{label}</span>
                  <span className="text-xs font-medium">{value}%</span>
                </div>
                <Progress value={value} className="h-1.5" />
              </div>
            ))}
          </div>
        </div>

        {/* Pronunciation Dictionary */}
        <div className="space-y-2">
          <Label className="text-xs font-medium">Pronunciation Dictionary</Label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={pronunciationWord}
              onChange={(e) => setPronunciationWord(e.target.value)}
              placeholder="Word or name..."
              className="flex-1 h-8 text-xs rounded-md border border-input bg-background px-2 outline-none focus:ring-1 focus:ring-ring"
            />
            <Button
              variant="outline"
              size="sm"
              className="h-8 px-2"
              onClick={() => setPronunciationWord("")}
            >
              <Plus className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Output Settings */}
        <div className="space-y-3">
          <Label className="text-xs font-medium">Output Settings</Label>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Format</Label>
            <Select value={project.outputFormat} onValueChange={onOutputFormatChange}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="mp3">MP3</SelectItem>
                <SelectItem value="wav">WAV</SelectItem>
                <SelectItem value="flac">FLAC</SelectItem>
                <SelectItem value="m4b">M4B (Audiobook)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Platform</Label>
            <Select value={project.platform} onValueChange={onPlatformChange}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="acx">ACX / Audible</SelectItem>
                <SelectItem value="findaway">Findaway Voices</SelectItem>
                <SelectItem value="google">Google Play Books</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs text-muted-foreground">Sample Rate</Label>
              <span className="text-xs font-mono text-muted-foreground">
                {project.sampleRate.toLocaleString()} Hz
              </span>
            </div>
            <Slider
              value={[project.sampleRate]}
              min={22050}
              max={48000}
              step={50}
              onValueChange={([v]) => onSampleRateChange(v)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

interface BottomPlayerProps {
  chapter: AudiobookChapter | null;
  isPlaying: boolean;
  currentTime: number;
  speed: number;
  volume: number;
  muted: boolean;
  onPlayPause: () => void;
  onSkipBack: () => void;
  onSkipForward: () => void;
  onSeek: (time: number) => void;
  onSpeedChange: (speed: number) => void;
  onVolumeChange: (volume: number) => void;
  onMuteToggle: () => void;
}

function BottomPlayer({
  chapter,
  isPlaying,
  currentTime,
  speed,
  volume,
  muted,
  onPlayPause,
  onSkipBack,
  onSkipForward,
  onSeek,
  onSpeedChange,
  onVolumeChange,
  onMuteToggle,
}: BottomPlayerProps) {
  const duration = chapter?.duration ?? 0;
  const hasAudio = chapter && (chapter.status === "approved" || chapter.status === "review");

  return (
    <div className="h-16 border-t flex items-center gap-4 px-4 bg-background shrink-0">
      {/* Playback controls */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          disabled={!hasAudio}
          onClick={onSkipBack}
        >
          <SkipBack className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9"
          disabled={!hasAudio}
          onClick={onPlayPause}
        >
          {isPlaying ? (
            <Pause className="h-5 w-5" />
          ) : (
            <Play className="h-5 w-5" />
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          disabled={!hasAudio}
          onClick={onSkipForward}
        >
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>

      {/* Current chapter info */}
      <div className="min-w-0 text-sm">
        {chapter ? (
          <p className="truncate text-foreground">
            Ch. {chapter.number}: {chapter.title}
          </p>
        ) : (
          <p className="text-muted-foreground">No chapter selected</p>
        )}
      </div>

      {/* Seek bar */}
      <div className="flex-1 flex items-center gap-2">
        <span className="text-xs text-muted-foreground font-mono w-12 text-right">
          {formatDuration(currentTime)}
        </span>
        <Slider
          value={[currentTime]}
          min={0}
          max={Math.max(duration, 1)}
          step={1}
          onValueChange={([v]) => onSeek(v)}
          disabled={!hasAudio}
          className="flex-1"
        />
        <span className="text-xs text-muted-foreground font-mono w-12">
          {formatDuration(duration)}
        </span>
      </div>

      {/* Speed selector */}
      <Select value={speed.toString()} onValueChange={(v) => onSpeedChange(parseFloat(v))}>
        <SelectTrigger className="h-8 w-20 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {[0.5, 0.75, 1, 1.25, 1.5, 2].map((s) => (
            <SelectItem key={s} value={s.toString()}>
              {s}x
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Volume */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onMuteToggle}
        >
          {muted ? (
            <VolumeX className="h-4 w-4" />
          ) : (
            <Volume2 className="h-4 w-4" />
          )}
        </Button>
        <Slider
          value={[muted ? 0 : volume]}
          min={0}
          max={100}
          step={1}
          onValueChange={([v]) => onVolumeChange(v)}
          className="w-20"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main AudiobookStudio component
// ---------------------------------------------------------------------------

interface AudiobookStudioProps {
  projectId: string;
}

export function AudiobookStudio({ projectId }: AudiobookStudioProps) {
  // ------ State ------
  // TODO: Replace mock data with real hooks:
  // const { data: project } = useAudiobookProject(projectId);
  // const ws = useAudiobookWebSocket(projectId);
  // const store = useAudiobookStudioStore();
  const [project, setProject] = useState<AudiobookProject>(MOCK_PROJECT);
  const [voices] = useState<VoiceProfile[]>(MOCK_VOICES);
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(
    project.chapters[0]?.id ?? null
  );

  // Title editing
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(project.title);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [volume, setVolume] = useState(80);
  const [muted, setMuted] = useState(false);
  const [playingSentenceIdx, setPlayingSentenceIdx] = useState(-1);

  // Playback simulation timer
  const playbackTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const selectedChapter = useMemo(
    () => project.chapters.find((c) => c.id === selectedChapterId) ?? null,
    [project.chapters, selectedChapterId]
  );

  // ------ Playback simulation ------
  useEffect(() => {
    if (playbackTimerRef.current) {
      clearInterval(playbackTimerRef.current);
      playbackTimerRef.current = null;
    }

    if (isPlaying && selectedChapter) {
      playbackTimerRef.current = setInterval(() => {
        setCurrentTime((prev) => {
          const next = prev + playbackSpeed;
          if (next >= selectedChapter.duration) {
            setIsPlaying(false);
            return selectedChapter.duration;
          }
          return next;
        });
      }, 1000);
    }

    return () => {
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }
    };
  }, [isPlaying, selectedChapter, playbackSpeed]);

  // Sentence highlighting sync
  useEffect(() => {
    if (!selectedChapter || !isPlaying || selectedChapter.duration <= 0) {
      setPlayingSentenceIdx(-1);
      return;
    }
    const sentences = selectedChapter.content
      .split(/(?<=[.!?])\s+/)
      .filter((s) => s.trim().length > 0);
    const sentenceCount = sentences.length;
    if (sentenceCount === 0) {
      setPlayingSentenceIdx(-1);
      return;
    }
    const progress = currentTime / selectedChapter.duration;
    const idx = Math.min(Math.floor(progress * sentenceCount), sentenceCount - 1);
    setPlayingSentenceIdx(idx);
  }, [currentTime, selectedChapter, isPlaying]);

  // Reset time when chapter changes
  useEffect(() => {
    setCurrentTime(0);
    setIsPlaying(false);
    setPlayingSentenceIdx(-1);
  }, [selectedChapterId]);

  // ------ Handlers ------
  const handleTitleClick = useCallback(() => {
    setTitleDraft(project.title);
    setEditingTitle(true);
  }, [project.title]);

  const handleTitleBlur = useCallback(() => {
    setEditingTitle(false);
    if (titleDraft.trim() && titleDraft !== project.title) {
      setProject((prev) => ({ ...prev, title: titleDraft.trim() }));
    }
  }, [titleDraft, project.title]);

  const handleGenerateAll = useCallback(() => {
    // Trigger generation for all pending chapters
    setProject((prev) => ({
      ...prev,
      status: "generating",
      chapters: prev.chapters.map((ch) =>
        ch.status === "pending" ? { ...ch, status: "generating" as ChapterStatus } : ch
      ),
    }));
  }, []);

  const handleMaster = useCallback(() => {
    setProject((prev) => ({ ...prev, status: "mastering" }));
  }, []);

  const handleValidate = useCallback(() => {
    // ACX validation would run here
  }, []);

  const handleGenerateChapter = useCallback((chapterId: string) => {
    setProject((prev) => ({
      ...prev,
      chapters: prev.chapters.map((ch) =>
        ch.id === chapterId ? { ...ch, status: "generating" as ChapterStatus } : ch
      ),
    }));
  }, []);

  const handleRegenerateChapter = useCallback((chapterId: string) => {
    setProject((prev) => ({
      ...prev,
      chapters: prev.chapters.map((ch) =>
        ch.id === chapterId
          ? { ...ch, status: "generating" as ChapterStatus, duration: 0 }
          : ch
      ),
    }));
  }, []);

  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const handleSkipBack = useCallback(() => {
    setCurrentTime((prev) => Math.max(0, prev - 10));
  }, []);

  const handleSkipForward = useCallback(() => {
    if (!selectedChapter) return;
    setCurrentTime((prev) => Math.min(selectedChapter.duration, prev + 10));
  }, [selectedChapter]);

  const handleNarratorChange = useCallback((voiceId: string) => {
    setProject((prev) => ({ ...prev, narratorVoiceId: voiceId }));
  }, []);

  const handleCharacterVoiceChange = useCallback((character: string, voiceId: string) => {
    setProject((prev) => ({
      ...prev,
      characterVoices: prev.characterVoices.map((cv) =>
        cv.character === character ? { ...cv, voiceId } : cv
      ),
    }));
  }, []);

  const handleOutputFormatChange = useCallback((format: string) => {
    setProject((prev) => ({ ...prev, outputFormat: format }));
  }, []);

  const handlePlatformChange = useCallback((platform: string) => {
    setProject((prev) => ({ ...prev, platform }));
  }, []);

  const handleSampleRateChange = useCallback((rate: number) => {
    setProject((prev) => ({ ...prev, sampleRate: rate }));
  }, []);

  // ------ Render ------
  return (
    <div className="h-screen flex flex-col bg-background">
      <TopBar
        project={project}
        editingTitle={editingTitle}
        titleDraft={titleDraft}
        onTitleClick={handleTitleClick}
        onTitleChange={setTitleDraft}
        onTitleBlur={handleTitleBlur}
        onGenerateAll={handleGenerateAll}
        onMaster={handleMaster}
        onValidate={handleValidate}
      />

      <div className="flex-1 flex overflow-hidden">
        <ChapterList
          chapters={project.chapters}
          selectedId={selectedChapterId}
          onSelect={setSelectedChapterId}
        />

        <ChapterContentPanel
          chapter={selectedChapter}
          playingSentenceIdx={playingSentenceIdx}
          onGenerate={handleGenerateChapter}
          onRegenerate={handleRegenerateChapter}
        />

        <SettingsPanel
          project={project}
          voices={voices}
          onNarratorChange={handleNarratorChange}
          onCharacterVoiceChange={handleCharacterVoiceChange}
          onOutputFormatChange={handleOutputFormatChange}
          onPlatformChange={handlePlatformChange}
          onSampleRateChange={handleSampleRateChange}
        />
      </div>

      <BottomPlayer
        chapter={selectedChapter}
        isPlaying={isPlaying}
        currentTime={currentTime}
        speed={playbackSpeed}
        volume={volume}
        muted={muted}
        onPlayPause={handlePlayPause}
        onSkipBack={handleSkipBack}
        onSkipForward={handleSkipForward}
        onSeek={setCurrentTime}
        onSpeedChange={setPlaybackSpeed}
        onVolumeChange={setVolume}
        onMuteToggle={() => setMuted((prev) => !prev)}
      />
    </div>
  );
}

export default AudiobookStudio;
