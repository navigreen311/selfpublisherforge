"use client";

import { useState, useCallback } from "react";
import {
  Brush,
  Pen,
  Eraser,
  PaintBucket,
  Spline,
  Circle,
  Ruler,
  ZoomIn,
  ZoomOut,
  Undo2,
  Redo2,
  Wand2,
  Upload,
  Sparkles,
  ShieldCheck,
  Eye,
  ImageIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import type { ColoringPage } from "../hooks";

// ─── Types ────────────────────────────────────────────────────────────────────

type CanvasTool =
  | "brush"
  | "pen"
  | "eraser"
  | "fill"
  | "smooth"
  | "close_shape"
  | "normalize";

interface ToolDef {
  id: CanvasTool;
  label: string;
  icon: typeof Brush;
  description: string;
}

const CANVAS_TOOLS: ToolDef[] = [
  { id: "brush", label: "Brush", icon: Brush, description: "Paint white to cover marks" },
  { id: "pen", label: "Pen", icon: Pen, description: "Draw black to fix broken lines" },
  { id: "eraser", label: "Eraser", icon: Eraser, description: "Erase strokes" },
  { id: "fill", label: "Fill", icon: PaintBucket, description: "Fill area with white" },
  { id: "smooth", label: "Smooth Lines", icon: Spline, description: "Smooth jagged lines" },
  { id: "close_shape", label: "Close Shape", icon: Circle, description: "Connect open endpoints" },
  { id: "normalize", label: "Normalize Stroke", icon: Ruler, description: "Even out line thickness" },
];

const PAGE_ACTIONS = [
  { id: "generate", label: "Generate", icon: Wand2 },
  { id: "upload", label: "Upload", icon: Upload },
  { id: "clean_lines", label: "Clean Lines", icon: Sparkles },
  { id: "vectorize", label: "Vectorize", icon: Spline },
  { id: "quality_check", label: "Quality Check", icon: ShieldCheck },
  { id: "simulate", label: "Simulate", icon: Eye },
] as const;

type PageAction = (typeof PAGE_ACTIONS)[number]["id"];

// ─── Component ────────────────────────────────────────────────────────────────

export interface ColoringEditorProps {
  pages: ColoringPage[];
  onPageAction: (pageId: string, action: PageAction) => void;
}

export function ColoringEditor({ pages, onPageAction }: ColoringEditorProps) {
  const [selectedPage, setSelectedPage] = useState<ColoringPage | null>(null);
  const [activeTool, setActiveTool] = useState<CanvasTool>("pen");
  const [lineWeight, setLineWeight] = useState([3]);
  const [zoom, setZoom] = useState([100]);
  const [undoStack] = useState<number>(0);
  const [redoStack] = useState<number>(0);

  const handlePageClick = useCallback((page: ColoringPage) => {
    setSelectedPage(page);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedPage(null);
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Thumbnail Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {pages.map((page) => (
          <div
            key={page.id}
            className="group relative border rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
            onClick={() => handlePageClick(page)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") handlePageClick(page);
            }}
          >
            {/* Thumbnail */}
            <div className="aspect-[3/4] bg-white flex items-center justify-center">
              {page.illustration_url ? (
                <img
                  src={page.cleaned_url ?? page.illustration_url}
                  alt={`Page ${page.page_number}`}
                  className="w-full h-full object-contain"
                />
              ) : (
                <ImageIcon className="h-10 w-10 text-muted-foreground/30" />
              )}
            </div>

            {/* Page info overlay */}
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent p-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-white">
                  Page {page.page_number}
                </span>
                <Badge
                  variant="secondary"
                  className="text-[10px] h-5 capitalize"
                >
                  {page.status}
                </Badge>
              </div>
            </div>

            {/* Per-page toolbar on hover */}
            <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1">
              {PAGE_ACTIONS.map((action) => (
                <Tooltip key={action.id}>
                  <TooltipTrigger asChild>
                    <Button
                      variant="secondary"
                      size="icon"
                      className="h-7 w-7"
                      onClick={(e) => {
                        e.stopPropagation();
                        onPageAction(page.id, action.id);
                      }}
                    >
                      <action.icon className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="left">{action.label}</TooltipContent>
                </Tooltip>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Detail Modal / Panel */}
      <Dialog open={!!selectedPage} onOpenChange={(open) => !open && handleCloseDetail()}>
        <DialogContent className="max-w-5xl h-[85vh] flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-0">
            <DialogTitle>
              Page {selectedPage?.page_number} Editor
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-1 overflow-hidden">
            {/* Canvas Cleanup Toolbar (left) */}
            <div className="w-14 border-r bg-muted/30 flex flex-col items-center py-3 gap-1">
              {CANVAS_TOOLS.map((tool) => (
                <Tooltip key={tool.id}>
                  <TooltipTrigger asChild>
                    <Button
                      variant={activeTool === tool.id ? "default" : "ghost"}
                      size="icon"
                      className="h-9 w-9"
                      onClick={() => setActiveTool(tool.id)}
                    >
                      <tool.icon className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p className="font-medium">{tool.label}</p>
                    <p className="text-xs text-muted-foreground">
                      {tool.description}
                    </p>
                  </TooltipContent>
                </Tooltip>
              ))}

              <div className="border-t my-2 w-8" />

              {/* Line Weight */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="px-1 w-full">
                    <Slider
                      orientation="vertical"
                      min={1}
                      max={10}
                      step={1}
                      value={lineWeight}
                      onValueChange={setLineWeight}
                      className="h-20"
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  Line Weight: {lineWeight[0]}px
                </TooltipContent>
              </Tooltip>

              <div className="border-t my-2 w-8" />

              {/* Undo / Redo */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9"
                    disabled={undoStack === 0}
                  >
                    <Undo2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Undo</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9"
                    disabled={redoStack === 0}
                  >
                    <Redo2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Redo</TooltipContent>
              </Tooltip>
            </div>

            {/* Canvas Area */}
            <div className="flex-1 flex flex-col">
              {/* Zoom toolbar */}
              <div className="flex items-center gap-3 px-4 py-2 border-b bg-muted/20">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() =>
                    setZoom(([v]) => [Math.max(25, v - 25)])
                  }
                  disabled={zoom[0] <= 25}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Slider
                  min={25}
                  max={200}
                  step={25}
                  value={zoom}
                  onValueChange={setZoom}
                  className="w-40"
                />
                <span className="text-xs text-muted-foreground w-10 text-right">
                  {zoom[0]}%
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() =>
                    setZoom(([v]) => [Math.min(200, v + 25)])
                  }
                  disabled={zoom[0] >= 200}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>

                <div className="ml-auto flex items-center gap-1">
                  {PAGE_ACTIONS.map((action) => (
                    <Tooltip key={action.id}>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs gap-1.5"
                          onClick={() =>
                            selectedPage &&
                            onPageAction(selectedPage.id, action.id)
                          }
                        >
                          <action.icon className="h-3.5 w-3.5" />
                          {action.label}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>{action.label}</TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              </div>

              {/* Canvas */}
              <div className="flex-1 overflow-auto bg-[#f0f0f0] flex items-center justify-center p-4">
                <div
                  className="bg-white shadow-lg border"
                  style={{
                    width: `${(600 * zoom[0]) / 100}px`,
                    height: `${(800 * zoom[0]) / 100}px`,
                  }}
                >
                  {selectedPage?.illustration_url ? (
                    <img
                      src={
                        selectedPage.cleaned_url ??
                        selectedPage.illustration_url
                      }
                      alt={`Page ${selectedPage.page_number}`}
                      className="w-full h-full object-contain"
                      draggable={false}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                      <div className="text-center space-y-2">
                        <ImageIcon className="h-12 w-12 mx-auto opacity-30" />
                        <p className="text-sm">
                          No image yet. Generate or upload one.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
