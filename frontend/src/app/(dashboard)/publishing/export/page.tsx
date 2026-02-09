"use client";

import { ExportWizard } from "@/modules/publishing/components/ExportWizard";
import Link from "next/link";

// Demo chapters for the export wizard; in production these would come from
// the manuscript/book data loaded via the book ID.
const DEMO_CHAPTERS = [
  {
    title: "Chapter 1: The Beginning",
    content:
      "It was a bright cold day in April, and the clocks were striking thirteen.\n\n" +
      "Winston Smith, his chin nuzzled into his breast in an effort to escape the vile wind, " +
      "slipped quickly through the glass doors of Victory Mansions.",
    order: 1,
  },
  {
    title: "Chapter 2: The Journey",
    content:
      "The journey of a thousand miles begins with a single step.\n\n" +
      "She packed her bags carefully, making sure to include the old leather journal " +
      "that had belonged to her grandmother.",
    order: 2,
  },
  {
    title: "Chapter 3: The Discovery",
    content:
      "Hidden beneath the floorboards was a letter, yellowed with age.\n\n" +
      "The handwriting was unmistakable -- it was her father's.",
    order: 3,
  },
];

// In production this would come from the URL params or selected book context
const DEMO_BOOK_ID = "00000000-0000-0000-0000-000000000099";

export default function ExportPage() {
  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm text-gray-500">
        <Link href="/publishing" className="hover:text-gray-700">
          Publishing
        </Link>
        <span>/</span>
        <span className="text-gray-900">Export</span>
      </nav>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Export Manuscript</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate an EPUB for digital distribution or a print-ready PDF for KDP / IngramSpark.
        </p>
      </div>

      {/* Export Wizard */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <ExportWizard bookId={DEMO_BOOK_ID} chapters={DEMO_CHAPTERS} />
      </div>
    </div>
  );
}
