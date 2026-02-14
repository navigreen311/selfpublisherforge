"use client";

import { useState } from "react";
import { EditorObject } from "./CoverEditor";
import { Eye, EyeOff, Lock, Unlock, Type, Image, Square } from "lucide-react";

interface LayersPanelProps {
  objects: EditorObject[];
  selectedObjectId: string | null;
  onSelect?: (objectId: string | null) => void;
  onUpdate?: (objectId: string, properties: Partial<EditorObject>) => void;
}

export function LayersPanel({ objects, selectedObjectId, onSelect, onUpdate }: LayersPanelProps) {
  const [showLayers, setShowLayers] = useState(true);

  return (
    <div className="border-t bg-card">
      <div className="p-3 border-b">
        <button onClick={() => setShowLayers(!showLayers)} className="text-sm font-medium">
          Layers ({objects.length})
        </button>
      </div>
      {showLayers && (
        <div className="max-h-60 overflow-y-auto">
          {objects.length === 0 ? (
            <div className="p-6 text-center">
              <p className="text-sm text-muted-foreground">No layers yet</p>
            </div>
          ) : (
            <div className="divide-y">
              {objects.map((obj) => (
                <div
                  key={obj.id}
                  onClick={() => onSelect?.(obj.id)}
                  className={`flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-accent ${
                    obj.id === selectedObjectId ? "bg-primary/10" : ""
                  }`}
                >
                  <p className="text-sm flex-1">{obj.type}</p>
                  <button
                    onClick={(e) => { e.stopPropagation(); onUpdate?.(obj.id, { visible: !obj.visible }); }}
                    className="p-1"
                  >
                    {obj.visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
