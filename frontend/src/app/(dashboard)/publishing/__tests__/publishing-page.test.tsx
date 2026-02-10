import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUsePublishingAccounts = jest.fn();
const mockUseCreateAccount = jest.fn();
const mockUseListings = jest.fn();
const mockUseDeleteAccount = jest.fn();
const mockUseSyncListing = jest.fn();

jest.mock("@/modules/publishing/hooks", () => ({
  usePublishingAccounts: (...args: unknown[]) => mockUsePublishingAccounts(...args),
  useCreateAccount: (...args: unknown[]) => mockUseCreateAccount(...args),
  useListings: (...args: unknown[]) => mockUseListings(...args),
  useDeleteAccount: (...args: unknown[]) => mockUseDeleteAccount(...args),
  useSyncListing: (...args: unknown[]) => mockUseSyncListing(...args),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className, ...props }: { className?: string }) => (
    <div data-testid="skeleton" className={className} {...props} />
  ),
}));

// ── Import component under test (after mocks) ───────────────────────────

import PublishingDashboardPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Test Data ────────────────────────────────────────────────────────────

const mockAccounts = [
  {
    id: "acc-1",
    org_id: "org-1",
    platform: "kdp",
    account_name: "My KDP Account",
    account_email: "user@kdp.com",
    is_active: true,
    last_synced_at: "2025-06-01T12:00:00Z",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-06-01T12:00:00Z",
  },
  {
    id: "acc-2",
    org_id: "org-1",
    platform: "ingram_spark",
    account_name: "My IngramSpark",
    account_email: null,
    is_active: false,
    last_synced_at: null,
    created_at: "2025-02-01T00:00:00Z",
    updated_at: "2025-02-01T00:00:00Z",
  },
];

const mockListingsData = [
  {
    id: "lst-1",
    book_id: "book-1",
    account_id: "acc-1",
    platform: "kdp",
    platform_listing_id: "B00TEST1",
    status: "active",
    listing_url: "https://amazon.com/dp/B00TEST1",
    title: "The Great Novel",
    current_price: 9.99,
    current_rank: 5432,
    reviews_count: 25,
    rating: 4.5,
    last_synced_at: "2025-06-01T12:00:00Z",
    sync_errors: [],
    created_at: "2025-03-01T00:00:00Z",
    updated_at: "2025-06-01T12:00:00Z",
  },
  {
    id: "lst-2",
    book_id: "book-2",
    account_id: "acc-2",
    platform: "ingram_spark",
    platform_listing_id: null,
    status: "draft",
    listing_url: null,
    title: "Upcoming Book",
    current_price: null,
    current_rank: null,
    reviews_count: null,
    rating: null,
    last_synced_at: null,
    sync_errors: [],
    created_at: "2025-04-01T00:00:00Z",
    updated_at: "2025-04-01T00:00:00Z",
  },
];

const mockMutate = jest.fn();

function setupDefaultMocks() {
  mockUsePublishingAccounts.mockReturnValue({
    data: mockAccounts,
    isLoading: false,
    error: null,
  });
  mockUseListings.mockReturnValue({
    data: mockListingsData,
    isLoading: false,
    isError: false,
    error: null,
  });
  mockUseCreateAccount.mockReturnValue({
    mutate: mockMutate,
    isPending: false,
  });
  mockUseDeleteAccount.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
  });
  mockUseSyncListing.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("PublishingDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupDefaultMocks();
  });

  // 1. Renders publishing dashboard
  it("renders the publishing dashboard with header and description", () => {
    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("Publishing Operations")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Manage your publishing accounts, export manuscripts, and track listings."
      )
    ).toBeInTheDocument();
  });

  // 2. Shows export section
  it("shows the export section with New Export button and export manuscript card", () => {
    renderWithProviders(<PublishingDashboardPage />);

    // New Export button in header
    const newExportLink = screen.getByRole("link", { name: /new export/i });
    expect(newExportLink).toHaveAttribute("href", "/publishing/export");

    // Export Manuscript quick action card
    expect(screen.getByText("Export Manuscript")).toBeInTheDocument();
    expect(
      screen.getByText("Generate EPUB or print-ready PDF with formatting templates")
    ).toBeInTheDocument();
  });

  // 3. Shows metadata section (Connected Accounts and Active Listings cards)
  it("shows the connected accounts and active listings stat cards", () => {
    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("Connected Accounts")).toBeInTheDocument();
    // 2 accounts
    expect(screen.getByText("2")).toBeInTheDocument();

    expect(screen.getByText("Active Listings")).toBeInTheDocument();
    // 1 active listing
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  // 4. Shows book listings (accounts rendered)
  it("shows publishing accounts cards when accounts exist", () => {
    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("Publishing Accounts")).toBeInTheDocument();
    expect(screen.getByText("My KDP Account")).toBeInTheDocument();
    expect(screen.getByText("My IngramSpark")).toBeInTheDocument();
  });

  // 5. Loading states work
  it("renders loading skeletons when accounts are loading", () => {
    mockUsePublishingAccounts.mockReturnValue({
      data: [],
      isLoading: true,
      error: null,
    });

    const { container } = renderWithProviders(<PublishingDashboardPage />);

    const skeletons = container.querySelectorAll('[data-testid="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  it("shows skeleton for active listings count when listings are loading", () => {
    mockUseListings.mockReturnValue({
      data: [],
      isLoading: true,
      isError: false,
      error: null,
    });

    const { container } = renderWithProviders(<PublishingDashboardPage />);

    // Active Listings section should show a skeleton
    expect(screen.getByText("Active Listings")).toBeInTheDocument();
    const skeletons = container.querySelectorAll('[data-testid="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  // 6. Empty states for no books/accounts
  it("shows empty state when no accounts are connected", () => {
    mockUsePublishingAccounts.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("No accounts connected")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Connect your first publishing platform account to get started."
      )
    ).toBeInTheDocument();
  });

  it("shows listings error message when listings fail to load", () => {
    mockUseListings.mockReturnValue({
      data: [],
      isLoading: false,
      isError: true,
      error: new Error("Server error"),
    });

    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("Failed to load")).toBeInTheDocument();
  });

  it("renders the Listings section heading", () => {
    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("Listings")).toBeInTheDocument();
  });

  it("shows the connect account form when + Connect Account is clicked", async () => {
    const user = userEvent.setup();

    renderWithProviders(<PublishingDashboardPage />);

    const connectBtn = screen.getByText("+ Connect Account");
    await user.click(connectBtn);

    expect(screen.getByText("Connect New Account")).toBeInTheDocument();
    // "Platform" may appear in multiple elements (label + select options),
    // so verify at least one "Platform" label is rendered
    expect(screen.getAllByText("Platform").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Account Name *")).toBeInTheDocument();
    // "Email" appears in the form label
    expect(screen.getAllByText("Email").length).toBeGreaterThanOrEqual(1);
  });

  it("shows Cancel button to hide form when connect form is open", async () => {
    const user = userEvent.setup();

    renderWithProviders(<PublishingDashboardPage />);

    await user.click(screen.getByText("+ Connect Account"));
    expect(screen.getByText("Cancel")).toBeInTheDocument();

    await user.click(screen.getByText("Cancel"));
    expect(screen.queryByText("Connect New Account")).not.toBeInTheDocument();
  });

  it("calls createAccount.mutate when the connect form is submitted", async () => {
    const user = userEvent.setup();

    renderWithProviders(<PublishingDashboardPage />);

    await user.click(screen.getByText("+ Connect Account"));

    const nameInput = screen.getByPlaceholderText("My KDP Account");
    await user.type(nameInput, "Test Account");

    const connectBtn = screen.getByRole("button", { name: /^connect$/i });
    await user.click(connectBtn);

    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        platform: "kdp",
        account_name: "Test Account",
      }),
      expect.any(Object)
    );
  });

  it("displays the correct count of connected accounts", () => {
    renderWithProviders(<PublishingDashboardPage />);

    // Connected Accounts stat card shows count from accounts array length
    expect(screen.getByText("Connected Accounts")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders 0 for connected accounts when no accounts exist", () => {
    mockUsePublishingAccounts.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    renderWithProviders(<PublishingDashboardPage />);

    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("has links pointing to /publishing/export", () => {
    renderWithProviders(<PublishingDashboardPage />);

    const exportLinks = screen.getAllByRole("link").filter(
      (link) => link.getAttribute("href") === "/publishing/export"
    );
    // New Export button + Export Manuscript card
    expect(exportLinks.length).toBeGreaterThanOrEqual(2);
  });
});
