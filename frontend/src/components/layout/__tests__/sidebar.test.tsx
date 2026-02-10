import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock next/navigation
const mockPathname = "/dashboard";
jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

// Mock hooks and store
const mockToggle = jest.fn();
const mockLogout = jest.fn();

jest.mock("@/hooks/use-sidebar", () => ({
  useSidebar: () => ({
    collapsed: false,
    mobileOpen: false,
    toggle: mockToggle,
    collapse: jest.fn(),
    expand: jest.fn(),
    openMobile: jest.fn(),
    closeMobile: jest.fn(),
  }),
}));

jest.mock("@/lib/store", () => ({
  useAuthStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      user: { name: "Test User", email: "test@example.com", id: "1", role: "owner", org_id: "1" },
      logout: mockLogout,
    }),
}));

// Mock Radix Tooltip to avoid portal issues in tests
jest.mock("@radix-ui/react-tooltip", () => ({
  Provider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Root: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Trigger: React.forwardRef(
    ({ children, asChild, ...props }: { children: React.ReactNode; asChild?: boolean }, ref: React.Ref<HTMLButtonElement>) =>
      asChild ? <>{children}</> : <button ref={ref} {...props}>{children}</button>
  ),
  Content: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { Sidebar } from "../sidebar";

describe("Sidebar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the logo text", () => {
    render(<Sidebar />);
    expect(screen.getByText("SelfPublisherForge")).toBeInTheDocument();
  });

  it("renders all navigation items", () => {
    render(<Sidebar />);
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

  it("displays user name", () => {
    render(<Sidebar />);
    expect(screen.getByText("Test User")).toBeInTheDocument();
  });

  it("displays user initials in avatar", () => {
    render(<Sidebar />);
    expect(screen.getByText("TU")).toBeInTheDocument();
  });

  it("highlights the active navigation item", () => {
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveClass("bg-primary");
  });

  it("has a collapse toggle button", async () => {
    render(<Sidebar />);
    // Find the collapse button (last button in sidebar)
    const buttons = screen.getAllByRole("button");
    const collapseButton = buttons[buttons.length - 1];
    await userEvent.click(collapseButton);
    expect(mockToggle).toHaveBeenCalledTimes(1);
  });
});
