"use client";

import { useParams } from "next/navigation";
import { MetadataForm } from "@/modules/publishing/components/MetadataForm";
import Link from "next/link";

export default function MetadataEditorPage() {
  const params = useParams();
  const bookId = params.bookId as string;

  if (!bookId) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-500">No book selected.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm text-gray-500">
        <Link href="/publishing" className="hover:text-gray-700">
          Publishing
        </Link>
        <span>/</span>
        <span className="text-gray-900">Metadata Editor</span>
      </nav>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Book Metadata</h1>
        <p className="mt-1 text-sm text-gray-500">
          Edit title, description, keywords, categories, pricing, and identifiers for your book.
        </p>
      </div>

      {/* Metadata Form */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <MetadataForm bookId={bookId} />
      </div>
    </div>
  );
}
