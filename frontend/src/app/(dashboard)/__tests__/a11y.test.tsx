import { render, screen } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import DashboardLayout from "../layout";
import { SkipLink } from "@/components/shared/SkipLink";
import { VisuallyHidden } from "@/components/shared/VisuallyHidden";
import { Loading } from "@/components/shared/loading";
import {
  announceToScreenReader,
  generateA11yId,
  hasValidContrast,
  getAccessibleLabel,
} from "@/lib/a11y";

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock Next.js router and navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
  }),
}));

// Mock hooks
jest.mock("@/hooks/use-sidebar", () => ({
  useSidebar: () => ({
    collapsed: false,
    toggle: jest.fn(),
    openMobile: jest.fn(),
  }),
}));

jest.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({
    theme: "light",
    setTheme: jest.fn(),
  }),
}));

// The unread count comes from the notifications module now, not the UI store,
// and the header only mounts the bell for a user with an id.
jest.mock("@/modules/notifications/hooks", () => ({
  useNotifications: () => ({ data: { items: [] }, isLoading: false }),
  useUnreadCount: () => ({ data: { unread_count: 2 } }),
  useMarkAllAsRead: () => ({ mutate: jest.fn(), isPending: false }),
  useMarkAsRead: () => ({ mutate: jest.fn(), isPending: false }),
  useNotificationSubscription: () => undefined,
}));

jest.mock("@/lib/store", () => ({
  useAuthStore: (selector: any) => {
    const store = {
      user: { id: "user-1", name: "Test User", email: "test@example.com" },
      logout: jest.fn(),
    };
    return selector ? selector(store) : store;
  },
  useUIStore: (selector: any) => {
    const store = {
      notifications: [
        { id: "1", read: false, message: "Test" },
        { id: "2", read: false, message: "Test 2" },
      ],
    };
    return selector ? selector(store) : store;
  },
}));

describe("Accessibility - Dashboard Layout", () => {
  it("should not have any accessibility violations", async () => {
    const { container } = render(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("should have skip to main content link", () => {
    render(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    );

    const skipLink = screen.getByText("Skip to main content");
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute("href", "#main-content");
  });

  it("should have main landmark with id", () => {
    const { container } = render(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    );

    const main = container.querySelector('main[role="main"]');
    expect(main).toBeInTheDocument();
    expect(main).toHaveAttribute("id", "main-content");
  });

  it("should have navigation landmark with aria-label", () => {
    const { container } = render(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    );

    const nav = container.querySelector('nav[aria-label="Main navigation"]');
    expect(nav).toBeInTheDocument();
  });

  it("should have aria-current on active navigation links", () => {
    const { container } = render(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    );

    // The current path is /dashboard, so Dashboard link should have aria-current
    const dashboardLink = screen.getByRole("link", { name: "Dashboard" });
    expect(dashboardLink).toHaveAttribute("aria-current", "page");
  });
});

describe("Accessibility - SkipLink Component", () => {
  it("should render with default props", () => {
    render(<SkipLink />);
    const link = screen.getByText("Skip to main content");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "#main-content");
  });

  it("should render with custom href and text", () => {
    render(<SkipLink href="#custom-id">Skip to custom section</SkipLink>);
    const link = screen.getByText("Skip to custom section");
    expect(link).toHaveAttribute("href", "#custom-id");
  });

  it("should have sr-only class for visual hiding", () => {
    render(<SkipLink />);
    const link = screen.getByText("Skip to main content");
    expect(link).toHaveClass("sr-only");
  });

  it("should not have any accessibility violations", async () => {
    const { container } = render(<SkipLink />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe("Accessibility - VisuallyHidden Component", () => {
  it("should render children", () => {
    render(<VisuallyHidden>Hidden content</VisuallyHidden>);
    expect(screen.getByText("Hidden content")).toBeInTheDocument();
  });

  it("should have sr-only class", () => {
    render(<VisuallyHidden>Hidden content</VisuallyHidden>);
    const element = screen.getByText("Hidden content");
    expect(element).toHaveClass("sr-only");
  });

  it("should support polite aria-live", () => {
    render(<VisuallyHidden polite>Polite announcement</VisuallyHidden>);
    const element = screen.getByText("Polite announcement");
    expect(element).toHaveAttribute("aria-live", "polite");
    expect(element).toHaveAttribute("aria-atomic", "true");
  });

  it("should support assertive aria-live", () => {
    render(<VisuallyHidden assertive>Assertive announcement</VisuallyHidden>);
    const element = screen.getByText("Assertive announcement");
    expect(element).toHaveAttribute("aria-live", "assertive");
    expect(element).toHaveAttribute("aria-atomic", "true");
  });

  it("should not have aria-live by default", () => {
    render(<VisuallyHidden>No announcement</VisuallyHidden>);
    const element = screen.getByText("No announcement");
    expect(element).not.toHaveAttribute("aria-live");
  });
});

describe("Accessibility - Loading Component", () => {
  it("should have proper ARIA attributes", () => {
    const { container } = render(<Loading />);
    const loadingDiv = container.querySelector('[role="status"]');
    expect(loadingDiv).toBeInTheDocument();
    expect(loadingDiv).toHaveAttribute("aria-live", "polite");
    expect(loadingDiv).toHaveAttribute("aria-busy", "true");
  });

  it("should have visually hidden loading text when no text provided", () => {
    render(<Loading />);
    const hiddenText = screen.getByText("Loading...");
    expect(hiddenText).toHaveClass("sr-only");
  });

  it("should show custom text when provided", () => {
    render(<Loading text="Loading your data" />);
    expect(screen.getByText("Loading your data")).toBeInTheDocument();
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  it("should mark spinner as decorative with aria-hidden", () => {
    const { container } = render(<Loading />);
    const spinner = container.querySelector('svg');
    expect(spinner).toHaveAttribute("aria-hidden", "true");
  });

  it("should not have any accessibility violations", async () => {
    const { container } = render(<Loading text="Loading data" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe("Accessibility - Helper Functions", () => {
  describe("announceToScreenReader", () => {
    beforeEach(() => {
      document.body.innerHTML = "";
    });

    it("should create announcement element with polite priority", () => {
      announceToScreenReader("Test message");
      const announcement = document.querySelector('[role="status"]');
      expect(announcement).toBeInTheDocument();
      expect(announcement).toHaveAttribute("aria-live", "polite");
      expect(announcement?.textContent).toBe("Test message");
    });

    it("should create announcement element with assertive priority", () => {
      announceToScreenReader("Urgent message", "assertive");
      const announcement = document.querySelector('[role="status"]');
      expect(announcement).toHaveAttribute("aria-live", "assertive");
    });

    it("should clean up announcement after timeout", async () => {
      jest.useFakeTimers();
      announceToScreenReader("Test message");
      expect(document.querySelector('[role="status"]')).toBeInTheDocument();

      jest.advanceTimersByTime(1100);
      expect(document.querySelector('[role="status"]')).not.toBeInTheDocument();
      jest.useRealTimers();
    });
  });

  describe("generateA11yId", () => {
    it("should generate unique IDs", () => {
      const id1 = generateA11yId();
      const id2 = generateA11yId();
      expect(id1).not.toBe(id2);
    });

    it("should use custom prefix", () => {
      const id = generateA11yId("custom");
      expect(id).toMatch(/^custom-/);
    });

    it("should use default prefix", () => {
      const id = generateA11yId();
      expect(id).toMatch(/^a11y-/);
    });
  });

  describe("hasValidContrast", () => {
    it("should validate high contrast (black on white)", () => {
      expect(hasValidContrast("#000000", "#ffffff")).toBe(true);
    });

    it("should validate sufficient contrast for normal text", () => {
      // 4.5:1 is minimum for normal text
      expect(hasValidContrast("#595959", "#ffffff")).toBe(true);
    });

    it("should reject insufficient contrast for normal text", () => {
      expect(hasValidContrast("#aaaaaa", "#ffffff")).toBe(false);
    });

    it("should validate large text with lower threshold", () => {
      // 3:1 is minimum for large text
      expect(hasValidContrast("#777777", "#ffffff", true)).toBe(true);
    });
  });

  describe("getAccessibleLabel", () => {
    it("should get aria-label", () => {
      const div = document.createElement("div");
      div.setAttribute("aria-label", "Test label");
      expect(getAccessibleLabel(div)).toBe("Test label");
    });

    it("should get label from aria-labelledby", () => {
      const label = document.createElement("span");
      label.id = "test-label";
      label.textContent = "Label text";
      document.body.appendChild(label);

      const div = document.createElement("div");
      div.setAttribute("aria-labelledby", "test-label");
      expect(getAccessibleLabel(div)).toBe("Label text");

      document.body.removeChild(label);
    });

    it("should get label from associated label element", () => {
      const label = document.createElement("label");
      label.setAttribute("for", "test-input");
      label.textContent = "Input label";
      document.body.appendChild(label);

      const input = document.createElement("input");
      input.id = "test-input";
      expect(getAccessibleLabel(input)).toBe("Input label");

      document.body.removeChild(label);
    });

    it("should return null if no label found", () => {
      const div = document.createElement("div");
      expect(getAccessibleLabel(div)).toBeNull();
    });
  });
});

describe("Accessibility - Interactive Elements", () => {
  it("should have aria-labels on icon-only buttons in sidebar", () => {
    render(
      <DashboardLayout>
        <div>Test</div>
      </DashboardLayout>
    );

    const collapseButton = screen.getByLabelText("Collapse sidebar");
    expect(collapseButton).toBeInTheDocument();

    const signOutButtons = screen.getAllByLabelText("Sign out");
    expect(signOutButtons.length).toBeGreaterThan(0);
  });

  it("should have aria-label on theme toggle button", () => {
    render(
      <DashboardLayout>
        <div>Test</div>
      </DashboardLayout>
    );

    const themeButton = screen.getByLabelText("Toggle theme");
    expect(themeButton).toBeInTheDocument();
  });

  it("should have descriptive aria-label on notifications button", () => {
    render(
      <DashboardLayout>
        <div>Test</div>
      </DashboardLayout>
    );

    // Since there are 2 unread notifications in the mock
    const notifButton = screen.getByRole("button", {
      name: "Notifications (2 unread)",
    });
    expect(notifButton).toBeInTheDocument();
  });

  it("should have aria-label on search input", () => {
    render(
      <DashboardLayout>
        <div>Test</div>
      </DashboardLayout>
    );

    const searchInput = screen.getByLabelText("Search books, keywords, and markets");
    expect(searchInput).toBeInTheDocument();
  });
});

describe("Accessibility - Focus Management", () => {
  it("should have visible focus styles on buttons", () => {
    const { container } = render(
      <DashboardLayout>
        <div>Test</div>
      </DashboardLayout>
    );

    // All buttons should have focus-visible class from shadcn/ui button component
    const buttons = container.querySelectorAll("button");
    buttons.forEach((button) => {
      const classes = button.className;
      expect(classes).toMatch(/focus-visible/);
    });
  });

  it("should have proper tab order for navigation", () => {
    render(
      <DashboardLayout>
        <div>Test</div>
      </DashboardLayout>
    );

    const skipLink = screen.getByText("Skip to main content");
    const dashboardLink = screen.getByRole("link", { name: "Dashboard" });

    // Skip link should come first in tab order
    expect(skipLink.compareDocumentPosition(dashboardLink)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING
    );
  });
});
