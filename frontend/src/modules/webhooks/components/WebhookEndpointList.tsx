"use client";

import { useState } from "react";

import {
  useDeleteWebhookEndpoint,
  useTestWebhookEndpoint,
  useUpdateWebhookEndpoint,
  useWebhookEndpoints,
} from "../hooks";
import type { WebhookEndpoint } from "../types";

import { WebhookLogsPanel } from "./WebhookLogsPanel";

interface Props {
  onOpenCreate: () => void;
}

export function WebhookEndpointList({ onOpenCreate }: Props) {
  const { data, isLoading, isError } = useWebhookEndpoints();
  const update = useUpdateWebhookEndpoint();
  const remove = useDeleteWebhookEndpoint();
  const test = useTestWebhookEndpoint();
  const [testResult, setTestResult] = useState<
    { id: string; status: number | null; delivered: boolean } | null
  >(null);
  const [logsEndpointId, setLogsEndpointId] = useState<string | null>(null);

  if (isLoading) return <div>Loading webhooks…</div>;
  if (isError) return <div>Failed to load webhooks.</div>;

  const endpoints: WebhookEndpoint[] = data ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Webhooks</h2>
        <button
          type="button"
          onClick={onOpenCreate}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
        >
          + Add Webhook Endpoint
        </button>
      </div>

      {endpoints.length === 0 && (
        <p className="text-sm text-gray-500">
          No webhooks yet. Add an endpoint to receive event notifications.
        </p>
      )}

      <ul className="space-y-3">
        {endpoints.map((ep) => (
          <li
            key={ep.id}
            className="rounded border border-gray-200 p-4 dark:border-gray-700"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block size-2 rounded-full ${
                      ep.active ? "bg-green-500" : "bg-gray-400"
                    }`}
                    aria-hidden
                  />
                  <span className="font-medium">
                    {ep.description || "(no description)"}
                  </span>
                </div>
                <p className="mt-1 truncate text-sm text-gray-600 dark:text-gray-400">
                  {ep.url}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  Events: {ep.events.join(", ")}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  Secret: {ep.signing_secret_masked}
                </p>
                {ep.last_triggered_at && (
                  <p className="mt-1 text-xs text-gray-500">
                    Last triggered: {new Date(ep.last_triggered_at).toLocaleString()}{" "}
                    {ep.last_status_code && `(${ep.last_status_code})`}
                  </p>
                )}
                {testResult?.id === ep.id && (
                  <p
                    className={`mt-1 text-xs ${
                      testResult.delivered ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    Test result: {testResult.status ?? "—"}{" "}
                    {testResult.delivered ? "delivered" : "failed"}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded border px-2 py-1 text-xs"
                  onClick={async () => {
                    const res = await test.mutateAsync(ep.id);
                    setTestResult({
                      id: ep.id,
                      status: res.status_code,
                      delivered: res.delivered,
                    });
                  }}
                  disabled={test.isPending}
                >
                  Test
                </button>
                <button
                  type="button"
                  className="rounded border px-2 py-1 text-xs"
                  onClick={() =>
                    setLogsEndpointId(logsEndpointId === ep.id ? null : ep.id)
                  }
                >
                  {logsEndpointId === ep.id ? "Hide Logs" : "View Logs"}
                </button>
                <button
                  type="button"
                  className="rounded border px-2 py-1 text-xs"
                  onClick={() =>
                    update.mutate({
                      id: ep.id,
                      payload: { active: !ep.active },
                    })
                  }
                >
                  {ep.active ? "Disable" : "Enable"}
                </button>
                <button
                  type="button"
                  className="rounded border border-red-300 px-2 py-1 text-xs text-red-600"
                  onClick={() => {
                    if (confirm("Delete this webhook endpoint?")) {
                      remove.mutate(ep.id);
                    }
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
            {logsEndpointId === ep.id && (
              <div className="mt-3 border-t border-gray-200 pt-3 dark:border-gray-700">
                <WebhookLogsPanel endpointId={ep.id} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
