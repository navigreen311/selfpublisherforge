import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

let mockPathname = "/dashboard/projects";

jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

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

jest.mock("lucide-react", () => ({
  Home: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="home-icon" {...props} />
  ),
  ChevronRight: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-right-icon" {...props} />
  ),
}));

// ─── Import after mocks ─────────────────────────────────────────────────────

import { Breadcrumb } from "../breadcrumb";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("Breadcrumb", () => {
  beforeEach(() => {
    mockPathname = "/dashboard/projects";
  });

  it("returns null when only one breadcrumb segment", () => {
    mockPathname = "/dashboard";
    const { container } = render(<Breadcrumb />);
    expect(container.querySelector("nav")).not.toBeInTheDocument();
  });

  it("renders auto-generated breadcrumbs from multi-segment pathname", () => {
    mockPathname = "/dashboard/projects";
    render(<Breadcrumb />);

    const nav = screen.getByLabelText("Breadcrumb");
    expect(nav).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
  });

  it("renders custom items when provided", () => {
    const items = [
      { label: "Home", href: "/" },
      { label: "Books", href: "/books" },
      { label: "Edit" },
    ];
    render(<Breadcrumb items={items} />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Books")).toBeInTheDocument();
    expect(screen.getByText("Edit")).toBeInTheDocument();
  });

  it("links intermediate items and renders last item as plain text", () => {
    mockPathname = "/dashboard/projects/settings";
    render(<Breadcrumb />);

    // "Dashboard" should be a link
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toBeInTheDocument();
    expect(dashboardLink).toHaveAttribute("href", "/dashboard");

    // "Projects" should be a link
    const projectsLink = screen.getByText("Projects").closest("a");
    expect(projectsLink).toBeInTheDocument();
    expect(projectsLink).toHaveAttribute("href", "/dashboard/projects");

    // "Settings" is the last item, should be a span (not a link)
    const settingsEl = screen.getByText("Settings");
    expect(settingsEl.tagName).toBe("SPAN");
    expect(settingsEl.closest("a")).not.toBeInTheDocument();
  });

  it("renders Home icon link pointing to /dashboard", () => {
    render(<Breadcrumb />);

    const homeIcon = screen.getByTestId("home-icon");
    expect(homeIcon).toBeInTheDocument();

    const homeLink = screen.getByLabelText("Home");
    expect(homeLink).toHaveAttribute("href", "/dashboard");
  });

  it("truncates UUID segments", () => {
    mockPathname = "/dashboard/projects/550e8400-e29b-41d4-a716-446655440000";
    render(<Breadcrumb />);

    expect(screen.getByText("550e8400...")).toBeInTheDocument();
  });

  it("maps known route labels correctly", () => {
    mockPathname = "/writing/outline";
    render(<Breadcrumb />);

    expect(screen.getByText("Writing Studio")).toBeInTheDocument();
    expect(screen.getByText("Outline Generator")).toBeInTheDocument();
  });

  it("capitalizes unknown segments as fallback", () => {
    mockPathname = "/dashboard/some-custom-page";
    render(<Breadcrumb />);

    expect(screen.getByText("Some Custom Page")).toBeInTheDocument();
  });

  it("filters out route group segments in parentheses", () => {
    // Simulating a pathname that might include Next.js route groups
    mockPathname = "/(dashboard)/projects/settings";
    render(<Breadcrumb />);

    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<Breadcrumb className="my-custom-class" />);

    const nav = screen.getByLabelText("Breadcrumb");
    expect(nav).toHaveClass("my-custom-class");
  });

  it("renders chevron separators between breadcrumb items", () => {
    mockPathname = "/dashboard/projects";
    render(<Breadcrumb />);

    const chevrons = screen.getAllByTestId("chevron-right-icon");
    // Two breadcrumb items = two chevrons (one before each)
    expect(chevrons.length).toBe(2);
  });
});
