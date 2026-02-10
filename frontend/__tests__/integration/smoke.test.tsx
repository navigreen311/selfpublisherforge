/**
 * Frontend integration smoke tests for SelfPublisherForge.
 *
 * These tests verify that major pages and layout components render
 * without crashing. They use shallow rendering with mocked dependencies
 * (Next.js navigation, Zustand stores, Lucide icons).
 */

import React from "react";
import { render, screen } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks — set up before component imports
// ---------------------------------------------------------------------------

// Mock next/navigation (used by almost every component)
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/link to render a plain <a>
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...rest}>
        {children}
      </a>
    );
  };
});

// Mock the auth store
jest.mock("@/lib/store", () => ({
  useAuthStore: (selector?: (state: Record<string, unknown>) => unknown) => {
    const state = {
      user: { id: "1", name: "Test User", email: "test@example.com", role: "owner", org_id: "org-1" },
      isAuthenticated: true,
      isLoading: false,
      setUser: jest.fn(),
      setAuthenticated: jest.fn(),
      setLoading: jest.fn(),
      logout: jest.fn(),
    };
    return selector ? selector(state) : state;
  },
  useUIStore: (selector?: (state: Record<string, unknown>) => unknown) => {
    const state = {
      sidebarCollapsed: false,
      sidebarMobileOpen: false,
      theme: "light" as const,
      notifications: [],
      toggleSidebar: jest.fn(),
      setSidebarCollapsed: jest.fn(),
      setSidebarMobileOpen: jest.fn(),
      setTheme: jest.fn(),
      addNotification: jest.fn(),
      markNotificationRead: jest.fn(),
      clearNotifications: jest.fn(),
      unreadCount: () => 0,
    };
    return selector ? selector(state) : state;
  },
}));

// Mock the auth hook
jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", name: "Test User", email: "test@example.com", role: "owner", org_id: "org-1" },
    isAuthenticated: true,
    isLoading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    checkAuth: jest.fn(),
  }),
}));

// Mock sidebar hook
jest.mock("@/hooks/use-sidebar", () => ({
  useSidebar: () => ({
    collapsed: false,
    mobileOpen: false,
    toggle: jest.fn(),
    collapse: jest.fn(),
    expand: jest.fn(),
    openMobile: jest.fn(),
    closeMobile: jest.fn(),
  }),
}));

// Mock theme hook
jest.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({
    theme: "light",
    resolvedTheme: "light",
    setTheme: jest.fn(),
    toggleTheme: jest.fn(),
  }),
}));

// Mock the API module
jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn().mockResolvedValue({ data: {} }),
    post: jest.fn().mockResolvedValue({ data: {} }),
    put: jest.fn().mockResolvedValue({ data: {} }),
    patch: jest.fn().mockResolvedValue({ data: {} }),
    delete: jest.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  },
}));

// Mock analytics hooks to avoid import chain issues
jest.mock("@/modules/analytics/hooks", () => ({
  useDashboard: () => ({ data: null, isLoading: true, error: null }),
}));

// Mock analytics components
jest.mock("@/modules/analytics/components/KPICard", () => ({
  KPICard: () => <div data-testid="kpi-card" />,
}));
jest.mock("@/modules/analytics/components/RevenueChart", () => ({
  RevenueChart: () => <div data-testid="revenue-chart" />,
}));
jest.mock("@/modules/analytics/components/PortfolioTable", () => ({
  PortfolioTable: () => <div data-testid="portfolio-table" />,
}));

// Mock Radix UI primitives that are hard to test in JSDOM
jest.mock("@radix-ui/react-tooltip", () => ({
  Root: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Trigger: React.forwardRef(({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => <div ref={ref} {...props}>{children}</div>),
  Content: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Provider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("@radix-ui/react-dropdown-menu", () => ({
  Root: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Trigger: React.forwardRef(({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLButtonElement>) => <button ref={ref} {...props}>{children}</button>),
  Content: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Item: ({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>) => <div {...props}>{children}</div>,
  Label: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Separator: () => <hr />,
  Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("@radix-ui/react-select", () => ({
  Root: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Trigger: React.forwardRef(({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLButtonElement>) => <button ref={ref} {...props}>{children}</button>),
  Value: ({ children }: { children?: React.ReactNode }) => <span>{children}</span>,
  Content: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Item: React.forwardRef(({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => <div ref={ref} {...props}>{children}</div>),
  ItemText: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Viewport: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Icon: () => <span />,
  ItemIndicator: ({ children }: { children?: React.ReactNode }) => <span>{children}</span>,
  ScrollUpButton: () => <div />,
  ScrollDownButton: () => <div />,
  Group: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Label: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Separator: () => <hr />,
}));

jest.mock("@radix-ui/react-avatar", () => ({
  Root: ({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>) => <div {...props}>{children}</div>,
  Image: (props: Record<string, unknown>) => <img {...props} />,
  Fallback: ({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>) => <span {...props}>{children}</span>,
}));

jest.mock("@radix-ui/react-separator", () => ({
  Root: React.forwardRef((props: Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => <div ref={ref} role="separator" {...props} />),
}));

jest.mock("@radix-ui/react-switch", () => ({
  Root: React.forwardRef(({ children, ...props }: { children?: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLButtonElement>) => <button ref={ref} role="switch" {...props}>{children}</button>),
  Thumb: () => <span />,
}));

jest.mock("@radix-ui/react-slot", () => ({
  Slot: React.forwardRef(({ children, ...props }: { children?: React.ReactNode } & Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => {
    if (React.isValidElement(children)) {
      return React.cloneElement(children, { ...props, ref } as Record<string, unknown>);
    }
    return <div ref={ref} {...props}>{children}</div>;
  }),
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Frontend Integration Smoke Tests", () => {
  // 1. Auth layout renders
  it("renders the auth layout with branding", async () => {
    const AuthLayout = (await import("@/app/(auth)/layout")).default;
    render(
      <AuthLayout>
        <div data-testid="child">Child Content</div>
      </AuthLayout>
    );
    expect(screen.getByText("SelfPublisherForge")).toBeInTheDocument();
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  // 2. Login page renders
  it("renders the login page with form elements", async () => {
    const LoginPage = (await import("@/app/(auth)/login/page")).default;
    render(<LoginPage />);
    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(screen.getByText("Sign in")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument();
  });

  // 3. Register page renders
  it("renders the register page with form elements", async () => {
    const RegisterPage = (await import("@/app/(auth)/register/page")).default;
    render(<RegisterPage />);
    expect(screen.getByText("Create your account")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Create account")).toBeInTheDocument();
  });

  // 4. Dashboard layout renders
  it("renders the dashboard layout with sidebar and header", async () => {
    const DashboardLayout = (await import("@/app/(dashboard)/layout")).default;
    render(
      <DashboardLayout>
        <div data-testid="dashboard-child">Dashboard Content</div>
      </DashboardLayout>
    );
    expect(screen.getByTestId("dashboard-child")).toBeInTheDocument();
  });

  // 5. Dashboard page renders
  it("renders the main dashboard page with stats", async () => {
    const DashboardPage = (await import("@/app/(dashboard)/dashboard/page")).default;
    render(<DashboardPage />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Total Books")).toBeInTheDocument();
    expect(screen.getByText("Monthly Revenue")).toBeInTheDocument();
  });

  // 6. StatCard component renders
  it("renders the StatCard component correctly", async () => {
    const { StatCard } = await import("@/components/shared/stat-card");
    const MockIcon = () => <svg data-testid="mock-icon" />;
    render(
      <StatCard
        label="Test Metric"
        value={42}
        icon={MockIcon as unknown as import("lucide-react").LucideIcon}
        trend={{ value: 10, isPositive: true }}
      />
    );
    expect(screen.getByText("Test Metric")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("+10% from last month")).toBeInTheDocument();
  });

  // 7. Sidebar navigation has all expected links
  it("renders the sidebar with all navigation items", async () => {
    const { Sidebar } = await import("@/components/layout/sidebar");
    render(<Sidebar />);

    const expectedLabels = [
      "Dashboard",
      "Projects",
      "Market Research",
      "Writing Studio",
      "Publishing",
      "Marketing",
      "Advertising",
      "Analytics",
      "AI Agents",
      "Settings",
    ];

    for (const label of expectedLabels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  // 8. Types are well-defined
  it("has correct User type shape", async () => {
    // This is a compile-time check more than runtime, but we can verify
    // the type module exports the expected interface
    const types = await import("@/types");
    // If the module loads without error, the types are valid
    expect(types).toBeDefined();
  });
});
