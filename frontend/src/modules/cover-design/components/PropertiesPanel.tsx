"use client";

import { EditorObject } from "./CoverEditor";

interface PropertiesPanelProps {
  selectedObject: EditorObject | null;
  onUpdate?: (objectId: string, properties: Partial<EditorObject>) => void;
}

export function PropertiesPanel({ selectedObject, onUpdate }: PropertiesPanelProps) {
  if (!selectedObject) {
    return (
      <div className="w-80 p-6 border-l bg-card">
        <p className="text-sm text-muted-foreground text-center">
          Select an object to view properties
        </p>
      </div>
    );
  }

  return (
    <div className="w-80 p-6 border-l bg-card overflow-y-auto">
      <h3 className="text-lg font-semibold mb-4">Properties</h3>
      <div className="space-y-6">
        <div>
          <label className="text-xs font-medium text-muted-foreground uppercase">Type</label>
          <p className="text-sm capitalize mt-1">{selectedObject.type}</p>
        </div>
        <div>
          <label className="text-sm font-medium">Position</label>
          <p className="text-xs text-muted-foreground mt-1">
            X: {selectedObject.x}, Y: {selectedObject.y}
          </p>
        </div>
        <div>
          <label className="text-sm font-medium">Size</label>
          <p className="text-xs text-muted-foreground mt-1">
            W: {selectedObject.width}, H: {selectedObject.height}
          </p>
        </div>
        <div>
          <label className="text-sm font-medium">Opacity</label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={selectedObject.opacity}
            onChange={(e) => onUpdate?.(selectedObject.id, { opacity: parseFloat(e.target.value) })}
            className="w-full mt-1"
          />
          <p className="text-xs text-muted-foreground">{Math.round(selectedObject.opacity * 100)}%</p>
        </div>
        <div>
          <label className="text-sm font-medium">Rotation</label>
          <input
            type="number"
            value={selectedObject.rotation}
            onChange={(e) => onUpdate?.(selectedObject.id, { rotation: parseInt(e.target.value) || 0 })}
            className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
          />
        </div>
      </div>
    </div>
  );
}
