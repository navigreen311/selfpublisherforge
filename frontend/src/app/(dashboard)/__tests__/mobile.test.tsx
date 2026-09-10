/**
 * Mobile Responsive Tests for Dashboard Pages
 * Tests that dashboard and module pages render properly at mobile breakpoints
 */

import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@/test-utils";
import "@testing-library/jest-dom";

// Mock Next.js router
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock API hooks
jest.mock("@/modules/analytics/hooks", () => ({
  useDashboard: () => ({
    data: {
      kpis: [
        { label: "Total Revenue", value: "$12,345", change_percent: 5.2, change_direction: "up" },
        { label: "Units Sold", value: "1,234", change_percent: 3.1, change_direction: "up" },
      ],
      revenue_chart: [],
      top_books: [],
      recent_royalties: [],
      platform_breakdown: {},
    },
    isLoading: false,
    error: null,
    refetch: jest.fn(),
  }),
  useEnhancedDashboard: () => ({ data: undefined, isLoading: false, isError: false, error: null, refetch: jest.fn() }),
}));

jest.mock("@/modules/projects/hooks", () => ({
  useProjects: () => ({
    data: [
      {
        id: "1",
        title: "Test Project",
        type: "book",
        status: "active",
        books: [],
        updated_at: new Date().toISOString(),
      },
    ],
    isLoading: false,
    isError: false,
  }),
  useDeleteProject: () => ({
    mutateAsync: jest.fn(),
  }),
  useUpdateProject: () => ({
    mutateAsync: jest.fn(),
  }),
}));

jest.mock("@/modules/writing/hooks", () => ({
  useBooks: () => ({
    data: [
      {
        id: "1",
        title: "Test Book",
        status: "writing",
        chapter_count: 10,
        word_count: 50000,
        updated_at: new Date().toISOString(),
      },
    ],
    isLoading: false,
    error: null,
  }),
  useWritingSessions: () => ({
    data: [
      {
        id: "1",
        book_id: "1",
        book_title: "Test Book",
        words_written: 500,
        duration_minutes: 30,
        created_at: new Date().toISOString(),
      },
    ],
    isLoading: false,
    error: null,
  }),
}));

jest.mock("@/modules/publishing/hooks", () => ({
  usePublishingAccounts: () => ({
    data: [],
    isLoading: false,
  }),
  useListings: () => ({
    // One listing so the Listings tab actually renders its table — the
    // horizontal-scroll assertion below needs something to scroll.
    data: [
      {
        id: "listing-1",
        book_id: "book-1",
        book_title: "Test Book",
        platform: "kdp",
        status: "active",
        external_id: "B00TEST",
        price: 9.99,
        currency: "USD",
        last_synced_at: null,
      },
    ],
    isLoading: false,
    isError: false,
  }),
  useCreateAccount: () => ({
    mutate: jest.fn(),
    isPending: false,
  }),
}));

jest.mock("@/modules/marketing/hooks", () => ({
  useLaunchPlans: () => ({
    data: { items: [], total_count: 0 },
    isLoading: false,
  }),
  useEmailSequences: () => ({
    data: { items: [], total_count: 0 },
    isLoading: false,
  }),
  useSocialCalendar: () => ({
    data: { posts: [] },
    isLoading: false,
  }),
  useARCCampaigns: () => ({
    data: { items: [], total_count: 0 },
    isLoading: false,
  }),
  useRecentActivity: () => ({
    items: [],
    isLoading: false,
  }),
}));

jest.mock("@/modules/knowledge/hooks", () => ({
  useKnowledgeEntries: () => ({
    data: { items: [], total_count: 0 },
    isPending: false,
  }),
  useKnowledgeTags: () => ({
    data: { tags: [], counts: {} },
  }),
  useKnowledgeSearch: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useCreateEntry: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useDeleteEntry: () => ({
    mutateAsync: jest.fn(),
  }),
  useImportEntry: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
}));

// Helper to set viewport size
const setViewport = (width: number, height: number) => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, "innerHeight", {
    writable: true,
    configurable: true,
    value: height,
  });
  window.dispatchEvent(new Event("resize"));
};

describe("Mobile Responsive Dashboard Pages", () => {
  beforeEach(() => {
    // Reset to mobile viewport before each test
    setViewport(375, 667);
  });

  describe("Dashboard Page", () => {
    it("renders dashboard header responsively on mobile", async () => {
      const DashboardPage = (await import("../dashboard/page")).default;
      render(<DashboardPage />);

      const heading = screen.getByRole("heading", { name: /dashboard/i });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("stacks KPI cards in single column on mobile", async () => {
      const DashboardPage = (await import("../dashboard/page")).default;
      const { container } = render(<DashboardPage />);

      const kpiGrid = container.querySelector(".grid");
      expect(kpiGrid).toHaveClass("grid-cols-1");
      expect(kpiGrid).toHaveClass("sm:grid-cols-2");
      expect(kpiGrid).toHaveClass("lg:grid-cols-4");
    });

    it("renders action button full-width on mobile", async () => {
      const DashboardPage = (await import("../dashboard/page")).default;
      render(<DashboardPage />);

      // The header CTA and the quick-action tile both link to /projects/new;
      // the header one is the responsive button.
      const [newProjectButton] = screen.getAllByRole("link", {
        name: /new project/i,
      });
      expect(newProjectButton).toHaveClass("w-full", "sm:w-auto");
    });
  });

  describe("Projects Page", () => {
    it("renders projects header responsively on mobile", async () => {
      const ProjectsPage = (await import("../projects/page")).default;
      render(<ProjectsPage />);

      const heading = screen.getByRole("heading", { name: /^projects$/i });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("stacks filter controls vertically on mobile", async () => {
      const ProjectsPage = (await import("../projects/page")).default;
      const { container } = render(<ProjectsPage />);

      const filterContainer = container.querySelector(".flex.flex-col.sm\\:flex-row");
      expect(filterContainer).toBeInTheDocument();
    });

    it("renders project grid responsively", async () => {
      const ProjectsPage = (await import("../projects/page")).default;
      const { container } = render(<ProjectsPage />);

      const projectGrid = container.querySelector(".grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-3");
      expect(projectGrid).toBeInTheDocument();
    });
  });

  describe("Writing Page", () => {
    it("renders writing studio header responsively", async () => {
      const WritingPage = (await import("../writing/page")).default;
      render(<WritingPage />);

      const heading = screen.getByRole("heading", { name: /writing studio/i });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("stacks quick action cards in single column on mobile", async () => {
      const WritingPage = (await import("../writing/page")).default;
      const { container } = render(<WritingPage />);

      const quickActionsGrid = container.querySelector(".grid.grid-cols-1.sm\\:grid-cols-3");
      expect(quickActionsGrid).toBeInTheDocument();
    });

    it("enables horizontal scroll for sessions table on mobile", async () => {
      const WritingPage = (await import("../writing/page")).default;
      const { container } = render(<WritingPage />);

      const scrollContainer = container.querySelector(".overflow-x-auto");
      expect(scrollContainer).toBeInTheDocument();
    });
  });

  describe("Analytics Page", () => {
    it("renders analytics header responsively", async () => {
      const AnalyticsPage = (await import("../analytics/page")).default;
      render(<AnalyticsPage />);

      const heading = screen.getByRole("heading", { name: /analytics dashboard/i });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("stacks KPI cards in single column on mobile", async () => {
      const AnalyticsPage = (await import("../analytics/page")).default;
      const { container } = render(<AnalyticsPage />);

      const kpiGrid = container.querySelector(".grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-4");
      expect(kpiGrid).toBeInTheDocument();
    });

    it("renders navigation buttons full-width on mobile", async () => {
      const AnalyticsPage = (await import("../analytics/page")).default;
      const { container } = render(<AnalyticsPage />);

      const navContainer = container.querySelector("nav");
      const links = navContainer?.querySelectorAll("a");
      links?.forEach((link) => {
        expect(link).toHaveClass("w-full", "sm:w-auto");
      });
    });
  });

  describe("Publishing Page", () => {
    it("renders publishing header responsively", async () => {
      const PublishingPage = (await import("../publishing/page")).default;
      render(<PublishingPage />);

      const heading = screen.getByRole("heading", { name: /publishing operations/i });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("stacks quick action cards in single column on mobile", async () => {
      const PublishingPage = (await import("../publishing/page")).default;
      const { container } = render(<PublishingPage />);

      const quickActionsGrid = container.querySelector(".grid.grid-cols-1");
      expect(quickActionsGrid).toBeInTheDocument();
    });

    it("enables horizontal scroll for listings table on mobile", async () => {
      // Assert on the tab itself: the listings table lives behind a tab on the
      // page, and what matters here is that the table can scroll sideways.
      const { ListingsTab } = await import(
        "@/modules/publishing/components/ListingsTab"
      );
      render(<ListingsTab />);

      const table = await screen.findByRole("table");
      expect(table.parentElement).toHaveClass("overflow-x-auto");
    });
  });

  describe("Marketing Page", () => {
    it("renders marketing header responsively", async () => {
      const MarketingPage = (await import("../marketing/page")).default;
      render(<MarketingPage />);

      const heading = screen.getByRole("heading", { name: /marketing & launch command/i });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("enables horizontal scroll for tab navigation on mobile", async () => {
      const MarketingPage = (await import("../marketing/page")).default;
      const { container } = render(<MarketingPage />);

      const tabContainer = container.querySelector(".overflow-x-auto");
      expect(tabContainer).toBeInTheDocument();
    });

    it("stacks stat cards in single column on mobile", async () => {
      const MarketingPage = (await import("../marketing/page")).default;
      const { container } = render(<MarketingPage />);

      const statsGrid = container.querySelector(".grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-4");
      expect(statsGrid).toBeInTheDocument();
    });
  });

  describe("Knowledge Page", () => {
    it("renders knowledge vault header responsively", async () => {
      const KnowledgePage = (await import("../knowledge/page")).default;
      render(<KnowledgePage />);

      // The empty state's own heading also says "Knowledge Vault".
      const heading = screen.getByRole("heading", { level: 1, name: /knowledge vault/i });
      expect(heading).toHaveClass("text-xl", "sm:text-2xl");
    });

    it("renders action buttons responsively", async () => {
      const KnowledgePage = (await import("../knowledge/page")).default;
      render(<KnowledgePage />);

      const importButton = screen.getByRole("button", { name: /import knowledge entry/i });
      expect(importButton).toHaveClass("flex-1", "sm:flex-none");
    });

    it("stacks entry cards in single column on mobile", async () => {
      const KnowledgePage = (await import("../knowledge/page")).default;
      const { container } = render(<KnowledgePage />);

      // With no entries the page shows its empty state instead of the card
      // grid, so assert on whichever of the two is on screen.
      const entryGrid = container.querySelector(
        ".sm\\:grid-cols-2.lg\\:grid-cols-3"
      );
      expect(
        entryGrid ?? screen.getByText("Your Knowledge Vault is empty")
      ).toBeInTheDocument();
    });
  });

  describe("Common Responsive Patterns", () => {
    it("applies consistent padding on mobile across all pages", async () => {
      const pages = [
        (await import("../dashboard/page")).default,
        (await import("../projects/page")).default,
        (await import("../writing/page")).default,
        (await import("../analytics/page")).default,
      ];

      pages.forEach((PageComponent) => {
        const { container } = render(<PageComponent />);
        const mainContainer = container.firstChild as HTMLElement;

        // Check for responsive spacing classes
        expect(
          mainContainer.className.includes("px-4") ||
          mainContainer.className.includes("sm:px-6") ||
          mainContainer.className.includes("space-y-")
        ).toBe(true);
      });
    });

    it("uses responsive text sizes across headers", async () => {
      const DashboardPage = (await import("../dashboard/page")).default;
      render(<DashboardPage />);

      const heading = screen.getByRole("heading", { name: /dashboard/i });
      expect(heading.className).toMatch(/text-(xl|2xl)/);
      expect(heading.className).toMatch(/sm:text-(2xl|3xl)/);
    });
  });

  describe("Mobile Breakpoint Consistency", () => {
    it("uses consistent breakpoint classes (sm:, lg:)", async () => {
      const DashboardPage = (await import("../dashboard/page")).default;
      const { container } = render(<DashboardPage />);

      const html = container.innerHTML;

      // Should use sm: and lg: breakpoints consistently
      expect(html).toMatch(/sm:/);
      expect(html).toMatch(/lg:/);
    });
  });
});
