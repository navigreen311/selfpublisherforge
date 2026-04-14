import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

// Import after the mock so the hooks see the mocked api module.
import { api } from "@/lib/api";

import {
  useCreateWebhookEndpoint,
  useWebhookEndpoints,
  useWebhookEventCatalog,
} from "../hooks";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client: qc }, children);
}

describe("webhooks hooks", () => {
  beforeEach(() => jest.clearAllMocks());

  it("useWebhookEndpoints calls GET /api/v1/webhooks", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });
    const { result } = renderHook(() => useWebhookEndpoints(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledWith("/api/v1/webhooks");
  });

  it("useWebhookEventCatalog calls GET /api/v1/webhooks/events", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce({ data: [] });
    const { result } = renderHook(() => useWebhookEventCatalog(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledWith("/api/v1/webhooks/events");
  });

  it("useCreateWebhookEndpoint posts payload to webhooks endpoint", async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({
      data: {
        id: "x",
        url: "https://example.com/hook",
        description: null,
        events: ["book.created"],
        active: true,
        signing_secret: "whsec_abc",
        signing_secret_masked: "whsec_***...abc",
        created_at: "2026-04-13T00:00:00Z",
        last_triggered_at: null,
        last_status_code: null,
      },
    });
    const { result } = renderHook(() => useCreateWebhookEndpoint(), { wrapper });
    const created = await result.current.mutateAsync({
      url: "https://example.com/hook",
      events: ["book.created"],
    });
    expect(created.signing_secret).toBe("whsec_abc");
    expect(api.post).toHaveBeenCalledWith(
      "/api/v1/webhooks",
      expect.objectContaining({
        url: "https://example.com/hook",
        events: ["book.created"],
      }),
    );
  });
});
