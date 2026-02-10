"use client";

import { useState, useEffect, useCallback } from "react";
import {
  useBookMetadata,
  useUpdateMetadata,
  type BookMetadataUpdate,
} from "../hooks";
import { toast } from "sonner";

const MAX_KEYWORDS = 7;
const MAX_KEYWORD_LENGTH = 50;
const MAX_CATEGORIES = 2;
const MAX_TITLE_LENGTH = 200;
const MAX_DESCRIPTION_LENGTH = 4000;

// ---------------------------------------------------------------------------
// Validation helpers (simple functions — no zod)
// ---------------------------------------------------------------------------

const isValidISBN = (isbn: string): boolean => {
  const cleaned = isbn.replace(/[-\s]/g, "");
  if (cleaned.length === 10) {
    // ISBN-10: sum of (digit * position) mod 11 == 0
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
    // ISBN-13: alternating 1,3 weights, sum mod 10 == 0
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

const isValidASIN = (asin: string): boolean => {
  // ASIN: 10 alphanumeric characters, typically starting with B
  return /^[A-Z0-9]{10}$/.test(asin.toUpperCase());
};

type FieldErrors = Record<string, string>;

function validateTitle(value: string): string {
  if (!value || value.trim().length === 0) return "This field is required";
  if (value.length > MAX_TITLE_LENGTH) return `Title must be at most ${MAX_TITLE_LENGTH} characters`;
  return "";
}

function validateDescription(value: string): string {
  if (value.length > MAX_DESCRIPTION_LENGTH)
    return `Description must be at most ${MAX_DESCRIPTION_LENGTH} characters (KDP limit)`;
  return "";
}

function validateKeywords(input: string): string {
  const keywords = input
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (keywords.length > MAX_KEYWORDS) return `Maximum ${MAX_KEYWORDS} keywords allowed`;
  const tooLong = keywords.find((k) => k.length > MAX_KEYWORD_LENGTH);
  if (tooLong) return `Each keyword must be at most ${MAX_KEYWORD_LENGTH} characters`;
  return "";
}

function validateCategories(input: string): string {
  const categories = input
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (categories.length > MAX_CATEGORIES) return `Maximum ${MAX_CATEGORIES} categories allowed`;
  return "";
}

function validateISBN(value: string): string {
  if (!value || value.trim() === "") return "";
  if (!isValidISBN(value)) return "Invalid ISBN format. Must be a valid ISBN-10 or ISBN-13.";
  return "";
}

function validateASIN(value: string): string {
  if (!value || value.trim() === "") return "";
  if (!isValidASIN(value)) return "Invalid ASIN format. Must be 10 alphanumeric characters.";
  return "";
}

function validatePrice(value: string, fieldName: string, required: boolean): string {
  if (!required && (!value || value.trim() === "")) return "";
  const num = parseFloat(value);
  if (isNaN(num)) return `${fieldName} must be a valid number`;
  if (num < 0) return `${fieldName} must be a positive number`;
  return "";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface MetadataFormProps {
  bookId: string;
}

export function MetadataForm({ bookId }: MetadataFormProps) {
  const { data: metadata, isLoading } = useBookMetadata(bookId);
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

  // Touched state tracking — errors only show after user interaction or submit
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitAttempted, setSubmitAttempted] = useState(false);

  const markTouched = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  // Recompute all errors whenever form state changes
  const computeErrors = useCallback((): FieldErrors => {
    const errors: FieldErrors = {};

    const titleErr = validateTitle(form.title || "");
    if (titleErr) errors.title = titleErr;

    const descErr = validateDescription(form.description || "");
    if (descErr) errors.description = descErr;

    const kwErr = validateKeywords(keywordsInput);
    if (kwErr) errors.keywords = kwErr;

    const catErr = validateCategories(categoriesInput);
    if (catErr) errors.categories = catErr;

    const isbnErr = validateISBN(form.isbn || "");
    if (isbnErr) errors.isbn = isbnErr;

    const asinErr = validateASIN(form.asin || "");
    if (asinErr) errors.asin = asinErr;

    const listPriceErr = validatePrice(listPrice, "List price", false);
    if (listPriceErr) errors.listPrice = listPriceErr;

    const salePriceErr = validatePrice(salePrice, "Sale price", false);
    if (salePriceErr) errors.salePrice = salePriceErr;

    return errors;
  }, [form.title, form.description, form.isbn, form.asin, keywordsInput, categoriesInput, listPrice, salePrice]);

  useEffect(() => {
    setFieldErrors(computeErrors());
  }, [computeErrors]);

  const hasErrors = Object.keys(fieldErrors).length > 0;

  // Helper: should we show an error for a given field?
  const showError = (field: string): boolean =>
    !!(fieldErrors[field] && (touched[field] || submitAttempted));

  const errorClass = (field: string): string =>
    showError(field)
      ? "border-red-500 focus:border-red-500 focus:ring-red-500"
      : "border-gray-300 focus:border-indigo-500 focus:ring-indigo-500";

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
      // Reset validation state when metadata loads
      setTouched({});
      setSubmitAttempted(false);
    }
  }, [metadata]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitAttempted(true);

    const errors = computeErrors();
    setFieldErrors(errors);

    if (Object.keys(errors).length > 0) {
      // Show the first error as a toast
      const firstError = Object.values(errors)[0];
      toast.error(firstError);
      return;
    }

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
      onSuccess: () => {
        toast.success("Metadata saved successfully");
        setSubmitAttempted(false);
      },
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
              onBlur={() => markTouched("title")}
              maxLength={MAX_TITLE_LENGTH}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("title")}`}
            />
            <div className="flex justify-between mt-1">
              {showError("title") ? (
                <p className="text-xs text-red-500">{fieldErrors.title}</p>
              ) : (
                <span />
              )}
              <p className="text-xs text-gray-400">
                {(form.title || "").length}/{MAX_TITLE_LENGTH}
              </p>
            </div>
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
              onBlur={() => markTouched("description")}
              maxLength={MAX_DESCRIPTION_LENGTH}
              rows={5}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("description")}`}
            />
            <div className="flex justify-between mt-1">
              {showError("description") ? (
                <p className="text-xs text-red-500">{fieldErrors.description}</p>
              ) : (
                <span />
              )}
              <p
                className={`text-xs ${
                  (form.description || "").length >= MAX_DESCRIPTION_LENGTH
                    ? "text-red-500 font-medium"
                    : "text-gray-400"
                }`}
              >
                {(form.description || "").length}/{MAX_DESCRIPTION_LENGTH}
              </p>
            </div>
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
              Keywords (comma-separated, max {MAX_KEYWORDS})
            </label>
            <input
              type="text"
              value={keywordsInput}
              onChange={(e) => setKeywordsInput(e.target.value)}
              onBlur={() => markTouched("keywords")}
              placeholder="thriller, suspense, mystery, detective"
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("keywords")}`}
            />
            <div className="flex justify-between mt-1">
              {showError("keywords") ? (
                <p className="text-xs text-red-500">{fieldErrors.keywords}</p>
              ) : (
                <span />
              )}
              <p
                className={`text-xs ${
                  keywordsInput.split(",").filter((k) => k.trim()).length >= MAX_KEYWORDS
                    ? "text-red-500 font-medium"
                    : "text-gray-400"
                }`}
              >
                {keywordsInput.split(",").filter((k) => k.trim()).length}/{MAX_KEYWORDS} keywords
              </p>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categories (comma-separated, max {MAX_CATEGORIES})
            </label>
            <input
              type="text"
              value={categoriesInput}
              onChange={(e) => setCategoriesInput(e.target.value)}
              onBlur={() => markTouched("categories")}
              placeholder="Fiction > Thriller, Fiction > Mystery"
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("categories")}`}
            />
            <div className="flex justify-between mt-1">
              {showError("categories") ? (
                <p className="text-xs text-red-500">{fieldErrors.categories}</p>
              ) : (
                <span />
              )}
              <p
                className={`text-xs ${
                  categoriesInput.split(",").filter((c) => c.trim()).length >= MAX_CATEGORIES
                    ? "text-red-500 font-medium"
                    : "text-gray-400"
                }`}
              >
                {categoriesInput.split(",").filter((c) => c.trim()).length}/{MAX_CATEGORIES} categories
              </p>
            </div>
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
              onBlur={() => markTouched("isbn")}
              placeholder="978-0-123456-47-2"
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("isbn")}`}
            />
            {showError("isbn") ? (
              <p className="mt-1 text-xs text-red-500">{fieldErrors.isbn}</p>
            ) : (
              <p className="mt-1 text-xs text-gray-400">10 or 13 digits, with optional hyphens</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ASIN</label>
            <input
              type="text"
              value={form.asin || ""}
              onChange={(e) => setForm({ ...form, asin: e.target.value })}
              onBlur={() => markTouched("asin")}
              placeholder="B0XXXXXXXXX"
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("asin")}`}
            />
            {showError("asin") ? (
              <p className="mt-1 text-xs text-red-500">{fieldErrors.asin}</p>
            ) : (
              <p className="mt-1 text-xs text-gray-400">10 alphanumeric characters (e.g., B0XXXXXXXXX)</p>
            )}
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
              onBlur={() => markTouched("listPrice")}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("listPrice")}`}
            />
            {showError("listPrice") && (
              <p className="mt-1 text-xs text-red-500">{fieldErrors.listPrice}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sale Price</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={salePrice}
              onChange={(e) => setSalePrice(e.target.value)}
              onBlur={() => markTouched("salePrice")}
              placeholder="Optional"
              className={`w-full rounded-md border px-3 py-2 text-sm focus:ring-1 ${errorClass("salePrice")}`}
            />
            {showError("salePrice") && (
              <p className="mt-1 text-xs text-red-500">{fieldErrors.salePrice}</p>
            )}
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
          disabled={updateMetadata.isPending || hasErrors}
          className="rounded-md bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {updateMetadata.isPending ? "Saving..." : "Save Metadata"}
        </button>
      </div>
    </form>
  );
}
