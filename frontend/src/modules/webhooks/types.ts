export interface WebhookEndpoint {
  id: string;
  url: string;
  description: string | null;
  events: string[];
  active: boolean;
  last_triggered_at: string | null;
  last_status_code: number | null;
  created_at: string;
  signing_secret_masked: string;
}

export interface WebhookEndpointCreated extends WebhookEndpoint {
  signing_secret: string;
}

export interface WebhookEndpointCreatePayload {
  url: string;
  description?: string;
  events: string[];
  active?: boolean;
}

export interface WebhookEndpointUpdatePayload {
  url?: string;
  description?: string;
  events?: string[];
  active?: boolean;
}

export interface WebhookTestResponse {
  status_code: number | null;
  response_body: string | null;
  latency_ms: number | null;
  delivered: boolean;
}

export interface WebhookLog {
  id: string;
  endpoint_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  status_code: number | null;
  response_body: string | null;
  latency_ms: number | null;
  retries: number;
  delivered: boolean;
  created_at: string;
}

export interface EventCatalogEntry {
  type: string;
  category: string;
  description: string;
}
