"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Pen,
  Pencil,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type MediaType = "marker" | "crayon" | "colored-pencil";

export interface ColorSwatch {
  id: string;
  hex: string;
  name: string;
}

export interface SimulationPage {
  pageNumber: number;
  lineArtUrl: string;
  simulatedUrls: Record<MediaType, string>; // pre-rendered simulation per media
}

export interface ColoringSimulationProps {
  pages: SimulationPage[];
  currentPageIndex: number;
  onPageChange: (index: number) => void;
  selectedMedia: MediaType;
  onMediaChange: (media: MediaType) => void;
  palette: ColorSwatch[];
  selectedColorId: string | null;
  onColorSelect: (colorId: string) => void;
}

// ---------------------------------------------------------------------------
// Media icons
// ---------------------------------------------------------------------------

// Use simple SVG/icon representations for each media type
function MarkerIcon({ className }: { className?: string }) {
  return <Pen className={className} />;
}

function CrayonIcon({ className }: { className?: string }) {
  // Lucide doesn't have a crayon — we use a styled Pencil variant
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 20h4l12-12-4-4L4 16v4z" />
      <path d="M13.5 6.5l4 4" />
      <path d="M2 22l2-2" />
    </svg>
  );
}

function ColoredPencilIcon({ className }: { className?: string }) {
  return <Pencil className={className} />;
}

const MEDIA_CONFIG: Record<
  MediaType,
  { label: string; icon: (cls: string) => React.ReactNode; description: string }
> = {
  marker: {
    label: "Marker",
    icon: (cls) => <MarkerIcon className={cls} />,
    description: "Bold, saturated colors with slight bleed at edges",
  },
  crayon: {
    label: "Crayon",
    icon: (cls) => <CrayonIcon className={cls} />,
    description: "Waxy texture with visible strokes and uneven coverage",
  },
  "colored-pencil": {
    label: "Colored Pencil",
    icon: (cls) => <ColoredPencilIcon className={cls} />,
    description: "Soft, layered strokes with paper texture showing through",
  },
};

// ---------------------------------------------------------------------------
// Zoom controls
// ---------------------------------------------------------------------------

const ZOOM_MIN = 25;
const ZOOM_MAX = 200;
const ZOOM_STEP = 25;

// ---------------------------------------------------------------------------
// ColoringSimulation
// ---------------------------------------------------------------------------

export function ColoringSimulation({
  pages,
  currentPageIndex,
  onPageChange,
  selectedMedia,
  onMediaChange,
  palette,
  selectedColorId,
  onColorSelect,
}: ColoringSimulationProps) {
  const [zoom, setZoom] = React.useState(100);

  const currentPage = pages[currentPageIndex];
  const canGoPrev = currentPageIndex > 0;
  const canGoNext = currentPageIndex < pages.length - 1;

  const handleZoomIn = () =>
    setZoom((z) => Math.min(z + ZOOM_STEP, ZOOM_MAX));
  const handleZoomOut = () =>
    setZoom((z) => Math.max(z - ZOOM_STEP, ZOOM_MIN));
  const handleZoomReset = () => setZoom(100);

  if (!currentPage) {
    return (
      <Card className="p-12 flex items-center justify-center text-muted-foreground">
        No pages available for simulation.
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Media selector tabs */}
      <Card className="p-4">
        <Tabs
          value={selectedMedia}
          onValueChange={(v) => onMediaChange(v as MediaType)}
        >
          <TabsList className="w-full grid grid-cols-3">
            {(Object.keys(MEDIA_CONFIG) as MediaType[]).map((media) => {
              const cfg = MEDIA_CONFIG[media];
              return (
                <TabsTrigger
                  key={media}
                  value={media}
                  className="flex items-center gap-1.5"
                >
                  {cfg.icon("h-4 w-4")}
                  {cfg.label}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* Description for selected media */}
          {(Object.keys(MEDIA_CONFIG) as MediaType[]).map((media) => (
            <TabsContent key={media} value={media} className="pt-2">
              <p className="text-xs text-muted-foreground">
                {MEDIA_CONFIG[media].description}
              </p>
            </TabsContent>
          ))}
        </Tabs>
      </Card>

      {/* Side-by-side comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original line art */}
        <Card className="overflow-hidden">
          <div className="px-4 py-2 border-b bg-muted/30">
            <h4 className="text-sm font-semibold text-center">
              Original Line Art
            </h4>
          </div>
          <div className="relative overflow-auto bg-white aspect-square flex items-center justify-center">
            <div
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: "center center",
                transition: "transform 0.2s ease",
              }}
            >
              <img
                src={currentPage.lineArtUrl}
                alt={`Page ${currentPage.pageNumber} line art`}
                className="max-w-full max-h-full object-contain"
                draggable={false}
              />
            </div>
          </div>
        </Card>

        {/* Simulated colored version */}
        <Card className="overflow-hidden">
          <div className="px-4 py-2 border-b bg-muted/30">
            <h4 className="text-sm font-semibold text-center">
              {MEDIA_CONFIG[selectedMedia].label} Simulation
            </h4>
          </div>
          <div className="relative overflow-auto bg-white aspect-square flex items-center justify-center">
            <div
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: "center center",
                transition: "transform 0.2s ease",
              }}
            >
              <img
                src={currentPage.simulatedUrls[selectedMedia]}
                alt={`Page ${currentPage.pageNumber} ${selectedMedia} simulation`}
                className="max-w-full max-h-full object-contain"
                draggable={false}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Controls bar */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          {/* Page navigation */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => onPageChange(currentPageIndex - 1)}
              disabled={!canGoPrev}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium min-w-[80px] text-center">
              Page {currentPage.pageNumber} / {pages.length}
            </span>
            <Button
              variant="outline"
              size="icon"
              onClick={() => onPageChange(currentPageIndex + 1)}
              disabled={!canGoNext}
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={handleZoomOut}
              disabled={zoom <= ZOOM_MIN}
              aria-label="Zoom out"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>

            <div className="w-32">
              <Slider
                value={[zoom]}
                onValueChange={([v]) => setZoom(v)}
                min={ZOOM_MIN}
                max={ZOOM_MAX}
                step={ZOOM_STEP}
                aria-label="Zoom level"
              />
            </div>
            <span className="text-xs text-muted-foreground w-10 text-right">
              {zoom}%
            </span>

            <Button
              variant="outline"
              size="icon"
              onClick={handleZoomIn}
              disabled={zoom >= ZOOM_MAX}
              aria-label="Zoom in"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleZoomReset}
              aria-label="Reset zoom"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Color palette */}
      <Card className="p-4 space-y-3">
        <Label className="text-sm font-semibold">Simulation Palette</Label>
        <TooltipProvider delayDuration={150}>
          <div className="flex flex-wrap gap-2">
            {palette.map((color) => {
              const isSelected = selectedColorId === color.id;
              return (
                <Tooltip key={color.id}>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => onColorSelect(color.id)}
                      className={cn(
                        "h-8 w-8 rounded-full border-2 transition-all",
                        "hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        isSelected
                          ? "border-foreground ring-2 ring-primary scale-110"
                          : "border-muted"
                      )}
                      style={{ backgroundColor: color.hex }}
                      aria-label={color.name}
                      aria-pressed={isSelected}
                    />
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-xs font-medium">{color.name}</p>
                    <p className="text-[10px] text-muted-foreground uppercase">
                      {color.hex}
                    </p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        </TooltipProvider>
      </Card>
    </div>
  );
}
