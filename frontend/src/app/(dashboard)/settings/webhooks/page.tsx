"use client";

import { useState } from "react";

import { CreateWebhookModal } from "@/modules/webhooks/components/CreateWebhookModal";
import { WebhookEndpointList } from "@/modules/webhooks/components/WebhookEndpointList";

export default function WebhooksSettingsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Webhooks</h1>
        <p className="mt-1 text-sm text-gray-500">
          Webhooks send HTTP POST requests to your URL when events occur. Use
          them to integrate with Zapier, Make, Slack, or any automation tool.
        </p>
      </div>
      <WebhookEndpointList onOpenCreate={() => setCreateOpen(true)} />
      <CreateWebhookModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}
