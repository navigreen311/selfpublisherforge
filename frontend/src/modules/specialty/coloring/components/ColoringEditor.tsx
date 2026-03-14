"use client";

import { useState, useCallback, useEffect } from "react";
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
  ChevronDown,
  Frame,
  SlidersHorizontal,
  Type,
  Gauge,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import type { ColoringPage } from "../hooks";

type CanvasTool = "brush" | "pen" | "eraser" | "fill" | "smooth" | "close_shape" | "normalize";

interface ToolDef { id: CanvasTool; label: string; icon: typeof Brush; description: string; }

const CANVAS_TOOLS: ToolDef[] = [
  {
    id: "brush",
    label: "Brush",
    icon: Brush,
    description: "Paint white to cover marks",
  },
  {
    id: "pen",
    label: "Pen",
    icon: Pen,
    description: "Draw black to fix broken lines",
  },
  {
    id: "eraser",
    label: "Eraser",
    icon: Eraser,
    description: "Erase strokes",
  },
  {
    id: "fill",
    label: "Fill",
    icon: PaintBucket,
    description: "Fill area with white",
  },
  {
    id: "smooth",
    label: "Smooth Lines",
    icon: Spline,
    description: "Smooth jagged lines",
  },
  {
    id: "close_shape",
    label: "Close Shape",
    icon: Circle,
    description: "Connect open endpoints",
  },
  {
    id: "normalize",
    label: "Normalize Stroke",
    icon: Ruler,
    description: "Even out line thickness",
  },
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

const BORDER_STYLES = [
  { value: "none", label: "No Border" },
  { value: "simple", label: "Simple Line" },
  { value: "decorative", label: "Decorative" },
  { value: "themed", label: "Themed Frame" },
  { value: "rounded", label: "Rounded Corners" },
] as const;

const DIFFICULTY_LABELS = ["Very Easy", "Easy", "Medium", "Hard", "Very Hard"];

// ─── Component ────────────────────────────────────────────────────────────────

export interface ColoringEditorProps {
  pages: ColoringPage[];
  onPageAction: (pageId: string, action: PageAction) => void;
}

export function ColoringEditor({ pages, onPageAction }: ColoringEditorProps) {
  const [selectedPageId, setSelectedPageId] = useState<string | null>(
    pages[0]?.id ?? null,
  );
  const [activeTool, setActiveTool] = useState<CanvasTool>("pen");
  const [lineWeight, setLineWeight] = useState([3]);
  const [zoom, setZoom] = useState([100]);
  const [undoStack] = useState<number>(0);
  const [redoStack] = useState<number>(0);
  const [illustrationPrompt, setIllustrationPrompt] = useState("");
  const [borderStyle, setBorderStyle] = useState("none");
  const [difficulty, setDifficulty] = useState([3]);
  const [caption, setCaption] = useState("");
  const [promptOpen, setPromptOpen] = useState(true);
  const [pipelineOpen, setPipelineOpen] = useState(true);
  const [postProcessOpen, setPostProcessOpen] = useState(true);
  const [simulationOpen, setSimulationOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(true);

  // Right panel state
  const [illustrationPrompt, setIllustrationPrompt] = useState("");
  const [borderStyle, setBorderStyle] = useState("none");
  const [difficulty, setDifficulty] = useState([3]);
  const [caption, setCaption] = useState("");

  // Collapsible sections
  const [promptOpen, setPromptOpen] = useState(true);
  const [pipelineOpen, setPipelineOpen] = useState(true);
  const [postProcessOpen, setPostProcessOpen] = useState(true);
  const [simulationOpen, setSimulationOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(true);

  const selectedPage = pages.find((p) => p.id === selectedPageId) ?? null;

  const handlePageSelect = useCallback((page: ColoringPage) => {
    setSelectedPageId(page.id);
    setIllustrationPrompt(page.illustration_prompt ?? "");
    setDifficulty([page.complexity_score ?? 3]);
  }, []);

  // Sync prompt on initial mount
  useEffect(() => {
    if (selectedPage && !illustrationPrompt && selectedPage.illustration_prompt) {
      setIllustrationPrompt(selectedPage.illustration_prompt);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPage?.id]);

  return (
    <div className="flex h-[calc(100vh-280px)] min-h-[600px] border rounded-lg overflow-hidden bg-background">
      {/* ─── Left Panel: Page Thumbnails ─────────────────────────────── */}
      <div className="w-48 border-r bg-muted/20 flex flex-col">
        <div className="px-3 py-2 border-b">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Pages ({pages.length})
          </h3>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {pages.map((page) => {
              const isSelected = page.id === selectedPageId;
              return (
                <button
                  key={page.id}
                  type="button"
                  className={cn(
                    "w-full rounded-md overflow-hidden border-2 transition-all text-left",
                    "hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    isSelected
                      ? "border-primary ring-1 ring-primary/30"
                      : "border-transparent",
                  )}
                  onClick={() => handlePageSelect(page)}
                >
                  <div className="aspect-[3/4] bg-white flex items-center justify-center relative">
                    {page.illustration_url ? (
                      <img
                        src={page.cleaned_url ?? page.illustration_url}
                        alt={`Page ${page.page_number}`}
                        className="w-full h-full object-contain"
                        draggable={false}
                      />
                    ) : (
                      <ImageIcon className="h-6 w-6 text-muted-foreground/30" />
                    )}
                  </div>
                  <div className="flex items-center justify-between px-2 py-1 bg-muted/40">
                    <span className="text-[11px] font-medium">
                      P{page.page_number}
                    </span>
                    <Badge
                      variant="secondary"
                      className="text-[9px] h-4 capitalize px-1"
                    >
                      {page.status}
                    </Badge>
                  </div>
                </button>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* ─── Center: Page Preview ────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Canvas Toolbar */}
        <div className="flex items-center gap-1 px-3 py-1.5 border-b bg-muted/20 flex-wrap">
          {CANVAS_TOOLS.map((tool) => (
            <Tooltip key={tool.id}>
              <TooltipTrigger asChild>
                <Button
                  variant={activeTool === tool.id ? "default" : "ghost"}
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setActiveTool(tool.id)}
                >
                  <tool.icon className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-medium">{tool.label}</p>
                <p className="text-xs text-muted-foreground">
                  {tool.description}
                </p>
              </TooltipContent>
            </Tooltip>
          ))}

          <Separator orientation="vertical" className="h-6 mx-1" />

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-muted-foreground">Wt</span>
            <Slider
              min={1}
              max={10}
              step={1}
              value={lineWeight}
              onValueChange={setLineWeight}
              className="w-16"
            />
            <span className="text-[10px] text-muted-foreground w-4">
              {lineWeight[0]}
            </span>
          </div>

          <Separator orientation="vertical" className="h-6 mx-1" />

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                disabled={undoStack === 0}
              >
                <Undo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Undo</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                disabled={redoStack === 0}
              >
                <Redo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Redo</TooltipContent>
          </Tooltip>

          <Separator orientation="vertical" className="h-6 mx-1" />

          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setZoom(([v]) => [Math.max(25, v - 25)])}
            disabled={zoom[0] <= 25}
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <Slider
            min={25}
            max={200}
            step={25}
            value={zoom}
            onValueChange={setZoom}
            className="w-24"
          />
          <span className="text-[10px] text-muted-foreground w-8 text-right">
            {zoom[0]}%
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setZoom(([v]) => [Math.min(200, v + 25)])}
            disabled={zoom[0] >= 200}
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 overflow-auto bg-[#f0f0f0] flex items-center justify-center p-4">
          {selectedPage ? (
            <div
              className="bg-white shadow-lg border"
              style={{
                width: `${(600 * zoom[0]) / 100}px`,
                height: `${(800 * zoom[0]) / 100}px`,
              }}
            >
              {selectedPage.illustration_url ? (
                <img
                  src={
                    selectedPage.cleaned_url ?? selectedPage.illustration_url
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
          ) : (
            <div className="text-center text-muted-foreground space-y-2">
              <ImageIcon className="h-16 w-16 mx-auto opacity-20" />
              <p className="text-sm">Select a page from the left panel</p>
            </div>
          )}
        </div>
      </div>

      {/* ─── Right Panel: Controls ───────────────────────────────────── */}
      <div className="w-80 border-l bg-muted/10 flex flex-col">
        <div className="px-3 py-2 border-b">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Page Controls
            {selectedPage && (
              <span className="ml-1 text-foreground">
                — P{selectedPage.page_number}
              </span>
            )}
          </h3>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-3 space-y-1">
            {/* ── Illustration Prompt ──────────────────────────────── */}
            <Collapsible open={promptOpen} onOpenChange={setPromptOpen}>
              <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
                <span className="flex items-center gap-2">
                  <Wand2 className="h-4 w-4" />
                  Illustration Prompt
                </span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    promptOpen && "rotate-180",
                  )}
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-3 pb-3">
                <Textarea
                  placeholder="Describe the illustration for this page..."
                  value={illustrationPrompt}
                  onChange={(e) => setIllustrationPrompt(e.target.value)}
                  rows={3}
                  className="text-sm resize-none"
                  disabled={!selectedPage}
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    className="flex-1 gap-1.5"
                    disabled={!selectedPage || !illustrationPrompt.trim()}
                    onClick={() =>
                      selectedPage &&
                      onPageAction(selectedPage.id, "generate")
                    }
                  >
                    <Wand2 className="h-3.5 w-3.5" />
                    Generate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    disabled={!selectedPage}
                    onClick={() =>
                      selectedPage && onPageAction(selectedPage.id, "upload")
                    }
                  >
                    <Upload className="h-3.5 w-3.5" />
                    Upload
                  </Button>
                </div>
              </CollapsibleContent>
            </Collapsible>

            <Separator />

            {/* ── Quality Pipeline ─────────────────────────────────── */}
            <Collapsible open={pipelineOpen} onOpenChange={setPipelineOpen}>
              <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
                <span className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4" />
                  Quality Pipeline
                </span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    pipelineOpen && "rotate-180",
                  )}
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-3 pb-3">
                {selectedPage ? (
                  <>
                    <div className="space-y-2">
                      {[
                        {
                          step: "Generated",
                          done:
                            selectedPage.status !== "pending" &&
                            selectedPage.status !== "generating",
                        },
                        {
                          step: "Lines Cleaned",
                          done:
                            selectedPage.status === "cleaned" ||
                            selectedPage.status === "approved",
                        },
                        {
                          step: "Vectorized",
                          done: !!selectedPage.vectorized_url,
                        },
                        {
                          step: "QA Passed",
                          done: selectedPage.status === "approved",
                        },
                      ].map(({ step, done }) => (
                        <div
                          key={step}
                          className="flex items-center gap-2 text-sm"
                        >
                          <div
                            className={cn(
                              "h-2 w-2 rounded-full",
                              done
                                ? "bg-green-500"
                                : "bg-muted-foreground/30",
                            )}
                          />
                          <span
                            className={cn(!done && "text-muted-foreground")}
                          >
                            {step}
                          </span>
                        </div>
                      ))}
                    </div>

                    {selectedPage.quality_score != null && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Quality</span>
                          <span className="font-medium">
                            {selectedPage.quality_score}/100
                          </span>
                        </div>
                        <Progress
                          value={selectedPage.quality_score}
                          className="h-2"
                        />
                      </div>
                    )}

                    {selectedPage.quality_issues &&
                      selectedPage.quality_issues.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-xs text-muted-foreground">
                            Issues:
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {selectedPage.quality_issues.map((issue, i) => (
                              <Badge
                                key={i}
                                variant="outline"
                                className="text-[10px]"
                              >
                                {issue}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full gap-1.5"
                      onClick={() =>
                        onPageAction(selectedPage.id, "quality_check")
                      }
                    >
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Run Quality Check
                    </Button>
                  </>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Select a page to view pipeline status.
                  </p>
                )}
              </CollapsibleContent>
            </Collapsible>

            <Separator />

            {/* ── Post-Processing Controls ─────────────────────────── */}
            <Collapsible
              open={postProcessOpen}
              onOpenChange={setPostProcessOpen}
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
                <span className="flex items-center gap-2">
                  <SlidersHorizontal className="h-4 w-4" />
                  Post-Processing
                </span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    postProcessOpen && "rotate-180",
                  )}
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-2 pb-3">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-start gap-2"
                  disabled={!selectedPage}
                  onClick={() =>
                    selectedPage &&
                    onPageAction(selectedPage.id, "clean_lines")
                  }
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Clean Lines
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-start gap-2"
                  disabled={!selectedPage}
                  onClick={() =>
                    selectedPage &&
                    onPageAction(selectedPage.id, "vectorize")
                  }
                >
                  <Spline className="h-3.5 w-3.5" />
                  Vectorize
                </Button>
              </CollapsibleContent>
            </Collapsible>

            <Separator />

            {/* ── Simulation Preview ───────────────────────────────── */}
            <Collapsible
              open={simulationOpen}
              onOpenChange={setSimulationOpen}
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
                <span className="flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Simulation Preview
                </span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    simulationOpen && "rotate-180",
                  )}
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-3 pb-3">
                {selectedPage?.illustration_url ? (
                  <>
                    <div className="aspect-[3/4] bg-white border rounded-md overflow-hidden">
                      <img
                        src={
                          selectedPage.cleaned_url ??
                          selectedPage.illustration_url
                        }
                        alt={`Simulation preview P${selectedPage.page_number}`}
                        className="w-full h-full object-contain opacity-80"
                        style={{ filter: "sepia(0.15) saturate(0.8)" }}
                        draggable={false}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground text-center">
                      Simulated coloring preview (marker style)
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full gap-1.5"
                      onClick={() =>
                        selectedPage &&
                        onPageAction(selectedPage.id, "simulate")
                      }
                    >
                      <Eye className="h-3.5 w-3.5" />
                      Open Full Simulation
                    </Button>
                  </>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Generate an illustration to preview simulation.
                  </p>
                )}
              </CollapsibleContent>
            </Collapsible>

            <Separator />

            {/* ── Border / Difficulty / Caption ────────────────────── */}
            <Collapsible open={settingsOpen} onOpenChange={setSettingsOpen}>
              <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
                <span className="flex items-center gap-2">
                  <Frame className="h-4 w-4" />
                  Page Settings
                </span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    settingsOpen && "rotate-180",
                  )}
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 pb-3">
                <div className="space-y-1.5">
                  <Label className="text-xs flex items-center gap-1.5">
                    <Frame className="h-3 w-3" />
                    Border Style
                  </Label>
                  <Select
                    value={borderStyle}
                    onValueChange={setBorderStyle}
                    disabled={!selectedPage}
                  >
                    <SelectTrigger className="h-8 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {BORDER_STYLES.map((b) => (
                        <SelectItem key={b.value} value={b.value}>
                          {b.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs flex items-center gap-1.5">
                    <Gauge className="h-3 w-3" />
                    Difficulty
                  </Label>
                  <Slider
                    min={1}
                    max={5}
                    step={1}
                    value={difficulty}
                    onValueChange={setDifficulty}
                    disabled={!selectedPage}
                  />
                  <p className="text-[10px] text-muted-foreground text-center">
                    {DIFFICULTY_LABELS[difficulty[0] - 1]}
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs flex items-center gap-1.5">
                    <Type className="h-3 w-3" />
                    Caption
                  </Label>
                  <Input
                    placeholder="Optional page caption..."
                    value={caption}
                    onChange={(e) => setCaption(e.target.value)}
                    className="h-8 text-sm"
                    disabled={!selectedPage}
                  />
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
