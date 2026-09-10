import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock the advertising module hooks
const mockUseAdDashboard = jest.fn();

jest.mock("@/modules/advertising/hooks", () => ({
  useAdDashboard: (...args: unknown[]) => mockUseAdDashboard(...args),
  useEnhancedDashboard: () => ({ data: undefined, isLoading: false, isError: false, error: null, refetch: jest.fn() }),
}));

// Mock the CampaignCard component
jest.mock("@/modules/advertising/components/CampaignCard", () => ({
  CampaignCard: ({ campaign }: { campaign: { id: string; name: string } }) => (
    <div data-testid={`campaign-card-${campaign.id}`}>
      {campaign.name}
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import AdvertisingDashboardPage from "../page";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const mockDashboardData = {
  total_active_campaigns: 5,
  total_spend_today: 45.5,
  total_spend_month: 1250.75,
  total_sales_month: 3500.0,
  overall_acos: 35.7,
  overall_roas: 2.8,
  top_campaigns: [
    {
      id: "camp-1",
      org_id: "org-1",
      name: "Fantasy Series Campaign",
      platform: "amazon" as const,
      campaign_type: "sponsored_products",
      status: "active" as const,
      daily_budget: 25,
      bid_strategy: "manual",
      targeting_keywords: ["fantasy books"],
      negative_keywords: [],
      created_at: "2025-06-01T00:00:00Z",
      updated_at: "2025-07-01T00:00:00Z",
      performance_summary: {
        total_impressions: 15000,
        total_clicks: 450,
        total_spend: 350.0,
        total_sales: 1200.0,
        total_orders: 40,
        avg_acos: 29.2,
        avg_roas: 3.43,
        avg_ctr: 3.0,
        avg_cpc: 0.78,
        avg_conversion_rate: 8.9,
      },
    },
    {
      id: "camp-2",
      org_id: "org-1",
      name: "Romance Promo Campaign",
      platform: "facebook" as const,
      campaign_type: "facebook_feed",
      status: "active" as const,
      daily_budget: 15,
      bid_strategy: "auto_low",
      targeting_keywords: [],
      negative_keywords: [],
      created_at: "2025-06-15T00:00:00Z",
      updated_at: "2025-07-10T00:00:00Z",
      performance_summary: {
        total_impressions: 8000,
        total_clicks: 200,
        total_spend: 180.0,
        total_sales: 500.0,
        total_orders: 15,
        avg_acos: 36.0,
        avg_roas: 2.78,
        avg_ctr: 2.5,
        avg_cpc: 0.9,
        avg_conversion_rate: 7.5,
      },
    },
  ],
  platform_breakdown: {
    amazon: {
      total_impressions: 15000,
      total_clicks: 450,
      total_spend: 800.0,
      total_sales: 2500.0,
      total_orders: 80,
      avg_acos: 32.0,
      avg_roas: 3.13,
      avg_ctr: 3.0,
      avg_cpc: 0.78,
      avg_conversion_rate: 8.9,
    },
    facebook: {
      total_impressions: 8000,
      total_clicks: 200,
      total_spend: 450.75,
      total_sales: 1000.0,
      total_orders: 30,
      avg_acos: 45.1,
      avg_roas: 2.22,
      avg_ctr: 2.5,
      avg_cpc: 2.25,
      avg_conversion_rate: 15.0,
    },
  },
  recent_optimizations: ["Optimized bids for Fantasy Series Campaign"],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdvertisingDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the advertising dashboard with page header", () => {
    mockUseAdDashboard.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Advertising Intelligence");
  });

  it("displays campaign list via top campaigns section", () => {
    mockUseAdDashboard.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    expect(screen.getByText("Top Campaigns")).toBeInTheDocument();

    // CampaignCard components should render for each top campaign
    expect(screen.getByTestId("campaign-card-camp-1")).toBeInTheDocument();
    expect(screen.getByText("Fantasy Series Campaign")).toBeInTheDocument();
    expect(screen.getByTestId("campaign-card-camp-2")).toBeInTheDocument();
    expect(screen.getByText("Romance Promo Campaign")).toBeInTheDocument();
  });

  it("renders the View All Campaigns button linking to campaigns page", () => {
    mockUseAdDashboard.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    const viewAllLink = screen.getByRole("link", { name: /view all campaigns/i });
    expect(viewAllLink).toBeInTheDocument();
    expect(viewAllLink).toHaveAttribute("href", "/advertising/campaigns");
  });

  it("displays campaign metrics KPI cards with correct values", () => {
    mockUseAdDashboard.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    // KPI labels
    expect(screen.getByText("Active Campaigns")).toBeInTheDocument();
    expect(screen.getByText("Today's Spend")).toBeInTheDocument();
    expect(screen.getByText("Monthly Spend")).toBeInTheDocument();
    expect(screen.getByText("Overall ACOS")).toBeInTheDocument();

    // KPI values
    expect(screen.getByText("5")).toBeInTheDocument(); // total_active_campaigns
    expect(screen.getByText("$45.50")).toBeInTheDocument(); // total_spend_today
    expect(screen.getByText("$1250.75")).toBeInTheDocument(); // total_spend_month
    expect(screen.getByText("35.7%")).toBeInTheDocument(); // overall_acos

    // Subtext values
    expect(screen.getByText("Sales: $3500.00")).toBeInTheDocument();
    expect(screen.getByText("ROAS: 2.80x")).toBeInTheDocument();
  });

  it("renders platform breakdown section", () => {
    mockUseAdDashboard.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    expect(screen.getByText("Platform Performance")).toBeInTheDocument();
    expect(screen.getByText("Amazon Ads")).toBeInTheDocument();
    expect(screen.getByText("Facebook Ads")).toBeInTheDocument();
  });

  it("renders loading state with skeletons while data is being fetched", () => {
    mockUseAdDashboard.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    const { container } = render(<AdvertisingDashboardPage />);

    // Page header should still be visible during loading
    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Advertising Intelligence");

    // Should render skeleton elements
    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders error state when API fails", () => {
    mockUseAdDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network timeout"),
    });

    render(<AdvertisingDashboardPage />);

    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Advertising Intelligence");
    expect(
      screen.getByText("Failed to load dashboard data. Please try again later.")
    ).toBeInTheDocument();
  });

  it("shows empty state when there are no top campaigns", () => {
    const emptyDashboard = {
      ...mockDashboardData,
      top_campaigns: [],
    };

    mockUseAdDashboard.mockReturnValue({
      data: emptyDashboard,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    expect(screen.getByText("No active campaigns yet.")).toBeInTheDocument();

    const createLink = screen.getByRole("link", { name: /create your first campaign/i });
    expect(createLink).toBeInTheDocument();
    expect(createLink).toHaveAttribute("href", "/advertising/campaigns");
  });

  it("highlights ACOS in red when above 40%", () => {
    const highAcosDashboard = {
      ...mockDashboardData,
      overall_acos: 55.0,
      overall_roas: 1.5,
    };

    mockUseAdDashboard.mockReturnValue({
      data: highAcosDashboard,
      isLoading: false,
      error: null,
    });

    const { container } = render(<AdvertisingDashboardPage />);

    // The value 55.0% should have the red text class
    const acosValue = screen.getByText("55.0%");
    expect(acosValue).toHaveClass("text-red-600");
  });

  it("highlights ACOS in green when below 40% and above 0", () => {
    mockUseAdDashboard.mockReturnValue({
      data: mockDashboardData, // overall_acos is 35.7
      isLoading: false,
      error: null,
    });

    const { container } = render(<AdvertisingDashboardPage />);

    const acosValue = screen.getByText("35.7%");
    expect(acosValue).toHaveClass("text-green-600");
  });

  it("does not render platform breakdown when there are no platforms", () => {
    const noPlatforms = {
      ...mockDashboardData,
      platform_breakdown: {},
    };

    mockUseAdDashboard.mockReturnValue({
      data: noPlatforms,
      isLoading: false,
      error: null,
    });

    render(<AdvertisingDashboardPage />);

    expect(screen.queryByText("Platform Performance")).not.toBeInTheDocument();
  });
});
