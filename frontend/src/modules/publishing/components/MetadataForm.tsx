"use client";

import { useState, useEffect } from "react";
import {
  useBookMetadata,
  useUpdateMetadata,
  type BookMetadata,
  type BookMetadataUpdate,
} from "../hooks";
import { toast } from "sonner";

interface MetadataFormProps {
  bookId: string;
}

export function MetadataForm({ bookId }: MetadataFormProps) {
  const { data: metadata, isLoading, error } = useBookMetadata(bookId);
  const updateMetadata = useUpdateMetadata(bookId);

  const [form, setForm] = useState<BookMetadataUpdate>({
    title: "",
    subtitle: "",
    description: "",
    authors: [],
    keywords: [],
    categories: [],
    language: "en",
    isbn: "",
    asin: "",
    publisher: "",
    series_name: "",
    series_number: undefined,
    page_count: undefined,
    age_range: "",
  });

  const [authorsInput, setAuthorsInput] = useState("");
  const [keywordsInput, setKeywordsInput] = useState("");
  const [categoriesInput, setCategoriesInput] = useState("");
  const [listPrice, setListPrice] = useState("0.00");
  const [salePrice, setSalePrice] = useState("");
  const [currency, setCurrency] = useState("USD");

  useEffect(() => {
    if (metadata) {
      setForm({
        title: metadata.title || "",
        subtitle: metadata.subtitle || "",
        description: metadata.description || "",
        authors: metadata.authors || [],
        keywords: metadata.keywords || [],
        categories: metadata.categories || [],
        language: metadata.language || "en",
        isbn: metadata.isbn || "",
        asin: metadata.asin || "",
        publisher: metadata.publisher || "",
        series_name: metadata.series_name || "",
        series_number: metadata.series_number ?? undefined,
        page_count: metadata.page_count ?? undefined,
        age_range: metadata.age_range || "",
      });
      setAuthorsInput((metadata.authors || []).join(", "));
      setKeywordsInput((metadata.keywords || []).join(", "));
      setCategoriesInput((metadata.categories || []).join(", "));
      setListPrice(String(metadata.pricing?.list_price ?? "0.00"));
      setSalePrice(metadata.pricing?.sale_price != null ? String(metadata.pricing.sale_price) : "");
      setCurrency(metadata.pricing?.currency || "USD");
    }
  }, [metadata]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const payload: BookMetadataUpdate = {
      ...form,
      authors: authorsInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      keywords: keywordsInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      categories: categoriesInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      pricing: {
        currency,
        list_price: parseFloat(listPrice) || 0,
        sale_price: salePrice ? parseFloat(salePrice) : null,
      },
    };

    updateMetadata.mutate(payload, {
      onSuccess: () => toast.success("Metadata saved successfully"),
      onError: () => toast.error("Failed to save metadata"),
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading metadata...</div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Basic Information */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <input
              type="text"
              value={form.title || ""}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Subtitle</label>
            <input
              type="text"
              value={form.subtitle || ""}
              onChange={(e) => setForm({ ...form, subtitle: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={form.description || ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={5}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Authors (comma-separated)
            </label>
            <input
              type="text"
              value={authorsInput}
              onChange={(e) => setAuthorsInput(e.target.value)}
              placeholder="Jane Doe, John Smith"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
            <select
              value={form.language || "en"}
              onChange={(e) => setForm({ ...form, language: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="pt">Portuguese</option>
              <option value="ja">Japanese</option>
              <option value="zh">Chinese</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Publisher</label>
            <input
              type="text"
              value={form.publisher || ""}
              onChange={(e) => setForm({ ...form, publisher: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </section>

      {/* Discoverability */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Discoverability</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Keywords (comma-separated, max 7)
            </label>
            <input
              type="text"
              value={keywordsInput}
              onChange={(e) => setKeywordsInput(e.target.value)}
              placeholder="thriller, suspense, mystery, detective"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-400">
              {keywordsInput.split(",").filter((k) => k.trim()).length}/7 keywords
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categories (comma-separated)
            </label>
            <input
              type="text"
              value={categoriesInput}
              onChange={(e) => setCategoriesInput(e.target.value)}
              placeholder="Fiction > Thriller, Fiction > Mystery"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </section>

      {/* Identifiers */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Identifiers</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ISBN</label>
            <input
              type="text"
              value={form.isbn || ""}
              onChange={(e) => setForm({ ...form, isbn: e.target.value })}
              placeholder="978-0-123456-47-2"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ASIN</label>
            <input
              type="text"
              value={form.asin || ""}
              onChange={(e) => setForm({ ...form, asin: e.target.value })}
              placeholder="B0XXXXXXXXX"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </section>

      {/* Series */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Series</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Series Name</label>
            <input
              type="text"
              value={form.series_name || ""}
              onChange={(e) => setForm({ ...form, series_name: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Book Number</label>
            <input
              type="number"
              min={1}
              value={form.series_number ?? ""}
              onChange={(e) =>
                setForm({ ...form, series_number: e.target.value ? parseInt(e.target.value) : undefined })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Pricing</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="CAD">CAD</option>
              <option value="AUD">AUD</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">List Price</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={listPrice}
              onChange={(e) => setListPrice(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sale Price</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={salePrice}
              onChange={(e) => setSalePrice(e.target.value)}
              placeholder="Optional"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </section>

      {/* Additional */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Details</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Page Count</label>
            <input
              type="number"
              min={1}
              value={form.page_count ?? ""}
              onChange={(e) =>
                setForm({ ...form, page_count: e.target.value ? parseInt(e.target.value) : undefined })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Age Range</label>
            <input
              type="text"
              value={form.age_range || ""}
              onChange={(e) => setForm({ ...form, age_range: e.target.value })}
              placeholder="e.g., 12-18"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </section>

      {/* Submit */}
      <div className="flex justify-end border-t border-gray-200 pt-6">
        <button
          type="submit"
          disabled={updateMetadata.isPending}
          className="rounded-md bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {updateMetadata.isPending ? "Saving..." : "Save Metadata"}
        </button>
      </div>
    </form>
  );
}
