"use client";

import { useState } from "react";
import { ExportWizard } from "./ExportWizard";

export function ExportsTab() {
  const [bookId] = useState("default");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Export Book</h2>
        <p className="mt-1 text-sm text-gray-500">
          Generate EPUB or print-ready PDF files for your book.
        </p>
      </div>
      <ExportWizard bookId={bookId} />
    </div>
  );
}
