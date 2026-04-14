"use client";

import { useWebhookDeliveries } from "../hooks";
import type { WebhookDelivery } from "../types";

function StatusBadge({ d }: { d: WebhookDelivery }) {
  if (d.delivered) {
    return (
      <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-800">
        {d.status_code ?? 200} OK
      </span>
    );
  }
  return (
    <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-800">
      {d.status_code ?? "ERR"}
    </span>
  );
}

export function DeliveryLog({ webhookId }: { webhookId: string }) {
  const { data, isLoading, error, refetch } = useWebhookDeliveries(webhookId);

  if (isLoading) {
    return <p className="text-sm text-gray-500">Loading delivery log...</p>;
  }
  if (error) {
    return (
      <p className="text-sm text-red-600">Failed to load delivery log.</p>
    );
  }
  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-gray-500">
        <p>No deliveries yet.</p>
        <button
          className="mt-2 text-blue-600 underline"
          onClick={() => refetch()}
          type="button"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Recent Deliveries</h4>
        <button
          className="text-xs text-blue-600 underline"
          onClick={() => refetch()}
          type="button"
        >
          Refresh
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-600">
            <tr>
              <th className="px-3 py-2 text-left">Time</th>
              <th className="px-3 py-2 text-left">Event</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Latency</th>
              <th className="px-3 py-2 text-left">Attempt</th>
              <th className="px-3 py-2 text-left">Response</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((d) => (
              <tr key={d.id}>
                <td className="px-3 py-2 text-gray-700">
                  {new Date(d.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-2 font-mono text-xs">{d.event_type}</td>
                <td className="px-3 py-2">
                  <StatusBadge d={d} />
                </td>
                <td className="px-3 py-2 text-gray-600">
                  {d.latency_ms != null ? `${d.latency_ms} ms` : "-"}
                </td>
                <td className="px-3 py-2 text-gray-600">{d.attempt}</td>
                <td className="px-3 py-2 text-xs text-gray-500 max-w-xs truncate">
                  {d.error ?? d.response_body ?? ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
