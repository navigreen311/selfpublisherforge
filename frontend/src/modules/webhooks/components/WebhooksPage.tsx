"use client";

import { useState } from "react";
import {
  useCreateWebhook,
  useDeleteWebhook,
  useRotateSecret,
  useTestWebhook,
  useUpdateWebhook,
  useWebhooks,
} from "../hooks";
import type { Webhook, WebhookTestResult } from "../types";
import { WebhookForm } from "./WebhookForm";
import { DeliveryLog } from "./DeliveryLog";

type Mode =
  | { kind: "list" }
  | { kind: "create" }
  | { kind: "edit"; webhook: Webhook }
  | { kind: "logs"; webhook: Webhook };

export function WebhooksPage() {
  const { data: webhooks, isLoading, error } = useWebhooks();
  const createMutation = useCreateWebhook();
  const updateMutation = useUpdateWebhook();
  const deleteMutation = useDeleteWebhook();
  const testMutation = useTestWebhook();
  const rotateMutation = useRotateSecret();

  const [mode, setMode] = useState<Mode>({ kind: "list" });
  const [newSecret, setNewSecret] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{
    id: string;
    result: WebhookTestResult;
  } | null>(null);

  const resetToList = () => {
    setMode({ kind: "list" });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-8 w-1/3 bg-gray-200 rounded" />
        <div className="h-32 bg-gray-100 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-red-600">Failed to load webhooks.</p>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold">Webhooks</h1>
        <p className="text-sm text-gray-500">
          Webhooks send HTTP POST requests to your URL when events occur.
          Payloads are signed with HMAC-SHA256 using your endpoint secret —
          verify the <code className="rounded bg-gray-100 px-1">X-Webhook-Signature</code>{" "}
          header.
        </p>
      </header>

      {newSecret ? (
        <div className="rounded border border-amber-300 bg-amber-50 p-4 text-sm">
          <p className="font-semibold text-amber-900">
            Copy your signing secret now — it will not be shown again.
          </p>
          <pre className="mt-2 overflow-x-auto rounded bg-white p-2 font-mono text-xs">
            {newSecret}
          </pre>
          <button
            className="mt-2 text-xs text-amber-900 underline"
            onClick={() => setNewSecret(null)}
          >
            Dismiss
          </button>
        </div>
      ) : null}

      {mode.kind === "list" ? (
        <>
          <div>
            <button
              type="button"
              onClick={() => setMode({ kind: "create" })}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white"
            >
              + Add Webhook Endpoint
            </button>
          </div>

          <div className="space-y-3">
            {(webhooks ?? []).length === 0 ? (
              <p className="text-sm text-gray-500">
                No webhooks yet. Click{" "}
                <em>Add Webhook Endpoint</em> to create one.
              </p>
            ) : (
              (webhooks ?? []).map((w) => (
                <div
                  key={w.id}
                  className="rounded border border-gray-200 bg-white p-4 space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={
                            w.active
                              ? "inline-block h-2 w-2 rounded-full bg-green-500"
                              : "inline-block h-2 w-2 rounded-full bg-gray-400"
                          }
                        />
                        <h3 className="font-semibold truncate">
                          {w.description || w.url}
                        </h3>
                      </div>
                      <p className="mt-1 break-all font-mono text-xs text-gray-600">
                        {w.url}
                      </p>
                      <p className="mt-1 text-xs text-gray-500">
                        Events:{" "}
                        <span className="font-mono">
                          {w.events.join(", ")}
                        </span>
                      </p>
                      <p className="mt-1 text-xs text-gray-500">
                        Secret:{" "}
                        <span className="font-mono">{w.secret_preview}</span>
                      </p>
                      <p className="mt-1 text-xs text-gray-500">
                        Last triggered:{" "}
                        {w.last_triggered_at
                          ? `${new Date(w.last_triggered_at).toLocaleString()} (${w.last_status_code ?? "—"})`
                          : "never"}
                        {w.failure_count > 0 ? (
                          <span className="ml-2 text-red-600">
                            {w.failure_count} failure
                            {w.failure_count === 1 ? "" : "s"}
                          </span>
                        ) : null}
                      </p>
                    </div>
                  </div>

                  {testResult && testResult.id === w.id ? (
                    <div
                      className={`rounded p-2 text-xs ${
                        testResult.result.delivered
                          ? "bg-green-50 text-green-800"
                          : "bg-red-50 text-red-800"
                      }`}
                    >
                      Test: status={testResult.result.status_code ?? "n/a"},
                      latency={testResult.result.latency_ms ?? "?"}ms
                      {testResult.result.error
                        ? ` — ${testResult.result.error}`
                        : ""}
                    </div>
                  ) : null}

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded border border-gray-300 px-3 py-1 text-xs"
                      onClick={() => setMode({ kind: "edit", webhook: w })}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="rounded border border-gray-300 px-3 py-1 text-xs disabled:opacity-50"
                      disabled={testMutation.isPending}
                      onClick={async () => {
                        const result = await testMutation.mutateAsync(w.id);
                        setTestResult({ id: w.id, result });
                      }}
                    >
                      {testMutation.isPending ? "Testing..." : "Test"}
                    </button>
                    <button
                      type="button"
                      className="rounded border border-gray-300 px-3 py-1 text-xs"
                      onClick={() => setMode({ kind: "logs", webhook: w })}
                    >
                      View Logs
                    </button>
                    <button
                      type="button"
                      className="rounded border border-gray-300 px-3 py-1 text-xs"
                      onClick={() =>
                        updateMutation.mutate({
                          id: w.id,
                          body: { active: !w.active },
                        })
                      }
                    >
                      {w.active ? "Disable" : "Enable"}
                    </button>
                    <button
                      type="button"
                      className="rounded border border-gray-300 px-3 py-1 text-xs"
                      onClick={async () => {
                        if (
                          !confirm(
                            "Rotate signing secret? Existing consumers will need to be updated."
                          )
                        )
                          return;
                        const res = await rotateMutation.mutateAsync(w.id);
                        setNewSecret(res.secret);
                      }}
                    >
                      Rotate Secret
                    </button>
                    <button
                      type="button"
                      className="rounded border border-red-300 px-3 py-1 text-xs text-red-700"
                      onClick={() => {
                        if (confirm("Delete this webhook?"))
                          deleteMutation.mutate(w.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      ) : null}

      {mode.kind === "create" ? (
        <div className="rounded border border-gray-200 bg-white p-4">
          <h2 className="mb-4 text-lg font-semibold">Add Webhook</h2>
          <WebhookForm
            busy={createMutation.isPending}
            onCancel={resetToList}
            onSubmit={async (payload) => {
              const result = await createMutation.mutateAsync(payload);
              setNewSecret(result.secret);
              resetToList();
            }}
          />
        </div>
      ) : null}

      {mode.kind === "edit" ? (
        <div className="rounded border border-gray-200 bg-white p-4">
          <h2 className="mb-4 text-lg font-semibold">Edit Webhook</h2>
          <WebhookForm
            submitLabel="Save Changes"
            initialUrl={mode.webhook.url}
            initialDescription={mode.webhook.description ?? ""}
            initialEvents={mode.webhook.events}
            initialActive={mode.webhook.active}
            busy={updateMutation.isPending}
            onCancel={resetToList}
            onSubmit={async (payload) => {
              await updateMutation.mutateAsync({
                id: mode.webhook.id,
                body: payload,
              });
              resetToList();
            }}
          />
        </div>
      ) : null}

      {mode.kind === "logs" ? (
        <div className="rounded border border-gray-200 bg-white p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Delivery Log — {mode.webhook.description || mode.webhook.url}
            </h2>
            <button
              type="button"
              className="text-sm text-blue-600 underline"
              onClick={resetToList}
            >
              Back
            </button>
          </div>
          <DeliveryLog webhookId={mode.webhook.id} />
        </div>
      ) : null}
    </div>
  );
}
