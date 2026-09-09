"use client";

import { useState } from "react";
import { EVENT_CATALOG } from "../types";
import type { WebhookCreatePayload } from "../types";

interface WebhookFormProps {
  initialUrl?: string;
  initialDescription?: string;
  initialEvents?: string[];
  initialActive?: boolean;
  submitLabel?: string;
  onCancel: () => void;
  onSubmit: (payload: WebhookCreatePayload) => Promise<void> | void;
  busy?: boolean;
}

export function WebhookForm({
  initialUrl = "",
  initialDescription = "",
  initialEvents = [],
  initialActive = true,
  submitLabel = "Create Webhook",
  onCancel,
  onSubmit,
  busy = false,
}: WebhookFormProps) {
  const [url, setUrl] = useState(initialUrl);
  const [description, setDescription] = useState(initialDescription);
  const [events, setEvents] = useState<Set<string>>(new Set(initialEvents));
  const [active, setActive] = useState(initialActive);
  const [error, setError] = useState<string | null>(null);

  const toggleEvent = (id: string) => {
    setEvents((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!url.trim()) {
      setError("Endpoint URL is required");
      return;
    }
    if (events.size === 0) {
      setError("Select at least one event");
      return;
    }
    try {
      await onSubmit({
        url: url.trim(),
        description: description.trim() || null,
        events: Array.from(events),
        active,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save webhook");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Endpoint URL <span className="text-red-500">*</span>
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://hooks.zapier.com/..."
          className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Zapier - notify when book published"
          className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Events to subscribe
        </label>
        <div className="space-y-3 max-h-80 overflow-y-auto rounded border border-gray-200 p-3">
          {EVENT_CATALOG.map((group) => (
            <div key={group.label}>
              <div className="text-xs font-semibold uppercase text-gray-500 mb-1">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.events.map((evt) => (
                  <label
                    key={evt.id}
                    className="flex items-start gap-2 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={events.has(evt.id)}
                      onChange={() => toggleEvent(evt.id)}
                      className="mt-0.5"
                    />
                    <span className="font-mono text-xs text-gray-800">
                      {evt.id}
                    </span>
                    <span className="text-gray-500">— {evt.description}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={active}
          onChange={(e) => setActive(e.target.checked)}
        />
        <span>Active</span>
      </label>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-gray-300 bg-white px-4 py-2 text-sm"
          disabled={busy}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-60"
          disabled={busy}
        >
          {busy ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
