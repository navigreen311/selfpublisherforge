import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock lucide-react icons to simple elements
jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  LayoutDashboard: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="layout-dashboard-icon" {...props} />
  ),
  FolderOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="folder-open-icon" {...props} />
  ),
  TrendingUp: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="trending-up-icon" {...props} />
  ),
  PenTool: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="pen-tool-icon" {...props} />
  ),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="book-open-icon" {...props} />
  ),
  Megaphone: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="megaphone-icon" {...props} />
  ),
  Target: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="target-icon" {...props} />
  ),
  BarChart3: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="bar-chart-icon" {...props} />
  ),
  Bot: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="bot-icon" {...props} />
  ),
  Settings: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="settings-icon" {...props} />
  ),
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="x-icon" {...props} />
  ),
  LogOut: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="logout-icon" {...props} />
  ),
}));

// Mock useSidebar hook
const mockCloseMobile = jest.fn();
jest.mock("@/hooks/use-sidebar", () => ({
  useSidebar: () => ({
    collapsed: false,
    mobileOpen: true, // Default to open so the component renders
    toggle: jest.fn(),
    collapse: jest.fn(),
    expand: jest.fn(),
    openMobile: jest.fn(),
    closeMobile: mockCloseMobile,
  }),
}));

// Mock auth store
const mockLogout = jest.fn();
jest.mock("@/lib/store", () => ({
  useAuthStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      user: { name: "Jane Doe", email: "jane@example.com", id: "1", role: "owner", org_id: "1" },
      logout: mockLogout,
    }),
}));

// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import { MobileNav } from "../mobile-nav";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("MobileNav", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders all navigation items", () => {
    render(<MobileNav />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Market Research")).toBeInTheDocument();
    expect(screen.getByText("Writing Studio")).toBeInTheDocument();
    expect(screen.getByText("Publishing")).toBeInTheDocument();
    expect(screen.getByText("Marketing")).toBeInTheDocument();
    expect(screen.getByText("Advertising")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();
    expect(screen.getByText("AI Agents")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders the app title", () => {
    render(<MobileNav />);
    expect(screen.getByText("SelfPublisherForge")).toBeInTheDocument();
  });

  it("renders the close button", () => {
    render(<MobileNav />);
    // The close button contains the X icon
    const buttons = screen.getAllByRole("button");
    const closeButton = buttons.find((btn) =>
      btn.querySelector("[data-testid='x-icon']")
    );
    expect(closeButton).toBeTruthy();
  });

  it("calls closeMobile when close button is clicked", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    const buttons = screen.getAllByRole("button");
    const closeButton = buttons.find((btn) =>
      btn.querySelector("[data-testid='x-icon']")
    );
    expect(closeButton).toBeTruthy();
    await user.click(closeButton!);

    expect(mockCloseMobile).toHaveBeenCalledTimes(1);
  });

  it("renders the sign out button with logout icon", () => {
    render(<MobileNav />);
    const buttons = screen.getAllByRole("button");
    const logoutButton = buttons.find((btn) =>
      btn.querySelector("[data-testid='logout-icon']")
    );
    expect(logoutButton).toBeTruthy();
  });

  it("calls logout and closeMobile when sign out button is clicked", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    const buttons = screen.getAllByRole("button");
    const logoutButton = buttons.find((btn) =>
      btn.querySelector("[data-testid='logout-icon']")
    );
    expect(logoutButton).toBeTruthy();
    await user.click(logoutButton!);

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockCloseMobile).toHaveBeenCalledTimes(1);
  });

  it("navigation links point to correct routes", () => {
    render(<MobileNav />);

    const expectedRoutes: Record<string, string> = {
      Dashboard: "/dashboard",
      Projects: "/projects",
      "Market Research": "/market",
      "Writing Studio": "/writing",
      Publishing: "/publishing",
      Marketing: "/marketing",
      Advertising: "/advertising",
      Analytics: "/analytics",
      "AI Agents": "/agents",
      Settings: "/settings",
    };

    for (const [label, href] of Object.entries(expectedRoutes)) {
      const link = screen.getByText(label).closest("a");
      expect(link).toHaveAttribute("href", href);
    }
  });

  it("displays user name", () => {
    render(<MobileNav />);
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
  });

  it("displays user email", () => {
    render(<MobileNav />);
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
  });

  it("displays user initials in avatar", () => {
    render(<MobileNav />);
    // "Jane Doe" -> "JD"
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("highlights the active navigation item", () => {
    render(<MobileNav />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveClass("bg-primary");
  });

  it("non-active navigation items do not have active class", () => {
    render(<MobileNav />);
    const projectsLink = screen.getByText("Projects").closest("a");
    expect(projectsLink).not.toHaveClass("bg-primary");
  });

  it("calls closeMobile when a navigation link is clicked", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    const projectsLink = screen.getByText("Projects").closest("a");
    expect(projectsLink).toBeTruthy();
    await user.click(projectsLink!);

    expect(mockCloseMobile).toHaveBeenCalledTimes(1);
  });

  it("calls closeMobile when backdrop is clicked", async () => {
    const user = userEvent.setup();
    const { container } = render(<MobileNav />);

    // The backdrop is the first child div with bg-black/50 class
    const backdrop = container.querySelector(".bg-black\\/50");
    expect(backdrop).toBeTruthy();
    await user.click(backdrop!);

    expect(mockCloseMobile).toHaveBeenCalledTimes(1);
  });

  it("returns null when mobileOpen is false", () => {
    // Override the useSidebar mock for this test
    const useSidebarModule = require("@/hooks/use-sidebar");
    const originalUseSidebar = useSidebarModule.useSidebar;
    useSidebarModule.useSidebar = () => ({
      collapsed: false,
      mobileOpen: false,
      toggle: jest.fn(),
      collapse: jest.fn(),
      expand: jest.fn(),
      openMobile: jest.fn(),
      closeMobile: jest.fn(),
    });

    const { container } = render(<MobileNav />);
    expect(container.innerHTML).toBe("");

    // Restore original mock
    useSidebarModule.useSidebar = originalUseSidebar;
  });

  it("renders exactly 10 navigation links", () => {
    render(<MobileNav />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(10);
  });
});
