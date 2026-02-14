"use client";

import { useRef, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

export interface EditorObject {
  id: string;
  type: "text" | "image" | "shape";
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  opacity: number;
  locked: boolean;
  visible: boolean;
  zIndex: number;
  properties: Record<string, unknown>;
}

export interface EditorState {
  objects: EditorObject[];
  background: {
    type: "color" | "gradient" | "image";
    value: string;
  };
  dimensions: {
    width: number;
    height: number;
  };
}

interface CoverEditorProps {
  initialState?: EditorState;
  selectedObjectId?: string | null;
  onSelectionChange?: (objectId: string | null) => void;
  onStateChange?: (state: EditorState) => void;
  className?: string;
}

export function CoverEditor({
  initialState,
  selectedObjectId,
  onSelectionChange,
  onStateChange,
  className = "",
}: CoverEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editorState, setEditorState] = useState<EditorState>(
    initialState || {
      objects: [],
      background: { type: "color", value: "#ffffff" },
      dimensions: { width: 1600, height: 2400 }, // Standard 6x9 book cover at 300 DPI
    }
  );

  // Initialize canvas
  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas dimensions
    canvas.width = editorState.dimensions.width;
    canvas.height = editorState.dimensions.height;

    // Draw background
    if (editorState.background.type === "color") {
      ctx.fillStyle = editorState.background.value;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Draw objects (simplified for now)
    editorState.objects
      .sort((a, b) => a.zIndex - b.zIndex)
      .forEach((obj) => {
        if (!obj.visible) return;

        ctx.save();
        ctx.globalAlpha = obj.opacity;

        // Apply transformations
        ctx.translate(obj.x + obj.width / 2, obj.y + obj.height / 2);
        ctx.rotate((obj.rotation * Math.PI) / 180);
        ctx.translate(-(obj.x + obj.width / 2), -(obj.y + obj.height / 2));

        // Draw based on type
        if (obj.type === "shape") {
          ctx.fillStyle = (obj.properties.fill as string) || "#000000";
          ctx.fillRect(obj.x, obj.y, obj.width, obj.height);
        } else if (obj.type === "text") {
          ctx.font = `${obj.properties.fontSize || 24}px ${obj.properties.fontFamily || "Arial"}`;
          ctx.fillStyle = (obj.properties.fill as string) || "#000000";
          ctx.fillText(
            (obj.properties.text as string) || "",
            obj.x,
            obj.y + (obj.properties.fontSize as number || 24)
          );
        }

        // Highlight selected object
        if (obj.id === selectedObjectId) {
          ctx.strokeStyle = "#3b82f6";
          ctx.lineWidth = 2;
          ctx.strokeRect(obj.x - 2, obj.y - 2, obj.width + 4, obj.height + 4);
        }

        ctx.restore();
      });

    setIsLoading(false);
  }, [editorState, selectedObjectId]);

  // Handle canvas click for selection
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !containerRef.current) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    // Find clicked object (reverse order to check top objects first)
    const clickedObject = [...editorState.objects]
      .reverse()
      .find((obj) => {
        return (
          obj.visible &&
          !obj.locked &&
          x >= obj.x &&
          x <= obj.x + obj.width &&
          y >= obj.y &&
          y <= obj.y + obj.height
        );
      });

    onSelectionChange?.(clickedObject?.id || null);
  };

  // Update state and notify parent
  const updateState = (newState: EditorState) => {
    setEditorState(newState);
    onStateChange?.(newState);
  };

  return (
    <div
      ref={containerRef}
      className={`relative bg-muted rounded-lg overflow-hidden ${className}`}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}
      <div className="flex items-center justify-center p-8">
        <div className="relative shadow-2xl">
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            className="max-w-full h-auto cursor-crosshair"
            style={{ maxHeight: "70vh" }}
          />
        </div>
      </div>
    </div>
  );
}
