"use client";

import { useState } from "react";
import { MetadataForm } from "./MetadataForm";

export function ISBNsTab() {
  const [bookId] = useState("default");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">ISBNs &amp; Identifiers</h2>
        <p className="mt-1 text-sm text-gray-500">
          Manage ISBNs, ASINs, and other book identifiers along with metadata.
        </p>
      </div>
      <MetadataForm bookId={bookId} />
    </div>
  );
}
