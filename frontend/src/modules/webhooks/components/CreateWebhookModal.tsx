"use client";

import { useMemo, useState } from "react";

import { useCreateWebhookEndpoint, useWebhookEventCatalog } from "../hooks";
import type { WebhookEndpointCreated } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CreateWebhookModal({ open, onClose }: Props) {
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [created, setCreated] = useState<WebhookEndpointCreated | null>(null);

  const { data: catalog } = useWebhookEventCatalog();
  const createMut = useCreateWebhookEndpoint();

  const grouped = useMemo(() => {
    const out: Record<string, { type: string; description: string }[]> = {};
    (catalog ?? []).forEach((e) => {
      (out[e.category] ||= []).push({ type: e.type, description: e.description });
    });
    return out;
  }, [catalog]);

  if (!open) return null;

  const toggle = (t: string) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url || selected.size === 0) return;
    const res = await createMut.mutateAsync({
      url,
      description: description || undefined,
      events: Array.from(selected),
    });
    setCreated(res);
  };

  const close = () => {
    setUrl("");
    setDescription("");
    setSelected(new Set());
    setCreated(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded bg-white p-6 shadow-lg dark:bg-gray-900">
        {created ? (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Webhook created</h3>
            <p className="text-sm">
              Copy and save this signing secret — it will not be shown again:
            </p>
            <code className="block break-all rounded bg-gray-100 p-2 text-xs dark:bg-gray-800">
              {created.signing_secret}
            </code>
            <button
              type="button"
              onClick={close}
              className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <h3 className="text-lg font-semibold">Add Webhook</h3>
            <label className="block text-sm">
              Endpoint URL
              <input
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
                placeholder="https://hooks.zapier.com/…"
              />
            </label>
            <label className="block text-sm">
              Description
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              />
            </label>

            <div>
              <p className="text-sm font-medium">Events to subscribe</p>
              <div className="mt-2 space-y-3">
                {Object.entries(grouped).map(([cat, items]) => (
                  <div key={cat}>
                    <p className="text-xs font-semibold uppercase text-gray-500">
                      {cat}
                    </p>
                    <div className="mt-1 space-y-1">
                      {items.map((i) => (
                        <label key={i.type} className="flex items-start gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={selected.has(i.type)}
                            onChange={() => toggle(i.type)}
                          />
                          <span>
                            <code className="text-xs">{i.type}</code>{" "}
                            <span className="text-gray-500">— {i.description}</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={close}
                className="rounded border px-3 py-1.5 text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-60"
                disabled={createMut.isPending || selected.size === 0 || !url}
              >
                Create Webhook
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
