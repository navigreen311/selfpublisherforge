"use client";

import { useEffect, useState } from "react";

import { useGenerateWidgetConfig } from "../hooks";

interface Props {
  bookId: string;
}

export function WidgetGenerator({ bookId }: Props) {
  const [style, setStyle] = useState<"compact" | "full" | "badge">("compact");
  const [theme, setTheme] = useState<"light" | "dark" | "auto">("light");
  const [maxReviews, setMaxReviews] = useState(3);
  const [copied, setCopied] = useState(false);

  const generate = useGenerateWidgetConfig();

  useEffect(() => {
    generate.mutate({
      book_id: bookId,
      style,
      theme,
      max_reviews: maxReviews,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId, style, theme, maxReviews]);

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // noop
    }
  };

  const embed = generate.data?.embed_code ?? "";
  const apiUrl = generate.data?.api_url ?? "";

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Embed Review Widget</h1>

      <div className="grid gap-4 rounded border p-4 md:grid-cols-3">
        <label className="text-sm">
          Style
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value as typeof style)}
            className="mt-1 w-full rounded border px-2 py-1 text-sm"
          >
            <option value="compact">Compact Card</option>
            <option value="full">Full Reviews</option>
            <option value="badge">Badge Only</option>
          </select>
        </label>
        <label className="text-sm">
          Theme
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as typeof theme)}
            className="mt-1 w-full rounded border px-2 py-1 text-sm"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="auto">Auto (matches site)</option>
          </select>
        </label>
        <label className="text-sm">
          Max Reviews
          <input
            type="number"
            min={0}
            max={10}
            value={maxReviews}
            onChange={(e) => setMaxReviews(parseInt(e.target.value || "0", 10))}
            className="mt-1 w-full rounded border px-2 py-1 text-sm"
          />
        </label>
      </div>

      <section>
        <h2 className="text-lg font-semibold">Embed Code</h2>
        <pre className="mt-2 overflow-x-auto rounded bg-gray-100 p-3 text-xs dark:bg-gray-800">
          <code>{embed || "Loading…"}</code>
        </pre>
        <button
          type="button"
          onClick={() => copy(embed)}
          disabled={!embed}
          className="mt-2 rounded bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-60"
        >
          {copied ? "Copied!" : "Copy Code"}
        </button>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Or use the API directly</h2>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          <code className="break-all">{apiUrl || "Loading…"}</code>
        </p>
        <button
          type="button"
          onClick={() => copy(apiUrl)}
          disabled={!apiUrl}
          className="mt-2 rounded border px-3 py-1.5 text-sm disabled:opacity-60"
        >
          Copy URL
        </button>
      </section>
    </div>
  );
}
