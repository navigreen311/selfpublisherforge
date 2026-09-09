export interface Webhook {
  id: string;
  url: string;
  description: string | null;
  events: string[];
  active: boolean;
  secret_preview: string;
  last_triggered_at: string | null;
  last_status_code: number | null;
  last_error: string | null;
  failure_count: number;
  created_at: string;
  updated_at: string;
}

export interface WebhookWithSecret extends Webhook {
  secret: string;
}

export interface WebhookCreatePayload {
  url: string;
  description?: string | null;
  events: string[];
  active?: boolean;
}

export interface WebhookUpdatePayload {
  url?: string;
  description?: string | null;
  events?: string[];
  active?: boolean;
}

export interface WebhookTestResult {
  status_code: number | null;
  response_body: string | null;
  latency_ms: number | null;
  delivered: boolean;
  error?: string | null;
}

export interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event_type: string;
  event_id: string | null;
  payload: Record<string, unknown>;
  status_code: number | null;
  response_body: string | null;
  latency_ms: number | null;
  attempt: number;
  delivered: boolean;
  error: string | null;
  created_at: string;
}

export interface EventCatalogGroup {
  label: string;
  events: { id: string; description: string }[];
}

export const EVENT_CATALOG: EventCatalogGroup[] = [
  {
    label: "Books & Content",
    events: [
      { id: "project.created", description: "A new project is created" },
      { id: "book.created", description: "A new book is created" },
      { id: "book.published", description: "A book is published to a distributor" },
      { id: "book.status_changed", description: "Book status changes" },
      { id: "book.exported", description: "A book file is exported" },
      { id: "book.deleted", description: "A book is deleted" },
    ],
  },
  {
    label: "Reviews & Analytics",
    events: [
      { id: "review.received", description: "New review detected" },
      { id: "review.negative", description: "Negative review (<=2 stars)" },
      { id: "analytics.daily", description: "Daily sales summary" },
      { id: "analytics.bsr_change", description: "Significant BSR movement" },
      { id: "royalty.imported", description: "Royalty data imported" },
    ],
  },
  {
    label: "Pipeline & Tasks",
    events: [
      { id: "pipeline.stage_changed", description: "Pipeline moves to new stage" },
      { id: "pipeline.completed", description: "Pipeline reaches final stage" },
      { id: "task.completed", description: "A pipeline task is completed" },
      { id: "task.overdue", description: "A task passes its due date" },
    ],
  },
  {
    label: "Generation & Export",
    events: [
      { id: "generation.completed", description: "AI generation job finishes" },
      { id: "batch.completed", description: "Batch factory job completes" },
      { id: "export.completed", description: "Export file is ready" },
    ],
  },
  {
    label: "Pricing & Marketing",
    events: [
      { id: "price.changed", description: "Price change executed" },
      { id: "campaign.launched", description: "Marketing campaign goes live" },
    ],
  },
];
