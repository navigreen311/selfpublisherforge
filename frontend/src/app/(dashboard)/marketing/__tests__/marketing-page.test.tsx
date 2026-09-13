import React from "react";
import { render, screen, within } from "@/test-utils";
import userEvent from "@testing-library/user-event";
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

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock lucide-react icons to simple elements
jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Rocket: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="rocket-icon" {...props} />
  ),
  Mail: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="mail-icon" {...props} />
  ),
  Activity: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="activity-icon" {...props} />
  ),
  Inbox: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="inbox-icon" {...props} />
  ),
}));

// Mock the marketing module hooks
const mockUseLaunchPlans = jest.fn();
const mockUseEmailSequences = jest.fn();
const mockUseSocialCalendar = jest.fn();
const mockUseARCCampaigns = jest.fn();
const mockUseRecentActivity = jest.fn();

jest.mock("@/modules/marketing/hooks", () => ({
  useLaunchPlans: (...args: unknown[]) => mockUseLaunchPlans(...args),
  useEmailSequences: (...args: unknown[]) => mockUseEmailSequences(...args),
  useSocialCalendar: (...args: unknown[]) => mockUseSocialCalendar(...args),
  useARCCampaigns: (...args: unknown[]) => mockUseARCCampaigns(...args),
  useRecentActivity: (...args: unknown[]) => mockUseRecentActivity(...args),
  useGenerateSocialPosts: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
  useUpdateSocialPost: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
  useCreateARCCampaign: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
}));

// Mock shared components
jest.mock("@/modules/marketing/components/ARCTable", () => ({
  ARCTable: ({ campaigns, isLoading }: { campaigns: unknown[]; isLoading: boolean }) => (
    <div data-testid="arc-table">ARC Table (loading: {String(isLoading)}, count: {Array.isArray(campaigns) ? campaigns.length : 0})</div>
  ),
}));

jest.mock("@/modules/marketing/components/SocialCalendar", () => ({
  SocialCalendar: ({ calendar, isLoading }: { calendar: unknown; isLoading: boolean }) => (
    <div data-testid="social-calendar">Social Calendar (loading: {String(isLoading)})</div>
  ),
}));

// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import MarketingDashboard from "../page";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const mockLaunchPlansData = {
  items: [
    {
      id: "lp-1",
      title: "Fantasy Book Launch",
      status: "active",
      launch_date: "2025-08-15T00:00:00Z",
      genre: "Fantasy",
      created_at: "2025-06-01T00:00:00Z",
    },
    {
      id: "lp-2",
      title: "Romance Novel Launch",
      status: "draft",
      launch_date: undefined,
      genre: "Romance",
      created_at: "2025-07-01T00:00:00Z",
    },
  ],
  total_count: 2,
  has_more: false,
};

const mockEmailSequencesData = {
  items: [
    {
      id: "es-1",
      name: "Welcome Series",
      status: "active",
      recipient_count: 100,
      sent_count: 75,
      created_at: "2025-05-01T00:00:00Z",
    },
    {
      id: "es-2",
      name: "Launch Announcement",
      status: "draft",
      recipient_count: 50,
      sent_count: 0,
      created_at: "2025-06-15T00:00:00Z",
    },
  ],
  total_count: 2,
  has_more: false,
};

const mockSocialCalendarData = {
  posts: [
    {
      id: "sp-1",
      platform: "twitter",
      content: "Check out my new book!",
      status: "published",
      published_at: "2025-07-01T00:00:00Z",
      updated_at: "2025-07-01T00:00:00Z",
    },
  ],
  total_scheduled: 3,
  total_published: 1,
  total_draft: 2,
  platforms: { twitter: 1 },
};

const mockARCCampaignsData = {
  items: [
    {
      id: "arc-1",
      name: "ARC Campaign 1",
      status: "active",
      total_copies: 50,
      sent_copies: 30,
      reviews_received: 10,
    },
  ],
  total_count: 1,
  has_more: false,
};

const mockRecentActivityItems = [
  {
    id: "lp-1",
    type: "launch_plan" as const,
    action: "Plan activated",
    title: "Fantasy Book Launch",
    timestamp: "2025-07-10T14:00:00Z",
  },
  {
    id: "es-1",
    type: "email_sequence" as const,
    action: "Email sent (75/100)",
    title: "Welcome Series",
    timestamp: "2025-07-09T10:00:00Z",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupLoadedState() {
  mockUseLaunchPlans.mockReturnValue({
    data: mockLaunchPlansData,
    isLoading: false,
    error: null,
  });
  mockUseEmailSequences.mockReturnValue({
    data: mockEmailSequencesData,
    isLoading: false,
    error: null,
  });
  mockUseSocialCalendar.mockReturnValue({
    data: mockSocialCalendarData,
    isLoading: false,
    error: null,
  });
  mockUseARCCampaigns.mockReturnValue({
    data: mockARCCampaignsData,
    isLoading: false,
    error: null,
  });
  mockUseRecentActivity.mockReturnValue({
    items: mockRecentActivityItems,
    isLoading: false,
  });
}

function setupEmptyState() {
  mockUseLaunchPlans.mockReturnValue({
    data: { items: [], total_count: 0, has_more: false },
    isLoading: false,
    error: null,
  });
  mockUseEmailSequences.mockReturnValue({
    data: { items: [], total_count: 0, has_more: false },
    isLoading: false,
    error: null,
  });
  mockUseSocialCalendar.mockReturnValue({
    data: { posts: [], total_scheduled: 0, total_published: 0, total_draft: 0, platforms: {} },
    isLoading: false,
    error: null,
  });
  mockUseARCCampaigns.mockReturnValue({
    data: { items: [], total_count: 0, has_more: false },
    isLoading: false,
    error: null,
  });
  mockUseRecentActivity.mockReturnValue({
    items: [],
    isLoading: false,
  });
}

function setupLoadingState() {
  mockUseLaunchPlans.mockReturnValue({
    data: undefined,
    isLoading: true,
    error: null,
  });
  mockUseEmailSequences.mockReturnValue({
    data: undefined,
    isLoading: true,
    error: null,
  });
  mockUseSocialCalendar.mockReturnValue({
    data: undefined,
    isLoading: true,
    error: null,
  });
  mockUseARCCampaigns.mockReturnValue({
    data: undefined,
    isLoading: true,
    error: null,
  });
  mockUseRecentActivity.mockReturnValue({
    items: [],
    isLoading: true,
  });
}

// ---------------------------------------------------------------------------
// Tab helper — tabs are <button> elements inside a <nav>. The stat card labels
// on the overview tab share the same text ("Launch Plans", "Email Sequences",
// etc.), so we must scope to the nav element to target the correct button.
// ---------------------------------------------------------------------------

function getTabButton(name: string) {
  const nav = screen.getByRole("navigation");
  return within(nav).getByText(name);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("MarketingDashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the marketing dashboard with page header", () => {
    setupLoadedState();

    render(<MarketingDashboard />);

    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Marketing & Launch Command");
    expect(
      screen.getByText(
        "Manage launch plans, email campaigns, social media, and ARC distribution."
      )
    ).toBeInTheDocument();
  });

  it("renders all tab navigation buttons", () => {
    setupLoadedState();

    render(<MarketingDashboard />);

    const nav = screen.getByRole("navigation");
    expect(within(nav).getByText("Overview")).toBeInTheDocument();
    expect(within(nav).getByText("Launch Plans")).toBeInTheDocument();
    expect(within(nav).getByText("Email Sequences")).toBeInTheDocument();
    expect(within(nav).getByText("Social Media")).toBeInTheDocument();
    expect(within(nav).getByText("ARC Campaigns")).toBeInTheDocument();
  });

  it("shows launch plans section when tab is clicked", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Launch Plans"));

    // Should see plan titles
    expect(screen.getByText("Fantasy Book Launch")).toBeInTheDocument();
    expect(screen.getByText("Romance Novel Launch")).toBeInTheDocument();

    // Should see status badges
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("draft")).toBeInTheDocument();

    // Should see the generate launch plan button link
    const generateLink = screen.getByText("+ Generate Launch Plan");
    expect(generateLink).toBeInTheDocument();
    expect(generateLink.closest("a")).toHaveAttribute("href", "/marketing/launch/new");
  });

  it("shows email campaigns section when tab is clicked", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Email Sequences"));

    // Should see sequence names
    expect(screen.getByText("Welcome Series")).toBeInTheDocument();
    expect(screen.getByText("Launch Announcement")).toBeInTheDocument();

    // Should see send counts
    expect(screen.getByText("75 / 100 sent")).toBeInTheDocument();
    expect(screen.getByText("0 / 50 sent")).toBeInTheDocument();

    // Should see the create sequence button link
    const createLink = screen.getByText("+ Create Sequence");
    expect(createLink).toBeInTheDocument();
    expect(createLink.closest("a")).toHaveAttribute("href", "/marketing/email");
  });

  it("renders empty state when no data exists (launch plans tab)", async () => {
    const user = userEvent.setup();
    setupEmptyState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Launch Plans"));

    expect(screen.getByText("No launch plans yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Generate your first AI-powered launch plan to coordinate your book launch."
      )
    ).toBeInTheDocument();
  });

  it("renders empty state when no data exists (email tab)", async () => {
    const user = userEvent.setup();
    setupEmptyState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Email Sequences"));

    expect(screen.getByText("No email sequences yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create your first email sequence to engage your readers and build your audience."
      )
    ).toBeInTheDocument();
  });

  it("EmptyState action buttons use router.push for launch plans (not window.location)", async () => {
    const user = userEvent.setup();
    setupEmptyState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Launch Plans"));

    const generateButton = screen.getByRole("button", { name: "Generate Launch Plan" });
    expect(generateButton).toBeInTheDocument();

    await user.click(generateButton);

    expect(mockPush).toHaveBeenCalledWith("/marketing/launch/new");
  });

  it("EmptyState action buttons use router.push for email (not window.location)", async () => {
    const user = userEvent.setup();
    setupEmptyState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Email Sequences"));

    const createButton = screen.getByRole("button", { name: "Create Sequence" });
    expect(createButton).toBeInTheDocument();

    await user.click(createButton);

    expect(mockPush).toHaveBeenCalledWith("/marketing/email");
  });

  it("renders recent activity section on the overview tab", () => {
    setupLoadedState();

    render(<MarketingDashboard />);

    // The overview tab is active by default
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();

    // Activity items should be visible
    expect(screen.getByText("Plan activated")).toBeInTheDocument();
    expect(screen.getByText("Fantasy Book Launch")).toBeInTheDocument();
    expect(screen.getByText("Email sent (75/100)")).toBeInTheDocument();
    expect(screen.getByText("Welcome Series")).toBeInTheDocument();
  });

  it("renders empty state for recent activity when no activity exists", () => {
    setupEmptyState();

    render(<MarketingDashboard />);

    expect(screen.getByText("No recent activity")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Activity will appear here as you create campaigns, send emails, and publish posts."
      )
    ).toBeInTheDocument();
  });

  it("renders loading skeletons for recent activity while data is loading", () => {
    setupLoadingState();

    const { container } = render(<MarketingDashboard />);

    // Page header should still show during loading
    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Marketing & Launch Command");

    // Skeleton elements should be present (from activity loading state)
    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders loading skeletons for launch plans tab", async () => {
    const user = userEvent.setup();
    mockUseLaunchPlans.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    mockUseEmailSequences.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    mockUseSocialCalendar.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    mockUseARCCampaigns.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    mockUseRecentActivity.mockReturnValue({
      items: [],
      isLoading: false,
    });

    const { container } = render(<MarketingDashboard />);

    await user.click(getTabButton("Launch Plans"));

    // Skeleton elements should be present for loading launch plans
    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders overview stat cards with correct counts", () => {
    setupLoadedState();

    render(<MarketingDashboard />);

    // Stat card labels (these also appear in the tab nav, so use getAllByText)
    expect(screen.getAllByText("Launch Plans").length).toBeGreaterThanOrEqual(2); // tab + stat
    expect(screen.getAllByText("Email Sequences").length).toBeGreaterThanOrEqual(2); // tab + stat
    expect(screen.getByText("Social Posts")).toBeInTheDocument(); // unique to stat card
    expect(screen.getAllByText("ARC Campaigns").length).toBeGreaterThanOrEqual(2); // tab + stat

    // Values from the mock data (numbers may appear in multiple stat cards)
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1); // launch plans and email sequences count
    expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(1); // social posts / arc count
  });

  it("renders quick actions links on the overview tab", () => {
    setupLoadedState();

    render(<MarketingDashboard />);

    expect(screen.getByText("Quick Actions")).toBeInTheDocument();

    const launchPlanLink = screen.getByText("Generate a new launch plan with AI");
    expect(launchPlanLink.closest("a")).toHaveAttribute("href", "/marketing/launch/new");

    const emailLink = screen.getByText("Create an email sequence");
    expect(emailLink.closest("a")).toHaveAttribute("href", "/marketing/email");
  });

  it("switches between tabs correctly", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<MarketingDashboard />);

    // Overview is active by default
    expect(screen.getByText("Quick Actions")).toBeInTheDocument();

    // Switch to Launch Plans
    await user.click(getTabButton("Launch Plans"));
    expect(screen.getByText("Fantasy Book Launch")).toBeInTheDocument();

    // Switch to Email Sequences
    await user.click(getTabButton("Email Sequences"));
    expect(screen.getByText("Welcome Series")).toBeInTheDocument();

    // Switch to Social Media
    await user.click(getTabButton("Social Media"));
    expect(screen.getByTestId("social-calendar")).toBeInTheDocument();

    // Switch to ARC Campaigns
    await user.click(getTabButton("ARC Campaigns"));
    expect(screen.getByTestId("arc-table")).toBeInTheDocument();
  });

  it("renders launch plan items as links to their detail pages", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Launch Plans"));

    const links = screen.getAllByRole("link");
    const planLinks = links.filter((link) =>
      link.getAttribute("href")?.startsWith("/marketing/launch/")
    );
    // Should have the "Generate Launch Plan" link + 2 plan links
    const detailLinks = planLinks.filter((link) =>
      link.getAttribute("href")?.match(/^\/marketing\/launch\/lp-\d+$/)
    );
    expect(detailLinks).toHaveLength(2);
    expect(detailLinks[0]).toHaveAttribute("href", "/marketing/launch/lp-1");
    expect(detailLinks[1]).toHaveAttribute("href", "/marketing/launch/lp-2");
  });

  it("shows genre on launch plan cards when available", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<MarketingDashboard />);

    await user.click(getTabButton("Launch Plans"));

    expect(screen.getByText("Fantasy")).toBeInTheDocument();
    expect(screen.getByText("Romance")).toBeInTheDocument();
  });
});
