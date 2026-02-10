import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Mocks — must be set up before component imports ──────────────────────

const mockCheckoutMutate = jest.fn();
const mockPortalMutate = jest.fn();

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => "/settings/billing",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock sonner toast
const mockToastSuccess = jest.fn();
const mockToastInfo = jest.fn();
jest.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    info: (...args: unknown[]) => mockToastInfo(...args),
  },
}));

// Mock billing hooks
const mockUsePlans = jest.fn();
const mockUseSubscription = jest.fn();
const mockUseUsage = jest.fn();
const mockUseInvoices = jest.fn();
const mockUseCreateCheckout = jest.fn();
const mockUseCreatePortal = jest.fn();

jest.mock("@/modules/billing/hooks", () => ({
  usePlans: (...args: unknown[]) => mockUsePlans(...args),
  useSubscription: (...args: unknown[]) => mockUseSubscription(...args),
  useUsage: (...args: unknown[]) => mockUseUsage(...args),
  useInvoices: (...args: unknown[]) => mockUseInvoices(...args),
  useCreateCheckout: (...args: unknown[]) => mockUseCreateCheckout(...args),
  useCreatePortal: (...args: unknown[]) => mockUseCreatePortal(...args),
}));

// Mock billing components to simplify testing
jest.mock("@/modules/billing/components/PlanCard", () => ({
  PlanCard: ({
    plan,
    currentTier,
    onSelect,
    isLoading,
  }: {
    plan: { tier: string; name: string; price_monthly: number };
    currentTier: string;
    onSelect: (tier: string) => void;
    isLoading?: boolean;
  }) => (
    <div data-testid={`plan-card-${plan.tier}`}>
      <span>{plan.name}</span>
      <button
        onClick={() => onSelect(plan.tier)}
        disabled={plan.tier === currentTier || isLoading}
      >
        {plan.tier === currentTier
          ? "Current Plan"
          : plan.tier === "enterprise"
            ? "Contact Sales"
            : plan.price_monthly === 0
              ? "Downgrade to Free"
              : "Upgrade"}
      </button>
    </div>
  ),
}));

jest.mock("@/modules/billing/components/UsageMeter", () => ({
  UsageMeter: ({
    label,
    used,
    limit,
  }: {
    label: string;
    used: number;
    limit: number | null;
  }) => (
    <div data-testid={`usage-meter-${label}`}>
      <span>{label}</span>
      <span>
        {used} / {limit === null ? "Unlimited" : limit}
      </span>
    </div>
  ),
}));

jest.mock("@/modules/billing/components/InvoiceList", () => ({
  InvoiceList: ({
    invoices,
    isLoading,
  }: {
    invoices: Array<{ id: string; number: string | null; amount_due: number; status: string }>;
    isLoading?: boolean;
  }) => (
    <div data-testid="invoice-list">
      {isLoading ? (
        <span>Loading invoices...</span>
      ) : invoices.length === 0 ? (
        <span>No invoices found.</span>
      ) : (
        invoices.map((inv) => (
          <div key={inv.id} data-testid={`invoice-${inv.id}`}>
            <span>{inv.number || inv.id}</span>
            <span>${(inv.amount_due / 100).toFixed(2)}</span>
            <span>{inv.status}</span>
          </div>
        ))
      )}
    </div>
  ),
}));

// ── Import after mocks ──────────────────────────────────────────────────

import BillingSettingsPage from "../../settings/billing/page";

// ── Test Data ────────────────────────────────────────────────────────────

const mockPlans = [
  {
    tier: "free",
    name: "Free",
    price_monthly: 0,
    description: "Get started with the basics",
    max_projects: 3,
    ai_generations_per_day: 10,
    features: ["3 projects", "Basic analytics"],
    highlight: false,
  },
  {
    tier: "starter",
    name: "Starter",
    price_monthly: 1900,
    description: "For growing authors",
    max_projects: 10,
    ai_generations_per_day: 50,
    features: ["10 projects", "Advanced analytics"],
    highlight: false,
  },
  {
    tier: "pro",
    name: "Pro",
    price_monthly: 4900,
    description: "For professional publishers",
    max_projects: null,
    ai_generations_per_day: 200,
    features: ["Unlimited projects", "Full analytics"],
    highlight: true,
  },
  {
    tier: "business",
    name: "Business",
    price_monthly: 9900,
    description: "For publishing teams",
    max_projects: null,
    ai_generations_per_day: 500,
    features: ["Unlimited projects", "Team management"],
    highlight: false,
  },
  {
    tier: "enterprise",
    name: "Enterprise",
    price_monthly: 0,
    description: "Custom solutions",
    max_projects: null,
    ai_generations_per_day: 9999,
    features: ["Custom", "Dedicated support"],
    highlight: false,
  },
];

const mockSubscription = {
  org_id: "org-1",
  plan_tier: "starter" as const,
  subscription_status: "active",
  stripe_subscription_id: "sub_test123",
  stripe_customer_id: "cus_test123",
  current_period_start: "2025-01-01T00:00:00Z",
  current_period_end: "2025-02-01T00:00:00Z",
  cancel_at_period_end: false,
};

const mockUsageData = {
  org_id: "org-1",
  plan_tier: "starter" as const,
  projects_used: 5,
  projects_limit: 10,
  ai_generations_used_today: 20,
  ai_generations_daily_limit: 50,
  current_period_start: "2025-01-01T00:00:00Z",
  current_period_end: "2025-02-01T00:00:00Z",
};

const mockInvoiceData = {
  invoices: [
    {
      id: "inv_1",
      number: "INV-001",
      status: "paid",
      amount_due: 1900,
      amount_paid: 1900,
      currency: "usd",
      created: "2025-01-01T00:00:00Z",
      period_start: "2025-01-01T00:00:00Z",
      period_end: "2025-02-01T00:00:00Z",
      hosted_invoice_url: "https://stripe.com/inv1",
      invoice_pdf: "https://stripe.com/inv1.pdf",
    },
    {
      id: "inv_2",
      number: "INV-002",
      status: "paid",
      amount_due: 1900,
      amount_paid: 1900,
      currency: "usd",
      created: "2024-12-01T00:00:00Z",
      period_start: "2024-12-01T00:00:00Z",
      period_end: "2025-01-01T00:00:00Z",
      hosted_invoice_url: "https://stripe.com/inv2",
      invoice_pdf: "https://stripe.com/inv2.pdf",
    },
  ],
  has_more: false,
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("BillingSettingsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default: return full data for all hooks
    mockUsePlans.mockReturnValue({
      data: mockPlans,
      isLoading: false,
    });
    mockUseSubscription.mockReturnValue({
      data: mockSubscription,
      isLoading: false,
    });
    mockUseUsage.mockReturnValue({
      data: mockUsageData,
      isLoading: false,
    });
    mockUseInvoices.mockReturnValue({
      data: mockInvoiceData,
      isLoading: false,
    });
    mockUseCreateCheckout.mockReturnValue({
      mutate: mockCheckoutMutate,
      isPending: false,
    });
    mockUseCreatePortal.mockReturnValue({
      mutate: mockPortalMutate,
      isPending: false,
    });
  });

  // 1. Renders current plan info
  it("renders current plan info", () => {
    render(<BillingSettingsPage />);

    expect(screen.getByText("Billing & Subscription")).toBeInTheDocument();
    expect(
      screen.getByText("Manage your plan, monitor usage, and view invoices.")
    ).toBeInTheDocument();

    // Current plan section
    expect(screen.getByText(/Current Plan:/)).toBeInTheDocument();
    expect(screen.getByText("starter")).toBeInTheDocument();

    // Subscription status
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  // 2. Shows billing history
  it("shows billing history (invoice list)", () => {
    render(<BillingSettingsPage />);

    expect(screen.getByText("Invoice History")).toBeInTheDocument();
    expect(screen.getByTestId("invoice-list")).toBeInTheDocument();

    // Invoice items rendered
    expect(screen.getByTestId("invoice-inv_1")).toBeInTheDocument();
    expect(screen.getByTestId("invoice-inv_2")).toBeInTheDocument();
    expect(screen.getByText("INV-001")).toBeInTheDocument();
    expect(screen.getByText("INV-002")).toBeInTheDocument();
  });

  // 3. Upgrade/downgrade buttons
  it("renders plan cards with upgrade/downgrade buttons", () => {
    render(<BillingSettingsPage />);

    expect(screen.getByText("Available Plans")).toBeInTheDocument();

    // All plan cards are rendered
    expect(screen.getByTestId("plan-card-free")).toBeInTheDocument();
    expect(screen.getByTestId("plan-card-starter")).toBeInTheDocument();
    expect(screen.getByTestId("plan-card-pro")).toBeInTheDocument();
    expect(screen.getByTestId("plan-card-business")).toBeInTheDocument();
    expect(screen.getByTestId("plan-card-enterprise")).toBeInTheDocument();

    // Current plan button says "Current Plan"
    expect(screen.getByText("Current Plan")).toBeInTheDocument();

    // Other plans have upgrade/downgrade buttons
    expect(screen.getByText("Downgrade to Free")).toBeInTheDocument();
    expect(screen.getAllByText("Upgrade").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Contact Sales")).toBeInTheDocument();
  });

  // 4. Stripe redirect on plan change (checkout mutation fired)
  it("triggers checkout mutation when selecting a different plan", async () => {
    const user = userEvent.setup();

    render(<BillingSettingsPage />);

    // Click upgrade on the Pro plan
    const proCard = screen.getByTestId("plan-card-pro");
    const upgradeButton = proCard.querySelector("button")!;
    await user.click(upgradeButton);

    expect(mockCheckoutMutate).toHaveBeenCalledWith({
      plan_tier: "pro",
      success_url: expect.stringContaining("/settings/billing?success=true"),
      cancel_url: expect.stringContaining("/settings/billing?canceled=true"),
    });
  });

  // Additional: loading state
  it("shows loading skeleton when plans/subscription data is loading", () => {
    mockUsePlans.mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    mockUseSubscription.mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    const { container } = render(<BillingSettingsPage />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  // Additional: usage meters display
  it("renders usage meters with correct data", () => {
    render(<BillingSettingsPage />);

    expect(screen.getByText("Current Usage")).toBeInTheDocument();
    expect(screen.getByTestId("usage-meter-Projects")).toBeInTheDocument();
    expect(
      screen.getByTestId("usage-meter-AI Generations (today)")
    ).toBeInTheDocument();
  });

  // Additional: manage billing button triggers portal mutation
  it("manage billing button triggers portal mutation", async () => {
    const user = userEvent.setup();

    render(<BillingSettingsPage />);

    const manageBillingButton = screen.getByRole("button", {
      name: /manage billing/i,
    });
    await user.click(manageBillingButton);

    expect(mockPortalMutate).toHaveBeenCalledWith({
      return_url: expect.stringContaining("/settings/billing"),
    });
  });

  // Additional: cancellation notice shown
  it("shows cancellation notice when cancel_at_period_end is true", () => {
    mockUseSubscription.mockReturnValue({
      data: {
        ...mockSubscription,
        cancel_at_period_end: true,
      },
      isLoading: false,
    });

    render(<BillingSettingsPage />);

    expect(screen.getByText("(Cancels at period end)")).toBeInTheDocument();
  });

  // Additional: empty invoices
  it("shows empty invoice message when no invoices exist", () => {
    mockUseInvoices.mockReturnValue({
      data: { invoices: [], has_more: false },
      isLoading: false,
    });

    render(<BillingSettingsPage />);

    expect(screen.getByText("No invoices found.")).toBeInTheDocument();
  });

  // Additional: period end date displayed
  it("displays current period end date", () => {
    render(<BillingSettingsPage />);

    // The date is formatted via toLocaleDateString — check for the presence
    expect(
      screen.getByText(/current period ends/i)
    ).toBeInTheDocument();
  });

  // Additional: free tier user (no manage billing button)
  it("does not show manage billing when subscription is not active", () => {
    mockUseSubscription.mockReturnValue({
      data: {
        ...mockSubscription,
        subscription_status: "canceled",
      },
      isLoading: false,
    });

    render(<BillingSettingsPage />);

    expect(
      screen.queryByRole("button", { name: /manage billing/i })
    ).not.toBeInTheDocument();
  });
});
