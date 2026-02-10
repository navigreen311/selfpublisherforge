"use client";

import { useState, useCallback, useMemo } from "react";
import { X, Upload, Link as LinkIcon, Loader2 } from "lucide-react";
import { useImportEntry } from "../hooks";

const ACCEPTED_EXTENSIONS = [".pdf", ".epub", ".txt", ".md", ".docx", ".html"];
const ACCEPTED_FORMATS_LABEL = "PDF, EPUB, TXT, MD, DOCX, or HTML";
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isValidUrl(value: string): boolean {
  return /^https?:\/\//i.test(value.trim());
}

function hasValidExtension(name: string): boolean {
  const lower = name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

interface ImportModalProps {
  open: boolean;
  onClose: () => void;
}

export function ImportModal({ open, onClose }: ImportModalProps) {
  const [tab, setTab] = useState<"url" | "file">("url");
  const [url, setUrl] = useState("");
  const [urlTouched, setUrlTouched] = useState(false);
  const [fileName, setFileName] = useState("");
  const [fileSize, setFileSize] = useState<number>(0);
  const [fileBase64, setFileBase64] = useState("");
  const [fileError, setFileError] = useState("");
  const [extractFacts, setExtractFacts] = useState(true);
  const importMutation = useImportEntry();

  const urlError = useMemo(() => {
    if (!urlTouched || url.trim() === "") return "";
    if (!isValidUrl(url)) return "URL must start with http:// or https://";
    return "";
  }, [url, urlTouched]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset previous state
    setFileError("");
    setFileName("");
    setFileSize(0);
    setFileBase64("");

    // Validate format
    if (!hasValidExtension(file.name)) {
      setFileError(
        `File must be ${ACCEPTED_FORMATS_LABEL} (max ${formatFileSize(MAX_FILE_SIZE_BYTES)})`
      );
      e.target.value = "";
      return;
    }

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setFileError(
        `File is too large (${formatFileSize(file.size)}). Maximum allowed size is ${formatFileSize(MAX_FILE_SIZE_BYTES)}.`
      );
      e.target.value = "";
      return;
    }

    setFileName(file.name);
    setFileSize(file.size);

    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(",")[1] || "";
      setFileBase64(base64);
    };
    reader.readAsDataURL(file);
  }, []);

  const isSubmitDisabled = useMemo(() => {
    if (importMutation.isPending) return true;
    if (tab === "url") {
      return !url.trim() || !isValidUrl(url);
    }
    // file tab
    return !fileName || !fileBase64 || !!fileError;
  }, [importMutation.isPending, tab, url, fileName, fileBase64, fileError]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (isSubmitDisabled) return;

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
      setUrlTouched(false);
      setFileName("");
      setFileSize(0);
      setFileBase64("");
      setFileError("");
    },
    [isSubmitDisabled, tab, url, fileName, fileBase64, extractFacts, importMutation, onClose]
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
              <label htmlFor="import-url" className="block text-sm font-medium mb-1">
                URL
              </label>
              <input
                id="import-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onBlur={() => setUrlTouched(true)}
                placeholder="https://example.com/article"
                className={`w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 ${
                  urlError ? "border-red-500" : ""
                }`}
                aria-invalid={urlError ? "true" : undefined}
                aria-describedby={urlError ? "url-error" : undefined}
                required
              />
              {urlError && (
                <p id="url-error" className="mt-1 text-xs text-red-500" role="alert">
                  {urlError}
                </p>
              )}
            </div>
          ) : (
            <div>
              <label htmlFor="import-file" className="block text-sm font-medium mb-1">
                File ({ACCEPTED_FORMATS_LABEL})
              </label>
              <input
                id="import-file"
                type="file"
                accept={ACCEPTED_EXTENSIONS.join(",")}
                onChange={handleFileChange}
                className={`w-full border rounded-lg px-3 py-2 text-sm bg-background file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-primary file:text-primary-foreground ${
                  fileError ? "border-red-500" : ""
                }`}
                aria-invalid={fileError ? "true" : undefined}
                aria-describedby={
                  fileError ? "file-error" : fileName ? "file-info" : "file-hint"
                }
                required
              />
              {fileError && (
                <p id="file-error" className="mt-1 text-xs text-red-500" role="alert">
                  {fileError}
                </p>
              )}
              {!fileError && fileName && (
                <p id="file-info" className="mt-1 text-xs text-muted-foreground">
                  Selected: {fileName} ({formatFileSize(fileSize)})
                </p>
              )}
              {!fileError && !fileName && (
                <p id="file-hint" className="mt-1 text-xs text-muted-foreground">
                  File must be {ACCEPTED_FORMATS_LABEL} (max {formatFileSize(MAX_FILE_SIZE_BYTES)})
                </p>
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
            disabled={isSubmitDisabled}
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
