"use client";

import { useState, useCallback } from "react";
import { X, Upload, Link as LinkIcon, Loader2 } from "lucide-react";
import { useImportEntry } from "../hooks";

interface ImportModalProps {
  open: boolean;
  onClose: () => void;
}

export function ImportModal({ open, onClose }: ImportModalProps) {
  const [tab, setTab] = useState<"url" | "file">("url");
  const [url, setUrl] = useState("");
  const [fileName, setFileName] = useState("");
  const [fileBase64, setFileBase64] = useState("");
  const [extractFacts, setExtractFacts] = useState(true);
  const importMutation = useImportEntry();

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);

    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(",")[1] || "";
      setFileBase64(base64);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (tab === "url" && url.trim()) {
        await importMutation.mutateAsync({
          url: url.trim(),
          extract_facts: extractFacts,
        });
      } else if (tab === "file" && fileName && fileBase64) {
        await importMutation.mutateAsync({
          file_name: fileName,
          file_content_base64: fileBase64,
          extract_facts: extractFacts,
        });
      }
      onClose();
      setUrl("");
      setFileName("");
      setFileBase64("");
    },
    [tab, url, fileName, fileBase64, extractFacts, importMutation, onClose]
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-background border rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
        >
          <X className="h-5 w-5" />
        </button>

        <h2 className="text-lg font-semibold mb-4">Import Research</h2>

        {/* Tab switcher */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setTab("url")}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              tab === "url"
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground"
            }`}
          >
            <LinkIcon className="h-4 w-4" /> From URL
          </button>
          <button
            onClick={() => setTab("file")}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              tab === "file"
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground"
            }`}
          >
            <Upload className="h-4 w-4" /> From File
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === "url" ? (
            <div>
              <label className="block text-sm font-medium mb-1">URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/article"
                className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                required
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-1">File (PDF, DOCX, TXT)</label>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="w-full border rounded-lg px-3 py-2 text-sm bg-background file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-primary file:text-primary-foreground"
                required
              />
              {fileName && (
                <p className="mt-1 text-xs text-muted-foreground">Selected: {fileName}</p>
              )}
            </div>
          )}

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="extract-facts"
              checked={extractFacts}
              onChange={(e) => setExtractFacts(e.target.checked)}
              className="h-4 w-4 rounded border"
            />
            <label htmlFor="extract-facts" className="text-sm">
              Extract key facts with AI
            </label>
          </div>

          <button
            type="submit"
            disabled={importMutation.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {importMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Importing...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" /> Import
              </>
            )}
          </button>

          {importMutation.isError && (
            <p className="text-sm text-red-500">Import failed. Please try again.</p>
          )}
        </form>
      </div>
    </div>
  );
}
