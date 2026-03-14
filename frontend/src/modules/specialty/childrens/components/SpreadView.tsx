"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ZoomIn,
  ZoomOut,
  Ruler,
  Eye,
  EyeOff,
} from "lucide-react";
import type { LayoutType } from "./LayoutSelector";
import type { PageData } from "./PageThumbnailStrip";

// ─── Constants ──────────────────────────────────────────────────────────────

const ZOOM_LEVELS = [50, 75, 100, 125, 150] as const;
type ZoomLevel = (typeof ZOOM_LEVELS)[number];

interface GuideOverlays {
  bleed: boolean;
  trim: boolean;
  safeZone: boolean;
  gutter: boolean;
}

interface SpreadViewProps {
  leftPage: PageData | null;
  rightPage: PageData | null;
  zoom: ZoomLevel;
  onZoomChange: (zoom: ZoomLevel) => void;
  guidesVisible: boolean;
  onGuidesToggle: () => void;
}

// ─── Guide overlay component ───────────────────────────────────────────────

function GuideOverlay({
  guides,
  isLeftPage,
}: {
  guides: GuideOverlays;
  isLeftPage: boolean;
}) {
  return (
    <div className="pointer-events-none absolute inset-0">
      {/* Bleed zone - red, outermost */}
      {guides.bleed && (
        <div
          className="absolute inset-0 border-2 border-red-500/50"
          aria-label="Bleed zone"
        >
          <span className="absolute left-1 top-0.5 text-[8px] font-medium text-red-500/70">
            Bleed
          </span>
        </div>
      )}

      {/* Trim line - blue, inside bleed */}
      {guides.trim && (
        <div
          className="absolute inset-[6px] border-2 border-dashed border-blue-500/50"
          aria-label="Trim line"
        >
          <span className="absolute right-1 top-0.5 text-[8px] font-medium text-blue-500/70">
            Trim
          </span>
        </div>
      )}

      {/* Safe zone - green, inside trim */}
      {guides.safeZone && (
        <div
          className="absolute inset-[18px] border-2 border-green-500/40"
          aria-label="Safe zone"
        >
          <span className="absolute left-1 bottom-0.5 text-[8px] font-medium text-green-500/70">
            Safe
          </span>
        </div>
      )}

      {/* Gutter - yellow, spine side only */}
      {guides.gutter && (
        <div
          className={cn(
            "absolute bottom-0 top-0 w-[14px] border-2 border-yellow-500/50 bg-yellow-500/10",
            isLeftPage ? "right-0" : "left-0"
          )}
          aria-label="Gutter zone"
        >
          <span
            className={cn(
              "absolute top-1 text-[7px] font-medium text-yellow-600/70",
              isLeftPage ? "right-0.5" : "left-0.5"
            )}
          >
            G
          </span>
        </div>
      )}
    </div>
  );
}

// ─── Layout renderer for a single page ──────────────────────────────────────

function PageLayoutRenderer({
  page,
  isLeftPage,
  guides,
  showGuides,
}: {
  page: PageData | null;
  isLeftPage: boolean;
  guides: GuideOverlays;
  showGuides: boolean;
}) {
  if (!page) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-muted/20">
        <span className="text-sm text-muted-foreground">No page</span>
      </div>
    );
  }

  const imageZone = (className?: string) => (
    <div
      className={cn(
        "relative flex items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-50 to-indigo-100 transition-colors",
        className
      )}
    >
      {page.illustrationUrl ? (
        <img
          src={page.illustrationUrl}
          alt={`Illustration for page ${page.pageNumber}`}
          className="h-full w-full object-cover"
        />
      ) : (
        <div className="flex flex-col items-center gap-1 text-indigo-300">
          <div className="h-8 w-8 rounded border-2 border-dashed border-current" />
          <span className="text-[10px]">Image</span>
        </div>
      )}
    </div>
  );

  const textZone = (className?: string) => (
    <div
      className={cn(
        "flex items-center justify-center p-3 transition-colors",
        className
      )}
    >
      {page.textContent ? (
        <p className="text-center text-xs leading-relaxed text-foreground/80">
          {page.textContent}
        </p>
      ) : (
        <div className="flex flex-col items-center gap-0.5 text-muted-foreground/40">
          <div className="h-1 w-12 rounded-full bg-current" />
          <div className="h-1 w-9 rounded-full bg-current" />
          <div className="h-1 w-10 rounded-full bg-current" />
        </div>
      )}
    </div>
  );

  const renderLayout = (layout: LayoutType) => {
    switch (layout) {
      case "full-bleed":
        return (
          <div className="relative h-full w-full">
            {imageZone("absolute inset-0")}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/30 to-transparent p-4">
              {textZone()}
            </div>
          </div>
        );
      case "top-image-bottom-text":
        return (
          <div className="grid h-full w-full grid-rows-[6fr_4fr]">
            {imageZone()}
            {textZone("bg-white")}
          </div>
        );
      case "bottom-image-top-text":
        return (
          <div className="grid h-full w-full grid-rows-[4fr_6fr]">
            {textZone("bg-white")}
            {imageZone()}
          </div>
        );
      case "left-image-right-text":
        return (
          <div className="grid h-full w-full grid-cols-2">
            {imageZone()}
            {textZone("bg-white")}
          </div>
        );
      case "right-image-left-text":
        return (
          <div className="grid h-full w-full grid-cols-2">
            {textZone("bg-white")}
            {imageZone()}
          </div>
        );
      case "text-only":
        return (
          <div className="flex h-full w-full items-center justify-center bg-white p-6">
            {textZone()}
          </div>
        );
      case "full-bleed-no-text":
        return imageZone("h-full w-full");
      default:
        return null;
    }
  };

  return (
    <div className="relative h-full w-full overflow-hidden">
      {renderLayout(page.layout)}
      {showGuides && <GuideOverlay guides={guides} isLeftPage={isLeftPage} />}
      {/* Page number */}
      <span
        className={cn(
          "absolute bottom-1 text-[9px] font-medium text-muted-foreground/60",
          isLeftPage ? "left-2" : "right-2"
        )}
      >
        {page.pageNumber}
      </span>
    </div>
  );
}

// ─── SpreadView Component ───────────────────────────────────────────────────

export function SpreadView({
  leftPage,
  rightPage,
  zoom,
  onZoomChange,
  guidesVisible,
  onGuidesToggle,
}: SpreadViewProps) {
  const [guides, setGuides] = React.useState<GuideOverlays>({
    bleed: true,
    trim: true,
    safeZone: true,
    gutter: true,
  });

  const zoomIndex = ZOOM_LEVELS.indexOf(zoom);

  const handleZoomIn = React.useCallback(() => {
    if (zoomIndex < ZOOM_LEVELS.length - 1) {
      onZoomChange(ZOOM_LEVELS[zoomIndex + 1]);
    }
  }, [zoomIndex, onZoomChange]);

  const handleZoomOut = React.useCallback(() => {
    if (zoomIndex > 0) {
      onZoomChange(ZOOM_LEVELS[zoomIndex - 1]);
    }
  }, [zoomIndex, onZoomChange]);

  const toggleGuideLayer = React.useCallback(
    (layer: keyof GuideOverlays) => {
      setGuides((prev) => ({ ...prev, [layer]: !prev[layer] }));
    },
    []
  );

  const scaleFactor = zoom / 100;

  return (
    <div className="flex h-full flex-col bg-muted/10">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b bg-background px-3 py-1.5">
        {/* Zoom controls */}
        <div className="flex items-center gap-1">
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleZoomOut}
                  disabled={zoomIndex === 0}
                  aria-label="Zoom out"
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Zoom out</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <div className="flex items-center gap-0.5">
            {ZOOM_LEVELS.map((level) => (
              <Button
                key={level}
                variant={zoom === level ? "secondary" : "ghost"}
                size="sm"
                className={cn(
                  "h-7 px-2 text-xs",
                  zoom === level && "font-semibold"
                )}
                onClick={() => onZoomChange(level)}
              >
                {level}%
              </Button>
            ))}
          </div>

          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleZoomIn}
                  disabled={zoomIndex === ZOOM_LEVELS.length - 1}
                  aria-label="Zoom in"
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Zoom in</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Guide controls */}
        <div className="flex items-center gap-1.5">
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={guidesVisible ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 gap-1 px-2 text-xs"
                  onClick={onGuidesToggle}
                >
                  {guidesVisible ? (
                    <Eye className="h-3 w-3" />
                  ) : (
                    <EyeOff className="h-3 w-3" />
                  )}
                  Guides
                </Button>
              </TooltipTrigger>
              <TooltipContent>Toggle guide overlays</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {guidesVisible && (
            <div className="flex items-center gap-1">
              {(
                [
                  { key: "bleed", color: "bg-red-500", label: "Bleed" },
                  { key: "trim", color: "bg-blue-500", label: "Trim" },
                  { key: "safeZone", color: "bg-green-500", label: "Safe" },
                  { key: "gutter", color: "bg-yellow-500", label: "Gutter" },
                ] as const
              ).map(({ key, color, label }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggleGuideLayer(key)}
                  className={cn(
                    "flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium transition-all",
                    guides[key]
                      ? "bg-muted text-foreground"
                      : "text-muted-foreground/50 line-through"
                  )}
                  aria-label={`Toggle ${label} guide`}
                  aria-pressed={guides[key]}
                >
                  <span
                    className={cn(
                      "inline-block h-2 w-2 rounded-full transition-opacity",
                      color,
                      !guides[key] && "opacity-30"
                    )}
                  />
                  {label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Spread canvas area */}
      <div className="flex flex-1 items-center justify-center overflow-auto p-6">
        <div
          className="transition-transform duration-200 ease-out"
          style={{ transform: `scale(${scaleFactor})` }}
        >
          <div className="flex shadow-2xl">
            {/* Left page */}
            <div
              className="relative h-[500px] w-[375px] overflow-hidden border border-r-0 bg-white"
              aria-label={
                leftPage
                  ? `Left page ${leftPage.pageNumber}`
                  : "Left page (empty)"
              }
            >
              <PageLayoutRenderer
                page={leftPage}
                isLeftPage={true}
                guides={guides}
                showGuides={guidesVisible}
              />
            </div>

            {/* Spine / gutter line */}
            <div className="w-px bg-muted-foreground/20" />

            {/* Right page */}
            <div
              className="relative h-[500px] w-[375px] overflow-hidden border border-l-0 bg-white"
              aria-label={
                rightPage
                  ? `Right page ${rightPage.pageNumber}`
                  : "Right page (empty)"
              }
            >
              <PageLayoutRenderer
                page={rightPage}
                isLeftPage={false}
                guides={guides}
                showGuides={guidesVisible}
              />
            </div>
          </div>

          {/* Spread label */}
          <div className="mt-2 text-center">
            <Badge variant="secondary" className="text-[10px]">
              <Ruler className="mr-1 h-2.5 w-2.5" />
              {leftPage ? `p${leftPage.pageNumber}` : "--"}
              {" / "}
              {rightPage ? `p${rightPage.pageNumber}` : "--"}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
}

export { ZOOM_LEVELS };
export type { ZoomLevel, GuideOverlays };
