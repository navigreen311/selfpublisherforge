"use client";

import { useState, useMemo } from "react";
import {
  ChevronLeft,
  DollarSign,
  Clock,
  BarChart3,
  AlertTriangle,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateAudiobookProject } from "@/modules/audiobook/hooks";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface WizardStep3ConfigureProps {
  selectedBookId: string;
  voiceId: string;
  tier: string;
  wordCount: number;
  onBack: () => void;
  onComplete: (projectId: string) => void;
}

interface PlatformConfig {
  label: string;
  format: string;
  bitrate: string;
  sampleRate: string;
  channels: string;
}

interface Provider {
  name: string;
  rate: number;
  quality: string;
  tier: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PLATFORM_CONFIGS: Record<string, PlatformConfig> = {
  acx: {
    label: "ACX/Audible",
    format: "MP3",
    bitrate: "192 kbps CBR",
    sampleRate: "44.1 kHz",
    channels: "Mono",
  },
  findaway: {
    label: "Findaway Voices",
    format: "MP3",
    bitrate: "128-192 kbps",
    sampleRate: "44.1 kHz",
    channels: "Stereo",
  },
  direct: {
    label: "Direct Distribution",
    format: "MP3/AAC",
    bitrate: "256 kbps VBR",
    sampleRate: "48 kHz",
    channels: "Stereo",
  },
  custom: {
    label: "Custom",
    format: "MP3",
    bitrate: "192 kbps",
    sampleRate: "44.1 kHz",
    channels: "Mono",
  },
};

const NARRATION_SPEEDS: Record<string, { label: string; wpm: number }> = {
  slow: { label: "Slow (120 wpm)", wpm: 120 },
  normal: { label: "Normal (150 wpm)", wpm: 150 },
  fast: { label: "Fast (180 wpm)", wpm: 180 },
};

const NARRATION_STYLES = [
  { value: "conversational", label: "Conversational" },
  { value: "professional", label: "Professional" },
  { value: "dramatic", label: "Dramatic" },
  { value: "documentary", label: "Documentary" },
  { value: "storytelling", label: "Storytelling" },
];

const PROVIDERS: Provider[] = [
  { name: "Coqui XTTS (Self-Hosted)", rate: 0.001, quality: "Good", tier: "$" },
  { name: "ElevenLabs (Premium)", rate: 0.03, quality: "Premium", tier: "$$$" },
  { name: "Piper (Fast Preview)", rate: 0.0001, quality: "Basic", tier: "¢" },
];

const PROFESSIONAL_NARRATOR_LOW = 2000;
const PROFESSIONAL_NARRATOR_HIGH = 5000;

const qualityColors: Record<string, string> = {
  Basic: "bg-gray-100 text-gray-800",
  Good: "bg-blue-100 text-blue-800",
  Premium: "bg-purple-100 text-purple-800",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(amount: number): string {
  return amount < 0.01 && amount > 0
    ? `$${amount.toFixed(4)}`
    : `$${amount.toFixed(2)}`;
}

function formatDuration(minutes: number): string {
  const hrs = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hrs === 0) return `${mins}m`;
  return `${hrs}h ${mins}m`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WizardStep3Configure({
  selectedBookId,
  voiceId,
  tier,
  wordCount,
  onBack,
  onComplete,
}: WizardStep3ConfigureProps) {
  const router = useRouter();
  const [platform, setPlatform] = useState<string>("acx");
  const [narrationSpeed, setNarrationSpeed] = useState<string>("normal");
  const [narrationStyle, setNarrationStyle] = useState<string>("conversational");
  const [budgetLimit, setBudgetLimit] = useState<string>("");

  const createProject = useCreateAudiobookProject();

  // Calculate estimates
  const estimatedMinutes = useMemo(() => {
    const wpm = NARRATION_SPEEDS[narrationSpeed].wpm;
    return wordCount / wpm;
  }, [wordCount, narrationSpeed]);

  const providerCosts = useMemo(
    () =>
      PROVIDERS.map((p) => ({
        ...p,
        totalCost: estimatedMinutes * p.rate,
      })),
    [estimatedMinutes]
  );

  const maxCost = Math.max(...providerCosts.map((p) => p.totalCost));
  const budgetValue = budgetLimit ? parseFloat(budgetLimit) : null;
  const isBudgetExceeded =
    budgetValue !== null &&
    !isNaN(budgetValue) &&
    providerCosts.some((p) => p.totalCost > budgetValue);

  const selectedPlatformConfig = PLATFORM_CONFIGS[platform];

  const handleCreateAudiobook = async () => {
    try {
      const result = await createProject.mutateAsync({
        book_id: selectedBookId,
        voice_id: voiceId,
        target_platform: platform,
        output_format: selectedPlatformConfig.format.split("/")[0].toLowerCase(),
        sample_rate: parseInt(selectedPlatformConfig.sampleRate) * 1000,
        bit_rate: parseInt(selectedPlatformConfig.bitrate) * 1000,
        channels: selectedPlatformConfig.channels === "Mono" ? 1 : 2,
        narration_style: {
          pacing: NARRATION_SPEEDS[narrationSpeed].wpm,
          emphasis: narrationStyle,
        },
      });

      toast.success("Audiobook project created successfully!");
      onComplete(result.id);
      router.push(`/audiobook-studio/${result.id}`);
    } catch (error) {
      // Error toast is handled by the mutation
      console.error("Failed to create audiobook:", error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Configure Audiobook</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Set output format, narration preferences, and budget limits
        </p>
      </div>

      {/* Platform Configuration */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="platform">Target Platform</Label>
          <Select value={platform} onValueChange={setPlatform}>
            <SelectTrigger id="platform">
              <SelectValue placeholder="Select platform" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(PLATFORM_CONFIGS).map(([key, config]) => (
                <SelectItem key={key} value={key}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Output Format Display */}
        <div className="border rounded-lg p-4 bg-muted/30 space-y-2">
          <h3 className="font-semibold text-sm">Output Format</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground">Format:</span>
              <span className="ml-2 font-medium">
                {selectedPlatformConfig.format}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Bitrate:</span>
              <span className="ml-2 font-medium">
                {selectedPlatformConfig.bitrate}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Sample Rate:</span>
              <span className="ml-2 font-medium">
                {selectedPlatformConfig.sampleRate}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Channels:</span>
              <span className="ml-2 font-medium">
                {selectedPlatformConfig.channels}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Narration Settings */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="speed">Narration Speed</Label>
          <Select value={narrationSpeed} onValueChange={setNarrationSpeed}>
            <SelectTrigger id="speed">
              <SelectValue placeholder="Select speed" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(NARRATION_SPEEDS).map(([key, speed]) => (
                <SelectItem key={key} value={key}>
                  {speed.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="style">Narration Style</Label>
          <Select value={narrationStyle} onValueChange={setNarrationStyle}>
            <SelectTrigger id="style">
              <SelectValue placeholder="Select style" />
            </SelectTrigger>
            <SelectContent>
              {NARRATION_STYLES.map((style) => (
                <SelectItem key={style.value} value={style.value}>
                  {style.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Cost Estimate Panel */}
      <div className="border rounded-lg overflow-hidden">
        <div className="p-4 border-b bg-muted/30">
          <h3 className="font-semibold text-sm">Cost Estimate</h3>
        </div>
        <div className="p-4 space-y-4">
          {/* Overview cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="border rounded-lg p-3 bg-card space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground">
                <BarChart3 className="h-4 w-4" />
                <span className="text-xs font-medium">Total Words</span>
              </div>
              <p className="text-xl font-bold">{wordCount.toLocaleString()}</p>
            </div>

            <div className="border rounded-lg p-3 bg-card space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span className="text-xs font-medium">Est. Duration</span>
              </div>
              <p className="text-xl font-bold">
                {formatDuration(estimatedMinutes)}
              </p>
              <p className="text-xs text-muted-foreground">
                ~{NARRATION_SPEEDS[narrationSpeed].wpm} words/min
              </p>
            </div>

            <div className="border rounded-lg p-3 bg-card space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                <span className="text-xs font-medium">Est. Cost</span>
              </div>
              <p className="text-xl font-bold">
                {formatCurrency(providerCosts[0]?.totalCost ?? 0)}
              </p>
              <p className="text-xs text-muted-foreground">
                {PROVIDERS[0].tier} tier
              </p>
            </div>
          </div>

          {/* Provider comparison */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Provider Comparison</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/10">
                    <th className="text-left p-2 font-medium">Provider</th>
                    <th className="text-right p-2 font-medium">Cost/Min</th>
                    <th className="text-right p-2 font-medium">Total Est.</th>
                    <th className="text-center p-2 font-medium">Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {providerCosts.map((provider) => {
                    const overBudget =
                      budgetValue !== null &&
                      !isNaN(budgetValue) &&
                      provider.totalCost > budgetValue;

                    return (
                      <tr
                        key={provider.name}
                        className={cn(
                          "border-b last:border-b-0",
                          overBudget && "bg-destructive/5"
                        )}
                      >
                        <td className="p-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs">{provider.name}</span>
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1.5"
                            >
                              {provider.tier}
                            </Badge>
                          </div>
                        </td>
                        <td className="p-2 text-right font-mono text-xs">
                          {formatCurrency(provider.rate)}
                        </td>
                        <td className="p-2 text-right font-mono font-semibold">
                          <span className={cn(overBudget && "text-destructive")}>
                            {formatCurrency(provider.totalCost)}
                          </span>
                          {overBudget && (
                            <AlertTriangle className="inline h-3 w-3 ml-1 text-destructive" />
                          )}
                        </td>
                        <td className="p-2 text-center">
                          <span
                            className={cn(
                              "text-[10px] px-2 py-0.5 rounded-full font-medium",
                              qualityColors[provider.quality] ??
                                "bg-gray-100 text-gray-800"
                            )}
                          >
                            {provider.quality}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Budget limit */}
          <div className="space-y-2">
            <Label htmlFor="budget">Budget Limit (Optional)</Label>
            <div className="flex items-center gap-3">
              <div className="relative flex-1 max-w-xs">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="budget"
                  type="number"
                  min="0"
                  step="0.01"
                  value={budgetLimit}
                  onChange={(e) => setBudgetLimit(e.target.value)}
                  placeholder="Set max budget"
                  className="pl-9"
                />
              </div>
              {isBudgetExceeded && (
                <div className="flex items-center gap-1.5 text-destructive text-sm">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Exceeded by some providers</span>
                </div>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Generation will pause if budget is exceeded
            </p>
          </div>

          {/* Comparison callout */}
          <div className="border rounded-lg p-3 bg-primary/5 space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <h4 className="text-sm font-semibold">Cost Comparison</h4>
            </div>
            <p className="text-sm text-muted-foreground">
              AI narration:{" "}
              <span className="font-semibold text-foreground">
                {formatCurrency(providerCosts[0]?.totalCost ?? 0)}
                {" – "}
                {formatCurrency(providerCosts[1]?.totalCost ?? 0)}
              </span>
              {" vs "}
              Professional narrator:{" "}
              <span className="font-semibold text-foreground">
                ${PROFESSIONAL_NARRATOR_LOW.toLocaleString()} – $
                {PROFESSIONAL_NARRATOR_HIGH.toLocaleString()}+
              </span>
            </p>
            <p className="text-xs text-muted-foreground">
              Save up to{" "}
              <span className="font-semibold text-green-600">
                {Math.round(
                  ((PROFESSIONAL_NARRATOR_LOW -
                    (providerCosts[0]?.totalCost ?? 0)) /
                    PROFESSIONAL_NARRATOR_LOW) *
                    100
                )}
                %
              </span>{" "}
              with AI-powered narration.
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={createProject.isPending}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        <Button
          onClick={handleCreateAudiobook}
          disabled={createProject.isPending}
          size="lg"
        >
          {createProject.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating...
            </>
          ) : (
            "Create Audiobook"
          )}
        </Button>
      </div>
    </div>
  );
}
