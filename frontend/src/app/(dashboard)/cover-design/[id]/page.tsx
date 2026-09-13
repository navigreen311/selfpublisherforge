"use client";

import { useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Save, Download, MoreVertical, Loader2 } from "lucide-react";
import { CoverEditor, EditorState, EditorObject } from "@/modules/cover-design/components/CoverEditor";
import { EditorToolbar } from "@/modules/cover-design/components/EditorToolbar";
import { PropertiesPanel } from "@/modules/cover-design/components/PropertiesPanel";
import { LayersPanel } from "@/modules/cover-design/components/LayersPanel";
import { useCover } from "@/modules/cover-design/hooks";
import { Skeleton } from "@/components/ui/skeleton";

export default function CoverDetailPage() {
  const router = useRouter();
  const params = useParams();
  const coverId = params?.id as string;

  const { data: cover, isPending, error } = useCover(coverId);

  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);
  const [editorState, setEditorState] = useState<EditorState>({
    objects: [],
    background: { type: "color", value: "#ffffff" },
    dimensions: { width: 1600, height: 2400 },
  });
  const [isSaving, setIsSaving] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [coverName, setCoverName] = useState(cover?.title || "Untitled");
  const [isEditingName, setIsEditingName] = useState(false);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log("Saving:", editorState);
    } finally {
      setIsSaving(false);
    }
  }, [editorState]);

  const handleExport = useCallback((format: string) => {
    setExportMenuOpen(false);
    console.log("Exporting:", format);
  }, []);

  const handleAddText = useCallback(() => {
    const newObject: EditorObject = {
      id: `text-${Date.now()}`,
      type: "text",
      x: 100,
      y: 100,
      width: 300,
      height: 50,
      rotation: 0,
      opacity: 1,
      locked: false,
      visible: true,
      zIndex: editorState.objects.length,
      properties: { text: "New Text", fontSize: 32, fontFamily: "Arial", fill: "#000000" },
    };
    setEditorState((prev) => ({ ...prev, objects: [...prev.objects, newObject] }));
    setSelectedObjectId(newObject.id);
  }, [editorState.objects.length]);

  const handleUpdateObject = useCallback((objectId: string, properties: Partial<EditorObject>) => {
    setEditorState((prev) => ({
      ...prev,
      objects: prev.objects.map((obj) => (obj.id === objectId ? { ...obj, ...properties } : obj)),
    }));
  }, []);

  const selectedObject = editorState.objects.find((obj) => obj.id === selectedObjectId) || null;

  if (isPending) {
    return (
      <div className="h-screen flex flex-col">
        <div className="p-4 border-b"><Skeleton className="h-10 w-64" /></div>
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !cover) {
    return (
      <div className="h-screen flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <p>Cover not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b bg-card">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-accent rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold">Cover Editor: &quot;{coverName}&quot;</h1>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg">
            <Save className="h-4 w-4" /> Save
          </button>
          <button onClick={() => setExportMenuOpen(!exportMenuOpen)} className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg">
            <Download className="h-4 w-4" /> Export
          </button>
        </div>
      </div>

      <div className="px-4 py-2 border-b">
        <EditorToolbar onAddText={handleAddText} hasSelection={selectedObjectId !== null} />
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-auto">
          <CoverEditor
            initialState={editorState}
            selectedObjectId={selectedObjectId}
            onSelectionChange={setSelectedObjectId}
            onStateChange={setEditorState}
            className="h-full"
          />
        </div>
        <PropertiesPanel selectedObject={selectedObject} onUpdate={handleUpdateObject} />
      </div>

      <LayersPanel
        objects={editorState.objects}
        selectedObjectId={selectedObjectId}
        onSelect={setSelectedObjectId}
        onUpdate={handleUpdateObject}
      />
    </div>
  );
}
