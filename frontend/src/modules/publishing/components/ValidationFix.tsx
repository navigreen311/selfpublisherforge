"use client";

import { Lightbulb } from "lucide-react";
import type { ValidationIssue } from "../hooks";

interface ValidationFixProps {
  issue: ValidationIssue;
}

const FIX_SUGGESTIONS: Record<string, string> = {
  // Print validation
  "margins-too-small": "Increase your margins to at least 0.5 inches on outside edges and 0.75 inches on inside (gutter) margins. Adjust your document layout in your word processor or design software.",
  "page-count-odd": "KDP requires an even page count for print books. Add a blank page at the end of your manuscript to make the total page count even.",
  "low-image-dpi": "Increase image resolution to at least 300 DPI. Re-export images from the source at higher resolution or use image upscaling tools.",
  "fonts-not-embedded": "Ensure all fonts are embedded in your PDF. In Adobe Acrobat or your PDF export settings, enable 'Embed all fonts' option.",
  "incorrect-color-space": "Convert your document to the correct color space. For print interiors, use RGB or Grayscale. For covers, use CMYK for best results.",
  "bleed-required": "Add 0.125 inch bleed on all edges if your interior contains full-page images or backgrounds. Extend your content beyond the trim size.",

  // Ebook validation
  "missing-toc": "Add a Table of Contents (TOC) to your ebook. Use your word processor's heading styles to generate an automatic TOC, or create one manually in your EPUB editor.",
  "large-image-size": "Compress images to reduce file size. Use tools like TinyPNG or ImageOptim, and ensure images are sized appropriately for screen display (typically 600-800px wide max).",
  "broken-links": "Fix broken internal links by ensuring all chapter references point to valid locations. Check external URLs for validity.",
  "javascript-detected": "Remove JavaScript from your ebook. KDP does not support interactive JavaScript in EPUBs. Use standard HTML and CSS only.",
  "external-resources": "Embed all resources (images, fonts, CSS) within the EPUB package. Remove references to external URLs or CDN-hosted resources.",
  "small-font-size": "Increase minimum font size to at least 12pt for body text. Smaller fonts are difficult to read on e-readers.",
  "file-too-large": "Reduce EPUB file size by compressing images, removing unused resources, and optimizing HTML. KDP recommends keeping ebooks under 50MB.",

  // Cover validation
  "low-cover-dpi": "Increase cover image resolution to at least 300 DPI. Re-create or re-export your cover at higher resolution.",
  "incorrect-dimensions": "Ensure cover dimensions match your chosen trim size. Use KDP's cover calculator to determine exact pixel dimensions for your trim size and page count.",
  "text-in-bleed": "Move important text elements (title, author name) away from the bleed area (0.125 inches from edge) and the spine area to prevent them from being cut off.",
  "wrong-format": "Save your cover in the correct format. KDP accepts JPEG, TIFF, or PDF for covers. Ensure the file format matches KDP requirements.",
  "cover-color-space": "Convert your cover to CMYK color space for print. RGB may result in color shifts when printed.",

  // Compliance
  "prohibited-content": "Review your content for KDP policy violations. Remove prohibited content including graphic violence, hate speech, or copyrighted material without permission.",
  "trademark-violation": "Remove or modify trademarked terms unless you have permission. Use generic alternatives or create original terminology.",
  "misleading-metadata": "Ensure your title, description, and keywords accurately describe your book's content. Remove misleading or irrelevant terms.",
  "category-mismatch": "Select categories that accurately match your book's genre and content. Use KDP's category browser to find appropriate classifications.",
  "keyword-stuffing": "Reduce keyword count to relevant terms only. Avoid repetitive or unrelated keywords. Focus on 5-7 highly relevant search terms.",
};

export function ValidationFix({ issue }: ValidationFixProps) {
  // Try to match the rule to a known fix suggestion
  const suggestion =
    FIX_SUGGESTIONS[issue.rule] ||
    "Review KDP's content guidelines and formatting requirements for detailed resolution steps. Contact KDP support if you need additional assistance.";

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2">
        <Lightbulb className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <h6 className="text-xs font-semibold text-gray-900 mb-1">How to Fix</h6>
          <p className="text-xs text-gray-700 leading-relaxed">{suggestion}</p>
        </div>
      </div>

      {issue.details && Object.keys(issue.details).length > 0 && (
        <div className="rounded border border-gray-200 bg-white p-2">
          <h6 className="text-xs font-semibold text-gray-900 mb-1">Details</h6>
          <dl className="space-y-1">
            {Object.entries(issue.details).map(([key, value]) => (
              <div key={key} className="flex gap-2 text-xs">
                <dt className="font-medium text-gray-700 capitalize">
                  {key.replace(/_/g, " ")}:
                </dt>
                <dd className="text-gray-600">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
