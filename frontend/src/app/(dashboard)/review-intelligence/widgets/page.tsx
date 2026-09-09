"use client";

import { useMemo, useState } from "react";
import { useBookReviewSummaries } from "@/modules/reviews/hooks";
import {
  useReviewWidgets,
  useCreateReviewWidget,
  useDeleteReviewWidget,
  type WidgetStyle,
  type WidgetTheme,
} from "@/modules/reviews/widget-hooks";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Copy, Trash2, Star } from "lucide-react";

const STYLE_OPTIONS: { value: WidgetStyle; label: string; blurb: string }[] = [
  { value: "card_grid", label: "Card Grid", blurb: "Responsive grid of review cards" },
  { value: "carousel", label: "Carousel", blurb: "Horizontal scrolling review strip" },
  { value: "compact_list", label: "Compact List", blurb: "Minimal vertical list" },
];

const THEME_OPTIONS: { value: WidgetTheme; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "auto", label: "Auto" },
];

export default function ReviewWidgetsPage() {
  const { data: books } = useBookReviewSummaries();
  const { data: widgets, isLoading } = useReviewWidgets();
  const createWidget = useCreateReviewWidget();
  const deleteWidget = useDeleteReviewWidget();

  const [bookId, setBookId] = useState<string>("");
  const [style, setStyle] = useState<WidgetStyle>("card_grid");
  const [theme, setTheme] = useState<WidgetTheme>("light");
  const [maxReviews, setMaxReviews] = useState<number>(3);
  const [minRating, setMinRating] = useState<number>(4);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const selectedBook = useMemo(
    () => books?.find((b) => b.book_id === bookId),
    [books, bookId],
  );

  const apiBase =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || window.location.origin
      : "";

  const handleCreate = async () => {
    if (!bookId) return;
    await createWidget.mutateAsync({
      book_id: bookId,
      style,
      theme,
      max_reviews: maxReviews,
      min_rating: minRating,
    });
  };

  const handleCopy = async (id: string, code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1800);
    } catch {
      /* no-op */
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Embed Review Widget</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate a copy-paste embed snippet to show your book&apos;s ratings and top
          reviews on any website.
        </p>
      </div>

      {/* Generator */}
      <Card className="p-6 space-y-5">
        <h2 className="text-lg font-semibold">Create a new widget</h2>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="widget-book">Book</Label>
            <select
              id="widget-book"
              className="w-full border rounded-md px-3 py-2 bg-background"
              value={bookId}
              onChange={(e) => setBookId(e.target.value)}
            >
              <option value="">— Select a book —</option>
              {(books ?? []).map((b) => (
                <option key={b.book_id} value={b.book_id}>
                  {b.title} ({b.review_count} reviews, {b.rating.toFixed(1)}★)
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label>Theme</Label>
            <div className="flex gap-2">
              {THEME_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setTheme(t.value)}
                  className={`px-3 py-1.5 rounded-md text-sm border ${
                    theme === t.value
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Style</Label>
          <div className="grid md:grid-cols-3 gap-3">
            {STYLE_OPTIONS.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setStyle(s.value)}
                className={`text-left p-3 rounded-md border ${
                  style === s.value
                    ? "border-primary ring-2 ring-primary/30"
                    : "border-border"
                }`}
              >
                <div className="font-medium text-sm">{s.label}</div>
                <div className="text-xs text-muted-foreground">{s.blurb}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="max-reviews">Max reviews</Label>
            <Input
              id="max-reviews"
              type="number"
              min={1}
              max={20}
              value={maxReviews}
              onChange={(e) => setMaxReviews(Number(e.target.value) || 1)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="min-rating">Minimum rating</Label>
            <Input
              id="min-rating"
              type="number"
              min={1}
              max={5}
              value={minRating}
              onChange={(e) => setMinRating(Number(e.target.value) || 1)}
            />
          </div>
        </div>

        {/* Preview */}
        <div className="space-y-2">
          <Label>Preview</Label>
          <div
            className={`border rounded-lg p-4 ${
              theme === "dark" ? "bg-neutral-900 text-neutral-100" : "bg-card"
            }`}
          >
            <div className="flex items-center gap-2 mb-3">
              <Star className="h-4 w-4 text-yellow-500" />
              <span className="font-semibold">
                {selectedBook ? selectedBook.rating.toFixed(1) : "4.4"} out of 5
              </span>
              <span className="text-sm text-muted-foreground">
                ({selectedBook?.review_count ?? 0} reviews)
              </span>
            </div>
            <div className="text-sm italic opacity-80">
              &quot;This is where top reviews from your book will appear in a{" "}
              {STYLE_OPTIONS.find((s) => s.value === style)?.label.toLowerCase()} layout.&quot;
            </div>
            <div className="text-[10px] text-right opacity-60 mt-3">
              Powered by SelfPublisherForge
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            onClick={handleCreate}
            disabled={!bookId || createWidget.isPending}
          >
            {createWidget.isPending ? "Creating…" : "Generate embed code"}
          </Button>
        </div>
      </Card>

      {/* Existing widgets */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your widgets</h2>
        {isLoading && (
          <div className="text-sm text-muted-foreground">Loading widgets…</div>
        )}
        {!isLoading && (widgets?.length ?? 0) === 0 && (
          <div className="text-sm text-muted-foreground">
            No widgets yet. Create one above.
          </div>
        )}
        {widgets?.map((w) => {
          const fullEmbed = w.embed_code.replace(
            'src="/api/',
            `src="${apiBase}/api/`,
          );
          return (
            <Card key={w.id} className="p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium text-sm">
                    Widget {w.id.slice(0, 8)} — {w.style.replace("_", " ")} / {w.theme}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Book {w.book_id.slice(0, 8)} · up to {w.max_reviews} reviews · min {w.min_rating}★
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopy(w.id, fullEmbed)}
                  >
                    <Copy className="h-3.5 w-3.5 mr-1" />
                    {copiedId === w.id ? "Copied!" : "Copy code"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => deleteWidget.mutate(w.id)}
                    disabled={deleteWidget.isPending}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
              <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                <code>{fullEmbed}</code>
              </pre>
              <div className="text-xs text-muted-foreground">
                Public JSON API:{" "}
                <code className="text-xs">
                  GET {apiBase}/api/v1/widgets/{w.id}/reviews
                </code>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
