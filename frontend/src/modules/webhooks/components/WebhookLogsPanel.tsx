"use client";

import { useRetryWebhookLog, useWebhookLogs } from "../hooks";

export function WebhookLogsPanel({ endpointId }: { endpointId: string }) {
  const { data, isLoading } = useWebhookLogs(endpointId);
  const retry = useRetryWebhookLog();

  if (isLoading) return <div className="text-sm">Loading logs…</div>;
  const logs = data ?? [];
  if (logs.length === 0)
    return <div className="text-sm text-gray-500">No deliveries yet.</div>;

  return (
    <table className="w-full text-left text-xs">
      <thead>
        <tr className="text-gray-500">
          <th className="py-1">Time</th>
          <th>Event</th>
          <th>Status</th>
          <th>Retries</th>
          <th>Delivered</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {logs.map((log) => (
          <tr key={log.id} className="border-t border-gray-100 dark:border-gray-800">
            <td className="py-1">{new Date(log.created_at).toLocaleString()}</td>
            <td>{log.event_type}</td>
            <td>{log.status_code ?? "—"}</td>
            <td>{log.retries}</td>
            <td>{log.delivered ? "yes" : "no"}</td>
            <td>
              <button
                type="button"
                className="rounded border px-2 py-0.5"
                onClick={() => retry.mutate(log.id)}
                disabled={retry.isPending}
              >
                Retry
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
