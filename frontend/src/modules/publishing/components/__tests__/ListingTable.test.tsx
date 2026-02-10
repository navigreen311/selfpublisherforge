import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUseListings = jest.fn();
const mockSyncMutate = jest.fn();
const mockUseSyncListing = jest.fn();

jest.mock("../../hooks", () => ({
  useListings: (...args: unknown[]) => mockUseListings(...args),
  useSyncListing: (...args: unknown[]) => mockUseSyncListing(...args),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock the Skeleton UI component to render a simple div with animate-pulse
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div
      data-testid="skeleton"
      className={`animate-pulse rounded-md bg-muted ${className || ""}`}
    />
  ),
}));

// Mock the constants used by ListingTable
jest.mock("@/lib/constants", () => ({
  PUBLISHING_PLATFORM_LABELS: {
    kdp: "Amazon KDP",
    ingram_spark: "IngramSpark",
    draft2digital: "Draft2Digital",
    smashwords: "Smashwords",
    acx: "ACX",
    apple_books: "Apple Books",
    barnes_noble: "Barnes & Noble",
    kobo: "Kobo",
    google_play: "Google Play Books",
  } as Record<string, string>,
  LISTING_STATUS_STYLES: {
    draft: "bg-gray-100 text-gray-700",
    pending: "bg-yellow-100 text-yellow-700",
    live: "bg-green-100 text-green-700",
    paused: "bg-orange-100 text-orange-700",
    rejected: "bg-red-100 text-red-700",
    archived: "bg-gray-200 text-gray-500",
  } as Record<string, string>,
}));

// Import after mocks
import { ListingTable } from "../ListingTable";

// ── Fixture data ─────────────────────────────────────────────────────────

const mockListings = [
  {
    id: "lst-1",
    book_id: "book-1",
    account_id: "acc-1",
    platform: "kdp",
    platform_listing_id: "B00TEST1",
    status: "live",
    listing_url: "https://amazon.com/dp/B00TEST1",
    title: "The Great Adventure",
    current_price: 9.99,
    current_rank: 1234,
    reviews_count: 42,
    rating: 4.5,
    last_synced_at: "2025-06-01T00:00:00Z",
    sync_errors: [],
    created_at: "2025-03-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
  {
    id: "lst-2",
    book_id: "book-2",
    account_id: "acc-2",
    platform: "ingram_spark",
    platform_listing_id: null,
    status: "draft",
    listing_url: null,
    title: "Mystery Novel",
    current_price: null,
    current_rank: null,
    reviews_count: null,
    rating: null,
    last_synced_at: null,
    sync_errors: [],
    created_at: "2025-04-01T00:00:00Z",
    updated_at: "2025-04-01T00:00:00Z",
  },
  {
    id: "lst-3",
    book_id: "book-3",
    account_id: "acc-3",
    platform: "apple_books",
    platform_listing_id: "APPLE123",
    status: "pending",
    listing_url: null,
    title: "Sci-Fi Epic",
    current_price: 14.99,
    current_rank: 5678,
    reviews_count: 0,
    rating: null,
    last_synced_at: "2025-05-15T00:00:00Z",
    sync_errors: [],
    created_at: "2025-02-01T00:00:00Z",
    updated_at: "2025-05-15T00:00:00Z",
  },
  {
    id: "lst-4",
    book_id: "book-4",
    account_id: "acc-4",
    platform: "kobo",
    platform_listing_id: "KOBO456",
    status: "rejected",
    listing_url: null,
    title: "Romance Tales",
    current_price: 4.99,
    current_rank: null,
    reviews_count: 15,
    rating: 3.8,
    last_synced_at: "2025-05-20T00:00:00Z",
    sync_errors: ["Content policy violation"],
    created_at: "2025-01-15T00:00:00Z",
    updated_at: "2025-05-20T00:00:00Z",
  },
];

// ── Default mock setup ───────────────────────────────────────────────────

function setDefaultMocks(overrides?: {
  listings?: unknown;
  isLoading?: boolean;
  error?: Error | null;
  syncIsPending?: boolean;
}) {
  mockUseListings.mockReturnValue({
    data: overrides?.listings ?? mockListings,
    isLoading: overrides?.isLoading ?? false,
    error: overrides?.error ?? null,
  });

  mockUseSyncListing.mockReturnValue({
    mutate: mockSyncMutate,
    isPending: overrides?.syncIsPending ?? false,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("ListingTable", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Renders table with listing data
  it("renders table with listing data", () => {
    setDefaultMocks();
    render(<ListingTable />);

    // Table headers should be present
    expect(screen.getByText("Book")).toBeInTheDocument();
    expect(screen.getByText("Platform")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Price")).toBeInTheDocument();
    expect(screen.getByText("Rank")).toBeInTheDocument();
    expect(screen.getByText("Reviews")).toBeInTheDocument();

    // Listing titles should be visible
    expect(screen.getByText("The Great Adventure")).toBeInTheDocument();
    expect(screen.getByText("Mystery Novel")).toBeInTheDocument();
    expect(screen.getByText("Sci-Fi Epic")).toBeInTheDocument();
    expect(screen.getByText("Romance Tales")).toBeInTheDocument();
  });

  // 2. Shows skeleton loading state with animation
  it("shows skeleton loading state with animate-pulse class", () => {
    setDefaultMocks({ isLoading: true, listings: [] });
    render(<ListingTable />);

    // Skeleton elements should be rendered with the animate-pulse class
    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(5); // 5 rows x 8 columns = 40 skeletons

    // Each skeleton should have the animate-pulse class
    skeletons.forEach((skeleton) => {
      expect(skeleton).toHaveClass("animate-pulse");
    });
  });

  // 3. Skeleton has aria-busy="true" and role="status"
  it("skeleton loading state has aria-busy and role=status for accessibility", () => {
    setDefaultMocks({ isLoading: true, listings: [] });
    const { container } = render(<ListingTable />);

    // The outer container should have aria-busy="true"
    const busyContainer = container.querySelector('[aria-busy="true"]');
    expect(busyContainer).toBeInTheDocument();

    // There should be an element with role="status"
    const statusElement = screen.getByRole("status");
    expect(statusElement).toBeInTheDocument();
    expect(statusElement).toHaveAttribute("aria-label", "Loading listings");
  });

  // 4. Shows empty state when no listings match filters
  it("shows empty state when no listings exist", () => {
    setDefaultMocks({ listings: [] });
    render(<ListingTable />);

    expect(screen.getByText("No listings yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Export your book and publish to a platform to see listings here."
      )
    ).toBeInTheDocument();
  });

  // 5. Displays platform badges with correct styling/labels
  it("displays platform labels with correct human-readable names", () => {
    setDefaultMocks();
    render(<ListingTable />);

    // Platform labels should use human-readable names from constants
    expect(screen.getByText("Amazon KDP")).toBeInTheDocument();
    expect(screen.getByText("IngramSpark")).toBeInTheDocument();
    expect(screen.getByText("Apple Books")).toBeInTheDocument();
    expect(screen.getByText("Kobo")).toBeInTheDocument();
  });

  // 6. Displays status badges with correct styling
  it("displays status badges with appropriate CSS classes", () => {
    setDefaultMocks();
    render(<ListingTable />);

    // Check that status badges exist and have correct styling classes
    const liveStatus = screen.getByText("live");
    expect(liveStatus).toHaveClass("bg-green-100");
    expect(liveStatus).toHaveClass("text-green-700");

    const draftStatus = screen.getByText("draft");
    expect(draftStatus).toHaveClass("bg-gray-100");
    expect(draftStatus).toHaveClass("text-gray-700");

    const pendingStatus = screen.getByText("pending");
    expect(pendingStatus).toHaveClass("bg-yellow-100");
    expect(pendingStatus).toHaveClass("text-yellow-700");

    const rejectedStatus = screen.getByText("rejected");
    expect(rejectedStatus).toHaveClass("bg-red-100");
    expect(rejectedStatus).toHaveClass("text-red-700");
  });

  // 7. Handles empty listings array gracefully
  it("handles empty listings array gracefully without errors", () => {
    setDefaultMocks({ listings: [] });

    // Should not throw
    expect(() => render(<ListingTable />)).not.toThrow();

    // Should show the empty state, not a broken table
    expect(screen.getByText("No listings yet")).toBeInTheDocument();
    expect(screen.queryByText("Sync")).not.toBeInTheDocument();
  });

  // 8. Displays pricing data correctly
  it("displays pricing data with dollar format and dashes for null values", () => {
    setDefaultMocks();
    render(<ListingTable />);

    // lst-1 has price $9.99
    expect(screen.getByText("$9.99")).toBeInTheDocument();
    // lst-3 has price $14.99
    expect(screen.getByText("$14.99")).toBeInTheDocument();
    // lst-4 has price $4.99
    expect(screen.getByText("$4.99")).toBeInTheDocument();
    // lst-2 has null price, should show "-"
    const dashElements = screen.getAllByText("-");
    expect(dashElements.length).toBeGreaterThanOrEqual(1);
  });

  // 9. Displays rank data correctly
  it("displays rank data with hash prefix", () => {
    setDefaultMocks();
    render(<ListingTable />);

    // lst-1 has rank 1234
    expect(screen.getByText("#1,234")).toBeInTheDocument();
    // lst-3 has rank 5678
    expect(screen.getByText("#5,678")).toBeInTheDocument();
  });

  // 10. Displays reviews and ratings
  it("displays review counts and ratings correctly", () => {
    setDefaultMocks();
    render(<ListingTable />);

    // lst-1 has 42 reviews with rating 4.5
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("(4.5)")).toBeInTheDocument();

    // lst-4 has 15 reviews with rating 3.8
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("(3.8)")).toBeInTheDocument();
  });

  // 11. Sync button calls sync mutation
  it("sync button triggers sync mutation for the listing", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    render(<ListingTable />);

    const syncButtons = screen.getAllByText("Sync");
    expect(syncButtons.length).toBe(4);

    // Click the first sync button
    await user.click(syncButtons[0]);

    expect(mockSyncMutate).toHaveBeenCalledWith(
      "lst-1",
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      })
    );
  });

  // 12. Shows error state
  it("shows error state when API fails", () => {
    setDefaultMocks({ error: new Error("Server error"), listings: [] });
    render(<ListingTable />);

    expect(
      screen.getByText("Failed to load listings. Please try again.")
    ).toBeInTheDocument();
  });

  // 13. View link renders for listings with a listing_url
  it("renders View link for listings with listing_url", () => {
    setDefaultMocks();
    render(<ListingTable />);

    const viewLinks = screen.getAllByText("View");
    expect(viewLinks.length).toBeGreaterThanOrEqual(1);

    const firstViewLink = viewLinks[0];
    expect(firstViewLink).toHaveAttribute(
      "href",
      "https://amazon.com/dp/B00TEST1"
    );
    expect(firstViewLink).toHaveAttribute("target", "_blank");
    expect(firstViewLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  // 14. Shows filter-based empty state when all listings are filtered out
  it("shows filter empty state when no listings match the filter", () => {
    setDefaultMocks();
    render(<ListingTable filter={() => false} />);

    expect(
      screen.getByText("No listings match your filters")
    ).toBeInTheDocument();
  });

  // 15. Sync buttons disabled when sync is pending
  it("disables sync buttons when a sync is pending", () => {
    setDefaultMocks({ syncIsPending: true });
    render(<ListingTable />);

    const syncButtons = screen.getAllByText("Sync");
    syncButtons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });
});
