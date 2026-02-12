"use client";

import { useState, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Download,
  Upload,
  Image,
  Clock,
  Settings2,
  ChevronDown,
  ChevronRight,
  FileAudio,
  Package,
  CheckCircle,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ExportPlatform = "acx" | "findaway" | "authors_republic" | "google_play" | "custom";

interface PlatformConfig {
  format: string;
  bitrate: string;
  sampleRate: string;
  channels: "mono" | "stereo";
}

interface ExportMetadata {
  title: string;
  subtitle: string;
  author: string;
  narrator: string;
  copyright: string;
  description: string;
  genre: string;
}

interface ExportHistoryItem {
  id: string;
  platform: ExportPlatform;
  format: string;
  createdAt: string;
  fileSize: string;
  downloadUrl: string;
  status: "completed" | "failed" | "expired";
}

interface AudiobookExportProps {
  projectId: string;
  projectTitle?: string;
  onStartExport: (config: {
    platform: ExportPlatform;
    settings: PlatformConfig;
    metadata: ExportMetadata;
    includeCoverArt: boolean;
    includeRetailSample: boolean;
  }) => Promise<void>;
  onDownload?: (exportId: string) => void;
  exportProgress?: number;
  isExporting?: boolean;
  exportHistory?: ExportHistoryItem[];
  coverArtUrl?: string;
}

// ---------------------------------------------------------------------------
// Platform defaults
// ---------------------------------------------------------------------------

const PLATFORM_LABELS: Record<ExportPlatform, string> = {
  acx: "ACX / Audible",
  findaway: "Findaway Voices",
  authors_republic: "Authors Republic",
  google_play: "Google Play",
  custom: "Custom",
};

const PLATFORM_DEFAULTS: Record<ExportPlatform, PlatformConfig> = {
  acx: { format: "mp3", bitrate: "192", sampleRate: "44100", channels: "mono" },
  findaway: { format: "flac", bitrate: "1411", sampleRate: "44100", channels: "mono" },
  authors_republic: { format: "wav", bitrate: "1411", sampleRate: "44100", channels: "mono" },
  google_play: { format: "mp3", bitrate: "192", sampleRate: "44100", channels: "stereo" },
  custom: { format: "mp3", bitrate: "192", sampleRate: "44100", channels: "mono" },
};

const FORMAT_OPTIONS = ["mp3", "flac", "wav", "m4b", "aac", "ogg"];
const BITRATE_OPTIONS = ["64", "96", "128", "192", "256", "320", "1411"];
const SAMPLE_RATE_OPTIONS = ["22050", "44100", "48000"];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PlatformCard({
  platform,
  isSelected,
  onClick,
}: {
  platform: ExportPlatform;
  isSelected: boolean;
  onClick: () => void;
}) {
  const config = PLATFORM_DEFAULTS[platform];
  return (
    <button
      onClick={onClick}
      className={`rounded-lg border-2 p-4 text-left transition-colors ${
        isSelected
          ? "border-indigo-600 bg-indigo-50"
          : "border-gray-200 hover:border-gray-300"
      }`}
    >
      <h3 className="font-semibold text-gray-900 text-sm">{PLATFORM_LABELS[platform]}</h3>
      {platform !== "custom" && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {config.format.toUpperCase()}
          </span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {config.bitrate}kbps
          </span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {(parseInt(config.sampleRate) / 1000).toFixed(1)}kHz
          </span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {config.channels}
          </span>
        </div>
      )}
    </button>
  );
}

function ExportHistoryRow({
  item,
  onDownload,
}: {
  item: ExportHistoryItem;
  onDownload?: (id: string) => void;
}) {
  return (
    <div className="flex items-center justify-between py-3 px-1 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-3">
        <FileAudio className="h-4 w-4 text-gray-500" />
        <div>
          <p className="text-sm font-medium text-gray-900">
            {PLATFORM_LABELS[item.platform]}
          </p>
          <p className="text-xs text-gray-500">
            {item.format.toUpperCase()} &middot; {item.fileSize} &middot;{" "}
            {new Date(item.createdAt).toLocaleDateString()}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {item.status === "completed" && (
          <>
            <Badge className="bg-green-100 text-green-800 hover:bg-green-100 text-xs">
              Completed
            </Badge>
            <button
              onClick={() => onDownload?.(item.id)}
              className="inline-flex items-center gap-1 rounded-md border border-gray-300 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              <Download className="h-3 w-3" />
              Download
            </button>
          </>
        )}
        {item.status === "failed" && (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-100 text-xs">Failed</Badge>
        )}
        {item.status === "expired" && (
          <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-100 text-xs">Expired</Badge>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AudiobookExport({
  projectId,
  projectTitle = "Untitled Audiobook",
  onStartExport,
  onDownload,
  exportProgress = 0,
  isExporting = false,
  exportHistory = [],
  coverArtUrl,
}: AudiobookExportProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<ExportPlatform>("acx");
  const [settings, setSettings] = useState<PlatformConfig>(PLATFORM_DEFAULTS.acx);
  const [showOverrides, setShowOverrides] = useState(false);
  const [includeCoverArt, setIncludeCoverArt] = useState(true);
  const [includeRetailSample, setIncludeRetailSample] = useState(true);
  const [showHistory, setShowHistory] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);

  const [metadata, setMetadata] = useState<ExportMetadata>({
    title: projectTitle,
    subtitle: "",
    author: "",
    narrator: "",
    copyright: "",
    description: "",
    genre: "",
  });

  const handlePlatformSelect = useCallback(
    (platform: ExportPlatform) => {
      setSelectedPlatform(platform);
      if (platform !== "custom") {
        setSettings(PLATFORM_DEFAULTS[platform]);
        setShowOverrides(false);
      } else {
        setShowOverrides(true);
      }
    },
    [],
  );

  const updateSetting = useCallback(
    <K extends keyof PlatformConfig>(key: K, value: PlatformConfig[K]) => {
      setSettings((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const updateMetadata = useCallback(
    <K extends keyof ExportMetadata>(key: K, value: ExportMetadata[K]) => {
      setMetadata((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const handleStartExport = useCallback(async () => {
    if (!metadata.title.trim()) {
      toast.error("Title is required");
      return;
    }
    try {
      setExportComplete(false);
      await onStartExport({
        platform: selectedPlatform,
        settings,
        metadata,
        includeCoverArt,
        includeRetailSample,
      });
      setExportComplete(true);
      toast.success("Export completed successfully");
    } catch {
      toast.error("Export failed. Please try again.");
    }
  }, [selectedPlatform, settings, metadata, includeCoverArt, includeRetailSample, onStartExport]);

  const completedExports = useMemo(
    () => exportHistory.filter((e) => e.status === "completed"),
    [exportHistory],
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Audiobook Export</h2>
          <p className="mt-1 text-sm text-gray-600">
            Configure and export your audiobook for distribution
          </p>
        </div>
        {completedExports.length > 0 && (
          <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">
            <Package className="h-3.5 w-3.5 mr-1" />
            {completedExports.length} export{completedExports.length !== 1 ? "s" : ""}
          </Badge>
        )}
      </div>

      {/* Platform Selection */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-700">
            Distribution Platform
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {(Object.keys(PLATFORM_LABELS) as ExportPlatform[]).map((platform) => (
              <PlatformCard
                key={platform}
                platform={platform}
                isSelected={selectedPlatform === platform}
                onClick={() => handlePlatformSelect(platform)}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Settings Overrides */}
      <Card>
        <CardHeader className="pb-3">
          <button
            onClick={() => setShowOverrides(!showOverrides)}
            className="flex items-center gap-2 w-full text-left"
          >
            {showOverrides ? (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            )}
            <Settings2 className="h-4 w-4 text-gray-500" />
            <CardTitle className="text-sm font-medium text-gray-700">
              Audio Settings
              {!showOverrides && selectedPlatform !== "custom" && (
                <span className="ml-2 text-xs font-normal text-gray-400">
                  (auto-configured for {PLATFORM_LABELS[selectedPlatform]})
                </span>
              )}
            </CardTitle>
          </button>
        </CardHeader>
        {showOverrides && (
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {/* Format */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Format</label>
                <select
                  value={settings.format}
                  onChange={(e) => updateSetting("format", e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  {FORMAT_OPTIONS.map((f) => (
                    <option key={f} value={f}>
                      {f.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Bitrate */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Bitrate (kbps)
                </label>
                <select
                  value={settings.bitrate}
                  onChange={(e) => updateSetting("bitrate", e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  {BITRATE_OPTIONS.map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sample Rate */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Sample Rate
                </label>
                <select
                  value={settings.sampleRate}
                  onChange={(e) => updateSetting("sampleRate", e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  {SAMPLE_RATE_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {(parseInt(r) / 1000).toFixed(1)} kHz
                    </option>
                  ))}
                </select>
              </div>

              {/* Channels */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Channels</label>
                <select
                  value={settings.channels}
                  onChange={(e) =>
                    updateSetting("channels", e.target.value as "mono" | "stereo")
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="mono">Mono</option>
                  <option value="stereo">Stereo</option>
                </select>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-700">Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Title *</label>
              <input
                type="text"
                value={metadata.title}
                onChange={(e) => updateMetadata("title", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Subtitle</label>
              <input
                type="text"
                value={metadata.subtitle}
                onChange={(e) => updateMetadata("subtitle", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Author</label>
              <input
                type="text"
                value={metadata.author}
                onChange={(e) => updateMetadata("author", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Narrator Credits
              </label>
              <input
                type="text"
                value={metadata.narrator}
                onChange={(e) => updateMetadata("narrator", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Copyright</label>
              <input
                type="text"
                value={metadata.copyright}
                onChange={(e) => updateMetadata("copyright", e.target.value)}
                placeholder="\u00a9 2026 Author Name"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Genre</label>
              <input
                type="text"
                value={metadata.genre}
                onChange={(e) => updateMetadata("genre", e.target.value)}
                placeholder="e.g., Fiction, Mystery, Self-Help"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={metadata.description}
                onChange={(e) => updateMetadata("description", e.target.value)}
                rows={3}
                placeholder="Audiobook description for store listing..."
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Options */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-gray-700">Export Options</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Cover Art */}
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="coverArt"
                checked={includeCoverArt}
                onChange={(e) => setIncludeCoverArt(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-indigo-600"
              />
              <div className="flex-1">
                <label htmlFor="coverArt" className="text-sm font-medium text-gray-700">
                  Include cover art
                </label>
                <p className="text-xs text-gray-500">
                  Embed cover image in exported files (required for most platforms)
                </p>
                {includeCoverArt && coverArtUrl && (
                  <div className="mt-2 flex items-center gap-3">
                    <div className="h-16 w-16 rounded border border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden">
                      <img
                        src={coverArtUrl}
                        alt="Cover art preview"
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <span className="text-xs text-gray-500">Cover art preview</span>
                  </div>
                )}
                {includeCoverArt && !coverArtUrl && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-yellow-600">
                    <Image className="h-3.5 w-3.5" />
                    No cover art uploaded yet
                  </div>
                )}
              </div>
            </div>

            {/* Retail Sample */}
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="retailSample"
                checked={includeRetailSample}
                onChange={(e) => setIncludeRetailSample(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-indigo-600"
              />
              <div>
                <label htmlFor="retailSample" className="text-sm font-medium text-gray-700">
                  Include retail sample
                </label>
                <p className="text-xs text-gray-500">
                  Generate a 5-minute preview clip from the beginning of the audiobook
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export Action */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleStartExport}
          disabled={isExporting || !metadata.title.trim()}
          className="inline-flex items-center gap-1.5 rounded-md bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          <Upload className="h-4 w-4" />
          {isExporting ? "Exporting..." : "Start Export"}
        </button>
        <span className="text-xs text-gray-500">
          Output: ZIP of chapter files or single M4B
        </span>
      </div>

      {/* Export Progress */}
      {isExporting && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-200 border-t-indigo-600" />
              <span className="text-sm font-medium text-gray-900">Exporting...</span>
            </div>
            <span className="text-sm font-bold text-indigo-600">{exportProgress}%</span>
          </div>
          <Progress value={exportProgress} className="h-2" />
          <p className="mt-2 text-xs text-gray-500">
            Processing chapters for {PLATFORM_LABELS[selectedPlatform]}...
          </p>
        </Card>
      )}

      {/* Export Complete */}
      {exportComplete && !isExporting && (
        <Card className="border-green-200 bg-green-50 p-6">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <div>
              <h3 className="font-semibold text-green-900">Export Complete</h3>
              <p className="text-sm text-green-700">
                Your audiobook has been exported for {PLATFORM_LABELS[selectedPlatform]}
              </p>
            </div>
          </div>
          <button
            onClick={() => onDownload?.("latest")}
            className="inline-flex items-center gap-1.5 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            <Download className="h-4 w-4" />
            Download Export
          </button>
        </Card>
      )}

      {/* Export History */}
      {exportHistory.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center gap-2 w-full text-left"
            >
              {showHistory ? (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-500" />
              )}
              <Clock className="h-4 w-4 text-gray-500" />
              <CardTitle className="text-sm font-medium text-gray-700">
                Export History ({exportHistory.length})
              </CardTitle>
            </button>
          </CardHeader>
          {showHistory && (
            <CardContent>
              {exportHistory.map((item) => (
                <ExportHistoryRow key={item.id} item={item} onDownload={onDownload} />
              ))}
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
