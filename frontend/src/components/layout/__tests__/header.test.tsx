import React from "react";
import { render, screen } from "@/test-utils";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
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
  Bell: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="bell-icon" {...props} />
  ),
  Search: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="search-icon" {...props} />
  ),
  Sun: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="sun-icon" {...props} />
  ),
  Moon: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="moon-icon" {...props} />
  ),
  Monitor: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="monitor-icon" {...props} />
  ),
  Menu: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="menu-icon" {...props} />
  ),
}));

// Mock useTheme hook
const mockSetTheme = jest.fn();
jest.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({
    theme: "system",
    resolvedTheme: "light",
    setTheme: mockSetTheme,
    toggleTheme: jest.fn(),
  }),
}));

// Mock useSidebar hook
const mockOpenMobile = jest.fn();
jest.mock("@/hooks/use-sidebar", () => ({
  useSidebar: () => ({
    collapsed: false,
    mobileOpen: false,
    toggle: jest.fn(),
    collapse: jest.fn(),
    expand: jest.fn(),
    openMobile: mockOpenMobile,
    closeMobile: jest.fn(),
  }),
}));

// Mock auth and UI stores
const mockLogout = jest.fn();
const mockNotifications = [
  { id: "n1", title: "Test", message: "Unread", type: "info", read: false, createdAt: "2025-01-01" },
  { id: "n2", title: "Test2", message: "Read", type: "info", read: true, createdAt: "2025-01-01" },
];

jest.mock("@/lib/store", () => ({
  useAuthStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      user: { name: "Jane Doe", email: "jane@example.com", id: "1", role: "owner", org_id: "1" },
      logout: mockLogout,
    }),
  useUIStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      notifications: mockNotifications,
    }),
}));

// Mock Radix DropdownMenu to avoid portal/pointer issues in jsdom
jest.mock("@radix-ui/react-dropdown-menu", () => {
  const MockRoot = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  const MockTrigger = React.forwardRef<HTMLButtonElement, { children: React.ReactNode; asChild?: boolean }>(
    ({ children, asChild, ...props }, ref) =>
      asChild ? <>{children}</> : <button ref={ref} {...props}>{children}</button>
  );
  MockTrigger.displayName = "DropdownMenuTrigger";

  const MockContent = React.forwardRef<HTMLDivElement, { children: React.ReactNode; className?: string; align?: string }>(
    ({ children, className, ...props }, ref) => <div ref={ref} className={className} {...props}>{children}</div>
  );
  MockContent.displayName = "DropdownMenuContent";

  const MockItem = React.forwardRef<HTMLDivElement, { children: React.ReactNode; onClick?: () => void; asChild?: boolean; className?: string }>(
    ({ children, onClick, asChild, className, ...props }, ref) => (
      <div ref={ref} role="menuitem" className={className} onClick={onClick} {...props}>{children}</div>
    )
  );
  MockItem.displayName = "DropdownMenuItem";

  const MockLabel = React.forwardRef<HTMLDivElement, { children: React.ReactNode }>(
    ({ children, ...props }, ref) => <div ref={ref} {...props}>{children}</div>
  );
  MockLabel.displayName = "DropdownMenuLabel";

  const MockSeparator = React.forwardRef<HTMLDivElement>((props, ref) => <div ref={ref} {...props} />);
  MockSeparator.displayName = "DropdownMenuSeparator";

  const MockPortal = ({ children }: { children: React.ReactNode }) => <>{children}</>;
  const MockSub = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  const MockSubTrigger = React.forwardRef<HTMLDivElement, { children: React.ReactNode }>(
    ({ children, ...props }, ref) => <div ref={ref} {...props}>{children}</div>
  );
  MockSubTrigger.displayName = "DropdownMenuSubTrigger";
  const MockSubContent = React.forwardRef<HTMLDivElement, { children: React.ReactNode }>(
    ({ children, ...props }, ref) => <div ref={ref} {...props}>{children}</div>
  );
  MockSubContent.displayName = "DropdownMenuSubContent";

  return {
    Root: MockRoot,
    Trigger: MockTrigger,
    Content: MockContent,
    Item: MockItem,
    Label: MockLabel,
    Separator: MockSeparator,
    Portal: MockPortal,
    Sub: MockSub,
    SubTrigger: MockSubTrigger,
    SubContent: MockSubContent,
    CheckboxItem: MockItem,
    RadioItem: MockItem,
    RadioGroup: MockRoot,
    ItemIndicator: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
    Group: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import { Header } from "../header";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Header", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the page title based on current pathname", () => {
    render(<Header />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders the search input that accepts text", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const searchInput = screen.getByPlaceholderText("Search books, keywords, markets...");
    expect(searchInput).toBeInTheDocument();

    await user.type(searchInput, "fantasy novel");
    expect(searchInput).toHaveValue("fantasy novel");
  });

  it("navigates to market search on Enter key press", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const searchInput = screen.getByPlaceholderText("Search books, keywords, markets...");
    await user.type(searchInput, "romance{Enter}");

    expect(mockPush).toHaveBeenCalledWith("/market?q=romance");
  });

  it("does not navigate on Enter with empty search", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const searchInput = screen.getByPlaceholderText("Search books, keywords, markets...");
    await user.type(searchInput, "{Enter}");

    expect(mockPush).not.toHaveBeenCalled();
  });

  it("renders the notifications button", () => {
    render(<Header />);
    const notificationsButton = screen.getByRole("button", { name: /notifications/i });
    expect(notificationsButton).toBeInTheDocument();
  });

  it("shows unread notification count badge", () => {
    render(<Header />);
    // mockNotifications has 1 unread notification
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("navigates to settings when notifications button is clicked", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const notificationsButton = screen.getByRole("button", { name: /notifications/i });
    await user.click(notificationsButton);

    expect(mockPush).toHaveBeenCalledWith("/settings");
  });

  it("renders user avatar with initials", () => {
    render(<Header />);
    // "Jane Doe" -> "JD"
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("displays user name in dropdown", () => {
    render(<Header />);
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
  });

  it("displays user email in dropdown", () => {
    render(<Header />);
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
  });

  it("renders the settings link in user dropdown", () => {
    render(<Header />);
    const settingsLink = screen.getByRole("link", { name: /settings/i });
    expect(settingsLink).toBeInTheDocument();
    expect(settingsLink).toHaveAttribute("href", "/settings");
  });

  it("renders sign out option in user dropdown", () => {
    render(<Header />);
    const signOutItem = screen.getByText("Sign out");
    expect(signOutItem).toBeInTheDocument();
  });

  it("calls logout when sign out is clicked", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const signOutItem = screen.getByText("Sign out");
    await user.click(signOutItem);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it("renders the theme toggle button with aria-label", () => {
    render(<Header />);
    const themeButton = screen.getByRole("button", { name: /toggle theme/i });
    expect(themeButton).toBeInTheDocument();
  });

  it("renders the mobile menu button with aria-label", () => {
    render(<Header />);
    const menuButton = screen.getByRole("button", { name: /open menu/i });
    expect(menuButton).toBeInTheDocument();
  });

  it("calls openMobile when mobile menu button is clicked", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const menuButton = screen.getByRole("button", { name: /open menu/i });
    await user.click(menuButton);

    expect(mockOpenMobile).toHaveBeenCalledTimes(1);
  });

  it("all icon-only buttons have aria-labels for accessibility", () => {
    render(<Header />);

    // Verify each icon-only button has an accessible name
    expect(screen.getByRole("button", { name: /open menu/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /toggle theme/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /notifications/i })).toBeInTheDocument();
  });

  it("renders the search input with an aria-label", () => {
    render(<Header />);
    const searchInput = screen.getByLabelText("Search books, keywords, and markets");
    expect(searchInput).toBeInTheDocument();
  });

  it("renders theme options (Light, Dark, System) in dropdown", () => {
    render(<Header />);
    expect(screen.getByText("Light")).toBeInTheDocument();
    expect(screen.getByText("Dark")).toBeInTheDocument();
    expect(screen.getByText("System")).toBeInTheDocument();
  });
});
