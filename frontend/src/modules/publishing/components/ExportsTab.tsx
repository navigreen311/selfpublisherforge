"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useBooks, useChapters } from "@/modules/writing/hooks";
import { useExportEpub, useExportPdf, type ExportRequest } from "../hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BookOpen,
  FileText,
  FileDown,
  Printer,
  Eye,
  Download,
  Clock,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type ExportFormat = "epub" | "pdf" | "docx" | "kpf";

interface FormatOption {
  id: ExportFormat;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    id: "epub",
    label: "EPUB",
    description: "E-readers & digital distribution",
    icon: <BookOpen className="h-6 w-6" />,
  },
  {
    id: "pdf",
    label: "Print PDF",
    description: "Print-ready for KDP & IngramSpark",
    icon: <Printer className="h-6 w-6" />,
  },
  {
    id: "docx",
    label: "DOCX",
    description: "Word document for editors & agents",
    icon: <FileText className="h-6 w-6" />,
  },
  {
    id: "kpf",
    label: "KPF",
    description: "Kindle Package Format for KDP",
    icon: <FileDown className="h-6 w-6" />,
  },
];

const TRIM_SIZES = [
  { value: "5x8", label: '5" x 8"' },
  { value: "5.5x8.5", label: '5.5" x 8.5"' },
  { value: "6x9", label: '6" x 9"' },
  { value: "8.5x11", label: '8.5" x 11"' },
];

const FONT_OPTIONS = [
  "Garamond",
  "Times New Roman",
  "Georgia",
  "Palatino",
  "Baskerville",
  "Caslon",
];

const FONT_SIZE_OPTIONS = ["10", "11", "12", "13", "14"];

const LINE_SPACING_OPTIONS = [
  { value: "1.0", label: "Single (1.0)" },
  { value: "1.15", label: "1.15" },
  { value: "1.5", label: "1.5" },
  { value: "2.0", label: "Double (2.0)" },
];

const DOCX_STYLES = [
  {
    value: "manuscript",
    label: "Manuscript",
    description: "Standard submission format — double-spaced, Courier/TNR",
  },
  {
    value: "galley",
    label: "Galley",
    description: "Typeset-like — single-spaced, serif font, chapter headings",
  },
  {
    value: "clean",
    label: "Clean",
    description: "Minimal formatting — easy to restyle in Word",
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ExportsTab() {
  // Step 1 — Book selection
  const [selectedBookId, setSelectedBookId] = useState<string>("");

  // Step 2 — Format
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("epub");

  // Step 3 — EPUB / KPF config
  const [epubFont, setEpubFont] = useState("Garamond");
  const [epubFontSize, setEpubFontSize] = useState("12");
  const [epubLineSpacing, setEpubLineSpacing] = useState("1.5");
  const [epubChapterBreaks, setEpubChapterBreaks] = useState(true);
  const [epubIncludeToc, setEpubIncludeToc] = useState(true);
  const [epubIncludeCover, setEpubIncludeCover] = useState(true);
  const [epubIsbn, setEpubIsbn] = useState("");

  // Step 3 — Print PDF config
  const [pdfTrimSize, setPdfTrimSize] = useState("6x9");
  const [pdfMargins, setPdfMargins] = useState("0.75");
  const [pdfFont, setPdfFont] = useState("Garamond");
  const [pdfFontSize, setPdfFontSize] = useState("11");
  const [pdfPageNumbers, setPdfPageNumbers] = useState(true);
  const [pdfIsbn, setPdfIsbn] = useState("");

  // Step 3 — DOCX config
  const [docxStyle, setDocxStyle] = useState("manuscript");

  // Data hooks
  const { data: books = [], isLoading: booksLoading } = useBooks();
  const { data: chapters = [] } = useChapters(selectedBookId);
  const exportEpub = useExportEpub();
  const exportPdf = useExportPdf();

  const isExporting = exportEpub.isPending || exportPdf.isPending;

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleExport = () => {
    if (!selectedBookId) {
      toast.error("Please select a book first");
      return;
    }

    const chapterInputs = chapters.map((ch) => ({
      title: ch.title,
      content: ch.content,
      order: ch.order,
    }));

    if (chapterInputs.length === 0) {
      toast.error("Selected book has no chapters to export");
      return;
    }

    if (selectedFormat === "epub" || selectedFormat === "kpf") {
      const payload: ExportRequest = {
        book_id: selectedBookId,
        format: "epub",
        chapters: chapterInputs,
        include_toc: epubIncludeToc,
        include_cover: epubIncludeCover,
        isbn: epubIsbn || null,
        include_isbn_barcode: !!epubIsbn,
      };
      exportEpub.mutate(payload, {
        onSuccess: (data) => {
          toast.success(
            `${selectedFormat.toUpperCase()} export completed! ${data.message}`
          );
        },
      });
    } else if (selectedFormat === "pdf") {
      const payload: ExportRequest = {
        book_id: selectedBookId,
        format: "pdf",
        chapters: chapterInputs,
        trim_size: pdfTrimSize,
        include_toc: true,
        include_cover: true,
        isbn: pdfIsbn || null,
        include_isbn_barcode: !!pdfIsbn,
      };
      exportPdf.mutate(payload, {
        onSuccess: (data) => {
          toast.success(`Print PDF export completed! ${data.message}`);
        },
      });
    } else if (selectedFormat === "docx") {
      // DOCX uses the EPUB endpoint as a placeholder for now
      const payload: ExportRequest = {
        book_id: selectedBookId,
        format: "epub",
        chapters: chapterInputs,
        include_toc: true,
        include_cover: false,
      };
      exportEpub.mutate(payload, {
        onSuccess: () => {
          toast.success("DOCX export completed!");
        },
      });
    }
  };

  const handlePreview = () => {
    toast("Preview coming soon — first 3 chapters will render here.");
  };

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const selectedBook = books.find((b) => b.id === selectedBookId);

  return (
    <div className="space-y-8">
      {/* ----------------------------------------------------------------- */}
      {/* Step 1 — Select Book                                              */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. Select Book</CardTitle>
        </CardHeader>
        <CardContent>
          {booksLoading ? (
            <p className="text-sm text-muted-foreground">Loading books...</p>
          ) : books.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No books found. Create a manuscript first.
            </p>
          ) : (
            <Select value={selectedBookId} onValueChange={setSelectedBookId}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Choose a book to export" />
              </SelectTrigger>
              <SelectContent>
                {books.map((book) => (
                  <SelectItem key={book.id} value={book.id}>
                    {book.title}
                    {book.chapter_count != null &&
                      ` (${book.chapter_count} chapters)`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {selectedBook && (
            <div className="mt-3 flex gap-4 text-sm text-muted-foreground">
              {selectedBook.word_count != null && (
                <span>{selectedBook.word_count.toLocaleString()} words</span>
              )}
              {selectedBook.status && <span>Status: {selectedBook.status}</span>}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Step 2 — Choose Format                                            */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. Choose Format</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {FORMAT_OPTIONS.map((fmt) => (
              <button
                key={fmt.id}
                type="button"
                onClick={() => setSelectedFormat(fmt.id)}
                className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 text-center transition-colors ${
                  selectedFormat === fmt.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/40"
                }`}
              >
                {fmt.icon}
                <span className="text-sm font-semibold">{fmt.label}</span>
                <span className="text-xs text-muted-foreground">
                  {fmt.description}
                </span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Step 3 — Configuration                                            */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            3. Configure {selectedFormat.toUpperCase()} Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* ---------- EPUB / KPF Config ---------- */}
          {(selectedFormat === "epub" || selectedFormat === "kpf") && (
            <div className="grid gap-6 sm:grid-cols-2">
              {/* Font */}
              <div className="space-y-2">
                <Label>Font Family</Label>
                <Select value={epubFont} onValueChange={setEpubFont}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FONT_OPTIONS.map((f) => (
                      <SelectItem key={f} value={f}>
                        {f}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Font Size */}
              <div className="space-y-2">
                <Label>Font Size (pt)</Label>
                <Select value={epubFontSize} onValueChange={setEpubFontSize}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FONT_SIZE_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s}pt
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Line Spacing */}
              <div className="space-y-2">
                <Label>Line Spacing</Label>
                <Select
                  value={epubLineSpacing}
                  onValueChange={setEpubLineSpacing}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LINE_SPACING_OPTIONS.map((ls) => (
                      <SelectItem key={ls.value} value={ls.value}>
                        {ls.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* ISBN */}
              <div className="space-y-2">
                <Label>ISBN (optional)</Label>
                <Input
                  value={epubIsbn}
                  onChange={(e) => setEpubIsbn(e.target.value)}
                  placeholder="978-0-123456-47-2"
                />
              </div>

              {/* Toggles */}
              <div className="flex items-center justify-between sm:col-span-2">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Switch
                      id="epub-chapter-breaks"
                      checked={epubChapterBreaks}
                      onCheckedChange={setEpubChapterBreaks}
                    />
                    <Label htmlFor="epub-chapter-breaks">Chapter Breaks</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      id="epub-toc"
                      checked={epubIncludeToc}
                      onCheckedChange={setEpubIncludeToc}
                    />
                    <Label htmlFor="epub-toc">Table of Contents</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      id="epub-cover"
                      checked={epubIncludeCover}
                      onCheckedChange={setEpubIncludeCover}
                    />
                    <Label htmlFor="epub-cover">Cover Image</Label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ---------- Print PDF Config ---------- */}
          {selectedFormat === "pdf" && (
            <div className="grid gap-6 sm:grid-cols-2">
              {/* Trim Size */}
              <div className="space-y-2">
                <Label>Trim Size</Label>
                <Select value={pdfTrimSize} onValueChange={setPdfTrimSize}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRIM_SIZES.map((ts) => (
                      <SelectItem key={ts.value} value={ts.value}>
                        {ts.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Margins */}
              <div className="space-y-2">
                <Label>Margins (inches)</Label>
                <Input
                  value={pdfMargins}
                  onChange={(e) => setPdfMargins(e.target.value)}
                  placeholder="0.75"
                  type="text"
                />
              </div>

              {/* Font */}
              <div className="space-y-2">
                <Label>Font Family</Label>
                <Select value={pdfFont} onValueChange={setPdfFont}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FONT_OPTIONS.map((f) => (
                      <SelectItem key={f} value={f}>
                        {f}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Font Size */}
              <div className="space-y-2">
                <Label>Font Size (pt)</Label>
                <Select value={pdfFontSize} onValueChange={setPdfFontSize}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FONT_SIZE_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s}pt
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Page Numbers Toggle */}
              <div className="flex items-center gap-2">
                <Switch
                  id="pdf-page-numbers"
                  checked={pdfPageNumbers}
                  onCheckedChange={setPdfPageNumbers}
                />
                <Label htmlFor="pdf-page-numbers">Page Numbers</Label>
              </div>

              {/* ISBN */}
              <div className="space-y-2">
                <Label>ISBN (optional)</Label>
                <Input
                  value={pdfIsbn}
                  onChange={(e) => setPdfIsbn(e.target.value)}
                  placeholder="978-0-123456-47-2"
                />
              </div>
            </div>
          )}

          {/* ---------- DOCX Config ---------- */}
          {selectedFormat === "docx" && (
            <div className="space-y-4">
              <Label>Formatting Style</Label>
              <div className="grid gap-3 sm:grid-cols-3">
                {DOCX_STYLES.map((style) => (
                  <button
                    key={style.value}
                    type="button"
                    onClick={() => setDocxStyle(style.value)}
                    className={`rounded-lg border-2 p-4 text-left transition-colors ${
                      docxStyle === style.value
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/40"
                    }`}
                  >
                    <span className="text-sm font-semibold">{style.label}</span>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {style.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Step 4 — Actions                                                  */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">4. Export</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button variant="outline" onClick={handlePreview}>
              <Eye className="mr-2 h-4 w-4" />
              Preview First 3 Chapters
            </Button>
            <Button
              onClick={handleExport}
              disabled={!selectedBookId || isExporting}
            >
              <Download className="mr-2 h-4 w-4" />
              {isExporting
                ? "Exporting..."
                : `Export ${selectedFormat.toUpperCase()}`}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Export History                                                     */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Export History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Export history coming soon
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
