"use client";

import {
  Type,
  Image,
  Square,
  Circle,
  Undo,
  Redo,
  Trash2,
  Copy,
  AlignLeft,
  AlignCenter,
  AlignRight,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

interface EditorToolbarProps {
  onAddText?: () => void;
  onAddImage?: () => void;
  onAddShape?: (shape: "rectangle" | "circle") => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onAlign?: (alignment: "left" | "center" | "right") => void;
  onZoom?: (direction: "in" | "out") => void;
  canUndo?: boolean;
  canRedo?: boolean;
  hasSelection?: boolean;
}

export function EditorToolbar({
  onAddText,
  onAddImage,
  onAddShape,
  onUndo,
  onRedo,
  onDelete,
  onDuplicate,
  onAlign,
  onZoom,
  canUndo = false,
  canRedo = false,
  hasSelection = false,
}: EditorToolbarProps) {
  return (
    <div className="flex items-center gap-1 p-2 bg-card border rounded-lg">
      {/* Add tools */}
      <div className="flex items-center gap-1 pr-2 border-r">
        <button
          onClick={onAddText}
          className="p-2 rounded hover:bg-accent transition-colors"
          title="Add Text"
          aria-label="Add text"
        >
          <Type className="h-4 w-4" />
        </button>
        <button
          onClick={onAddImage}
          className="p-2 rounded hover:bg-accent transition-colors"
          title="Add Image"
          aria-label="Add image"
        >
          <Image className="h-4 w-4" />
        </button>
        <div className="relative group">
          <button
            className="p-2 rounded hover:bg-accent transition-colors"
            title="Add Shape"
            aria-label="Add shape"
          >
            <Square className="h-4 w-4" />
          </button>
          <div className="absolute top-full left-0 mt-1 hidden group-hover:block bg-card border rounded-lg shadow-lg z-10">
            <button
              onClick={() => onAddShape?.("rectangle")}
              className="flex items-center gap-2 px-3 py-2 hover:bg-accent w-full text-left text-sm"
            >
              <Square className="h-4 w-4" />
              Rectangle
            </button>
            <button
              onClick={() => onAddShape?.("circle")}
              className="flex items-center gap-2 px-3 py-2 hover:bg-accent w-full text-left text-sm"
            >
              <Circle className="h-4 w-4" />
              Circle
            </button>
          </div>
        </div>
      </div>

      {/* History */}
      <div className="flex items-center gap-1 pr-2 border-r">
        <button
          onClick={onUndo}
          disabled={!canUndo}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Undo"
          aria-label="Undo"
        >
          <Undo className="h-4 w-4" />
        </button>
        <button
          onClick={onRedo}
          disabled={!canRedo}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Redo"
          aria-label="Redo"
        >
          <Redo className="h-4 w-4" />
        </button>
      </div>

      {/* Object actions */}
      <div className="flex items-center gap-1 pr-2 border-r">
        <button
          onClick={onDuplicate}
          disabled={!hasSelection}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Duplicate"
          aria-label="Duplicate selected object"
        >
          <Copy className="h-4 w-4" />
        </button>
        <button
          onClick={onDelete}
          disabled={!hasSelection}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-destructive"
          title="Delete"
          aria-label="Delete selected object"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {/* Alignment */}
      <div className="flex items-center gap-1 pr-2 border-r">
        <button
          onClick={() => onAlign?.("left")}
          disabled={!hasSelection}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Align Left"
          aria-label="Align left"
        >
          <AlignLeft className="h-4 w-4" />
        </button>
        <button
          onClick={() => onAlign?.("center")}
          disabled={!hasSelection}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Align Center"
          aria-label="Align center"
        >
          <AlignCenter className="h-4 w-4" />
        </button>
        <button
          onClick={() => onAlign?.("right")}
          disabled={!hasSelection}
          className="p-2 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Align Right"
          aria-label="Align right"
        >
          <AlignRight className="h-4 w-4" />
        </button>
      </div>

      {/* Zoom */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => onZoom?.("out")}
          className="p-2 rounded hover:bg-accent transition-colors"
          title="Zoom Out"
          aria-label="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={() => onZoom?.("in")}
          className="p-2 rounded hover:bg-accent transition-colors"
          title="Zoom In"
          aria-label="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
