"use client";

import { useState, useCallback, useMemo, useRef, DragEvent } from "react";
import {
  Upload,
  Link as LinkIcon,
  ClipboardPaste,
  BookOpen,
  Loader2,
  FileText,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { useImportEntry, useCreateEntry } from "../hooks";
import { useBooks } from "@/modules/writing/hooks";
import { useChapters } from "@/modules/writing/hooks";

// ── Constants ──────────────────────────────────────────────────

const ACCEPTED_EXTENSIONS = [".pdf", ".epub", ".txt", ".md", ".docx"];
const ACCEPTED_FORMATS_LABEL = "DOCX, PDF, TXT, MD, EPUB";
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
const ACCEPTED_MIME_TYPES = [
  "application/pdf",
  "application/epub+zip",
  "text/plain",
  "text/markdown",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

type ImportTab = "file" | "url" | "clipboard" | "manuscript";

// ── Helpers ────────────────────────────────────────────────────

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

// ── Tab card config ────────────────────────────────────────────

const TAB_CARDS: {
  key: ImportTab;
  label: string;
  description: string;
  icon: typeof Upload;
}[] = [
  {
    key: "file",
    label: "Upload Files",
    description: ACCEPTED_FORMATS_LABEL,
    icon: Upload,
  },
  {
    key: "url",
    label: "Import from URL",
    description: "Paste any web link",
    icon: LinkIcon,
  },
  {
    key: "clipboard",
    label: "Paste Clipboard",
    description: "Paste text content",
    icon: ClipboardPaste,
  },
  {
    key: "manuscript",
    label: "From Manuscript",
    description: "Import a chapter",
    icon: BookOpen,
  },
];

// ── Props ──────────────────────────────────────────────────────

interface ImportModalProps {
  open: boolean;
  onClose: () => void;
}

// ── Component ──────────────────────────────────────────────────

export function ImportModal({ open, onClose }: ImportModalProps) {
  const [activeTab, setActiveTab] = useState<ImportTab | null>(null);

  // Shared mutations
  const importMutation = useImportEntry();
  const createMutation = useCreateEntry();

  const resetAndClose = useCallback(() => {
    setActiveTab(null);
    onClose();
  }, [onClose]);

  const handleSuccess = useCallback(
    (title: string) => {
      toast.success(`Imported "${title}"`);
      resetAndClose();
    },
    [resetAndClose]
  );

  return (
    <Dialog open={open} onOpenChange={(o) => !o && resetAndClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import Research</DialogTitle>
          <DialogDescription>
            Choose how you want to add content to your knowledge base.
          </DialogDescription>
        </DialogHeader>

        {activeTab === null ? (
          <div className="grid grid-cols-2 gap-3 pt-2">
            {TAB_CARDS.map(({ key, label, description, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className="flex items-start gap-3 rounded-lg border p-4 text-left transition-colors hover:bg-accent hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="mt-0.5 rounded-md bg-primary/10 p-2">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{description}</p>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div>
            <button
              onClick={() => setActiveTab(null)}
              className="mb-4 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronRight className="h-3 w-3 rotate-180" />
              Back to options
            </button>

            {activeTab === "file" && (
              <FileUploadPane
                importMutation={importMutation}
                onSuccess={handleSuccess}
              />
            )}
            {activeTab === "url" && (
              <UrlImportPane
                importMutation={importMutation}
                onSuccess={handleSuccess}
              />
            )}
            {activeTab === "clipboard" && (
              <ClipboardPane
                createMutation={createMutation}
                onSuccess={handleSuccess}
              />
            )}
            {activeTab === "manuscript" && (
              <ManuscriptPane
                createMutation={createMutation}
                onSuccess={handleSuccess}
              />
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ── File Upload Pane ───────────────────────────────────────────

interface FilePaneProps {
  importMutation: ReturnType<typeof useImportEntry>;
  onSuccess: (title: string) => void;
}

function FileUploadPane({ importMutation, onSuccess }: FilePaneProps) {
  const [fileName, setFileName] = useState("");
  const [fileSize, setFileSize] = useState(0);
  const [fileBase64, setFileBase64] = useState("");
  const [fileError, setFileError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback((file: File) => {
    setFileError("");
    setFileName("");
    setFileSize(0);
    setFileBase64("");

    if (!hasValidExtension(file.name)) {
      setFileError(`Unsupported format. Accepted: ${ACCEPTED_FORMATS_LABEL}`);
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setFileError(
        `File too large (${formatFileSize(file.size)}). Max ${formatFileSize(MAX_FILE_SIZE_BYTES)}.`
      );
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

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) processFile(file);
    },
    [processFile]
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) processFile(file);
    },
    [processFile]
  );

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const canSubmit = !!fileName && !!fileBase64 && !fileError && !importMutation.isPending;

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;
    const result = await importMutation.mutateAsync({
      file_name: fileName,
      file_content_base64: fileBase64,
    });
    onSuccess(result.title);
  }, [canSubmit, importMutation, fileName, fileBase64, onSuccess]);

  return (
    <div className="space-y-4">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 cursor-pointer transition-colors ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        }`}
      >
        <Upload className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium">
          Drop a file here or click to browse
        </p>
        <p className="text-xs text-muted-foreground">
          {ACCEPTED_FORMATS_LABEL} (max {formatFileSize(MAX_FILE_SIZE_BYTES)})
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {fileError && (
        <p className="text-xs text-red-500">{fileError}</p>
      )}

      {!fileError && fileName && (
        <div className="flex items-center gap-2 rounded-lg border bg-muted/50 p-3 text-sm">
          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
          <span className="truncate">{fileName}</span>
          <span className="text-muted-foreground text-xs shrink-0">
            ({formatFileSize(fileSize)})
          </span>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
      >
        {importMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Importing…
          </>
        ) : (
          <>
            <Upload className="h-4 w-4" /> Import File
          </>
        )}
      </button>

      {importMutation.isError && (
        <p className="text-sm text-red-500">Import failed. Please try again.</p>
      )}
    </div>
  );
}

// ── URL Import Pane ────────────────────────────────────────────

interface UrlPaneProps {
  importMutation: ReturnType<typeof useImportEntry>;
  onSuccess: (title: string) => void;
}

function UrlImportPane({ importMutation, onSuccess }: UrlPaneProps) {
  const [url, setUrl] = useState("");
  const [touched, setTouched] = useState(false);

  const urlError = useMemo(() => {
    if (!touched || url.trim() === "") return "";
    if (!isValidUrl(url)) return "URL must start with http:// or https://";
    return "";
  }, [url, touched]);

  const canSubmit = !!url.trim() && isValidUrl(url) && !importMutation.isPending;

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!canSubmit) return;
      const result = await importMutation.mutateAsync({ url: url.trim() });
      onSuccess(result.title);
    },
    [canSubmit, importMutation, url, onSuccess]
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="import-url" className="block text-sm font-medium mb-1">
          URL
        </label>
        <input
          id="import-url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onBlur={() => setTouched(true)}
          placeholder="https://example.com/article"
          className={`w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 ${
            urlError ? "border-red-500" : ""
          }`}
          autoFocus
        />
        {urlError && (
          <p className="mt-1 text-xs text-red-500">{urlError}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
      >
        {importMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Importing…
          </>
        ) : (
          <>
            <LinkIcon className="h-4 w-4" /> Import URL
          </>
        )}
      </button>

      {importMutation.isError && (
        <p className="text-sm text-red-500">Import failed. Please try again.</p>
      )}
    </form>
  );
}

// ── Clipboard Pane ─────────────────────────────────────────────

interface ClipboardPaneProps {
  createMutation: ReturnType<typeof useCreateEntry>;
  onSuccess: (title: string) => void;
}

function ClipboardPane({ createMutation, onSuccess }: ClipboardPaneProps) {
  const [text, setText] = useState("");

  const canSubmit = text.trim().length > 0 && !createMutation.isPending;

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!canSubmit) return;
      const result = await createMutation.mutateAsync({
        title: "Pasted content",
        content: text.trim(),
        source_type: "clip",
      });
      onSuccess(result.title);
    },
    [canSubmit, createMutation, text, onSuccess]
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="clipboard-text" className="block text-sm font-medium mb-1">
          Paste your content
        </label>
        <textarea
          id="clipboard-text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste or type text here…"
          rows={6}
          className="w-full border rounded-lg px-3 py-2 text-sm bg-background resize-y focus:outline-none focus:ring-2 focus:ring-primary/50"
          autoFocus
        />
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
      >
        {createMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Saving…
          </>
        ) : (
          <>
            <ClipboardPaste className="h-4 w-4" /> Save to Knowledge Base
          </>
        )}
      </button>

      {createMutation.isError && (
        <p className="text-sm text-red-500">Save failed. Please try again.</p>
      )}
    </form>
  );
}

// ── Manuscript Pane ────────────────────────────────────────────

interface ManuscriptPaneProps {
  createMutation: ReturnType<typeof useCreateEntry>;
  onSuccess: (title: string) => void;
}

function ManuscriptPane({ createMutation, onSuccess }: ManuscriptPaneProps) {
  const [selectedBookId, setSelectedBookId] = useState("");
  const [selectedChapterId, setSelectedChapterId] = useState("");

  const { data: books, isLoading: booksLoading } = useBooks();
  const { data: chapters, isLoading: chaptersLoading } = useChapters(selectedBookId);

  const selectedChapter = useMemo(
    () => chapters?.find((c) => c.id === selectedChapterId),
    [chapters, selectedChapterId]
  );

  const canSubmit =
    !!selectedChapter && selectedChapter.content.trim().length > 0 && !createMutation.isPending;

  const handleBookChange = useCallback((bookId: string) => {
    setSelectedBookId(bookId);
    setSelectedChapterId("");
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!canSubmit || !selectedChapter) return;
    const result = await createMutation.mutateAsync({
      title: selectedChapter.title,
      content: selectedChapter.content,
      source_type: "manual",
    });
    onSuccess(result.title);
  }, [canSubmit, createMutation, selectedChapter, onSuccess]);

  return (
    <div className="space-y-4">
      {/* Book selector */}
      <div>
        <label htmlFor="book-select" className="block text-sm font-medium mb-1">
          Select Book
        </label>
        <select
          id="book-select"
          value={selectedBookId}
          onChange={(e) => handleBookChange(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          disabled={booksLoading}
        >
          <option value="">
            {booksLoading ? "Loading books…" : "Choose a book"}
          </option>
          {books?.map((book) => (
            <option key={book.id} value={book.id}>
              {book.title}
            </option>
          ))}
        </select>
        {!booksLoading && books && books.length === 0 && (
          <p className="mt-1 text-xs text-muted-foreground">
            No manuscripts found. Create one in Writing Studio first.
          </p>
        )}
      </div>

      {/* Chapter selector */}
      {selectedBookId && (
        <div>
          <label htmlFor="chapter-select" className="block text-sm font-medium mb-1">
            Select Chapter
          </label>
          <select
            id="chapter-select"
            value={selectedChapterId}
            onChange={(e) => setSelectedChapterId(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            disabled={chaptersLoading}
          >
            <option value="">
              {chaptersLoading ? "Loading chapters…" : "Choose a chapter"}
            </option>
            {chapters?.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.title} ({ch.word_count} words)
              </option>
            ))}
          </select>
          {!chaptersLoading && chapters && chapters.length === 0 && (
            <p className="mt-1 text-xs text-muted-foreground">
              This book has no chapters yet.
            </p>
          )}
        </div>
      )}

      {/* Chapter preview */}
      {selectedChapter && (
        <div className="rounded-lg border bg-muted/50 p-3">
          <p className="text-sm font-medium mb-1">{selectedChapter.title}</p>
          <p className="text-xs text-muted-foreground line-clamp-3">
            {selectedChapter.content.slice(0, 300)}
            {selectedChapter.content.length > 300 ? "…" : ""}
          </p>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
      >
        {createMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Importing…
          </>
        ) : (
          <>
            <BookOpen className="h-4 w-4" /> Import Chapter
          </>
        )}
      </button>

      {createMutation.isError && (
        <p className="text-sm text-red-500">Import failed. Please try again.</p>
      )}
    </div>
  );
}
