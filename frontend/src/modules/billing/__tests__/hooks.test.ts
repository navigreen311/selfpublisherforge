import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// ---------------------------------------------------------------------------
// Mock window.location for redirect tests
// ---------------------------------------------------------------------------

const originalLocation = window.location;

beforeAll(() => {
  Object.defineProperty(window, "location", {
    writable: true,
    value: { ...originalLocation, href: "" },
  });
});

afterAll(() => {
  Object.defineProperty(window, "location", {
    writable: true,
    value: originalLocation,
  });
});

// ---------------------------------------------------------------------------
// Import hooks under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import {
  usePlans,
  useSubscription,
  useUsage,
  useInvoices,
  useCreateCheckout,
  useCreatePortal,
  billingKeys,
} from "../hooks";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
}

// ---------------------------------------------------------------------------
// Tests: billingKeys (query key structure)
// ---------------------------------------------------------------------------

describe("billingKeys", () => {
  it("has correct 'all' key", () => {
    expect(billingKeys.all).toEqual(["billing"]);
  });

  it("has correct 'plans' key", () => {
    expect(billingKeys.plans()).toEqual(["billing", "plans"]);
  });

  it("has correct 'subscription' key", () => {
    expect(billingKeys.subscription()).toEqual(["billing", "subscription"]);
  });

  it("has correct 'usage' key", () => {
    expect(billingKeys.usage()).toEqual(["billing", "usage"]);
  });

  it("has correct 'invoices' key", () => {
    expect(billingKeys.invoices()).toEqual(["billing", "invoices"]);
  });
});

// ---------------------------------------------------------------------------
// Tests: usePlans
// ---------------------------------------------------------------------------

describe("usePlans", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches plans from /api/v1/billing/plans", async () => {
    const mockPlans = [
      {
        tier: "free",
        name: "Free",
        price_monthly: 0,
        description: "Get started",
        max_projects: 1,
        ai_generations_per_day: 5,
        features: ["Basic editing"],
        highlight: false,
      },
      {
        tier: "pro",
        name: "Pro",
        price_monthly: 1999,
        description: "For professionals",
        max_projects: null,
        ai_generations_per_day: 100,
        features: ["Advanced editing", "AI writing"],
        highlight: true,
      },
    ];
    mockGet.mockResolvedValue({ data: mockPlans });

    const { result } = renderHook(() => usePlans(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/billing/plans");
    expect(result.current.data).toEqual(mockPlans);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Failed to fetch plans"));

    const { result } = renderHook(() => usePlans(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useSubscription
// ---------------------------------------------------------------------------

describe("useSubscription", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches subscription from /api/v1/billing/subscription", async () => {
    const mockSubscription = {
      org_id: "org-123",
      plan_tier: "pro",
      subscription_status: "active",
      stripe_subscription_id: "sub_abc123",
      stripe_customer_id: "cus_xyz789",
      current_period_start: "2025-01-01T00:00:00Z",
      current_period_end: "2025-02-01T00:00:00Z",
      cancel_at_period_end: false,
    };
    mockGet.mockResolvedValue({ data: mockSubscription });

    const { result } = renderHook(() => useSubscription(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/billing/subscription");
    expect(result.current.data).toEqual(mockSubscription);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Subscription fetch failed"));

    const { result } = renderHook(() => useSubscription(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useUsage
// ---------------------------------------------------------------------------

describe("useUsage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches usage stats from /api/v1/billing/usage", async () => {
    const mockUsage = {
      org_id: "org-123",
      plan_tier: "pro",
      projects_used: 3,
      projects_limit: null,
      ai_generations_used_today: 15,
      ai_generations_daily_limit: 100,
      current_period_start: "2025-01-01T00:00:00Z",
      current_period_end: "2025-02-01T00:00:00Z",
    };
    mockGet.mockResolvedValue({ data: mockUsage });

    const { result } = renderHook(() => useUsage(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/billing/usage");
    expect(result.current.data).toEqual(mockUsage);
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Usage fetch failed"));

    const { result } = renderHook(() => useUsage(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useInvoices
// ---------------------------------------------------------------------------

describe("useInvoices", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches invoices from /api/v1/billing/invoices with default limit", async () => {
    const mockInvoices = {
      invoices: [
        {
          id: "inv_1",
          number: "INV-001",
          status: "paid",
          amount_due: 1999,
          amount_paid: 1999,
          currency: "usd",
          created: "2025-01-01T00:00:00Z",
          period_start: "2025-01-01T00:00:00Z",
          period_end: "2025-02-01T00:00:00Z",
          hosted_invoice_url: "https://stripe.com/inv/1",
          invoice_pdf: "https://stripe.com/inv/1.pdf",
        },
      ],
      has_more: false,
    };
    mockGet.mockResolvedValue({ data: mockInvoices });

    const { result } = renderHook(() => useInvoices(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/billing/invoices", {
      params: { limit: 10 },
    });
    expect(result.current.data).toEqual(mockInvoices);
  });

  it("passes custom limit param", async () => {
    mockGet.mockResolvedValue({ data: { invoices: [], has_more: false } });

    const { result } = renderHook(() => useInvoices(25), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/billing/invoices", {
      params: { limit: 25 },
    });
  });

  it("handles fetch error", async () => {
    mockGet.mockRejectedValue(new Error("Invoices fetch failed"));

    const { result } = renderHook(() => useInvoices(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Tests: useCreateCheckout
// ---------------------------------------------------------------------------

describe("useCreateCheckout", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.location.href = "";
  });

  it("posts to /api/v1/billing/subscribe", async () => {
    const mockCheckout = {
      checkout_url: "https://checkout.stripe.com/session123",
      session_id: "cs_test_123",
    };
    mockPost.mockResolvedValue({ data: mockCheckout });

    const { result } = renderHook(() => useCreateCheckout(), {
      wrapper: createWrapper(),
    });

    const payload = {
      plan_tier: "pro" as const,
      success_url: "https://app.com/success",
      cancel_url: "https://app.com/cancel",
    };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/billing/subscribe",
      payload
    );
    expect(result.current.data).toEqual(mockCheckout);
  });

  it("redirects to checkout_url on success", async () => {
    const mockCheckout = {
      checkout_url: "https://checkout.stripe.com/redirect",
      session_id: "cs_test_456",
    };
    mockPost.mockResolvedValue({ data: mockCheckout });

    const { result } = renderHook(() => useCreateCheckout(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ plan_tier: "starter" });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(window.location.href).toBe("https://checkout.stripe.com/redirect");
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Checkout failed"));

    const { result } = renderHook(() => useCreateCheckout(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ plan_tier: "pro" });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Checkout failed");
  });
});

// ---------------------------------------------------------------------------
// Tests: useCreatePortal
// ---------------------------------------------------------------------------

describe("useCreatePortal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.location.href = "";
  });

  it("posts to /api/v1/billing/portal", async () => {
    const mockPortal = {
      portal_url: "https://billing.stripe.com/portal123",
    };
    mockPost.mockResolvedValue({ data: mockPortal });

    const { result } = renderHook(() => useCreatePortal(), {
      wrapper: createWrapper(),
    });

    const payload = { return_url: "https://app.com/settings" };

    result.current.mutate(payload);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/billing/portal", payload);
    expect(result.current.data).toEqual(mockPortal);
  });

  it("sends empty object when no body is provided", async () => {
    const mockPortal = {
      portal_url: "https://billing.stripe.com/portal456",
    };
    mockPost.mockResolvedValue({ data: mockPortal });

    const { result } = renderHook(() => useCreatePortal(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(undefined);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/billing/portal", {});
  });

  it("redirects to portal_url on success", async () => {
    const mockPortal = {
      portal_url: "https://billing.stripe.com/portal-redirect",
    };
    mockPost.mockResolvedValue({ data: mockPortal });

    const { result } = renderHook(() => useCreatePortal(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(undefined);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(window.location.href).toBe(
      "https://billing.stripe.com/portal-redirect"
    );
  });

  it("handles error on failure", async () => {
    mockPost.mockRejectedValue(new Error("Portal creation failed"));

    const { result } = renderHook(() => useCreatePortal(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(undefined);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Portal creation failed");
  });
});
