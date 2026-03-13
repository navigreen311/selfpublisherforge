"use client";

import React, { useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Paintbrush, Pen, Eraser, PaintBucket, Spline, Square, Ruler, Undo2, Redo2, ZoomIn, ZoomOut, Image } from "lucide-react";
import { useColoringEditorStore } from "../store";
import type { ColoringPage, EditorTool } from "../types";

const TOOLS: { tool: EditorTool; label: string; icon: React.ElementType; description: string }[] = [
  { tool: "brush", label: "Brush", icon: Paintbrush, description: "Paint white to cover marks" },
  { tool: "pen", label: "Pen", icon: Pen, description: "Draw black lines" },
  { tool: "eraser", label: "Eraser", icon: Eraser, description: "Erase content" },
  { tool: "fill", label: "Fill", icon: PaintBucket, description: "Fill area with white" },
  { tool: "smooth", label: "Smooth Lines", icon: Spline, description: "Smooth jagged lines" },
  { tool: "close_shape", label: "Close Shape", icon: Square, description: "Connect open endpoints" },
  { tool: "normalize_stroke", label: "Normalize", icon: Ruler, description: "Even out line thickness" },
];

export interface ColoringPageEditorProps { pages: ColoringPage[]; bookId: string; }

function ThumbnailStrip({ pages, selectedPageId, onSelectPage }: { pages: ColoringPage[]; selectedPageId: string | null; onSelectPage: (id: string) => void }) {
  return (<div className="w-24 border-r bg-muted/30 overflow-y-auto p-2 space-y-2 shrink-0">{pages.map((page) => (<button key={page.id} type="button" onClick={() => onSelectPage(page.id)} className={cn("w-full aspect-[3/4] rounded border overflow-hidden transition-all relative", selectedPageId === page.id ? "ring-2 ring-primary border-primary" : "hover:border-primary/40")}>{page.cleaned_url || page.illustration_url ? <img src={page.cleaned_url || page.illustration_url} alt={"Page " + page.page_number} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center bg-white"><Image className="h-4 w-4 text-muted-foreground/30" aria-hidden="true" /></div>}<span className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[9px] text-center py-0.5">{page.page_number}</span></button>))}</div>);
}

export function ColoringPageEditor({ pages, bookId }: ColoringPageEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { selectedPageId, selectPage, activeTool, setActiveTool, lineWeight, setLineWeight, zoomLevel, setZoomLevel, undoStack, redoStack, undo, redo } = useColoringEditorStore();
  const selectedPage = pages.find((p) => p.id === selectedPageId) ?? pages[0] ?? null;
  const handleZoomIn = useCallback(() => setZoomLevel(Math.min(200, zoomLevel + 25)), [zoomLevel, setZoomLevel]);
  const handleZoomOut = useCallback(() => setZoomLevel(Math.max(25, zoomLevel - 25)), [zoomLevel, setZoomLevel]);

  return (
    <div className="flex h-full bg-background">
      <ThumbnailStrip pages={pages.filter((p) => p.page_type === "coloring")} selectedPageId={selectedPage?.id ?? null} onSelectPage={selectPage} />
      <div className="flex-1 flex flex-col min-w-0">
        <div className="border-b px-3 py-2 flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1 border-r pr-2 mr-2">{TOOLS.map(({ tool, label, icon: Icon, description }) => (<Tooltip key={tool}><TooltipTrigger asChild><Button variant={activeTool === tool ? "default" : "ghost"} size="sm" className="h-8 w-8 p-0" onClick={() => setActiveTool(tool)} aria-label={label}><Icon className="h-4 w-4" /></Button></TooltipTrigger><TooltipContent><p className="font-medium">{label}</p><p className="text-xs text-muted-foreground">{description}</p></TooltipContent></Tooltip>))}</div>
          <div className="flex items-center gap-2 border-r pr-2 mr-2"><span className="text-xs text-muted-foreground whitespace-nowrap">Weight: {lineWeight}px</span><Slider min={1} max={8} step={0.5} value={[lineWeight]} onValueChange={([v]) => setLineWeight(v)} className="w-20" /></div>
          <div className="flex items-center gap-1 border-r pr-2 mr-2"><Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => undo()} disabled={undoStack.length === 0} aria-label="Undo"><Undo2 className="h-4 w-4" /></Button><Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => redo()} disabled={redoStack.length === 0} aria-label="Redo"><Redo2 className="h-4 w-4" /></Button></div>
          <div className="flex items-center gap-1"><Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={handleZoomOut} disabled={zoomLevel <= 25} aria-label="Zoom out"><ZoomOut className="h-4 w-4" /></Button><span className="text-xs text-muted-foreground min-w-[3rem] text-center">{zoomLevel}%</span><Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={handleZoomIn} disabled={zoomLevel >= 200} aria-label="Zoom in"><ZoomIn className="h-4 w-4" /></Button></div>
        </div>
        <div className="flex-1 overflow-auto flex items-center justify-center bg-muted/20 p-4">
          {selectedPage ? (<div className="relative bg-white shadow-lg border" style={{ width: (612 * zoomLevel) / 100 + "px", height: (792 * zoomLevel) / 100 + "px" }}>{selectedPage.illustration_url || selectedPage.cleaned_url ? <img src={selectedPage.cleaned_url || selectedPage.illustration_url} alt={"Page " + selectedPage.page_number} className="w-full h-full object-contain" /> : <div className="w-full h-full flex items-center justify-center"><div className="text-center text-muted-foreground"><Image className="h-12 w-12 mx-auto mb-2 opacity-30" aria-hidden="true" /><p className="text-sm">No illustration generated yet</p><p className="text-xs">Generate pages from the batch panel</p></div></div>}<canvas ref={canvasRef} className="absolute inset-0 w-full h-full cursor-crosshair" style={{ touchAction: "none" }} /></div>) : (<div className="text-center text-muted-foreground"><p className="text-sm">Select a page from the thumbnail strip</p></div>)}
        </div>
      </div>
    </div>
  );
}
