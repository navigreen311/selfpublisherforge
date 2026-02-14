"use client";

import { Type, Image, Square, Minus, ZoomIn, ZoomOut, Undo2, Redo2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EditorToolbarProps {
  onAddText?: () => void;
  onAddImage?: () => void;
  onAddShape?: () => void;
  onAddLine?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  hasSelection?: boolean;
}

export function EditorToolbar({
  onAddText,
  onAddImage,
  onAddShape,
  onAddLine,
  onZoomIn,
  onZoomOut,
  onUndo,
  onRedo,
  hasSelection = false,
}: EditorToolbarProps) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      <div className="flex items-center gap-1 border-r pr-2 mr-2">
        <Button variant="ghost" size="sm" onClick={onAddText} title="Add Text">
          <Type className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onAddImage} title="Add Image">
          <Image className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onAddShape} title="Add Shape">
          <Square className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onAddLine} title="Add Line">
          <Minus className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center gap-1 border-r pr-2 mr-2">
        <Button variant="ghost" size="sm" onClick={onZoomOut} title="Zoom Out">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onZoomIn} title="Zoom In">
          <ZoomIn className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={onUndo} title="Undo">
          <Undo2 className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onRedo} title="Redo">
          <Redo2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
