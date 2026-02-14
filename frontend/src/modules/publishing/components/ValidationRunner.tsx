"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { FullValidationRequest } from "../hooks";

interface ValidationRunnerProps {
  bookId: string;
  onRun: (request: FullValidationRequest) => void;
  isRunning: boolean;
}

const TRIM_SIZES = [
  { value: "5x8", label: '5" x 8"' },
  { value: "5.25x8", label: '5.25" x 8"' },
  { value: "5.5x8.5", label: '5.5" x 8.5"' },
  { value: "6x9", label: '6" x 9"' },
  { value: "7x10", label: '7" x 10"' },
  { value: "8.5x11", label: '8.5" x 11"' },
];

export function ValidationRunner({ bookId, onRun, isRunning }: ValidationRunnerProps) {
  const [validatePrint, setValidatePrint] = useState(true);
  const [validateEbook, setValidateEbook] = useState(true);
  const [validateCover, setValidateCover] = useState(true);
  const [validateCompliance, setValidateCompliance] = useState(true);

  // Print validation fields
  const [trimSize, setTrimSize] = useState("6x9");
  const [pageCount, setPageCount] = useState(200);
  const [insideMargin, setInsideMargin] = useState(0.75);
  const [outsideMargin, setOutsideMargin] = useState(0.5);
  const [topMargin, setTopMargin] = useState(0.75);
  const [bottomMargin, setBottomMargin] = useState(0.75);

  // Ebook validation fields
  const [fileSize, setFileSize] = useState(5000000); // 5MB default

  // Cover validation fields
  const [coverWidth, setCoverWidth] = useState(6);
  const [coverHeight, setCoverHeight] = useState(9);
  const [coverDpi, setCoverDpi] = useState(300);
  const [coverFormat, setCoverFormat] = useState("JPEG");

  const handleRun = () => {
    const request: FullValidationRequest = {};

    if (validatePrint) {
      request.print_validation = {
        trim_size: trimSize,
        page_count: pageCount,
        paper_type: "white",
        has_bleed: false,
        inside_margin: insideMargin,
        outside_margin: outsideMargin,
        top_margin: topMargin,
        bottom_margin: bottomMargin,
        image_dpi: 300,
        fonts_embedded: true,
        color_space: "RGB",
      };
    }

    if (validateEbook) {
      request.ebook_validation = {
        has_ncx_toc: true,
        has_html_toc: true,
        images: [],
        links: [],
        has_javascript: false,
        has_external_resources: false,
        min_font_size_pt: 12,
        file_size_bytes: fileSize,
      };
    }

    if (validateCover) {
      request.cover_validation = {
        cover_type: "print",
        width_inches: coverWidth,
        height_inches: coverHeight,
        dpi: coverDpi,
        file_format: coverFormat,
        color_space: "CMYK",
        trim_size: trimSize,
        page_count: pageCount,
        paper_type: "white",
        has_text_in_bleed: false,
      };
    }

    if (validateCompliance) {
      request.compliance_scan = {
        title: "Sample Book Title",
        subtitle: "",
        description: "Sample description",
        keywords: ["fiction", "mystery"],
        categories: ["Fiction > Mystery"],
        content_sample: "Sample content for compliance check",
      };
    }

    onRun(request);
  };

  return (
    <Card className="p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Validation Options</h3>

      {/* Validation Type Checkboxes */}
      <div className="space-y-3 mb-6">
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={validatePrint}
            onChange={(e) => setValidatePrint(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600"
          />
          <span className="text-sm font-medium text-gray-700">Validate Print Specs</span>
        </label>

        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={validateEbook}
            onChange={(e) => setValidateEbook(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600"
          />
          <span className="text-sm font-medium text-gray-700">Validate Ebook Format</span>
        </label>

        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={validateCover}
            onChange={(e) => setValidateCover(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600"
          />
          <span className="text-sm font-medium text-gray-700">Validate Cover Specs</span>
        </label>

        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={validateCompliance}
            onChange={(e) => setValidateCompliance(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600"
          />
          <span className="text-sm font-medium text-gray-700">Check Content Compliance</span>
        </label>
      </div>

      {/* Print Settings */}
      {validatePrint && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Print Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
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
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Page Count
              </label>
              <input
                type="number"
                value={pageCount}
                onChange={(e) => setPageCount(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Inside Margin (in)
              </label>
              <input
                type="number"
                step="0.1"
                value={insideMargin}
                onChange={(e) => setInsideMargin(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Outside Margin (in)
              </label>
              <input
                type="number"
                step="0.1"
                value={outsideMargin}
                onChange={(e) => setOutsideMargin(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* Ebook Settings */}
      {validateEbook && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Ebook Settings</h4>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              File Size (bytes)
            </label>
            <input
              type="number"
              value={fileSize}
              onChange={(e) => setFileSize(Number(e.target.value))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>
      )}

      {/* Cover Settings */}
      {validateCover && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Cover Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Width (inches)
              </label>
              <input
                type="number"
                step="0.1"
                value={coverWidth}
                onChange={(e) => setCoverWidth(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Height (inches)
              </label>
              <input
                type="number"
                step="0.1"
                value={coverHeight}
                onChange={(e) => setCoverHeight(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                DPI
              </label>
              <input
                type="number"
                value={coverDpi}
                onChange={(e) => setCoverDpi(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Format
              </label>
              <select
                value={coverFormat}
                onChange={(e) => setCoverFormat(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="JPEG">JPEG</option>
                <option value="TIFF">TIFF</option>
                <option value="PNG">PNG</option>
              </select>
            </div>
          </div>
        </div>
      )}

      <Button
        onClick={handleRun}
        disabled={isRunning || (!validatePrint && !validateEbook && !validateCover && !validateCompliance)}
        className="w-full"
      >
        {isRunning ? "Running Validation..." : "Run Full Validation"}
      </Button>
    </Card>
  );
}
