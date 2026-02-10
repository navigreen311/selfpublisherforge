"use client";

import { useState } from "react";
import {
  useExportEpub,
  useExportPdf,
  useFormattingTemplates,
  type ExportRequest,
  type ExportResponse,
  type FormattingTemplate,
} from "../hooks";
import { toast } from "sonner";

const TRIM_SIZES = [
  { value: "5x8", label: '5" x 8"' },
  { value: "5.25x8", label: '5.25" x 8"' },
  { value: "5.5x8.5", label: '5.5" x 8.5"' },
  { value: "6x9", label: '6" x 9"' },
  { value: "7x10", label: '7" x 10"' },
  { value: "8.5x11", label: '8.5" x 11"' },
];

interface ExportWizardProps {
  bookId: string;
  chapters?: { title: string; content: string; order: number }[];
}

type Step = "format" | "template" | "options" | "review";

export function ExportWizard({ bookId, chapters = [] }: ExportWizardProps) {
  const [step, setStep] = useState<Step>("format");
  const [format, setFormat] = useState<"epub" | "pdf">("epub");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [trimSize, setTrimSize] = useState("6x9");
  const [includeToc, setIncludeToc] = useState(true);
  const [includeCover, setIncludeCover] = useState(false);
  const [includeIsbn, setIncludeIsbn] = useState(false);
  const [isbn, setIsbn] = useState("");
  const [isbnTouched, setIsbnTouched] = useState(false);
  const [result, setResult] = useState<ExportResponse | null>(null);

  const { data: templates = [] } = useFormattingTemplates();
  const exportEpub = useExportEpub();
  const exportPdf = useExportPdf();

  const isExporting = exportEpub.isPending || exportPdf.isPending;

  // ISBN validation for the export wizard
  const isValidISBN = (value: string): boolean => {
    const cleaned = value.replace(/[-\s]/g, "");
    if (cleaned.length === 10) {
      let sum = 0;
      for (let i = 0; i < 10; i++) {
        const char = cleaned[i];
        const val = char === "X" && i === 9 ? 10 : parseInt(char, 10);
        if (isNaN(val)) return false;
        sum += val * (10 - i);
      }
      return sum % 11 === 0;
    }
    if (cleaned.length === 13) {
      let sum = 0;
      for (let i = 0; i < 13; i++) {
        const val = parseInt(cleaned[i], 10);
        if (isNaN(val)) return false;
        sum += val * (i % 2 === 0 ? 1 : 3);
      }
      return sum % 10 === 0;
    }
    return false;
  };

  const isbnError =
    isbn.trim() !== "" && !isValidISBN(isbn)
      ? "Invalid ISBN format. Must be a valid ISBN-10 or ISBN-13."
      : "";

  const showIsbnError = isbnTouched && !!isbnError;

  const handleExport = () => {
    // Block export if ISBN is invalid
    if (includeIsbn && isbn.trim() !== "" && !isValidISBN(isbn)) {
      toast.error("Invalid ISBN format");
      setIsbnTouched(true);
      return;
    }

    const payload: ExportRequest = {
      book_id: bookId,
      format,
      chapters,
      template_id: selectedTemplateId,
      include_toc: includeToc,
      include_cover: includeCover,
      trim_size: trimSize,
      include_isbn_barcode: includeIsbn,
      isbn: isbn || null,
    };

    const mutation = format === "epub" ? exportEpub : exportPdf;
    mutation.mutate(payload, {
      onSuccess: (data) => {
        setResult(data);
        toast.success(`${format.toUpperCase()} export completed!`);
      },
      onError: () => {
        toast.error(`Failed to generate ${format.toUpperCase()}`);
      },
    });
  };

  const steps: Step[] = ["format", "template", "options", "review"];
  const currentIndex = steps.indexOf(step);

  return (
    <div className="mx-auto max-w-3xl">
      {/* Step indicator */}
      <nav className="mb-8">
        <ol className="flex items-center space-x-4">
          {steps.map((s, i) => (
            <li key={s} className="flex items-center">
              <button
                onClick={() => i <= currentIndex && setStep(s)}
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                  i <= currentIndex
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {i + 1}
              </button>
              <span className="ml-2 text-sm font-medium text-gray-700 capitalize">{s}</span>
              {i < steps.length - 1 && (
                <div className="ml-4 h-px w-12 bg-gray-300" />
              )}
            </li>
          ))}
        </ol>
      </nav>

      {/* Step: Format Selection */}
      {step === "format" && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Choose Export Format</h2>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => setFormat("epub")}
              className={`rounded-lg border-2 p-6 text-center transition-colors ${
                format === "epub"
                  ? "border-indigo-600 bg-indigo-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-3xl mb-2">📖</div>
              <h3 className="font-semibold text-gray-900">EPUB</h3>
              <p className="mt-1 text-sm text-gray-500">
                For e-readers and digital distribution
              </p>
            </button>
            <button
              onClick={() => setFormat("pdf")}
              className={`rounded-lg border-2 p-6 text-center transition-colors ${
                format === "pdf"
                  ? "border-indigo-600 bg-indigo-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-3xl mb-2">📄</div>
              <h3 className="font-semibold text-gray-900">PDF</h3>
              <p className="mt-1 text-sm text-gray-500">
                Print-ready for KDP and IngramSpark
              </p>
            </button>
          </div>
          <div className="flex justify-end">
            <button
              onClick={() => setStep("template")}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step: Template Selection */}
      {step === "template" && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Select Formatting Template</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {templates.map((t: FormattingTemplate) => (
              <button
                key={t.id}
                onClick={() => setSelectedTemplateId(t.id)}
                className={`rounded-lg border-2 p-4 text-left transition-colors ${
                  selectedTemplateId === t.id
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <h3 className="font-semibold text-gray-900">{t.name}</h3>
                <p className="mt-1 text-xs text-gray-500">{t.description}</p>
                <div className="mt-2 flex gap-2">
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                    {t.genre}
                  </span>
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                    {t.trim_size}
                  </span>
                </div>
              </button>
            ))}
          </div>
          <div className="flex justify-between">
            <button
              onClick={() => setStep("format")}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={() => setStep("options")}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step: Options */}
      {step === "options" && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Export Options</h2>
          <div className="space-y-4">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={includeToc}
                onChange={(e) => setIncludeToc(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600"
              />
              <span className="text-sm text-gray-700">Include Table of Contents</span>
            </label>

            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={includeCover}
                onChange={(e) => setIncludeCover(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600"
              />
              <span className="text-sm text-gray-700">Include Cover Image</span>
            </label>

            {format === "pdf" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trim Size
                  </label>
                  <select
                    value={trimSize}
                    onChange={(e) => setTrimSize(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  >
                    {TRIM_SIZES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={includeIsbn}
                    onChange={(e) => setIncludeIsbn(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-indigo-600"
                  />
                  <span className="text-sm text-gray-700">Include ISBN Barcode</span>
                </label>

                {includeIsbn && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ISBN
                    </label>
                    <input
                      type="text"
                      value={isbn}
                      onChange={(e) => setIsbn(e.target.value)}
                      onBlur={() => setIsbnTouched(true)}
                      placeholder="978-0-123456-47-2"
                      className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${
                        showIsbnError
                          ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                          : "border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
                      }`}
                    />
                    {showIsbnError ? (
                      <p className="mt-1 text-xs text-red-500">{isbnError}</p>
                    ) : (
                      <p className="mt-1 text-xs text-gray-400">10 or 13 digits, with optional hyphens</p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
          <div className="flex justify-between">
            <button
              onClick={() => setStep("template")}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={() => setStep("review")}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step: Review & Generate */}
      {step === "review" && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Review & Generate</h2>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-5 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Format</span>
              <span className="font-medium text-gray-900">{format.toUpperCase()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Chapters</span>
              <span className="font-medium text-gray-900">{chapters.length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Table of Contents</span>
              <span className="font-medium text-gray-900">{includeToc ? "Yes" : "No"}</span>
            </div>
            {format === "pdf" && (
              <>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Trim Size</span>
                  <span className="font-medium text-gray-900">{trimSize}</span>
                </div>
                {includeIsbn && isbn && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">ISBN</span>
                    <span className="font-medium text-gray-900">{isbn}</span>
                  </div>
                )}
              </>
            )}
            {selectedTemplateId && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Template</span>
                <span className="font-medium text-gray-900">
                  {templates.find((t: FormattingTemplate) => t.id === selectedTemplateId)?.name || "Custom"}
                </span>
              </div>
            )}
          </div>

          {result && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-5">
              <h3 className="font-semibold text-green-800">Export Complete</h3>
              <p className="mt-1 text-sm text-green-700">{result.message}</p>
              {result.file_url && (
                <p className="mt-2 text-sm">
                  <span className="text-green-600">File: </span>
                  <code className="text-green-800">{result.file_url}</code>
                </p>
              )}
              {result.file_size_bytes && (
                <p className="text-sm text-green-600">
                  Size: {(result.file_size_bytes / 1024).toFixed(1)} KB
                </p>
              )}
            </div>
          )}

          <div className="flex justify-between">
            <button
              onClick={() => setStep("options")}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="rounded-md bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {isExporting ? "Generating..." : `Generate ${format.toUpperCase()}`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
